"""システム設定ファイル"""

import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# LINE Bot設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

# Ollama設定
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_NUM_PARALLEL = int(os.getenv("OLLAMA_NUM_PARALLEL", "4"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))  # 秒

# データベース設定
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hirakata:hirakata@localhost:5432/hirakata_bot")

# Flask設定
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# セキュリティ設定
LINE_ID_SALT = os.getenv("LINE_ID_SALT", "default_salt_please_change")
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_please_change")

# ポイント設定
POINT_CHAT_OPINION = int(os.getenv("POINT_CHAT_OPINION", "10"))
POINT_FREE_FORM = int(os.getenv("POINT_FREE_FORM", "5"))
POINT_POLL_RESPONSE = int(os.getenv("POINT_POLL_RESPONSE", "3"))

# チャット対話設定
MAX_CHAT_TURNS = int(os.getenv("MAX_CHAT_TURNS", "5"))  # 最大対話ターン数
CHAT_SESSION_TIMEOUT = int(os.getenv("CHAT_SESSION_TIMEOUT", "600"))  # 10分

# システムプロンプト（対話フェーズ）
SYSTEM_PROMPT_CHAT = """あなたは枚方市の市民相談を担当するAIアシスタントです。
市民の困りごとや意見を傾聴し、深掘りして具体的なニーズを引き出すことが役割です。

重要な指針:
- 解決策は提示せず、傾聴と質問に徹する
- 150文字以内の丁寧語で応答する
- 具体的な状況や背景を引き出す質問をする
- 共感的な態度で接する

回答は日本語で行ってください。"""

# システムプロンプト（要約フェーズ）
SYSTEM_PROMPT_SUMMARY = """対話ログから市民の意見を要約し、以下のJSON形式で出力してください。

{
  "summary": "意見の要約文（100文字以内）",
  "category": "カテゴリ（交通、福祉、教育、環境、その他から選択）",
  "emotion_score": 感情の強さ（0-10の整数、10が最も強い）
}

JSONのみを出力し、余計な説明は不要です。"""

# カテゴリ定義
OPINION_CATEGORIES = [
    "交通",
    "福祉",
    "教育",
    "環境",
    "子育て",
    "医療",
    "防災",
    "その他"
]
