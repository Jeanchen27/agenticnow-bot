# CLAUDE.md — AgenticNow Bot 项目规则

## 项目背景

本项目使用 Python。所有脚本和自动化任务请优先使用 Python。

核心项目：**AgenticNow Telegram RSS 聚合机器人**
- 每日自动抓取 40 个信源（Newsletter、Podcast、Reddit、GitHub Trending）
- 用 Claude API 生成中文摘要，按相关度筛选推送到 Telegram 频道 @AgenticNow
- 推送完成后生成英文 X Thread 草稿，发送到管理员私聊审阅
- 通过 GitHub Actions 每天 UTC 04:00（北京时间 12:00）自动运行

## 通用规则

- 添加任何外部 URL（RSS Feed、API 端点等）之前，必须先用 `curl`/`fetch` 验证其真实可访问。**绝不猜测或幻觉 URL。**
- 不要创建不必要的文件，优先编辑现有文件。
- 不要过度工程化，保持简洁，只做被要求的改动。

## 代码质量

- 使用 Python 3.11+，类型注解优先。
- 所有外部 HTTP 请求使用 `httpx`（已有依赖），不引入新的 HTTP 库。
- AI 调用使用 `anthropic` SDK，模型默认 `claude-haiku-4-5`（摘要/生成任务），复杂推理用 `claude-sonnet-4-6`。
- 日志使用 `logging` 模块，不用 `print`（调试预览除外）。
- 环境变量通过 `os.environ.get()` 读取，敏感值（API Key、Token）必须从 GitHub Secrets 注入，不得硬编码。

## 测试

- 对于内容过滤/聚合系统：在宣布完成前，必须用真实数据样本测试过滤器。展示**通过**和**被拒绝**的内容示例，让用户能够验证过滤质量。
- 本地测试用 `python3 main.py --dry-run` 预览输出，不触发真实推送。
- 新增信源后需验证 feed 可正常解析（有效条目 > 0）。

## 内容/数据处理

- 对于内容过滤/聚合系统：在宣布完成前，必须用真实数据样本测试过滤器。展示**通过**和**被拒绝**的内容示例，让用户能够验证过滤质量。
- RSS 信源时间窗口：Newsletter/Podcast 用 168h（7天），Reddit 用 48h。
- 全量 Crypto 媒体（Decrypt、Bankless 等）必须加关键词预过滤，只保留与 AI / AI Agent 相关的文章。
- 最终推送 10~15 条，按类型排列：Newsletter → Podcast → Reddit → GitHub。
- 标题级去重：相同新闻多信源来源时只保留评分最高的一条。
- Claude 相关度评分 1~10，低于 6 分的文章不推送。

## 项目结构

```
agenticnow-bot/
├── main.py                  # 主流程入口
├── sources.py               # 40个信源配置
├── fetchers/
│   ├── rss.py               # RSS/Podcast 抓取（含关键词预过滤）
│   ├── reddit.py            # Reddit 抓取
│   └── github_trending.py   # GitHub Trending 抓取
├── processor/
│   ├── summarizer.py        # Claude 中文摘要 + 相关度评分
│   └── thread_writer.py     # X Thread 英文草稿生成
├── publisher/
│   └── telegram.py          # Telegram 推送 + 管理员私聊
├── storage/
│   └── dedup.py             # URL 去重存储
└── .github/workflows/
    └── daily.yml            # GitHub Actions 定时任务
```
