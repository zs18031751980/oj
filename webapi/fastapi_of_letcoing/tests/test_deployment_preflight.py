"""部署前配置与连接预算失败必须可解释，且不得输出秘密。"""
import pytest


def environment():
    return {'APP_ENV': 'production', 'JWT_SECRET_KEY': 'a'*48, 'FLASK_SECRET_KEY': 'b'*48,
            'FRONTEND_URL': 'https://front.test', 'PUBLIC_BACKEND_URL': 'https://api.test',
            'ALLOWED_ORIGINS': 'https://front.test', 'DB_HOST': 'db.internal'}


def test_preflight_aggregates_invalid_numbers_and_missing_database():
    from deploy.preflight import validate_environment
    env = environment()
    env.pop('DB_HOST')
    env.update(DB_PORT='credential-value', REDIS_PORT='bad')
    with pytest.raises(ValueError) as failure:
        validate_environment(env)
    assert all(name in str(failure.value) for name in ('DB_PORT', 'REDIS_PORT', 'DB_HOST'))
    assert 'credential-value' not in str(failure.value)


def test_connection_budget_counts_replicas_workers_and_maintenance():
    from deploy.preflight import validate_environment
    env = environment()
    env.update(DB_CONNECTION_BUDGET='100', API_REPLICAS='2', WEB_WORKERS='2',
               DB_MAX_CONNECTIONS='20', WORKER_REPLICAS='3', WORKER_DB_MAX_CONNECTIONS='5',
               DB_MAINTENANCE_CONNECTIONS='6')
    with pytest.raises(ValueError, match='DB_CONNECTION_BUDGET'):
        validate_environment(env)
    env['DB_CONNECTION_BUDGET'] = '101'
    assert validate_environment(env)['database_connection_upper_bound'] == 101


def test_tls_requirement_does_not_accept_prefer_or_override_url_silently():
    from deploy.preflight import validate_environment
    env = environment()
    env.pop('DB_HOST')
    env.update(DATABASE_URL='postgresql://test:private@db.test/oj?sslmode=prefer', DB_REQUIRE_TLS='1')
    with pytest.raises(ValueError, match='TLS'):
        validate_environment(env)
    env['DATABASE_URL'] = 'postgresql://test:private@db.test/oj?sslmode=verify-full'
    assert validate_environment(env)


def test_database_ca_and_pool_timeout_are_propagated():
    from services.config_service import ConfigService
    config = ConfigService({'DATABASE_URL': 'postgresql://test:p@db.test/oj?sslmode=verify-full',
                            'DB_SSLROOTCERT': '/certs/ca.pem', 'DB_POOL_TIMEOUT': '2'}).get_database_config()
    assert config['sslrootcert'] == '/certs/ca.pem'
    assert int(config['pool_timeout']) == 2


def test_typo_in_environment_cannot_disable_production_validation():
    from core.runtime_config import validate_runtime_config
    with pytest.raises(ValueError, match='APP_ENV'):
        validate_runtime_config({'APP_ENV': 'prodution'})


def test_tls_boolean_must_not_silently_disable_verification():
    from deploy.preflight import validate_environment
    env = environment()
    env['DB_REQUIRE_TLS'] = 'true'
    with pytest.raises(ValueError, match='DB_REQUIRE_TLS'):
        validate_environment(env)
