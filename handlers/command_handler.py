"""コマンドハンドラー"""

import logging
from typing import List
from linebot.v3.messaging import TextMessage
from database.db_manager import get_db, get_or_create_user
import logging
import os

logger = logging.getLogger(__name__)

def is_command(text: str) -> bool:
    """テキストがコマンドかどうかを判定"""
    return text.startswith('/') or text in ['アンケート', '投票']

def handle_command(user_id: str, text: str) -> list:
    """コマンドを処理
    
    Args:
        user_id: LINE User ID
        text: コマンドテキスト
        
    Returns:
        応答メッセージのリスト
    """
    text = text.strip()
    text_lower = text.lower()
    
    if text == 'アンケート':
        return handle_survey(user_id)
    elif text == '投票':
        return handle_poll(user_id)
    elif text_lower == '/help':
        return handle_help()
    elif text_lower == '/reset':
        return handle_reset(user_id)
    elif text_lower == '/point':
        return handle_point(user_id)
    else:
        return [TextMessage(text="不明なコマンドです。/help でコマンド一覧を確認できます。")]


def handle_survey(user_id: str) -> list:
    """アンケートURLを返す"""
    # ngrok URLを環境変数または設定から取得
    # 本番環境では固定URLを使用
    base_url = os.getenv('PUBLIC_URL', 'https://longevous-cubbishly-helena.ngrok-free.dev')
    survey_url = f"{base_url}/web/survey?user_id={user_id}"
    
    survey_text = f"""📝 アンケートフォーム

以下のリンクからアンケートに回答できます：

{survey_url}

カテゴリを選択して、ご意見をお聞かせください。
回答で5ポイント獲得できます！"""
    
    return [TextMessage(text=survey_text)]


def handle_poll(user_id: str) -> list:
    """最新の投票を表示"""
    from database.db_manager import get_db, Poll
    from features.poll_manager import get_poll_flex_message
    
    with get_db() as db:
        # 公開中の投票を取得
        poll = db.query(Poll).filter(
            Poll.status == 'published'
        ).order_by(Poll.created_at.desc()).first()
        
        if not poll:
            return [TextMessage(text="現在、公開中の投票はありません。")]
        
        try:
            flex_message = get_poll_flex_message(poll.id)
            return [flex_message]
        except Exception as e:
            logger.error(f"Error creating flex message: {e}")
            return [TextMessage(text="エラーが発生しました。")]


def handle_help() -> list:
    """ヘルプメッセージを返す"""
    help_text = """【利用可能なコマンド】

💬 対話で意見を送る
「意見を送りたい」と入力してください

📝 アンケートで意見を送る
「アンケート」と入力またはリッチメニューから

📊 投票に参加
「投票」と入力

💎 ポイント確認
/point

🔄 対話をリセット
/reset

❓ ヘルプ
/help

ご意見をお待ちしています！"""
    
    return [TextMessage(text=help_text)]


def handle_reset(user_id: str) -> list:
    """対話履歴をリセット"""
    from features.chat_opinion import reset_chat_session
    
    reset_chat_session(user_id)
    
    return [TextMessage(text="対話履歴をリセットしました。新しい意見を送信できます。")]


def handle_point(user_id: str) -> list:
    """ポイント残高を表示"""
    try:
        with get_db() as db:
            user = get_or_create_user(db, user_id)
            
            point_text = f"""💎 あなたのポイント

総ポイント: {user.total_points} ポイント

【ポイントの貯め方】
・対話で意見: 10ポイント
・アンケート: 5ポイント
・投票: 3ポイント

引き続きご意見をお待ちしています！"""
            
            return [TextMessage(text=point_text)]
    except Exception as e:
        logger.error(f"Error in handle_point: {e}")
        return [TextMessage(text="ポイント取得でエラーが発生しました。")]
