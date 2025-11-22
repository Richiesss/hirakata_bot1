"""LINE Bot メインアプリケーション

Flask + LINE Messaging APIを使用したメインアプリ
"""

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    PostbackEvent
)
import logging

from config import (
    LINE_CHANNEL_SECRET,
    LINE_CHANNEL_ACCESS_TOKEN,
    FLASK_HOST,
    FLASK_PORT,
    FLASK_DEBUG,
)
from database.db_manager import init_db, get_db, get_or_create_user
from handlers.message_handler import handle_text_message
from handlers.follow_handler import handle_follow
from handlers.postback_handler import handle_postback

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flaskアプリケーションの初期化
app = Flask(__name__)

# LINE Bot APIの設定
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/", methods=["GET"])
def index():
    """ヘルスチェック用のエンドポイント"""
    return {
        "status": "ok",
        "service": "枚方市民ニーズ抽出ハイブリッドシステム",
        "version": "1.0.0"
    }


@app.route("/health", methods=["GET"])
def health():
    """詳細ヘルスチェック"""
    from ollama_client import get_ollama_client
    
    ollama_status = "ok" if get_ollama_client().is_available() else "error"
    
    return {
        "status": "ok",
        "components": {
            "database": "ok",  # TODO: DB接続チェック
            "ollama": ollama_status,
            "line_api": "ok"
        }
    }


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhook コールバック"""
    # X-Line-Signatureヘッダーを取得
    signature = request.headers.get("X-Line-Signature")
    
    if not signature:
        logger.error("Missing X-Line-Signature header")
        abort(400)
    
    # リクエストボディを取得
    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")
    
    # Webhookボディをパース
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        abort(500)
    
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event: MessageEvent):
    """テキストメッセージイベントのハンドラー"""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            # ユーザー情報取得
            user_id = event.source.user_id
            user_message = event.message.text
            
            logger.info(f"Received message from {user_id}: {user_message}")
            
            # データベースでユーザーを取得または作成
            with get_db() as db:
                user = get_or_create_user(db, user_id)
                logger.info(f"User: {user.id} (hash: {user.line_user_id_hash[:8]}...)")
            
            # メッセージハンドラーに委譲
            reply_messages = handle_text_message(user_id, user_message)
            
            # 応答送信
            if reply_messages:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=reply_messages
                    )
                )
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        # エラー時の応答
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="申し訳ございません。エラーが発生しました。しばらくしてから再度お試しください。")]
                    )
                )
        except:
            pass


@handler.add(FollowEvent)
def handle_follow_event(event: FollowEvent):
    """友だち追加イベントのハンドラー"""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            user_id = event.source.user_id
            logger.info(f"New follower: {user_id}")
            
            # フォローハンドラーに委譲
            reply_messages = handle_follow(user_id)
            
            if reply_messages:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=reply_messages
                    )
                )
            
    except Exception as e:
        logger.error(f"Error in handle_follow_event: {e}")


@handler.add(PostbackEvent)
def handle_postback_event(event: PostbackEvent):
    """ポストバックイベントのハンドラー"""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            user_id = event.source.user_id
            postback_data = event.postback.data
            
            logger.info(f"Postback from {user_id}: {postback_data}")
            
            # ポストバックハンドラーに委譲
            reply_messages = handle_postback(user_id, postback_data)
            
            if reply_messages:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=reply_messages
                    )
                )
            
    except Exception as e:
        logger.error(f"Error in handle_postback_event: {e}")


if __name__ == "__main__":
    # データベース初期化
    logger.info("Initializing database...")
    init_db()
    
    # アプリケーション起動
    logger.info(f"Starting Flask app on {FLASK_HOST}:{FLASK_PORT}")
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )
