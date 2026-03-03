# AgenticNow Daily Bot 🤖

每日自动抓取 80+ 英文 AI/Crypto 信源，通过 Claude API 生成中文标题 + 摘要，推送至 [@AgenticNow](https://t.me/AgenticNow) Telegram 频道。

---

## 功能特性

- 📡 **多信源抓取**：RSS/Atom、Reddit、GitHub Trending、X/Twitter（可选）
- 🧠 **Claude AI 摘要**：批量生成中文标题（≤25字）+ 摘要（80-120字）+ 相关度评分
- 📤 **双模式推送**：单篇独立发送 / 每日合集汇总
- 🔁 **URL 去重**：JSON 持久化，30 天自动清理
- ⏰ **双班推送**：每天北京时间 08:00（早班 8 篇）+ 20:00（晚班 6 篇）自动运行

---

## 项目结构

```
agenticnow-bot/
├── main.py                    # 主入口
├── sources.py                 # 80+ 信源配置
├── requirements.txt
├── .env.example               # 环境变量模板
├── seen_urls.json             # 已发送 URL 记录（自动生成）
├── fetchers/
│   ├── rss.py                 # RSS/Atom 抓取
│   ├── reddit.py              # Reddit JSON API
│   └── github_trending.py    # GitHub Trending 爬取
├── processor/
│   └── summarizer.py         # Claude API 摘要生成
├── publisher/
│   └── telegram.py           # Telegram 推送
├── storage/
│   └── dedup.py              # URL 去重存储
└── .github/
    └── workflows/
        └── daily.yml         # GitHub Actions 定时任务
```

---

## 快速开始

### 1. 克隆并安装依赖

```bash
git clone <your-repo-url>
cd agenticnow-bot
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Keys
```

**必填变量：**

| 变量 | 说明 |
|------|------|
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com) 获取 |
| `TELEGRAM_BOT_TOKEN` | 通过 [@BotFather](https://t.me/BotFather) 创建机器人获取 |
| `TELEGRAM_CHANNEL_ID` | 频道 ID，如 `@AgenticNow` 或 `-100xxxxxxxxx` |

**可选变量：**

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MAX_ARTICLES_PER_RUN` | `12` | 每次最多推送文章数 |
| `HOURS_LOOKBACK` | `48` | 抓取过去多少小时的内容 |
| `PUBLISH_MODE` | `individual` | `individual`（单篇）或 `digest`（合集） |
| `ENABLE_TWITTER` | `false` | 是否启用 X/Twitter 信源 |
| `RSSHUB_BASE_URL` | `https://rsshub.app` | RSSHub 实例地址（Twitter 信源需要） |

### 3. 本地测试

```bash
# 预览模式（不推送 Telegram，仅打印格式化内容）
python main.py --dry-run

# 预览最多 5 篇
python main.py --dry-run --max-articles 5

# 正式运行
python main.py

# 每日合集模式
python main.py --mode digest

# 启用 Twitter 信源
python main.py --enable-twitter
```

---

## Telegram 机器人设置

1. 在 Telegram 搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`，按提示创建机器人，获取 `Bot Token`
3. 将机器人添加为频道管理员（需要**发消息**权限）
4. 频道 ID：
   - 公开频道：直接用 `@频道用户名`
   - 私有频道：发一条消息后通过 [API](https://api.telegram.org/bot<TOKEN>/getUpdates) 获取数字 ID

---

## GitHub Actions 部署

### 设置 Secrets

在仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

| Secret 名称 | 值 |
|-------------|-----|
| `ANTHROPIC_API_KEY` | 你的 Anthropic API Key |
| `TELEGRAM_BOT_TOKEN` | 你的 Telegram Bot Token |
| `TELEGRAM_CHANNEL_ID` | 频道 ID（如 `@AgenticNow`） |
| `RSSHUB_BASE_URL` | （可选）RSSHub 实例地址 |
| `ENABLE_TWITTER` | （可选）`true` 启用 Twitter 信源 |

### 运行时间

| 时段 | UTC 时间 | 北京时间 | 文章数 | Lookback |
|------|---------|---------|-------|---------|
| 晨推 | 00:00 | 08:00 | 8 篇 | 13 小时 |
| 晚推 | 12:00 | 20:00 | 6 篇 | 13 小时 |

去重机制确保两次推送不会重复同一篇文章——`seen_urls.json` 在每次推送后自动更新并提交，晚班运行时会自动跳过晨班已推送的内容。

- **手动触发**：Actions → AgenticNow Daily Bot → Run workflow

### 手动触发选项

| 选项 | 说明 |
|------|------|
| 预览模式 | `true` = 只抓取摘要，不推送 |
| 最多文章数 | 覆盖默认的 12 篇 |
| 推送模式 | `individual` 或 `digest` |

---

## 信源覆盖

| 类型 | 数量 | 说明 |
|------|------|------|
| RSS/Substack | ~45 | The Rundown AI、Ben's Bites、a16z、Coindesk 等 |
| Reddit | 3 | r/AIAgents、r/ClaudeAI、r/LocalLLaMA |
| GitHub Trending | 动态 | ai-agent、llm、autonomous-agent、mcp 标签 |
| X/Twitter | 23 | Greg Brockman、Demis Hassabis 等（需 RSSHub） |

> Discord 信源（Hugging Face 等）因不支持公开爬取，暂未接入。

---

## 输出示例

**单篇推送格式（individual 模式）：**

```
🤖 OpenAI 发布新一代 o3 推理模型

o3 在数学和编程基准测试中超越人类专家水平，推理深度达到 12 层。OpenAI 表示该模型将于下月向开发者开放访问。

📌 阅读原文 · The Rundown AI · AI大模型

#OpenAI #o3 #推理模型
```

---

## X/Twitter 信源配置（可选）

X/Twitter 信源通过 [RSSHub](https://docs.rsshub.app/) 转为 RSS 格式。

**选项一：使用公共实例**
```env
RSSHUB_BASE_URL=https://rsshub.app
ENABLE_TWITTER=true
```
> ⚠️ 公共实例可能限速，建议自建

**选项二：自建 RSSHub**
```bash
docker run -d --name rsshub -p 1200:1200 diygod/rsshub
```
```env
RSSHUB_BASE_URL=http://localhost:1200
ENABLE_TWITTER=true
```

---

## 常见问题

**Q: 运行后没有推送任何内容？**
A: 可能原因：1）所有文章都已在 `seen_urls.json` 中；2）信源在过去 48 小时无更新。尝试 `--dry-run` 查看实际抓取数量。

**Q: Telegram 报 403 错误？**
A: 确认机器人已被添加为频道**管理员**，并具有"发送消息"权限。

**Q: Claude API 配额不足？**
A: 减少 `MAX_ARTICLES_PER_RUN` 或增加 `HOURS_LOOKBACK` 以降低候选文章数量。

**Q: GitHub Actions 没有运行？**
A: 确认仓库有实际 commit（全新空仓库可能不触发 cron）；检查 Actions 是否已启用。

---

## 技术栈

- **Python 3.11+**
- **Claude API** (`claude-opus-4-6`) — 中文摘要生成
- **feedparser** — RSS/Atom 解析
- **httpx** — HTTP 客户端
- **BeautifulSoup4** — GitHub Trending 爬取
- **GitHub Actions** — 定时任务调度
- **Telegram Bot API** — 消息推送

---

## License

MIT
