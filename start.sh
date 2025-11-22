#!/bin/bash
# アプリケーション起動スクリプト

# 仮想環境の有効化
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: 仮想環境が見つかりません。./setup.sh を実行してください。"
    exit 1
fi

# 環境変数のチェック
if [ ! -f ".env" ]; then
    echo "Error: .envファイルが見つかりません。"
    exit 1
fi

echo "=== 枚方市民ニーズ抽出システム 起動 ==="

# Flaskアプリケーション起動
python app.py
