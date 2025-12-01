#!/usr/bin/env python3
"""AI分析バッチ処理スクリプト

既存の意見データに対して優先度スコアを計算し、データベースを更新します。
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import get_db, Opinion
from features.ai_analysis import get_analyzer

def run_analysis():
    print("=== AI分析バッチ処理開始 ===\n")
    
    analyzer = get_analyzer()
    
    with get_db() as db:
        # 優先度スコアが未設定、または全件更新したい場合はフィルタを調整
        opinions = db.query(Opinion).all()
        print(f"対象件数: {len(opinions)}件")
        
        updated_count = 0
        
        for op in opinions:
            # 優先度スコア計算
            old_score = op.priority_score
            new_score = analyzer.calculate_priority_score(op.content)
            
            if old_score != new_score:
                op.priority_score = new_score
                updated_count += 1
                print(f"ID {op.id}: {old_score} -> {new_score} (Text: {op.content[:20]}...)")
        
        db.commit()
        print(f"\n更新完了: {updated_count}件")

    # トレンド分析テスト
    print("\n=== トレンド分析テスト ===")
    with get_db() as db:
        opinions = db.query(Opinion).all()
        opinion_dicts = [
            {
                "created_at": op.created_at,
                "priority_score": op.priority_score,
                "emotion_score": op.emotion_score
            }
            for op in opinions
        ]
        
        trends = analyzer.analyze_trends(opinion_dicts, period='monthly')
        if "error" in trends:
            print(f"エラー: {trends['error']}")
        else:
            print(f"分析対象: {trends['total_count']}件")
            for t in trends['trends']:
                print(f"期間: {t['period']}, 件数: {t['count']}, 平均優先度: {t['avg_priority']:.2f}")

if __name__ == "__main__":
    run_analysis()
