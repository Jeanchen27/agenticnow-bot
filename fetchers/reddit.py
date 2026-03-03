"""
Reddit 抓取器
Reddit 已封锁未授权 JSON API，改用 RSS/Atom 接口
"""

import calendar
import logging
import time
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

logger = logging.getLogger(__name__)

REDDIT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
}


def fetch_subreddit(source: dict, hours_lookback: int = 48, limit: int = 25) -> list[dict]:
    """
    通过 RSS 接口抓取 subreddit 的热门帖子。

    Args:
        source: 包含 subreddit、name、category 的信源字典
        hours_lookback: 只返回此时间窗口内的帖子
        limit: 最多抓取帖子数

    Returns:
        文章字典列表
    """
    articles: list[dict] = []
    subreddit = source["subreddit"]
    url = f"https://www.reddit.com/r/{subreddit}/.rss?sort=hot&limit={limit}"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)

    try:
        resp = httpx.get(url, headers=REDDIT_HEADERS, timeout=15, follow_redirects=True)

        if resp.status_code != 200:
            logger.warning("[r/%s] HTTP %d", subreddit, resp.status_code)
            return articles

        feed = feedparser.parse(resp.content)

        for entry in feed.entries:
            # 解析发布时间
            pub_date = None
            for field in ("published_parsed", "updated_parsed"):
                t = getattr(entry, field, None)
                if t:
                    try:
                        pub_date = datetime.fromtimestamp(
                            calendar.timegm(t), tz=timezone.utc
                        )
                    except Exception:
                        pass
                    break

            if pub_date and pub_date < cutoff:
                continue

            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "")

            # Reddit RSS 的 link 已经是完整 URL
            # 外链帖子的原始链接在 content 里，但解析复杂 → 直接用 reddit 链接
            if not title or not link:
                continue

            # 跳过图片/视频帖
            if link.endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webp")):
                continue

            # 提取摘要（RSS content 是 HTML，简单截取文字）
            excerpt = ""
            content = getattr(entry, "summary", "") or ""
            if content:
                import re
                excerpt = re.sub(r"<[^>]+>", " ", content).strip()[:500]

            articles.append(
                {
                    "title": title,
                    "url": link,
                    "source_name": f"r/{subreddit}",
                    "source_id": source["id"],
                    "category": source["category"],
                    "published": pub_date.isoformat() if pub_date else "",
                    "excerpt": excerpt,
                    "score": 0,
                    "num_comments": 0,
                    "type": "reddit",
                }
            )

        logger.info("[r/%s] %d posts", subreddit, len(articles))

    except Exception as exc:
        logger.error("[r/%s] Error: %s", subreddit, exc)

    return articles


def fetch_reddit_sources(sources: list[dict], hours_lookback: int = 48) -> list[dict]:
    """
    抓取所有 Reddit 信源，请求间隔 2s（避免限速）。
    """
    all_articles: list[dict] = []
    for source in sources:
        articles = fetch_subreddit(source, hours_lookback)
        all_articles.extend(articles)
        time.sleep(2)
    return all_articles
