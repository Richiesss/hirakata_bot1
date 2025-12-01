FROM python:3.10-slim

# システム依存関係のインストール
# fonts-noto-cjk: matplotlibの日本語表示用
# curl: ヘルスチェック用
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルのコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# 実行権限の付与
RUN chmod +x start_prod.sh stop.sh

# ポート公開
EXPOSE 5000 8080

# 環境変数のデフォルト値（docker-composeで上書き可能）
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 起動コマンド
# start_prod.shは仮想環境(venv)を使う前提になっているため、
# コンテナ内では直接python/gunicornを呼ぶように修正が必要だが、
# ここでは簡易的にstart_prod.shを修正せずに、直接コマンドを指定する
CMD ["/bin/bash", "-c", "gunicorn -c gunicorn_config.py app:app & gunicorn -w 2 -b 0.0.0.0:8080 admin.admin_app:app"]
