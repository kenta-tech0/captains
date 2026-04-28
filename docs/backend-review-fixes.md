# Backend Review & Fixes — 2026-04-28

`backend/` ディレクトリのレビューで検出した不具合と、本コミットで適用した修正の一覧。

---

## 修正サマリ

| # | 種別 | ファイル | 内容 |
|---|------|---------|------|
| 1 | Critical | `backend/app/main.py` | モジュール import 時に走る script コードを撤去し、`POST /generate` エンドポイント化 |
| 2 | Critical | `backend/app/main.py` | `from ai import ...` → `from app.ai import ...` に変更（`uvicorn app.main:app` で起動するため） |
| 3 | Critical | `backend/app/docx.py` → `docx_writer.py` | サードパーティ `python-docx` と完全に名前衝突していたためリネーム |
| 4 | Critical | `backend/app/ai.py` | `model="gpt=4o"` のタイポを `"gpt-4o"` に修正 |
| 5 | Critical | `backend/app/ai.py` / `main.py` | プロンプトファイル名と引数キーの不一致を解消（日本語キー → 英語キー `issues` / `plan` / `effect`） |
| 6 | Critical | `backend/pyproject.toml` | 未宣言だった `openai` と `python-docx` を `dependencies` に追加 |
| 7 | Critical | `backend/app/main.py` | CORS の `allow_origins` が空でフロントから叩けない状態を修正（環境変数 `ALLOWED_ORIGINS` から構成） |
| 8 | Important | `backend/app/ai.py`, `main.py`, `docx_writer.py` | 相対パス依存を `Path(__file__)` 基準の絶対パスに変更 |
| 9 | Important | `backend/Dockerfile` | `UV_COMPILE_BYCODE` のタイポを `UV_COMPILE_BYTECODE` に修正 |
| 10 | Important | `backend/app/docx_writer.py` | `paragraph.text = ...` 代入で書式が壊れる問題を run 単位の置換に修正、テーブル内段落もカバー |
| 11 | Important | `backend/app/ai.py` | 同期 `OpenAI` → `AsyncOpenAI` に変更し、`asyncio.gather` で 3 セクション並列生成 |
| 12 | Important | `backend/app/main.py` | template.docx 不在/空のときに 500 で早期失敗する明示ガードを追加 |

---

## 詳細と背景

### 1. main.py が import 時に副作用を起こしていた

旧コード:
```python
with open("sample_conversation.txt") as f:
    conversation = f.read()
data = extract_structure(conversation)
sections = { ... generate_section(...) ... }
fill_docx("templates/template.docx", "output.docx", sections)
print("output.docx を生成しました")
```

`uvicorn app.main:app` がモジュールをロードするたびに OpenAI を叩き docx 生成する状態。サーバ起動が確実に失敗する上、API キーが無いと健全な health check すらできない。

→ `POST /generate { "conversation": "..." }` を受け取り `output.docx` を `FileResponse` で返す形に再構築。一時ファイルは送信後に `BackgroundTask` で削除。

### 2. import パスの誤り

旧: `from ai import ...` / `from docx import fill_docx`
- `app.main` モジュールから見た正しいパスは `from app.ai import ...`。
- `from docx import fill_docx` はサードパーティ `python-docx` と名前衝突しており、`backend/app/docx.py` 自身が `from docx import Document` を実行した瞬間に再帰 import の危険があった。

→ ローカルファイルを `docx_writer.py` にリネームし、`from app.docx_writer import fill_docx` に統一。

### 3. プロンプトファイル名の不一致

旧 `main.py`:
```python
generate_section("課題", data)   # → prompts/課題.txt を探す
generate_section("事業計画", data) # → prompts/事業計画.txt を探す
generate_section("効果", data)   # → prompts/効果.txt を探す
```

実ファイルは `issue.txt` / `plan.txt` / `effect.txt`。100% `FileNotFoundError`。

→ `ai.py` に `SECTION_PROMPTS = {"issues": "issue.txt", "plan": "plan.txt", "effect": "effect.txt"}` のマッピングを置き、main 側からは英語キーで呼ぶ。

### 4. CORS

旧: `allow_origins=[]`（コメントアウトされた TODO のみ）
→ 環境変数 `ALLOWED_ORIGINS`（カンマ区切り）から構成。デフォルトは `http://localhost:3000`。

### 5. パス解決

`load_prompt("prompts/extract.txt")` / `open("sample_conversation.txt")` / `"templates/template.docx"` はすべて CWD 依存。Docker では CWD は `/app` で、ファイルは `/app/app/...` に置かれるため `FileNotFoundError`。

→ `Path(__file__).parent` 基準に統一。

### 6. python-docx の段落書式

旧:
```python
for p in doc.paragraphs:
    for k, v in mapping.items():
        if k in p.text:
            p.text = p.text.replace(k, v)
```

`paragraph.text = ...` への代入は全 run を破棄し 1 run に潰す。フォント・太字・サイズなどの書式が消える。

→ `_replace_in_paragraph` で各 run の `run.text` を直接置換。プレースホルダが run をまたぐ場合のみ最初の run にマージ。表セル内段落も走査。

### 7. AsyncOpenAI

FastAPI は async ランタイム。同期 client を使うと event loop がブロックされ、同時リクエストを処理できない。さらに 3 セクションの生成を `asyncio.gather` で並列化することで 1 リクエストあたりのレイテンシを 1/3 に短縮。

---

## 残課題（このコミットでは未対応）

| 項目 | 影響 | 対応案 |
|------|------|--------|
| ~~`backend/app/templates/template.docx` が **0 バイト**~~ | ~~`/generate` 実行時 500 で落ちる~~ | **解消済み**: `r1y2-1.docx` を素テンプレ、`scripts/build_template.py` を加工スクリプトとし、生成物 `template.docx` をコミットに含めた |
| `OPENAI_API_KEY` の管理が暗黙 | 本番でキー欠落に気づきにくい | `pydantic-settings` で `Settings` を作り起動時に検証 |
| `pyproject.toml` で宣言済の `sqlalchemy` / `asyncmy` / `azure-cosmos` が未使用 | image サイズ / supply chain | 実際に使う時点まで削除するか、使う側のモジュールを実装 |
| エラーハンドリング・rate limit / timeout | OpenAI 側障害でリクエストが詰まる | `httpx.Timeout` / リトライ / 5xx マッピング |
| `sample_conversation.txt` の置き場所 | 本番にも同梱されている | `backend/tests/fixtures/` に移動するか `.dockerignore` |
| ロギング | デバッグ困難 | `logging.getLogger(__name__)` で構造化ログ |

---

## テンプレート構成

| ファイル | 役割 |
|---|---|
| `backend/app/templates/r1y2-1.docx` | 持続化補助金 様式2-1 の素テンプレ。プレースホルダ無し |
| `backend/scripts/build_template.py` | 素テンプレに `{{company}}` 等を差し込むビルドスクリプト |
| `backend/app/templates/template.docx` | ランタイムが読む生成物。スクリプトで再生成可能 |

挿入位置のマッピングは `build_template.py` の `INSERTIONS` 定数を参照。

```bash
# 素テンプレを更新したらこれで template.docx を作り直す
uv run python backend/scripts/build_template.py
```

---

## 動作確認手順

```bash
cd backend
uv sync
export OPENAI_API_KEY=sk-...
export ALLOWED_ORIGINS=http://localhost:3000

# ※ templates/template.docx を実体のあるテンプレートに差し替えてから
uv run uvicorn app.main:app --reload --port 8000
```

別ターミナルで:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile c backend/app/sample_conversation.txt '{conversation:$c}')" \
  --output out.docx
```
