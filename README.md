# captains

経産省クエスト（中小企業庁）向け補助金マッチング・申請支援アプリ。
小規模事業者が「自社に合う補助金を見つけ、相談しながら申請まで進める」体験を、生成AIで支えるプロダクト。

---

## プロジェクト背景

**経産省クエスト**は中小企業庁（経済産業省）と連携した課題解決型プロジェクト。全4チームが同じクエストに取り組んでおり、キャプテンズはその1チーム。

- **主担当者**: 中小企業庁・生産性向上支援室 村上さん
- **コアテーマ**: 既存の中小企業支援策に生成AIを組み込み、**中小企業がAIの恩恵を実感できる**サービスを作る
- **政府がやる意義（上司説明の要）**:
  1. **政府データの活用**（計画認定情報・相談窓口情報など政府しか持たない情報）
  2. **既存政策との接続**（補助金・よろず支援拠点など、民間では難しい出口を持つ）
- **MVPスコープ**: 国の補助金制度に絞る（自治体は将来拡張）
- **ターゲット**: 小規模事業者（専門家不在の中小企業経営者、B/C 層＝課題を感じている層）
- **重要な設計原則**: 「楽に申請できる」だけでなく、**経営判断を促す対話プロセス**を必ず挟む

詳しい議事録と意思決定の経緯は [Notion: 経産省クエスト（キャプテンズ）](https://www.notion.so/31d0c2f661938020aa30df2f2b8c0795) を参照。

---

## 技術スタック

| レイヤ | 採用技術 | 用途 |
|---|---|---|
| Frontend | Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS | UI |
| Backend | FastAPI (Python 3.13) + SQLAlchemy + Uvicorn | API |
| RDB | MySQL 8.4 LTS | 補助金マスタ・ユーザ・申請データ |
| NoSQL | Azure Cosmos DB vNext Emulator (NoSQL API) | 対話履歴・AI コンテキスト |
| Orchestration | Docker Compose v2 | ローカル開発（devcontainer 経由で起動） |
| DX | VS Code Dev Containers（frontend / backend 別） | チーム統一環境 |

ディレクトリ構成:

```
captains/
├── frontend/          # Next.js アプリ
├── backend/           # FastAPI アプリ
├── compose.yaml       # 4 サービスを束ねるメイン compose
├── .devcontainer/
│   ├── docker-compose.dev.yml     # devcontainer 用オーバーレイ
│   ├── frontend/devcontainer.json
│   └── backend/devcontainer.json
├── .env.example
└── README.md
```

---

## 環境構築

前提として **Docker Desktop**（または OrbStack / Docker Engine）と **VS Code** が入っていること。本プロジェクトは **VS Code Dev Containers で開くのが唯一の公式フロー**です。拡張機能・Linter・Claude Code CLI まで統一された状態で立ち上がるので、ローカル Node / Python の差異に悩まされません。

1. VS Code 拡張 **Dev Containers**（`ms-vscode-remote.remote-containers`）をインストール
2. リポジトリを clone して VS Code で開く
3. 初回のみ `.env` を作成

   ```bash
   cp .env.example .env
   ```

4. コマンドパレット（`Cmd+Shift+P` / `Ctrl+Shift+P`）→ **Dev Containers: Reopen in Container**
5. **frontend** か **backend** を選ぶ（どちらを選んでも monorepo 全体は見える）
6. 初回ビルドは数分かかる。終わったら統合ターミナルで `whoami` → `vscode` が返ればOK

#### devcontainer の使い分け

| 担当 | 選ぶ devcontainer | 中で走っているもの |
|---|---|---|
| UI 実装 | frontend | `next dev`（Next.js Hot Reload） |
| API 実装 | backend | `uvicorn --reload`（FastAPI Hot Reload） |
| 仕様駆動で両方見たい | どちらでも可 | **どちらを選んでも frontend/ も backend/ も VS Code エクスプローラに表示される** |

#### Claude Code の初回ログイン

1. devcontainer 内のターミナルで `claude login` を実行
2. 以降は **VS Code 再起動しても、devcontainer を rebuild しても、frontend↔backend を切り替えてもログイン情報は保持される**
3. ログインを破棄したい時だけ `docker volume rm captains-claude-config`

#### アクセス先

| サービス | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| Backend API docs | http://localhost:8000/docs |
| MySQL | `localhost:3306`（`.env` の認証情報を使用） |
| Cosmos DB Gateway | http://localhost:8081 |
| Cosmos DB Data Explorer | http://localhost:1234/_explorer/index.html |

停止は VS Code を閉じれば十分。DB データを丸ごと消したい時だけホストで `docker compose down -v` を実行する。

---

## よく使うコマンド

devcontainer 内 / ホスト側どちらからでも（ホスト側は `docker compose exec <service>` を前に付ける）。

### Frontend

```bash
npm run dev        # Next.js dev（通常は自動起動済み）
npm run build      # プロダクションビルド
npm run lint       # ESLint
```

### Backend

```bash
# FastAPI は uvicorn --reload で常時起動中なので通常は何もしなくてOK
pytest                              # 将来テスト追加時
docker compose exec backend bash    # シェルに入る
```

### DB

```bash
# MySQL
docker compose exec mysql mysql -u captains -p$MYSQL_PASSWORD captains

# Cosmos DB
# ブラウザで http://localhost:1234/_explorer/index.html
```

### ヘルスチェック

```bash
docker compose ps                          # すべて healthy になっているか
curl http://localhost:8000/health          # backend
curl http://localhost:3000                 # frontend（HTML が返る）
```

---

## 開発フロー

1. **Issue/タスクを拾う** → Slack or Notion で宣言（ティール型のためリーダー不在・自発的に）
2. **ブランチを切る** → `feat/<短い説明>` or `fix/<短い説明>`
3. **devcontainer で開発**（HMR が効くので保存するたびに反映）
4. **動作確認** → 上記ヘルスチェックと各ページの手動確認
5. **コミット** → 小さく、1コミット1トピック
6. **PR 作成** → レビュー依頼 → マージ

---

## トラブルシューティング

### `docker compose up` でポートが既に使われている
`3000 / 8000 / 3306 / 8081 / 1234` の誰かがホストで動いていないか確認。既存プロセスを止めるか `compose.yaml` のホスト側ポート（`"3000:3000"` の左側）を変える。

### devcontainer のビルドが失敗する
- Docker Desktop のディスク残量（Settings → Resources）を確認
- `docker system prune` で未使用イメージ・ボリュームを掃除
- それでもダメなら `docker compose build --no-cache`

### Next.js の HMR が効かない
`WATCHPACK_POLLING=true` が `compose.yaml` で有効になっているか確認。Windows / WSL2 環境で inotify が届かないケース向けの fallback。

### Cosmos DB エミュレータが healthy にならない
初回起動は最大45秒かかる（`start_period: 45s` を設定済み）。それでも落ちる時はメモリ不足の可能性あり。Docker Desktop のメモリを 4GB 以上に。

### `claude login` を毎回求められる
**そうならない設計にしている**が、もし症状が出たら:
```bash
docker volume inspect captains-claude-config   # 存在確認
ls -la /home/vscode/.claude.json                # symlink になっているか
```
`.claude.json` が通常ファイルだと毎回新規扱いになる。`postCreateCommand` が失敗していないか devcontainer の起動ログを確認。

### MySQL の認証で弾かれる
`.env` の `MYSQL_PASSWORD` と `DATABASE_URL` のパスワード部分が一致しているか確認。`.env` を書き換えたら `docker compose down -v` でボリュームを消さないと初期化が走らない。

---

## チームとコミュニケーション

- **チームコントラクト**（ティール型・全員リーダー）
  - 自らタスクを取りに行く（指示待ちしない）
  - 思ったことを素直に言う
  - 辛いときは早めにヘルプを出す
  - 人格攻撃はしない、必要な指摘はする
- **定例**: 毎週水曜ホームルーム後
- **連絡**: Slack
- **ドキュメント**: [Notion: 経産省クエスト（キャプテンズ）](https://www.notion.so/31d0c2f661938020aa30df2f2b8c0795)

---

## メンバー

でらねぇ / くまぷー / よこち / けんた
