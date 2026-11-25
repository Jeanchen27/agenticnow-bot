# AgenticNow Daily Bot

每日抓取英文 AI / Crypto 信源，用智谱 GLM 生成中文编译标题 + 摘要，推送到 [@AgenticNow](https://t.me/AgenticNow)。

正式入口：`pipeline.py`。`main.py` 只做转调，旧命令仍然能用。

---

## 实际能力

- 信源：40 个 RSS（newsletter / podcast / rss）+ 3 个 Reddit + GitHub Trending
- 流水线：抓取 → URL/标题去重 → 关键词预过滤 → GLM 中文编译与评分 → Telegram
- 默认推送：digest 合集，12 篇；RSS 窗口 168 小时，Reddit 48 小时
- 模型：智谱 GLM（默认 `glm-5.3-flash`，可通过 `GLM_MODEL` 覆盖）
- 调度：GitHub Actions 无内置 cron，由 cron-job.org 触发 `daily.yml`

没有 Twitter / RSSHub 抓取。那是旧文档，已经删掉。

---

## 项目结构

```
agenticnow-bot/
├── pipeline.py              # 正式入口
├── main.py                  # 转调 pipeline.py
├── sources.py               # 信源配置
├── fetchers/                # RSS / Reddit / GitHub
├── agents/                  # 三代理流水线
├── processor/summarizer.py
├── publisher/telegram.py
├── storage/dedup.py
├── scripts/check_sources.py
├── tests/
└── .github/workflows/daily.yml
```

---

## 快速开始

```bash
cd agenticnow-bot
pip install -r requirements.txt
cp .env.example .env
# 填入 GLM_API_KEY / TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID
```

```bash
python pipeline.py --dry-run              # 预览，不推送
python pipeline.py --dry-run --max-articles 5
python pipeline.py --mode individual      # 逐条推送
python pipeline.py                        # 正式：digest，12 篇
make check-sources
```

兼容：`python main.py --dry-run` 与 `--hours-lookback`、`--disable-github` 仍可用。

---

## Telegram 机器人设置

1. 在 Telegram 搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`，获取 Bot Token
3. 将机器人添加为频道管理员（需要发消息权限）
4. 公开频道用 `@频道用户名`；私有频道用数字 ID

---

## GitHub Actions

仓库 → Settings → Secrets and variables → Actions：

| Secret | 说明 |
|--------|------|
| `GLM_API_KEY` | 智谱 GLM API Key |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHANNEL_ID` | 如 `@AgenticNow` |
| `TELEGRAM_ADMIN_ID` | 信源体检告警用（可选） |

`daily.yml` 默认 digest、12 篇、RSS 168h，跑完会提交 `seen_urls.json` 和 `daily-digest/`。

手动触发：Actions → AgenticNow Daily Bot → Run workflow。

---

## 常见问题

**Q: 运行后没有推送？**  
A: 文章已在 `seen_urls.json`，或窗口内无新内容。先 `--dry-run`。记录只保留 30 天，停机超过 30 天再跑可能重发旧文。

**Q: Telegram 报 403？**  
A: 确认机器人是频道管理员，且有发送消息权限。

**Q: GLM API 限流或配额不足？**  
A: 减小 `--max-articles`，或在 `.env` 中调整 `GLM_MODEL`。

---

## 技术栈

- Python 3.11+
- 智谱 GLM API（`glm-5.3-flash`，通过 `httpx` 调用）
- feedparser / httpx / BeautifulSoup4
- GitHub Actions + Telegram Bot API

## License

MIT
