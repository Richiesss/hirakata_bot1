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
        sns.set(style="whitegrid", font="IPAGothic") # 日本語フォントがあれば指定したいが、環境による
        
        # データをDataFrameに変換してプロットしやすくする
        x = [d["x"] for d in data]
        y = [d["y"] for d in data]
        clusters = [d["cluster"] for d in data]
        
        scatter = plt.scatter(x, y, c=clusters, cmap='viridis', s=100, alpha=0.7)
        plt.colorbar(scatter, label='Cluster')
        plt.title('意見の分布 (AI分析結果)')
        plt.xlabel('Dimension 1')
        plt.ylabel('Dimension 2')
        
        # 画像をバッファに保存
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return img_str

# シングルトンインスタンス（ロード時間を節約するため）
_analyzer_instance = None

def get_analyzer():
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = OpinionAnalyzer()
    return _analyzer_instance
