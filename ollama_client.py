"""Ollama LLMクライアント

対話モード、要約モード、分類モードに対応したLLMクライアント
"""

import ollama
import json
import logging
from typing import List, Dict, Optional
from config import (
    OLLAMA_MODEL,
    OLLAMA_URL,
    OLLAMA_TIMEOUT,
    SYSTEM_PROMPT_CHAT,
    SYSTEM_PROMPT_SUMMARY
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama LLMクライアント"""
    
    def __init__(self):
        """初期化"""
        self.model = OLLAMA_MODEL
        self.base_url = OLLAMA_URL
        self.timeout = OLLAMA_TIMEOUT
        
        # Ollamaクライアント設定
        self.client = ollama.Client(host=self.base_url)
        logger.info(f"Ollama client initialized with model: {self.model}")
    
    def chat_mode(self, user_message: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        対話モード: 市民との対話で意見を引き出す
        
        Args:
            user_message: ユーザーのメッセージ
            chat_history: 過去の対話履歴 [{"role": "user"|"assistant", "content": "..."}]
        
        Returns:
            LLMの応答（150文字以内の質問・傾聴）
        """
        try:
            # メッセージ履歴の構築
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_CHAT}
            ]
            
            # 過去の履歴を追加
            if chat_history:
                messages.extend(chat_history)
            
            # 現在のユーザーメッセージを追加
            messages.append({"role": "user", "content": user_message})
            
            # Ollama呼び出し
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.7,  # 対話モードは創造性を持たせる
                    "num_predict": 200,  # 最大トークン数
                }
            )
            
            assistant_message = response['message']['content'].strip()
            logger.info(f"Chat mode response generated: {len(assistant_message)} chars")
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error in chat_mode: {e}")
            return "申し訳ございません。少し時間をおいてもう一度お試しください。"
    
    def summary_mode(self, chat_history: List[Dict[str, str]]) -> Optional[Dict]:
        """
        要約モード: 対話ログから構造化データを抽出
        
        Args:
            chat_history: 対話履歴
        
        Returns:
            {
                "summary": "要約文",
                "category": "カテゴリ",
                "emotion_score": 感情スコア
            }
        """
        try:
            # 対話ログをテキスト化
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in chat_history
                if msg['role'] in ['user', 'assistant']
            ])
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_SUMMARY},
                {"role": "user", "content": f"以下の対話ログを要約してください:\n\n{conversation_text}"}
            ]
            
            # Ollama呼び出し（temperature=0.0で決定的な出力）
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.0,
                    "num_predict": 300,
                },
                format="json"  # JSON形式での出力を要求
            )
            
            # JSON解析
            result_text = response['message']['content'].strip()
            result = json.loads(result_text)
            
            logger.info(f"Summary generated: {result.get('summary', '')[:50]}...")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in summary_mode: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in summary_mode: {e}")
            return None
    
    def classify_opinion(self, opinion_text: str) -> Optional[Dict]:
        """
        分類モード: 意見をカテゴリ分類し、感情スコアを付与
        
        Args:
            opinion_text: 分類対象の意見文
        
        Returns:
            {
                "category": "カテゴリ",
                "emotion_score": 感情スコア
            }
        """
        try:
            classify_prompt = """以下の市民の意見を分析し、カテゴリと感情スコアをJSON形式で出力してください。

カテゴリは以下から選択:
- 交通
- 福祉
- 教育
- 環境
- 子育て
- 医療
- 防災
- その他

感情スコアは0-10の整数（10が最も強い不満・要望）

出力形式:
{
  "category": "カテゴリ名",
  "emotion_score": 感情スコア
}
"""
            
            messages = [
                {"role": "system", "content": classify_prompt},
                {"role": "user", "content": opinion_text}
            ]
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": 0.0,
                    "num_predict": 100,
                },
                format="json"
            )
            
            result_text = response['message']['content'].strip()
            result = json.loads(result_text)
            
            logger.info(f"Opinion classified: {result.get('category')} (score: {result.get('emotion_score')})")
            return result
            
        except Exception as e:
            logger.error(f"Error in classify_opinion: {e}")
            return None
    
    def is_available(self) -> bool:
        """Ollamaサービスの死活確認"""
        try:
            # モデル一覧取得で接続確認
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama service not available: {e}")
            return False


# シングルトンインスタンス
_ollama_client = None

def get_ollama_client() -> OllamaClient:
    """Ollamaクライアントのシングルトンインスタンスを取得"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


if __name__ == "__main__":
    # テスト実行
    client = OllamaClient()
    
    if client.is_available():
        print("✓ Ollama service is available")
        
        # 対話モードテスト
        response = client.chat_mode("公園の遊具が古くて心配です")
        print(f"\n[Chat mode test]\nResponse: {response}")
        
        # 要約モードテスト
        test_history = [
            {"role": "user", "content": "公園の遊具が古くて心配です"},
            {"role": "assistant", "content": "具体的にどの公園の、どのような遊具でしょうか?"},
            {"role": "user", "content": "枚方公園のブランコです。錆びていて危ないと思います"}
        ]
        summary = client.summary_mode(test_history)
        print(f"\n[Summary mode test]\nResult: {summary}")
    else:
        print("✗ Ollama service is not available")
