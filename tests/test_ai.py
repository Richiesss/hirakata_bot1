import pytest
from features.ai_analysis import OpinionAnalyzer

# AIモデルのロードをスキップするためのモック（必要に応じて）
# ここではcalculate_priority_scoreはモデルを使わないのでそのままテスト

def test_priority_score_high():
    """優先度スコア（高）のテスト"""
    analyzer = OpinionAnalyzer()
    # モデルロードを回避するために__init__をバイパスするか、
    # calculate_priority_scoreがself.modelを使わないことを利用
    
    text = "道路が陥没していて非常に危険です。至急対応をお願いします。"
    score = analyzer.calculate_priority_score(text)
    assert score == 1.0

def test_priority_score_medium():
    """優先度スコア（中）のテスト"""
    analyzer = OpinionAnalyzer()
    text = "ゴミ収集の時間を変更してほしいという要望があります。"
    score = analyzer.calculate_priority_score(text)
    assert score >= 0.5

def test_priority_score_low():
    """優先度スコア（低）のテスト"""
    analyzer = OpinionAnalyzer()
    text = "こんにちは。いい天気ですね。"
    score = analyzer.calculate_priority_score(text)
    assert score == 0.2
