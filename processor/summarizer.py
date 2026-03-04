"""
Claude API 摘要生成器
批量处理文章，生成中文标题 + 摘要 + 标签 + 相关度评分
"""

import json
import logging
import re
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

# ─── Prompt ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """你是 @AgenticNow Telegram频道的内容编辑。频道专注于：
- AI Agent 与自主系统（核心主题）
- AI × Crypto / Web3 / 去中心化计算
- Agentic 支付与金融科技
- AI 实用工具与工作流自动化
- AI 带来的未来工作与经济变革

你的读者是对 AI 前沿感兴趣的中文用户，具备一定技术背景，关注实际落地。"""

USER_TEMPLATE = """请为以下英文文章生成中文摘要，返回 JSON 数组。

每篇文章必须包含：
- title_zh: 中文标题（≤25字，准确且有吸引力，突出核心信息点）
- summary_zh: 中文摘要（2-3句，共80-120字。格式：①是什么 ②为什么重要 ③对 AI/Crypto/工作的影响）
- tags: 3-5个标签（#开头，中英文均可，如 #AIAgent #Agentic支付 #去中心化）
- relevance: 与AgenticNow主题的相关度评分 1-10（10=核心主题，1=不相关）

文章列表：
{articles_json}

直接返回 JSON 数组，不要 markdown 包裹，不要额外解释。

示例格式：
[
  {{
    "title_zh": "OpenAI 发布新一代 Agent 框架",
    "summary_zh": "OpenAI 推出名为 Realtime Agent API 的新框架，支持多模态工具调用与长期记忆。该框架大幅降低构建自主 AI 系统的门槛，开发者可在数小时内完成端到端 Agent 部署。这标志着 AI Agent 商业化进入快速普及阶段，对企业自动化流程影响深远。",
    "tags": ["#AIAgent", "#OpenAI", "#自主系统", "#工具调用"],
    "relevance": 10
  }}
]"""


# ─── Helper ──────────────────────────────────────────────────────────────────

def _build_article_input(articles: list[dict]) -> str:
    """构建发给 Claude 的文章 JSON 输入。"""
    items = []
    for i, art in enumerate(articles):
        items.append(
            {
                "id": i,
                "title": art.get("title", ""),
                "source": art.get("source_name", ""),
                "category": art.get("category", ""),
                "excerpt": art.get("excerpt", "")[:400],
                "url": art.get("url", ""),
            }
        )
    return json.dumps(items, ensure_ascii=False, indent=2)


def _extract_json(text: str) -> list[dict]:
    """从 Claude 响应中提取 JSON 数组，兼容 markdown 代码块。"""
    # 去掉 markdown code block
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取第一个 JSON 数组
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Cannot parse JSON from response: {text[:200]}")


def _fallback_article(article: dict) -> dict:
    """若 Claude 调用失败，返回带原始标题的文章（无中文摘要）。"""
    return {
        **article,
        "title_zh": article.get("title", ""),
        "summary_zh": article.get("excerpt", "")[:100],
        "tags": [f"#{article.get('category', 'AI').replace('×', '').replace(' ', '')}"],
        "relevance": 5,
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def summarize_articles(
    articles: list[dict],
    api_key: Optional[str] = None,
) -> list[dict]:
    """
    使用 Claude API 批量生成中文摘要。

    每批最多 15 篇文章，使用流式请求（避免超时）。
    若某批失败则降级为原始标题，不中断整体流程。

    Args:
        articles: 文章字典列表（含 title、excerpt、category 等）
        api_key:  可选，若不传则读取 ANTHROPIC_API_KEY 环境变量

    Returns:
        enriched_articles: 每篇文章额外包含 title_zh、summary_zh、tags、relevance
    """
    if not articles:
        return []

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    enriched: list[dict] = []

    BATCH_SIZE = 15
    total_batches = (len(articles) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(articles), BATCH_SIZE):
        batch = articles[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        logger.info("Summarizing batch %d/%d (%d articles)...", batch_num, total_batches, len(batch))

        try:
            article_json = _build_article_input(batch)
            user_message = USER_TEMPLATE.format(articles_json=article_json)

            # 使用 streaming 避免长请求超时
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()

            response_text = response.content[0].text
            summaries = _extract_json(response_text)

            # 将摘要合并回原文章
            for j, summary in enumerate(summaries):
                if j < len(batch):
                    enriched.append(
                        {
                            **batch[j],
                            "title_zh": summary.get("title_zh") or batch[j].get("title", ""),
                            "summary_zh": summary.get("summary_zh", ""),
                            "tags": summary.get("tags", []),
                            "relevance": int(summary.get("relevance", 5)),
                        }
                    )

            # 若 Claude 返回条数少于发送条数，用 fallback 补齐
            if len(summaries) < len(batch):
                for k in range(len(summaries), len(batch)):
                    enriched.append(_fallback_article(batch[k]))

            logger.info("Batch %d/%d done.", batch_num, total_batches)

        except ValueError as exc:
            logger.error("JSON parse error in batch %d: %s", batch_num, exc)
            for article in batch:
                enriched.append(_fallback_article(article))

        except anthropic.APIError as exc:
            logger.error("Claude API error in batch %d: %s", batch_num, exc)
            for article in batch:
                enriched.append(_fallback_article(article))

        except Exception as exc:
            logger.error("Unexpected error in batch %d: %s", batch_num, exc)
            for article in batch:
                enriched.append(_fallback_article(article))

    return enriched
