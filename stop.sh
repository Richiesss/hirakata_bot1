#!/bin/bash
# システム停止スクリプト

echo "=== システム停止 ==="

# Gunicornプロセスの停止
if pgrep -f "gunicorn" > /dev/null; then
    echo "Gunicornプロセスを停止中..."
    pkill -f "gunicorn" || true
else
    echo "Gunicornプロセスは起動していません"
fi

# LINE Botの停止 (Legacy)
if pgrep -f "python.*app.py" > /dev/null; then
    echo "LINE Bot(Dev)を停止中..."
    pkill -f "python.*app.py" || true
fi

# 管理画面の停止 (Legacy)
if pgrep -f "python.*admin_app.py" > /dev/null; then
    echo "管理画面(Dev)を停止中..."
    pkill -f "python.*admin_app.py" || true
fi

sleep 2

# 停止確認
if pgrep -f "python.*(app|admin_app)" > /dev/null; then
    echo "⚠️  一部プロセスが残っています。強制終了します..."
    pkill -9 -f "python.*(app|admin_app)" || true
    sleep 1
fi

echo "✓ システム停止完了"
