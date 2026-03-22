"""
agents/base.py
AgentResult 数据类 + BaseAgent 基类

每个子代理都继承 BaseAgent，run() 返回 AgentResult。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FilterEvent:
    """单条过滤/决策日志。"""
    stage: str          # "source_validator" | "content_scorer" | "draft_formatter"
    item: str           # 文章标题或 URL（截断）
    source: str         # 信源名称
    passed: bool        # True = 通过，False = 被过滤
    reason: str         # 过滤原因描述
    detail: str = ""    # 额外细节（可选）


@dataclass
class AgentResult:
    """代理运行结果标准格式。"""
    agent_name: str
    success: bool
    data: dict[str, Any]              # 传递给下一个代理的结构化数据
    events: list[FilterEvent] = field(default_factory=list)
    duration_sec: float = 0.0
    error: str = ""

    # ── 便捷统计 ──────────────────────────────────────────────────────────────

    @property
    def passed_count(self) -> int:
        return sum(1 for e in self.events if e.passed)

    @property
    def filtered_count(self) -> int:
        return sum(1 for e in self.events if not e.passed)

    def summary(self) -> str:
        return (
            f"[{self.agent_name}] "
            f"✅ {self.passed_count} passed  "
            f"❌ {self.filtered_count} filtered  "
            f"⏱ {self.duration_sec:.1f}s"
            + (f"  ⚠️ {self.error}" if self.error else "")
        )


class BaseAgent:
    """所有子代理的基类。"""

    name: str = "base"

    def __init__(self):
        self.logger = logging.getLogger(f"agenticnow.agent.{self.name}")

    def run(self, *args, **kwargs) -> AgentResult:
        raise NotImplementedError

    def _timed_run(self, fn, *args, **kwargs) -> AgentResult:
        """计时包装器，自动记录耗时。"""
        t0 = time.perf_counter()
        result: AgentResult = fn(*args, **kwargs)
        result.duration_sec = time.perf_counter() - t0
        return result
