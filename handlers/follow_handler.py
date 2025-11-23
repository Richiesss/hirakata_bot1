"""友だち追加ハンドラー

新規ユーザー登録と初回挨拶
"""

import logging
from typing import List
from linebot.v3.messaging import TextMessage

from database.db_manager import get_db, get_or_create_user

logger = logging.getLogger(__name__)


def handle_follow(user_id: str) -> List[TextMessage]:
    """
    友だち追加時の処理
    
    Args:
        user_id: LINE User ID
    
    Returns:
        応答メッセージのリスト
    """
    try:
        # ユーザー登録
        with get_db() as db:
            user = get_or_create_user(db, user_id)
            logger.info(f"New user registered: {user.id}")
        
        # ウェルカムメッセージ
        welcome_text = """枚方市民ニーズ抽出システムへようこそ！

このBotでは、市政に関するあなたのご意見・ご要望をお聞かせいただけます。

【3つの参加方法】
1. 対話形式：AIとの対話でニーズを引き出します
2. 自由記述：アンケートフォームから意見を投稿
3. 選択式投票：定期的な簡単アンケートに回答

いただいたご意見は市政改善に活用されます。
ご協力いただくとポイントが貯まります！

※友だち追加により、アンケートや投票の通知が届くようになります。

まずは、あなたの困りごとや要望を自由にお話しください。"""
        
        return [TextMessage(text=welcome_text)]
        
    except Exception as e:
        logger.error(f"Error in handle_follow: {e}")
        return [TextMessage(text="ご登録ありがとうございます！")]
