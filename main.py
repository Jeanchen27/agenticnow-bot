#!/usr/bin/env python3
"""
AgenticNow Daily Bot
━━━━━━━━━━━━━━━━━━━
每日自动抓取 RSS / Podcast / Reddit / GitHub 信源，
通过 Claude API 生成中文标题+摘要，
推送至 @AgenticNow Telegram 频道。

用法:
    python main.py                     # 正式运行
    python main.py --dry-run           # 预览模式（不推送 Telegram）
    python main.py --max-articles 12   # 自定义最多推送文章数
    python main.py --mode digest       # 每日合集模式
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
from sources import RSS_SOURCES, REDDIT_SOURCES, GITHUB_TOPICS
from fetchers.rss import fetch_rss_sources
from fetchers.reddit import fetch_reddit_sources
from fetchers.github_trending import fetch_github_trending
from sources import RSS_SOURCES as _RSS_SOURCES

# 建立 source_id → min_relevance 映射（供最终过滤用）
_MIN_RELEVANCE_BY_SOURCE: dict[str, int] = {
    s["id"]: s["min_relevance"]
    for s in _RSS_SOURCES
    if "min_relevance" in s
}
from processor.summarizer import summarize_articles
from publisher.telegram import TelegramPublisher
from storage.dedup import URLStore


# ─── 来源配额配置 ─────────────────────────────────────────────────────────────
# 保底名额：确保每种来源类型在最终推送中有最少占比
SOURCE_QUOTAS = {
    "newsletter": 4,   # 至少 4 条 Newsletter
    "podcast":    2,   # 至少 2 条 Podcast
    "github":     1,   # 至少 1 个 GitHub 项目
    # reddit 不设保底，填满剩余名额
}


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def _score_article(article: dict) -> float:
    """
    对文章打分，用于预排序（在调用 Claude 之前）。
    分数越高 = 优先处理。
    """
    score = 0.0
    article_type = article.get("type", "rss")

    # Newsletter / Podcast 基础加分（确保不被 Reddit 数量淹没）
    if article_type in ("newsletter", "podcast"):
        score += 5.0
    elif article_type == "github":
        score += 3.0

    # Reddit 热度加分
    if article_type == "reddit":
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


def _is_similar_title(title_a: str, title_b: str) -> bool:
    """
    判断两个标题是否描述同一新闻。
    使用简单的词集重叠率（Jaccard 系数），阈值 0.4。
    """
    if not title_a or not title_b:
        return False
    # 统一小写，取中文标题或英文标题
    words_a = set(title_a.lower().split())
    words_b = set(title_b.lower().split())
    if not words_a or not words_b:
        return False
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union) >= 0.4


def _dedup_by_title(articles: list[dict]) -> list[dict]:
    """
    标题级去重：同一新闻被多个信源报道时，只保留 relevance 最高的那条。
    """
    result: list[dict] = []
    for art in articles:
        title = art.get("title_zh") or art.get("title", "")
        is_dup = False
        for existing in result:
            existing_title = existing.get("title_zh") or existing.get("title", "")
            if _is_similar_title(title, existing_title):
                # 保留评分更高的那条
                if art.get("relevance", 5) > existing.get("relevance", 5):
                    result.remove(existing)
                    result.append(art)
                is_dup = True
                break
        if not is_dup:
            result.append(art)
    return result


def _apply_quotas(articles: list[dict], max_articles: int) -> list[dict]:
    """
    按来源配额选取最终推送文章。

    策略：
    0. 先做标题级去重（同一新闻多源报道只保留一条）
    1. 先为每种类型按配额取保底名额（按 relevance 排序取 top N）
    2. 剩余名额从所有未选文章中按 relevance 排序填满
    3. 最终按 类型分组顺序 + relevance 排序输出
    """
    # 0. 标题去重
    articles = _dedup_by_title(articles)

    # 0b. 对设有 min_relevance 的信源（Bankless/Decrypt）强制过滤低分文章
    if _MIN_RELEVANCE_BY_SOURCE:
        articles = [
            a for a in articles
            if a.get("relevance", 5) >= _MIN_RELEVANCE_BY_SOURCE.get(
                a.get("source_id", ""), 0
            )
        ]

    # 按类型分组
    by_type: dict[str, list[dict]] = {}
    for art in articles:
        t = art.get("type", "rss")
        by_type.setdefault(t, []).append(art)

    # 每组按 relevance 降序
    for t in by_type:
        by_type[t].sort(key=lambda x: x.get("relevance", 5), reverse=True)

    selected: list[dict] = []
    selected_urls: set[str] = set()

    # 1. 按配额取保底
    for source_type, quota in SOURCE_QUOTAS.items():
        candidates = by_type.get(source_type, [])
        count = 0
        for art in candidates:
            if count >= quota:
                break
            url = art.get("url", "")
            if url not in selected_urls:
                selected.append(art)
                selected_urls.add(url)
                count += 1

    # 2. 剩余名额按 relevance 从所有未选文章中填满
    remaining = max_articles - len(selected)
    if remaining > 0:
        all_remaining = sorted(
            [a for a in articles if a.get("url", "") not in selected_urls],
            key=lambda x: x.get("relevance", 5),
            reverse=True,
        )
        for art in all_remaining[:remaining]:
            selected.append(art)
            selected_urls.add(art.get("url", ""))

    # 3. 按类型分组排序：newsletter → podcast → reddit → github
    type_order = {"newsletter": 0, "podcast": 1, "rss": 2, "reddit": 3, "github": 4}
    selected.sort(
        key=lambda x: (
            type_order.get(x.get("type", "rss"), 9),
            -x.get("relevance", 5),
        )
    )

    return selected[:max_articles]


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def run(
    dry_run: bool = False,
    max_articles: int = 12,
    hours_lookback_rss: int = 168,
    hours_lookback_reddit: int = 48,
    publish_mode: str = "individual",
    enable_github: bool = True,
) -> None:
    """
    AgenticNow Bot 主流程。

    1. 抓取所有信源（RSS/Podcast + Reddit + GitHub）
    2. 过滤已发送 URL
    3. 预选候选文章
    4. Claude API 生成中文摘要
    5. 按配额 + 相关度排序，取 top N
    6. 推送至 Telegram（按 Newsletter → Podcast → Reddit 分组）
    7. 标记 URL 为已发送并保存
    """
    logger.info("=" * 56)
    logger.info("  🤖  AgenticNow Bot  |  %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    logger.info("  Max articles : %d  |  RSS lookback : %dh  |  Reddit lookback : %dh",
                max_articles, hours_lookback_rss, hours_lookback_reddit)
    logger.info("  Mode : %s  |  %s", publish_mode, "DRY RUN" if dry_run else "LIVE")
    logger.info("=" * 56)

    # ── 读取环境变量 ──────────────────────────────────────────────────────────
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_channel = os.environ.get("TELEGRAM_CHANNEL_ID", "@AgenticNow")

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

    # 1. RSS + Podcast（主力信源，7天窗口捕获周刊）
    logger.info("📡 Fetching RSS/Podcast sources (%d sources)...", len(RSS_SOURCES))
    rss_articles = fetch_rss_sources(RSS_SOURCES, hours_lookback=hours_lookback_rss)
    logger.info("   → %d articles", len(rss_articles))
    all_articles.extend(rss_articles)

    # 2. Reddit（48h 窗口，社区热点）
    logger.info("📡 Fetching Reddit sources (%d subreddits)...", len(REDDIT_SOURCES))
    reddit_articles = fetch_reddit_sources(REDDIT_SOURCES, hours_lookback=hours_lookback_reddit)
    logger.info("   → %d posts", len(reddit_articles))
    all_articles.extend(reddit_articles)

    # 3. GitHub Trending（可关闭）
    if enable_github:
        logger.info("📡 Fetching GitHub Trending...")
        github_articles = fetch_github_trending(topics=GITHUB_TOPICS, max_items=5)
        logger.info("   → %d repos", len(github_articles))
        all_articles.extend(github_articles)

    logger.info("📊 Total fetched: %d articles", len(all_articles))

    # ── 去重过滤 ──────────────────────────────────────────────────────────────
    new_articles = url_store.filter_new(all_articles)
    if not new_articles:
        logger.info("✅ No new articles found. Nothing to publish today.")
        return

    # ── 预选候选文章（2× 目标数量，留给 Claude 评分空间）──────────────────────
    candidates = _preselect(new_articles, n=max_articles * 3)
    logger.info("🎯 Pre-selected %d candidates for summarization", len(candidates))

    # ── Claude 摘要生成 ───────────────────────────────────────────────────────
    logger.info("🧠 Generating Chinese summaries via Claude API...")
    enriched = summarize_articles(candidates, api_key=anthropic_api_key)

    # ── 按配额 + 相关度选取最终文章 ──────────────────────────────────────────
    final_articles = _apply_quotas(enriched, max_articles)

    logger.info("📋 Final selection: %d articles", len(final_articles))
    for i, a in enumerate(final_articles, 1):
        title = a.get("title_zh") or a.get("title", "")
        logger.info(
            "   %d. [%s] [%s/10] %s",
            i,
            a.get("type", "?"),
            a.get("relevance", "?"),
            title[:55],
        )

    # ── 预览 / 推送 ───────────────────────────────────────────────────────────
    if dry_run:
        logger.info("\n🔍 DRY RUN — 消息预览：")
        logger.info("=" * 56)
        dummy = TelegramPublisher("dummy_token", "@AgenticNow")
        if publish_mode == "digest":
            print(dummy.format_digest(final_articles))
        else:
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
        help="Override RSS lookback window in hours (default: 168 = 7 days)",
    )
    p.add_argument(
        "--mode",
        choices=["individual", "digest"],
        default=None,
        help="Publish mode: 'individual' (one post per article) or 'digest' (daily summary)",
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
        hours_lookback_rss=(
            args.hours_lookback
            or int(os.environ.get("HOURS_LOOKBACK_RSS", 168))
        ),
        hours_lookback_reddit=int(os.environ.get("HOURS_LOOKBACK_REDDIT", 48)),
        publish_mode=(
            args.mode
            or os.environ.get("PUBLISH_MODE", "digest")
        ),
        enable_github=not args.disable_github,
    )
