import logging
import numpy as np
from typing import List, Dict, Any
import io
import base64
import matplotlib

# バックエンドをAggに設定（GUIなし環境用）
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

# PyTorch関連のインポートを遅延させるか、try-exceptで囲む
try:
    import torch
    from transformers import BertJapaneseTokenizer, BertModel
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt
    import seaborn as sns
    PYTORCH_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import AI libraries: {e}")
    PYTORCH_AVAILABLE = False

class OpinionAnalyzer:
    def __init__(self, model_name: str = "cl-tohoku/bert-base-japanese-v3"):
        """
        初期化
        Args:
            model_name: 使用するBERTモデル名
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("AI analysis libraries (torch, transformers, etc.) are not installed.")
            
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        self.model_name = model_name
        self.model = None
        self.tokenizer = None

    def _load_model(self, progress_callback=None):
        """モデルをロードする"""
        if self.model is not None:
            return

        try:
            if progress_callback:
                progress_callback(10, "モデルを読み込んでいます...")
            
            logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = BertJapaneseTokenizer.from_pretrained(self.model_name)
            
            if progress_callback:
                progress_callback(20, "モデルをGPU/CPUに展開しています...")
                
            self.model = BertModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval() # 推論モード
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def compute_embeddings(self, texts: List[str], batch_size: int = 32, progress_callback=None) -> np.ndarray:
        """
        テキストリストから埋め込みベクトルを計算
        """
        # モデルロード確認
        self._load_model(progress_callback)
        
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        # バッチ処理
        for i in range(0, len(texts), batch_size):
            batch_idx = i // batch_size
            if progress_callback:
                # 30%〜70%の間で進捗を表示
                progress = 30 + int((batch_idx / total_batches) * 40)
                progress_callback(progress, f"ベクトル化を実行中 ({batch_idx+1}/{total_batches})...")
            
            batch_texts = texts[i:i + batch_size]
            
            try:
                # トークナイズ
                inputs = self.tokenizer(
                    batch_texts, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True, 
                    max_length=128
                ).to(self.device)
                
                # 推論
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                # CLSトークンのベクトルを取得 (batch_size, hidden_size)
                cls_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                all_embeddings.append(cls_embeddings)
                
            except Exception as e:
                logger.error(f"Error computing embeddings for batch {i}: {e}")
                continue
                
        if not all_embeddings:
            return np.array([])
            
        return np.concatenate(all_embeddings, axis=0)

    def analyze_opinions(self, opinions: List[Dict[str, Any]], n_clusters: int = 5, progress_callback=None) -> Dict[str, Any]:
        """
        意見リストを分析し、クラスタリング結果と可視化データを返す
        Args:
            opinions: [{"id": 1, "text": "...", ...}, ...]
            n_clusters: クラスタ数
            progress_callback: func(percent: int, message: str)
        """
        if not opinions:
            return {"error": "No opinions to analyze"}
            
        texts = [op["text"] for op in opinions]
        ids = [op["id"] for op in opinions]
        
        logger.info(f"Analyzing {len(texts)} opinions...")
        
        if progress_callback:
            progress_callback(5, "分析を開始します...")
        
        # 1. ベクトル化 (10% - 70%)
        embeddings = self.compute_embeddings(texts, progress_callback=progress_callback)
        if len(embeddings) == 0:
            return {"error": "Failed to compute embeddings"}
            
        # 2. クラスタリング (K-Means) (70% - 85%)
        if progress_callback:
            progress_callback(75, "クラスタリングを実行中...")
            
        # データ数がクラスタ数より少ない場合は調整
        actual_n_clusters = min(n_clusters, len(texts))
        if actual_n_clusters < 2:
             return {"error": "Not enough data for clustering"}

        kmeans = KMeans(n_clusters=actual_n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # 3. 次元圧縮 (可視化用) (85% - 95%)
        if progress_callback:
            progress_callback(85, "可視化データを生成中...")
            
        # データ数に応じてPCAかt-SNEを選択
        if len(texts) > 50:
            reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(texts)-1))
        else:
            reducer = PCA(n_components=2, random_state=42)
            
        coords = reducer.fit_transform(embeddings)
        
        # 4. 結果の整形
        if progress_callback:
            progress_callback(95, "結果をまとめています...")
            
        results = []
        clusters = {}
        
        for i, (text, label, coord, op_id) in enumerate(zip(texts, cluster_labels, coords, ids)):
            # クラスタごとの情報を集約
            label_str = str(label)
            if label_str not in clusters:
                clusters[label_str] = {"count": 0, "keywords": [], "texts": []}
            
            clusters[label_str]["count"] += 1
            clusters[label_str]["texts"].append(text)
            
            results.append({
                "id": op_id,
                "text": text,
                "cluster": int(label),
                "x": float(coord[0]),
                "y": float(coord[1])
            })
            
        # クラスタごとの特徴語抽出
        for label in clusters:
            clusters[label]["representative"] = clusters[label]["texts"][0][:20] + "..."

        # 5. プロット生成
        plot_image = self._generate_plot(results, actual_n_clusters)
        
        if progress_callback:
            progress_callback(100, "完了しました！")
        
        return {
            "clusters": clusters,
            "data": results,
            "plot_image": plot_image,
            "total": len(texts)
        }

    def _generate_plot(self, data: List[Dict], n_clusters: int) -> str:
        """
        散布図を生成しBase64文字列で返す
        """
        plt.figure(figsize=(10, 8))
        
        # 日本語フォント設定
        import matplotlib.font_manager as fm
        import os
        
        # システムにインストールされたNoto Sans CJKを使用
        font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
        if os.path.exists(font_path):
            fm.fontManager.addfont(font_path)
            plt.rcParams['font.family'] = 'Noto Sans CJK JP'
            sns.set(style="whitegrid", font="Noto Sans CJK JP")
        else:
            # フォールバック（他のパスも試す）
            font_path_alt = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'
            if os.path.exists(font_path_alt):
                fm.fontManager.addfont(font_path_alt)
                plt.rcParams['font.family'] = 'Noto Sans CJK JP'
                sns.set(style="whitegrid", font="Noto Sans CJK JP")
            else:
                sns.set(style="whitegrid", font="IPAGothic") # 最終フォールバック

        
        # データをDataFrameに変換してプロットしやすくする
        x = [d["x"] for d in data]
        y = [d["y"] for d in data]
        clusters = [d["cluster"] for d in data]
        
        scatter = plt.scatter(x, y, c=clusters, cmap='viridis', s=100, alpha=0.7)
        plt.colorbar(scatter, label='Cluster')
        plt.title('意見の分布 (AI分析結果)')
        plt.xlabel('次元 1')
        plt.ylabel('次元 2')
        
        # 画像をバッファに保存
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return img_str

    def calculate_priority_score(self, text: str) -> float:
        """
        意見の優先度スコアを計算する (0.0 - 1.0)
        
        Args:
            text: 意見テキスト
            
        Returns:
            float: 優先度スコア
        """
        score = 0.2  # デフォルト（低）
        
        # キーワードベースのヒューリスティック
        critical_keywords = ['危険', '事故', '緊急', '犯罪', '火災', '倒壊', '命', '死', '怪我', '救急']
        high_keywords = ['困る', '被害', '苦情', '破損', '汚染', '騒音', '悪臭', '不法投棄', '暴力']
        medium_keywords = ['要望', '提案', '不便', '改善', '欲しい', '足りない', '遅い', '高い']
        
        for kw in critical_keywords:
            if kw in text:
                return 1.0  # 即時対応レベル
                
        for kw in high_keywords:
            if kw in text:
                score = max(score, 0.8)
                
        for kw in medium_keywords:
            if kw in text:
                score = max(score, 0.5)
                
        # 文字数による加点（長文は熱量が高い可能性があるため、少し加点）
        if len(text) > 100:
            score = min(score + 0.1, 1.0)
            
        return score

    def analyze_trends(self, opinions: List[Dict[str, Any]], period: str = 'monthly') -> Dict[str, Any]:
        """
        意見のトレンド分析を行う
        
        Args:
            opinions: 意見リスト [{"created_at": datetime, "priority_score": float, ...}]
            period: 集計期間 'monthly' or 'daily'
            
        Returns:
            トレンド分析結果
        """
        if not opinions:
            return {"error": "No opinions to analyze"}
            
        from collections import defaultdict
        import pandas as pd
        
        # データフレーム作成
        df = pd.DataFrame(opinions)
        if 'created_at' not in df.columns:
            return {"error": "Missing 'created_at' in opinions"}
            
        # 日付変換
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # 期間設定
        if period == 'monthly':
            df['period'] = df['created_at'].dt.to_period('M').astype(str)
        else:
            df['period'] = df['created_at'].dt.to_period('D').astype(str)
            
        # 集計
        trend_data = []
        grouped = df.groupby('period')
        
        for name, group in grouped:
            period_stats = {
                "period": name,
                "count": len(group),
                "avg_priority": float(group['priority_score'].mean()) if 'priority_score' in group.columns else 0.0,
                "avg_emotion": float(group['emotion_score'].mean()) if 'emotion_score' in group.columns else 0.0
            }
            trend_data.append(period_stats)
            
        return {
            "trends": trend_data,
            "total_count": len(opinions)
        }

# シングルトンインスタンス（ロード時間を節約するため）
_analyzer_instance = None

def get_analyzer():
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = OpinionAnalyzer()
    return _analyzer_instance
