"""
Telegram 频道推送器
支持「单篇推送」和「每日摘要」两种模式
"""

import logging
import time
from datetime import datetime

import httpx

from sources import CATEGORY_EMOJI

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}"
MAX_MESSAGE_LENGTH = 4096  # Telegram 单条消息最大字符数


class TelegramPublisher:
    """Telegram 频道内容推送器。"""

    def __init__(self, bot_token: str, channel_id: str):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self._api_base = f"https://api.telegram.org/bot{bot_token}"

    # ─── 格式化 ───────────────────────────────────────────────────────────────

    def _get_emoji(self, category: str) -> str:
        return CATEGORY_EMOJI.get(category, CATEGORY_EMOJI["default"])

    def format_article(self, article: dict) -> str:
        """
        将单篇文章格式化为 Telegram HTML 消息。

        示例输出：
        🤖 <b>OpenAI 发布新一代 Agent 框架</b>

        OpenAI 推出...

        📌 <a href="...">阅读原文</a> · <i>The Rundown AI</i>

        #AIAgent #OpenAI
        """
        emoji = self._get_emoji(article.get("category", ""))
        title_zh = article.get("title_zh") or article.get("title", "无标题")
        summary_zh = article.get("summary_zh", "")
        tags = article.get("tags", [])
        source_name = article.get("source_name", "")
        url = article.get("url", "")
        category = article.get("category", "")

        parts = [f"{emoji} <b>{_escape_html(title_zh)}</b>", ""]

        if summary_zh:
            parts.append(_escape_html(summary_zh))
            parts.append("")

        # 来源行
        source_line = f'📌 <a href="{url}">阅读原文</a>'
        if source_name:
            source_line += f" · <i>{_escape_html(source_name)}</i>"
        if category:
            source_line += f" · {category}"
        parts.append(source_line)

        # 标签行
        if tags:
            parts.append("")
            parts.append(" ".join(tags[:5]))

        return "\n".join(parts)

    def format_daily_header(self, date: datetime, count: int) -> str:
        """每日摘要开头横幅。"""
        date_str = date.strftime("%Y年%m月%d日")
        return (
            f"🗞️ <b>AgenticNow · 今日精选</b>\n"
            f"{date_str} | 精选 {count} 篇\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

    # ─── 发送 ─────────────────────────────────────────────────────────────────

    def _send(self, text: str, disable_preview: bool = True) -> dict:
        """向频道发送一条 HTML 格式消息，含重试逻辑。"""
        url = f"{self._api_base}/sendMessage"
        payload = {
            "chat_id": self.channel_id,
            "text": text[:MAX_MESSAGE_LENGTH],
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_preview,
        }

        for attempt in range(3):
            try:
                resp = httpx.post(url, json=payload, timeout=15)
                result = resp.json()

                if result.get("ok"):
                    return result

                error_desc = result.get("description", "Unknown error")
                logger.warning("Telegram error (attempt %d): %s", attempt + 1, error_desc)

                # 若是频率限制，等待后重试
                if "Too Many Requests" in error_desc:
                    retry_after = result.get("parameters", {}).get("retry_after", 30)
                    logger.info("Rate limited, waiting %ds...", retry_after)
                    time.sleep(retry_after)
                else:
                    break  # 非限速错误不重试

            except httpx.TimeoutException:
                logger.warning("Telegram timeout (attempt %d)", attempt + 1)
                time.sleep(5)
            except Exception as exc:
                logger.error("Telegram error: %s", exc)
                break

        return {"ok": False}

    # ─── 推送模式 ─────────────────────────────────────────────────────────────

    def publish_individual(self, articles: list[dict]) -> int:
        """
        单篇推送模式：每篇文章发一条独立消息。
        Telegram 同一频道限制：约 20 条/分钟，每条间隔 3s。
        """
        published = 0
        for article in articles:
            text = self.format_article(article)
            result = self._send(text)
            if result.get("ok"):
                published += 1
                logger.info(
                    "✅ Published: %s",
                    article.get("title_zh", article.get("title", ""))[:50],
                )
            else:
                logger.error(
                    "❌ Failed: %s",
                    article.get("title_zh", article.get("title", ""))[:50],
                )
            time.sleep(3)  # 每条消息间隔 3 秒

        return published

    def publish_digest(self, articles: list[dict]) -> int:
        """
        日报合集模式：先发一条横幅，再分组发文章列表。
        每组 5 篇，避免超出消息长度限制。
        """
        if not articles:
            return 0

        # 发横幅
        header = self.format_daily_header(datetime.now(), len(articles))
        self._send(header)
        time.sleep(2)

        # 分组发文章摘要（每组5篇）
        published = 0
        CHUNK = 5
        for i in range(0, len(articles), CHUNK):
            chunk = articles[i : i + CHUNK]
            lines = []
            for j, art in enumerate(chunk, i + 1):
                title_zh = art.get("title_zh") or art.get("title", "")
                summary_zh = art.get("summary_zh", "")
                url = art.get("url", "")
                source = art.get("source_name", "")
                emoji = self._get_emoji(art.get("category", ""))

                item = (
                    f"{emoji} <b>{j}. {_escape_html(title_zh)}</b>\n"
                    f"{_escape_html(summary_zh[:80])}...\n"
                    f'🔗 <a href="{url}">{_escape_html(source)}</a>'
                )
                lines.append(item)

            text = "\n\n".join(lines)
            result = self._send(text)
            if result.get("ok"):
                published += len(chunk)
            time.sleep(3)

        return published

    def publish_articles(
        self, articles: list[dict], mode: str = "individual"
    ) -> int:
        """
        统一推送入口。

        Args:
            articles: 已处理的文章列表
            mode: "individual"（默认）或 "digest"

        Returns:
            成功发送的文章数量
        """
        if not articles:
            logger.info("No articles to publish.")
            return 0

        if mode == "digest":
            count = self.publish_digest(articles)
        else:
            count = self.publish_individual(articles)

        logger.info("Published %d/%d articles to %s", count, len(articles), self.channel_id)
        return count


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def _escape_html(text: str) -> str:
    """转义 Telegram HTML 特殊字符。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
