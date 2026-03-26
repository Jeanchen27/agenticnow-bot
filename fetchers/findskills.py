"""
findskills.org API 抓取器
支持语义搜索和批量拉取，覆盖三类用户画像的 Skill 候选池
"""

import logging
import time
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://findskills.org/api"
RATE_LIMIT_DELAY = 1.1  # 60次/分钟 → 每次间隔 1.1s 保险

HEADERS = {
    "User-Agent": "AgenticNow-SkillBot/1.0",
    "Accept": "application/json",
}

# 三类用户画像搜索词
QUERIES = {
    "上班族": [
        "summarize meeting notes",
        "write report email",
        "document pdf analysis",
        "productivity workflow",
    ],
    "个体从业者": [
        "xiaohongshu content",
        "social media copywriting",
        "wechat marketing",
        "viral content creation",
    ],
    "小企业主": [
        "crm customer automation",
        "sales workflow",
        "data analysis spreadsheet",
        "business intelligence",
    ],
}


def _get(path: str, params: dict = None, retries: int = 2):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        try:
            resp = httpx.get(url, params=params, headers=HEADERS, timeout=20, follow_redirects=True)
            if resp.status_code == 200:
                return resp.json()
            logger.warning("findskills.org %s → HTTP %d", path, resp.status_code)
        except httpx.TimeoutException:
            logger.warning("findskills.org timeout (attempt %d): %s", attempt + 1, path)
        except Exception as exc:
            logger.error("findskills.org error: %s", exc)
        if attempt < retries:
            time.sleep(3)
    return None


def _normalize(raw: dict, persona: str = "") -> dict:
    """将 findskills.org 返回的 skill 字典标准化为内部格式。"""
    updated_at = raw.get("updated_at") or raw.get("created_at", "")
    return {
        "id": raw.get("id") or raw.get("skill_id", ""),
        "name": raw.get("name", ""),
        "description": raw.get("description", ""),
        "tags": raw.get("tags", []),
        "source": raw.get("source", "findskills"),
        "url": raw.get("url") or raw.get("repository_url", ""),
        "stars": int(raw.get("stars", 0) or 0),
        "installs": int(raw.get("installs", 0) or raw.get("downloads", 0) or 0),
        "updated_at": updated_at,
        "quality_score": float(raw.get("quality_score", 0) or 0),
        "safety_score": float(raw.get("safety_score", 0) or 0),
        "safety_tier": raw.get("safety_tier", "unknown"),
        "has_license": bool(raw.get("quality", {}).get("has_license") if isinstance(raw.get("quality"), dict) else raw.get("has_license")),
        "persona_hint": persona,
        "_raw": raw,
    }


def search_by_query(query: str, persona: str, max_results: int = 20) -> list[dict]:
    """用语义搜索抓取 Skill。"""
    data = _get("/search", params={"q": query, "limit": max_results})
    if not data:
        return []

    items = data if isinstance(data, list) else data.get("results", data.get("skills", []))
    results = [_normalize(item, persona) for item in items if isinstance(item, dict)]
    logger.info("findskills search '%s' → %d skills", query, len(results))
    time.sleep(RATE_LIMIT_DELAY)
    return results


def fetch_batch(
    category: str = "",
    min_safety: int = 50,
    sort: str = "quality",
    limit: int = 50,
    persona: str = "",
) -> list[dict]:
    """批量拉取高质量 Skill。"""
    params = {"sort": sort, "limit": limit}
    if category:
        params["category"] = category
    if min_safety:
        params["min_safety"] = min_safety

    data = _get("/v1/skills", params=params)
    if not data:
        return []

    items = data if isinstance(data, list) else data.get("skills", data.get("results", []))
    results = [_normalize(item, persona) for item in items if isinstance(item, dict)]
    logger.info("findskills batch category='%s' → %d skills", category, len(results))
    time.sleep(RATE_LIMIT_DELAY)
    return results


def fetch_all_personas(max_per_query: int = 15) -> list[dict]:
    """
    遍历三类用户画像的所有搜索词，返回合并后的候选 Skill 列表。
    同一 id 会保留（去重在 pipeline 层处理）。
    """
    all_skills: list[dict] = []

    for persona, queries in QUERIES.items():
        for q in queries:
            skills = search_by_query(q, persona=persona, max_results=max_per_query)
            all_skills.extend(skills)

    # 补充批量拉取（按分类）
    for category in ["productivity", "content", "automation", "data", "communication"]:
        skills = fetch_batch(category=category, min_safety=50, limit=30)
        all_skills.extend(skills)

    logger.info("findskills total fetched (before dedup): %d", len(all_skills))
    return all_skills
