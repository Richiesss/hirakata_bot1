# 枚方市民ニーズ抽出ハイブリッドシステム 実装計画

## 概要

本システムは、LINE公式アカウントとローカルLLM（Ollama）を活用し、枚方市民の意見・ニーズを継続的かつ網羅的に収集・分析する統合システムです。

参照リポジトリ `hirakata_bot` をベースに、以下の主要機能を実装します:

- **3つの意見収集方法**: AI対話型、自由記述フォーム、選択式アンケート
- **ローカルLLMによるAI分析**: 意見の自動分類、クラスタリング、優先順位付け
- **管理者ダッシュボード**: 収集した意見の可視化・分析・レポート出力
- **ポイントシステム**: 市民の参加意欲を高めるインセンティブ機能

## ユーザーレビュー必須事項

> [!IMPORTANT]
> **データベース選択について**
> 要件定義では「PostgreSQL / MongoDB」と記載がありますが、実装計画では以下の理由により**PostgreSQL単独**を推奨します:
> - USERS, OPINIONS等のリレーショナルデータ構造に適している
> - トランザクション管理が容易
> - AI分類結果（JSON形式）もPostgreSQLのJSONB型で十分対応可能
> - 運用・保守の複雑度を低減
> 
> MongoDBの採用が必須の場合は、以下の構成を検討します:
> - PostgreSQL: ユーザー情報、ポイント管理、投票結果
> - MongoDB: 意見テキスト、対話履歴、AI分析結果
> 
> **ご希望の構成をお知らせください。**

> [!WARNING]
> **Ollamaハードウェア要件**
> 要件定義のハードウェアスペック（NVIDIA RTX 3090/4090、VRAM 24GB、RAM 64GB）は、実環境での動作を前提としています。
> - 開発環境で同等のスペックがない場合、応答時間3秒以内の達成が困難な可能性があります
> - GPU非搭載環境での開発の場合、CPU推論となり応答時間が10-30秒程度になります
> - 開発環境のハードウェアスペックを事前に確認させてください

## 提案する変更内容

本実装計画では、システムを複数のコンポーネントに分割し、段階的に構築します。

---

### コンポーネント1: データベース層

データモデルとスキーマの設計・実装

#### [NEW] [schema.sql](file:///root/workspace/hirakata_bot1/database/schema.sql)

PostgreSQLスキーマ定義ファイル。以下のテーブルを作成:

- `users`: ユーザー情報（LINE IDハッシュ、年代、地区、累積ポイント）
- `opinions`: 意見データ（内容、ソース種別、AI分類結果、感情スコア）
- `chat_sessions`: 対話セッション管理
- `chat_messages`: 対話メッセージ履歴
- `polls`: 選択式アンケート定義
- `poll_options`: アンケート選択肢
- `poll_responses`: アンケート回答結果
- `points_history`: ポイント付与履歴
- `admin_users`: 管理者アカウント

#### [NEW] [database/db_manager.py](file:///root/workspace/hirakata_bot1/database/db_manager.py)

データベース接続・操作を管理するモジュール:
- SQLAlchemyを使用したORM実装
- コネクションプーリング
- トランザクション管理
- 各テーブルに対するCRUD操作

---

### コンポーネント2: LINE Bot基盤

参照リポジトリの構造を踏襲し、拡張機能を追加

#### [NEW] [app.py](file:///root/workspace/hirakata_bot1/app.py)

Flaskメインアプリケーション:
- Webhook受信エンドポイント (`/callback`)
- ヘルスチェックエンドポイント (`/`)
- メッセージタイプ別ルーティング（テキスト、ポストバック、フォロー等）
- リッチメニュー設定API連携

#### [NEW] [config.py](file:///root/workspace/hirakata_bot1/config.py)

設定管理:
- 環境変数の読み込み（LINE認証情報、Ollama設定、DB接続情報）
- システムプロンプト定義（対話フェーズ用、要約フェーズ用）
- 各種定数（ポイント付与額、応答タイムアウト等）

#### [NEW] [handlers/](file:///root/workspace/hirakata_bot1/handlers/)

