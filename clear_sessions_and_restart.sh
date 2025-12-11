#!/bin/bash
# セッションをクリアして再起動

echo "=========================================="
echo "セッションクリア＆サーバー再起動"
echo "=========================================="

echo ""
echo "1. Flaskセッションディレクトリをクリア..."
rm -rf /home/hirakata_bot1/admin/flask_session/*
echo "   ✓ 完了"

echo ""
echo "2. 一時ファイルをクリア..."
rm -f /home/hirakata_bot1/admin/static/tmp/analysis_*.png
echo "   ✓ 完了"

echo ""
echo "3. Gunicornをリロード..."
pkill -HUP -f "gunicorn.*admin_app"
sleep 2
echo "   ✓ 完了"

echo ""
echo "=========================================="
echo "✅ セッションクリア＆再起動完了"
echo ""
echo "次のステップ:"
echo "1. ブラウザでハードリフレッシュ (Ctrl+Shift+R または Cmd+Shift+R)"
echo "2. 管理画面にアクセス: http://localhost:8080/admin/analysis"
echo "3. 「スマート分析 (新版)」を実行"
echo "=========================================="
