"""テストデータ作成スクリプト"""

from database.db_manager import get_db, User, Opinion, ChatSession, hash_line_user_id, add_points
from datetime import datetime, timedelta
import random

# テストデータ
test_opinions = [
    {"category": "交通", "content": "駅前の駐輪場が少なくて困っています", "emotion_score": 7},
    {"category": "環境", "content": "公園の遊具が古くて危険です", "emotion_score": 8},
    {"category": "教育", "content": "図書館の開館時間を延長してほしい", "emotion_score": 5},
    {"category": "福祉", "content": "高齢者向けの施設をもっと増やしてほしい", "emotion_score": 6},
    {"category": "子育て", "content": "保育園の待機児童が多すぎます", "emotion_score": 9},
    {"category": "交通", "content": "バスの本数を増やしてください", "emotion_score": 6},
    {"category": "環境", "content": "ゴミ回収の頻度を増やしてほしい", "emotion_score": 5},
    {"category": "医療", "content": "夜間診療所が近くにありません", "emotion_score": 7},
    {"category": "防災", "content": "避難所の設備が不十分です", "emotion_score": 8},
    {"category": "その他", "content": "市役所の手続きがオンライン化されていない", "emotion_score": 4},
]

def create_test_data():
    """テストデータを作成"""
    with get_db() as db:
        # テストユーザー作成
        for i in range(5):
            line_id = f"test_user_{i}"
            user = db.query(User).filter(
                User.line_user_id_hash == hash_line_user_id(line_id)
            ).first()
            
            if not user:
                user_hash = hash_line_user_id(line_id)
                user = User(
                    line_user_id_hash=user_hash,
                    display_name=f"テストユーザー{i+1}",
                    age_range="30-39",
                    total_points=0
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        
        # テスト意見を作成
        users = db.query(User).all()
        
        for i, opinion_data in enumerate(test_opinions):
            # 日付をランダムに設定（過去7日間）
            days_ago = random.randint(0, 7)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            opinion = Opinion(
                user_id=random.choice(users).id,
                source_type=random.choice(['chat', 'free_form']),
                content=opinion_data['content'],
                category=opinion_data['category'],
                emotion_score=opinion_data['emotion_score'],
                priority_score=random.uniform(0.5, 1.0),
                created_at=created_at
            )
            db.add(opinion)
        
        db.commit()
        print(f"✓ Created {len(test_opinions)} test opinions")
        print(f"✓ Created {len(users)} test users")

if __name__ == "__main__":
    create_test_data()