メッセージハンドラー群:
- `message_handler.py`: テキストメッセージ処理
- `postback_handler.py`: ポストバックイベント処理（ボタンタップ等）
- `follow_handler.py`: 友だち追加時の初回登録処理
- `command_handler.py`: コマンド処理（/help, /reset, /point等）

---

### コンポーネント3: AI/LLM統合

Ollamaを使用したLLM推論と意見分析

#### [MODIFY] [ollama_client.py](file:///root/workspace/hirakata_bot1/ollama_client.py)

参照リポジトリのファイルを拡張:
- **対話モード**: temperature=0.7、傾聴・深掘りプロンプト
- **要約モード**: temperature=0.0、JSON形式での構造化出力
- **分類モード**: カテゴリ自動分類
- 並列処理対応（リクエストキュー実装）
- タイムアウト・リトライ処理

#### [NEW] [ai/analyzer.py](file:///root/workspace/hirakata_bot1/ai/analyzer.py)

AI分析機能:
- 意見の自動カテゴリ分類（AD-002）
- クラスタリング（AD-003）: TF-IDF + K-Meansまたは類似度ベース
- 優先順位スコアリング（AD-004）: 感情強度、重複度、時系列トレンド

#### [NEW] [ai/prompts.py](file:///root/workspace/hirakata_bot1/ai/prompts.py)

プロンプトテンプレート集:
- 対話フェーズプロンプト（市民の困りごとを引き出す質問生成）
- 要約フェーズプロンプト（対話ログからJSON形式で抽出）
- 分類プロンプト（カテゴリ、感情スコア付与）

---

### コンポーネント4: 市民向け機能

3つの意見収集方法を実装

#### [NEW] [features/chat_opinion.py](file:///root/workspace/hirakata_bot1/features/chat_opinion.py)

対話型意見収集（UC-001～UC-005）:
- セッション管理（対話開始、継続、終了判定）
- Ollamaによる質問生成
- 対話終了時の要約生成
- ポイント付与処理

#### [NEW] [features/free_form.py](file:///root/workspace/hirakata_bot1/features/free_form.py)

自由記述アンケート（UC-006～UC-010）:
- LINE Flex Messageでフォーム表示
- カテゴリ選択UI（Quick Reply使用）
- 入力内容の確認・送信
- ポイント付与処理

#### [NEW] [features/poll.py](file:///root/workspace/hirakata_bot1/features/poll.py)

選択式アンケート（UC-011～UC-014）:
- プッシュ通知配信
- 4択表示（上位3意見 + 該当なし）
- ワンタップ投票処理
- ポイント付与処理

#### [NEW] [features/user_utils.py](file:///root/workspace/hirakata_bot1/features/user_utils.py)

ユーティリティ機能（UC-015～UC-019）:
- ユーザー登録・プロフィール管理
- ポイント確認
- 履歴参照
- 通知設定
- 履歴リセット

---

### コンポーネント5: 管理者ダッシュボード

Webベースの管理画面

#### [NEW] [admin/](file:///root/workspace/hirakata_bot1/admin/)

Flask-Adminまたは独自実装の管理画面:
- `admin_app.py`: 管理画面用Flaskアプリ（別ポート起動）
- `auth.py`: 認証・セッション管理（多要素認証対応）
- `templates/`: HTML テンプレート（Jinja2）
  - `dashboard.html`: ダッシュボード（AD-006）
  - `opinions.html`: 意見一覧・フィルタリング
  - `analysis.html`: AI分析結果表示
  - `reports.html`: レポート生成画面
  - `poll_create.html`: アンケート作成画面
- `static/`: CSS/JS（Chart.js等）

#### [NEW] [admin/routes/](file:///root/workspace/hirakata_bot1/admin/routes/)

管理画面ルーティング:
- `dashboard.py`: ダッシュボード表示（AD-001, AD-006）
- `analysis.py`: AI分析結果表示（AD-002～AD-005）
- `export.py`: CSV/PDF/Excel出力（AD-007, AD-008）
- `poll_management.py`: アンケート配信管理（AD-009）
- `point_management.py`: ポイント管理（AD-010）

