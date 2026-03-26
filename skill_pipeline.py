#!/usr/bin/env python3
"""
skill_pipeline.py — AgenticNow Skill 推荐筛选流水线

七步流程：
  1. 抓取：findskills.org API + GitHub 中文场景专项搜索
  2. 安全初筛：caution tier 丢弃 / 硬编码密钥检测 / 黑名单过滤
  3. 用户画像匹配：按三类用户关键词过滤
  4. Claude API 中文友好度评分
  5. 综合评分排序，取 Top 20，SQLite/JSON 去重
  6. Telegram 推送审核卡片至 AgenticNow 频道
  7. 人工实测（自动化不处理）

用法：
    python skill_pipeline.py                 # 正式推送
    python skill_pipeline.py --dry-run       # 预览，不推送 Telegram
    python skill_pipeline.py --top 10        # 只取 Top 10
    python skill_pipeline.py --no-github     # 不抓 GitHub 补充源
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agenticnow.skill_pipeline")

sys.path.insert(0, os.path.dirname(__file__))

from fetchers.findskills import fetch_all_personas
from fetchers.github_skills import fetch_chinese_skills
from storage.dedup import URLStore

# ─── 常量 ─────────────────────────────────────────────────────────────────────

SKILL_STORE_PATH = "seen_skill_ids.json"

# 安全黑名单（已知恶意 Skill 来源）
BLACKLIST_NAMES = {
    "capability-evolver",
    "evomap",
}

# 硬编码密钥 pattern
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9\-_]{20,}", re.IGNORECASE),
    re.compile(r"password\s*=\s*['\"][^'\"]{6,}['\"]", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*=\s*['\"][^'\"]{10,}['\"]", re.IGNORECASE),
]

# 向外发送数据 pattern（curl+webhook 组合）
EXFIL_PATTERNS = [
    re.compile(r"curl.*webhook", re.IGNORECASE | re.DOTALL),
    re.compile(r"curl.*discord\.com/api/webhooks", re.IGNORECASE),
]

# 用户画像关键词（用于匹配 name + description + tags）
PERSONA_KEYWORDS = {
    "上班族": {
        "summarize", "meeting", "report", "email", "pdf", "pptx",
        "document", "writing", "notes", "recap", "draft", "memo",
        "calendar", "schedule", "productivity", "workflow",
    },
    "个体从业者": {
        "xiaohongshu", "content", "social", "media", "copywriting",
        "viral", "marketing", "wechat", "instagram", "tiktok",
        "douyin", "blog", "newsletter", "creator", "posting",
    },
    "小企业主": {
        "crm", "automation", "workflow", "data", "excel", "customer",
        "sales", "integration", "invoice", "feishu", "dingtalk",
        "spreadsheet", "business", "intelligence", "pipeline",
    },
}

# Claude API 中文友好度评分 Prompt
CHINA_JUDGE_PROMPT = """分析这个 Skill，从国内用户视角评分，返回 JSON（不要有其他文字）：
{{
  "china_network_ok": true/false,
  "no_foreign_api_required": true/false,
  "chinese_prompt_works": true/false,
  "target_persona": "上班族|个体从业者|小企业主|开发者",
  "one_line_cn": "用中文一句话说这个Skill能帮你做什么",
  "install_cmd": "最简安装命令，如 clawhub install xxx",
  "china_score": 0到20的整数
}}

Skill信息：
- 名称：{name}
- 描述：{description}
- 标签：{tags}
- 来源：{source}
"""


# ─── Step 1: 抓取 ─────────────────────────────────────────────────────────────

def fetch_candidates(enable_github: bool = True) -> list[dict]:
    logger.info("Step 1: 抓取 Skill 候选池...")
    skills = fetch_all_personas()

    if enable_github:
        github_token = os.environ.get("GITHUB_TOKEN", "")
        gh_skills = fetch_chinese_skills(github_token=github_token)
        skills.extend(gh_skills)

    logger.info("候选池总量（去重前）: %d", len(skills))
    return skills


# ─── Step 2: 安全初筛 ─────────────────────────────────────────────────────────

def _has_secrets(skill: dict) -> bool:
    text = f"{skill.get('name','')} {skill.get('description','')} {' '.join(skill.get('tags',[]))}"
    return any(p.search(text) for p in SECRET_PATTERNS)


def _has_exfil(skill: dict) -> bool:
    text = f"{skill.get('name','')} {skill.get('description','')}"
    return any(p.search(text) for p in EXFIL_PATTERNS)


def safety_filter(skills: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    返回 (通过列表, 高风险列表)。
    caution tier 和黑名单直接丢弃（不进入高风险列表）。
    """
    passed, high_risk = [], []

    for skill in skills:
        name_lower = skill.get("name", "").lower()

        # 黑名单直接丢弃
        if any(b in name_lower for b in BLACKLIST_NAMES):
            logger.info("BLACKLIST 丢弃: %s", skill["name"])
            continue

        # caution tier 直接丢弃
        if skill.get("safety_tier") == "caution":
            logger.info("CAUTION 丢弃: %s", skill["name"])
            continue

        # 硬编码密钥 → 高风险
        if _has_secrets(skill):
            skill["risk_flag"] = "hardcoded_secrets"
            high_risk.append(skill)
            continue

        # 向外发送数据 → 高风险
        if _has_exfil(skill):
            skill["risk_flag"] = "exfiltration"
            high_risk.append(skill)
            continue

        passed.append(skill)

    logger.info("安全初筛: %d 通过 / %d 高风险 / %d 丢弃",
                len(passed), len(high_risk),
                len(skills) - len(passed) - len(high_risk))
    return passed, high_risk


