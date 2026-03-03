#!/usr/bin/env python3
"""
AgenticNow 信源健康检测工具
─────────────────────────────
并发检测所有 RSS/Substack 信源，输出状态报告。

用法:
    python scripts/check_sources.py              # 摘要报告
    python scripts/check_sources.py --verbose    # 显示每篇文章标题
    python scripts/check_sources.py --category Newsletter  # 只检测某分类
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# 将项目根目录加入 sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import feedparser
import httpx
from sources import RSS_SOURCES

# ─── ANSI 颜色 ────────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
GRAY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AgenticNow-Checker/1.0; "
        "+https://t.me/AgenticNow)"
    ),
    "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
}

TIMEOUT = 15  # 秒


# ─── 核心检测 ─────────────────────────────────────────────────────────────────

def check_source(source: dict, hours_lookback: int = 48) -> dict:
    """
    检测单个 RSS 信源并返回状态字典。

    Returns:
        {
            "source": source dict,
            "status": "ok" | "empty" | "stale" | "error",
            "total_entries": int,
            "recent_entries": int,   # within hours_lookback
            "latest_date": str | None,
            "error": str | None,
            "elapsed_ms": int,
        }
    """
    t0 = time.time()
    result = {
        "source": source,
        "status": "error",
        "total_entries": 0,
        "recent_entries": 0,
        "latest_date": None,
        "error": None,
        "elapsed_ms": 0,
    }

    rss_url = source.get("rss") or source.get("url", "")
    if not rss_url:
        result["error"] = "No RSS URL"
        return result

    try:
        resp = httpx.get(rss_url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        if feed.bozo and not feed.entries:
            result["error"] = f"Feed parse error: {getattr(feed, 'bozo_exception', 'unknown')}"
            return result

        entries = feed.entries
        result["total_entries"] = len(entries)

        now = datetime.now(timezone.utc)
        cutoff_hours = hours_lookback

        recent = []
        latest = None

        for entry in entries:
            pub = None
            for field in ("published_parsed", "updated_parsed"):
                t = getattr(entry, field, None)
                if t:
                    try:
                        import calendar
                        pub = datetime.fromtimestamp(
                            calendar.timegm(t), tz=timezone.utc
                        )
                    except Exception:
                        pass
                    break

            if pub:
                if latest is None or pub > latest:
                    latest = pub
                hours_old = (now - pub).total_seconds() / 3600
                if hours_old <= cutoff_hours:
                    recent.append(entry)

        result["recent_entries"] = len(recent)
        result["latest_date"] = latest.strftime("%Y-%m-%d %H:%M") if latest else None

        if len(entries) == 0:
            result["status"] = "empty"
        elif len(recent) == 0:
            result["status"] = "stale"
        else:
            result["status"] = "ok"

    except httpx.TimeoutException:
        result["error"] = f"Timeout (>{TIMEOUT}s)"
    except httpx.HTTPStatusError as e:
        result["error"] = f"HTTP {e.response.status_code}"
    except Exception as e:
        result["error"] = str(e)[:80]
    finally:
        result["elapsed_ms"] = int((time.time() - t0) * 1000)

    return result


def status_icon(status: str) -> str:
    return {
        "ok":    f"{GREEN}✅{RESET}",
        "stale": f"{YELLOW}⚠️ {RESET}",
        "empty": f"{YELLOW}🈳{RESET}",
        "error": f"{RED}❌{RESET}",
    }.get(status, "❓")


# ─── 主程序 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="AgenticNow 信源健康检测")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--category", "-c", default=None, help="只检测指定分类")
    parser.add_argument(
        "--hours", type=int, default=48, help="判断「近期」的时间窗口（小时，默认 48）"
    )
    parser.add_argument(
        "--workers", type=int, default=10, help="并发线程数（默认 10）"
    )
    args = parser.parse_args()

    sources = RSS_SOURCES
    if args.category:
        sources = [s for s in sources if s.get("category", "").lower() == args.category.lower()]
        if not sources:
            print(f"{RED}未找到分类 '{args.category}' 的信源。{RESET}")
            sys.exit(1)

    print(f"\n{BOLD}AgenticNow 信源健康检测{RESET}")
    print(f"共 {len(sources)} 个信源 | 时间窗口: {args.hours}h | 并发: {args.workers} 线程")
    print("─" * 70)

    results = []
    t_start = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(check_source, s, args.hours): s
            for s in sources
        }
        done = 0
        for future in as_completed(futures):
            done += 1
            r = future.result()
            results.append(r)
            src = r["source"]
            icon = status_icon(r["status"])
            name = src.get("name", src.get("id", "?"))[:30]
            cat  = src.get("category", "")[:12]

            if r["status"] == "ok":
                detail = (
                    f"{GREEN}{r['recent_entries']} 篇近期{RESET} / "
                    f"{r['total_entries']} 篇总计"
                )
            elif r["status"] == "stale":
                detail = (
                    f"{YELLOW}最新: {r['latest_date'] or 'unknown'}{RESET} "
                    f"({r['total_entries']} 篇但超过 {args.hours}h)"
                )
            elif r["status"] == "empty":
                detail = f"{YELLOW}Feed 为空{RESET}"
            else:
                detail = f"{RED}{r['error']}{RESET}"

            ms = f"{GRAY}{r['elapsed_ms']}ms{RESET}"
            print(f"  {icon} [{done:>2}/{len(sources)}] {name:<30} {cat:<14} {detail} {ms}")

    elapsed = time.time() - t_start

    # ─── 汇总 ──────────────────────────────────────────────────────────────────
    ok     = [r for r in results if r["status"] == "ok"]
    stale  = [r for r in results if r["status"] == "stale"]
    empty  = [r for r in results if r["status"] == "empty"]
    errors = [r for r in results if r["status"] == "error"]

    print("\n" + "─" * 70)
    print(f"{BOLD}检测完成  ·  耗时 {elapsed:.1f}s{RESET}")
    print(
        f"  {GREEN}✅ 正常: {len(ok)}{RESET}  "
        f"{YELLOW}⚠️  陈旧: {len(stale)}{RESET}  "
        f"{YELLOW}🈳 空: {len(empty)}{RESET}  "
        f"{RED}❌ 错误: {len(errors)}{RESET}"
    )

    if errors:
        print(f"\n{RED}{BOLD}── 错误信源（建议检查或替换 RSS 地址）──{RESET}")
        for r in sorted(errors, key=lambda x: x["source"].get("name", "")):
            name = r["source"].get("name", r["source"].get("id", "?"))
            rss  = r["source"].get("rss", r["source"].get("url", ""))
            print(f"  • {name:<30} {r['error']}")
            if args.verbose:
                print(f"    {GRAY}{rss}{RESET}")

    if stale:
        print(f"\n{YELLOW}{BOLD}── 陈旧信源（超过 {args.hours}h 无新内容）──{RESET}")
        for r in sorted(stale, key=lambda x: x["latest_date"] or ""):
            name   = r["source"].get("name", r["source"].get("id", "?"))
            latest = r["latest_date"] or "未知"
            print(f"  • {name:<30} 最新: {latest}")

    if args.verbose and ok:
        print(f"\n{GREEN}{BOLD}── 正常信源详情 ──{RESET}")
        for r in sorted(ok, key=lambda x: -x["recent_entries"]):
            name = r["source"].get("name", r["source"].get("id", "?"))
            print(
                f"  • {name:<30} "
                f"{r['recent_entries']:>3} 篇近期 / {r['total_entries']:>3} 篇 "
                f"| 最新: {r['latest_date'] or '?'}"
            )

    print()
    # 非零退出码方便 CI 捕获
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
