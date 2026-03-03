#!/usr/bin/env python3
"""
AgenticNow Daily Bot
━━━━━━━━━━━━━━━━━━━
每日自动抓取 80+ 英文 AI/Crypto 信源，
通过 Claude API 生成中文标题+摘要，
推送至 @AgenticNow Telegram 频道。

用法:
    python main.py                     # 正式运行
    python main.py --dry-run           # 预览模式（不推送 Telegram）
    python main.py --max-articles 8    # 自定义最多推送文章数
    python main.py --mode digest       # 每日合集模式
    python main.py --enable-twitter    # 启用 X/Twitter 信源（需 RSSHub）
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

# ─── 日志配置 ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agenticnow")

# ─── 模块导入 ─────────────────────────────────────────────────────────────────
from sources import RSS_SOURCES, REDDIT_SOURCES, TWITTER_SOURCES, GITHUB_TOPICS
from fetchers.rss import fetch_rss_sources
from fetchers.reddit import fetch_reddit_sources
from fetchers.github_trending import fetch_github_trending
from processor.summarizer import summarize_articles
from publisher.telegram import TelegramPublisher
from storage.dedup import URLStore


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def _build_twitter_rss_sources(rsshub_base: str) -> list[dict]:
    """将 Twitter/X 账号转为 RSSHub RSS 信源格式。"""
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "url": f"https://x.com/{s['handle']}",
            "rss": f"{rsshub_base.rstrip('/')}/twitter/user/{s['handle']}",
            "category": s["category"],
        }
        for s in TWITTER_SOURCES
    ]


def _score_article(article: dict) -> float:
    """
    对文章打分，用于预排序（在调用 Claude 之前）。
    分数越高 = 优先处理。
    """
    score = 0.0

    # Reddit 热度加分
    if article.get("type") == "reddit":
        score += min(article.get("score", 0) / 50, 5.0)

    # 新鲜度加分（越新越高）
    pub_str = article.get("published")
    if pub_str:
        try:
            pub = datetime.fromisoformat(pub_str)
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            hours_old = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
            score += max(0.0, 10.0 - hours_old / 4)  # 40h 内线性衰减
        except Exception:
            pass

    # 有摘要内容加分（意味着信源质量更高）
    if article.get("excerpt"):
        score += 1.0

    return score


def _preselect(articles: list[dict], n: int) -> list[dict]:
    """从所有新文章中预选 n 篇候选，送入 Claude 处理。"""
    ranked = sorted(articles, key=_score_article, reverse=True)
    return ranked[:n]


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def run(
    dry_run: bool = False,
    max_articles: int = 12,
    hours_lookback: int = 48,
    publish_mode: str = "individual",
    enable_twitter: bool = False,
    enable_github: bool = True,
) -> None:
    """
    AgenticNow Bot 主流程。

    1. 抓取所有信源（RSS + Reddit + GitHub + 可选 Twitter）
    2. 过滤已发送 URL
    3. 预选候选文章
    4. Claude API 生成中文摘要
    5. 按相关度排序，取 top N
    6. 推送至 Telegram
    7. 标记 URL 为已发送并保存
    """
    logger.info("=" * 56)
    logger.info("  🤖  AgenticNow Bot  |  %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("  Max articles : %d  |  Lookback : %dh", max_articles, hours_lookback)
    logger.info("  Mode : %s  |  %s", publish_mode, "DRY RUN" if dry_run else "LIVE")
    logger.info("=" * 56)

    # ── 读取环境变量 ──────────────────────────────────────────────────────────
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_channel = os.environ.get("TELEGRAM_CHANNEL_ID", "@AgenticNow")
    rsshub_base = os.environ.get("RSSHUB_BASE_URL", "https://rsshub.app")

    if not anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY is not set. Exiting.")
        sys.exit(1)
    if not dry_run and not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set (required for live mode). Exiting.")
        sys.exit(1)

    # ── URL 去重存储 ──────────────────────────────────────────────────────────
    url_store = URLStore("seen_urls.json")

    # ── 抓取阶段 ──────────────────────────────────────────────────────────────
    all_articles: list[dict] = []

    # 1. RSS（主力信源）
    logger.info("📡 Fetching RSS sources (%d sources)...", len(RSS_SOURCES))
    rss_articles = fetch_rss_sources(RSS_SOURCES, hours_lookback=hours_lookback)
    logger.info("   → %d articles", len(rss_articles))
    all_articles.extend(rss_articles)

    # 2. Reddit
    logger.info("📡 Fetching Reddit sources (%d subreddits)...", len(REDDIT_SOURCES))
    reddit_articles = fetch_reddit_sources(REDDIT_SOURCES, hours_lookback=hours_lookback)
    logger.info("   → %d posts", len(reddit_articles))
    all_articles.extend(reddit_articles)

    # 3. GitHub Trending（可关闭）
    if enable_github:
        logger.info("📡 Fetching GitHub Trending...")
        github_articles = fetch_github_trending(topics=GITHUB_TOPICS, max_items=5)
        logger.info("   → %d repos", len(github_articles))
        all_articles.extend(github_articles)

    # 4. X/Twitter via RSSHub（可选）
    if enable_twitter:
        twitter_rss = _build_twitter_rss_sources(rsshub_base)
        logger.info("📡 Fetching X/Twitter sources (%d accounts via RSSHub)...", len(twitter_rss))
        twitter_articles = fetch_rss_sources(twitter_rss, hours_lookback=hours_lookback)
        logger.info("   → %d tweets/posts", len(twitter_articles))
        all_articles.extend(twitter_articles)

    logger.info("📊 Total fetched: %d articles", len(all_articles))

    # ── 去重过滤 ──────────────────────────────────────────────────────────────
    new_articles = url_store.filter_new(all_articles)
    if not new_articles:
        logger.info("✅ No new articles found. Nothing to publish today.")
        return

    # ── 预选候选文章（2× 目标数量，留给 Claude 评分空间）──────────────────────
    candidates = _preselect(new_articles, n=max_articles * 2)
    logger.info("🎯 Pre-selected %d candidates for summarization", len(candidates))

    # ── Claude 摘要生成 ───────────────────────────────────────────────────────
    logger.info("🧠 Generating Chinese summaries via Claude API...")
    enriched = summarize_articles(candidates, api_key=anthropic_api_key)

    # ── 最终排序：按 Claude 相关度评分取 Top N ────────────────────────────────
    final_articles = sorted(enriched, key=lambda x: x.get("relevance", 5), reverse=True)[
        :max_articles
    ]

    logger.info("📋 Final selection: %d articles", len(final_articles))
    for i, a in enumerate(final_articles, 1):
        title = a.get("title_zh") or a.get("title", "")
        logger.info(
            "   %d. [%s/10] %s",
            i,
            a.get("relevance", "?"),
            title[:55],
        )

    # ── 预览 / 推送 ───────────────────────────────────────────────────────────
    if dry_run:
        logger.info("\n🔍 DRY RUN — 消息预览：")
        logger.info("=" * 56)
        dummy = TelegramPublisher("dummy_token", "@AgenticNow")
        for article in final_articles:
            print(dummy.format_article(article))
            print("─" * 40)
        return

    publisher = TelegramPublisher(telegram_token, telegram_channel)
    logger.info("📤 Publishing to %s...", telegram_channel)
    published_count = publisher.publish_articles(final_articles, mode=publish_mode)

    # ── 标记已发送 & 保存 ─────────────────────────────────────────────────────
    published_urls = [a["url"] for a in final_articles[:published_count]]
    url_store.mark_seen_batch(published_urls)
    url_store.save()

    logger.info("=" * 56)
    logger.info(
        "✅ Done! Published %d/%d articles. Store: %d URLs",
        published_count,
        len(final_articles),
        url_store.total,
    )


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="AgenticNow Daily Bot — AI content curator for Telegram"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and summarize but DO NOT post to Telegram",
    )
    p.add_argument(
        "--max-articles",
        type=int,
        default=None,
        metavar="N",
        help="Override max articles per run (default: MAX_ARTICLES_PER_RUN env or 12)",
    )
    p.add_argument(
        "--hours-lookback",
        type=int,
        default=None,
        metavar="H",
        help="Override lookback window in hours (default: HOURS_LOOKBACK env or 48)",
    )
    p.add_argument(
        "--mode",
        choices=["individual", "digest"],
        default=None,
        help="Publish mode: 'individual' (one post per article) or 'digest' (daily summary)",
    )
    p.add_argument(
        "--enable-twitter",
        action="store_true",
        help="Enable X/Twitter sources via RSSHub (RSSHUB_BASE_URL must be set)",
    )
    p.add_argument(
        "--disable-github",
        action="store_true",
        help="Disable GitHub Trending source",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    run(
        dry_run=args.dry_run,
        max_articles=(
            args.max_articles
            or int(os.environ.get("MAX_ARTICLES_PER_RUN", 12))
        ),
        hours_lookback=(
            args.hours_lookback
            or int(os.environ.get("HOURS_LOOKBACK", 48))
        ),
        publish_mode=(
            args.mode
            or os.environ.get("PUBLISH_MODE", "individual")
        ),
        enable_twitter=(
            args.enable_twitter
            or os.environ.get("ENABLE_TWITTER", "").lower() == "true"
        ),
        enable_github=not args.disable_github,
    )
