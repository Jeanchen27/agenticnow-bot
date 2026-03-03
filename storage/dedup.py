"""
URL 去重存储
追踪已发送文章的 URL，避免重复推送
使用 JSON 文件持久化，30天后自动过期清理
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_AGE_DAYS = 30
DEFAULT_PATH = "seen_urls.json"


class URLStore:
    """持久化 URL 去重存储器。"""

    def __init__(self, store_path: str = DEFAULT_PATH):
        self.store_path = Path(store_path)
        self._data: dict[str, str] = {}  # url -> ISO datetime（首次发现时间）
        self._load()

    # ─── 持久化 ───────────────────────────────────────────────────────────────

    def _load(self):
        """从磁盘加载已记录的 URL。"""
        if self.store_path.exists():
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info("Loaded %d URLs from store (%s)", len(self._data), self.store_path)
            except Exception as exc:
                logger.error("Failed to load URL store: %s", exc)
                self._data = {}
        else:
            self._data = {}

    def save(self):
        """将当前 URL 集合保存到磁盘（保存前自动清理过期记录）。"""
        self._prune()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d URLs to store", len(self._data))

    def _prune(self):
        """删除超过 MAX_AGE_DAYS 天的记录。"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
        to_delete = []

        for url, date_str in self._data.items():
            try:
                dt = datetime.fromisoformat(date_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    to_delete.append(url)
            except Exception:
                to_delete.append(url)  # 格式异常的记录一并清理

        for url in to_delete:
            del self._data[url]

        if to_delete:
            logger.info("Pruned %d expired URLs", len(to_delete))

    # ─── 查询与标记 ──────────────────────────────────────────────────────────

    def is_seen(self, url: str) -> bool:
        """判断 URL 是否已发送过。"""
        return url in self._data

    def mark_seen(self, url: str):
        """标记单个 URL 为已发送。"""
        self._data[url] = datetime.now(timezone.utc).isoformat()

    def mark_seen_batch(self, urls: list[str]):
        """批量标记 URL 为已发送。"""
        now = datetime.now(timezone.utc).isoformat()
        for url in urls:
            self._data[url] = now

    def filter_new(self, articles: list[dict]) -> list[dict]:
        """
        从文章列表中过滤掉已发送过的文章。

        Args:
            articles: 文章字典列表，每条必须含 "url" 字段

        Returns:
            只含新文章的列表
        """
        new = [a for a in articles if not self.is_seen(a.get("url", ""))]
        logger.info(
            "Dedup: %d total → %d new (%d already seen)",
            len(articles),
            len(new),
            len(articles) - len(new),
        )
        return new

    @property
    def total(self) -> int:
        """当前存储的 URL 总数。"""
        return len(self._data)
