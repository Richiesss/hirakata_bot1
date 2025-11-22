# 枚方市民ニーズ抽出ハイブリッドシステム

LINE公式アカウントとローカルLLM（Ollama）を活用した市民ニーズ収集・分析システムです。

## 主な機能

- **AI対話型意見収集**: LLMとの対話で市民の意見・ニーズを引き出し
- **自由記述アンケート**: フォームからの意見投稿（準備中）
- **選択式アンケート**: プッシュ通知による簡単投票（準備中）
- **ポイントシステム**: 参加インセンティブとしてポイント付与
- **AI分析**: 意見の自動分類、クラスタリング、優先順位付け（準備中）
- **管理者ダッシュボード**: 収集した意見の可視化・分析（準備中）

## 技術スタック

- **バックエンド**: Python 3.9+, Flask
- **LINE Bot**: LINE Messaging API SDK v3
- **LLM**: Ollama (llama3.2)
- **データベース**: PostgreSQL
- **ORM**: SQLAlchemy

## クイックスタート

### 1. 前提条件

- Python 3.9以上
- PostgreSQL 12以上
- Ollama（RTX4090等のGPU推奨）
- LINE Developersアカウント

### 2. セットアップ

```bash
# リポジトリをクローン
cd hirakata_bot1

# セットアップスクリプトを実行
chmod +x setup.sh start.sh
./setup.sh
```

### 3. 環境変数の設定

`.env`ファイルを編集してLINE認証情報を設定:

```bash
LINE_CHANNEL_SECRET=your_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_access_token_here
DATABASE_URL=postgresql://user:password@localhost:5432/hirakata_bot
```

### 4. PostgreSQLデータベースのセットアップ

```bash
# データベース作成
createdb hirakata_bot

# テーブル初期化
source venv/bin/activate
python -c 'from database.db_manager import init_db; init_db()'
```

または、SQLファイルから直接作成:

```bash
psql -d hirakata_bot -f database/schema.sql
```

### 5. Ollamaの起動

別ターミナルで:

```bash
ollama serve
ollama pull llama3.2
```

### 6. アプリケーションの起動

```bash
./start.sh
```

### 7. Webhookの設定

ngrokで公開URL取得:

```bash
ngrok http 5000
```

LINE Developers ConsoleでWebhook URLを設定:

```
https://your-ngrok-url.ngrok-free.app/callback
```

## 使い方

### ユーザー（市民）側

1. LINE公式アカウントを友だち追加
2. メッセージを送信すると、AIが質問を返して意見を引き出します
3. 数ターンの対話後、意見が要約されてポイント付与

### コマンド

- `/help` - ヘルプ表示
- `/reset` - 対話履歴をリセット
- `/point` - 累積ポイント確認

## プロジェクト構造

```
hirakata_bot1/
├── app.py                  # メインアプリケーション
├── config.py               # 設定管理
├── ollama_client.py        # LLMクライアント
├── requirements.txt        # 依存パッケージ
├── setup.sh               # セットアップスクリプト
├── start.sh               # 起動スクリプト
├── database/
│   ├── schema.sql         # データベーススキーマ
│   ├── db_manager.py      # ORM定義・DB操作
│   └── __init__.py
├── handlers/
│   ├── message_handler.py # メッセージ処理
│   ├── command_handler.py # コマンド処理
│   ├── follow_handler.py  # 友だち追加処理
│   ├── postback_handler.py# ポストバック処理
│   └── __init__.py
├── features/
│   ├── chat_opinion.py    # 対話型意見収集
│   └── __init__.py
├── ai/                    # AI分析（準備中）
├── admin/                 # 管理画面（準備中）
├── security/              # セキュリティ（準備中）
├── scripts/               # 運用スクリプト
└── tests/                 # テストコード
```

## 現在の実装状況（v1.0基本実装）

✅ **完了**
- データベース設計・ORM実装
- LINE Bot基盤（Webhook、イベントルーティング）
- Ollama統合（対話・要約・分類モード）
- 対話型意見収集機能（UC-001～UC-005）
- ユーザー登録・ポイント管理
- コマンド機能（/help, /reset, /point）

🚧 **準備中**
- 自由記述アンケート
- 選択式アンケート
- AI分析機能（分類、クラスタリング）
- 管理者ダッシュボード
- セキュリティ強化（ハッシュ化、レート制限）

## カスタマイズ

`config.py`でシステムプロンプトや各種設定を変更できます:

- `SYSTEM_PROMPT_CHAT`: 対話モードのプロンプト
- `SYSTEM_PROMPT_SUMMARY`: 要約モードのプロンプト
- `MAX_CHAT_TURNS`: 対話の最大ターン数
- `POINT_CHAT_OPINION`: 対話完了時のポイント

## トラブルシューティング

### Ollamaに接続できない

```bash
# Ollamaサービスが起動しているか確認
curl http://localhost:11434/api/tags

# モデルがダウンロードされているか確認
ollama list
```

### データベース接続エラー

```bash
# PostgreSQLが起動しているか確認
pg_isready

# データベースが存在するか確認
psql -l | grep hirakata_bot
```

## ライセンス

MIT License

## お問い合わせ

枚方市デジタル推進課

---

**注意**: 本システムは要件定義書に基づき段階的に開発中です。現在は基本機能（対話型意見収集）のみ実装されています。
