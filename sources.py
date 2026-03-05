"""
@AgenticNow 信源配置 v5
精选英文+中文信源，覆盖 OpenClaw生态 / AI Agent / Crypto×AI / Agentic Payment / 中文信源
"""

# ─────────────────────────────────────────────────────────────────────────────
# RSS / ATOM 信源（可直接抓取）
# ─────────────────────────────────────────────────────────────────────────────
RSS_SOURCES: list[dict] = [

    # ── OpenClaw 核心生态 ──────────────────────────────────────────────────
    {
        "id": "steipete_blog",
        "name": "steipete.me Blog (Peter Steinberger)",
        "url": "https://steipete.me",
        "rss": "https://steipete.me/rss.xml",
        "category": "OpenClaw",
    },

    # ── AI Agent Newsletter / 博客 ─────────────────────────────────────────
    {
        "id": "nates_newsletter",
        "name": "Nate's Newsletter",
        "url": "https://natesnewsletter.substack.com",
        "rss": "https://natesnewsletter.substack.com/feed",
        "category": "AI Agent",
    },
    {
        "id": "latent_space",
        "name": "Latent Space",
        "url": "https://www.latent.space",
        "rss": "https://www.latent.space/feed",
        "category": "AI Dev",
    },
    {
        "id": "import_ai",
        "name": "Import AI (Jack Clark)",
        "url": "https://importai.substack.com",
        "rss": "https://importai.substack.com/feed",
        "category": "AI Agent",
    },
    {
        "id": "last_week_in_ai",
        "name": "Last Week in AI",
        "url": "https://lastweekin.ai",
        "rss": "https://lastweekin.ai/feed",
        "category": "AI Agent",
    },
    {
        "id": "bens_bites",
        "name": "Ben's Bites",
        "url": "https://www.bensbites.com",
        "rss": "https://www.bensbites.com/feed",
        "category": "AI Tools",
    },
    {
        "id": "one_useful_thing",
        "name": "One Useful Thing (Ethan Mollick)",
        "url": "https://oneusefulthing.substack.com",
        "rss": "https://oneusefulthing.substack.com/feed",
        "category": "AI Agent",
    },
    {
        "id": "interconnected",
        "name": "Interconnected (Matt Webb)",
        "url": "https://interconnected.org",
        "rss": "https://interconnected.org/home/feed",
        "category": "AI Agent",
    },
    {
        "id": "platformer",
        "name": "Platformer (Casey Newton)",
        "url": "https://www.platformer.news",
        "rss": "https://www.platformer.news/feed",
        "category": "AI Agent",
    },
    {
        "id": "rogerwong_blog",
        "name": "Roger Wong Blog",
        "url": "https://rogerwong.me",
        "rss": "https://rogerwong.me/rss.xml",
        "category": "AI Agent",
    },
    {
        "id": "simon_willison",
        "name": "Simon Willison's Blog",
        "url": "https://simonwillison.net",
        "rss": "https://simonwillison.net/atom/everything/",
        "category": "AI Dev",
    },
    {
        "id": "swyx",
        "name": "swyx (Shawn Wang)",
        "url": "https://www.swyx.io",
        "rss": "https://www.swyx.io/rss.xml",
        "category": "AI Dev",
    },
    {
        "id": "hackernoon_ai",
        "name": "HackerNoon · AI Agents",
        "url": "https://hackernoon.com/tagged/ai-agents",
        "rss": "https://hackernoon.com/tagged/ai-agents/feed",
        "category": "AI Dev",
    },
    {
        "id": "hn_ai",
        "name": "Hacker News (AI/LLM精选)",
        "url": "https://news.ycombinator.com",
        "rss": "https://hnrss.org/frontpage?q=AI+agent+LLM+claude&points=50",
        "category": "AI Dev",
    },

    # ── Crypto × AI · Agentic Payment ─────────────────────────────────────
    {
        "id": "defi0xjeff",
        "name": "0xJeff (DeFi0xJeff)",
        "url": "https://defi0xjeff.substack.com",
        "rss": "https://defi0xjeff.substack.com/feed",
        "category": "Crypto×AI",
    },
    {
        "id": "linas_fintech",
        "name": "Linas' Newsletter (Fintech)",
        "url": "https://linas.substack.com",
        "rss": "https://linas.substack.com/feed",
        "category": "Agentic Payment",
    },
    {
        "id": "payments_dive",
        "name": "Payments Dive",
        "url": "https://www.paymentsdive.com",
        "rss": "https://www.paymentsdive.com/feeds/news/",
        "category": "Agentic Payment",
    },
    {
        "id": "stripe_blog",
        "name": "Stripe Blog",
        "url": "https://stripe.com/blog",
        "rss": "https://stripe.com/blog/feed.rss",
        "category": "Agentic Payment",
    },

    # ── 中文信源 ──────────────────────────────────────────────────────────
    {
        "id": "jiqizhixin",
        "name": "机器之心",
        "url": "https://www.jiqizhixin.com",
        "rss": "https://www.jiqizhixin.com/rss",
        "category": "中文信源",
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
# X / TWITTER 个人账号（通过 RSSHub 转为 RSS）
# 需要设置 RSSHUB_BASE_URL 环境变量
# 公共实例: https://rsshub.app（可能限速）
# 建议自建: https://docs.rsshub.app/deploy/
# ─────────────────────────────────────────────────────────────────────────────
TWITTER_SOURCES: list[dict] = [

    # ── OpenClaw 核心生态 ──────────────────────────────────────────────────
    {"id": "steipete",        "name": "Peter Steinberger",    "handle": "steipete",        "category": "OpenClaw"},
    {"id": "velvet_shark",    "name": "Radek Sienkiewicz",    "handle": "velvet_shark",    "category": "OpenClaw"},
    {"id": "floriandarroman", "name": "Florian Darroman",     "handle": "floriandarroman", "category": "OpenClaw"},

    # ── 个人 X 账号 · 英文实操派 ───────────────────────────────────────────
    {"id": "emollick",        "name": "Ethan Mollick",        "handle": "emollick",        "category": "AI Agent"},
    {"id": "gregisenberg",    "name": "Greg Isenberg",        "handle": "gregisenberg",    "category": "AI Agent"},
    {"id": "mckaywrigley",    "name": "McKay Wrigley",        "handle": "mckaywrigley",    "category": "AI Agent"},
    {"id": "yaborobot",       "name": "Yabo",                 "handle": "yaborobot",       "category": "AI Tools"},
    {"id": "wesroth",         "name": "Wes Roth",             "handle": "WesRoth",         "category": "AI Tools"},
    {"id": "nickscamara_",    "name": "Nick Camara",          "handle": "nickscamara_",    "category": "AI Tools"},
    {"id": "mattshumer_",     "name": "Matt Shumer",          "handle": "mattshumer_",     "category": "AI Agent"},
    {"id": "skiaborot",       "name": "Skiab",                "handle": "skiaborot",       "category": "AI Tools"},
    {"id": "hwchase17",       "name": "Harrison Chase",       "handle": "hwchase17",       "category": "AI Dev"},
    {"id": "andrewng",        "name": "Andrew Ng",            "handle": "AndrewYNg",       "category": "AI Agent"},
    {"id": "jasonbe",         "name": "Jason Beutel",         "handle": "JasonBe",         "category": "AI Agent"},
    {"id": "jakebrowatzke",   "name": "Jake Browatzke",       "handle": "jakebrowatzke",   "category": "AI Tools"},
    {"id": "maboroshinosf",   "name": "Maboroshi",            "handle": "maboroshinoSF",   "category": "AI Tools"},
    {"id": "mrsharma",        "name": "Nik Sharma",           "handle": "mrsharma",        "category": "AI Tools"},
    {"id": "searchbrat",      "name": "Kieran Flanagan",      "handle": "searchbrat",      "category": "AI Tools"},
    {"id": "wes_kao",         "name": "Wes Kao",              "handle": "wes_kao",         "category": "AI×创作"},
    {"id": "ajstuyvenberg",   "name": "AJ Stuyvenberg",       "handle": "AJStuyvenberg",   "category": "AI Dev"},
    {"id": "christinetyip",   "name": "Christine Tyip",       "handle": "christinetyip",   "category": "AI Tools"},
    {"id": "hesamation",      "name": "Hesam",                "handle": "Hesamation",      "category": "AI Tools"},
    {"id": "antonplex",       "name": "Anton",                "handle": "antonplex",       "category": "AI Tools"},

    # ── Crypto × AI · Agentic Payment ─────────────────────────────────────
    {"id": "shaborot",        "name": "Shaw (ai16z)",         "handle": "shaborot",        "category": "Crypto×AI"},
    {"id": "0xsammy",         "name": "0xSammy",              "handle": "0xSammy",         "category": "Crypto×AI"},
    {"id": "balajis_x",       "name": "Balaji Srinivasan",    "handle": "balajis",         "category": "Crypto×AI"},

    # ── 中文信源 ──────────────────────────────────────────────────────────
    {"id": "op7418",          "name": "歸藏",                  "handle": "op7418",          "category": "中文信源"},
    {"id": "dotey",           "name": "宝玉",                  "handle": "dotey",           "category": "中文信源"},
]

# ─────────────────────────────────────────────────────────────────────────────
# 分类表情符号映射
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY_EMOJI: dict[str, str] = {
    "OpenClaw":        "🦞",
    "AI Agent":        "🤖",
    "AI Dev":          "⚙️",
    "AI Tools":        "🛠️",
    "AI Infra":        "🏗️",
    "AI Design":       "🎨",
    "AI Automation":   "⚡",
    "AI×Product":      "📦",
    "AI×创作":          "✍️",
    "Crypto×AI":       "🔗",
    "DeFi×AI":         "💎",
    "Crypto×Macro":    "📊",
    "数字主权":          "🛡️",
    "DeFi×隐私":        "🔒",
    "Agentic Payment": "💳",
    "Agentic Finance": "🏦",
    "Agentic Economy": "🌐",
    "Fintech×AI":      "💰",
    "AI×Crypto":       "🔮",
    "Crypto":          "₿",
    "中文信源":          "🀄",
    "default":         "📰",
}
