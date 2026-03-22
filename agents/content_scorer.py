"""
agents/content_scorer.py
Agent 2 — 内容评分器

职责：
- URL 去重（URLStore）
- 关键词预过滤（只对 keyword_filter=True 的信源）
- 标题语义去重（Jaccard 0.4）
- 预排序候选文章（freshnss + type 加分）
- 调用 Claude API 生成中文摘要 + 相关度评分（1-10）
- 输出：评分后的文章列表 + 逐条过滤报告
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.base import AgentResult, BaseAgent, FilterEvent
from processor.summarizer import summarize_articles
from sources import (
    KEYWORD_BLOCKLIST,
    KEYWORD_FILTER_EXACT,
    KEYWORD_FILTER_TERMS,
    RSS_SOURCES,
)
from storage.dedup import URLStore

# 每种类型的基础加分（防止 Reddit 数量淹没 Newsletter）
_TYPE_BONUS = {"newsletter": 5.0, "podcast": 5.0, "github": 3.0}

# source_id → min_relevance 映射
_MIN_RELEVANCE: dict[str, int] = {
    s["id"]: s["min_relevance"]
    for s in RSS_SOURCES
    if "min_relevance" in s
}

# 配置了关键词过滤的信源 ID 集合
_FILTERED_SOURCE_IDS: set[str] = {
    s["id"] for s in RSS_SOURCES if s.get("keyword_filter", False)
}


class ContentScorerAgent(BaseAgent):
    """
    Agent 2：内容评分器

    接收 Agent 1 输出的原始文章列表，返回经过
    去重 → 过滤 → 预排序 → LLM 评分 的最终候选列表。
    """

    name = "content_scorer"

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        store_path: str = "seen_urls.json",
        preselect_multiplier: int = 3,
    ):
        super().__init__()
        self.api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.url_store = URLStore(store_path)
        self.preselect_multiplier = preselect_multiplier

    # ── 公开入口 ──────────────────────────────────────────────────────────────

    def run(self, articles: list[dict], max_articles: int = 12) -> AgentResult:
        return self._timed_run(self._run_impl, articles, max_articles)

    # ── 内部实现 ──────────────────────────────────────────────────────────────

    def _run_impl(self, articles: list[dict], max_articles: int) -> AgentResult:
        events: list[FilterEvent] = []
        total_in = len(articles)

        # ── Step 1: URL 去重 ─────────────────────────────────────────────────
        new_articles = self._url_dedup(articles, events)
        self.logger.info("[Agent 2] URL 去重: %d → %d", total_in, len(new_articles))

        if not new_articles:
            return AgentResult(
                agent_name=self.name,
                success=True,
                data={"scored_articles": [], "url_store": self.url_store},
                events=events,
                error="无新文章（全部已推送过）",
            )

        # ── Step 2: 关键词预过滤（仅对配置了 keyword_filter 的信源）────────
        kw_filtered = self._keyword_filter(new_articles, events)
        self.logger.info("[Agent 2] 关键词过滤: %d → %d", len(new_articles), len(kw_filtered))

        # ── Step 3: 预排序，取 top N 送入 Claude ────────────────────────────
        n_candidates = max_articles * self.preselect_multiplier
        candidates = self._preselect(kw_filtered, n_candidates)
        self.logger.info("[Agent 2] 预选候选: %d → %d", len(kw_filtered), len(candidates))

        # ── Step 4: Claude LLM 摘要 + 相关度评分 ────────────────────────────
        self.logger.info("[Agent 2] 调用 Claude API 评分...")
        enriched = summarize_articles(candidates, api_key=self.api_key)

        for art in enriched:
            score = art.get("relevance", 5)
            events.append(FilterEvent(
                stage="content_scorer",
                item=art.get("title_zh") or art.get("title", "")[:60],
                source=art.get("source_name", "?"),
                passed=score >= 6,
                reason=f"LLM 相关度评分: {score}/10",
                detail=art.get("summary_zh", "")[:80],
            ))

        # ── Step 5: 应用 min_relevance 门槛 ─────────────────────────────────
        scored = self._apply_min_relevance(enriched, events)

        self.logger.info(
            "✅ [Agent 2] 完成：%d 条文章通过评分（相关度≥6）",
            sum(1 for e in events if e.stage == "content_scorer" and e.passed),
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "scored_articles": scored,
                "url_store": self.url_store,
                "stats": {
                    "total_in": total_in,
                    "after_url_dedup": len(new_articles),
                    "after_keyword_filter": len(kw_filtered),
                    "candidates_sent_to_llm": len(candidates),
                    "after_llm_scoring": len(scored),
                },
            },
            events=events,
        )

    # ── 子步骤 ────────────────────────────────────────────────────────────────

    def _url_dedup(self, articles: list[dict], events: list[FilterEvent]) -> list[dict]:
        new = []
        for a in articles:
            url = a.get("url", "")
            if self.url_store.is_seen(url):
                events.append(FilterEvent(
                    stage="content_scorer",
                    item=a.get("title", "")[:60],
                    source=a.get("source_name", "?"),
                    passed=False,
                    reason="URL 已推送过（去重）",
                ))
            else:
                new.append(a)
        return new

    def _keyword_filter(self, articles: list[dict], events: list[FilterEvent]) -> list[dict]:
        result = []
        for a in articles:
            src_id = a.get("source_id", "")
            if src_id not in _FILTERED_SOURCE_IDS:
                # 不需要关键词过滤的信源直接通过
                result.append(a)
                continue

            title = a.get("title", "")
            excerpt = a.get("excerpt", "") or ""
            passed, reason = _matches_keyword_filter(title, excerpt)

            events.append(FilterEvent(
                stage="content_scorer",
                item=title[:60],
                source=a.get("source_name", "?"),
                passed=passed,
                reason=f"关键词过滤: {reason}",
            ))
            if passed:
                result.append(a)

        return result

    def _preselect(self, articles: list[dict], n: int) -> list[dict]:
        scored = sorted(articles, key=_score_article, reverse=True)
        return scored[:n]

    def _apply_min_relevance(
        self, articles: list[dict], events: list[FilterEvent]
    ) -> list[dict]:
        result = []
        for a in articles:
            src_id = a.get("source_id", "")
            min_rel = _MIN_RELEVANCE.get(src_id, 0)
            rel = a.get("relevance", 5)
            if rel < min_rel:
                events.append(FilterEvent(
                    stage="content_scorer",
                    item=a.get("title_zh") or a.get("title", "")[:60],
                    source=a.get("source_name", "?"),
                    passed=False,
                    reason=f"低于信源门槛（{rel} < min_relevance={min_rel}）",
                ))
            else:
                result.append(a)
        return result


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _matches_keyword_filter(title: str, excerpt: str) -> tuple[bool, str]:
    """返回 (passed, reason)"""
    text = f"{title} {excerpt}".lower()

    for blocked in KEYWORD_BLOCKLIST:
        if blocked in text:
            return False, f"黑名单: '{blocked}'"

    for term in KEYWORD_FILTER_TERMS:
        if len(term) <= 3:
            if re.search(rf"\b{re.escape(term)}\b", text):
                return True, f"白名单词: '{term}'"
        else:
            if term in text:
                return True, f"白名单词: '{term}'"

    for phrase in KEYWORD_FILTER_EXACT:
        if phrase in text:
            return True, f"精确短语: '{phrase}'"

    return False, "无关键词命中"


def _score_article(article: dict) -> float:
    score = 0.0
    atype = article.get("type", "rss")
    score += _TYPE_BONUS.get(atype, 0.0)
    if atype == "reddit":
        score += min(article.get("score", 0) / 50, 5.0)
    pub_str = article.get("published")
    if pub_str:
        try:
            pub = datetime.fromisoformat(pub_str)
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            hours_old = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
            score += max(0.0, 10.0 - hours_old / 4)
        except Exception:
            pass
    if article.get("excerpt"):
        score += 1.0
    return score
