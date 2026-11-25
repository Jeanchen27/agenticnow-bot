"""
智谱 GLM API 中文编译摘要与评分生成器
批量处理英文信源文章，生成中文标题 + 中文编译摘要 + 标签 + 相关度评分
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_GLM_MODEL = "glm-5.3-flash"

# ─── Prompt ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """你是 @AgenticNow Telegram 频道的主编。频道聚焦五大方向：
1. AI Agent — 自主系统、Agent 框架、MCP、多智能体协作
2. Agentic Web — AI 改变互联网交互方式、平台策略、自主浏览
3. Agentic Economy — AI 驱动的经济变革、Crypto×AI、去中心化计算
4. Agentic Commerce — 自主商业、DeFi、AI 驱动的市场与交易
5. Agentic Payment — Agent 支付、稳定币、金融科技、支付基础设施

你的读者是对 AI 前沿感兴趣的中文读者，关注实际落地与趋势判断。
评分标准：与以上五大方向直接相关给 8-10 分，间接相关给 6-7 分，泛科技/纯行情/无关内容给 1-5 分。

中文编译与写作规范：
- 必须将英文标题与内容准确编译为自然流畅的中文，严禁直接照搬整句英文原文
- 保留核心英文专有术语不强行翻译（如 Agent、MCP、A2A、DAO、RWA、DeFi、LLM、RAG、OPC 及产品/公司名）
- 短句表达，直接进主题，禁用「值得注意的是」「总而言之」「综上所述」等 AI 腔连接词
- 字符串内部引用统一使用中文引号「」或书名号《》，禁止使用英文双引号"""

USER_TEMPLATE = """请将以下英文文章编译为中文精选内容并打分，返回 JSON 数组。

每篇文章必须包含：
- id: 对应输入文章的整数 id（保持一致）
- title_zh: 中文编译标题（≤25字，准确提炼核心信息点，必须包含中文）
- summary_zh: 中文编译摘要（2-3句完整中文，共80-120字。结构：①核心发布了什么/讲了什么 ②为什么重要 ③对 AI/Crypto/实际工作流的影响）
- tags: 3-5个标签（#开头，中英文均可，如 #AIAgent #AgenticPayment #MCP）
- relevance: 与 AgenticNow 主题的相关度整数评分 1-10（10=核心主题，低于6分将不予推送）

⚠️ 重要：所有字符串值内部禁止使用英文双引号（"），改用中文引号「」或书名号《》，否则 JSON 解析会失败。

文章列表：
{articles_json}

直接返回 JSON 数组，不要 markdown 代码块包裹，不要额外解释。

示例格式：
[
  {{
    "id": 0,
    "title_zh": "OpenAI 发布新一代 Realtime Agent 框架",
    "summary_zh": "OpenAI 推出 Realtime Agent API，原生支持多模态工具调用与长期记忆。该框架降低了自主系统开发门槛，数小时内即可完成端到端 Agent 部署。企业自动化工作流正加速向原生 Agent 架构迁移。",
    "tags": ["#AIAgent", "#OpenAI", "#工具调用", "#自主系统"],
    "relevance": 10
  }}
]"""


# ─── Helper ──────────────────────────────────────────────────────────────────

def _has_chinese(text: str) -> bool:
    """检查字符串是否包含至少 2 个中文字符，确保已完成中文编译。"""
    if not text:
        return False
    return len(re.findall(r"[\u4e00-\u9fff]", text)) >= 2


def _build_article_input(articles: list[dict]) -> str:
    """构建发给 GLM 的文章 JSON 输入。"""
    items = []
    for i, art in enumerate(articles):
        items.append(
            {
                "id": i,
                "title": art.get("title", ""),
                "source": art.get("source_name", ""),
                "category": art.get("category", ""),
                "excerpt": art.get("excerpt", "")[:300],
                "url": art.get("url", ""),
            }
        )
    return json.dumps(items, ensure_ascii=False, indent=2)


def _clean_json_text(text: str) -> str:
    """清洗模型输出，剥离 markdown 代码块。"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _fix_unescaped_quotes(text: str) -> str:
    """修复 JSON 字符串值内部的未转义英文双引号，替换为「。"""
    result = []
    in_string = False
    escape_next = False
    i = 0
    while i < len(text):
        ch = text[i]
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == "\\":
            result.append(ch)
            escape_next = True
        elif ch == '"':
            if not in_string:
                in_string = True
                result.append(ch)
            else:
                j = i + 1
                while j < len(text) and text[j] in " \t\r\n":
                    j += 1
                next_ch = text[j] if j < len(text) else ""
                if next_ch in (":", ",", "]", "}", ""):
                    in_string = False
                    result.append(ch)
                else:
                    result.append("\u300c")
        else:
            result.append(ch)
        i += 1
    return "".join(result)


def _extract_json(text: str) -> list[dict]:
    """从 GLM 响应中提取 JSON 数组，兼容 markdown 代码块和裸引号。"""
    text = _clean_json_text(text)

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        candidate = match.group()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            try:
                parsed = json.loads(_fix_unescaped_quotes(candidate))
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Cannot parse JSON from GLM response: {text[:200]}")


