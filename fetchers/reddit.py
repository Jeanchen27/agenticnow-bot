"""
Reddit 抓取器
使用 Reddit JSON API（公开帖子，无需登录）
"""

import logging
import time
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

REDDIT_HEADERS = {
    "User-Agent": "AgenticNowBot/1.0 (Telegram: @AgenticNow)",
}


def fetch_subreddit(source: dict, hours_lookback: int = 48, limit: int = 25) -> list[dict]:
    """
    抓取 subreddit 的热门帖子。

    Args:
        source: 包含 subreddit、name、category 的信源字典
        hours_lookback: 只返回此时间窗口内的帖子
        limit: 最多抓取帖子数

    Returns:
        文章字典列表
    """
    articles: list[dict] = []
    subreddit = source["subreddit"]
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_lookback)

    try:
        resp = httpx.get(url, headers=REDDIT_HEADERS, timeout=15, follow_redirects=True)

        if resp.status_code != 200:
            logger.warning("[r/%s] HTTP %d", subreddit, resp.status_code)
            return articles

        data = resp.json()
        posts = data.get("data", {}).get("children", [])

        for post in posts:
            p = post["data"]

            # 跳过置顶帖
            if p.get("stickied"):
                continue

            # 跳过评分过低的帖子
            if p.get("score", 0) < 5:
                continue

            # 时间过滤
            created_utc = p.get("created_utc", 0)
            pub_date = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            if pub_date < cutoff:
                continue

            # 外链帖用原始链接，自发帖用 Reddit permalink
            is_self = p.get("is_self", False)
            permalink = f"https://www.reddit.com{p.get('permalink', '')}"
            article_url = permalink if is_self else p.get("url", permalink)

            # 跳过图片/视频帖（非文章内容）
            if article_url.endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webp")):
                continue

            excerpt = ""
            if is_self:
                excerpt = p.get("selftext", "")[:500]

            articles.append(
                {
                    "title": p.get("title", "").strip(),
                    "url": article_url,
                    "source_name": f"r/{subreddit}",
                    "source_id": source["id"],
                    "category": source["category"],
                    "published": pub_date.isoformat(),
                    "excerpt": excerpt,
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
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