---

### コンポーネント6: インフラ・セキュリティ

#### [NEW] [docker-compose.yml](file:///root/workspace/hirakata_bot1/docker-compose.yml)

コンテナ構成:
- `linebot`: Flask LINE Botアプリ
- `admin`: 管理画面アプリ
- `postgres`: PostgreSQLデータベース
- `ollama`: Ollama LLMサービス（GPU対応）
- `nginx`: リバースプロキシ（HTTPS終端）

#### [NEW] [.env.sample](file:///root/workspace/hirakata_bot1/.env.sample)

環境変数テンプレート:
```
# LINE Bot
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=

# Ollama
OLLAMA_MODEL=llama3.2
OLLAMA_URL=http://ollama:11434
OLLAMA_NUM_PARALLEL=4

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/hirakata_bot

# Admin
ADMIN_USERNAME=
ADMIN_PASSWORD=
SECRET_KEY=

# セキュリティ
LINE_ID_SALT=  # ハッシュ化用ソルト
```

#### [NEW] [security/](file:///root/workspace/hirakata_bot1/security/)

セキュリティ機能:
- `hash_utils.py`: LINE IDハッシュ化処理
- `content_filter.py`: 誹謗中傷検出（NGワードフィルタ）
- `rate_limiter.py`: レート制限（DoS対策）

---

### コンポーネント7: ユーティリティ・テスト

#### [NEW] [requirements.txt](file:///root/workspace/hirakata_bot1/requirements.txt)

依存パッケージ:
```
# LINE Bot SDK
line-bot-sdk==3.6.0

# Web Framework
Flask==3.0.0
Flask-Admin==1.6.0

# Database
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9

# AI/ML
ollama==0.1.6
scikit-learn==1.3.2
numpy==1.26.2

# PDF/Excel出力
reportlab==4.0.7
openpyxl==3.1.2

# セキュリティ
bcrypt==4.1.2
PyJWT==2.8.0

# その他
python-dotenv==1.0.0
requests==2.31.0
```

#### [NEW] [tests/](file:///root/workspace/hirakata_bot1/tests/)

テストコード:
- `test_ollama_client.py`: LLM推論のテスト
- `test_chat_opinion.py`: 対話機能のテスト
- `test_db_manager.py`: データベース操作のテスト
- `test_analyzer.py`: AI分析機能のテスト

#### [NEW] [scripts/](file:///root/workspace/hirakata_bot1/scripts/)

運用スクリプト:
- `setup.sh`: 初期セットアップスクリプト
- `start.sh`: アプリケーション起動スクリプト
- `migrate_db.sh`: データベースマイグレーション
- `backup_db.sh`: バックアップスクリプト

---

## 検証計画

### 自動テスト

実装後、以下のテストを実行します:

#### 1. 単体テスト

```bash
# テスト環境のセットアップ
cd /root/workspace/hirakata_bot1
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov

# 全テスト実行
pytest tests/ -v --cov=. --cov-report=term-missing
```

期待結果: 全テストがパスし、カバレッジ70%以上

#### 2. データベーステスト

```bash
# テスト用DBの初期化
export DATABASE_URL="postgresql://test:test@localhost:5432/test_hirakata_bot"
python scripts/migrate_db.py

# データベーステスト実行
pytest tests/test_db_manager.py -v
```

期待結果: CRUD操作、トランザクション処理が正常に動作

#### 3. Ollama統合テスト

```bash
# Ollamaサービス起動
ollama serve &
ollama pull llama3.2

# LLMテスト実行
pytest tests/test_ollama_client.py -v
```

期待結果: 
- 対話モードが温度0.7で応答生成
- 要約モードがJSON形式で構造化出力
- 応答時間が5秒以内（開発環境では緩和）

#### 4. LINE Bot統合テスト

```bash
# テストサーバー起動
export FLASK_ENV=testing
python app.py &

# Webhookテスト（モックイベント送信）
curl -X POST http://localhost:5000/callback \
  -H "X-Line-Signature: test_signature" \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/text_message_event.json
```

