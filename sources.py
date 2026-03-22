"""
@AgenticNow 信源配置 v7
40 个精选信源，覆盖 AI Agent / Agentic Web / Agentic Economy / Agentic Commerce / Agentic Payment / OpenClaw
"""

# ─────────────────────────────────────────────────────────────────────────────
# 关键词预过滤（对 Decrypt / Bankless 等高产量媒体启用，只保留 AI Agent 相关）
# ─────────────────────────────────────────────────────────────────────────────
KEYWORD_FILTER_TERMS = [
    # 短词（≤3字符）→ 词边界匹配，防止误命中
    "ai", "llm", "gpt", "mcp", "a2a",
    # 长词 → 子串匹配
    "agent", "agentic", "autonomous", "anthropic", "openai",
    "deepmind", "copilot", "claude", "chatgpt",
    "artificial intelligence", "machine learning", "neural network",
    "large language model", "generative ai", "foundation model",
    "transformer model", "rag", "fine-tun",
]

# 多词精确短语（只对关键词过滤信源生效）
KEYWORD_FILTER_EXACT = [
    "ai agent", "ai-powered", "ai payment", "ai wallet",
    "ai commerce", "ai trading", "defi ai", "crypto ai",
    "web3 ai", "smart contract ai", "model context protocol",
    "reasoning model", "language model", "inference engine",
    # gemini 须搭配 AI 上下文才通过，避免误命中 Gemini 加密交易所
    "gemini ai", "gemini model", "gemini pro", "gemini ultra",
    "gemini nano", "gemini 2", "google gemini",
]

# 关键词黑名单：命中这些词时，即使通过了白名单也直接丢弃
# 用于排除 gemini 交易所、crypto 交易所等噪声
KEYWORD_BLOCKLIST = [
    "gemini exchange", "gemini trading", "gemini trust",
    "gemini lawsuit", "gemini sec", "gemini earn",
    "winklevoss",  # Gemini 交易所创始人
]

