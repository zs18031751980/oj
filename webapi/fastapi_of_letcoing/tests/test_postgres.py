"""真实 PostgreSQL：迁移、持久化 outbox 与投影。不连接用户数据库。"""
import os
from pathlib import Path
import shutil
import subprocess

import pytest
from peewee import PostgresqlDatabase

from models import db_models as m


@pytest.fixture
def postgres(tmp_path, monkeypatch):
    bindir = os.environ.get('PG_BINDIR', '/usr/lib/postgresql/17/bin')
    initdb = str(Path(bindir) / 'initdb')
    if not Path(initdb).exists():
        pytest.fail('PostgreSQL test tools missing; set PG_BINDIR')
    data, socket = tmp_path / 'pgdata', tmp_path / 'socket'
    socket.mkdir()
    subprocess.run([initdb, '-D', str(data), '-A', 'trust', '--no-locale', '-E', 'UTF8'],
                   check=True, capture_output=True)
    ctl = str(Path(bindir) / 'pg_ctl')
    subprocess.run([ctl, '-D', str(data), '-l', str(tmp_path / 'pg.log'), '-o',
        f'-h "" -k {socket} -F -c max_connections=20', '-w', 'start'], check=True, capture_output=True)
    db = PostgresqlDatabase('postgres', host=str(socket), user=os.environ.get('USER', 'z'))
    monkeypatch.setattr(m, '_actual_db', db)
    try:
        with db.bind_ctx(m.MODELS):
            yield db
    finally:
        db.close()
        subprocess.run([ctl, '-D', str(data), '-m', 'immediate', '-w', 'stop'], check=True, capture_output=True)


def test_migrations_bootstrap_and_rerun_without_losing_data(postgres):
    m.run_schema_migrations()
    assert m.AuthSession.table_exists(), 'session migration missing'
    user = m.User.create(username='preserved')
    m.run_schema_migrations()
    assert m.User.get_by_id(user.id).username == 'preserved'
    assert m.SubmissionOutbox.table_exists()
    assert postgres.execute_sql("SELECT count(*) FROM schema_migrations").fetchone()[0] == len(m._SCHEMA_MIGRATIONS)


def test_migration_failure_is_not_recorded_as_success(postgres, monkeypatch):
    monkeypatch.setattr(m, '_SCHEMA_MIGRATIONS', [('broken', ['SELECT non_existing_column'])])
    with pytest.raises(Exception):
        m.run_schema_migrations()
    assert postgres.execute_sql("SELECT count(*) FROM schema_migrations WHERE name='broken'").fetchone()[0] == 0


def test_seed_failure_is_not_silently_ignored(postgres, monkeypatch):
    from pages.problem_data import PROBLEMS
    m.run_schema_migrations()
    monkeypatch.setitem(PROBLEMS, 991991, {'title': None})
    with pytest.raises(Exception):
        m.seed_problem_catalog()
