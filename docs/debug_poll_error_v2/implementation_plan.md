# OOMエラー解決計画

## 問題の概要
AI分析機能の実行中に「Internal Server Error」が発生しています。ログを確認したところ、`SIGKILL`と"Perhaps out of memory?"というメッセージが記録されており、メモリ不足によりプロセスが強制終了されていることがわかりました。
現在、Gunicornの設定では `multiprocessing.cpu_count() * 2 + 1` 個のワーカーを起動するように設定されています。CPUsが8個の場合、17個のワーカーが生成されます。複数のワーカーが同時にBERTモデル（約500MB以上）を読み込んだり処理を行ったりすると、システムメモリが枯渇します。

## 提案される変更

### 設定変更
#### [MODIFY] [gunicorn_config.py](file:///root/workspace/hirakata_bot1/gunicorn_config.py)
- `workers` の数を固定値（例: 4）に変更し、メモリ消費を抑えます。

### AI機能の修正
#### [MODIFY] [features/ai_analysis.py](file:///root/workspace/hirakata_bot1/features/ai_analysis.py)
- `compute_embeddings` メソッドのデフォルト `batch_size` を32から8に減らし、推論時のピークメモリ使用量を削減します。

## 検証計画
### 自動テスト
- アプリケーションを再起動し、起動が成功することを確認します。
- ログを監視し、プロセスが安定しているか確認します。
- （可能であれば）テストスクリプトで負荷をかけずに動作することを確認します。

### 手動検証
- ユーザーに再度「意見から投票を作成」ボタンを試してもらい、エラーが発生しないことを確認していただきます。
