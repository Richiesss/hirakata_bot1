"""投票のポストバック処理

ユーザーの投票選択を処理し、ポイントを付与
"""

import logging
from typing import List
from linebot.v3.messaging import TextMessage

from database.db_manager import (
    get_db,
    get_or_create_user,
    add_points,
    Poll,
    PollOption,
    PollResponse
)
from config import POINT_POLL_RESPONSE

logger = logging.getLogger(__name__)


def handle_poll_response(user_id: str, poll_id: int, option_id: int) -> List[TextMessage]:
    """投票回答を処理
    
    Args:
        user_id: LINE User ID
        poll_id: 投票ID
        option_id: 選択した選択肢ID
    
    Returns:
        応答メッセージのリスト
    """
    try:
        with get_db() as db:
            # ユーザー取得
            user = get_or_create_user(db, user_id)
            
            # 投票取得
            poll = db.query(Poll).filter(Poll.id == poll_id).first()
            if not poll:
                return [TextMessage(text="申し訳ございません。アンケートが見つかりませんでした。")]
            
            if poll.status == 'closed':
                return [TextMessage(text="このアンケートは既に締め切られています。")]
            
            # 選択肢取得
            option = db.query(PollOption).filter(PollOption.id == option_id).first()
            if not option or option.poll_id != poll_id:
                return [TextMessage(text="申し訳ございません。選択が無効です。")]
            
            # 既に回答済みかチェック
            existing_response = db.query(PollResponse).filter(
                PollResponse.poll_id == poll_id,
                PollResponse.user_id == user.id
            ).first()
            
            if existing_response:
                return [TextMessage(text="このアンケートには既に回答済みです。ご協力ありがとうございました。")]
            
            # 回答を保存
            response = PollResponse(
                poll_id=poll_id,
                user_id=user.id,
                option_id=option_id
            )
            db.add(response)
            db.commit()
            
            # ポイント付与
            total_points = add_points(
                db,
                user.id,
                POINT_POLL_RESPONSE,
                'poll_response',
                reference_id=poll_id
            )
            
            logger.info(f"Poll response saved: user={user.id}, poll={poll_id}, option={option_id}")
            
            # 応答メッセージ
            response_text = f"""📊 ご回答ありがとうございます！

あなたの選択:
{option.option_text}

💎 {POINT_POLL_RESPONSE}ポイントを獲得しました
累積ポイント: {total_points} pt

引き続きご協力をお願いします。"""
            
            return [TextMessage(text=response_text)]
    
    except Exception as e:
        logger.error(f"Error in handle_poll_response: {e}", exc_info=True)
        return [TextMessage(text="申し訳ございません。エラーが発生しました。")]


def handle_text_poll_response(user_id: str, text: str) -> List[TextMessage]:
    """テキスト入力による投票処理
    
    Args:
        user_id: LINE User ID
        text: 入力テキスト（1-4）
    
    Returns:
        応答メッセージのリスト（投票処理されなかった場合はNone）
    """
    # 全角数字を半角に変換
    text = text.replace('１', '1').replace('２', '2').replace('３', '3').replace('４', '4')
    
    if text not in ['1', '2', '3', '4']:
        return None
        
    choice_index = int(text)
    
    with get_db() as db:
        # 公開中の最新の投票を取得
        poll = db.query(Poll).filter(
            Poll.status == 'published'
        ).order_by(Poll.created_at.desc()).first()
        
        if not poll:
            return None
            
        # 選択肢を取得
        option = db.query(PollOption).filter(
            PollOption.poll_id == poll.id,
            PollOption.option_order == choice_index
        ).first()
        
        if not option:
            return None
            
        # 投票処理を実行
        return handle_poll_response(user_id, poll.id, option.id)
