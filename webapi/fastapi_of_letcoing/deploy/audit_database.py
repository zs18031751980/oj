"""只读审计当前连接账号权限与数据库连接使用量；不输出角色名或连接串。"""
import argparse
import json


def audit_database(database):
    with database.connection_context():
        superuser, create_role, create_db = database.execute_sql(
            'SELECT rolsuper, rolcreaterole, rolcreatedb FROM pg_roles WHERE rolname=current_user').fetchone()
        owns_tables = database.execute_sql(
            "SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname=current_schema() AND c.relkind IN ('r','p','S') "
            "AND pg_has_role(current_user,c.relowner,'USAGE'))").fetchone()[0]
        schema_create = database.execute_sql(
            "SELECT has_schema_privilege(current_schema(),'CREATE')").fetchone()[0]
        connections, waiting = database.execute_sql(
            "SELECT count(*), count(*) FILTER (WHERE wait_event_type='Lock') FROM pg_stat_activity").fetchone()
        limit = int(database.execute_sql('SHOW max_connections').fetchone()[0])
    return {'superuser': superuser, 'create_role': create_role, 'create_database': create_db,
            'owns_application_tables': owns_tables, 'schema_create': schema_create,
            'least_privilege': not any((superuser, create_role, create_db, owns_tables, schema_create)),
            'connections': connections, 'lock_waiters_visible_to_role': waiting, 'max_connections': limit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-least-privilege', action='store_true')
    args = parser.parse_args()
    from app_factory import create_app
    from models.db_models import get_database
    app = create_app()
    with app.app_context():
        result = audit_database(get_database())
    print(json.dumps(result))
    if args.require_least_privilege and not result['least_privilege']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
