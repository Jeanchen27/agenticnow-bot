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
        "id": "xkcd",
        "name": "xkcd",
        "url": "https://xkcd.com",
        "rss": "https://xkcd.com/rss.xml",
        "category": "AI Dev",
    },
    {
        "id": "steipete_blog",
        "name": "steipete.me Blog (Peter Steinberger)",
        "url": "https://steipete.me",
        "rss": "https://steipete.me/rss.xml",
        "category": "OpenClaw",
    },
    {
        "id": "openclaw_cn",
        "name": "openclaw-cn 中文汉化版",
        "url": "https://github.com/jiulingyun/openclaw-cn",
        "rss": "https://github.com/jiulingyun/openclaw-cn/releases.atom",
        "category": "中文信源",
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
        "rss": "https://www.oneusefulthing.org/feed",
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
        "rss": "https://www.platformer.news/rss/",
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