def _call_glm_chat(
    user_message: str,
    api_key: str,
    model: str,
    max_retries: int = 3,
) -> str:
    """调用智谱 GLM Chat Completions 接口，带退避重试。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "thinking": {"type": "disabled"},
        "temperature": 0.2,
        "max_tokens": 8192,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    }

    last_error: Optional[Exception] = None
    timeout = httpx.Timeout(120.0, connect=15.0)

    for attempt in range(1, max_retries + 1):
        try:
            resp = httpx.post(GLM_API_URL, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if content:
                    return content
                raise ValueError(f"GLM returned empty content: {resp.text[:200]}")

            if resp.status_code in (429, 500, 502, 503, 504):
                wait_sec = 2 ** attempt
                logger.warning(
                    "GLM API HTTP %d (attempt %d/%d): %s — retrying in %ds",
                    resp.status_code,
                    attempt,
                    max_retries,
                    resp.text[:160],
                    wait_sec,
                )
                time.sleep(wait_sec)
                last_error = RuntimeError(f"GLM HTTP {resp.status_code}: {resp.text[:160]}")
                continue

            raise RuntimeError(f"GLM HTTP {resp.status_code}: {resp.text[:200]}")

        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            wait_sec = 2 ** attempt
            logger.warning(
                "GLM network/timeout error (attempt %d/%d): %s — retrying in %ds",
                attempt,
                max_retries,
                exc,
                wait_sec,
            )
            last_error = exc
            time.sleep(wait_sec)

    raise RuntimeError(f"GLM API failed after {max_retries} attempts: {last_error}")


def _merge_summary(article: dict, summary: dict) -> Optional[dict]:
    """合并单条模型输出，校验中文标题和中文摘要是否有效。"""
    title_zh = (summary.get("title_zh") or "").strip()
    summary_zh = (summary.get("summary_zh") or "").strip()

    if not (_has_chinese(title_zh) and _has_chinese(summary_zh)):
        return None

    try:
        relevance = int(summary.get("relevance", 5))
    except (TypeError, ValueError):
        relevance = 5
    relevance = max(1, min(10, relevance))

    tags = summary.get("tags")
    if not isinstance(tags, list) or not tags:
        cat_tag = article.get("category", "AI").replace("×", "").replace(" ", "")
        tags = [f"#{cat_tag}"]

    return {
        **article,
        "title_zh": title_zh,
        "summary_zh": summary_zh,
        "tags": tags,
        "relevance": relevance,
        "translated": True,
    }


def _untranslated_fallback(article: dict) -> dict:
    """
    若多次重试后仍无法生成中文编译，标记 translated=False 且 relevance=0，
    由下游评分器拦截，绝不将未翻译的英文原文直接推出去。
    """
    return {
        **article,
        "title_zh": "",
        "summary_zh": "",
        "tags": [],
        "relevance": 0,
        "translated": False,
    }


def _summarize_batch_once(
    batch: list[dict],
    api_key: str,
    model: str,
) -> dict[int, dict]:
    """对一批文章调用一次 GLM，返回成功通过中文校验的 {batch_index: merged_article}。"""
    article_json = _build_article_input(batch)
    user_message = USER_TEMPLATE.format(articles_json=article_json)
    response_text = _call_glm_chat(user_message, api_key=api_key, model=model)
    summaries = _extract_json(response_text)

    resolved: dict[int, dict] = {}
    for pos, summary in enumerate(summaries):
        if not isinstance(summary, dict):
            continue
        idx = summary.get("id")
        if not isinstance(idx, int) or not (0 <= idx < len(batch)):
            idx = pos
        if 0 <= idx < len(batch) and idx not in resolved:
            merged = _merge_summary(batch[idx], summary)
            if merged is not None:
                resolved[idx] = merged

    return resolved


# ─── Main ────────────────────────────────────────────────────────────────────

def summarize_articles(
    articles: list[dict],
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> list[dict]:
    """
    使用智谱 GLM API 批量生成中文编译标题、中文摘要与相关度评分。

    每批最多 10 篇文章；若整批失败或部分条目缺失中文翻译，会自动对漏译条目补译重试一次。
    若最终仍失败，则标记 translated=False（relevance=0），杜绝英文原文裸推。
    """
    if not articles:
        return []

    resolved_key = api_key or os.environ.get("GLM_API_KEY")
    if not resolved_key:
        raise ValueError("GLM_API_KEY is not set.")

    resolved_model = model or os.environ.get("GLM_MODEL", DEFAULT_GLM_MODEL)
    enriched: list[dict] = []

    batch_size = 10
    total_batches = (len(articles) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(articles), batch_size):
        batch = articles[batch_idx : batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        logger.info(
            "Summarizing batch %d/%d (%d articles) via %s...",
            batch_num,
            total_batches,
            len(batch),
            resolved_model,
        )

        resolved_map: dict[int, dict] = {}
        try:
            resolved_map = _summarize_batch_once(batch, resolved_key, resolved_model)
        except Exception as exc:
            logger.warning("Batch %d failed (%s), retrying missing items...", batch_num, exc)

        # 对漏译或未返回中文的条目执行一次补译重试
        missing_indices = [i for i in range(len(batch)) if i not in resolved_map]
        if missing_indices:
            retry_articles = [batch[i] for i in missing_indices]
            logger.info(
                "Retrying %d untranslated article(s) in batch %d...",
                len(retry_articles),
                batch_num,
            )
            try:
                retry_map = _summarize_batch_once(retry_articles, resolved_key, resolved_model)
                for sub_idx, merged in retry_map.items():
                    orig_idx = missing_indices[sub_idx]
                    resolved_map[orig_idx] = merged
            except Exception as exc:
                logger.error("Retry failed in batch %d: %s", batch_num, exc)

        for i, art in enumerate(batch):
            if i in resolved_map:
                enriched.append(resolved_map[i])
            else:
                logger.warning(
                    "Article translation failed, dropping untranslated item: %s",
                    art.get("title", "")[:60],
                )
                enriched.append(_untranslated_fallback(art))

        logger.info(
            "Batch %d/%d done (%d/%d translated).",
            batch_num,
            total_batches,
            len(resolved_map),
            len(batch),
        )

    return enriched
