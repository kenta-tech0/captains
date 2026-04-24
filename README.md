# 経産省クエスト (Captains)

中小企業庁 × 生成AIによる **補助金マッチング・申請支援アプリケーション** のリポジトリです。
事業に悩みを抱える中小企業経営者が、自分に合った補助金を AI との対話を通じて発見し、申請まで進められることを目指しています。

---

## 目次

- [プロジェクト概要](#プロジェクト概要)
- [技術スタック](#技術スタック)
- [前提：これからインストールするもの](#前提これからインストールするもの)
- [Docker ってなに？（初めての人向け）](#docker-ってなに初めての人向け)
- [環境構築手順（はじめての人向け）](#環境構築手順はじめての人向け)
- [開発の進め方](#開発の進め方)
- [ポート・URL 一覧](#ポートurl-一覧)
- [ホスト側で使うコマンド集](#ホスト側で使うコマンド集)
- [コンテナ内で使うコマンド集](#コンテナ内で使うコマンド集)
- [トラブルシューティング](#トラブルシューティング)
- [プロジェクト構成](#プロジェクト構成)

---

## プロジェクト概要

- **対象ユーザー**: 事業課題を感じている中小企業経営者
- **MVP スコープ**: 国（経産省／中小企業庁）の補助金を対象（自治体分は将来対応）
- **特徴**:
  - 政府が保有する補助金認定情報・相談窓口情報を活用
  - 既存政策（補助金、よろず支援拠点）と接続した出口設計
  - 「申請を楽にする」だけでなく「経営判断を促す対話」を組み込む

---

## 技術スタック

| レイヤー | 技術 |
|---|---|
| フロントエンド | Next.js 16（App Router） / React 19 / TypeScript / Tailwind CSS 4 |
| バックエンド | FastAPI / Python 3.13 / SQLAlchemy 2.x / Uvicorn |
| RDB | MySQL 8.4 |
| NoSQL | Azure Cosmos DB Emulator（vNext, NoSQL API） |
| パッケージ管理 | npm（フロント） / uv（バックエンド） |
| 開発環境 | Docker Compose v2 + VS Code Dev Containers |

> **大事なポイント**: このプロジェクトは **Dev Containers** が唯一の開発パスです。
> ローカルに Node.js や Python を直接インストールする必要はありません。Docker さえ動けば OK です。

---

## 前提：これからインストールするもの

以下 2 つをインストールしてください。（Mac / Windows どちらも OK）

1. **Docker Desktop**
   - [公式サイト](https://www.docker.com/products/docker-desktop/) からダウンロード
   - インストール後、Docker Desktop アプリを **起動したまま** にしておく（クジラのアイコンが出ていれば OK）
2. **Dev Containers 拡張機能**（VS Code 内でインストール）
   - VS Code を開く → 左の四角アイコン（拡張機能） → `Dev Containers` で検索 → Microsoft 公式のものをインストール

---

## Docker ってなに？（初めての人向け）

ざっくり言うと **「開発に必要な OS・ライブラリ・ツールが全部入った、使い捨てできる小さなパソコン」** を自分の PC の中に立ち上げる仕組みです。

チーム開発で起きがちな
「私のマシンでは動くんだけど…」
「Node のバージョンが違う…」
「MySQL のインストールで半日潰れた…」
といった問題を、**全員が同じ環境を使う**ことで解決します。

このプロジェクトでよく出てくる用語：

| 用語 | ひとことで言うと |
|---|---|
| **イメージ (image)** | コンテナを作るための「設計図」 |
| **コンテナ (container)** | イメージから起動した「実行中の小さな PC」 |
| **Dockerfile** | イメージを作るレシピ |
| **Docker Compose** | 複数のコンテナ（フロント、DB など）をまとめて起動・停止する仕組み |
| **ボリューム (volume)** | コンテナを消してもデータを残したい時に使う「外付け HDD」みたいなもの |
| **Dev Container** | VS Code がコンテナの中に入り込んで、そこで開発できる仕組み |

---

## 環境構築手順（はじめての人向け）

> 所要時間：初回は **15〜30 分程度**（ネットワーク状況による）

### ステップ 1：リポジトリをクローン

```bash
git clone https://github.com/kenta-tech0/captains.git
cd captains
```

### ステップ 2：`.env` ファイルを作成

`.env.example` をコピーして `.env` という名前にします。

```bash
cp .env.example .env
```

> `.env` は機密情報を入れるファイルで、Git にコミットされません（`.gitignore` 済み）。
> 開発用のパスワードは初期値のままで OK です。

### ステップ 3：Docker Desktop を起動

タスクバー／メニューバーに **クジラのアイコン** が表示されていることを確認してください。表示されていなければ Docker Desktop アプリを起動してください。

### ステップ 4：VS Code でプロジェクトを開く

```bash
code .
```

もしくは VS Code で「フォルダーを開く」から `captains` を選択。

### ステップ 5：Dev Container で再オープン

VS Code の右下に **「Reopen in Container（コンテナーで再度開く）」** の通知が出ます。
出ない場合は：

- `F1`（または `Cmd+Shift+P` / `Ctrl+Shift+P`）を押す
- `Dev Containers: Reopen in Container` と入力して選択

すると **どちらのコンテナで開くか** 聞かれます：

- **`captains · frontend`** を選ぶ → フロントエンド開発用
- **`captains · backend`** を選ぶ → バックエンド開発用

> どちらを選んでも MySQL と Cosmos DB は自動で裏側で立ち上がります。
> 両方同時に開発したい場合は VS Code ウィンドウを 2 つ起動して、片方でフロント、もう片方でバックを開けば OK です。

### ステップ 6：初回ビルドを待つ

初回は Docker イメージのダウンロード＆ビルドが走るので **数分〜十数分** かかります。
「Starting Dev Container…」のログが流れているので、落ち着いて待ちましょう。

### ステップ 7：自動で開発サーバーが起動する

- **frontend コンテナ**: `npm run dev` が自動実行 → http://localhost:3000
- **backend コンテナ**: `uvicorn app.main:app --reload` が自動実行 → http://localhost:8000

ブラウザで以下にアクセスして確認：

- http://localhost:3000 → Next.js の画面が表示される
- http://localhost:8000/health → `{"status":"ok"}` が返ってくる
- http://localhost:8000/docs → FastAPI の API ドキュメント（Swagger UI）

これで環境構築は完了です 🎉

---

## 開発の進め方

### ファイルを編集する

VS Code 上で普通にファイルを編集するだけで OK です。
変更は即座にコンテナ内に反映され、**ホットリロード**で画面も自動更新されます。

- フロント（Next.js）→ 保存すると自動でブラウザが更新
- バックエンド（FastAPI）→ 保存すると `--reload` により自動で再起動

### ターミナルを開く

VS Code 内で `` Ctrl + ` `` （バッククォート）でターミナルが開きます。これは **コンテナの中のシェル** です。
ここで `npm` や `uv` のコマンドを直接叩けます。

詳しいコマンド一覧は [コンテナ内で使うコマンド集](#コンテナ内で使うコマンド集) を参照してください。

### Dev Container を停止したい

VS Code のウィンドウを閉じるだけで OK。コンテナは自動で停止します。
MySQL / Cosmos DB も止めたい場合は、ホスト側のターミナルで：

```bash
docker compose down
```

---

## ポート・URL 一覧

| サービス | URL | 用途 |
|---|---|---|
| Next.js（フロント） | http://localhost:3000 | 画面 |
| FastAPI（バック） | http://localhost:8000 | API |
| FastAPI ドキュメント | http://localhost:8000/docs | Swagger UI |
| FastAPI ヘルスチェック | http://localhost:8000/health | 動作確認 |
| MySQL | `localhost:3306` | DB クライアントから接続 |
| Cosmos DB Gateway | http://localhost:8081 | エミュレータ API |
| Cosmos DB Data Explorer | http://localhost:1234/_explorer/index.html | DB の中身を GUI で確認 |

---

## トラブルシューティング

### 「port is already allocated」と言われる

すでに 3306 / 3000 / 8000 などのポートを他のプロセスが使っています。

- 別の MySQL がローカルで動いていないか確認（`brew services list` など）
- 前回の Docker Compose がゾンビ化していないか → `docker compose down` で停止

### Dev Container のビルドで止まる・エラーになる

1. Docker Desktop が起動しているか確認（クジラのアイコン）
2. `F1` → `Dev Containers: Rebuild Container` で再ビルド
3. それでもダメなら `F1` → `Dev Containers: Rebuild Without Cache and Reopen in Container`

### MySQL に接続できない

- `docker compose ps` で `mysql` が `healthy` になっているか確認
- 起動直後はヘルスチェックに 30 秒ほど猶予があるので少し待つ
- `.env` のパスワードを変更した直後の場合、ボリュームを消して再作成が必要：
  ```bash
  docker compose down -v
  docker compose up -d mysql cosmosdb
  ```

### Cosmos DB エミュレータが重い／起動が遅い

vNext preview エミュレータは初回起動に **30〜60 秒** かかることがあります。
`docker compose logs -f cosmosdb` でログを見ながら待ちましょう。

### npm install / uv sync が遅い

初回だけは仕方ありません。2 回目以降はキャッシュが効くので速くなります。

### VS Code でファイル保存が反映されない

- Dev Container の中で VS Code を開いているか確認（左下に「Dev Container: captains · frontend」のような表示があれば OK）
- ホスト側の VS Code でファイルを触っていないか確認

---

## プロジェクト構成

```
captains/
├── .devcontainer/
│   ├── frontend/devcontainer.json    # フロント用 Dev Container 設定
│   └── backend/devcontainer.json     # バック用 Dev Container 設定
├── .env.example                      # 環境変数のテンプレート（これをコピーして .env を作る）
├── compose.yaml                      # MySQL + Cosmos DB の定義
├── frontend/                         # Next.js アプリ
│   ├── Dockerfile
│   ├── app/                          # App Router のページ
│   ├── public/                       # 静的アセット
│   ├── package.json
│   └── tsconfig.json
└── backend/                          # FastAPI アプリ
    ├── Dockerfile
    ├── app/
    │   └── main.py                   # エントリポイント
    ├── pyproject.toml                # 依存関係定義
    └── uv.lock
```

---

## 困ったときは

- まずは上の [トラブルシューティング](#トラブルシューティング) を確認
- それでも解決しなければチームの Slack / Notion で気軽に質問してください
- エラーメッセージは省略せず、**全文コピペ** で共有するとスムーズに解決できます
