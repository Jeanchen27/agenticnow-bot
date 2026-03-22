"""
agents/source_validator.py
Agent 1 — 源验证器

职责：
- 抓取所有 40 个 RSS / Podcast 信源
- 用 feedparser 验证每个 URL 返回有效 XML
- 标记死链 / 空 feed / 幻觉 URL
- 同时抓取 Reddit + GitHub Trending
- 输出：有效文章列表 + 逐源验证报告
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser

# 确保 sys.path 包含项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.base import AgentResult, BaseAgent, FilterEvent
from fetchers.reddit import fetch_reddit_sources
from fetchers.github_trending import fetch_github_trending
from sources import RSS_SOURCES, REDDIT_SOURCES, GITHUB_TOPICS


class SourceValidatorAgent(BaseAgent):
    """
    Agent 1：源验证器

    - 并发抓取所有 RSS 信源（最多 10 线程）
    - 验证 feed 是否返回有效 XML + 有效条目
    - 标记失效信源，不阻断后续流程
    """

    name = "source_validator"

    def __init__(
        self,
        hours_lookback_rss: int = 168,
        hours_lookback_reddit: int = 48,
        enable_github: bool = True,
        max_workers: int = 10,
    ):
        super().__init__()
        self.hours_lookback_rss = hours_lookback_rss
        self.hours_lookback_reddit = hours_lookback_reddit
        self.enable_github = enable_github
        self.max_workers = max_workers

    # ── 公开入口 ──────────────────────────────────────────────────────────────

    def run(self) -> AgentResult:
        return self._timed_run(self._run_impl)

    # ── 内部实现 ──────────────────────────────────────────────────────────────

    def _run_impl(self) -> AgentResult:
        events: list[FilterEvent] = []
        all_articles: list[dict] = []
        valid_sources: list[str] = []
        dead_sources: list[dict] = []

        # 1. 并发验证 + 抓取所有 RSS 信源
        self.logger.info("📡 [Agent 1] 验证 %d 个 RSS 信源...", len(RSS_SOURCES))
        rss_results = self._fetch_rss_concurrent(events, valid_sources, dead_sources)
        all_articles.extend(rss_results)

        # 2. Reddit
        self.logger.info("📡 [Agent 1] 抓取 Reddit...")
        try:
            reddit_articles = fetch_reddit_sources(
                REDDIT_SOURCES, hours_lookback=self.hours_lookback_reddit
            )
            all_articles.extend(reddit_articles)
            for a in reddit_articles:
                events.append(FilterEvent(
                    stage="source_validator",
                    item=a.get("title", "")[:60],
                    source=a.get("source_name", "Reddit"),
                    passed=True,
                    reason="Reddit 抓取成功",
                ))
            self.logger.info("   → Reddit: %d 条", len(reddit_articles))
        except Exception as exc:
            self.logger.error("Reddit 抓取失败: %s", exc)

        # 3. GitHub Trending
        if self.enable_github:
            self.logger.info("📡 [Agent 1] 抓取 GitHub Trending...")
            try:
                github_articles = fetch_github_trending(topics=GITHUB_TOPICS, max_items=5)
                all_articles.extend(github_articles)
                for a in github_articles:
                    events.append(FilterEvent(
                        stage="source_validator",
                        item=a.get("title", "")[:60],
                        source="GitHub Trending",
                        passed=True,
                        reason="GitHub 抓取成功",
                    ))
                self.logger.info("   → GitHub: %d 个项目", len(github_articles))
            except Exception as exc:
                self.logger.error("GitHub Trending 抓取失败: %s", exc)

        self.logger.info(
            "✅ [Agent 1] 完成：%d 条文章 | %d 个有效信源 | %d 个死链",
            len(all_articles), len(valid_sources), len(dead_sources),
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "articles": all_articles,
                "valid_sources": valid_sources,
                "dead_sources": dead_sources,
                "total_fetched": len(all_articles),
            },
            events=events,
        )

    def _fetch_rss_concurrent(
        self,
        events: list[FilterEvent],
        valid_sources: list[str],
        dead_sources: list[dict],
    ) -> list[dict]:
        """并发抓取所有 RSS 信源，每个信源独立验证。"""
        from fetchers.rss import fetch_single_rss

        articles: list[dict] = []

        def _fetch_one(source: dict) -> tuple[dict, list[dict], str | None]:
            """返回 (source, articles, error_msg)"""
            try:
                # 先用 feedparser 快速验证
                d = feedparser.parse(source["rss"])
                if d.get("bozo") and not d.get("entries"):
                    err = str(d.get("bozo_exception", "empty feed"))[:80]
                    return source, [], err

                items = fetch_single_rss(source, hours_lookback=self.hours_lookback_rss)
                return source, items, None
            except Exception as exc:
                return source, [], str(exc)[:80]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(_fetch_one, src): src for src in RSS_SOURCES}
            for future in as_completed(futures):
                source, items, error = future.result()
                src_name = source.get("name", source.get("id", "?"))

                if error:
                    dead_sources.append({"id": source["id"], "name": src_name, "error": error})
                    events.append(FilterEvent(
                        stage="source_validator",
                        item=source["rss"][:70],
                        source=src_name,
                        passed=False,
                        reason=f"抓取失败: {error}",
                    ))
                    self.logger.warning("   ❌ %s: %s", src_name, error)
                else:
                    valid_sources.append(source["id"])
                    articles.extend(items)
                    for a in items:
                        events.append(FilterEvent(
                            stage="source_validator",
                            item=a.get("title", "")[:60],
                            source=src_name,
                            passed=True,
                            reason=f"有效 RSS，共 {len(items)} 条",
                        ))
                    self.logger.info("   ✅ %-30s %3d 条", src_name, len(items))

        return articles
