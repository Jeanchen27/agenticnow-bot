"""
@AgenticNow 信源配置
80个精选英文信源，覆盖 AI Agent / Crypto×AI / Agentic Finance / AI工具实操
"""

# ─────────────────────────────────────────────────────────────────────────────
# RSS / ATOM 信源（可直接抓取）
# ─────────────────────────────────────────────────────────────────────────────
RSS_SOURCES: list[dict] = [

    # ── Newsletter: AI Agent · 通用实操 ───────────────────────────────────────
    {
        "id": "nates_newsletter",
        "name": "Nate's Newsletter",
        "url": "https://natesnewsletter.substack.com",
        "rss": "https://natesnewsletter.substack.com/feed",
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
        "id": "one_useful_thing",
        "name": "One Useful Thing (Ethan Mollick)",
        "url": "https://www.oneusefulthing.org",
        "rss": "https://www.oneusefulthing.org/feed",
        "category": "AI Agent",
    },
    {
        "id": "import_ai",
        "name": "Import AI (Jack Clark)",
        "url": "https://importai.substack.com",
        "rss": "https://importai.substack.com/feed",
        "category": "AI Agent",
    },
    {
        "id": "the_batch",
        "name": "The Batch (Andrew Ng)",
        "url": "https://www.deeplearning.ai/the-batch",
        "rss": "https://www.deeplearning.ai/the-batch/feed/",
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
        "id": "ai_agents_simplified",
        "name": "AI Agents Simplified",
        "url": "https://aiagentssimplified.substack.com",
        "rss": "https://aiagentssimplified.substack.com/feed",
        "category": "AI Agent",
    },
    {
        "id": "bens_bites",
        "name": "Ben's Bites",
        "url": "https://bensbites.co",
        "rss": "https://bensbites.beehiiv.com/feed",
        "category": "AI Tools",
    },
    {
        "id": "the_rundown_ai",
        "name": "The Rundown AI",
        "url": "https://www.therundown.ai",
        "rss": "https://www.therundown.ai/feed",
        "category": "AI Tools",
    },
    {
        "id": "every_to",
        "name": "Every.to (AI系列)",
        "url": "https://every.to",
        "rss": "https://every.to/feed",
        "category": "AI Agent",
    },
    {
        "id": "openclaw_newsletter",
        "name": "openclaw-ai.dev Newsletter",
        "url": "https://openclaw-ai.dev",
        "rss": "https://openclaw-ai.dev/feed",
        "category": "AI Agent",
    },

    # ── Newsletter: Crypto × AI ───────────────────────────────────────────────
    {
        "id": "0xjeff",
        "name": "0xJeff",
        "url": "https://defi0xjeff.substack.com",
        "rss": "https://defi0xjeff.substack.com/feed",
        "category": "Crypto×AI",
    },
    {
        "id": "chain_of_thought",
        "name": "Chain of Thought (Teng Yan)",
        "url": "https://chainofthought.xyz",
        "rss": "https://chainofthought.substack.com/feed",
        "category": "Crypto×AI",
    },
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
        "rss": "https://milkroad.com/feed",
        "category": "Crypto",
    },
    {
        "id": "multicoin_capital",
        "name": "Multicoin Capital Blog",
        "url": "https://multicoin.capital/blog",
        "rss": "https://multicoin.capital/feed/",
        "category": "Crypto×AI",
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
        "id": "linas_fintech",
        "name": "Linas Fintech Newsletter",
        "url": "https://linas.substack.com",
        "rss": "https://linas.substack.com/feed",
        "category": "Agentic Finance",
    },
    {
        "id": "0xsammy",
        "name": "0xSammy's Web3 Snippets",
        "url": "https://www.0xsammy.com",
        "rss": "https://www.0xsammy.com/feed",
        "category": "Agentic Economy",
    },
    {
        "id": "fintech_brainfood",
        "name": "Fintech Brainfood (Simon Taylor)",
        "url": "https://www.fintechbrainfood.com",
        "rss": "https://www.fintechbrainfood.com/feed",
        "category": "Agentic Finance",
    },
    {
        "id": "fintech_blueprint",
        "name": "The Fintech Blueprint (Lex Sokolin)",
        "url": "https://fintech.global/blueprint",
        "rss": "https://www.fintechblueprint.com/feed",
        "category": "Agentic Finance",
    },
    {
        "id": "a16z_crypto",
        "name": "a16z crypto Blog",
        "url": "https://a16zcrypto.com",
        "rss": "https://a16zcrypto.com/feed/",
        "category": "Agentic Payment",
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

    # ── Newsletter: AI工具实操（非技术向）────────────────────────────────────
    {
        "id": "superhuman",
        "name": "Superhuman (Zain Kahn)",
        "url": "https://www.superhumanai.com",
        "rss": "https://www.superhumanai.com/feed",
        "category": "AI Tools",
    },
    {
        "id": "wonder_tools",
        "name": "Wonder Tools (Jeremy Caplan)",
        "url": "https://wondertools.substack.com",
        "rss": "https://wondertools.substack.com/feed",
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
        "id": "the_neuron",
        "name": "The Neuron",
        "url": "https://www.theneurondaily.com",
        "rss": "https://www.theneurondaily.com/feed",
        "category": "AI Tools",
    },
    {
        "id": "futuretools",
        "name": "FutureTools Weekly (Matt Wolfe)",
        "url": "https://futuretools.io",
        "rss": "https://futuretools.io/feed",
        "category": "AI Tools",
    },

    # ── 社区 · 媒体 ───────────────────────────────────────────────────────────
    {
        "id": "secret_agent",
        "name": "The Secret Agent (CoT子刊)",
        "url": "https://agents.chainofthought.xyz",
        "rss": "https://agents.chainofthought.xyz/feed",
        "category": "Agentic Economy",
    },
    {
        "id": "simon_willison",
        "name": "Simon Willison's Newsletter",
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
    {
        "id": "visa_perspectives",
        "name": "Visa Perspectives",
        "url": "https://corporate.visa.com/en/perspectives.html",
        "rss": "https://corporate.visa.com/en/perspectives.rss",
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
        "id": "rogerwong",
        "name": "Roger Wong",
        "url": "https://rogerwong.me",
        "rss": "https://rogerwong.me/feed",
        "category": "AI Agent",
    },
    {
        "id": "dannyshmueli",
        "name": "Danny Shmueli",
        "url": "https://dannyshmueli.com",
        "rss": "https://dannyshmueli.com/feed",
        "category": "AI Agent",
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
        "url": "https://www.pragmaticengineer.com",
        "rss": "https://www.pragmaticengineer.com/rss/",
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
        "name": "a16z Research (AI专区)",
        "url": "https://a16z.com/ai",
        "rss": "https://a16z.com/feed/",
        "category": "AI×Crypto",
    },
    {
        "id": "unchained",
        "name": "Unchained (Laura Shin)",
        "url": "https://unchainedcrypto.com",
        "rss": "https://unchainedcrypto.com/feed/",
        "category": "Crypto×AI",
    },
    {
        "id": "balajis_blog",
        "name": "Balaji.com",
        "url": "https://balajis.com",
        "rss": "https://balajis.com/feed/",
        "category": "数字主权",
    },
    {
        "id": "wes_kao_blog",
        "name": "Wes Kao Blog",
        "url": "https://www.weskao.com",
        "rss": "https://www.weskao.com/feed",
        "category": "AI×创作",
    },
    {
        "id": "notboring_blog",
        "name": "Packy McCormick Blog",
        "url": "https://www.notboring.co",
        "rss": "https://www.notboring.co/feed",
        "category": "Crypto×AI",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# REDDIT 信源（使用 JSON API，无需鉴权）
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
