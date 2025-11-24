#!/usr/bin/env python3
"""プッシュ通知のテスト"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from database.db_manager import get_db, User
from config import LINE_CHANNEL_ACCESS_TOKEN

def test_push_notification():
    """プッシュ通知のテスト"""
    print("=== プッシュ通知テスト ===\n")
    
    with get_db() as db:
        # 通知可能なユーザーを取得
        users = db.query(User).filter(
            User.notification_enabled == True,
            User.line_user_id != None
        ).all()
        
        print(f"通知可能ユーザー数: {len(users)}\n")
        
        if not users:
            print("通知可能なユーザーがいません")
            return
        
        # 各ユーザーにテストメッセージを送信
        configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            
            for user in users:
                print(f"User ID: {user.id}")
                print(f"  LINE User ID: {user.line_user_id}")
                print(f"  notification_enabled: {user.notification_enabled}")
                
                try:
                    # テストメッセージ送信
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=user.line_user_id,
                            messages=[TextMessage(
                                text="【テスト通知】\n\nプッシュ通知のテストです。この通知が届いていれば、プッシュ通知機能は正常に動作しています。"
                            )]
                        )
                    )
                    print("  ✅ プッシュ通知送信成功\n")
                except Exception as e:
                    print(f"  ❌ エラー: {e}\n")
                    import traceback
                    traceback.print_exc()

if __name__ == "__main__":
    test_push_notification()
