"""
GitHub Trending 抓取器
过滤出 AI / Agent / LLM 相关的热门开源项目
"""

import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

AI_KEYWORDS = {
    "ai", "agent", "llm", "gpt", "claude", "llama", "langchain",
    "autonomous", "rag", "embedding", "openai", "anthropic", "mcp",
    "multiagent", "copilot", "chatbot", "neural", "transformer",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_github_trending(
    topics: list[str] = None,
    max_items: int = 5,
) -> list[dict]:
    """
    抓取 GitHub Trending 中与 AI/Agent 相关的项目。

    Args:
        topics: 关键词列表（用于过滤，不用于 GitHub API 查询）
        max_items: 最多返回项目数

    Returns:
        文章字典列表（与其他信源格式一致）
    """
    articles: list[dict] = []
    url = "https://github.com/trending?since=daily&spoken_language_code=en"

    try:
        resp = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)

        if resp.status_code != 200:
            logger.warning("[GitHub Trending] HTTP %d", resp.status_code)
            return articles

        soup = BeautifulSoup(resp.text, "html.parser")
        repo_items = soup.find_all("article", class_="Box-row")

        count = 0
        for item in repo_items:
            if count >= max_items:
                break

            # 获取仓库名与 URL
            h2 = item.find("h2")
            if not h2:
                continue
            link = h2.find("a")
            if not link:
                continue

            repo_path = link.get("href", "").strip("/")
            if not repo_path or "/" not in repo_path:
                continue

            repo_url = f"https://github.com/{repo_path}"
            repo_name = repo_path.replace("/", " / ")

            # 获取描述
            desc_elem = item.find("p", class_=lambda x: x and "col-9" in x)
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # 过滤 AI 相关项目
            text_to_check = f"{repo_name} {description}".lower()
            if not any(kw in text_to_check for kw in AI_KEYWORDS):
                continue

            # 获取 star 数
            stars_elem = item.find("a", href=lambda x: x and "/stargazers" in x)
            stars = stars_elem.get_text(strip=True) if stars_elem else "0"

            # 获取今日新增 star 数
            gained_elem = item.find("span", class_=lambda x: x and "d-inline-block" in x)
            gained = ""
            if gained_elem:
                gained_text = gained_elem.get_text(strip=True)
                if "stars today" in gained_text.lower():
                    gained = f"🔥 {gained_text}"

            articles.append(
                {
                    "title": f"GitHub: {repo_name}",
                    "url": repo_url,
                    "source_name": "GitHub Trending",
                    "source_id": "github_trending",
                    "category": "AI Dev",
                    "published": datetime.now(timezone.utc).isoformat(),
                    "excerpt": f"{description} | ⭐ {stars} {gained}".strip(),
                    "type": "github",
                }
            )
            count += 1

        logger.info("[GitHub Trending] %d AI repos found", len(articles))

    except Exception as exc:
        logger.error("[GitHub Trending] Error: %s", exc)

    return articles