# ─────────────────────────────────────────────────────────────────────────────
# RSS / ATOM / PODCAST 信源（共 40 个）
# source_type: "newsletter" | "podcast" | "rss"
# keyword_filter: True = 抓取后先用关键词过滤再送入 Claude
# ─────────────────────────────────────────────────────────────────────────────
RSS_SOURCES: list[dict] = [

    # ══════════════════════════════════════════════════════════════════════════
    # AI Agent（16 个）
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "latent_space",
        "name": "Latent Space",
        "url": "https://www.latent.space",
        "rss": "https://www.latent.space/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "simon_willison",
        "name": "Simon Willison's Blog",
        "url": "https://simonwillison.net",
        "rss": "https://simonwillison.net/atom/everything/",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "swyx",
        "name": "swyx (Shawn Wang)",
        "url": "https://www.swyx.io",
        "rss": "https://www.swyx.io/rss.xml",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "import_ai",
        "name": "Import AI (Jack Clark)",
        "url": "https://importai.substack.com",
        "rss": "https://importai.substack.com/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "one_useful_thing",
        "name": "One Useful Thing (Ethan Mollick)",
        "url": "https://www.oneusefulthing.org",
        "rss": "https://www.oneusefulthing.org/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "nates_newsletter",
        "name": "Nate's Newsletter",
        "url": "https://natesnewsletter.substack.com",
        "rss": "https://natesnewsletter.substack.com/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "interconnected",
        "name": "Interconnected (Matt Webb)",
        "url": "https://interconnected.org",
        "rss": "https://interconnected.org/home/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "rogerwong_blog",
        "name": "Roger Wong Blog",
        "url": "https://rogerwong.me",
        "rss": "https://rogerwong.me/rss.xml",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "interconnects",
        "name": "Interconnects (Nathan Lambert)",
        "url": "https://www.interconnects.ai",
        "rss": "https://www.interconnects.ai/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "ai_snake_oil",
        "name": "AI Snake Oil (Narayanan)",
        "url": "https://aisnakeoil.substack.com",
        "rss": "https://aisnakeoil.substack.com/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "chip_huyen",
        "name": "Chip Huyen",
        "url": "https://huyenchip.com",
        "rss": "https://huyenchip.com/feed.xml",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "ahead_of_ai",
        "name": "Ahead of AI (Sebastian Raschka)",
        "url": "https://magazine.sebastianraschka.com",
        "rss": "https://magazine.sebastianraschka.com/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "ai_supremacy",
        "name": "AI Supremacy (Michael Spencer)",
        "url": "https://aisupremacy.substack.com",
        "rss": "https://aisupremacy.substack.com/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "algorithmic_bridge",
        "name": "The Algorithmic Bridge",
        "url": "https://www.thealgorithmicbridge.com",
        "rss": "https://www.thealgorithmicbridge.com/feed",
        "category": "AI Agent",
        "source_type": "newsletter",
    },
    {
        "id": "cognitive_revolution",
        "name": "Cognitive Revolution",
        "url": "https://www.cognitiverevolution.ai",
        "rss": "https://feeds.megaphone.fm/RINTP3108857801",
        "category": "AI Agent",
        "source_type": "podcast",
    },
    {
        "id": "thursdai",
        "name": "ThursdAI",
        "url": "https://sub.thursdai.news",
        "rss": "https://sub.thursdai.news/feed",
        "category": "AI Agent",
        "source_type": "podcast",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Agentic Web（5 个）
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "platformer",
        "name": "Platformer (Casey Newton)",
        "url": "https://www.platformer.news",
        "rss": "https://www.platformer.news/rss/",
        "category": "Agentic Web",
        "source_type": "newsletter",
    },
    {
        "id": "last_week_in_ai",
        "name": "Last Week in AI",
        "url": "https://lastweekin.ai",
        "rss": "https://lastweekin.ai/feed",
        "category": "Agentic Web",
        "source_type": "newsletter",
    },
    {
        "id": "hn_ai",
        "name": "Hacker News (AI/LLM精选)",
        "url": "https://news.ycombinator.com",
        "rss": "https://hnrss.org/frontpage?q=AI+agent+LLM+claude&points=50",
        "category": "Agentic Web",
        "source_type": "rss",
    },
    {
        "id": "hard_fork",
        "name": "Hard Fork (NYT)",
        "url": "https://www.nytimes.com/column/hard-fork",
        "rss": "https://feeds.simplecast.com/l2i9YnTd",
        "category": "Agentic Web",
        "source_type": "podcast",
    },
    {
        "id": "stratechery",
        "name": "Stratechery (Ben Thompson)",
        "url": "https://stratechery.com",
        "rss": "https://stratechery.com/feed/",
        "category": "Agentic Web",
        "source_type": "newsletter",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Agentic Economy（6 个）
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "a16z_crypto",
        "name": "a16z crypto",
        "url": "https://a16zcrypto.substack.com",
        "rss": "https://a16zcrypto.substack.com/feed",
        "category": "Agentic Economy",
        "source_type": "newsletter",
    },
    {
        "id": "the_neuron",
        "name": "The Neuron",
        "url": "https://www.theneuron.ai",
        "rss": "https://www.theneuron.ai/feed/",
        "category": "Agentic Economy",
        "source_type": "newsletter",
    },
    {
        "id": "not_boring",
        "name": "Not Boring (Packy McCormick)",
        "url": "https://www.notboring.co",
        "rss": "https://www.notboring.co/feed",
        "category": "Agentic Economy",
        "source_type": "newsletter",
    },
    {
        "id": "elad_gil",
        "name": "Elad Gil Blog",
        "url": "https://blog.eladgil.com",
        "rss": "https://blog.eladgil.com/feed",
        "category": "Agentic Economy",
        "source_type": "newsletter",
    },
    {
        "id": "no_priors",
        "name": "No Priors",
        "url": "https://www.nopriors.com",
        "rss": "https://feeds.megaphone.fm/nopriors",
        "category": "Agentic Economy",
        "source_type": "podcast",
    },
    {
        "id": "dwarkesh",
        "name": "Dwarkesh Podcast",
        "url": "https://www.dwarkesh.com",
        "rss": "https://api.substack.com/feed/podcast/69345.rss",
        "category": "Agentic Economy",
        "source_type": "podcast",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Agentic Commerce（5 个）
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "defi0xjeff",
        "name": "0xJeff (DeFi0xJeff)",
        "url": "https://defi0xjeff.substack.com",
        "rss": "https://defi0xjeff.substack.com/feed",
        "category": "Agentic Commerce",
        "source_type": "newsletter",
    },
    {
        "id": "bens_bites",
        "name": "Ben's Bites",
        "url": "https://www.bensbites.com",
        "rss": "https://www.bensbites.com/feed",
        "category": "Agentic Commerce",
        "source_type": "newsletter",
    },
    {
        "id": "bankless",
        "name": "Bankless",
        "url": "https://www.bankless.com",
        "rss": "https://www.bankless.com/rss/feed",
        "category": "Agentic Commerce",
        "source_type": "newsletter",
        "keyword_filter": True,
        "min_relevance": 8,   # 只有明确与 AI/Agent 相关的文章才入选
    },
    {
        "id": "decrypt",
        "name": "Decrypt",
        "url": "https://decrypt.co",
        "rss": "https://decrypt.co/feed",
        "category": "Agentic Commerce",
        "source_type": "newsletter",
        "keyword_filter": True,
        "min_relevance": 8,   # 只有明确与 AI/Agent 相关的文章才入选
    },
    {
        "id": "practical_ai",
        "name": "Practical AI (Changelog)",
        "url": "https://changelog.com/practicalai",
        "rss": "https://changelog.com/practicalai/feed",
        "category": "Agentic Commerce",
        "source_type": "podcast",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Agentic Payment（5 个）
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "stripe_blog",
        "name": "Stripe Blog",
        "url": "https://stripe.com/blog",
        "rss": "https://stripe.com/blog/feed.rss",
        "category": "Agentic Payment",
        "source_type": "newsletter",
    },
    {
        "id": "linas_fintech",
        "name": "Linas' Newsletter (Fintech)",
        "url": "https://linas.substack.com",
        "rss": "https://linas.substack.com/feed",
        "category": "Agentic Payment",
        "source_type": "newsletter",
    },
    {
        "id": "empire_blockworks",
        "name": "Empire (Blockworks)",
        "url": "https://blockworks.co/podcast/empire",
        "rss": "https://feeds.megaphone.fm/empire",
        "category": "Agentic Payment",
        "source_type": "podcast",
    },
    {
        "id": "bell_curve",
        "name": "Bell Curve",
        "url": "https://bellcurve.fm",
        "rss": "https://feeds.megaphone.fm/bellcurve",
        "category": "Agentic Payment",
        "source_type": "podcast",
    },
    {
        "id": "a16z_crypto_podcast",
        "name": "a16z crypto podcast",
        "url": "https://a16zcrypto.com",
        "rss": "https://feeds.simplecast.com/XPOpH7r4",
        "category": "Agentic Payment",
        "source_type": "podcast",
    },

    # ══════════════════════════════════════════════════════════════════════════
    # OpenClaw 生态（3 个）
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "steipete_blog",
        "name": "steipete.me Blog (Peter Steinberger)",
        "url": "https://steipete.me",
        "rss": "https://steipete.me/rss.xml",
        "category": "OpenClaw",
        "source_type": "newsletter",
    },
    {
        "id": "openclaw_cn",
        "name": "openclaw-cn 中文汉化版",
        "url": "https://github.com/jiulingyun/openclaw-cn",
        "rss": "https://github.com/jiulingyun/openclaw-cn/releases.atom",
        "category": "OpenClaw",
        "source_type": "rss",
    },
    {
        "id": "xkcd",
        "name": "xkcd",
        "url": "https://xkcd.com",
        "rss": "https://xkcd.com/rss.xml",
        "category": "OpenClaw",
        "source_type": "rss",
    },

]

