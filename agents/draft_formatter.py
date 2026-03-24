"""
agents/draft_formatter.py
Agent 3 — 草稿格式器

职责：
- 按来源类型配额 + 相关度排序，选取最终推送文章（10-15 条）
- 标题级去重（Jaccard 0.4）
- 格式化 Telegram 推送（newsletter → podcast → reddit 顺序）
- dry_run 时只打印预览，不实际发送
- 输出：推送结果 + 选取报告
"""

from __future__ import annotations

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.base import AgentResult, BaseAgent, FilterEvent
from publisher.telegram import TelegramPublisher
from storage.dedup import URLStore

# 来源类型配额（保底名额）
SOURCE_QUOTAS: dict[str, int] = {
    "newsletter": 4,
    "podcast":    2,
    "github":     1,
}

# 类型显示顺序
TYPE_ORDER: dict[str, int] = {
    "newsletter": 0,
    "podcast":    1,
    "rss":        2,
    "reddit":     3,
    "github":     4,
}


class DraftFormatterAgent(BaseAgent):
    """
    Agent 3：草稿格式器

    接收 Agent 2 输出的评分文章列表，执行最终选取、
    Telegram 推送和 X Thread 草稿生成。
    """

    name = "draft_formatter"

    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_channel: str = "@AgenticNow",
        anthropic_api_key: Optional[str] = None,
        dry_run: bool = False,
    ):
        super().__init__()
        self.telegram_token = telegram_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.telegram_channel = telegram_channel
        self.api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.dry_run = dry_run

    # ── 公开入口 ──────────────────────────────────────────────────────────────

    def run(
        self,
        scored_articles: list[dict],
        url_store: URLStore,
        max_articles: int = 12,
        publish_mode: str = "individual",
    ) -> AgentResult:
        return self._timed_run(
            self._run_impl, scored_articles, url_store, max_articles, publish_mode
        )

    # ── 内部实现 ──────────────────────────────────────────────────────────────

    def _run_impl(
        self,
        scored_articles: list[dict],
        url_store: URLStore,
        max_articles: int,
        publish_mode: str,
    ) -> AgentResult:
        events: list[FilterEvent] = []

        if not scored_articles:
            return AgentResult(
                agent_name=self.name,
                success=True,
                data={"published_count": 0, "x_threads": [], "final_articles": []},
                events=events,
                error="无文章可推送",
            )

        # ── Step 1: 标题去重 + 配额选取 ─────────────────────────────────────
        final_articles = self._apply_quotas(scored_articles, max_articles, events)
        self.logger.info("[Agent 3] 最终选取: %d 条", len(final_articles))

        # ── Step 2: 打印选取摘要 ─────────────────────────────────────────────
        self._log_selection(final_articles)

        # ── Step 3: Telegram 推送（或 dry_run 预览）─────────────────────────
        published_count = 0
        if self.dry_run:
            self.logger.info("\n🔍 DRY RUN — Telegram 消息预览：")
            self.logger.info("=" * 60)
            dummy = TelegramPublisher("dummy_token", self.telegram_channel)
            if publish_mode == "digest":
                print(dummy.format_digest(final_articles))
            else:
                for art in final_articles:
                    print(dummy.format_article(art))
                    print("─" * 40)
        else:
            publisher = TelegramPublisher(self.telegram_token, self.telegram_channel)
            published_count = publisher.publish_articles(final_articles, mode=publish_mode)

            # 标记已发送
            published_urls = [a["url"] for a in final_articles[:published_count]]
            url_store.mark_seen_batch(published_urls)
            url_store.save()
            self.logger.info("[Agent 3] 已推送 %d 条 → Telegram", published_count)

        for art in final_articles:
            events.append(FilterEvent(
                stage="draft_formatter",
                item=art.get("title_zh") or art.get("title", "")[:60],
                source=art.get("source_name", "?"),
                passed=True,
                reason=f"入选推送（{art.get('type','?')} | 评分 {art.get('relevance','?')}/10）",
            ))

        self.logger.info(
            "✅ [Agent 3] 完成：推送 %d 条",
            published_count if not self.dry_run else len(final_articles),
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "final_articles": final_articles,
                "published_count": published_count,
                "dry_run": self.dry_run,
            },
            events=events,
        )

    # ── 配额选取 ──────────────────────────────────────────────────────────────

    def _apply_quotas(
        self,
        articles: list[dict],
        max_articles: int,
        events: list[FilterEvent],
    ) -> list[dict]:
        # 0. 标题去重
        articles = self._dedup_by_title(articles, events)

        # 1. 按类型分组并按 relevance 降序
        by_type: dict[str, list[dict]] = {}
        for a in articles:
            t = a.get("type", "rss")
            by_type.setdefault(t, []).append(a)
        for t in by_type:
            by_type[t].sort(key=lambda x: x.get("relevance", 5), reverse=True)

        selected: list[dict] = []
        selected_urls: set[str] = set()

        # 2. 按配额保底
        for src_type, quota in SOURCE_QUOTAS.items():
            for art in by_type.get(src_type, []):
                if len([s for s in selected if s.get("type") == src_type]) >= quota:
                    break
                url = art.get("url", "")
                if url not in selected_urls:
                    selected.append(art)
                    selected_urls.add(url)

        # 3. 剩余按 relevance 填满
        remaining = max_articles - len(selected)
        if remaining > 0:
            rest = sorted(
                [a for a in articles if a.get("url", "") not in selected_urls],
                key=lambda x: x.get("relevance", 5),
                reverse=True,
            )
            for art in rest[:remaining]:
                selected.append(art)
                selected_urls.add(art.get("url", ""))

        # 4. 按类型顺序 + relevance 排序
        selected.sort(
            key=lambda x: (
                TYPE_ORDER.get(x.get("type", "rss"), 9),
                -x.get("relevance", 5),
            )
        )

        return selected[:max_articles]

    def _dedup_by_title(
        self, articles: list[dict], events: list[FilterEvent]
    ) -> list[dict]:
        result: list[dict] = []
        for art in articles:
            title_zh = art.get("title_zh", "")
            title_en = art.get("title", "")
            title = title_zh or title_en
            is_dup = False
            for existing in result:
                etitle_zh = existing.get("title_zh", "")
                etitle_en = existing.get("title", "")
                etitle = etitle_zh or etitle_en
                # 先比中文，再比英文（中文分词较弱时以英文为准）
                similar = _jaccard_similar(title, etitle)
                if not similar and title_en and etitle_en:
                    similar = _jaccard_similar(title_en, etitle_en)
                if similar:
                    if art.get("relevance", 5) > existing.get("relevance", 5):
                        result.remove(existing)
                        result.append(art)
                    events.append(FilterEvent(
                        stage="draft_formatter",
                        item=title[:60],
                        source=art.get("source_name", "?"),
                        passed=False,
                        reason=f"标题重复（Jaccard≥0.5），与「{etitle[:40]}」相似",
                    ))
                    is_dup = True
                    break
            if not is_dup:
                result.append(art)
        return result

    def _log_selection(self, articles: list[dict]) -> None:
        self.logger.info("─" * 56)
        for i, a in enumerate(articles, 1):
            title = a.get("title_zh") or a.get("title", "")
            self.logger.info(
                "  %2d. [%-10s] [%s/10] %s",
                i,
                a.get("type", "?"),
                a.get("relevance", "?"),
                title[:50],
            )
        self.logger.info("─" * 56)


