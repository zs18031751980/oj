"""只读就绪检查：验证兼容 schema 和对应队列的真实接单能力。"""
import math
import time

from models import db_models as m

POOLS = frozenset({'contest', 'practice', 'rejudge', 'validation', 'all'})


def check_schema(database=None):
    database = database or m.get_database()
    applied = {row[0] for row in database.execute_sql('SELECT name FROM schema_migrations')}
    if {name for name, _ in m._SCHEMA_MIGRATIONS} - applied:
        raise RuntimeError('database migration required: python manage.py migrate')
    # 一次元数据查询；允许滚动部署期间存在新版本的额外列和迁移。
    columns = set(database.execute_sql(
        'SELECT table_name, column_name FROM information_schema.columns '
        'WHERE table_schema = current_schema()').fetchall())
    required = {(model._meta.table_name, field.column_name)
                for model in m.MODELS for field in model._meta.sorted_fields}
    missing = sorted(required - columns)
    if missing:
        names = ', '.join(f'{table}.{column}' for table, column in missing[:20])
        raise RuntimeError(f'database column missing: {names}; verify migrations before serving traffic')


def worker_is_fresh(worker, now=None):
    if not isinstance(worker, dict) or worker.get('alive') is not True:
        return False
    stamp = worker.get('heartbeat_unix')
    if type(stamp) not in (int, float) or not math.isfinite(stamp):
        return False
    return -5 <= (time.time() if now is None else now) - stamp <= 45


def worker_accepts(worker, pool, now=None):
    return (worker_is_fresh(worker, now) and worker.get('pool') in {pool, 'all'}
            and worker.get('accepting_jobs') is True and not worker.get('draining'))


def judge_available(cache, pool='contest'):
    if pool not in POOLS:
        raise ValueError('unknown worker pool')
    if not cache.is_connected():
        return False
    # SCAN 的 count 不是上限；显式限制请求工作量，超出时保守报告不可用。
    for index, key in enumerate(cache._client.scan_iter('judge:worker:*', count=100)):
        if index >= 1000:
            break
        if worker_accepts(cache.get(key), pool):
            return True
    return False
