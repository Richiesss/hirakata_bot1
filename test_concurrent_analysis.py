#!/usr/bin/env python3
"""同時実行制御のテスト"""

import sys
import os
import time
from multiprocessing import Process

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.analysis_lock import get_analysis_lock

def worker(worker_id, duration=3):
    """ワーカープロセス"""
    lock = get_analysis_lock()

    print(f"[Worker {worker_id}] ロック取得を試行中...")

    if lock.acquire(timeout=2):
        print(f"[Worker {worker_id}] ✓ ロック取得成功！")
        print(f"[Worker {worker_id}] {duration}秒間処理を実行...")
        time.sleep(duration)
        lock.release()
        print(f"[Worker {worker_id}] ✓ ロック解放完了")
    else:
        print(f"[Worker {worker_id}] ❌ ロック取得失敗（タイムアウト）")

def test_concurrent_access():
    """同時アクセスのテスト"""
    print("=" * 60)
    print("同時実行制御テスト")
    print("=" * 60)
    print("\n3つのプロセスを同時に起動します...")
    print("期待される動作:")
    print("  - 最初のプロセスがロックを取得")
    print("  - 2番目と3番目はタイムアウトで失敗")
    print("")

    # 3つのワーカーを同時起動
    workers = []
    for i in range(3):
        p = Process(target=worker, args=(i+1, 3))
        p.start()
        workers.append(p)
        time.sleep(0.1)  # 少しずらして起動

    # すべて完了を待つ
    for p in workers:
        p.join()

    print("\n" + "=" * 60)
    print("✅ テスト完了")
    print("=" * 60)

def test_lock_cleanup():
    """古いロックのクリーンアップテスト"""
    print("\n" + "=" * 60)
    print("古いロッククリーンアップテスト")
    print("=" * 60)

    lock = get_analysis_lock()

    # 手動でロックファイルを作成（古いタイムスタンプ）
    from datetime import datetime, timedelta
    import os

    lock_file = "/tmp/hirakata_analysis_locks/analysis.lock"
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)

    with open(lock_file, 'w') as f:
        f.write("99999\n")  # 存在しないPID
        old_time = datetime.now() - timedelta(minutes=15)
        f.write(f"{old_time.isoformat()}\n")

    print("古いロックファイルを作成しました（15分前のタイムスタンプ）")

    # ロック取得を試行（クリーンアップされるはず）
    if lock.acquire(timeout=2):
        print("✓ 古いロックが自動クリーンアップされ、新しいロックを取得できました")
        lock.release()
    else:
        print("❌ ロック取得に失敗")

    print("=" * 60)

if __name__ == "__main__":
    test_concurrent_access()
    test_lock_cleanup()
