#!/usr/bin/env python3
"""AI分析v2のテストスクリプト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from features.ai_analysis_v2 import get_smart_analyzer

def test_smart_analysis():
    """スマート分析のテスト"""

    # テストデータ
    test_opinions = [
        {"id": 1, "text": "〇〇交差点の信号機が見づらくて危険です。特に朝の通学時間帯は児童が危ない目に遭っています。", "priority_score": 0.9},
        {"id": 2, "text": "同じく〇〇交差点の信号、雨の日は全然見えません。早急に改善してほしい。", "priority_score": 0.85},
        {"id": 3, "text": "通学路の横断歩道に白線が消えかけています。子供の安全のために塗り直しをお願いします。", "priority_score": 0.8},
        {"id": 4, "text": "公園の遊具が古くて錆びています。ブランコのチェーンが切れそうで心配です。", "priority_score": 0.7},
        {"id": 5, "text": "△△公園の砂場に猫のフンがあって不衛生です。定期的に清掃してください。", "priority_score": 0.6},
        {"id": 6, "text": "公園のトイレが汚いです。もっと清潔に保ってほしい。", "priority_score": 0.5},
        {"id": 7, "text": "ゴミ収集日が分かりにくいです。アプリで通知してくれるとありがたいです。", "priority_score": 0.4},
        {"id": 8, "text": "資源ごみの分別ルールが複雑すぎます。もっとシンプルにしてほしい。", "priority_score": 0.45},
        {"id": 9, "text": "不法投棄が多い場所があります。監視カメラの設置を検討してください。", "priority_score": 0.75},
        {"id": 10, "text": "市のホームページが見づらいです。もっと使いやすくしてほしい。", "priority_score": 0.3},
    ]

    print("=" * 60)
    print("AI分析v2 テスト実行")
    print("=" * 60)
    print(f"\n対象意見数: {len(test_opinions)}件\n")

    # 進捗コールバック
    def progress_callback(percent, message):
        print(f"[{percent:3d}%] {message}")

    # 分析実行
    analyzer = get_smart_analyzer()

    # Ollamaサービスチェック
    if not analyzer.llm_client.is_available():
        print("❌ エラー: Ollamaサービスが利用できません")
        print("   Ollamaを起動してから再度実行してください。")
        return False

    print("✓ Ollamaサービスは利用可能です\n")
    print("分析を開始します...\n")

    try:
        results = analyzer.analyze_opinions(
            test_opinions,
            max_topics=5,
            progress_callback=progress_callback
        )

        # 結果表示
        print("\n" + "=" * 60)
        print("分析結果")
        print("=" * 60)

        if "error" in results:
            print(f"❌ エラー: {results['error']}")
            return False

        print(f"\n📊 全体サマリー:")
        print(f"   {results.get('analysis_summary', '(なし)')}")

        print(f"\n🔍 検出されたトピック数: {len(results['topics'])}")
        print(f"📝 分析対象意見数: {results['total']}件\n")

        for i, topic in enumerate(results['topics'], 1):
            print(f"\n{'─' * 60}")
            print(f"トピック {i}: {topic['name']}")
            print(f"{'─' * 60}")
            print(f"  件数: {topic['count']}件")
            print(f"  緊急度: {topic['urgency_level']} ({topic['priority']})")
            print(f"  平均優先度: {topic['avg_priority_score']}")
            print(f"  キーワード: {', '.join(topic['keywords'])}")
            print(f"\n  📝 要約:")
            print(f"     {topic['summary']}")

            if topic['recommended_actions']:
                print(f"\n  ✅ 推奨アクション:")
                for j, action in enumerate(topic['recommended_actions'], 1):
                    print(f"     {j}. {action}")

            print(f"\n  含まれる意見 ({topic['count']}件):")
            for opinion in topic['opinions'][:3]:
                print(f"     - #{opinion['id']}: {opinion['text'][:60]}...")
            if topic['count'] > 3:
                print(f"     ... 他 {topic['count'] - 3}件")

        print("\n" + "=" * 60)
        print("✅ テスト完了")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_smart_analysis()
    sys.exit(0 if success else 1)
