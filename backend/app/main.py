# ============================================================
# main.py
#   FastAPI アプリのエントリポイント。
#   uvicorn app.main:app で起動されると、ここの `app` が呼ばれる。
# ============================================================

import asyncio  # 複数の async 処理を並列実行するため (asyncio.gather)
import os  # 環境変数の読み出し
import tempfile  # 一時ファイル(出力 docx)の作成
from pathlib import Path  # OS非依存のパス操作

from fastapi import FastAPI, HTTPException  # FastAPI 本体とエラー応答
from fastapi.middleware.cors import CORSMiddleware  # ブラウザからのクロスオリジン許可
from fastapi.responses import FileResponse  # ファイルをレスポンスとして返す
from pydantic import BaseModel  # リクエストボディのスキーマ定義
from starlette.background import BackgroundTask  # レスポンス送信後に走らせる後処理

# 自作モジュール（同一パッケージ app.* 配下）
from app.ai import extract_structure, generate_section  # OpenAI 呼び出しロジック
from app.docx_writer import fill_docx  # docx テンプレ穴埋めロジック

# --- パス設定 ----------------------------------------------------------------
# __file__ はこの main.py 自身の絶対パス。.parent でディレクトリを取得すれば、
# サーバの「現在の作業ディレクトリ」に依存せず安全に相対ファイルを参照できる。
APP_DIR = Path(__file__).parent
TEMPLATE_PATH = APP_DIR / "templates" / "template.docx"


# --- CORS 許可オリジン -------------------------------------------------------
# 環境変数 ALLOWED_ORIGINS をカンマ区切りで受け取り、空白を除いてリスト化。
# 例: ALLOWED_ORIGINS="http://localhost:3000,https://app.example.com"
_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]


# --- FastAPI アプリ本体 ------------------------------------------------------
app = FastAPI(title="Captains Backend")

# ブラウザの SOP(Same-Origin Policy) を超えてフロントから叩けるよう CORS を設定。
# allow_origins が空だと一切受け付けないので、必ず実環境のドメインを入れること。
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- リクエストスキーマ ------------------------------------------------------
# Pydantic の BaseModel を継承するだけで、JSON のバリデーションが自動で走る。
# 不正な型・欠落フィールドは FastAPI が 422 で返してくれる。
class GenerateRequest(BaseModel):
    conversation: str  # フロントから送られてくる「ヒアリング会話文」


# --- 死活監視用 --------------------------------------------------------------
# ロードバランサや監視ツールが叩く軽量エンドポイント。
@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- メイン処理: 会話文 → 申請書 docx ----------------------------------------
@app.post("/generate")
async def generate(req: GenerateRequest):
    # テンプレ docx が無い／空だとこの先必ず落ちるので、ここで早期に 500 を返す。
    if not TEMPLATE_PATH.exists() or TEMPLATE_PATH.stat().st_size == 0:
        raise HTTPException(
            status_code=500,
            detail=f"docx template missing or empty: {TEMPLATE_PATH}",
        )

    # ① 会話ログから JSON 構造データへ抽出（OpenAI 呼び出し）
    data = await extract_structure(req.conversation)

    # ② 3 セクションを並列生成。直列だと約 3 倍時間がかかるので gather で同時実行。
    issues, plan, effect = await asyncio.gather(
        generate_section("issues", data),
        generate_section("plan", data),
        generate_section("effect", data),
    )

    # ③ docx に差し込むプレースホルダ → 値 のマップを組み立て
    sections = {
        "company": data["company"]["name"],
        "issues": issues,
        "plan": plan,
        "effect": effect,
    }

    # ④ 出力先の一時ファイルを作る。
    #    delete=False にしておかないと close した瞬間に消えてしまうので注意。
    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp.close()
    output_path = Path(tmp.name)

    # ⑤ テンプレ docx にデータを差し込み、output_path に保存。
    #    途中で例外が出たら、ゴミ一時ファイルを掃除してから例外を再送出する。
    try:
        fill_docx(TEMPLATE_PATH, output_path, sections)
    except Exception:
        output_path.unlink(missing_ok=True)
        raise

    # ⑥ ファイルをレスポンスとして返す。
    #    BackgroundTask は「レスポンス送信完了後」に動くので、
    #    クライアントへ送り終わってから安全に一時ファイルを削除できる。
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="output.docx",
        background=BackgroundTask(output_path.unlink, missing_ok=True),
    )
