#!/bin/bash
# サーバーステータス確認スクリプト

echo "=========================================="
echo "管理画面サーバー ステータス確認"
echo "=========================================="

echo ""
echo "✓ Gunicornプロセス:"
ps aux | grep -E "python.*admin" | grep -v grep | head -3

echo ""
echo "✓ ポート8080の状態:"
netstat -tuln | grep 8080 || echo "  ポート8080はリッスンしていません"

echo ""
echo "✓ 最新のログ（最後の5行）:"
tail -5 /home/hirakata_bot1/logs/admin.log

echo ""
echo "=========================================="
echo "次のステップ:"
echo "1. ブラウザで管理画面にアクセス"
echo "   http://localhost:8080/admin/analysis"
echo ""
echo "2. 「スマート分析 (新版)」ボタンをクリック"
echo ""
echo "3. エラーが発生した場合は以下を実行:"
echo "   tail -50 /home/hirakata_bot1/logs/admin.log"
echo "=========================================="
