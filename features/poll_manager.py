"""投票（Poll）管理機能

4択投票の作成・配信・集計を管理
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    FlexMessage,
    FlexContainer,
    TextMessage,
)

from database.db_manager import (
    get_db,
    Poll,
    PollOption,
    PollResponse,
    User,
    PollDeliveryLog,
)
from config import LINE_CHANNEL_ACCESS_TOKEN

logger = logging.getLogger(__name__)


def create_poll(question: str, choices: List[str], description: str = None) -> int:
    """投票を作成

    Args:
        question: 質問文
        choices: 選択肢リスト（4つ）
        description: 説明（オプション）

    Returns:
        作成された投票ID
    """
    if len(choices) != 4:
        raise ValueError("選択肢は4つ必要です")

    with get_db() as db:
        # 投票作成
        poll = Poll(title=question, description=description, status="draft")
        db.add(poll)
        db.flush()

        # 選択肢作成
        for i, choice_text in enumerate(choices, 1):
            option = PollOption(
                poll_id=poll.id, option_text=choice_text, option_order=i
            )
            db.add(option)

        db.commit()
        db.refresh(poll)

        logger.info(f"Poll created: {poll.id}")
        return poll.id


def get_poll_flex_message(poll_id: int) -> FlexMessage:
    """投票用Flex Messageを生成

    Args:
        poll_id: 投票ID

    Returns:
        FlexMessage
    """
    with get_db() as db:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise ValueError(f"Poll not found: {poll_id}")

        options = (
            db.query(PollOption)
            .filter(PollOption.poll_id == poll_id)
            .order_by(PollOption.option_order)
            .all()
        )

        # Flex Message作成（シンプルなボタン形式）
        flex_content = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "市民アンケート",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#FFFFFF",
                    }
                ],
                "backgroundColor": "#667eea",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": poll.title,
                        "wrap": True,
                        "weight": "bold",
                        "size": "md",
                        "margin": "md",
                    },
                    {
                        "type": "text",
                        "text": "※選択肢の番号（1〜4）を入力して送信することでも投票できます。",
                        "wrap": True,
                        "size": "xs",
                        "color": "#666666",
                        "margin": "lg",
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": f"{i}. {option.option_text[:20]}",
                            "data": f"poll:{poll_id}:{option.id}",
                            "displayText": f"{i}. {option.option_text}",
                        },
                        "style": "primary" if i == 1 else "secondary",
                        "margin": "sm",
                    }
                    for i, option in enumerate(options, 1)
                ],
                "spacing": "sm",
            },
        }

        return FlexMessage(
            alt_text=f"アンケート: {poll.title}",
            contents=FlexContainer.from_dict(flex_content),
        )


def send_poll_to_users(poll_id: int, user_ids: List[str] = None) -> Dict:
    """投票をユーザーに配信

    Args:
        poll_id: 投票ID
        user_ids: 配信対象LINE User IDリスト（Noneの場合は全ユーザー）

    Returns:
        配信結果 {"success": int, "failed": int}
    """
    with get_db() as db:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise ValueError(f"Poll not found: {poll_id}")

        # 配信対象ユーザー取得
        if user_ids:
            # 指定ユーザーのみ
            from database.db_manager import hash_line_user_id

            hashes = [hash_line_user_id(uid) for uid in user_ids]
            users = db.query(User).filter(User.line_user_id_hash.in_(hashes)).all()
        else:
            # 全ユーザー
            users = db.query(User).filter(User.notification_enabled == True).all()

        if not users:
            logger.warning("No users to send poll")
            return {"success": 0, "failed": 0}

        # Flex Message生成
        flex_message = get_poll_flex_message(poll_id)

        # 配信ログ作成
        delivery_log = PollDeliveryLog(
            poll_id=poll_id, target_user_count=len(users), sent_at=datetime.utcnow()
        )
        db.add(delivery_log)
        db.flush()  # ID取得のためflush

        # プッシュ配信
        configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        success_count = 0
        failed_count = 0

        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)

            for user in users:
                try:
                    # LINE User IDがある場合のみ送信
                    if user.line_user_id:
                        messaging_api.push_message(
                            PushMessageRequest(
                                to=user.line_user_id, messages=[flex_message]
                            )
                        )
                        success_count += 1
                    else:
                        logger.warning(
                            f"User {user.id} has no line_user_id, skipping push"
                        )
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed to send poll to user {user.id}: {e}")
                    failed_count += 1

        # ログ更新
        delivery_log.sent_count = success_count
        delivery_log.failed_count = failed_count

        # 投票のステータスを更新
        if poll.status == "draft":
            poll.status = "published"
            poll.published_at = datetime.utcnow()

        db.commit()

        logger.info(
            f"Poll {poll_id} sent: {success_count} success, {failed_count} failed"
        )
        return {"success": success_count, "failed": failed_count}


def get_poll_results(poll_id: int) -> Dict:
    """投票結果を集計

    Args:
        poll_id: 投票ID

    Returns:
        集計結果
    """
    with get_db() as db:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise ValueError(f"Poll not found: {poll_id}")

        options = (
            db.query(PollOption)
            .filter(PollOption.poll_id == poll_id)
            .order_by(PollOption.option_order)
            .all()
        )

        total_responses = (
            db.query(PollResponse).filter(PollResponse.poll_id == poll_id).count()
        )

        results = []
        for option in options:
            count = (
                db.query(PollResponse)
                .filter(
                    PollResponse.poll_id == poll_id, PollResponse.option_id == option.id
                )
                .count()
            )

            percentage = (count / total_responses * 100) if total_responses > 0 else 0

            results.append(
                {
                    "option_id": option.id,
                    "option_text": option.option_text,
                    "count": count,
                    "percentage": round(percentage, 1),
                }
            )

        return {
            "poll_id": poll_id,
            "title": poll.title,
            "total_responses": total_responses,
            "options": results,
        }


def close_poll(poll_id: int):
    """投票を締め切る

    Args:
        poll_id: 投票ID
    """
    with get_db() as db:
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise ValueError(f"Poll not found: {poll_id}")

        poll.status = "closed"
        poll.closed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Poll {poll_id} closed")
