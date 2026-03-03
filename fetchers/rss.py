"""
RSS / Atom Feed 抓取器
支持 Substack、Ghost、WordPress 等主流 RSS 格式
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "AgenticNowBot/1.0 (Telegram: @AgenticNow; "
        "+https://t.me/AgenticNow)"
    ),
    "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
}


def _parse_date(entry) -> Optional[datetime]:
    """从 feed entry 解析发布时间，返回 timezone-aware datetime。"""
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, field, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _get_excerpt(entry) -> str:
    """提取文章摘要文本（最多500字符）。"""
    for attr in ("summary", "description"):
        text = getattr(entry, attr, None)
        if text:
            # Strip basic HTML tags for cleaner text
            import re
            clean = re.sub(r"<[^>]+>", " ", text)
            clean = re.sub(r"\s+", " ", clean).strip()
            return clean[:500]
    if hasattr(entry, "content") and entry.content:
        import re
        text = entry.content[0].get("value", "")
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:500]
    return ""


def fetch_single_rss(source: dict, hours_lookback: int = 48) -> list[dict]:
    """
    抓取单个 RSS 源的最新文章。

    Args:
        source: 信源配置字典（含 rss、name、category 等字段）
        hours_lookback: 只抓取此时间窗口内发布的文章

    Returns:
        文章字典列表
    """
    articles: list[dict] = []
    rss_url = source.get("rss", "")
    if not rss_url:
        return articles

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)

    try:
        resp = httpx.get(rss_url, headers=HEADERS, timeout=15, follow_redirects=True)

        if resp.status_code != 200:
            logger.warning(
                "[%s] HTTP %d for %s", source["name"], resp.status_code, rss_url
            )
            return articles

        feed = feedparser.parse(resp.text)

        if feed.bozo and not feed.entries:
            logger.warning(
                "[%s] Feed parse error: %s", source["name"], feed.bozo_exception
            )
            return articles

        for entry in feed.entries[:30]:  # 最多取30条，避免过多处理
            pub_date = _parse_date(entry)

            # 若能解析日期则做时间过滤；若无日期则保留（保守策略）
            if pub_date and pub_date < cutoff:
                continue

            url = entry.get("link", "").strip()
            if not url:
                continue

            articles.append(
                {
                    "title": entry.get("title", "").strip(),
                    "url": url,
                    "source_name": source["name"],
                    "source_id": source["id"],
                    "category": source["category"],
                    "published": pub_date.isoformat() if pub_date else None,
                    "excerpt": _get_excerpt(entry),
                    "type": "rss",
                }
            )

        logger.info("[%s] %d articles", source["name"], len(articles))

    except httpx.TimeoutException:
        logger.warning("[%s] Timeout: %s", source["name"], rss_url)
    except Exception as exc:
        logger.error("[%s] Error: %s", source["name"], exc)

    return articles


def fetch_rss_sources(sources: list[dict], hours_lookback: int = 48) -> list[dict]:
    """
    抓取所有 RSS 信源，返回合并后的文章列表。
    每个请求间隔 0.5s，避免对服务器造成压力。
    """
    all_articles: list[dict] = []
    for source in sources:
        articles = fetch_single_rss(source, hours_lookback)
        all_articles.extend(articles)
        time.sleep(0.5)
    return all_articles
