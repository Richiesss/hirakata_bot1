import multiprocessing
import os

# バインド設定
bind = "0.0.0.0:5000"

# ワーカー設定
# OllamaのようなLLMを使用する場合、worker数を抑えてリソース競合を防ぐ
# 推奨: 4-8 workers (CPU負荷よりもLLM待機時間が支配的なため)
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5

# ログ設定
if not os.path.exists('logs'):
    os.makedirs('logs')

accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# プロセス名
proc_name = "hirakata_bot"
