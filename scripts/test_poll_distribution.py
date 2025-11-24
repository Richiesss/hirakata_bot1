#!/usr/bin/env python3
"""投票配信のテスト"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from features.poll_manager import send_poll_to_users, get_poll_results
from database.db_manager import get_db, Poll

def test_poll_distribution():
    """投票配信のテスト"""
    print("=== 投票配信テスト ===\n")
    
    with get_db() as db:
        # 公開中の投票を取得
        polls = db.query(Poll).filter(Poll.status == 'published').all()
        
        if not polls:
            print("公開中の投票がありません")
            # draft状態の投票を表示
            draft_polls = db.query(Poll).filter(Poll.status == 'draft').all()
            if draft_polls:
                print(f"\nドラフト状態の投票: {len(draft_polls)}件")
                for poll in draft_polls:
                    print(f"  ID: {poll.id}, Title: {poll.title}")
            return
        
        print(f"公開中の投票: {len(polls)}件\n")
        
        for poll in polls:
            print(f"Poll ID: {poll.id}")
            print(f"  Title: {poll.title}")
            print(f"  Status: {poll.status}")
            print(f"  Published at: {poll.published_at}")
            
            # 結果を確認
            try:
                results = get_poll_results(poll.id)
                print(f"  Total responses: {results['total_responses']}")
                for option in results['options']:
                    print(f"    - {option['option_text']}: {option['count']}票 ({option['percentage']}%)")
            except Exception as e:
                print(f"  結果取得エラー: {e}")
            
            print()

def test_send_poll():
    """最新のdraft投票を配信してみる"""
    print("\n=== 投票配信実行 ===\n")
    
    with get_db() as db:
        # draft状態の投票を取得
        draft_poll = db.query(Poll).filter(Poll.status == 'draft').first()
        
        if not draft_poll:
            print("配信可能な投票がありません")
            return
        
        print(f"Poll ID {draft_poll.id} を配信します")
        print(f"Title: {draft_poll.title}\n")
        
        try:
            result = send_poll_to_users(draft_poll.id)
            print(f"✅ 配信完了")
            print(f"  成功: {result['success']}件")
            print(f"  失敗: {result['failed']}件")
        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_poll_distribution()
    
    # ユーザーの確認を求める
    print("\n" + "="*50)
    response = input("draft投票を配信してテストしますか？ (y/n): ")
    if response.lower() == 'y':
        test_send_poll()
