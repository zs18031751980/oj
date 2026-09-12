"""纯配置预检：一次报告缺项和连接预算，不连接生产服务，不打印配置值。"""
import os

from core.runtime_config import validate_runtime_config
from services.config_service import ConfigService


def validate_environment(environment):
    env = dict(environment)
    config = {key: env.get(key, '') for key in ('JWT_SECRET_KEY', 'FRONTEND_URL', 'PUBLIC_BACKEND_URL')}
    config.update(APP_ENV=env.get('APP_ENV', 'production'), SECRET_KEY=env.get('FLASK_SECRET_KEY', ''),
                  ALLOWED_ORIGINS=[x.strip() for x in env.get('ALLOWED_ORIGINS', '').split(',') if x.strip()])
    errors = []
    try:
        validate_runtime_config(config)
    except ValueError as exc:
        errors.append(str(exc))
    defaults = {'DB_PORT': 5432, 'REDIS_PORT': 6379, 'REDIS_DB': 0, 'REDIS_TIMEOUT': 5,
                'DB_MAX_CONNECTIONS': 20, 'DB_POOL_TIMEOUT': 5, 'DB_STALE_TIMEOUT': 300,
                'DB_STATEMENT_TIMEOUT_MS': 15000, 'WEB_WORKERS': 2, 'WEB_THREADS': 4,
                'API_REPLICAS': 1, 'WORKER_REPLICAS': 1, 'WORKER_DB_MAX_CONNECTIONS': 20,
                'DB_MAINTENANCE_CONNECTIONS': 5, 'TRUSTED_PROXY_HOPS': 0,
                'JWT_ACCESS_TOKEN_EXPIRE': 900, 'JWT_REFRESH_TOKEN_EXPIRE': 604800}
    values = {}
    for key, default in defaults.items():
        try:
            value = int(env.get(key, default))
            minimum = 0 if key in {'REDIS_DB', 'WORKER_REPLICAS', 'TRUSTED_PROXY_HOPS'} else 1
            maximum = 65535 if key.endswith('_PORT') else 100000000
            if not minimum <= value <= maximum:
                raise ValueError()
            values[key] = value
        except (ValueError, TypeError):
            errors.append(f'{key} 必须配置合法整数')
    if config['APP_ENV'] == 'production' and not env.get('DB_HOST') and not env.get('DATABASE_URL'):
        errors.append('必须配置 DB_HOST 或 DATABASE_URL')
    try:
        database = ConfigService(env).get_database_config()
        mode = database['sslmode']
        if mode not in {'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'}:
            errors.append('DB_SSLMODE / DATABASE_URL sslmode 无效')
        if env.get('DB_REQUIRE_TLS') == '1' and mode != 'verify-full':
            errors.append('DB_REQUIRE_TLS 要求 sslmode=verify-full，并配置可信 CA')
    except ValueError:
        errors.append('DATABASE_URL 格式无效')
    if env.get('DB_REQUIRE_TLS', '0') not in {'0', '1'}:
        errors.append('DB_REQUIRE_TLS 必须为 0 或 1')
    estimate = None
    if all(key in values for key in defaults):
        estimate = (values['API_REPLICAS'] * values['WEB_WORKERS'] * values['DB_MAX_CONNECTIONS']
                    + values['WORKER_REPLICAS'] * values['WORKER_DB_MAX_CONNECTIONS']
                    + values['DB_MAINTENANCE_CONNECTIONS'])
        if 'DB_CONNECTION_BUDGET' in env:
            try:
                if int(env['DB_CONNECTION_BUDGET']) < estimate:
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append('DB_CONNECTION_BUDGET 不足以覆盖 API、Worker 和维护连接上限')
    if env.get('DB_MIGRATION_MODE', 'migrate') not in {'migrate', 'check'}:
        errors.append('DB_MIGRATION_MODE 必须为 migrate 或 check')
    if errors:
        raise ValueError('; '.join(errors))
    return {'database_connection_upper_bound': estimate}


if __name__ == '__main__':
    result = validate_environment(os.environ)
    print(f"配置预检通过；数据库连接上限估计={result['database_connection_upper_bound']}")
