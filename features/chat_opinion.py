"""対話型意見収集機能

市民とのAI対話でニーズを収集し、要約してDBに保存
UC-001～UC-005を実装
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from linebot.v3.messaging import TextMessage

from database.db_manager import (
    get_db,
    get_or_create_user,
    add_points,
    User,
    ChatSession,
    ChatMessage,
    Opinion
)
from ollama_client import get_ollama_client
from config import (
    MAX_CHAT_TURNS,
    CHAT_SESSION_TIMEOUT,
    POINT_CHAT_OPINION
)

logger = logging.getLogger(__name__)

# セッションキャッシュ（メモリ上で管理）
_active_sessions = {}


def get_active_session(user_id: str) -> Optional[dict]:
    """アクティブなセッション情報を取得"""
    if user_id in _active_sessions:
        session_info = _active_sessions[user_id]
        
        # タイムアウトチェック
        if datetime.now() - session_info['last_updated'] > timedelta(seconds=CHAT_SESSION_TIMEOUT):
            logger.info(f"Session timeout for user {user_id}")
            del _active_sessions[user_id]
            return None
        
        return session_info
    
    return None


def set_active_session(user_id: str, session_id: int):
    """アクティブセッションを設定"""
    _active_sessions[user_id] = {
        'session_id': session_id,
        'last_updated': datetime.now()
    }


def clear_active_session(user_id: str):
    """アクティブセッションをクリア"""
    if user_id in _active_sessions:
        del _active_sessions[user_id]


def reset_chat_session(user_id: str):
    """対話セッションをリセット"""
    clear_active_session(user_id)


def handle_chat_message(user_id: str, message_text: str) -> List[TextMessage]:
    """
    対話メッセージを処理（UC-001〜UC-004）
    
    Args:
        user_id: LINE User ID
        message_text: ユーザーメッセージ
    
    Returns:
        応答メッセージのリスト
    """
    try:
        with get_db() as db:
            # ユーザー取得
            user = get_or_create_user(db, user_id)
            
            # アクティブセッションチェック
            session_info = get_active_session(user_id)
            
            if session_info:
                # 既存セッション継続
                session_id = session_info['session_id']
                session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            else:
                # 新規セッション開始（UC-001）
                session = ChatSession(
                    user_id=user.id,
                    status='active',
                    turn_count=0
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                
                set_active_session(user_id, session.id)
                logger.info(f"New chat session started: {session.id} for user {user.id}")
            
            # ユーザーメッセージを保存
            user_msg = ChatMessage(
                session_id=session.id,
                role='user',
                content=message_text
            )
            db.add(user_msg)
            
            # 対話履歴取得
            chat_history = get_chat_history(db, session.id)
            
            # Ollama呼び出し（UC-002: 意見収集対話、UC-003: 追加質問）
            ollama_client = get_ollama_client()
            assistant_response = ollama_client.chat_mode(message_text, chat_history)
            
            # アシスタント応答を保存
            assistant_msg = ChatMessage(
                session_id=session.id,
                role='assistant',
                content=assistant_response
            )
            db.add(assistant_msg)
            
            # ターン数更新
            session.turn_count += 1
            db.commit()
            
            # セッション更新時刻を更新
            set_active_session(user_id, session.id)
            
            # 終了判定
            if session.turn_count >= MAX_CHAT_TURNS:
                # 対話終了 → 要約生成（UC-004）
                summary_result = finalize_chat_session(db, session)
                
                if summary_result:
                    # ポイント付与（UC-005）
                    total_points = add_points(
                        db,
                        user.id,
                        POINT_CHAT_OPINION,
                        'chat_opinion',
                        reference_id=summary_result['opinion_id']
                    )
                    
                    return [
                        TextMessage(text=assistant_response),
                        TextMessage(text=f"""ご意見ありがとうございました！

【あなたの意見】
{summary_result['summary']}

カテゴリ: {summary_result['category']}

{POINT_CHAT_OPINION}ポイントを付与しました。
累積ポイント: {total_points} pt

引き続き、ご意見をお聞かせください。""")
                    ]
                else:
                    return [
                        TextMessage(text=assistant_response),
                        TextMessage(text="ご意見ありがとうございました！")
                    ]
            else:
                # 対話継続
                remaining_turns = MAX_CHAT_TURNS - session.turn_count
                return [
                    TextMessage(text=assistant_response),
                    TextMessage(text=f"(あと{remaining_turns}回の質問で意見をまとめます)")
                ]
    
    except Exception as e:
        logger.error(f"Error in handle_chat_message: {e}", exc_info=True)
        return [TextMessage(text="申し訳ございません。エラーが発生しました。/resetでやり直してください。")]


def get_chat_history(db, session_id: int) -> List[dict]:
    """
    セッションの対話履歴を取得
    
    Returns:
        [{"role": "user"|"assistant", "content": "..."}]
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


def finalize_chat_session(db, session: ChatSession) -> Optional[dict]:
    """
    対話セッションを終了し、要約を生成してDBに保存
    
    Args:
        db: データベースセッション
        session: ChatSessionオブジェクト
    
    Returns:
        {
            "opinion_id": 意見ID,
            "summary": 要約文,
            "category": カテゴリ
        }
    """
    try:
        # 対話履歴取得
        chat_history = get_chat_history(db, session.id)
        
        if not chat_history:
            logger.warning(f"No chat history for session {session.id}")
            return None
        
        # Ollamaで要約生成
        ollama_client = get_ollama_client()
        summary_result = ollama_client.summary_mode(chat_history)
        
        if not summary_result:
            logger.error(f"Failed to generate summary for session {session.id}")
            return None
        
        # セッションに要約を保存
        session.status = 'completed'
        session.completed_at = datetime.utcnow()
        session.summary_text = summary_result.get('summary', '')
        session.summary_category = summary_result.get('category', 'その他')
        session.summary_emotion_score = summary_result.get('emotion_score', 5)
        
        # 意見テーブルに登録
        opinion = Opinion(
            user_id=session.user_id,
            source_type='chat',
            content=summary_result.get('summary', ''),
            category=summary_result.get('category', 'その他'),
            emotion_score=summary_result.get('emotion_score', 5),
            session_id=session.id
        )
        db.add(opinion)
        db.commit()
        db.refresh(opinion)
        
        # アクティブセッションをクリア
        clear_active_session(str(session.user_id))
        
        logger.info(f"Chat session finalized: {session.id}, opinion: {opinion.id}")
        
        return {
            "opinion_id": opinion.id,
            "summary": summary_result.get('summary', ''),
            "category": summary_result.get('category', 'その他')
        }
    
    except Exception as e:
        logger.error(f"Error in finalize_chat_session: {e}", exc_info=True)
        return None
