"""真实进程崩溃、数据库回滚和磁盘故障的隔离验收，不连接部署服务。"""
import errno
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from models import db_models as m
from test_postgres import postgres
from test_job_reliability import worker
from test_acm_upgrade import contest_fixture


def wait_until(predicate, timeout=5):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.02)
    raise AssertionError('isolated process did not reach expected state')


def test_sigkill_after_claim_recovers_and_scores_once(postgres, cache, worker, tmp_path, monkeypatch):
    from services.contest_outbox import dispatch_outbox_entry
    from controllers.contest_rankings_controller import _compute_rankings
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('JUDGE_BACKEND', 'local')
    monkeypatch.setenv('ALLOW_UNSAFE_LOCAL_JUDGE', '1')
    m.run_schema_migrations()
    user, contest, problem = contest_fixture()
    m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='42')
    row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', code='print(42)', language='python', status='Queued', job_id='killed-consumer')
    entry = m.ContestJudgeOutbox.create(submission=row)
    assert dispatch_outbox_entry(cache, entry)
    marker = tmp_path/'claimed.json'
    socket = cache._client.connection_pool.connection_kwargs['path']
    script = '''import sys, json, signal, redis
from pathlib import Path
from services.redis_service import RedisService
service = object.__new__(RedisService)
service._connected = True
service._client = redis.Redis(unix_socket_path=sys.argv[1], decode_responses=True)
delivery = service.list_claim('contest_judge_queue', 'contest_judge_queue:processing')
Path(sys.argv[2]).write_text(json.dumps(delivery))
signal.pause()
'''
    process = subprocess.Popen([sys.executable, '-c', script, socket, str(marker)])
    try:
        wait_until(marker.exists)
        process.kill(); process.wait(timeout=3)
        claim = json.loads(marker.read_text())
        cache._client.pexpire(cache._lease_key('contest_judge_queue:processing', claim['receipt']), 20)
        wait_until(lambda: cache.list_recover('contest_judge_queue:processing', 'contest_judge_queue') == 1)
        recovered = cache.list_claim('contest_judge_queue', 'contest_judge_queue:processing')
        assert worker._process_contest_task(recovered['payload']) is not False
        assert worker._process_contest_task(recovered['payload']) is not False
        assert m.ContestSubmission.get_by_id(row.id).status == 'AC'
        assert m.Contest.get_by_id(contest.id).scoreboard_requested_version == 1
        assert _compute_rankings(contest.id)['rankings'][0]['solved_count'] == 1
    finally:
        if process.poll() is None:
            process.kill(); process.wait(timeout=3)


def test_process_death_rolls_back_uncommitted_database_work(postgres, tmp_path):
    m.run_schema_migrations()
    marker = tmp_path/'transaction-open'
    # 使用 ORM 生成完整默认值，避免测试 SQL 与新增 NOT NULL 列脱节。
    script = '''import sys, signal
from pathlib import Path
from peewee import PostgresqlDatabase
from models import db_models as m
db = PostgresqlDatabase('postgres', host=sys.argv[1], user=sys.argv[2])
m.database_proxy.initialize(db)
with db.atomic():
    m.User.create(username='uncommitted')
    Path(sys.argv[3]).touch()
    signal.pause()
'''
    process = subprocess.Popen([sys.executable, '-c', script, postgres.connect_params['host'],
                                os.environ.get('USER', 'z'), str(marker)])
    try:
        wait_until(marker.exists)
        process.kill(); process.wait(timeout=3)
        assert not m.User.select().where(m.User.username == 'uncommitted').exists()
        m.User.create(username='after-reconnect')
        assert m.User.select().count() == 1
    finally:
        if process.poll() is None:
            process.kill(); process.wait(timeout=3)


def test_disk_full_cleans_work_directory_and_is_not_a_compile_error(tmp_path, monkeypatch):
    from controllers.contest_problem_controller import _prepare_program
    monkeypatch.setenv('JUDGE_WORK_ROOT', str(tmp_path/'jobs'))
    with patch('controllers.contest_problem_controller.open', side_effect=OSError(errno.ENOSPC, 'disk full')):
        with pytest.raises(RuntimeError):
            _prepare_program('print(42)', 'python')
    assert not list((tmp_path/'jobs').iterdir())


def test_redis_restart_rebuilds_dispatched_queue_from_database(db, cache, worker, tmp_path, monkeypatch):
    import redis
    from services.contest_outbox import dispatch_outbox_entry
    user, contest, problem = contest_fixture()
    row = m.ContestSubmission.create(contest=contest, user=user, contest_problem=problem,
        problem_index='A', code='print(42)', language='python', status='Queued', job_id='restart-redis')
    outbox = m.ContestJudgeOutbox.create(submission=row)
    socket = str(tmp_path/'restart.sock')
    client = redis.Redis(unix_socket_path=socket, decode_responses=True, socket_timeout=1)
    def start():
        instance = subprocess.Popen(['redis-server', '--port', '0', '--unixsocket', socket,
            '--save', '', '--appendonly', 'no', '--dir', str(tmp_path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def ready():
            try:
                return client.ping()
            except redis.ConnectionError:
                return False
        try:
            wait_until(ready)
        except Exception:
            instance.kill(); instance.wait(timeout=3)
            raise
        return instance
    process = start()
    try:
        monkeypatch.setattr(cache, '_client', client)
        assert dispatch_outbox_entry(cache, outbox)
        assert cache.list_length('contest_judge_queue') == 1
        process.kill(); process.wait(timeout=3)
        client.connection_pool.disconnect()
        process = start()
        assert cache.list_length('contest_judge_queue') == 0
        worker._reconcile_dispatched_jobs()
        worker._reconcile_dispatched_jobs()
        assert cache.list_length('contest_judge_queue') == 1
        recovered = cache.list_claim('contest_judge_queue', 'contest_judge_queue:processing')
        assert recovered['payload']['submission_id'] == row.id
        assert m.ContestJudgeOutbox.get_by_id(outbox.id).state == 'DISPATCHED'
    finally:
        client.close()
        if process.poll() is None:
            process.terminate(); process.wait(timeout=3)
