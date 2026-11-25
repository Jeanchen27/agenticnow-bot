# CLAUDE.md — AgenticNow Bot 项目规则

## 项目背景

本项目使用 Python。所有脚本和自动化任务请优先使用 Python。

核心项目：**AgenticNow Telegram RSS 聚合机器人**
- 抓取 40 个 RSS（newsletter / podcast / rss）、3 个 Reddit、GitHub Trending
- 用智谱 GLM API（默认 `glm-5.3-flash`）生成中文编译标题 + 摘要，按相关度筛选后推送到 @AgenticNow
- 正式入口是 `pipeline.py`（`main.py` 只是转调）
- GitHub Actions `daily.yml` 无 cron，由 cron-job.org 触发；默认 digest、12 篇、RSS 168h

## 通用规则

- 添加任何外部 URL（RSS Feed、API 端点等）之前，必须先用 `curl`/`fetch` 验证其真实可访问。**绝不猜测或幻觉 URL。**
- 不要创建不必要的文件，优先编辑现有文件。
- 不要过度工程化，保持简洁，只做被要求的改动。
- 改行为时同步改 README、Makefile、`.env.example`、本文件。不要留第二套入口。

## 代码质量

- 使用 Python 3.11+，类型注解优先。
- 所有外部 HTTP 请求使用 `httpx`（已有依赖），不引入新的 HTTP 库。
- AI 调用使用智谱 GLM HTTP 接口（`GLM_API_KEY`，默认 `glm-5.3-flash`，可通过 `GLM_MODEL` 配置）。
- 日志使用 `logging` 模块，不用 `print`（调试预览除外）。
- 环境变量通过 `os.environ.get()` 读取，敏感值（API Key、Token）必须从 GitHub Secrets 注入，不得硬编码。

## 测试

- 对于内容过滤/聚合系统：在宣布完成前，必须用真实数据样本测试过滤器。展示**通过**和**被拒绝**的内容示例，让用户能够验证过滤质量。
- 本地测试用 `python pipeline.py --dry-run` 预览输出，不触发真实推送。
- 过滤器回归：`python -m pytest tests/ -q`
- 新增信源后需验证 feed 可正常解析（有效条目 > 0）。

## 内容/数据处理

- RSS 信源时间窗口：Newsletter/Podcast 用 168h（7天），Reddit 用 48h。
- 全量 Crypto 媒体（Decrypt、Bankless 等）必须加关键词预过滤，只保留与 AI / AI Agent 相关的文章。
- 最终推送 10~15 条，按类型排列：Newsletter → Podcast → Reddit → GitHub。
- 标题级去重：相同新闻多信源来源时只保留评分最高的一条。
- GLM 相关度评分 1~10，低于 6 分或未通过中文编译校验的文章不推送。

## 项目结构

```
agenticnow-bot/
├── pipeline.py              # 正式入口：三代理流水线
├── main.py                  # 兼容转调，勿再写逻辑
├── sources.py               # 信源配置
├── skill_pipeline.py        # Skill 推荐线（独立，workflow 已下线）
├── fetchers/                # RSS / Reddit / GitHub / Skill 抓取
├── agents/                  # source_validator → content_scorer → draft_formatter
├── processor/summarizer.py  # GLM 中文编译摘要 + 相关度评分
├── publisher/telegram.py    # Telegram 推送
├── storage/dedup.py         # URL 去重
├── scripts/                 # check_sources / heal_sources
├── tests/                   # 过滤与去重测试
└── .github/workflows/
    ├── daily.yml            # 日报（外部 cron 触发）
    └── source-health.yml    # 每周信源体检
```
