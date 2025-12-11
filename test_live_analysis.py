#!/usr/bin/env python3
"""ライブ環境での分析テスト（実際のDBデータを使用）"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import get_db, Opinion

def test_with_real_data():
    """実際のDBデータで分析テスト"""
    print("=" * 60)
    print("実データでの分析テスト")
    print("=" * 60)

    try:
        with get_db() as db:
            # 最新5件のみ取得（高速テスト）
            opinions = db.query(Opinion).order_by(Opinion.created_at.desc()).limit(5).all()

            if not opinions:
                print("❌ データベースに意見がありません")
                return False

            print(f"\n✓ データベースから{len(opinions)}件取得")

            opinion_data = [
                {
                    "id": op.id,
                    "text": op.content,
                    "priority_score": op.priority_score if op.priority_score else 0.5,
                    "category": op.category if op.category else "その他"
                }
                for op in opinions
                if len(op.content) > 5
            ]

            print(f"✓ 有効な意見: {len(opinion_data)}件")

            # スマート分析実行
            from features.ai_analysis_v2 import get_smart_analyzer

            analyzer = get_smart_analyzer()

            if not analyzer.llm_client.is_available():
                print("❌ Ollamaが利用できません")
                return False

            print("✓ Ollama接続OK")
            print("\n分析開始...")

            def progress(percent, msg):
                print(f"  [{percent:3d}%] {msg}")

            results = analyzer.analyze_opinions(
                opinion_data,
                max_topics=3,
                progress_callback=progress
            )

            if "error" in results:
                print(f"\n❌ 分析エラー: {results['error']}")
                return False

            print("\n✓ 分析成功！")
            print(f"  - モード: {results.get('mode', 'smart')}")
            print(f"  - トピック数: {len(results.get('topics', []))}")
            print(f"  - 合計: {results.get('total', 0)}件")
            print(f"  - plot_imageキー: {'plot_image' in results}")

            if 'plot_image' in results:
                print("  ⚠️  警告: plot_imageが含まれています")
                return False

            print("\n" + "=" * 60)
            print("✅ テスト成功 - admin_app.pyでも動作するはずです")
            print("=" * 60)
            return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_real_data()
    sys.exit(0 if success else 1)
