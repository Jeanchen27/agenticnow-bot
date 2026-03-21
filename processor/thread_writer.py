"""
X Thread 生成器
从每日推送的文章中精选 2-3 条，生成英文 X Thread（每条 ≤280 字符）
"""

import json
import logging
import re
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the social media editor for @AgenticNow, a media brand covering:
- AI Agents & autonomous systems
- Agentic Web, Economy, Commerce & Payment

Your job: turn curated news articles into engaging English X (Twitter) threads.

Rules:
- Each tweet MUST be ≤ 280 characters (STRICT LIMIT, count carefully)
- Each thread has 3 tweets: hook → insight → takeaway
- Use plain text, no markdown
- Use 1-2 emojis per tweet max
- Include 2-3 hashtags ONLY in the last tweet
- The last tweet must include a source attribution
- Be opinionated and insightful, not just summarizing
- Write for a tech-savvy audience interested in AI and crypto"""

USER_TEMPLATE = """From the following articles (already published in our Telegram channel today), pick the TOP 2 most impactful stories and write an X Thread for each.

Each thread = exactly 3 tweets. Each tweet ≤ 280 characters (STRICT).

Articles:
{articles_json}

Return a JSON array of thread objects:
[
  {{
    "article_index": 0,
    "article_title": "original title",
    "tweets": [
      "🧵 1/3 First tweet text here (≤280 chars)",
      "2/3 Second tweet text here (≤280 chars)",
      "3/3 Third tweet with source and hashtags (≤280 chars)"
    ]
  }}
]

Return ONLY valid JSON. No markdown wrapping. No explanation."""


def generate_threads(
    articles: list[dict],
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    从推送文章中精选 2 条，生成英文 X Thread。

    Args:
        articles: 已推送的文章列表（含 title_zh、summary_zh、url 等）
        api_key: Anthropic API key

    Returns:
        thread 列表，每个含 article_title 和 tweets[]
    """
    if not articles:
        return []

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    # 构建文章输入
    items = []
    for i, art in enumerate(articles):
        items.append({
            "index": i,
            "title": art.get("title", ""),
            "title_zh": art.get("title_zh", ""),
            "summary_zh": art.get("summary_zh", ""),
            "source": art.get("source_name", ""),
            "category": art.get("category", ""),
            "url": art.get("url", ""),
        })

    articles_json = json.dumps(items, ensure_ascii=False, indent=2)
    user_message = USER_TEMPLATE.format(articles_json=articles_json)

    try:
        with client.messages.stream(
            model="claude-haiku-4-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            response = stream.get_final_message()

        text = response.content[0].text.strip()
        # 清理 markdown 包裹
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        threads = json.loads(text)

        # 验证每条推文 ≤ 280 字符
        for thread in threads:
            for i, tweet in enumerate(thread.get("tweets", [])):
                if len(tweet) > 280:
                    # 截断到 280（保险措施，Claude 应该已经控制好了）
                    thread["tweets"][i] = tweet[:277] + "..."
                    logger.warning(
                        "Tweet truncated to 280 chars: %s...", tweet[:50]
                    )

        logger.info("Generated %d X threads", len(threads))
        return threads

    except Exception as exc:
        logger.error("Failed to generate X threads: %s", exc)
        return []


def format_thread_for_telegram(thread: dict, thread_num: int) -> str:
    """
    将一个 thread 格式化为 Telegram 消息（供人工审阅复制）。

    输出示例：
    ━━━━━━━━━━━━━━━━━━━━
    🐦 X Thread #1
    ━━━━━━━━━━━━━━━━━━━━

    🧵 1/3
    First tweet text...

    2/3
    Second tweet text...

    3/3
    Third tweet with hashtags...

    ━━━━━━━━━━━━━━━━━━━━
    📋 复制以上内容发布到 X
    """
    tweets = thread.get("tweets", [])
    title = thread.get("article_title", "")

    lines = [
        "━━━━━━━━━━━━━━━━━━━━",
        f"🐦 <b>X Thread #{thread_num}</b>",
        f"<i>{_escape_html(title)}</i>",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for tweet in tweets:
        lines.append(_escape_html(tweet))
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("📋 复制以上内容发布到 X")

    return "\n".join(lines)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
