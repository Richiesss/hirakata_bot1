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
    
    # 数字入力（1-4）の場合は投票として処理
    if message_text.strip() in ['1', '2', '3', '4', '１', '２', '３', '４']:
        from features.poll_handler import handle_text_poll_response
        poll_response = handle_text_poll_response(user_id, message_text.strip())
        if poll_response:
            return poll_response
    
    # 通常メッセージ → 対話モードへ
    return handle_chat_message(user_id, message_text)
