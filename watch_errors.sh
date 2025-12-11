#!/bin/bash
# リアルタイムでエラーを監視

echo "=========================================="
echo "エラーログをリアルタイムで監視中..."
echo "（Ctrl+Cで終了）"
echo "=========================================="
echo ""

tail -f /home/hirakata_bot1/logs/admin.log | grep --line-buffered -E "ERROR|Traceback|Exception|KeyError" --color=always
