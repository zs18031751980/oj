"""每进程连接池预算须与 API / Worker 数量一起计算。"""
import os

bind = '0.0.0.0:' + os.environ.get('PORT', '8080')
workers = int(os.environ.get('WEB_WORKERS', '2'))
threads = int(os.environ.get('WEB_THREADS', '4'))
worker_class = 'gthread'
timeout = 45
graceful_timeout = 35
max_requests = 5000
max_requests_jitter = 500
preload_app = False
accesslog = '-'
# U 不包含查询字符串，OAuth code 不进入访问日志。
access_log_format = '%(h)s %(m)s %(U)s %(s)s %(L)s'
errorlog = '-'


def child_exit(server, worker):
    if os.environ.get('PROMETHEUS_MULTIPROC_DIR'):
        from prometheus_client import multiprocess
        multiprocess.mark_process_dead(worker.pid)
