#!/usr/bin/env python3
"""友だち追加イベントテスト用のスクリプト"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    BroadcastRequest,
    TextMessage
)
from config import LINE_CHANNEL_ACCESS_TOKEN

def send_broadcast_message():
    """全友だちにブロードキャストメッセージを送信"""
    
    print("="*60)
    print("ブロードキャストメッセージ送信")
    print("="*60)
    
    message_text = """【重要】枚方市民ニーズ抽出システムへようこそ！

このメッセージを受け取った方は、
何でもいいのでこのBotに返信してください。

例: 「こんにちは」「登録」「1」など

返信していただくことで、
今後のアンケートや投票の通知を
受け取れるようになります。

ご協力をお願いします！"""
    
    print(f"\n送信するメッセージ:")
    print("-"*60)
    print(message_text)
    print("-"*60)
    
    response = input("\nこのメッセージを全友だちに送信しますか？ (y/n): ")
    
    if response.lower() != 'y':
        print("キャンセルしました")
        return
    
    try:
        configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
        
        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            
            # ブロードキャストメッセージ送信
            messaging_api.broadcast(
                BroadcastRequest(
                    messages=[TextMessage(text=message_text)]
                )
            )
            
            print("\n✅ ブロードキャストメッセージを送信しました")
            print("\n注意:")
            print("  - 無料プランの場合、月1000通までの制限があります")
            print("  - 友だちが返信すると、データベースに自動登録されます")
            print("  - 返信があったら scripts/check_users.py で確認してください")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_broadcast_message()
