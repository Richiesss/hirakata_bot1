#!/usr/bin/env python3
"""スマート分析の統合テスト（admin_app.pyのロジックを検証）"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_integration():
    """統合テスト"""
    print("=" * 60)
    print("スマート分析統合テスト")
    print("=" * 60)

    # モジュールのインポートテスト
    try:
        from features.ai_analysis_v2 import get_smart_analyzer
        print("✓ ai_analysis_v2モジュールのインポート成功")
    except Exception as e:
        print(f"❌ ai_analysis_v2のインポート失敗: {e}")
        return False

    try:
        from features.ai_analysis import get_analyzer
        print("✓ ai_analysis（旧版）モジュールのインポート成功")
    except Exception as e:
        print(f"❌ ai_analysisのインポート失敗: {e}")
        return False

    # テストデータ
    test_opinions = [
        {"id": 1, "text": "信号機が見えにくい", "priority_score": 0.9, "category": "交通"},
        {"id": 2, "text": "公園が汚い", "priority_score": 0.6, "category": "環境"},
        {"id": 3, "text": "ゴミ収集日が分からない", "priority_score": 0.4, "category": "環境"},
    ]

    print("\nテストデータ: 3件の意見")

    # スマート分析のテスト
    print("\n--- スマート分析（新版）のテスト ---")
    try:
        analyzer = get_smart_analyzer()

        if not analyzer.llm_client.is_available():
            print("❌ Ollamaサービスが利用できません")
            print("   管理画面での実行前にOllamaを起動してください。")
            return False

        results = analyzer.analyze_opinions(test_opinions, max_topics=3)

        # 結果の検証
        if "error" in results:
            print(f"❌ 分析エラー: {results['error']}")
            return False

        print("✓ 分析成功")
        print(f"  - モード: {results.get('mode', 'smart')}")
        print(f"  - トピック数: {len(results.get('topics', []))}")
        print(f"  - 合計意見数: {results.get('total', 0)}")
        print(f"  - plot_imageキー: {'plot_image' in results}")

        # 重要: plot_imageがないことを確認
        if 'plot_image' in results:
            print("⚠️  警告: スマート分析にplot_imageが含まれています（不要）")
        else:
            print("✓ plot_imageなし（正常）")

        # トピック構造の確認
        topics = results.get('topics', [])
        if topics:
            print(f"\n✓ トピック例:")
            topic = topics[0]
            print(f"  - 名前: {topic.get('name', '(なし)')}")
            print(f"  - 件数: {topic.get('count', 0)}")
            print(f"  - 緊急度: {topic.get('urgency_level', '(なし)')}")
            print(f"  - 優先度: {topic.get('priority', '(なし)')}")
            print(f"  - 要約: {topic.get('summary', '(なし)')[:50]}...")

    except Exception as e:
        print(f"❌ スマート分析でエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ 統合テスト完了")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. 管理画面にアクセス: http://localhost:5001/admin/analysis")
    print("2. 「スマート分析 (新版)」ボタンをクリック")
    print("3. 結果を確認")

    return True

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
