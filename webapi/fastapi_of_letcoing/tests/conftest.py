"""测试只使用临时 SQLite 和隔离的 Redis Unix socket，不加载部署配置。"""
import logging
import subprocess
import time

import pytest
import redis
from flask import Flask
from peewee import SqliteDatabase

from models import db_models
from services.redis_service import RedisService


@pytest.fixture
def db(tmp_path, monkeypatch):
    database = SqliteDatabase(tmp_path / 'test.sqlite', pragmas={'foreign_keys': 1})
    monkeypatch.setattr(db_models, '_actual_db', database)
    with database.bind_ctx(db_models.MODELS):
        database.create_tables(db_models.MODELS)
        yield database
        database.close()


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY='test-session-key')
    return app


@pytest.fixture(scope='session')
def redis_client(tmp_path_factory):
    directory = tmp_path_factory.mktemp('redis')
    socket = str(directory / 'redis.sock')
    process = subprocess.Popen([
        'redis-server', '--port', '0', '--unixsocket', socket,
        '--save', '', '--appendonly', 'no', '--dir', str(directory),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    client = redis.Redis(unix_socket_path=socket, decode_responses=True)
    for _ in range(100):
        try:
            if client.ping():
                break
        except redis.ConnectionError:
            time.sleep(.02)
    else:
        process.terminate()
        raise RuntimeError('isolated Redis did not start')
    yield client
    client.close()
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
def cache(redis_client):
    redis_client.flushdb()
    service = object.__new__(RedisService)
    service._client = redis_client
    service._connected = True
    service._logger_service = logging.getLogger('test')
    return service
