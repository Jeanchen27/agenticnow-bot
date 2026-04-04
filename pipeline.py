#!/usr/bin/env python3
"""
pipeline.py — AgenticNow 多代理流水线

三个子代理串联运行：

  Agent 1: SourceValidatorAgent   — 抓取 + 验证所有 RSS / Reddit / GitHub 信源
      ↓
  Agent 2: ContentScorerAgent     — URL去重 → 关键词过滤 → 预排序 → LLM评分
      ↓
  Agent 3: DraftFormatterAgent    — 配额选取 → Telegram推送

用法：
    python pipeline.py                    # 正式运行
    python pipeline.py --dry-run          # 预览，不推送 Telegram
    python pipeline.py --max-articles 12  # 控制最终推送数量
    python pipeline.py --mode digest      # 合集模式
    python pipeline.py --report           # 运行完成后输出完整过滤报告

报告文件自动保存至 reports/YYYY-MM-DD_HH-MM.json
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agenticnow.pipeline")

sys.path.insert(0, os.path.dirname(__file__))

from agents.base import AgentResult, FilterEvent
from agents.content_scorer import ContentScorerAgent
from agents.draft_formatter import DraftFormatterAgent
from agents.source_validator import SourceValidatorAgent


# ─── 流水线编排器 ──────────────────────────────────────────────────────────────

class AgenticNowPipeline:
    """串联三个子代理的主流水线。"""

    def __init__(
        self,
        dry_run: bool = False,
        max_articles: int = 12,
        publish_mode: str = "individual",
        hours_lookback_rss: int = 168,
        hours_lookback_reddit: int = 48,
        enable_github: bool = True,
        store_path: str = "seen_urls.json",
    ):
        self.dry_run = dry_run
        self.max_articles = max_articles
        self.publish_mode = publish_mode

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        tg_channel = os.environ.get("TELEGRAM_CHANNEL_ID", "@AgenticNow")

        if not api_key:
            logger.error("ANTHROPIC_API_KEY is not set. Exiting.")
            sys.exit(1)
        if not dry_run and not tg_token:
            logger.error("TELEGRAM_BOT_TOKEN is not set (required for live mode). Exiting.")
            sys.exit(1)

        self.agent1 = SourceValidatorAgent(
            hours_lookback_rss=hours_lookback_rss,
            hours_lookback_reddit=hours_lookback_reddit,
            enable_github=enable_github,
        )
        self.agent2 = ContentScorerAgent(
            anthropic_api_key=api_key,
            store_path=store_path,
        )
        self.agent3 = DraftFormatterAgent(
            telegram_token=tg_token,
            telegram_channel=tg_channel,
            anthropic_api_key=api_key,
            dry_run=dry_run,
        )

    def run(self) -> dict:
        """
        执行完整流水线，返回汇总报告 dict。
        """
        started_at = datetime.now(timezone.utc)
        logger.info("═" * 60)
        logger.info("  🤖  AgenticNow Pipeline  |  %s", started_at.strftime("%Y-%m-%d %H:%M UTC"))
        logger.info("  max_articles=%d  mode=%s  %s",
                    self.max_articles, self.publish_mode,
                    "DRY RUN" if self.dry_run else "LIVE")
        logger.info("═" * 60)

        results: list[AgentResult] = []

        # ── Agent 1: 源验证 ──────────────────────────────────────────────────
        logger.info("\n▶ Agent 1 / 3 — 源验证器")
        r1 = self.agent1.run()
        results.append(r1)
        logger.info(r1.summary())

        if not r1.data.get("articles"):
            logger.warning("Agent 1 未抓取到任何文章，流水线终止。")
            return self._build_report(results, started_at)

        # ── Agent 2: 内容评分 ────────────────────────────────────────────────
        logger.info("\n▶ Agent 2 / 3 — 内容评分器")
        r2 = self.agent2.run(
            articles=r1.data["articles"],
            max_articles=self.max_articles,
        )
        results.append(r2)
        logger.info(r2.summary())

        if not r2.data.get("scored_articles"):
            logger.warning("Agent 2 无文章通过评分，流水线终止。")
            return self._build_report(results, started_at)

        # ── Agent 3: 草稿格式化 + 推送 ──────────────────────────────────────
        logger.info("\n▶ Agent 3 / 3 — 草稿格式器")
        r3 = self.agent3.run(
            scored_articles=r2.data["scored_articles"],
            url_store=r2.data["url_store"],
            max_articles=self.max_articles,
            publish_mode=self.publish_mode,
        )
        results.append(r3)
        logger.info(r3.summary())

        # ── Digest 生成 ──────────────────────────────────────────────────────
        final_articles = r3.data.get("final_articles", [])
        if not self.dry_run and final_articles:
            digest_path = _save_digest(final_articles, started_at)
            logger.info("📝 Daily digest 已保存至 %s", digest_path)

        report = self._build_report(results, started_at)
        logger.info("\n%s", _format_pipeline_summary(report))
        return report

    # ── 报告生成 ──────────────────────────────────────────────────────────────

    def _build_report(self, results: list[AgentResult], started_at: datetime) -> dict:
        all_events = []
        for r in results:
            for e in r.events:
                all_events.append({
                    "stage":   e.stage,
                    "source":  e.source,
                    "title":   e.item,
                    "passed":  e.passed,
                    "reason":  e.reason,
                    "detail":  e.detail,
                })

        # 汇总每个阶段通过 / 拒绝数
        stage_stats: dict[str, dict] = {}
        for e in all_events:
            s = stage_stats.setdefault(e["stage"], {"passed": 0, "filtered": 0})
            if e["passed"]:
                s["passed"] += 1
            else:
                s["filtered"] += 1

        # 死链列表
        dead_sources = []
        if results:
            dead_sources = results[0].data.get("dead_sources", [])

        # 最终推送文章
        final_articles = []
        if len(results) >= 3:
            final_articles = [
                {
                    "title": a.get("title_zh") or a.get("title", ""),
                    "source": a.get("source_name", ""),
                    "type": a.get("type", ""),
                    "relevance": a.get("relevance", 0),
                    "url": a.get("url", ""),
                }
                for a in results[2].data.get("final_articles", [])
            ]

        return {
            "pipeline_run": {
                "started_at": started_at.isoformat(),
                "dry_run": self.dry_run,
                "max_articles": self.max_articles,
            },
            "stage_stats": stage_stats,
            "dead_sources": dead_sources,
            "final_articles": final_articles,
            "filter_log": all_events,
            "agent_durations": {
                r.agent_name: round(r.duration_sec, 2) for r in results
            },
        }


# ── 报告输出 ───────────────────────────────────────────────────────────────────

def _format_pipeline_summary(report: dict) -> str:
    lines = ["═" * 60, "  📊  Pipeline 执行摘要", "═" * 60]

    for stage, stats in report["stage_stats"].items():
        lines.append(
            f"  {stage:<25} ✅ {stats['passed']:>4} 通过   ❌ {stats['filtered']:>4} 过滤"
        )

    lines.append("─" * 60)

    dead = report.get("dead_sources", [])
    if dead:
        lines.append(f"  ⚠️  死链 / 失效信源: {len(dead)} 个")
        for d in dead:
            lines.append(f"     ✗ {d['name']}: {d['error']}")

    lines.append("─" * 60)
    lines.append(f"  📤 最终推送: {len(report['final_articles'])} 条")
    for i, a in enumerate(report["final_articles"], 1):
        lines.append(
            f"     {i:>2}. [{a['type']:<10}] [{a['relevance']}/10] {a['title'][:45]}"
        )

    lines.append("─" * 60)
    durations = report.get("agent_durations", {})
    total = sum(durations.values())
    for name, sec in durations.items():
        lines.append(f"  ⏱  {name:<25} {sec:.1f}s")
    lines.append(f"  ⏱  {'total':<25} {total:.1f}s")
    lines.append("═" * 60)

    return "\n".join(lines)


def _save_digest(articles: list[dict], run_time: datetime, digest_dir: str = "daily-digest") -> str:
    Path(digest_dir).mkdir(exist_ok=True)
    date_str = run_time.strftime("%Y-%m-%d")
    path = f"{digest_dir}/{date_str}.md"

    lines = [
        "---",
        f"date: {date_str}",
        f"source_count: {len(articles)}",
        "---",
        "",
        "# AgenticNow Daily Digest",
        "",
        "## 文章列表",
        "",
    ]
    for art in articles:
        title = art.get("title_zh") or art.get("title", "")
        url = art.get("url", "")
        source = art.get("source_name", "")
        score = art.get("relevance", "")
        summary = art.get("summary_zh", "")
        lines += [
            f"### [{title}]({url})",
            f"- 来源：{source}",
            f"- 评分：{score}",
            f"- 摘要：{summary}",
            "",
        ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def _save_report(report: dict, reports_dir: str = "reports") -> str:
    Path(reports_dir).mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    path = f"{reports_dir}/{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return path


def _print_filter_report(report: dict) -> None:
    """以表格形式打印完整过滤日志。"""
    events = report.get("filter_log", [])
    if not events:
        print("无过滤记录。")
        return

    print(f"\n{'阶段':<25} {'来源':<18} {'通过':<5} {'原因':<28} {'标题'}")
    print("─" * 110)
    for e in events:
        icon = "✅" if e["passed"] else "❌"
        stage = e["stage"][:24]
        source = e["source"][:17]
        reason = e["reason"][:27]
        title = e["title"][:38]
        print(f"{stage:<25} {source:<18} {icon:<5} {reason:<28} {title}")
    print("─" * 110)
    print(f"合计：{sum(1 for e in events if e['passed'])} 通过 / "
          f"{sum(1 for e in events if not e['passed'])} 过滤\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="AgenticNow 多代理流水线 — RSS 聚合 → 评分 → Telegram 推送"
    )
    p.add_argument("--dry-run", action="store_true", help="预览模式，不推送 Telegram")
    p.add_argument("--max-articles", type=int, default=12, help="最终推送文章数（默认 12）")
    p.add_argument("--mode", choices=["individual", "digest"], default="individual",
                   help="推送格式：individual（逐条）或 digest（合集）")
    p.add_argument("--rss-lookback", type=int, default=168, help="RSS 时间窗口（小时，默认 168）")
    p.add_argument("--reddit-lookback", type=int, default=48, help="Reddit 时间窗口（小时，默认 48）")
    p.add_argument("--no-github", action="store_true", help="禁用 GitHub Trending")
    p.add_argument("--report", action="store_true", help="打印完整过滤报告")
    p.add_argument("--save-report", action="store_true", help="将报告保存至 reports/ 目录")
    p.add_argument("--store", default="seen_urls.json", help="URL 去重存储文件路径")
    args = p.parse_args()

    pipeline = AgenticNowPipeline(
        dry_run=args.dry_run,
        max_articles=args.max_articles,
        publish_mode=args.mode,
        hours_lookback_rss=args.rss_lookback,
        hours_lookback_reddit=args.reddit_lookback,
        enable_github=not args.no_github,
        store_path=args.store,
    )

    report = pipeline.run()

    if args.report:
        _print_filter_report(report)

    if args.save_report:
        path = _save_report(report)
        logger.info("📄 报告已保存至 %s", path)


if __name__ == "__main__":
    main()
