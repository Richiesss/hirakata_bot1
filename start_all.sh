#!/bin/bash
# システム全体起動スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 枚方市民ニーズ抽出システム 全体起動 ==="
echo ""

# 事前チェック: Ollama
echo "【事前チェック】"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama: 起動済み"
else
    echo "⚠️  Ollama: 起動していません"
    echo ""
    echo "【Ollamaを起動してください】"
    echo "別のターミナルで以下のコマンドを実行:"
    echo "  ollama serve"
    echo ""
    read -p "Ollamaを起動しましたか？ (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "起動を中止します"
        exit 1
    fi
    # 再確認
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✗ Ollamaに接続できません。起動を確認してください。"
        exit 1
    fi
    echo "✓ Ollama接続確認"
fi

# ngrokチェック（オプション）
echo ""
if command -v ngrok &> /dev/null; then
    if pgrep -f "ngrok.*http.*5000" > /dev/null; then
        echo "✓ ngrok: 起動済み（LINE連携準備完了）"
    else
        echo "ℹ️  ngrok: 起動していません（ローカルモードで動作）"
        echo "   LINE連携する場合は別ターミナルで: ngrok http 5000"
    fi
else
    echo "ℹ️  ngrok: インストールされていません（ローカルモードのみ）"
fi

echo ""
echo "---"
echo ""

# 既存プロセスの停止
if pgrep -f "python.*(app|admin_app)" > /dev/null; then
    echo "既存プロセスを停止中..."
    ./stop.sh
    sleep 2
fi

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "Error: 仮想環境が見つかりません。./setup.sh を実行してください。"
    exit 1
fi

source venv/bin/activate

# データベース初期化確認
if [ ! -f "hirakata_bot.db" ]; then
    echo "データベースを初期化中..."
    python -c 'from database.db_manager import init_db; init_db()'
fi

# PYTHONPATHの設定
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# LINE Bot起動（バックグラウンド）
echo "【1/2】LINE Botを起動中..."
nohup python app.py > linebot.log 2>&1 &
LINEBOT_PID=$!
sleep 3

# LINE Bot起動確認
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ LINE Bot起動成功 (PID: $LINEBOT_PID, Port: 5000)"
else
    echo "✗ LINE Bot起動失敗"
    tail -20 linebot.log
    exit 1
fi

# 管理画面起動（バックグラウンド）
echo ""
echo "【2/2】管理画面を起動中..."
nohup python admin/admin_app.py > admin.log 2>&1 &
ADMIN_PID=$!
sleep 3

# 管理画面起動確認
if curl -s -I http://localhost:8080/admin/login > /dev/null 2>&1; then
    echo "✓ 管理画面起動成功 (PID: $ADMIN_PID, Port: 8080)"
else
    echo "✗ 管理画面起動失敗"
    tail -20 admin.log
    exit 1
fi

echo ""
echo "=== 全システム起動完了 ==="
echo ""
echo "【アクセス情報】"
echo "LINE Bot:   http://localhost:5000"
echo "管理画面:   http://localhost:8080/admin/login"
echo "            ユーザー名: admin"
echo "            パスワード: admin123"
echo ""
echo "【ログファイル】"
echo "LINE Bot:   linebot.log"
echo "管理画面:   admin.log"
echo ""
echo "【停止方法】"
echo "./stop.sh"
echo ""
echo "【LINE連携する場合】"
echo "別ターミナルで: ngrok http 5000"
