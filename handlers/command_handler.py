"""コマンドハンドラー

/help, /reset, /point等のコマンドを処理
"""

import logging
from typing import List
from linebot.v3.messaging import TextMessage

from database.db_manager import get_db, get_or_create_user
from features.chat_opinion import reset_chat_session

logger = logging.getLogger(__name__)


def is_command(message_text: str) -> bool:
    """メッセージがコマンドかどうか判定"""
    return message_text.startswith("/")


def handle_command(user_id: str, command: str) -> List[TextMessage]:
    """
    コマンドを処理
    
    Args:
        user_id: LINE User ID
        command: コマンド文字列
    
    Returns:
        応答メッセージのリスト
    """
    command = command.lower().strip()
    
    if command == "/help":
        return handle_help()
    elif command == "/reset":
        return handle_reset(user_id)
    elif command == "/point":
        return handle_point(user_id)
    else:
        return [TextMessage(text=f"不明なコマンドです: {command}\n/helpで利用可能なコマンドを確認できます。")]


def handle_help() -> List[TextMessage]:
    """ヘルプコマンド"""
    help_text = """【利用可能なコマンド】

/help - このヘルプを表示
/reset - 対話をリセット
/point - 累積ポイントを確認

【使い方】
メッセージを送信すると、AIが質問を返してあなたの意見を引き出します。
対話が完了すると、意見が保存されポイントが付与されます。"""
    
    return [TextMessage(text=help_text)]


def handle_reset(user_id: str) -> List[TextMessage]:
    """リセットコマンド"""
    try:
        reset_chat_session(user_id)
        return [TextMessage(text="対話履歴をリセットしました。新しい話題をお聞かせください。")]
    except Exception as e:
        logger.error(f"Error in handle_reset: {e}")
        return [TextMessage(text="リセット処理でエラーが発生しました。")]


def handle_point(user_id: str) -> List[TextMessage]:
    """ポイント確認コマンド"""
    try:
        with get_db() as db:
            user = get_or_create_user(db, user_id)
            
            point_text = f"""【あなたのポイント】

累積ポイント: {user.total_points} pt

ご協力ありがとうございます！
引き続き市政へのご意見をお聞かせください。"""
            
            return [TextMessage(text=point_text)]
    except Exception as e:
        logger.error(f"Error in handle_point: {e}")
        return [TextMessage(text="ポイント取得でエラーが発生しました。")]