# ─────────────────────────────────────────────────────────────────────────────
# REDDIT 信源（使用 RSS 接口）
# ─────────────────────────────────────────────────────────────────────────────
REDDIT_SOURCES: list[dict] = [
    {
        "id": "r_aiagents",
        "name": "r/AIAgents",
        "subreddit": "AIAgents",
        "category": "AI Agent",
    },
    {
        "id": "r_claudeai",
        "name": "r/ClaudeAI",
        "subreddit": "ClaudeAI",
        "category": "AI Agent",
    },
    {
        "id": "r_localllama",
        "name": "r/LocalLLaMA",
        "subreddit": "LocalLLaMA",
        "category": "AI Dev",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# GITHUB TRENDING（关键词过滤 AI 相关项目）
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_TOPICS: list[str] = ["ai-agent", "llm", "autonomous-agent", "mcp"]


# ─────────────────────────────────────────────────────────────────────────────
# 分类表情符号映射
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY_EMOJI: dict[str, str] = {
    "OpenClaw":          "🦞",
    "AI Agent":          "🤖",
    "AI Dev":            "⚙️",
    "AI Tools":          "🛠️",
    "Agentic Web":       "🌐",
    "Agentic Economy":   "💡",
    "Agentic Commerce":  "🛒",
    "Agentic Payment":   "💳",
    "Crypto×AI":         "🔗",
    "default":           "📰",
}

# ─────────────────────────────────────────────────────────────────────────────
# 来源类型表情符号（用于分组标题）
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_TYPE_EMOJI: dict[str, str] = {
    "newsletter": "📬",
    "podcast":    "🎙️",
    "reddit":     "💬",
    "github":     "⭐",
    "rss":        "📡",
}
