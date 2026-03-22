#!/usr/bin/env python3
"""
scripts/heal_sources.py — 自愈式 RSS 源管理器

流程：
  1. 读取 sources.py 中所有 40 个 RSS 信源
  2. 逐一抓取并验证（feedparser）——标记死链 / 30 天无更新的陈旧源
  3. 对每个死链/陈旧源，从候选池中搜索同主题替代源
  4. 实际抓取验证所有候选 URL（绝不加入未成功抓取的 URL）
  5. 按发布频率 + 新鲜度 + 主题相关性对所有源打分（满分 100）
  6. 输出带变更日志的 sources_healed.yaml + 终端摘要报告

用法：
    python scripts/heal_sources.py              # 扫描 + 输出 YAML
    python scripts/heal_sources.py --apply      # 同时覆盖更新 sources.py
    python scripts/heal_sources.py --dry-run    # 只报告，不写文件
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import feedparser
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from sources import RSS_SOURCES

# ── 配置 ─────────────────────────────────────────────────────────────────────
STALE_DAYS          = 30        # 超过此天数视为陈旧
MIN_SCORE_TO_KEEP   = 35        # 低于此分数触发替换搜索
MAX_WORKERS         = 8         # 并发线程数
FETCH_TIMEOUT       = 15        # 每个 feed 抓取超时（秒）
CANDIDATE_VALIDATE_WORKERS = 6  # 候选验证并发数

# 主题相关性关键词（用于打分）
TOPIC_KEYWORDS = {
    "ai", "agent", "agentic", "llm", "gpt", "claude", "anthropic",
    "openai", "autonomous", "mcp", "model", "language model",
    "machine learning", "generative", "inference", "fine-tun",
    "rag", "tool use", "function call", "multimodal", "embedding",
    "defi", "crypto", "payment", "fintech", "web3", "blockchain",
    "automation", "workflow", "pipeline", "orchestration",
}

# ── 候选替换池 ─────────────────────────────────────────────────────────────────
# 按类别分组，供死链/陈旧源的替换搜索使用
# 格式: {"id", "name", "rss", "category", "source_type"}
CANDIDATE_POOL: list[dict] = [

    # AI Agent / LLM Engineering
    {"id": "ml_news",          "name": "ML News (Sebastian Raschka)",       "rss": "https://mlnews.dev/feed.xml",                          "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "sebastian_mag",    "name": "Ahead of AI",                       "rss": "https://magazine.sebastianraschka.com/feed",            "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "gradient_flow",    "name": "Gradient Flow",                     "rss": "https://gradientflow.com/feed/",                        "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "the_sequence",     "name": "The Sequence",                      "rss": "https://thesequence.substack.com/feed",                 "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "deep_learning_wk", "name": "The Deep Learning Weekly",          "rss": "https://www.deeplearningweekly.com/feed",               "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "alan_d_thompson",  "name": "Alan D. Thompson – LifeArchitect",  "rss": "https://lifearchitect.ai/feed/",                        "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "roboflow_blog",    "name": "Roboflow Blog",                     "rss": "https://blog.roboflow.com/rss/",                        "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "langchain_blog",   "name": "LangChain Blog",                    "rss": "https://blog.langchain.dev/rss/",                       "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "huggingface_blog", "name": "Hugging Face Blog",                 "rss": "https://huggingface.co/blog/feed.xml",                  "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "openai_news",      "name": "OpenAI News",                       "rss": "https://openai.com/news/rss.xml",                       "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "anthropic_news",   "name": "Anthropic News",                    "rss": "https://www.anthropic.com/rss.xml",                     "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "google_deepmind",  "name": "Google DeepMind Blog",              "rss": "https://deepmind.google/blog/rss.xml",                  "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "mistral_blog",     "name": "Mistral AI Blog",                   "rss": "https://mistral.ai/feed.xml",                           "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "cohere_blog",      "name": "Cohere Blog",                       "rss": "https://cohere.com/blog/rss",                           "category": "AI Agent",       "source_type": "newsletter"},
    {"id": "ml_street_talk",   "name": "ML Street Talk Podcast",            "rss": "https://anchor.fm/s/1e4a0eac/podcast/rss",              "category": "AI Agent",       "source_type": "podcast"},
    {"id": "twiml_ai",         "name": "TWIML AI Podcast",                  "rss": "https://feeds.megaphone.fm/MLN2155636147",              "category": "AI Agent",       "source_type": "podcast"},
    {"id": "lex_fridman",      "name": "Lex Fridman Podcast",               "rss": "https://lexfridman.com/feed/podcast/",                  "category": "AI Agent",       "source_type": "podcast"},
    {"id": "eye_on_ai",        "name": "Eye on AI",                         "rss": "https://feeds.simplecast.com/L8R5D3rI",                 "category": "AI Agent",       "source_type": "podcast"},
    {"id": "practical_ai_alt", "name": "Practical AI (alt)",                "rss": "https://changelog.com/practicalai/feed",                "category": "AI Agent",       "source_type": "podcast"},
    {"id": "ai_daily_brief",   "name": "AI Daily Brief",                    "rss": "https://feeds.acast.com/public/shows/the-ai-daily-brief", "category": "Agentic Web", "source_type": "podcast"},
    {"id": "gradient_dissent", "name": "Gradient Dissent (W&B)",            "rss": "https://feeds.captivate.fm/gradient-dissent/",          "category": "AI Agent",       "source_type": "podcast"},

    # Agentic Web / Tech Strategy
    {"id": "ben_evans",        "name": "Benedict Evans",                    "rss": "https://www.ben-evans.com/benedictevans/rss.xml",       "category": "Agentic Web",    "source_type": "newsletter"},
    {"id": "daring_fireball",  "name": "Daring Fireball (John Gruber)",     "rss": "https://daringfireball.net/feeds/main",                 "category": "Agentic Web",    "source_type": "newsletter"},
    {"id": "tldr_ai",          "name": "TLDR AI Newsletter",                "rss": "https://tldr.tech/ai/rss",                             "category": "Agentic Web",    "source_type": "newsletter"},
    {"id": "exponential_view", "name": "Exponential View (Azeem Azhar)",    "rss": "https://www.exponentialview.co/feed",                  "category": "Agentic Web",    "source_type": "newsletter"},
    {"id": "every_to",         "name": "Every.to",                          "rss": "https://every.to/feed",                                "category": "Agentic Web",    "source_type": "newsletter"},
    {"id": "a16z_blog",        "name": "a16z Blog",                         "rss": "https://a16z.com/feed/",                               "category": "Agentic Economy", "source_type": "newsletter"},
    {"id": "sequoia_art",      "name": "Sequoia Capital Articles",          "rss": "https://www.sequoiacap.com/articles/feed/",            "category": "Agentic Economy", "source_type": "newsletter"},
    {"id": "yc_blog",          "name": "Y Combinator Blog",                 "rss": "https://www.ycombinator.com/blog.xml",                 "category": "Agentic Economy", "source_type": "newsletter"},
    {"id": "first_round_rev",  "name": "First Round Review",                "rss": "https://review.firstround.com/rss.xml",                "category": "Agentic Economy", "source_type": "newsletter"},
    {"id": "lightcone_yc",     "name": "Lightcone Podcast (YC)",            "rss": "https://feeds.simplecast.com/l2i9YnTd",                "category": "Agentic Economy", "source_type": "podcast"},

    # Agentic Payment / Crypto × AI
    {"id": "coindesk_tech",    "name": "CoinDesk Tech",                     "rss": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=json", "category": "Agentic Payment", "source_type": "newsletter"},
    {"id": "decrypt_feed",     "name": "Decrypt",                           "rss": "https://decrypt.co/feed",                              "category": "Agentic Payment", "source_type": "newsletter"},
    {"id": "the_defiant",      "name": "The Defiant",                       "rss": "https://thedefiant.io/feed",                           "category": "Agentic Payment", "source_type": "newsletter"},
    {"id": "bankless_alt",     "name": "Bankless (alt)",                    "rss": "https://www.bankless.com/rss/feed",                    "category": "Agentic Payment", "source_type": "newsletter"},
    {"id": "unchained_pod",    "name": "Unchained (Laura Shin)",            "rss": "https://unchainedcrypto.com/feed/",                    "category": "Agentic Payment", "source_type": "podcast"},
    {"id": "chopping_block",   "name": "The Chopping Block",                "rss": "https://feeds.megaphone.fm/choppingblock",             "category": "Agentic Payment", "source_type": "podcast"},
    {"id": "bankless_pod",     "name": "Bankless Podcast",                  "rss": "https://feeds.megaphone.fm/bankless",                  "category": "Agentic Payment", "source_type": "podcast"},
    {"id": "epicenter",        "name": "Epicenter Podcast",                 "rss": "https://feeds.megaphone.fm/epicenter",                 "category": "Agentic Payment", "source_type": "podcast"},
    {"id": "web3_academy",     "name": "Web3 Academy",                      "rss": "https://web3academy.pro/rss/",                         "category": "Agentic Commerce", "source_type": "newsletter"},
    {"id": "messari_res",      "name": "Messari Research",                  "rss": "https://messari.io/rss",                              "category": "Agentic Economy", "source_type": "newsletter"},
    {"id": "delphi_digital",   "name": "Delphi Digital",                    "rss": "https://members.delphidigital.io/reports/rss/",        "category": "Agentic Economy", "source_type": "newsletter"},
]


# ─── 数据类 ───────────────────────────────────────────────────────────────────

@dataclass
class FeedHealth:
    source_id: str
    name: str
    rss: str
    category: str
    source_type: str
    extra: dict = field(default_factory=dict)   # keyword_filter, min_relevance 等

    # 验证结果
    reachable: bool = False
    entry_count: int = 0
    days_since_last: Optional[float] = None     # None = 无法计算
    posts_per_month: float = 0.0
    topic_score: float = 0.0                    # 0-40
    error: str = ""

    @property
    def is_stale(self) -> bool:
        return (
            self.days_since_last is not None
            and self.days_since_last > STALE_DAYS
        )

    @property
    def is_dead(self) -> bool:
        return not self.reachable or (self.reachable and self.entry_count == 0)

    @property
    def total_score(self) -> float:
        """综合评分（满分 100）= 频率(30) + 新鲜度(30) + 主题相关性(40)"""
        freq_score = min(self.posts_per_month / 0.7, 30)    # 21帖/月 = 满分
        if self.days_since_last is None:
            fresh_score = 0.0
        elif self.days_since_last <= 7:
            fresh_score = 30.0
        elif self.days_since_last <= 14:
            fresh_score = 25.0
        elif self.days_since_last <= STALE_DAYS:
            fresh_score = 20.0
        elif self.days_since_last <= 60:
            fresh_score = 10.0
        else:
            fresh_score = 0.0
        return round(freq_score + fresh_score + self.topic_score, 1)

    @property
    def status(self) -> str:
        if self.is_dead:
            return "DEAD"
        if self.is_stale:
            return "STALE"
        if self.total_score < MIN_SCORE_TO_KEEP:
            return "LOW"
        return "OK"


@dataclass
class ChangelogEntry:
    action: str          # "KEPT" | "REPLACED" | "REMOVED" | "ADDED"
    source_id: str
    name: str
    rss: str
    reason: str
    score: float = 0.0
    replaces: str = ""   # 被替换的源 ID


# ─── 核心函数 ─────────────────────────────────────────────────────────────────

def _fetch_and_score(source: dict) -> FeedHealth:
    """
    抓取单个 RSS 源并计算健康评分。
    !! 绝不推断：只报告实际抓取到的数据。
    """
    health = FeedHealth(
        source_id  = source["id"],
        name       = source["name"],
        rss        = source["rss"],
        category   = source.get("category", ""),
        source_type= source.get("source_type", "rss"),
        extra      = {k: v for k, v in source.items()
                      if k not in ("id", "name", "rss", "category", "source_type", "url")},
    )

    try:
        d = feedparser.parse(source["rss"])

        # 判断是否可达
        if d.get("bozo") and not d.get("entries"):
            health.error = str(d.get("bozo_exception", "empty feed"))[:120]
            return health

        entries = d.get("entries", [])
        if not entries:
            health.reachable = True
            health.error = "feed reachable but 0 entries"
            return health

        health.reachable = True
        health.entry_count = len(entries)

        # 计算最后发布时间
        now = datetime.now(timezone.utc)
        pub_dates: list[datetime] = []
        for e in entries[:20]:
            for key in ("published_parsed", "updated_parsed"):
                val = e.get(key)
                if val:
                    try:
                        dt = datetime(*val[:6], tzinfo=timezone.utc)
                        pub_dates.append(dt)
                    except Exception:
                        pass
                    break

        if pub_dates:
            latest = max(pub_dates)
            health.days_since_last = (now - latest).total_seconds() / 86400

            # 计算发布频率（帖/月，用最早到最新的时间跨度估算）
            if len(pub_dates) >= 2:
                oldest = min(pub_dates)
                span_months = max((latest - oldest).total_seconds() / (30 * 86400), 0.1)
                health.posts_per_month = round(len(pub_dates) / span_months, 1)
            else:
                health.posts_per_month = 1.0

        # 主题相关性：检测最近 10 篇标题中关键词覆盖率
        titles = " ".join(
            e.get("title", "") for e in entries[:10]
        ).lower()
        kw_hits = sum(1 for kw in TOPIC_KEYWORDS if kw in titles)
        health.topic_score = min(kw_hits * 4, 40)   # 每命中 1 词得 4 分，上限 40

    except Exception as exc:
        health.error = str(exc)[:120]

    return health


def validate_candidate(candidate: dict) -> Optional[FeedHealth]:
    """
    验证候选替换源：只返回成功抓取且有最近内容的 FeedHealth。
    返回 None 表示候选无效（不可用）。
    """
    health = _fetch_and_score(candidate)
    if health.is_dead:
        return None
    if health.days_since_last is not None and health.days_since_last > 60:
        return None
    return health


def find_replacement(
    dead: FeedHealth,
    current_ids: set[str],
    existing_rss_urls: set[str],
) -> Optional[FeedHealth]:
    """
    为死链/陈旧源寻找替换：
    1. 先筛选同类别候选
    2. 实际抓取验证
    3. 返回评分最高的有效候选
    """
    same_cat = [
        c for c in CANDIDATE_POOL
        if c["category"] == dead.category
        and c["id"] not in current_ids
        and c["rss"] not in existing_rss_urls
    ]
    # 若同类别无候选，扩展到全池
    if not same_cat:
        same_cat = [
            c for c in CANDIDATE_POOL
            if c["id"] not in current_ids
            and c["rss"] not in existing_rss_urls
        ]

    # 并发验证候选
    valid: list[FeedHealth] = []
    with ThreadPoolExecutor(max_workers=CANDIDATE_VALIDATE_WORKERS) as ex:
        futures = {ex.submit(validate_candidate, c): c for c in same_cat}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                valid.append(result)

    if not valid:
        return None

    # 选评分最高的
    return max(valid, key=lambda h: h.total_score)


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, apply: bool = False) -> None:
    print("\n" + "═" * 70)
    print("  🔍  AgenticNow 自愈式 RSS 源管理器")
    print(f"  扫描 {len(RSS_SOURCES)} 个信源  |  陈旧阈值: {STALE_DAYS} 天")
    print("═" * 70 + "\n")

    # ── Step 1: 并发验证所有当前源 ─────────────────────────────────────────
    print("📡 Step 1 / 4 — 并发验证当前所有信源...\n")
    health_map: dict[str, FeedHealth] = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_fetch_and_score, src): src for src in RSS_SOURCES}
        for future in as_completed(futures):
            h = future.result()
            health_map[h.source_id] = h
            icon = {"OK": "✅", "STALE": "⚠️ ", "LOW": "🔅", "DEAD": "❌"}.get(h.status, "?")
            days = f"{h.days_since_last:.0f}d" if h.days_since_last is not None else "?d"
            print(
                f"  {icon} [{h.status:<5}] {h.name:<38} "
                f"score={h.total_score:>5.1f}  last={days:<6}  "
                f"freq={h.posts_per_month:.1f}/mo"
                + (f"  ⚠ {h.error[:40]}" if h.error and h.status == 'DEAD' else "")
            )

    # ── Step 2: 分类 ────────────────────────────────────────────────────────
    ok_sources    = [h for h in health_map.values() if h.status == "OK"]
    stale_sources = [h for h in health_map.values() if h.status in ("STALE", "LOW")]
    dead_sources  = [h for h in health_map.values() if h.status == "DEAD"]

    print(f"\n📊 Step 2 / 4 — 分类结果:")
    print(f"  ✅ 健康: {len(ok_sources)} 个")
    print(f"  ⚠️  陈旧/低分: {len(stale_sources)} 个")
    print(f"  ❌ 死链: {len(dead_sources)} 个")

    need_replacement = dead_sources + stale_sources

    # ── Step 3: 搜索 + 验证替换候选 ────────────────────────────────────────
    print(f"\n🔎 Step 3 / 4 — 为 {len(need_replacement)} 个源搜索替换候选...")
    current_ids      = set(h.source_id for h in health_map.values())
    existing_rss     = set(h.rss for h in health_map.values())
    replacements: dict[str, FeedHealth] = {}   # dead_id → new FeedHealth
    changelog: list[ChangelogEntry] = []

    for h in need_replacement:
        print(f"\n  🔎 为 [{h.status}] {h.name} 寻找替换...")
        candidate = find_replacement(h, current_ids, existing_rss)
        if candidate:
            replacements[h.source_id] = candidate
            current_ids.add(candidate.source_id)
            existing_rss.add(candidate.rss)
            print(f"     ✅ 找到: {candidate.name} (score={candidate.total_score})")
            changelog.append(ChangelogEntry(
                action="REPLACED",
                source_id=candidate.source_id,
                name=candidate.name,
                rss=candidate.rss,
                reason=(
                    f"替换 [{h.status}] {h.name}（"
                    + (f"最后更新 {h.days_since_last:.0f}d 前，" if h.days_since_last is not None else "无法访问，")
                    + f"评分 {h.total_score}）"
                ),
                score=candidate.total_score,
                replaces=h.source_id,
            ))
            changelog.append(ChangelogEntry(
                action="REMOVED",
                source_id=h.source_id,
                name=h.name,
                rss=h.rss,
                reason=(
                    f"状态: {h.status} | "
                    f"评分: {h.total_score} | "
                    + (f"最后更新: {h.days_since_last:.0f} 天前" if h.days_since_last else f"错误: {h.error}")
                ),
                score=h.total_score,
            ))
        else:
            print(f"     ❌ 未找到合适替换源，移除")
            changelog.append(ChangelogEntry(
                action="REMOVED",
                source_id=h.source_id,
                name=h.name,
                rss=h.rss,
                reason=f"状态: {h.status} | 无可用替换源 | 评分: {h.total_score}",
                score=h.total_score,
            ))

    # OK 源标记为 KEPT
    for h in ok_sources:
        changelog.append(ChangelogEntry(
            action="KEPT",
            source_id=h.source_id,
            name=h.name,
            rss=h.rss,
            reason=f"健康 | 评分: {h.total_score} | 最后更新: {h.days_since_last:.0f}d 前",
            score=h.total_score,
        ))

    # ── Step 4: 构建输出 YAML ──────────────────────────────────────────────
    print(f"\n📝 Step 4 / 4 — 构建更新后的信源列表...")

    final_sources: list[dict] = []

    # 先放健康源（保持原有字段）
    for src in RSS_SOURCES:
        h = health_map.get(src["id"])
        if h and h.status == "OK":
            final_sources.append(_to_yaml_dict(h, src))

    # 替换源（死链 / 陈旧源的替代品）
    for old_id, new_h in replacements.items():
        old_src = next((s for s in RSS_SOURCES if s["id"] == old_id), {})
        entry = _to_yaml_dict(new_h, {})
        entry["replaces"] = old_id
        final_sources.append(entry)

    # 构建 YAML 文档
    yaml_doc = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_sources": len(final_sources),
            "healed": len(replacements),
            "removed": len([c for c in changelog if c.action == "REMOVED"]),
            "stale_threshold_days": STALE_DAYS,
        },
        "changelog": [
            {
                "action":  c.action,
                "id":      c.source_id,
                "name":    c.name,
                "score":   c.score,
                "reason":  c.reason,
                **({"replaces": c.replaces} if c.replaces else {}),
            }
            for c in sorted(changelog, key=lambda c: c.action)
        ],
        "sources": final_sources,
    }

    # ── 打印终端摘要 ────────────────────────────────────────────────────────
    _print_summary(changelog, final_sources)

    if dry_run:
        print("\n⚠️  DRY RUN — 不写入文件")
        return

    # ── 写入 YAML ───────────────────────────────────────────────────────────
    out_path = Path(__file__).parent.parent / "sources_healed.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(
            yaml_doc, f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120,
        )
    print(f"\n✅ 已写入: {out_path}")

    if apply:
        _apply_to_sources_py(final_sources)


# ─── 工具函数 ──────────────────────────────────────────────────────────────────

def _to_yaml_dict(h: FeedHealth, original: dict) -> dict:
    """将 FeedHealth 转换为 YAML 源字典，保留原有的 keyword_filter 等字段。"""
    d = {
        "id":          h.source_id,
        "name":        h.name,
        "rss":         h.rss,
        "category":    h.category,
        "source_type": h.source_type,
        "_score":      h.total_score,
        "_last_pub_days": round(h.days_since_last, 1) if h.days_since_last else None,
        "_posts_per_month": h.posts_per_month,
    }
    # 保留原有的附加字段（keyword_filter, min_relevance 等）
    for key in ("url", "keyword_filter", "min_relevance"):
        if key in original:
            d[key] = original[key]
    return d


def _print_summary(changelog: list[ChangelogEntry], final_sources: list[dict]) -> None:
    kept     = [c for c in changelog if c.action == "KEPT"]
    replaced = [c for c in changelog if c.action == "REPLACED"]
    removed  = [c for c in changelog if c.action == "REMOVED"]

    print("\n" + "═" * 70)
    print("  📊  自愈摘要")
    print("═" * 70)
    print(f"  ✅ 健康保留: {len(kept):>3} 个")
    print(f"  🔄 成功替换: {len(replaced):>3} 个")
    print(f"  🗑  移除:     {len(removed) - len(replaced):>3} 个（无可用替换）")
    print(f"  📋 最终信源: {len(final_sources):>3} 个")

    if removed:
        print("\n  移除/替换详情:")
        for c in removed:
            print(f"    {'🔄' if c.source_id in [r.replaces for r in replaced] else '🗑 '} "
                  f"{c.name:<38} → {c.reason[:60]}")

    if replaced:
        print("\n  新增替换源:")
        for c in replaced:
            print(f"    ➕ {c.name:<38} score={c.score:.1f}  替换: {c.replaces}")

    print()
    print("  评分分布 (满分100):")
    all_scores = [s.get("_score", 0) for s in final_sources]
    if all_scores:
        print(f"    最高: {max(all_scores):.1f}  最低: {min(all_scores):.1f}  "
              f"平均: {sum(all_scores)/len(all_scores):.1f}")

    print("═" * 70)


def _apply_to_sources_py(final_sources: list[dict]) -> None:
    """将最终信源列表写回 sources.py（谨慎操作：先备份）。"""
    src_path = Path(__file__).parent.parent / "sources.py"
    bak_path = src_path.with_suffix(".py.bak")

    # 备份
    bak_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  📦 已备份原始文件: {bak_path}")

    # 读取现有 sources.py，替换 RSS_SOURCES 列表
    content = src_path.read_text(encoding="utf-8")
    new_list = _render_rss_sources_python(final_sources)

    # 找到 RSS_SOURCES = [ ... ] 的范围并替换
    pattern = r"RSS_SOURCES:\s*list\[dict\]\s*=\s*\[.*?\n\]"
    new_content = re.sub(pattern, new_list, content, flags=re.DOTALL)

    src_path.write_text(new_content, encoding="utf-8")
    print(f"  ✅ 已更新: {src_path}")


def _render_rss_sources_python(sources: list[dict]) -> str:
    """将信源列表渲染回 Python 字典列表格式。"""
    lines = ["RSS_SOURCES: list[dict] = ["]
    by_cat: dict[str, list[dict]] = {}
    for s in sources:
        cat = s.get("category", "Other")
        by_cat.setdefault(cat, []).append(s)

    for cat, srcs in by_cat.items():
        lines.append(f"\n    # {'═'*68}")
        lines.append(f"    # {cat}（{len(srcs)} 个）")
        lines.append(f"    # {'═'*68}")
        for s in srcs:
            lines.append("    {")
            for key in ("id", "name", "url", "rss", "category", "source_type",
                        "keyword_filter", "min_relevance", "replaces"):
                if key in s:
                    val = s[key]
                    if isinstance(val, str):
                        lines.append(f'        "{key}": "{val}",')
                    elif isinstance(val, bool):
                        lines.append(f'        "{key}": {val},')
                    elif val is not None:
                        lines.append(f'        "{key}": {val},')
            lines.append("    },")
    lines.append("]")
    return "\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="自愈式 RSS 源管理器 — 验证、替换、评分、输出"
    )
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写文件")
    parser.add_argument("--apply",   action="store_true", help="同时更新 sources.py（自动备份）")
    args = parser.parse_args()
    run(dry_run=args.dry_run, apply=args.apply)
