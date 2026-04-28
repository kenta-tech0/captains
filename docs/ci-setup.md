# CI / Pre-push チェック構成

push 前のローカル軽量チェック → push 後の GitHub Actions、という二段構えで「壊れたコードを main に乗せない」ことを目指す構成。

---

## 構成全体図

```
[ コードを書く ]
       │
       ▼
[ git commit ] ─── pre-commit が自動実行
                    ├ trailing-whitespace / EOF / YAML/TOML 検査
                    └ ruff check --fix / ruff format
       │
       ▼
[ make check ] ──── push 前に手動実行(任意だが推奨)
                    ├ ruff check
                    ├ ruff format --check
                    ├ mypy
                    └ import smoke (app.main を実 import)
       │
       ▼
[ git push ]
       │
       ▼
[ GitHub Actions: backend-ci ]
   ├ static-checks job
   │   ├ uv sync (依存解決)
   │   ├ ruff check / ruff format --check
   │   ├ mypy
   │   └ import smoke
   └ docker-build job
       └ docker build (Dockerfile + 依存宣言の最終確認)
```

---

## ファイル一覧

| ファイル | 役割 |
|---|---|
| `.github/workflows/backend-ci.yml` | GitHub Actions。`backend/**` 変更時のみ動く |
| `.pre-commit-config.yaml` | コミット直前の軽量チェック |
| `backend/Makefile` | `make check` などローカルクイックコマンド |
| `backend/pyproject.toml` の `[tool.ruff.lint]` / `[tool.mypy]` | 静的解析の設定 |

---

## 初回セットアップ

```bash
# 1) pre-commit を入れる (一度だけ)
pip install pre-commit
pre-commit install                 # このリポジトリで有効化
pre-commit run --all-files         # 既存ファイルにも一度走らせて整える

# 2) backend の依存を解決
cd backend
uv sync

# 3) 動作確認
make check
make build       # docker build まで通るか
```

---

## 日々のワークフロー

```bash
# コードを編集
$ vim backend/app/main.py

# (任意) コミット前にローカル全チェック
$ cd backend && make check

# コミット → pre-commit が走り ruff/whitespace 系を自動修正
$ git add -A && git commit -m "feat: ..."

# push → GitHub Actions が静的チェック + docker build
$ git push
```

---

## なぜこの分担にしたか

| チェック | ローカル | CI | 理由 |
|---|:-:|:-:|---|
| trailing-whitespace 等 | ✅ | — | 1 秒で終わる。CI で落とすほどでもない |
| ruff check / format | ✅ | ✅ | ローカルで自動修正、CI で「修正をコミットせず push した人」を捕まえる |
| mypy | ✅ | ✅ | 型エラーは早く気づきたい |
| import smoke | ✅ | ✅ | `gpt=4o` タイポや依存漏れみたいな致命傷を超低コストで検出 |
| docker build | △ | ✅ | ローカルだと数分かかるので毎 push は重い。CI に任せる |
| 単体/統合テスト | — | (将来) | テストが揃ってきたら CI に追加 |

---

## トラブルシュート

### `pre-commit install` 後、コミットができなくなった
hook が修正を入れてくれた場合、ファイルが変わっているので再度 `git add` → `git commit`。

### CI の mypy だけ落ちる
今は `continue-on-error: true` なので落ちても止まらないが、ローカルで `make typecheck` を試して原因を確認する。型エラーを直したら workflow から `continue-on-error` を消す。

### `make check` で `OPENAI_API_KEY` が要ると言われる
`AsyncOpenAI()` はクライアント初期化時に環境変数を見るので、import smoke でもダミー値が必要。Makefile では `OPENAI_API_KEY=dummy` を渡している。

### docker build が遅い
Actions では `cache-from: type=gha` で BuildKit のキャッシュを使っているので、2 回目以降は数倍速くなる。ローカルでも BuildKit (`DOCKER_BUILDKIT=1`) は有効にしておく。

---

## 今後追加候補

- **pytest を CI に追加**: テストを書き始めたら static-checks job に `uv run pytest` を追加
- **secrets スキャン**: `gitleaks-action` で API キーの誤コミットを防ぐ
- **コンテナ脆弱性スキャン**: `aquasecurity/trivy-action` で base image をチェック
- **frontend-ci.yml**: 同じ構成で `frontend/` 用に別ワークフローを足す
- **Dependabot**: `.github/dependabot.yml` で依存の自動更新 PR を有効化
