#!/bin/bash
# システム停止スクリプト

echo "=== システム停止 ==="

# LINE Botの停止
if pgrep -f "python.*app.py" > /dev/null; then
    echo "LINE Botを停止中..."
    pkill -f "python.*app.py" || true
else
    echo "LINE Botは起動していません"
fi

# 管理画面の停止
if pgrep -f "python.*admin_app.py" > /dev/null; then
    echo "管理画面を停止中..."
    pkill -f "python.*admin_app.py" || true
else
    echo "管理画面は起動していません"
fi

sleep 2

# 停止確認
if pgrep -f "python.*(app|admin_app)" > /dev/null; then
    echo "⚠️  一部プロセスが残っています。強制終了します..."
    pkill -9 -f "python.*(app|admin_app)" || true
    sleep 1
fi

echo "✓ システム停止完了"
