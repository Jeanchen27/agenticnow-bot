"""
tests/fixtures.py
测试数据固件

包含：
- 20 篇标注文章（相关 / 不相关）
- 10 对重复文章对（应被去重）
- 10 对非重复文章对（不应被去重）

标注说明：
  relevant=True  → 与 AgenticNow 定位相关，应通过过滤器
  relevant=False → 不相关，应被过滤器拒绝
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Article:
    title: str
    excerpt: str = ""
    relevant: bool = True          # 预期过滤结果
    reason: str = ""               # 标注说明
    source_id: str = "bankless"    # 默认使用需要关键词过滤的信源
    url: str = ""
    relevance_score: int = 7       # 预期 LLM 相关度（供参考，非强断言）


# ── 20 篇标注文章 ─────────────────────────────────────────────────────────────
# 前 10 篇：相关（应通过）
# 后 10 篇：不相关（应被拒绝）

ANNOTATED_ARTICLES: list[Article] = [

    # ── 相关（True）──────────────────────────────────────────────────────────

    Article(
        title="OpenAI Releases GPT-5 with Autonomous Agent Capabilities",
        excerpt="The new model can browse the web, run code, and complete multi-step tasks without human supervision.",
        relevant=True,
        reason="核心 AI Agent 新闻，含 openai + agent 双关键词",
    ),
    Article(
        title="Anthropic Launches Claude 4 with Computer Use API",
        excerpt="Claude 4 can interact with desktop applications, browse the web, and execute code autonomously.",
        relevant=True,
        reason="Anthropic + autonomous，符合 AI Agent 定位",
    ),
    Article(
        title="Model Context Protocol (MCP) Hits 10,000 Servers",
        excerpt="The open standard for connecting AI agents to data sources sees explosive developer adoption.",
        relevant=True,
        reason="MCP 是短词关键词，精确命中",
    ),
    Article(
        title="Agentic Commerce: AI Bots Now Complete Purchases Autonomously",
        excerpt="Shopify and Stripe have partnered to enable AI agent-initiated transactions.",
        relevant=True,
        reason="agentic 长词子串匹配 + 定位核心词",
    ),
    Article(
        title="LLM Inference Costs Drop 90% in 18 Months",
        excerpt="The commoditization of large language model inference is reshaping the AI startup landscape.",
        relevant=True,
        reason="LLM 短词词边界匹配",
    ),
    Article(
        title="Stripe Integrates AI Payment Agent for B2B Transactions",
        excerpt="The new AI-powered payment orchestration layer handles invoicing, reconciliation, and fraud detection.",
        relevant=True,
        reason="AI + payment，符合 Agentic Payment 定位",
    ),
    Article(
        title="a16z Crypto: Why AI Agents Need Crypto Wallets",
        excerpt="On-chain identity and micropayments are essential infrastructure for autonomous AI agents.",
        relevant=True,
        reason="AI agents + crypto wallets，精确定位交叉点",
    ),
    Article(
        title="Building RAG Pipelines for Enterprise AI Agents",
        excerpt="Retrieval-augmented generation enables agents to access proprietary data without retraining.",
        relevant=True,
        reason="RAG 关键词 + AI Agent 场景",
    ),
    Article(
        title="Weekly Roundup: Top AI Agent Launches This Week",
        excerpt="From AutoGPT to Claude's new tool use, here's everything that mattered in AI agents.",
        relevant=True,
        reason="AI agent 精确短语",
    ),
    Article(
        title="Bankless Daily: How Generative AI Is Transforming DeFi",
        excerpt="From automated trading to AI-powered yield strategies, generative AI is coming to crypto.",
        relevant=True,
        reason="generative ai 精确短语匹配",
    ),

    # ── 不相关（False）────────────────────────────────────────────────────────

    Article(
        title="Bitcoin Surges to $120K as Institutional Demand Grows",
        excerpt="BlackRock's IBIT ETF sees record $2B single-day inflow as BTC breaks all-time high.",
        relevant=False,
        reason="纯 BTC 价格新闻，无 AI 关键词",
    ),
    Article(
        title="SEC Files Emergency Motion Against Coinbase",
        excerpt="The regulator claims Coinbase operated an unregistered securities exchange since 2019.",
        relevant=False,
        reason="纯监管/法律新闻，无 AI",
    ),
    Article(
        title="Solana's Firedancer Upgrade Goes Live on Mainnet",
        excerpt="The new validator client written in C++ brings 1M+ TPS capacity to the Solana network.",
        relevant=False,
        reason="区块链技术升级，与 AI Agent 无关",
    ),
    Article(
        title="Ethereum Staking Yields Drop Below 3% APY",
        excerpt="Post-merge staking rewards have compressed as total staked ETH surpasses 30 million.",
        relevant=False,
        reason="ETH staking 收益，纯 DeFi，无 AI",
    ),
    Article(
        title="Top 10 NFT Projects to Watch in Q2 2026",
        excerpt="From Pudgy Penguins to new generative collections, here's what's hot in the NFT market.",
        relevant=False,
        reason="NFT 市场，无 AI Agent 内容",
    ),
    Article(
        title="Kalshi Raises $1B at $22B Valuation",
        excerpt="The prediction market platform doubles its valuation in three months with backing from Coatue.",
        relevant=False,
        reason="融资新闻，与 AI Agent 无关（无 AI 关键词）",
    ),
    Article(
        title="Gemini Exchange Faces Class-Action Over Prediction Market Pivot",
        excerpt="Users allege Gemini violated its terms of service when it discontinued the Gemini Earn product.",
        relevant=False,
        reason="Gemini 加密交易所诉讼，黑名单应拦截",
    ),
    Article(
        title="Fed Holds Rates at 4.5% Amid Inflation Concerns",
        excerpt="The Federal Reserve kept benchmark interest rates unchanged at its March meeting.",
        relevant=False,
        reason="宏观经济，完全无关",
    ),
    Article(
        title="Retail Traders Dominate Crypto Volume on Weekends",
        excerpt="Data shows retail participation spikes 40% on Saturdays compared to institutional flows.",
        relevant=False,
        reason="词边界测试：'retail' 含 'ai' 字母但非独立词，应拒绝",
    ),
    Article(
        title="Australia Considers Crypto Licensing Framework",
        excerpt="The Treasury has released a consultation paper on digital asset service provider regulations.",
        relevant=False,
        reason="词边界测试：'Australia' 含 'ai' 但非独立词，应拒绝",
    ),
]


# ── 10 对重复文章（应被 Jaccard 去重）────────────────────────────────────────
# 每对包含 (article_a, article_b, expected_kept_index)
# expected_kept_index: 0 = 保留 a，1 = 保留 b（通常保留 relevance 更高的）

@dataclass
class DuplicatePair:
    article_a: dict
    article_b: dict
    should_dedup: bool           # True = 应被识别为重复
    kept_index: int = 0          # 0 = 保留 a，1 = 保留 b
    reason: str = ""


DUPLICATE_PAIRS: list[DuplicatePair] = [

    # 1. 完全相同标题（不同来源）
    DuplicatePair(
        article_a={"title": "Kalshi Raises $1B at $22B Valuation", "url": "https://decrypt.co/kalshi-1b", "relevance": 6},
        article_b={"title": "Kalshi Raises $1B at $22B Valuation", "url": "https://bankless.com/kalshi-1b", "relevance": 7},
        should_dedup=True,
        kept_index=1,
        reason="完全相同标题，保留高分版本",
    ),

    # 2. 轻微措辞差异（同一事件）
    DuplicatePair(
        article_a={"title": "OpenAI Releases GPT-5 with Agentic Features", "url": "https://a.com/1", "relevance": 8},
        article_b={"title": "OpenAI Launches GPT-5 Featuring Agentic Capabilities", "url": "https://b.com/1", "relevance": 7},
        should_dedup=True,
        kept_index=0,
        reason="同一新闻不同措辞，Jaccard 应 ≥ 0.4",
    ),

    # 3. 标题共享核心名词
    DuplicatePair(
        article_a={"title": "Anthropic Raises $2B Series C at $18B Valuation", "url": "https://a.com/2", "relevance": 8},
        article_b={"title": "Anthropic $2B Fundraising Round Closes at $18B Valuation", "url": "https://b.com/2", "relevance": 8},
        should_dedup=True,
        kept_index=0,
        reason="融资新闻，核心词高度重叠",
    ),

    # 4. 中文标题重复（由 Claude 生成）
    DuplicatePair(
        article_a={"title_zh": "Stripe 推出 AI 支付代理", "title": "Stripe Launches AI Payment Agent", "url": "https://a.com/3", "relevance": 9},
        article_b={"title_zh": "Stripe 发布 AI 驱动的支付代理服务", "title": "Stripe Releases AI-Driven Payment Agent Service", "url": "https://b.com/3", "relevance": 7},
        should_dedup=True,
        kept_index=0,
        reason="中文标题相似度应触发去重",
    ),

    # 5. 数字不同但其他词完全相同
    DuplicatePair(
        article_a={"title": "Claude 3.5 Sonnet Tops LLM Benchmarks", "url": "https://a.com/4", "relevance": 7},
        article_b={"title": "Claude 3.7 Sonnet Tops LLM Benchmarks", "url": "https://b.com/4", "relevance": 8},
        should_dedup=True,
        kept_index=1,
        reason="仅版本号不同，应视为重复",
    ),

    # 6. 标题极短，一个是另一个的子集
    DuplicatePair(
        article_a={"title": "GPT-5 Is Here", "url": "https://a.com/5", "relevance": 6},
        article_b={"title": "GPT-5 Is Finally Here and It's Incredible", "url": "https://b.com/5", "relevance": 7},
        should_dedup=True,
        kept_index=1,
        reason="词集重叠率高，应去重",
    ),

    # 7. 播客 episode 标题重复
    DuplicatePair(
        article_a={"title": "The Cognitive Revolution: Sam Altman on AI Agents", "url": "https://a.com/6", "relevance": 8},
        article_b={"title": "Cognitive Revolution Podcast: Sam Altman Talks AI Agents", "url": "https://b.com/6", "relevance": 7},
        should_dedup=True,
        kept_index=0,
        reason="播客标题重复（不同平台收录同一集）",
    ),

    # 8. 同一报告被多个 Newsletter 转发
    DuplicatePair(
        article_a={"title": "State of AI Agents Report 2026 Published", "url": "https://a.com/7", "relevance": 8},
        article_b={"title": "2026 State of AI Agents Report Is Now Available", "url": "https://b.com/7", "relevance": 7},
        should_dedup=True,
        kept_index=0,
        reason="同一报告发布，标题重排",
    ),

    # 9. 带数字的融资新闻
    DuplicatePair(
        article_a={"title": "Perplexity AI Raises $500M at $9B Valuation", "url": "https://a.com/8", "relevance": 9},
        article_b={"title": "Perplexity Raises $500 Million Valuing Company at $9 Billion", "url": "https://b.com/8", "relevance": 8},
        should_dedup=True,
        kept_index=0,
        reason="同一融资新闻，$数字表达方式不同",
    ),

    # 10. URL 不同但 summary 高度相似
    DuplicatePair(
        article_a={"title": "Mistral Releases New Open-Weight 70B Model", "url": "https://a.com/9", "relevance": 7},
        article_b={"title": "Mistral Launches Open Weight 70B Language Model", "url": "https://b.com/9", "relevance": 8},
        should_dedup=True,
        kept_index=1,
        reason="几乎相同，只有 'open-weight' vs 'open weight' 差异",
    ),
]


# ── 10 对非重复文章（不应被去重）────────────────────────────────────────────
# should_dedup=False：这两篇是不同新闻，不应被误判为重复

NON_DUPLICATE_PAIRS: list[DuplicatePair] = [

    DuplicatePair(
        article_a={"title": "OpenAI Releases GPT-5", "url": "https://a.com/10", "relevance": 8},
        article_b={"title": "Anthropic Releases Claude 4", "url": "https://b.com/10", "relevance": 8},
        should_dedup=False,
        reason="不同公司不同产品发布",
    ),
    DuplicatePair(
        article_a={"title": "AI Agents Are Transforming Customer Service", "url": "https://a.com/11", "relevance": 7},
        article_b={"title": "AI Agents Are Transforming Software Development", "url": "https://b.com/11", "relevance": 8},
        should_dedup=False,
        reason="主题相近但应用领域不同（customer service vs software dev）",
    ),
    DuplicatePair(
        article_a={"title": "Stripe Launches AI Payment Agent", "url": "https://a.com/12", "relevance": 9},
        article_b={"title": "Stripe Launches Stablecoin Payment Rails", "url": "https://b.com/12", "relevance": 7},
        should_dedup=False,
        reason="同一公司，不同产品（AI Agent vs Stablecoin）",
    ),
    DuplicatePair(
        article_a={"title": "MCP Protocol Explained: A Developer Guide", "url": "https://a.com/13", "relevance": 7},
        article_b={"title": "A2A Protocol vs MCP: Which Should You Use?", "url": "https://b.com/13", "relevance": 8},
        should_dedup=False,
        reason="不同协议，内容有实质差异",
    ),
    DuplicatePair(
        article_a={"title": "Perplexity AI Raises $500M", "url": "https://a.com/14", "relevance": 9},
        article_b={"title": "Perplexity AI Launches Enterprise Tier", "url": "https://b.com/14", "relevance": 7},
        should_dedup=False,
        reason="同一公司，不同事件（融资 vs 产品发布）",
    ),
    DuplicatePair(
        article_a={"title": "The Future of AI Agents in Healthcare", "url": "https://a.com/15", "relevance": 7},
        article_b={"title": "The Future of AI Agents in Finance", "url": "https://b.com/15", "relevance": 8},
        should_dedup=False,
        reason="主题相同，行业不同，不应去重",
    ),
    DuplicatePair(
        article_a={"title": "Gemini 2.0 Flash Beats GPT-4o on Coding Benchmarks", "url": "https://a.com/16", "relevance": 8},
        article_b={"title": "Claude 3.7 Sonnet Beats GPT-4o on Coding Benchmarks", "url": "https://b.com/16", "relevance": 9},
        should_dedup=False,
        reason="不同 AI 模型的测试结果，不应混为一谈",
    ),
    DuplicatePair(
        article_a={"title": "Bankless: The Agentic Economy Explained", "url": "https://a.com/17", "relevance": 8},
        article_b={"title": "Bankless: Why Bitcoin Is Digital Gold", "url": "https://b.com/17", "relevance": 5},
        should_dedup=False,
        reason="同一信源，完全不同话题",
    ),
    DuplicatePair(
        article_a={"title": "LangChain vs LlamaIndex: Which Agent Framework?", "url": "https://a.com/18", "relevance": 7},
        article_b={"title": "LangChain Raises $25M to Build AI Agent Platform", "url": "https://b.com/18", "relevance": 8},
        should_dedup=False,
        reason="同一品牌，不同类型文章（对比 vs 融资新闻）",
    ),
    DuplicatePair(
        article_a={"title": "Weekly AI Digest: Top 10 Papers", "url": "https://a.com/19", "relevance": 6},
        article_b={"title": "Weekly Crypto Digest: Top 10 DeFi Moves", "url": "https://b.com/19", "relevance": 5},
        should_dedup=False,
        reason="格式相似但内容领域完全不同（AI 论文 vs DeFi）",
    ),
]
