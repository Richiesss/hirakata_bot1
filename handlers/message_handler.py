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
    
    # 数字入力（1-4）または "1. 選択肢" 形式の場合は投票として処理
    stripped_text = message_text.strip()
    logger.info(f"Processing text message: '{stripped_text}'")
    
    # 全角数字を半角に変換
    normalized_text = stripped_text.replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4')
    
    # "1. " のような形式かチェック
    vote_number = None
    if normalized_text in ['1', '2', '3', '4']:
        vote_number = normalized_text
    elif len(normalized_text) >= 2 and normalized_text[0] in ['1', '2', '3', '4'] and normalized_text[1] in ['.', '．']:
        vote_number = normalized_text[0]
        
    if vote_number:
        logger.info(f"Detected vote number: {vote_number}")
        from features.poll_handler import handle_text_poll_response
        poll_response = handle_text_poll_response(user_id, vote_number)
        if poll_response:
            logger.info("Poll response handled successfully")
            return poll_response
        else:
            logger.warning("Poll response handling returned None")
    
    # 通常メッセージ → 対話モードへ
    logger.info("Delegating to chat handler")
    return handle_chat_message(user_id, message_text)
