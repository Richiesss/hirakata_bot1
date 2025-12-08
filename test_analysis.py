#!/usr/bin/env python3
"""AI分析機能のテストスクリプト"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import get_db, Opinion
from features.ai_analysis import get_analyzer

def test_analysis():
    """少量データでAI分析をテスト"""
    print("=" * 60)
    print("AI分析機能テスト")
    print("=" * 60)

    # データベースから意見を取得
    print("\n1. データベースから意見を取得中...")
    with get_db() as db:
        opinions = db.query(Opinion).order_by(Opinion.created_at.desc()).limit(20).all()

        if not opinions:
            print("❌ エラー: 意見データがありません")
            return False

        opinion_data = [
            {"id": op.id, "text": op.content}
            for op in opinions
            if len(op.content) > 5
        ]

    print(f"✓ {len(opinion_data)}件の意見を取得しました")

    # 分析実行
    print("\n2. AI分析を実行中...")
    print("   （初回はモデルのダウンロードに時間がかかる場合があります）")

    try:
        analyzer = get_analyzer()
        results = analyzer.analyze_opinions(opinion_data)

        if "error" in results:
            print(f"❌ 分析エラー: {results['error']}")
            return False

        print(f"✓ 分析が完了しました")
        print(f"  - 分析対象: {results.get('total', 0)}件")
        print(f"  - クラスタ数: {len(results.get('clusters', {}))}")

        # クラスタ詳細を表示
        print("\n3. クラスタ詳細:")
        for label, cluster in results.get('clusters', {}).items():
            print(f"  - Group {label}: {cluster.get('count', 0)}件")
            print(f"    代表意見: {cluster.get('representative', 'N/A')}")

        # 画像が生成されたか確認
        if 'plot_image' in results:
            print(f"\n✓ プロット画像が生成されました（{len(results['plot_image'])}バイト）")
        else:
            print("\n❌ プロット画像が生成されませんでした")

        print("\n" + "=" * 60)
        print("✅ テスト成功！AI分析は正常に動作しています")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_analysis()
    sys.exit(0 if success else 1)
