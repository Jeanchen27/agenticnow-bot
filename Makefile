.PHONY: install dry-run dry-run-digest dry-run-5 run run-digest check-sources clean

# ─── 安装依赖 ──────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

# ─── 预览模式（不推送 Telegram）────────────────────────────────────────────────
dry-run:
	python main.py --dry-run

dry-run-5:
	python main.py --dry-run --max-articles 5

dry-run-digest:
	python main.py --dry-run --mode digest

# ─── 正式运行 ──────────────────────────────────────────────────────────────────
run:
	python main.py

run-digest:
	python main.py --mode digest

run-twitter:
	python main.py --enable-twitter

# ─── 信源检测 ──────────────────────────────────────────────────────────────────
check-sources:
	python scripts/check_sources.py

check-sources-verbose:
	python scripts/check_sources.py --verbose

# ─── 清理 ──────────────────────────────────────────────────────────────────────
clean:
	rm -f seen_urls.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true

# ─── 帮助 ──────────────────────────────────────────────────────────────────────
help:
	@echo "AgenticNow Bot - 常用命令"
	@echo ""
	@echo "  make install              安装 Python 依赖"
	@echo "  make dry-run              预览模式（不推送，默认12篇）"
	@echo "  make dry-run-5            预览模式（只看5篇）"
	@echo "  make dry-run-digest       预览每日合集格式"
	@echo "  make run                  正式推送（单篇模式）"
	@echo "  make run-digest           正式推送（合集模式）"
	@echo "  make check-sources        检测所有 RSS 信源健康状态"
	@echo "  make check-sources-verbose 详细检测模式（含文章列表）"
	@echo "  make clean                清理缓存和 seen_urls.json"
