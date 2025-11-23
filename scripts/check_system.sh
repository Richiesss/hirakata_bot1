#!/bin/bash
# 動作確認スクリプト

echo "=== 枚方市民ニーズ抽出システム 動作確認 ==="
echo ""

# 仮想環境の有効化
source venv/bin/activate

echo "【1. 環境確認】"
echo "Python: $(python --version)"
echo "データベース: $(ls -lh hirakata_bot.db 2>/dev/null | awk '{print $9, $5}' || echo 'Not found')"
echo ""

echo "【2. サービス起動状況】"
echo "LINE Bot (port 5000): $(curl -s http://localhost:5000/ 2>/dev/null | grep -q status && echo '✓ 稼働中' || echo '✗ 停止中')"
echo "管理画面 (port 8080): $(curl -s http://localhost:8080/admin/login 2>/dev/null | grep -q title && echo '✓ 稼働中' || echo '✗ 停止中')"
echo ""

echo "【3. データベース確認】"
PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python << 'EOF'
from database.db_manager import get_db, User, Opinion, ChatSession

with get_db() as db:
    users = db.query(User).count()
    opinions = db.query(Opinion).count()
    sessions = db.query(ChatSession).count()
    print(f"ユーザー数: {users}")
    print(f"意見数: {opinions}")
    print(f"セッション数: {sessions}")
EOF

echo ""
echo "【4. Ollama確認】"
curl -s http://localhost:11434/api/tags | python -m json.tool 2>/dev/null | grep -q name && echo "✓ Ollama稼働中" || echo "✗ Ollama停止中"

echo ""
echo "=== 確認完了 ==="
echo ""
echo "【起動コマンド】"
echo "LINE Bot起動: ./start.sh"
echo "管理画面起動: PYTHONPATH=/root/workspace/hirakata_bot1:$PYTHONPATH python admin/admin_app.py"
