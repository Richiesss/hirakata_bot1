"""AI分析 v2: LLMベースのトピック抽出と要約

BERTクラスタリングの代わりに、LLMを使った直感的な分析を提供
- 自動トピック抽出
- 各トピックの要約
- 優先度判定
- 市職員向けの実用的なダッシュボード
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json

from ollama_client import get_ollama_client

logger = logging.getLogger(__name__)


class SmartOpinionAnalyzer:
    """LLMベースの意見分析クラス"""

    def __init__(self):
        """初期化"""
        self.llm_client = get_ollama_client()
        logger.info("SmartOpinionAnalyzer initialized")

    def analyze_opinions(
        self,
        opinions: List[Dict[str, Any]],
        max_topics: int = 7,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        意見を分析し、トピックごとに整理する

        Args:
            opinions: [{"id": 1, "text": "...", "priority_score": 0.8, ...}, ...]
            max_topics: 最大トピック数
            progress_callback: func(percent: int, message: str)

        Returns:
            {
                "topics": [
                    {
                        "id": 0,
                        "name": "通学路の安全性",
                        "summary": "〇〇交差点の信号が見づらく...",
                        "count": 15,
                        "priority": "high",
                        "urgency_level": "緊急",
                        "opinions": [...],
                        "keywords": ["信号機", "横断歩道", "通学路"]
                    },
                    ...
                ],
                "total": 100,
                "analysis_summary": "全体的な傾向の要約"
            }
        """
        if not opinions:
            return {"error": "分析対象の意見がありません"}

        logger.info(f"Analyzing {len(opinions)} opinions with LLM...")

        if progress_callback:
            progress_callback(5, "意見データを準備中...")

        # 1. LLMでトピック抽出 (5% - 40%)
        topics_data = self._extract_topics(opinions, max_topics, progress_callback)

        if not topics_data:
            return {"error": "トピック抽出に失敗しました"}

        # 2. 各トピックに意見を割り当て (40% - 70%)
        topics_with_opinions = self._assign_opinions_to_topics(
            opinions,
            topics_data,
            progress_callback
        )

        # 3. 各トピックの要約と優先度判定 (70% - 95%)
        enriched_topics = self._enrich_topics(topics_with_opinions, progress_callback)

        # 4. 全体サマリー生成 (95% - 100%)
        if progress_callback:
            progress_callback(95, "全体サマリーを生成中...")

        overall_summary = self._generate_overall_summary(enriched_topics)

        if progress_callback:
            progress_callback(100, "分析完了！")

        return {
            "topics": enriched_topics,
            "total": len(opinions),
            "analysis_summary": overall_summary
        }

    def _extract_topics(
        self,
        opinions: List[Dict],
        max_topics: int,
        progress_callback=None
    ) -> Optional[List[Dict]]:
        """
        LLMを使ってトピックを抽出

        Returns:
            [
                {"name": "通学路の安全性", "description": "..."},
                ...
            ]
        """
        if progress_callback:
            progress_callback(10, "トピックを抽出中...")

        # サンプリング（大量データの場合は代表的なものを抽出）
        sample_size = min(100, len(opinions))
        sampled_opinions = opinions[:sample_size]

        # 意見テキストを結合
        opinion_texts = [op["text"][:100] for op in sampled_opinions]  # 最初の100文字のみ
        combined_text = "\n".join([f"- {text}" for text in opinion_texts])

        prompt = f"""以下は市民から寄せられた{len(opinions)}件の意見の一部です。
これらの意見を分析し、共通するテーマ（トピック）を{max_topics}個以内で抽出してください。

【意見サンプル】
{combined_text}

【出力形式】
以下のJSON形式で出力してください：
{{
  "topics": [
    {{
      "name": "トピック名（10文字以内で分かりやすく）",
      "description": "このトピックの詳細説明（30文字程度）",
      "keywords": ["キーワード1", "キーワード2", "キーワード3"]
    }},
    ...
  ]
}}

重要:
- トピック名は市役所職員が一目で理解できる具体的な名前にしてください
- 似たテーマはまとめてください
- 件数が少ないマイナーなトピックも重要であれば含めてください
- JSON以外の説明文は不要です
"""

        try:
            messages = [
                {"role": "system", "content": "あなたは市民の意見を分析する専門家です。"},
                {"role": "user", "content": prompt}
            ]

            response = self.llm_client.client.chat(
                model=self.llm_client.model,
                messages=messages,
                options={
                    "temperature": 0.3,
                    "num_predict": 1000,
                },
                format="json"
            )

            result_text = response['message']['content'].strip()
            result = json.loads(result_text)

            topics = result.get("topics", [])
            logger.info(f"Extracted {len(topics)} topics")

            return topics

        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return None

    def _assign_opinions_to_topics(
        self,
        opinions: List[Dict],
        topics_data: List[Dict],
        progress_callback=None
    ) -> List[Dict]:
        """
        各意見を適切なトピックに分類

        キーワードマッチングとLLM判定を組み合わせる
        """
        if progress_callback:
            progress_callback(50, "意見をトピック別に分類中...")

        # トピック初期化
        topics = []
        for i, topic in enumerate(topics_data):
            topics.append({
                "id": i,
                "name": topic["name"],
                "description": topic.get("description", ""),
                "keywords": topic.get("keywords", []),
                "opinions": [],
                "count": 0
            })

        # LLMを使って各意見をトピックに分類（少量の場合）
        # 大量の場合はキーワードマッチングで分類
        if len(opinions) <= 50:
            # 少量データの場合はLLMで精密に分類
            topics = self._classify_with_llm(opinions, topics_data)
        else:
            # キーワードベースで大まかに分類
            for opinion in opinions:
                text = opinion["text"]
                best_match = None
                best_score = 0

                # 各トピックとのマッチング
                for topic in topics:
                    score = 0
                    for keyword in topic.get("keywords", []):
                        if keyword in text:
                            score += 1

                    if score > best_score:
                        best_score = score
                        best_match = topic

                # マッチしたトピックに追加（マッチしない場合は最初のトピックに入れる）
                if best_match:
                    best_match["opinions"].append(opinion)
                    best_match["count"] += 1
                else:
                    # マッチしない場合は「その他」として最後のトピックに
                    topics[-1]["opinions"].append(opinion)
                    topics[-1]["count"] += 1

        # 空のトピックを除外
        topics = [t for t in topics if t["count"] > 0]

        return topics

    def _classify_with_llm(
        self,
        opinions: List[Dict],
        topics_data: List[Dict]
    ) -> List[Dict]:
        """
        LLMを使って各意見を適切なトピックに分類（少量データ向け）
        """
        # トピック初期化
        topics = []
        for i, topic in enumerate(topics_data):
            topics.append({
                "id": i,
                "name": topic["name"],
                "description": topic.get("description", ""),
                "keywords": topic.get("keywords", []),
                "opinions": [],
                "count": 0
            })

        # トピック一覧を文字列化
        topic_list = "\n".join([
            f"{i}. {t['name']}: {t['description']}"
            for i, t in enumerate(topics_data)
        ])

        # バッチで分類（5件ずつ）
        batch_size = 5
        for i in range(0, len(opinions), batch_size):
            batch = opinions[i:i+batch_size]
            opinion_texts = "\n".join([
                f"[{j}] {op['text'][:100]}"
                for j, op in enumerate(batch)
            ])

            prompt = f"""以下の意見を、適切なトピックに分類してください。

【トピック一覧】
{topic_list}

【意見】
{opinion_texts}

【出力形式】
以下のJSON形式で出力してください：
{{
  "classifications": [
    {{"opinion_index": 0, "topic_id": 2}},
    {{"opinion_index": 1, "topic_id": 0}},
    ...
  ]
}}

opinion_indexは意見の番号（0から開始）、topic_idはトピックの番号（0から開始）です。
"""

            try:
                messages = [
                    {"role": "system", "content": "あなたは意見を分類する専門家です。"},
                    {"role": "user", "content": prompt}
                ]

                response = self.llm_client.client.chat(
                    model=self.llm_client.model,
                    messages=messages,
                    options={
                        "temperature": 0.1,
                        "num_predict": 500,
                    },
                    format="json"
                )

                result_text = response['message']['content'].strip()
                result = json.loads(result_text)

                # 分類結果を反映
                for classification in result.get("classifications", []):
                    opinion_idx = classification.get("opinion_index")
                    topic_id = classification.get("topic_id")

                    if opinion_idx is not None and topic_id is not None:
                        if 0 <= opinion_idx < len(batch) and 0 <= topic_id < len(topics):
                            topics[topic_id]["opinions"].append(batch[opinion_idx])
                            topics[topic_id]["count"] += 1

            except Exception as e:
                logger.error(f"Error classifying batch: {e}")
                # エラー時は最初のトピックに入れる
                for op in batch:
                    topics[0]["opinions"].append(op)
                    topics[0]["count"] += 1

        # 空のトピックを除外
        topics = [t for t in topics if t["count"] > 0]
        return topics

    def _enrich_topics(
        self,
        topics: List[Dict],
        progress_callback=None
    ) -> List[Dict]:
        """
        各トピックを要約し、優先度を判定
        """
        enriched = []
        total = len(topics)

        for i, topic in enumerate(topics):
            if progress_callback:
                progress = 70 + int((i / total) * 25)
                progress_callback(progress, f"トピック {i+1}/{total} を分析中...")

            # 意見テキストをサンプリング（最大10件）
            sample_opinions = topic["opinions"][:10]
            opinion_texts = "\n".join([f"- {op['text']}" for op in sample_opinions])

            prompt = f"""以下は「{topic['name']}」に関する市民の意見です。

【意見】
{opinion_texts}

【タスク】
以下の情報を分析してJSON形式で出力してください：

1. summary: この意見群の要約（100文字以内、市職員向けに具体的に）
2. urgency_level: 緊急度（"緊急", "高", "中", "低"のいずれか）
3. recommended_actions: 推奨される対応アクション（3つ以内のリスト）

【出力形式】
{{
  "summary": "要約文",
  "urgency_level": "緊急度",
  "recommended_actions": ["アクション1", "アクション2", "アクション3"]
}}
"""

            try:
                messages = [
                    {"role": "system", "content": "あなたは市役所の政策立案を支援する分析官です。"},
                    {"role": "user", "content": prompt}
                ]

                response = self.llm_client.client.chat(
                    model=self.llm_client.model,
                    messages=messages,
                    options={
                        "temperature": 0.2,
                        "num_predict": 500,
                    },
                    format="json"
                )

                result_text = response['message']['content'].strip()
                result = json.loads(result_text)

                # 優先度スコアを計算
                priority_map = {"緊急": "critical", "高": "high", "中": "medium", "低": "low"}
                urgency = result.get("urgency_level", "中")
                priority = priority_map.get(urgency, "medium")

                # 平均優先度スコアも計算
                avg_priority = sum([op.get("priority_score", 0.5) for op in topic["opinions"]]) / len(topic["opinions"])

                enriched.append({
                    **topic,
                    "summary": result.get("summary", "要約なし"),
                    "urgency_level": urgency,
                    "priority": priority,
                    "avg_priority_score": round(avg_priority, 2),
                    "recommended_actions": result.get("recommended_actions", [])
                })

            except Exception as e:
                logger.error(f"Error enriching topic {topic['name']}: {e}")
                # エラー時はデフォルト値
                enriched.append({
                    **topic,
                    "summary": "要約を生成できませんでした",
                    "urgency_level": "中",
                    "priority": "medium",
                    "avg_priority_score": 0.5,
                    "recommended_actions": []
                })

        # 優先度順にソート（緊急度 → 件数）
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        enriched.sort(key=lambda x: (priority_order.get(x["priority"], 2), -x["count"]))

        return enriched

    def _generate_overall_summary(self, topics: List[Dict]) -> str:
        """全体サマリーを生成"""
        try:
            # トピック情報をまとめる
            topic_summaries = []
            for topic in topics:
                topic_summaries.append(
                    f"【{topic['name']}】({topic['count']}件, {topic['urgency_level']})\n{topic['summary'][:50]}..."
                )

            combined = "\n\n".join(topic_summaries)

            prompt = f"""以下は市民意見の分析結果です。全体的な傾向を50文字程度で要約してください。

{combined}

要約（50文字以内）:
"""

            messages = [
                {"role": "system", "content": "簡潔に要点をまとめてください。"},
                {"role": "user", "content": prompt}
            ]

            response = self.llm_client.client.chat(
                model=self.llm_client.model,
                messages=messages,
                options={"temperature": 0.2, "num_predict": 100}
            )

            summary = response['message']['content'].strip()
            return summary

        except Exception as e:
            logger.error(f"Error generating overall summary: {e}")
            return "市民から様々な意見が寄せられています。"


# シングルトンインスタンス
_smart_analyzer_instance = None

def get_smart_analyzer():
    """スマート分析器のシングルトンインスタンスを取得"""
    global _smart_analyzer_instance
    if _smart_analyzer_instance is None:
        _smart_analyzer_instance = SmartOpinionAnalyzer()
    return _smart_analyzer_instance
