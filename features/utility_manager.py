"""ユーティリティ機能管理モジュール

履歴確認や設定変更などのユーティリティ機能を提供
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from linebot.v3.messaging import (
    FlexMessage,
    FlexContainer,
    TextMessage
)

from database.db_manager import get_db, User, Opinion, PollResponse, Poll, PollOption

logger = logging.getLogger(__name__)


def get_user_history(user_id: str, limit: int = 5) -> Dict[str, Any]:
    """ユーザーの活動履歴を取得
    
    Args:
        user_id: LINE User ID
        limit: 取得件数
    
    Returns:
        履歴データ辞書
    """
    with get_db() as db:
        user = db.query(User).filter(User.line_user_id == user_id).first()
        if not user:
            return {"opinions": [], "poll_responses": []}
        
        # 意見履歴
        opinions = db.query(Opinion).filter(
            Opinion.user_id == user.id
        ).order_by(Opinion.created_at.desc()).limit(limit).all()
        
        # 投票履歴
        responses = db.query(PollResponse).filter(
            PollResponse.user_id == user.id
        ).order_by(PollResponse.created_at.desc()).limit(limit).all()
        
        # 投票の詳細情報を付加
        formatted_responses = []
        for res in responses:
            poll = db.query(Poll).filter(Poll.id == res.poll_id).first()
            option = db.query(PollOption).filter(PollOption.id == res.option_id).first()
            if poll and option:
                formatted_responses.append({
                    "poll_title": poll.title,
                    "option_text": option.option_text,
                    "created_at": res.created_at
                })
        
        return {
            "opinions": [
                {
                    "content": op.content,
                    "category": op.category,
                    "created_at": op.created_at
                }
                for op in opinions
            ],
            "poll_responses": formatted_responses
        }


def format_history_message(history_data: Dict[str, Any]) -> FlexMessage:
    """履歴表示用Flex Messageを生成"""
    
    # 意見履歴のコンポーネント
    opinion_contents = []
    if history_data["opinions"]:
        opinion_contents.append({
            "type": "text",
            "text": "📝 最近の意見",
            "weight": "bold",
            "size": "sm",
            "color": "#1DB446",
            "margin": "md"
        })
        for op in history_data["opinions"]:
            date_str = op["created_at"].strftime("%Y/%m/%d")
            opinion_contents.append({
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"[{op['category']}] {date_str}",
                        "size": "xs",
                        "color": "#aaaaaa"
                    },
                    {
                        "type": "text",
                        "text": op["content"][:50] + ("..." if len(op["content"]) > 50 else ""),
                        "size": "sm",
                        "wrap": True,
                        "color": "#555555"
                    }
                ],
                "margin": "sm"
            })
    else:
        opinion_contents.append({
            "type": "text",
            "text": "まだ意見の投稿はありません。",
            "size": "xs",
            "color": "#aaaaaa",
            "margin": "md"
        })

    # 投票履歴のコンポーネント
    poll_contents = []
    if history_data["poll_responses"]:
        poll_contents.append({
            "type": "separator",
            "margin": "lg"
        })
        poll_contents.append({
            "type": "text",
            "text": "📊 最近の投票",
            "weight": "bold",
            "size": "sm",
            "color": "#1DB446",
            "margin": "md"
        })
        for res in history_data["poll_responses"]:
            date_str = res["created_at"].strftime("%Y/%m/%d")
            poll_contents.append({
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{date_str}",
                        "size": "xs",
                        "color": "#aaaaaa"
                    },
                    {
                        "type": "text",
                        "text": f"Q. {res['poll_title']}",
                        "size": "xs",
                        "wrap": True,
                        "color": "#555555"
                    },
                    {
                        "type": "text",
                        "text": f"A. {res['option_text']}",
                        "size": "sm",
                        "weight": "bold",
                        "color": "#333333"
                    }
                ],
                "margin": "sm"
            })
    else:
        poll_contents.append({
            "type": "separator",
            "margin": "lg"
        })
        poll_contents.append({
            "type": "text",
            "text": "まだ投票の履歴はありません。",
            "size": "xs",
            "color": "#aaaaaa",
            "margin": "md"
        })

    flex_content = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "📜 活動履歴 (直近5件)",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": "#333333"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": opinion_contents + poll_contents
        }
    }

    return FlexMessage(
        alt_text="活動履歴",
        contents=FlexContainer.from_dict(flex_content)
    )


def get_settings_message(user_id: str) -> FlexMessage:
    """設定画面用Flex Messageを生成"""
    with get_db() as db:
        user = db.query(User).filter(User.line_user_id == user_id).first()
        is_enabled = user.notification_enabled if user else True
    
    status_text = "ON" if is_enabled else "OFF"
    status_color = "#1DB446" if is_enabled else "#aaaaaa"
    toggle_action_value = "false" if is_enabled else "true"
    button_label = "通知をOFFにする" if is_enabled else "通知をONにする"
    button_style = "secondary" if is_enabled else "primary"

    flex_content = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "⚙️ 設定",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": "#333333"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "プッシュ通知",
                            "size": "md",
                            "gravity": "center",
                            "flex": 2
                        },
                        {
                            "type": "text",
                            "text": status_text,
                            "size": "md",
                            "weight": "bold",
                            "color": status_color,
                            "align": "end",
                            "gravity": "center",
                            "flex": 1
                        }
                    ],
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "※アンケートや投票の通知を受け取る設定です。",
                    "size": "xs",
                    "color": "#aaaaaa",
                    "margin": "sm",
                    "wrap": True
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": button_label,
                        "data": f"action=toggle_notification&value={toggle_action_value}",
                        "displayText": button_label
                    },
                    "style": button_style
                }
            ]
        }
    }

    return FlexMessage(
        alt_text="設定",
        contents=FlexContainer.from_dict(flex_content)
    )


def update_notification_setting(user_id: str, enabled: bool) -> bool:
    """通知設定を更新"""
    try:
        with get_db() as db:
            user = db.query(User).filter(User.line_user_id == user_id).first()
            if user:
                user.notification_enabled = enabled
                db.commit()
                return True
            return False
    except Exception as e:
        logger.error(f"Error updating notification setting: {e}")
        return False
