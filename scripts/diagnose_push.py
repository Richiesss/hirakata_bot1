#!/usr/bin/env python3
"""プッシュ通知の問題を診断"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import get_db, User, Poll, PollResponse
from config import LINE_CHANNEL_ACCESS_TOKEN
import os

def diagnose_push_notification():
    """プッシュ通知の問題を診断"""
    print("="*60)
    print("プッシュ通知診断レポート")
    print("="*60)
    
    # 1. 環境変数の確認
    print("\n【1. LINE API設定】")
    if LINE_CHANNEL_ACCESS_TOKEN:
        print(f"  ✅ LINE_CHANNEL_ACCESS_TOKEN: 設定済み (長さ: {len(LINE_CHANNEL_ACCESS_TOKEN)})")
    else:
        print("  ❌ LINE_CHANNEL_ACCESS_TOKEN: 未設定")
    
    # 2. データベースの確認
    print("\n【2. データベース状態】")
    with get_db() as db:
        total_users = db.query(User).count()
        notifiable_users = db.query(User).filter(
            User.notification_enabled == True
        ).all()
        users_with_line_id = db.query(User).filter(
            User.line_user_id != None
        ).all()
        
        print(f"  総ユーザー数: {total_users}")
        print(f"  notification_enabled=True: {len(notifiable_users)}")
        print(f"  line_user_idあり: {len(users_with_line_id)}")
        
        # 通知可能なユーザーの詳細
        pushable_users = [u for u in notifiable_users if u.line_user_id]
        print(f"  プッシュ通知可能: {len(pushable_users)}")
        
        if pushable_users:
            print("\n  【ユーザー詳細】")
            for user in pushable_users:
                print(f"    - User ID: {user.id}")
                print(f"      LINE User ID: {user.line_user_id}")
                print(f"      notification_enabled: {user.notification_enabled}")
                print(f"      created_at: {user.created_at}")
    
    # 3. 投票の確認
    print("\n【3. 投票状態】")
    with get_db() as db:
        polls = db.query(Poll).all()
        print(f"  総投票数: {len(polls)}")
        
        for poll in polls:
            response_count = db.query(PollResponse).filter(
                PollResponse.poll_id == poll.id
            ).count()
            
            print(f"\n  投票 ID: {poll.id}")
            print(f"    タイトル: {poll.title}")
            print(f"    ステータス: {poll.status}")
            print(f"    公開日時: {poll.published_at}")
            print(f"    回答数: {response_count}")
    
    # 4. プッシュ通知テスト
    print("\n【4. プッシュ通知テスト】")
    from linebot.v3.messaging import (
        Configuration,
        ApiClient,
        MessagingApi,
        PushMessageRequest,
        TextMessage
    )
    
    with get_db() as db:
        pushable_users = db.query(User).filter(
            User.notification_enabled == True,
            User.line_user_id != None
        ).all()
        
        if not pushable_users:
            print("  ⚠️ プッシュ通知可能なユーザーがいません")
            return
        
        configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            
            for user in pushable_users:
                try:
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=user.line_user_id,
                            messages=[TextMessage(
                                text="【診断テスト】\n\nこのメッセージが届いていれば、プッシュ通知は正常に機能しています。"
                            )]
                        )
                    )
                    print(f"  ✅ User {user.id} へのプッシュ通知: 成功")
                except Exception as e:
                    print(f"  ❌ User {user.id} へのプッシュ通知: 失敗")
                    print(f"     エラー: {e}")
    
    print("\n" + "="*60)
    print("診断完了")
    print("="*60)

if __name__ == "__main__":
    diagnose_push_notification()
