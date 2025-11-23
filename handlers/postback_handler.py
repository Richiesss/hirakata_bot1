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
    logger.info(f"Postback from {user_id}: {postback_data}")
    
    # 投票のポストバック: poll:123:456 (poll_id:option_id)
    if postback_data.startswith('poll:'):
        from features.poll_handler import handle_poll_response
        
        try:
            parts = postback_data.split(':')
            if len(parts) != 3:
                return [TextMessage(text="無効なデータです。")]
            
            poll_id = int(parts[1])
            option_id = int(parts[2])
            
            return handle_poll_response(user_id, poll_id, option_id)
        
        except ValueError:
            return [TextMessage(text="無効なデータです。")]
        except Exception as e:
            logger.error(f"Error handling poll postback: {e}", exc_info=True)
            return [TextMessage(text="エラーが発生しました。")]
    
    # その他のポストバック
    return [TextMessage(text="この機能は準備中です。")]
