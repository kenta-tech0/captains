# backend/ の手元クイックチェック用ターゲット集
#
# 使い方:
#   make check      # push 前にこれだけ走らせれば 9 割の事故は防げる
#   make lint       # 個別: lint だけ
#   make fmt        # フォーマット適用
#   make build      # docker image をローカルでビルドして依存漏れを検出

.PHONY: check lint fmt typecheck import-smoke build clean

# CI と同じ静的チェックをローカルで一括実行
check: lint typecheck import-smoke
	@echo "[OK] all local checks passed"

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	-uv run mypy app

# import 解決と最低限の起動可能性チェック
# (OPENAI_API_KEY は import に必須ではないがダミーを渡しておく)
import-smoke:
	OPENAI_API_KEY=dummy uv run python -c "import app.main; print('import OK')"

build:
	docker build -t captains-backend:dev .

clean:
	rm -rf .ruff_cache .mypy_cache .pytest_cache __pycache__ */__pycache__