# ── 工具函数 ──────────────────────────────────────────────────────────────────

# 停用词表（去除后提高有效词的权重）
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "in", "at", "for", "to", "of", "on", "as", "by", "with",
    "and", "or", "but", "not", "that", "this", "its", "it",
    "how", "why", "what", "which", "who", "now", "has",
    "have", "had", "will", "would", "can", "could", "from", "up",
    "into", "about", "than", "more", "its", "their", "our",
}

# 简单后缀词干列表（降序按长度排列，优先匹配长后缀）
_SUFFIXES = ("tions", "tion", "ings", "ing", "ies", "ed", "ly",
             "ers", "er", "able", "ible", "ness", "ful", "less")


def _stem(word: str) -> str:
    """
    简单词干提取：去除常见后缀，保留词根。
    额外步骤：去除尾部 'e'，使 'feature'/'featuring' → 'featur'，
    'release'/'releases' → 'releas'，提高同根词匹配率。
    """
    result = word
    for suffix in _SUFFIXES:
        if result.endswith(suffix) and len(result) - len(suffix) >= 3:
            result = result[:-len(suffix)]
            break
    else:
        # 复数 s（不去 ss 结尾）
        if result.endswith("s") and len(result) > 3 and not result.endswith("ss"):
            result = result[:-1]
    # 去除尾部 'e'（如 feature→featur，release→releas）
    if result.endswith("e") and len(result) > 3:
        result = result[:-1]
    return result


def _normalize_title(title: str) -> set[str]:
    """
    标准化标题为词干集合：
    1. 小写
    2. 连字符 → 空格（open-weight → open weight）
    3. 金额规范化（$500M / $500 million → 500m）
    4. 去标点
    5. 分词 → 去停用词 → 词干化
    """
    import re
    text = title.lower()
    text = text.replace("-", " ")
    # $500M / $9B / $2.5B
    text = re.sub(r"\$(\d+\.?\d*)\s*(m|b|k|t)\b", r"\1\2", text)
    # $500 million / $9 billion
    text = re.sub(r"\$(\d+\.?\d*)\s*million\b", r"\1m", text)
    text = re.sub(r"\$(\d+\.?\d*)\s*billion\b", r"\1b", text)
    # 去标点（保留字母数字）
    text = re.sub(r"[^\w\s]", " ", text)
    words = set()
    for w in text.split():
        if w not in _STOPWORDS and len(w) > 1:
            words.add(_stem(w))
    return words


def _jaccard_similar(a: str, b: str, threshold: float = 0.5) -> bool:
    """
    判断两个标题是否描述同一新闻。
    使用规范化词干集合的 Jaccard 系数，阈值 0.5。
    自动尝试英文标题（当中文标题相似度不足时回退）。
    """
    if not a or not b:
        return False
    wa = _normalize_title(a)
    wb = _normalize_title(b)
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) >= threshold