期待結果: Webhookが正常に受信され、適切なレスポンスが返る

### 手動検証

以下の機能は、ユーザーによる手動検証をお願いします:

#### 1. LINE Bot動作確認

**前提条件**:
- LINE Developers Consoleでチャネル作成済み
- `.env`ファイルに認証情報を設定済み
- ngrokまたは公開URLが利用可能

**手順**:
1. システム起動
   ```bash
   cd /root/workspace/hirakata_bot1
   docker-compose up -d
   ```
2. ngrokで公開URL取得
   ```bash
   ngrok http 5000
   ```
3. LINE Developers ConsoleでWebhook URL設定
4. LINE公式アカウントを友だち追加
5. 以下の操作を実施:
   - [ ] メッセージ送信 → AI応答が返る
   - [ ] リッチメニュー「対話で意見」をタップ → 対話開始
   - [ ] 対話を3ターン継続 → 要約メッセージ受信
   - [ ] リッチメニュー「アンケート」をタップ → 自由記述フォーム表示
   - [ ] フォーム送信 → 「ポイント付与完了」メッセージ受信
   - [ ] `/point`コマンド送信 → 累積ポイント表示

**期待結果**: すべての操作が正常に完了し、データベースに保存される

#### 2. 管理者ダッシュボード確認

**手順**:
1. 管理画面にアクセス: `http://localhost:8080/admin`
2. ログイン（`.env`に設定した認証情報）
3. 以下の画面を確認:
   - [ ] ダッシュボード: 意見件数、カテゴリ分布グラフ表示
   - [ ] 意見一覧: テーブル表示、フィルタリング機能
   - [ ] AI分析: クラスタリング結果、トレンドグラフ
   - [ ] CSV出力: ダウンロードボタンクリック → CSVファイル取得

**期待結果**: すべての画面が正常に表示され、データ参照・出力が可能

#### 3. 性能確認（開発環境）

**手順**:
1. 負荷テストツールで同時リクエスト送信
   ```bash
   # Apache Benchを使用
   ab -n 100 -c 10 http://localhost:5000/
   ```
2. Ollama応答時間の測定
   ```bash
   time curl -X POST http://localhost:11434/api/generate \
     -d '{"model":"llama3.2","prompt":"こんにちは"}'
   ```

**期待結果**: 
- ヘルスチェックエンドポイントは100req/secを処理可能
- Ollama応答時間は10秒以内（開発環境、本番では3秒以内を目標）

---

## 実装スケジュール（推定）

| フェーズ | 所要時間 | 備考 |
|---------|---------|------|
| データベース設計・実装 | 2-3時間 | スキーマ定義、ORM実装 |
| LINE Bot基盤構築 | 3-4時間 | 参照リポジトリベースで拡張 |
| Ollama統合 | 2-3時間 | プロンプト調整含む |
| 市民向け機能（対話） | 4-5時間 | セッション管理が複雑 |
| 市民向け機能（アンケート） | 3-4時間 | フォームUI実装 |
| 管理者ダッシュボード | 5-6時間 | 認証、グラフ表示、エクスポート |
| AI分析機能 | 3-4時間 | クラスタリング、スコアリング |
| セキュリティ・非機能 | 2-3時間 | ハッシュ化、レート制限 |
| テスト・検証 | 3-4時間 | 単体テスト、統合テスト |
| **合計** | **27-36時間** | 段階的実装を推奨 |

---

## 既知の制約・トレードオフ

1. **GPU環境の依存**: Ollamaの性能は実行環境のGPUスペックに大きく依存します
2. **LINE APIレート制限**: プッシュ通知は月間1000通までの制限があります（有料プランで拡張可能）
3. **開発環境での制限**: 応答時間3秒以内の達成には本番相当のハードウェアが必要です
4. **画像・音声対応**: 将来拡張機能として、現フェーズでは未実装です

---

## 次のステップ

1. 本実装計画のレビュー・承認
2. データベース選択の確認（PostgreSQL単独 or PostgreSQL+MongoDB）
3. 開発環境のハードウェアスペック確認
4. 実装開始（フェーズ1: データベース層から）
