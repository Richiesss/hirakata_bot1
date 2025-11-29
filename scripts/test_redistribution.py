#!/usr/bin/env python3
"""投票再配信とログのテスト"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from features.poll_manager import send_poll_to_users
from database.db_manager import get_db, Poll, PollDeliveryLog

def test_redistribution():
    """再配信テスト"""
    print("=== 再配信テスト ===\n")
    
    with get_db() as db:
        # 公開中の投票を取得
        poll = db.query(Poll).filter(Poll.status == 'published').first()
        
        if not poll:
            print("公開中の投票がありません。テストをスキップします。")
            return
        
        print(f"Poll ID {poll.id} ({poll.title}) を再配信します...")
        
        # 再配信実行
        try:
            result = send_poll_to_users(poll.id)
            print(f"✅ 配信完了: 成功={result['success']}, 失敗={result['failed']}")
            
            # ログ確認
            log = db.query(PollDeliveryLog).filter(
                PollDeliveryLog.poll_id == poll.id
            ).order_by(PollDeliveryLog.sent_at.desc()).first()
            
            if log:
                print(f"\n✅ ログが作成されました:")
                print(f"  ID: {log.id}")
                print(f"  Sent Count: {log.sent_count}")
                print(f"  Failed Count: {log.failed_count}")
                print(f"  Target User Count: {log.target_user_count}")
                print(f"  Sent At: {log.sent_at}")
            else:
                print("\n❌ ログが作成されていません")
                
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_redistribution()
