"""
@AgenticNow 信源配置
精选英文信源，覆盖 AI Agent / Crypto×AI / Agentic Finance / AI工具实操
"""

# ─────────────────────────────────────────────────────────────────────────────
# RSS / ATOM 信源（可直接抓取）
# ─────────────────────────────────────────────────────────────────────────────
RSS_SOURCES: list[dict] = [

    # ── Newsletter: AI Agent · 通用实操 ───────────────────────────────────────
    {
        "id": "platformer",
        "name": "Platformer (Casey Newton)",
        "url": "https://www.platformer.news",
        "rss": "https://www.platformer.news/feed",
        "category": "AI Agent",
    },
    {
        "id": "one_useful_thing",
        "name": "One Useful Thing (Ethan Mollick)",
        "url": "https://www.oneusefulthing.org",
        "rss": "https://www.oneusefulthing.org/feed",
        "category": "AI Agent",
    },
    {
        "id": "import_ai",
        "name": "Import AI (Jack Clark)",
        "url": "https://jack-clark.net",
        "rss": "https://jack-clark.net/feed/",
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
        "id": "latent_space",
        "name": "Latent Space",
        "url": "https://www.latent.space",
        "rss": "https://www.latent.space/feed",
        "category": "AI Dev",
    },
    {
        "id": "bens_bites",
        "name": "Ben's Bites",
        "url": "https://www.bensbites.com",
        "rss": "https://www.bensbites.com/feed",
        "category": "AI Tools",
    },
    {
        "id": "the_rundown_ai",
        "name": "The Rundown AI",
        "url": "https://www.therundown.ai",
        "rss": "https://www.therundown.ai/rss",
        "category": "AI Tools",
    },
    {
        "id": "every_to",
        "name": "Every.to (AI系列)",
        "url": "https://every.to",
        "rss": "https://every.to/rss",
        "category": "AI Agent",
    },
    {
        "id": "the_batch",
        "name": "The Batch (Andrew Ng)",
        "url": "https://www.deeplearning.ai/the-batch",
        "rss": "https://www.deeplearning.ai/feed/",
        "category": "AI Agent",
    },
    # 新增可靠替代源
    {
        "id": "venturebeat_ai",
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/ai",
        "rss": "https://venturebeat.com/category/ai/feed/",
        "category": "AI Agent",
    },
    {
        "id": "mit_tech_review",
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com",
        "rss": "https://www.technologyreview.com/feed/",
        "category": "AI Agent",
    },
    {
        "id": "hn_ai",
        "name": "Hacker News (AI/LLM精选)",
        "url": "https://news.ycombinator.com",
        "rss": "https://hnrss.org/frontpage?q=AI+agent+LLM+claude&points=50",
        "category": "AI Dev",
    },

    # ── Newsletter: Crypto × AI ───────────────────────────────────────────────
    {
        "id": "bankless",
        "name": "Bankless Newsletter",
        "url": "https://www.bankless.com/read",
        "rss": "https://www.bankless.com/feed",
        "category": "Crypto×AI",
    },
    {
        "id": "not_boring",
        "name": "Not Boring (Packy McCormick)",
        "url": "https://www.notboring.co",
        "rss": "https://www.notboring.co/feed",
        "category": "Crypto×AI",
    },
    {
        "id": "the_defiant",
        "name": "The Defiant Newsletter",
        "url": "https://thedefiant.io",
        "rss": "https://thedefiant.io/feed",
        "category": "DeFi×AI",
    },
    {
        "id": "milk_road",
        "name": "Milk Road",
        "url": "https://milkroad.com",
        "rss": "https://milkroad.beehiiv.com/feed",
        "category": "Crypto",
    },
    {
        "id": "unchained",
        "name": "Unchained (Laura Shin)",
        "url": "https://unchainedcrypto.com",
        "rss": "https://unchainedcrypto.com/feed/",
        "category": "Crypto×AI",
    },
    {
        "id": "coindesk",
        "name": "CoinDesk",
        "url": "https://www.coindesk.com",
        "rss": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "category": "Crypto×AI",
    },
    {
        "id": "decrypt",
        "name": "Decrypt",
        "url": "https://decrypt.co",
        "rss": "https://decrypt.co/feed",
        "category": "Crypto×AI",
    },
    {
        "id": "balajis_blog",
        "name": "Balaji.com",
        "url": "https://balajis.com",
        "rss": "https://balajis.com/feed/",
        "category": "数字主权",
    },

    # ── Newsletter: Agentic Payment · Finance ─────────────────────────────────
    {
        "id": "payments_dive",
        "name": "Payments Dive",
        "url": "https://www.paymentsdive.com",
        "rss": "https://www.paymentsdive.com/feeds/news/",
        "category": "Agentic Payment",
    },
    {
        "id": "0xsammy",
        "name": "0xSammy's Web3 Snippets",
        "url": "https://www.0xsammy.com",
        "rss": "https://www.0xsammy.com/feed",
        "category": "Agentic Economy",
    },
    {
        "id": "thepaypers",
        "name": "The Paypers",
        "url": "https://www.thepaypers.com",
        "rss": "https://www.thepaypers.com/rss",
        "category": "Agentic Payment",
    },
    {
        "id": "fintech_futures",
        "name": "Fintech Futures",
        "url": "https://www.fintechfutures.com",
        "rss": "https://www.fintechfutures.com/feed/",
        "category": "Fintech×AI",
    },
    {
        "id": "a16z_crypto",
        "name": "a16z crypto Blog",
        "url": "https://a16zcrypto.com",
        "rss": "https://a16zcrypto.com/posts/feed/",
        "category": "Agentic Payment",
    },

    # ── Newsletter: AI工具实操（非技术向）────────────────────────────────────
    {
        "id": "superhuman",
        "name": "Superhuman (Zain Kahn)",
        "url": "https://www.superhumanai.com",
        "rss": "https://www.superhumanai.com/feed",
        "category": "AI Tools",
    },
    {
        "id": "lennys_newsletter",
        "name": "Lenny's Newsletter",
        "url": "https://www.lennysnewsletter.com",
        "rss": "https://www.lennysnewsletter.com/feed",
        "category": "AI×Product",
    },
    {
        "id": "futuretools",
        "name": "FutureTools Weekly (Matt Wolfe)",
        "url": "https://futuretools.io",
        "rss": "https://futuretools.beehiiv.com/feed",
        "category": "AI Tools",
    },
    {
        "id": "the_neuron",
        "name": "The Neuron",
        "url": "https://www.theneurondaily.com",
        "rss": "https://theneurondaily.beehiiv.com/feed",
        "category": "AI Tools",
    },

    # ── 社区 · 媒体 ───────────────────────────────────────────────────────────
    {
        "id": "simon_willison",
        "name": "Simon Willison's Blog",
        "url": "https://simonwillison.net",
        "rss": "https://simonwillison.net/atom/everything/",
        "category": "AI Dev",
    },
    {
        "id": "stripe_blog",
        "name": "Stripe Blog (AI/Payments)",
        "url": "https://stripe.com/blog",
        "rss": "https://stripe.com/blog/feed.rss",
        "category": "Agentic Payment",
    },

    # ── 个人博客 ──────────────────────────────────────────────────────────────
    {
        "id": "swyx",
        "name": "swyx (Shawn Wang)",
        "url": "https://www.swyx.io",
        "rss": "https://www.swyx.io/rss.xml",
        "category": "AI Dev",
    },
    {
        "id": "maggie_appleton",
        "name": "Maggie Appleton",
        "url": "https://maggieappleton.com",
        "rss": "https://maggieappleton.com/rss.xml",
        "category": "AI Design",
    },
    {
        "id": "pragmatic_engineer",
        "name": "The Pragmatic Engineer (Gergely Orosz)",
        "url": "https://newsletter.pragmaticengineer.com",
        "rss": "https://newsletter.pragmaticengineer.com/feed",
        "category": "AI Dev",
    },
    {
        "id": "semianalysis",
        "name": "SemiAnalysis (Dylan Patel)",
        "url": "https://www.semianalysis.com",
        "rss": "https://www.semianalysis.com/feed",
        "category": "AI Infra",
    },
    {
        "id": "zapier_blog",
        "name": "Zapier Blog (AI Automation)",
        "url": "https://zapier.com/blog/ai",
        "rss": "https://zapier.com/blog/feeds/latest/",
        "category": "AI Automation",
    },
    {
        "id": "lyn_alden_blog",
        "name": "Lyn Alden Blog",
        "url": "https://www.lynalden.com",
        "rss": "https://www.lynalden.com/feed/",
        "category": "Crypto×Macro",
    },
    {
        "id": "a16z_ai",
        "name": "a16z Research",
        "url": "https://a16z.com",
        "rss": "https://a16z.com/feed/",
        "category": "AI×Crypto",
    },
    {
        "id": "openai_blog",
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog",
        "rss": "https://openai.com/blog/rss.xml",
        "category": "AI Agent",
    },
    {
        "id": "anthropic_blog",
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/blog",
        "rss": "https://www.anthropic.com/blog/rss.xml",
        "category": "AI Agent",
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
    {"id": "emollick",        "name": "Ethan Mollick",       "handle": "emollick",       "category": "AI Agent"},
    {"id": "gregisenberg",    "name": "Greg Isenberg",        "handle": "gregisenberg",   "category": "AI Agent"},
    {"id": "karpathy",        "name": "Andrej Karpathy",      "handle": "karpathy",       "category": "AI Dev"},
    {"id": "linusekenstam",   "name": "Linus Ekenstam",       "handle": "LinusEkenstam",  "category": "AI Tools"},
    {"id": "danshipper",      "name": "Dan Shipper",          "handle": "danshipper",     "category": "AI Tools"},
    {"id": "steipete",        "name": "Peter Steinberger",    "handle": "steipete",       "category": "AI Agent"},
    {"id": "jakebrowatzke",   "name": "Jake Browatzke",       "handle": "jakebrowatzke",  "category": "AI Tools"},
    {"id": "searchbrat",      "name": "Kieran Flanagan",      "handle": "searchbrat",     "category": "AI Tools"},
    {"id": "wes_kao_x",       "name": "Wes Kao",              "handle": "wes_kao",        "category": "AI×创作"},
    {"id": "mrsharma",        "name": "Nik Sharma",           "handle": "mrsharma",       "category": "AI Tools"},
    {"id": "0xteng",          "name": "Teng Yan",             "handle": "0xteng",         "category": "Crypto×AI"},
    {"id": "shawmakesmagic",  "name": "Shaw Walters",         "handle": "shawmakesmagic", "category": "Crypto×AI"},
    {"id": "camilarusso",     "name": "Camila Russo",         "handle": "CamilaRusso",    "category": "DeFi×AI"},
    {"id": "hosseeb",         "name": "Haseeb Qureshi",       "handle": "hosseeb",        "category": "Crypto×AI"},
    {"id": "cdixon",          "name": "Chris Dixon",          "handle": "cdixon",         "category": "Crypto×AI"},
    {"id": "balajis_x",       "name": "Balaji Srinivasan",    "handle": "balajis",        "category": "数字主权"},
    {"id": "erikvoorhees",    "name": "Erik Voorhees",        "handle": "ErikVoorhees",   "category": "DeFi×隐私"},
    {"id": "laurashin",       "name": "Laura Shin",           "handle": "laurashin",      "category": "Crypto×AI"},
    {"id": "lynaldencontact", "name": "Lyn Alden",            "handle": "LynAldenContact","category": "Crypto×Macro"},
    {"id": "jimmarous",       "name": "Jim Marous",           "handle": "JimMarous",      "category": "Agentic Finance"},
    {"id": "sytaylor",        "name": "Simon Taylor",         "handle": "sytaylor",       "category": "Agentic Finance"},
    {"id": "lexsokolin",      "name": "Lex Sokolin",          "handle": "LexSokolin",     "category": "Agentic Finance"},
    {"id": "rogerwong_x",     "name": "Roger Wong",           "handle": "rogerwong",      "category": "AI Agent"},
]

# ─────────────────────────────────────────────────────────────────────────────
# 分类表情符号映射
# ─────────────────────────────────────────────────────────────────────────────
CATEGORY_EMOJI: dict[str, str] = {
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
    "default":         "📰",
}
