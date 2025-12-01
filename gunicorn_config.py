import multiprocessing
import os

# バインド設定
bind = "0.0.0.0:5000"

# ワーカー設定
workers = multiprocessing.cpu_count() * 2 + 1
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
