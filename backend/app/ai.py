# ============================================================
# ai.py
#   OpenAI API を呼び出して、会話文 → 構造化 JSON や、
#   構造化 JSON → 申請書セクション文章 を生成するモジュール。
# ============================================================

import json  # OpenAI レスポンスの JSON パース・dict→文字列化
from pathlib import Path  # プロンプト .txt ファイルの絶対パス解決

# AsyncOpenAI: 非同期(await 可)版の OpenAI クライアント。
# 同期版 OpenAI を使うと FastAPI の event loop がブロックされるので注意。
from openai import AsyncOpenAI

# --- 定数 --------------------------------------------------------------------

# プロンプトファイル(.txt)を置いてあるディレクトリ。
# Path(__file__).parent はこの ai.py がある場所(app/) を指すので、
# サーバの作業ディレクトリに依存せず確実に prompts/ を見つけられる。
PROMPTS_DIR = Path(__file__).parent / "prompts"

# 申請書セクションのキー → 対応するプロンプトファイル名 の対応表。
# main.py 側からは英語キーで呼ぶ約束にし、ファイル名のブレを吸収する。
SECTION_PROMPTS = {
    "issues": "issue.txt",  # 課題
    "plan": "plan.txt",  # 補助事業計画
    "effect": "effect.txt",  # 期待される効果
}

# 使用する OpenAI モデル名。差し替えたいときはここを 1 箇所変えるだけで済む。
MODEL_NAME = "gpt-4o"

# クライアントは「使い回す」のがベストプラクティス。
# 内部で HTTP コネクションプールを持っているので、リクエストごとに作らない。
# OPENAI_API_KEY 環境変数が自動で読み込まれる。
client = AsyncOpenAI()


# --- ヘルパー ----------------------------------------------------------------


def _load_prompt(filename: str) -> str:
    """prompts/ 配下の .txt を UTF-8 で読み込んで文字列で返す。"""
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


# --- ① 会話文 → 構造化 JSON --------------------------------------------------


async def extract_structure(conversation: str) -> dict:
    """ヒアリング会話文を入力し、申請書に必要な情報を JSON で抽出する。"""

    # extract.txt 内の {conversation} に会話本文を埋め込む。
    # Python の str.format は中括弧 {name} をプレースホルダとして扱う。
    prompt = _load_prompt("extract.txt").format(conversation=conversation)

    # response_format={"type": "json_object"} を指定すると、
    # OpenAI 側が「必ず JSON で返す」モードになる。後段のパースが安全に。
    res = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    # choices[0].message.content にモデルが返した文字列が入る。
    # JSON モードを指定しているのでそのまま json.loads で dict 化できる。
    return json.loads(res.choices[0].message.content)


# --- ② 構造化 JSON → セクション本文 -----------------------------------------


async def generate_section(section_key: str, data: dict) -> str:
    """指定セクション(issues / plan / effect)の本文を LLM に書かせる。"""

    # 想定外のキーが渡されたら早期に弾く。タイポ検出にもなる。
    if section_key not in SECTION_PROMPTS:
        raise ValueError(f"unknown section: {section_key}")

    # 対応するプロンプトテンプレを読み込み、{data} に入力 JSON を埋め込む。
    # ensure_ascii=False で日本語をエスケープせず、そのまま渡す。
    prompt = _load_prompt(SECTION_PROMPTS[section_key]).format(
        data=json.dumps(data, ensure_ascii=False)
    )

    # こちらは自由文(プレーンテキスト)を返すので response_format は指定しない。
    res = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    return res.choices[0].message.content
