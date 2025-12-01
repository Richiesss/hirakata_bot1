#!/bin/bash

# ディレクトリ移動
cd "$(dirname "$0")"

# 仮想環境のパス
VENV_PYTHON="./venv/bin/python"
VENV_GUNICORN="./venv/bin/gunicorn"

echo "=== 本番環境起動スクリプト ==="

# ログディレクトリ作成
mkdir -p logs

# 既存プロセス停止
./stop.sh

echo "データベース初期化..."
$VENV_PYTHON -c "from database.db_manager import init_db; init_db()"

echo "【1/2】LINE Botを起動中 (Gunicorn)..."
nohup $VENV_GUNICORN -c gunicorn_config.py app:app > logs/gunicorn_app.log 2>&1 &
PID_APP=$!
echo "✓ LINE Bot起動 (PID: $PID_APP)"

echo "【2/2】管理画面を起動中 (Gunicorn)..."
# 管理画面はポート8080で起動
nohup $VENV_GUNICORN -w 2 -b 0.0.0.0:8080 admin.admin_app:app > logs/gunicorn_admin.log 2>&1 &
PID_ADMIN=$!
echo "✓ 管理画面起動 (PID: $PID_ADMIN)"

echo "=== 起動完了 ==="
echo "LINE Bot: http://localhost:5000"
echo "管理画面: http://localhost:8080/admin/login"
