#!/bin/bash
# 管理画面を長いタイムアウトで起動

cd /home/hirakata_bot1

# 既存のプロセスを停止
pkill -f "gunicorn.*admin_app"
sleep 2

# タイムアウトを300秒（5分）に設定して起動
echo "管理画面を起動中（タイムアウト: 300秒）..."
./venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 \
    --timeout 300 \
    --graceful-timeout 300 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    admin.admin_app:app &

sleep 2
echo "✓ 管理画面起動完了"
echo ""
echo "アクセス: http://localhost:8080/admin"
echo "ログ: tail -f logs/gunicorn_error.log"
