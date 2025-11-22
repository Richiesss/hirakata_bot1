#!/bin/bash
# セットアップスクリプト

set -e

echo "=== 枚方市民ニーズ抽出システム セットアップ ==="

# Python仮想環境の作成
echo "1. Python仮想環境を作成中..."
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# 依存パッケージのインストール
echo "2. 依存パッケージをインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

# 環境変数ファイルの作成
if [ ! -f .env ]; then
    echo "3. .envファイルを作成中..."
    cp .env.sample .env
    echo "   ⚠️  .envファイルを編集してLINE認証情報を設定してください"
else
    echo "3. .envファイルは既に存在します"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "1. .envファイルを編集してLINE認証情報を設定"
echo "2. PostgreSQLデータベースをセットアップ"
echo "3. Ollamaをインストール・起動"
echo "   $ ollama serve"
echo "   $ ollama pull llama3.2"
echo "4. データベースを初期化"
echo "   $ source venv/bin/activate"
echo "   $ python -c 'from database.db_manager import init_db; init_db()'"
echo "5. アプリケーションを起動"
echo "   $ ./start.sh"
