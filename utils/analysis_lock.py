"""AI分析の同時実行制御

複数ユーザーが同時に分析を実行した場合の競合を防ぐ
"""

import os
import time
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ロックファイルのパス
LOCK_DIR = "/tmp/hirakata_analysis_locks"
LOCK_FILE = os.path.join(LOCK_DIR, "analysis.lock")
MAX_LOCK_AGE_SECONDS = 600  # 10分でロックを自動解除


class AnalysisLock:
    """分析処理のロック管理"""

    def __init__(self):
        """初期化"""
        # ロックディレクトリを作成
        os.makedirs(LOCK_DIR, exist_ok=True)

    def acquire(self, timeout: int = 5) -> bool:
        """
        ロックを取得

        Args:
            timeout: タイムアウト秒数

        Returns:
            ロック取得成功したかどうか
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 古いロックをクリーンアップ
            self._cleanup_stale_lock()

            # ロックファイルが存在しない場合は取得
            if not os.path.exists(LOCK_FILE):
                try:
                    # 排他的にロックファイルを作成
                    with open(LOCK_FILE, 'x') as f:
                        f.write(f"{os.getpid()}\n")
                        f.write(f"{datetime.now().isoformat()}\n")

                    logger.info(f"Analysis lock acquired by PID {os.getpid()}")
                    return True

                except FileExistsError:
                    # 他のプロセスが先に取得した
                    pass

            # 少し待機
            time.sleep(0.5)

        logger.warning("Failed to acquire analysis lock (timeout)")
        return False

    def release(self):
        """ロックを解放"""
        try:
            if os.path.exists(LOCK_FILE):
                # 自分が取得したロックか確認
                with open(LOCK_FILE, 'r') as f:
                    pid = int(f.readline().strip())

                if pid == os.getpid():
                    os.remove(LOCK_FILE)
                    logger.info(f"Analysis lock released by PID {os.getpid()}")
                else:
                    logger.warning(f"Cannot release lock owned by PID {pid}")

        except Exception as e:
            logger.error(f"Error releasing lock: {e}")

    def _cleanup_stale_lock(self):
        """古いロックを削除"""
        try:
            if not os.path.exists(LOCK_FILE):
                return

            # ロックファイルの情報を読む
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.readline().strip())
                timestamp_str = f.readline().strip()

            # タイムスタンプをチェック
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp

            if age.total_seconds() > MAX_LOCK_AGE_SECONDS:
                logger.warning(f"Removing stale lock (age: {age.total_seconds()}s, PID: {pid})")
                os.remove(LOCK_FILE)

        except Exception as e:
            logger.error(f"Error cleaning up stale lock: {e}")
            # エラーの場合は念のためロックを削除
            try:
                os.remove(LOCK_FILE)
            except:
                pass

    def is_locked(self) -> bool:
        """
        現在ロックされているかチェック

        Returns:
            ロックされている場合True
        """
        if not os.path.exists(LOCK_FILE):
            return False

        # 古いロックは無視
        self._cleanup_stale_lock()

        return os.path.exists(LOCK_FILE)

    def get_lock_info(self) -> Optional[dict]:
        """
        ロック情報を取得

        Returns:
            {"pid": int, "timestamp": datetime} または None
        """
        try:
            if not os.path.exists(LOCK_FILE):
                return None

            with open(LOCK_FILE, 'r') as f:
                pid = int(f.readline().strip())
                timestamp_str = f.readline().strip()
                timestamp = datetime.fromisoformat(timestamp_str)

            return {
                "pid": pid,
                "timestamp": timestamp,
                "age_seconds": (datetime.now() - timestamp).total_seconds()
            }

        except Exception as e:
            logger.error(f"Error getting lock info: {e}")
            return None

    def __enter__(self):
        """コンテキストマネージャー対応"""
        if not self.acquire(timeout=10):
            raise RuntimeError("Failed to acquire analysis lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー対応"""
        self.release()


# シングルトンインスタンス
_lock_instance = None

def get_analysis_lock() -> AnalysisLock:
    """ロックインスタンスを取得"""
    global _lock_instance
    if _lock_instance is None:
        _lock_instance = AnalysisLock()
    return _lock_instance