# ─── Step 3: 用户画像匹配 ─────────────────────────────────────────────────────

def _skill_text(skill: dict) -> str:
    return " ".join([
        skill.get("name", ""),
        skill.get("description", ""),
        " ".join(skill.get("tags", [])),
    ]).lower()


def persona_match(skills: list[dict]) -> list[dict]:
    """
    只保留至少匹配一类用户画像的 Skill，并填充 matched_personas 字段。
    """
    matched = []
    for skill in skills:
        text = _skill_text(skill)
        personas = []
        for persona, keywords in PERSONA_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                personas.append(persona)

        # persona_hint 来自抓取阶段，也算匹配
        hint = skill.get("persona_hint", "")
        if hint and hint not in personas:
            personas.append(hint)

        if personas:
            skill["matched_personas"] = personas
            matched.append(skill)

    logger.info("用户画像匹配: %d/%d 通过", len(matched), len(skills))
    return matched


# ─── Step 4: Claude API 中文友好度评分 ────────────────────────────────────────

def score_china_friendliness(skills: list[dict], api_key: str) -> list[dict]:
    """
    批量调用 Claude API，为每个 Skill 打中文友好度分。
    失败时 china_score 默认 5（中性），不阻断流水线。
    """
    client_url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    for i, skill in enumerate(skills):
        prompt = CHINA_JUDGE_PROMPT.format(
            name=skill.get("name", ""),
            description=skill.get("description", "")[:300],
            tags=", ".join(skill.get("tags", [])[:10]),
            source=skill.get("source", ""),
        )

        payload = {
            "model": "claude-haiku-4-5-20251001",  # 省 token，haiku 够用
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            resp = httpx.post(client_url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["content"][0]["text"].strip()
                # 提取 JSON（有时 Claude 会在前后加注释）
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    skill["china_judge"] = parsed
                    skill["china_score"] = int(parsed.get("china_score", 5))
                    skill["one_line_cn"] = parsed.get("one_line_cn", "")
                    skill["install_cmd"] = parsed.get("install_cmd", f"clawhub install {skill.get('name','')}")
                    skill["target_persona"] = parsed.get("target_persona", "")
                    skill["china_network_ok"] = parsed.get("china_network_ok", False)
                    skill["no_foreign_api"] = parsed.get("no_foreign_api_required", False)
                    skill["chinese_prompt_works"] = parsed.get("chinese_prompt_works", False)
                else:
                    skill["china_score"] = 5
            else:
                logger.warning("Claude API %d for skill '%s'", resp.status_code, skill["name"])
                skill["china_score"] = 5
        except Exception as exc:
            logger.warning("China score error for '%s': %s", skill["name"], exc)
            skill["china_score"] = 5

        if (i + 1) % 10 == 0:
            logger.info("  中文评分进度: %d/%d", i + 1, len(skills))
        time.sleep(0.5)  # 避免过快触发限速

    return skills


# ─── Step 5: 综合评分、去重、Top N ────────────────────────────────────────────

def _freshness_score(updated_at: str) -> int:
    if not updated_at:
        return 0
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - dt
        if age <= timedelta(days=7):
            return 20
        if age <= timedelta(days=30):
            return 15
        if age <= timedelta(days=90):
            return 8
        return 0
    except Exception:
        return 0


def compute_scores(skills: list[dict]) -> list[dict]:
    for skill in skills:
        # 热度（满30分）
        star_score = min(skill.get("stars", 0) / 100, 15)   # 1500星 → 满15分
        install_score = min(skill.get("installs", 0) / 200, 15)  # 3000次 → 满15分
        popularity = star_score + install_score

        # 新鲜度（满20分）
        freshness = _freshness_score(skill.get("updated_at", ""))

        # 可信度（满30分）：复用 safety_score（0-100 → 0-30）
        trust = skill.get("safety_score", 50) * 0.3

        # 中文友好度（满20分）
        china = skill.get("china_score", 5)

        total = round(popularity + freshness + trust + china, 1)
        skill["score_breakdown"] = {
            "popularity": round(popularity, 1),
            "freshness": freshness,
            "trust": round(trust, 1),
            "china": china,
            "total": total,
        }
        skill["total_score"] = total

    return skills


def dedup_and_rank(skills: list[dict], store: URLStore, top_n: int = 20) -> list[dict]:
    """去重 + 排序 + 取 Top N。"""
    # id 去重（同一 id 保留评分最高的）
    seen_ids: dict[str, dict] = {}
    for skill in skills:
        sid = skill.get("id", skill.get("url", skill.get("name", "")))
        if sid not in seen_ids or skill.get("total_score", 0) > seen_ids[sid].get("total_score", 0):
            seen_ids[sid] = skill

    unique = list(seen_ids.values())

    # 用 URLStore 过滤已推送过的 Skill
    new_skills = store.filter_new([{**s, "url": s.get("id", s.get("url", ""))} for s in unique])

    # 按综合评分降序
    ranked = sorted(new_skills, key=lambda s: s.get("total_score", 0), reverse=True)

    selected = ranked[:top_n]
    logger.info("去重排序: %d unique → %d new → Top %d 选出 %d",
                len(unique), len(new_skills), top_n, len(selected))
    return selected


# ─── Step 6: Telegram 审核卡片 ────────────────────────────────────────────────

def _icon(skill: dict) -> str:
    score = skill.get("total_score", 0)
    if score >= 70:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


def format_review_card(skill: dict) -> str:
    """生成 Telegram HTML 格式的审核卡片（与规格文档格式一致）。"""
    name = skill.get("name", "unknown")
    one_line = skill.get("one_line_cn") or skill.get("description", "")[:60]
    personas = skill.get("matched_personas", [skill.get("target_persona", "通用")])
    persona_str = " > ".join(personas[:2])
    safety_tier = skill.get("safety_tier", "unknown")
    safety_score = int(skill.get("safety_score", 0))
    quality_score = int(skill.get("quality_score", 0))
    install_cmd = skill.get("install_cmd") or f"clawhub install {name}"
    url = skill.get("url", "")
    breakdown = skill.get("score_breakdown", {})

    # 三个中文友好度标志
    cn_net = "✅" if skill.get("china_network_ok") else "❓"
    cn_key = "✅" if skill.get("no_foreign_api") else "❓"
    cn_prompt = "✅" if skill.get("chinese_prompt_works") else "❓"

    def esc(t: str) -> str:
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lines = [
        f"{_icon(skill)} <b>{esc(name)}</b>",
        f"{esc(one_line)}",
        "",
        f"适合人群：{esc(persona_str)}",
        f"安全评级：{esc(safety_tier)} ({safety_score}/100)",
        f"质量评分：{quality_score}/100",
        f"综合评分：{breakdown.get('total', 0):.0f}/100",
        f"国内可用：{cn_net}  无需境外Key：{cn_key}  中文可触发：{cn_prompt}",
        "",
        f"安装：<code>{esc(install_cmd)}</code>",
    ]

    if url:
        lines.append(f'来源：<a href="{url}">{esc(url[:60])}</a>')

    lines += [
        "",
        "<b>⚠️ 人工测试项：</b>",
        "□ 中文 prompt 触发测试",
        "□ 国内网络连通测试",
        "□ 实际发布效果 + 封号风险评估",
    ]

    return "\n".join(lines)


def push_to_telegram(
    skills: list[dict],
    bot_token: str,
    channel_id: str,
    dry_run: bool = False,
) -> int:
    """将审核卡片逐条推送到 Telegram 频道。"""
    api_base = f"https://api.telegram.org/bot{bot_token}"
    published = 0

    # 先发一条汇总头
    date_str = datetime.now().strftime("%Y年%m月%d日")
    header = (
        f"🤖 <b>AgenticNow · Skill 推荐审核清单</b>\n"
        f"📅 {date_str}  共 {len(skills)} 个候选\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"以下每张卡片请人工判断是否进入实测 ↓"
    )

    if dry_run:
        logger.info("[DRY RUN] 汇总头:\n%s", header)
    else:
        _tg_send(api_base, channel_id, header)
        time.sleep(2)

    for skill in skills:
        card = format_review_card(skill)
        if dry_run:
            logger.info("[DRY RUN] 卡片:\n%s\n---", card)
            published += 1
        else:
            result = _tg_send(api_base, channel_id, card)
            if result.get("ok"):
                published += 1
                logger.info("✅ 推送: %s (%.0f分)", skill.get("name"), skill.get("total_score", 0))
            else:
                logger.error("❌ 推送失败: %s", skill.get("name"))
            time.sleep(3)

    return published


def _tg_send(api_base: str, channel_id: str, text: str) -> dict:
    url = f"{api_base}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    for attempt in range(3):
        try:
            resp = httpx.post(url, json=payload, timeout=15)
            result = resp.json()
            if result.get("ok"):
                return result
            desc = result.get("description", "")
            logger.warning("TG error (attempt %d): %s", attempt + 1, desc)
            if "Too Many Requests" in desc:
                retry_after = result.get("parameters", {}).get("retry_after", 30)
                time.sleep(retry_after)
            else:
                break
        except httpx.TimeoutException:
            time.sleep(5)
        except Exception as exc:
            logger.error("TG send error: %s", exc)
            break
    return {"ok": False}


# ─── 主流水线 ──────────────────────────────────────────────────────────────────

def run(
    dry_run: bool = False,
    top_n: int = 20,
    enable_github: bool = True,
    store_path: str = SKILL_STORE_PATH,
) -> dict:
    started_at = datetime.now(timezone.utc)
    logger.info("═" * 60)
    logger.info("  🤖  AgenticNow Skill Pipeline  |  %s", started_at.strftime("%Y-%m-%d %H:%M UTC"))
    logger.info("  top_n=%d  %s", top_n, "DRY RUN" if dry_run else "LIVE")
    logger.info("═" * 60)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    tg_channel = os.environ.get("TELEGRAM_CHANNEL_ID", "@AgenticNow")

    if not api_key:
        logger.error("ANTHROPIC_API_KEY 未设置，退出。")
        sys.exit(1)
    if not dry_run and not tg_token:
        logger.error("TELEGRAM_BOT_TOKEN 未设置（正式模式需要），退出。")
        sys.exit(1)

    store = URLStore(store_path)

    # Step 1
    candidates = fetch_candidates(enable_github=enable_github)

    # Step 2
    passed, high_risk = safety_filter(candidates)
    logger.info("高风险（人工复核）: %d 个", len(high_risk))

    # Step 3
    matched = persona_match(passed)

    # Step 4
    logger.info("Step 4: Claude API 中文友好度评分（共 %d 个）...", len(matched))
    scored = score_china_friendliness(matched, api_key)

    # Step 5
    scored = compute_scores(scored)
    selected = dedup_and_rank(scored, store, top_n=top_n)

    # Step 6
    logger.info("Step 6: 推送 %d 张审核卡片 → %s", len(selected), tg_channel)
    published = push_to_telegram(selected, tg_token, tg_channel, dry_run=dry_run)

    # 标记已推送
    if not dry_run:
        for skill in selected:
            store.mark_seen(skill.get("id") or skill.get("url") or skill.get("name", ""))
        store.save()

    logger.info("═" * 60)
    logger.info("  完成：推送 %d/%d 张卡片", published, len(selected))
    logger.info("═" * 60)

    return {
        "started_at": started_at.isoformat(),
        "dry_run": dry_run,
        "candidates_fetched": len(candidates),
        "safety_passed": len(passed),
        "high_risk": len(high_risk),
        "persona_matched": len(matched),
        "selected": len(selected),
        "published": published,
        "skills": [
            {
                "name": s.get("name"),
                "score": s.get("total_score"),
                "personas": s.get("matched_personas", []),
                "china_score": s.get("china_score"),
                "one_line_cn": s.get("one_line_cn"),
            }
            for s in selected
        ],
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="AgenticNow Skill 推荐筛选流水线")
    p.add_argument("--dry-run", action="store_true", help="预览模式，不推送 Telegram")
    p.add_argument("--top", type=int, default=20, help="最终推送数量（默认 20）")
    p.add_argument("--no-github", action="store_true", help="禁用 GitHub 补充源")
    p.add_argument("--store", default=SKILL_STORE_PATH, help="去重存储文件路径")
    args = p.parse_args()

    report = run(
        dry_run=args.dry_run,
        top_n=args.top,
        enable_github=not args.no_github,
        store_path=args.store,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
