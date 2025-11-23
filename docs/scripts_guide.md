# 起動スクリプト利用ガイド

## 概要

枚方市民ニーズ抽出システムの起動・停止を簡単に行うためのスクリプト集です。

## スクリプト一覧

### 1. start_all.sh（推奨）
**システム全体を一括起動**

```bash
./start_all.sh
```

**機能:**
- 既存プロセスの自動停止
- LINE Botの起動（ポート5000）
- 管理画面の起動（ポート8080）
- 起動確認とエラー検出
- ログファイル出力（linebot.log、admin.log）

**起動確認メッセージ:**
```
✓ LINE Bot起動成功 (PID: xxxxx, Port: 5000)
✓ 管理画面起動成功 (PID: xxxxx, Port: 8080)
```

---

### 2. start.sh
**LINE Botのみ起動**

```bash
./start.sh
```

**注意:** フォアグラウンドで起動（Ctrl+Cで停止）

---

### 3. start_admin.sh
**管理画面のみ起動**

```bash
./start_admin.sh
```

**注意:** フォアグラウンドで起動（Ctrl+Cで停止）

---

### 4. stop.sh
**システム全体を停止**

```bash
./stop.sh
```

**機能:**
- LINE Botの停止
- 管理画面の停止
- プロセス残留確認と強制終了

---

### 5. setup.sh
**初回セットアップ**

```bash
./setup.sh
```

**機能:**
- Python仮想環境作成
- 依存パッケージインストール
- .envファイル生成

---

## 利用フロー

### 初回セットアップ

```bash
# 1. セットアップ実行
./setup.sh

# 2. .envファイルを編集（必要に応じて）
nano .env

# 3. データベース初期化
source venv/bin/activate
python -c 'from database.db_manager import init_db; init_db()'

# 4. テストデータ作成（オプション）
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python scripts/create_test_data.py
```

### 日常的な起動・停止

```bash
# 起動
./start_all.sh

# 停止
./stop.sh
```

### 個別サービスの起動

```bash
# LINE Botのみ起動
./start.sh &

# 管理画面のみ起動
./start_admin.sh &
```

---

## トラブルシューティング

### 起動失敗時

```bash
# ログを確認
tail -50 linebot.log
tail -50 admin.log

# プロセスを強制停止
./stop.sh

# 再起動
./start_all.sh
```

### ポート使用中エラー

```bash
# ポート5000を使用しているプロセスを確認
lsof -i:5000

# ポート8080を使用しているプロセスを確認
lsof -i:8080

# 手動でプロセス停止
pkill -f "python.*app.py"
pkill -f "python.*admin_app.py"
```

### データベースエラー

```bash
# データベース再初期化
source venv/bin/activate
rm hirakata_bot.db
python -c 'from database.db_manager import init_db; init_db()'
```

---

## ログファイル

システム起動後、以下のログファイルが生成されます：

- `linebot.log`: LINE Botのログ
- `admin.log`: 管理画面のログ

**ログの確認:**
```bash
# リアルタイムでログを監視
tail -f linebot.log
tail -f admin.log

# 最新50行を表示
tail -50 linebot.log
```

---

## 環境変数

起動スクリプトは自動的に以下の環境変数を設定します：

- `PYTHONPATH`: プロジェクトルートディレクトリ

その他の環境変数は`.env`ファイルで管理されます。

---

## スクリプトの特徴

### エラーハンドリング
- 仮想環境が存在しない場合はエラーメッセージを表示
- .envファイルが存在しない場合はエラーメッセージを表示
- データベースが存在しない場合は自動初期化
- 起動失敗時はログを表示してエラー終了

### プロセス管理
- 既存プロセスの自動検出と停止
- PIDの記録と表示
- 起動確認（ヘルスチェック）

### ログ管理
- 標準出力・標準エラーをログファイルに記録
- nohupでバックグラウンド実行

---

## まとめ

**推奨される使い方:**

1. **初回**: `./setup.sh` → `.env`編集 → `./start_all.sh`
2. **日常**: `./start_all.sh` で起動、`./stop.sh` で停止
3. **トラブル**: ログ確認 → `./stop.sh` → `./start_all.sh`

**アクセス:**
- LINE Bot: http://localhost:5000
- 管理画面: http://localhost:8080/admin/login （admin / admin123）
