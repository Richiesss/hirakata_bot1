"""ポストバックハンドラー

ボタンタップ等のポストバックイベントを処理
"""

import logging
from typing import List
from linebot.v3.messaging import TextMessage

logger = logging.getLogger(__name__)


def handle_postback(user_id: str, postback_data: str) -> List[TextMessage]:
    """
    ポストバックイベントを処理
    
    Args:
        user_id: LINE User ID
        postback_data: ポストバックデータ
    
    Returns:
        応答メッセージのリスト
    """
    # TODO: リッチメニュー、アンケート選択などのポストバック処理
    logger.info(f"Postback from {user_id}: {postback_data}")
    
    return [TextMessage(text="この機能は準備中です。")]
