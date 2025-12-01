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
    
    # ユーザー登録アクション
    elif postback_data == 'action=register':
        from database.db_manager import get_db, get_or_create_user
        
        try:
            with get_db() as db:
                user = get_or_create_user(db, user_id)
                logger.info(f"User manually registered via postback: {user.id}")
                
            return [TextMessage(text="✅ 登録が完了しました！\n\nこれでアンケートや投票の通知を受け取れるようになりました。\n\n引き続き、ご意見やご要望があればいつでもメッセージを送ってください。")]
            
        except Exception as e:
            logger.error(f"Error handling register postback: {e}", exc_info=True)
            return [TextMessage(text="登録処理中にエラーが発生しました。")]

    # 通知設定切り替え
    elif 'action=toggle_notification' in postback_data:
        from features.utility_manager import update_notification_setting, get_settings_message
        
        try:
            # パラメータ解析 (簡易的)
            value_str = 'false'
            if 'value=true' in postback_data:
                value_str = 'true'
            
            enabled = (value_str == 'true')
            
            if update_notification_setting(user_id, enabled):
                # 設定画面を再表示（状態更新のため）
                return [
                    TextMessage(text=f"通知を{'ON' if enabled else 'OFF'}にしました。"),
                    get_settings_message(user_id)
                ]
            else:
                return [TextMessage(text="設定の更新に失敗しました。")]
                
        except Exception as e:
            logger.error(f"Error handling notification toggle: {e}", exc_info=True)
            return [TextMessage(text="エラーが発生しました。")]

    # その他のポストバック
    return [TextMessage(text="この機能は準備中です。")]
