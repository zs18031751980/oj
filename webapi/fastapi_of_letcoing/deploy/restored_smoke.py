"""仅由 recovery 在新建的隔离恢复库中调用；使用真实控制器和固定自测程序。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from uuid import uuid4


def check(params: dict) -> dict:
    from datetime import timedelta
    import asyncio
    from flask import Flask
    from flask_restx import Api
    from peewee import PostgresqlDatabase
    from werkzeug.security import generate_password_hash
    from models import db_models as m
    from core.di_container import get_container
    from interfaces.service_interfaces import IJWTService, IUserService, IRedisService
    from services.config_service import ConfigService
    from services.jwt_service import JWTService
    from services.user_service import UserService
    from services.redis_service import RedisService
    from services.logger_service import LoggerService
    from services.judge_service import JudgeWorker
    from services.contest_operations import now
    from controllers.auth_controller import api as auth_api
    from controllers.contest_controller import api as contest_api
    from controllers.contest_rankings_controller import api as rankings_api, refresh_live_projection
    from middleware.request_middleware import register_request_hooks

    name = params.pop('dbname')
    if not name.startswith('oj_restore_') or len(name) != len('oj_restore_')+32:
        raise ValueError('smoke requires a generated restore database')
    db = PostgresqlDatabase(name, **params)
    m._actual_db = db
    db.bind(m.MODELS)
    with db.connection_context():
        applied = {row[0] for row in db.execute_sql('SELECT name FROM schema_migrations').fetchall()}
        if not {name for name, _ in m._SCHEMA_MIGRATIONS}.issubset(applied):
            raise RuntimeError('restored database migrations are incomplete')
        with tempfile.TemporaryDirectory(prefix='oj-restore-smoke-') as directory:
            socket = str(Path(directory)/'redis.sock')
            process = subprocess.Popen(['redis-server', '--port', '0', '--unixsocket', socket,
                '--unixsocketperm', '700', '--save', '', '--appendonly', 'no', '--dir', directory],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cache = None
            try:
                for _ in range(100):
                    if Path(socket).exists():
                        break
                    if process.poll() is not None:
                        raise RuntimeError('isolated Redis failed to start')
                    time.sleep(.02)
                config = ConfigService({'JWT_SECRET_KEY': uuid4().hex+uuid4().hex, 'REDIS_URL': 'unix://'+socket})
                logger = LoggerService()
                cache = RedisService(config, logger)
                if not cache.is_connected():
                    raise RuntimeError('isolated Redis unavailable')
                container = get_container()
                container.register_singleton(IRedisService, instance=cache)
                container.register_singleton(IJWTService, instance=JWTService(config, logger, cache))
                container.register_singleton(IUserService, instance=UserService(config))
                app = Flask('restore-smoke')
                app.config.update(TESTING=True, SECRET_KEY=uuid4().hex)
                register_request_hooks(app)
                api = Api(app)
                api.add_namespace(auth_api, path='/auth')
                api.add_namespace(contest_api, path='/contests')
                api.add_namespace(rankings_api, path='/contests')
                password = uuid4().hex
                user = m.User.create(username='restore-'+uuid4().hex, password_hash=generate_password_hash(password))
                current = now()
                contest = m.Contest.create(title='isolated restore acceptance', lifecycle_state='RUNNING',
                    start_time=current-timedelta(minutes=1), end_time=current+timedelta(hours=1))
                problem = m.ContestProblem.create(contest=contest, title='A', problem_index='A',
                    description='restore check', correct_answer='print(42)', language='python')
                m.ContestParticipant.create(contest=contest, user=user)
                m.ContestTestcase.create(contest_problem=problem, input_data='', expected_output='42')
                client = app.test_client()
                login = client.post('/auth/login/password', json={'identifier': user.username, 'password': password})
                if login.status_code != 200:
                    raise RuntimeError('restored login failed')
                headers = {'Authorization': 'Bearer '+login.json['tokens']['access_token'], 'Idempotency-Key': uuid4().hex}
                path = f'/contests/{contest.id}/problems/{problem.id}'
                accepted = client.post(path+'/submit', json={'code': 'print(42)', 'language': 'python'}, headers=headers)
                if accepted.status_code != 202:
                    raise RuntimeError('restored submit failed')
                claim = cache.list_claim('contest_judge_queue', 'contest_judge_queue:processing')
                if not claim or claim['payload']['submission_id'] != accepted.json['submission_id']:
                    raise RuntimeError('restored outbox dispatch failed')
                worker = JudgeWorker(cache, None, logger)
                worker._loop = asyncio.new_event_loop()
                try:
                    if worker._process_contest_task(claim['payload']) is False:
                        raise RuntimeError('restored judgement did not persist')
                finally:
                    worker._loop.close()
                cache.list_ack('contest_judge_queue:processing', claim['receipt'])
                row = m.ContestSubmission.get_by_id(accepted.json['submission_id'])
                result = client.get(path+f'/submission/{row.id}', headers=headers)
                if row.status != 'AC' or result.status_code != 200 or result.json['status'] != 'AC':
                    raise RuntimeError('restored verdict read failed')
                refresh_live_projection(contest.id)
                board = client.get(f'/contests/{contest.id}/rankings', headers=headers)
                if board.status_code != 200 or len(board.json['rankings']) != 1 or board.json['rankings'][0]['solved_count'] != 1:
                    raise RuntimeError('restored scoreboard failed')
                return {'verdict': row.status, 'solved_count': 1, 'login': True, 'submit': True}
            finally:
                if cache and cache._client:
                    cache._client.close()
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)


if __name__ == '__main__':
    try:
        print(json.dumps(check(json.load(sys.stdin))))
    except Exception as exc:
        # 不输出连接参数、凭证和恢复库中的数据。
        import traceback
        print(json.dumps({'error': type(exc).__name__, 'frames': [{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name} for f in traceback.extract_tb(exc.__traceback__)]}), file=sys.stderr)
        raise SystemExit(1)
