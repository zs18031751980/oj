"""启动前显式迁移并验证 schema；Gunicorn 多进程启动不执行 DDL。"""
import os
import sys


def prepare_database(mode):
    from models.db_models import get_database, run_schema_migrations
    from services.health import check_schema
    if mode not in {'migrate', 'check'}:
        raise ValueError('DB_MIGRATION_MODE 必须为 migrate 或 check')
    if mode == 'migrate':
        run_schema_migrations()
    with get_database().connection_context():
        check_schema()


def main():
    from deploy.preflight import validate_environment
    validate_environment(os.environ)
    from app_factory import create_app
    app = create_app()
    with app.app_context():
        prepare_database(os.environ.get('DB_MIGRATION_MODE', 'migrate'))
    os.execvp('gunicorn', ['gunicorn', '--config', 'gunicorn.conf.py', 'app_factory:create_app()'])


if __name__ == '__main__':
    main()
