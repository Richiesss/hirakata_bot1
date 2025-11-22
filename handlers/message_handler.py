"""テキストメッセージハンドラー

ユーザーからのテキストメッセージを処理し、コマンドまたは対話モードに振り分け
"""

import logging
from typing import List
from linebot.v3.messaging import TextMessage

from handlers.command_handler import handle_command, is_command
from features.chat_opinion import handle_chat_message

logger = logging.getLogger(__name__)


def handle_text_message(user_id: str, message_text: str) -> List[TextMessage]:
    """
    テキストメッセージを処理
    
    Args:
        user_id: LINE User ID
        message_text: メッセージテキスト
    
    Returns:
        応答メッセージのリスト
    """
    # コマンドチェック
    if is_command(message_text):
        return handle_command(user_id, message_text)
    
    # 通常メッセージ → 対話モードへ
    return handle_chat_message(user_id, message_text)
