# 枚方市民ニーズ抽出ハイブリッドシステム

LINE公式アカウントとローカルLLM（Ollama）を活用した市民ニーズ収集・分析システムです。
市民との対話を通じて意見を収集し、AIによる分析・可視化を行うことで、市政への反映を支援します。

## 主な機能

### 📱 市民向け機能 (LINE Bot)
- **AI対話型意見収集**: LLMとの自然な対話で市民の意見・ニーズを深掘り
- **自由記述アンケート**: メニューからの手軽な意見投稿
- **選択式アンケート**: プッシュ通知による投票機能
- **ポイントシステム**: 参加インセンティブとしてポイント付与
- **ユーザー登録**: 年代、居住区などの属性登録

### 💻 管理者向け機能 (Webダッシュボード)
- **ダッシュボード**: 収集した意見の統計、日別推移、カテゴリ分布の可視化
- **意見管理**: 意見の検索、フィルタリング、優先度・感情スコアの確認
- **AI分析**:
    - **クラスタリング**: 類似意見のグループ化と要約
    - **レポート出力**: 分析結果や運用状況のPDFレポート生成
- **アンケート管理**: 新規投票の作成、配信、結果確認
- **ユーザー管理**: 登録ユーザー一覧、ポイント付与
- **レスポンシブ対応**: スマホ・タブレットでの閲覧に対応

## 技術スタック

- **バックエンド**: Python 3.10+, Flask
- **LINE Bot**: LINE Messaging API SDK v3
- **LLM**: Ollama (llama3.2)
- **データベース**: PostgreSQL (本番) / SQLite (開発)
- **ORM**: SQLAlchemy
- **コンテナ**: Docker, Docker Compose
- **サーバー**: Gunicorn, Nginx (想定)
- **PDF生成**: ReportLab

## クイックスタート (Docker推奨)

### 1. 前提条件
- Docker & Docker Compose
- LINE Developersアカウント (Channel Secret, Access Token)

### 2. セットアップ
`.env.production` ファイルを作成し、必要な環境変数を設定します。

```bash
LINE_CHANNEL_SECRET=your_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_access_token
DATABASE_URL=postgresql://user:password@db:5432/hirakata_bot
ADMIN_PASSWORD=admin123
```

### 3. 起動

```bash
docker-compose up -d --build
```

### 4. アクセス
- **LINE Bot**: LINEアプリから友だち追加して利用
- **管理画面**: `http://localhost:8081/admin/login`
    - 初期アカウント: `admin` / `admin123`

## プロジェクト構造

```
hirakata_bot1/
├── app.py                  # LINE Bot アプリケーション
├── admin/                  # 管理画面アプリケーション
│   ├── admin_app.py        # 管理画面バックエンド
│   ├── templates/          # HTMLテンプレート
│   └── static/             # CSS, JS, フォント
├── ai/                     # AI分析モジュール
│   ├── analyzer.py         # 分析ロジック
│   └── sentiment.py        # 感情分析
├── database/               # データベース関連
│   ├── models.py           # データモデル
│   └── db_manager.py       # DB操作
├── handlers/               # LINE Bot ハンドラー
├── scripts/                # 運用・セットアップスクリプト
│   ├── reset_db.py         # DB初期化
│   ├── seed_admin.py       # 管理者作成
│   └── backup_db.sh        # バックアップ
├── docker-compose.yml      # コンテナ構成
└── requirements.txt        # 依存パッケージ
```

## 現在の実装状況

✅ **実装完了**
- LINE Bot 基本機能 (対話、登録、ポイント)
- 管理画面 (ダッシュボード、意見一覧、ユーザー管理)
- アンケート機能 (作成、配信、集計)
- AI分析機能 (クラスタリング、要約)
- PDFレポート出力 (分析レポート、運用レポート)
- レスポンシブデザイン
- Docker環境構築

## 運用・保守

### バックアップ
```bash
./scripts/backup_db.sh
```

### データベースリセット (注意: データが消えます)
```bash
python scripts/reset_db.py
python scripts/seed_admin.py
```

## ライセンス
MIT License

## お問い合わせ
大阪工業大学 情報科学部 データサイエンス学科 分散情報処理研究室
