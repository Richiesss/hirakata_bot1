#!/bin/bash
# 現在のリクエストの状態をデバッグ

echo "=========================================="
echo "現在のリクエスト状態を確認"
echo "=========================================="

echo ""
echo "1. 最新の10行のログ:"
tail -10 /home/hirakata_bot1/logs/admin.log

echo ""
echo "2. エラーがある場合（最新5件）:"
grep -E "ERROR|Traceback|Exception" /home/hirakata_bot1/logs/admin.log | tail -5

echo ""
echo "3. 分析完了の確認（最新5件）:"
grep "Analysis completed" /home/hirakata_bot1/logs/admin.log | tail -5

echo ""
echo "4. フラッシュメッセージの確認（最新5件）:"
grep "flash" /home/hirakata_bot1/logs/admin.log | tail -5

echo ""
echo "=========================================="
echo "【重要】ブラウザで以下を確認してください:"
echo "1. ブラウザのコンソール（F12 → Console）にエラーがないか"
echo "2. ネットワークタブ（F12 → Network）で500エラーの詳細"
echo "3. ページに「スマート分析が完了しました」と表示されているか"
echo "=========================================="
