"""发布应拒绝未迁移的数据库，健康检查应反映实际队列能力。"""
import time
from unittest.mock import patch

import pytest

from models import db_models as m
from test_postgres import postgres


def test_configuration_reports_all_missing_public_names_without_values():
    from core.runtime_config import validate_runtime_config
    with pytest.raises(ValueError) as failure:
        validate_runtime_config({'APP_ENV': 'production', 'JWT_SECRET_KEY': 'sensitive'})
    text = str(failure.value)
    assert 'JWT_SECRET_KEY' in text and 'FLASK_SECRET_KEY' in text
    assert 'FRONTEND_URL' in text and 'PUBLIC_BACKEND_URL' in text
    assert 'ALLOWED_ORIGINS' in text
    assert 'sensitive' not in text


def test_schema_readiness_rejects_missing_migration_and_column(postgres):
    from services.health import check_schema
    m.run_schema_migrations()
    check_schema(postgres)
    postgres.execute_sql("DELETE FROM schema_migrations WHERE name='0021_production_controls'")
    with pytest.raises(RuntimeError, match='migration'):
        check_schema(postgres)
    m.run_schema_migrations()
    postgres.execute_sql('ALTER TABLE contests DROP COLUMN rules_version')
    with pytest.raises(RuntimeError, match='column'):
        check_schema(postgres)


def test_readiness_http_fails_with_unmigrated_database(postgres, cache):
    from app_factory import create_app
    app = create_app({'TESTING': True})
    with patch('app_factory.get_container') as container:
        container.return_value.resolve.return_value = cache
        assert app.test_client().get('/readyz').status_code == 503
        m.run_schema_migrations()
        assert app.test_client().get('/readyz').status_code == 200


def test_judge_health_requires_fresh_accepting_worker_in_requested_pool(cache):
    from app_factory import create_app
    app = create_app({'TESTING': True})
    client = app.test_client()
    heartbeat = {'alive': True, 'pool': 'practice', 'accepting_jobs': True,
                 'draining': False, 'heartbeat_unix': time.time()}
    with patch('app_factory.get_container') as container:
        container.return_value.resolve.return_value = cache
        cache.set('judge:worker:test', heartbeat, 60)
        assert client.get('/healthz/judge?pool=contest').status_code == 503
        assert client.get('/healthz/judge?pool=practice').status_code == 200
        heartbeat.update(pool='all', draining=True)
        cache.set('judge:worker:test', heartbeat, 60)
        assert client.get('/healthz/judge').status_code == 503
        heartbeat.update(draining=False, heartbeat_unix=time.time()-120)
        cache.set('judge:worker:test', heartbeat, 60)
        assert client.get('/healthz/judge').status_code == 503
        heartbeat.update(heartbeat_unix=time.time())
        cache.set('judge:worker:test', heartbeat, 60)
        assert client.get('/healthz/judge').status_code == 200
        assert client.get('/healthz/judge?pool=anything').status_code == 400


def test_database_error_logs_keep_sqlstate_without_query_or_parameters(postgres):
    import json
    import logging
    import sys
    from services.logger_service import SafeJSONFormatter
    try:
        postgres.execute_sql("SELECT nonexistent_column FROM (SELECT %s AS safe) q", ('private-user-value',))
    except Exception:
        record = logging.LogRecord('test', logging.ERROR, __file__, 1, 'database failure', (), sys.exc_info())
        data = json.loads(SafeJSONFormatter().format(record))
    assert data['sqlstate'] == '42703'
    assert data['database_error'] == 'undefined_column'
    assert 'private-user-value' not in str(data)
    assert 'SELECT' not in str(data)


def test_startup_migrates_once_before_schema_check(postgres):
    from deploy.start_api import prepare_database
    prepare_database('migrate')
    m.User.create(username='preserved')
    prepare_database('check')
    assert m.User.get().username == 'preserved'
    postgres.execute_sql("DELETE FROM schema_migrations WHERE name='0021_production_controls'")
    with pytest.raises(RuntimeError):
        prepare_database('check')
    with pytest.raises(ValueError):
        prepare_database('anything')


def test_metrics_do_not_count_stale_or_nonaccepting_workers(app, db, cache):
    from services.observability import register_metrics
    app.config['METRICS_TOKEN'] = 'test-only'
    register_metrics(app)
    cache.set('judge:worker:stale', {'alive': True, 'pool': 'contest', 'accepting_jobs': True,
                                  'heartbeat_unix': time.time()-90}, 60)
    cache.set('judge:worker:paused', {'alive': True, 'pool': 'contest', 'accepting_jobs': False,
                                   'heartbeat_unix': time.time()}, 60)
    with patch('core.di_container.inject', return_value=cache):
        result = app.test_client().get('/metrics', headers={'Authorization': 'Bearer test-only'})
    assert 'letcoding_worker_slots{pool="contest",state="alive"} 1' in result.text
    assert 'letcoding_worker_slots{pool="contest",state="accepting"} 0' in result.text


def test_transaction_timing_includes_rollback_and_preserves_atomicity(app, db):
    from flask import g
    from services.contest_lifecycle import transactional
    @transactional
    def failed():
        m.User.create(username='should-rollback')
        return {}, 409
    with app.test_request_context():
        assert failed()[1] == 409
        assert g.contest_transaction_seconds >= 0
        assert m.User.select().count() == 0


def test_database_audit_detects_privileged_role_and_connection_budget(postgres):
    from deploy.audit_database import audit_database
    result = audit_database(postgres)
    assert result['superuser'] is True
    assert result['connections'] >= 1
    assert result['max_connections'] == 20
    assert result['least_privilege'] is False
