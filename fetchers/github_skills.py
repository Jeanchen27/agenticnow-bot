"""
GitHub 中文场景 Skill 专项搜索
补充 findskills.org 覆盖盲区，抓取国内开发者发布的垂直场景 Skill
"""

import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com/search/repositories"
RATE_LIMIT_DELAY = 2.0  # GitHub 未认证：10次/分钟

HEADERS = {
    "User-Agent": "AgenticNow-SkillBot/1.0",
    "Accept": "application/vnd.github+json",
}

# 中文场景关键词 → 对应用户画像
CHINESE_QUERIES = [
    ("SKILL.md xiaohongshu", "个体从业者"),
    ("SKILL.md wechat", "个体从业者"),
    ("SKILL.md feishu", "小企业主"),
    ("SKILL.md 中文 agent", "上班族"),
    ("SKILL.md dingtalk", "小企业主"),
    ("SKILL.md 周报 meeting", "上班族"),
]


def _normalize_repo(repo: dict, persona: str) -> dict:
    """将 GitHub repo 格式标准化为内部 Skill 格式。"""
    pushed_at = repo.get("pushed_at", repo.get("updated_at", ""))
    return {
        "id": f"github-{repo['full_name'].replace('/', '-')}",
        "name": repo.get("name", ""),
        "description": repo.get("description", "") or "",
        "tags": repo.get("topics", []),
        "source": "github",
        "url": repo.get("html_url", ""),
        "stars": int(repo.get("stargazers_count", 0) or 0),
        "installs": 0,  # GitHub 无 installs 数据
        "updated_at": pushed_at,
        "quality_score": 0.0,
        "safety_score": 60.0,  # GitHub 公开项目默认中等可信度
        "safety_tier": "community",
        "has_license": repo.get("license") is not None,
        "persona_hint": persona,
        "_raw": repo,
    }


def search_github_skills(
    query: str,
    persona: str,
    per_page: int = 20,
    github_token: str = "",
) -> list[dict]:
    """搜索 GitHub 上包含 SKILL.md 的中文场景仓库。"""
    headers = dict(HEADERS)
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    }

    try:
        resp = httpx.get(GITHUB_API, params=params, headers=headers, timeout=20)
        if resp.status_code == 403:
            logger.warning("GitHub rate limit hit, skipping '%s'", query)
            return []
        if resp.status_code != 200:
            logger.warning("GitHub API %d for '%s'", resp.status_code, query)
            return []

        data = resp.json()
        items = data.get("items", [])
        results = [_normalize_repo(repo, persona) for repo in items]
        logger.info("GitHub search '%s' → %d repos", query, len(results))
        return results

    except Exception as exc:
        logger.error("GitHub search error: %s", exc)
        return []
    finally:
        time.sleep(RATE_LIMIT_DELAY)


def fetch_chinese_skills(github_token: str = "") -> list[dict]:
    """
    遍历所有中文场景关键词，返回合并后的候选 Skill 列表。
    """
    if not github_token:
        github_token = os.environ.get("GITHUB_TOKEN", "")

    all_skills: list[dict] = []
    for query, persona in CHINESE_QUERIES:
        skills = search_github_skills(query, persona=persona, github_token=github_token)
        all_skills.extend(skills)

    logger.info("GitHub Chinese skills total: %d", len(all_skills))
    return all_skills
