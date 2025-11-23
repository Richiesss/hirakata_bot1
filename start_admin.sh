#!/bin/bash
# 管理画面 起動スクリプト

set -e  # エラー時に停止

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 管理画面 起動 ==="

# 仮想環境の確認と有効化
if [ ! -d "venv" ]; then
    echo "Error: 仮想環境が見つかりません。./setup.sh を実行してください。"
    exit 1
fi

source venv/bin/activate

# 環境変数の確認
if [ ! -f ".env" ]; then
    echo "Error: .envファイルが見つかりません。"
    exit 1
fi

# データベース初期化確認
if [ ! -f "hirakata_bot.db" ]; then
    echo "データベースを初期化中..."
    python -c 'from database.db_manager import init_db; init_db()'
fi

# 既存プロセスの確認と停止
if pgrep -f "python.*admin_app.py" > /dev/null; then
    echo "既存の管理画面プロセスを停止中..."
    pkill -f "python.*admin_app.py" || true
    sleep 2
fi

# 管理画面起動
echo "管理画面を起動中..."
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
python admin/admin_app.py

echo "管理画面起動完了"
