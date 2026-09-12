"""逻辑备份和独立数据库恢复演练；连接使用 pg_service.conf / PGPASSFILE。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from uuid import uuid4

import psycopg2
from psycopg2 import sql


def _environment(connection, database=None):
    env = dict(os.environ)
    params = connection.get_dsn_parameters()
    for key in ('host', 'port', 'user', 'dbname', 'sslmode', 'service', 'passfile'):
        if params.get(key):
            env['PGDATABASE' if key == 'dbname' else 'PG'+key.upper()] = params[key]
    if database:
        env['PGDATABASE'] = database
    return env


def _run(bindir, name, args, env):
    result = subprocess.run([str(Path(bindir)/name) if bindir else name, *args],
        env=env, capture_output=True, timeout=3600)
    if result.returncode:
        # 连接错误可能含 DSN；不输出 stderr 或连接参数。
        raise RuntimeError(f'{name} failed with exit code {result.returncode}')


def _checksum(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _fingerprint(connection):
    result = {}
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL TIME ZONE 'UTC'")
        cursor.execute("SET LOCAL datestyle='ISO, YMD'")
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        tables = [row[0] for row in cursor.fetchall()]
    for name in tables:
        digest, count = hashlib.sha256(), 0
        with connection.cursor(name='fingerprint_'+uuid4().hex) as cursor:
            # 文本排序不依赖物理行顺序，逐批流式读取。数据库临时排序空间应由运维预算。
            cursor.execute(sql.SQL('SELECT payload FROM (SELECT row_to_json(t)::text AS payload FROM {} t) s ORDER BY payload COLLATE "C"')
                .format(sql.Identifier('public', name)))
            for row in cursor:
                encoded = row[0].encode()
                digest.update(len(encoded).to_bytes(8, 'big'))
                digest.update(encoded)
                count += 1
        result[name] = {'rows': count, 'sha256': digest.hexdigest()}
    return result


def _schema_fingerprint(connection: 'psycopg2.extensions.connection') -> dict:
    with connection.cursor() as cursor:
        cursor.execute("""SELECT tablename, indexname, indexdef FROM pg_indexes
            WHERE schemaname='public' ORDER BY tablename,indexname""")
        indexes = [list(row) for row in cursor.fetchall()]
        # pg_dump 的数组类型转换可能重写成逐元素转换。重解析谓词并比较无成本计划，
        # 避免把等价的部分索引误判成损坏；保留列、排序、唯一性等定义。
        cursor.execute('SET LOCAL enable_indexscan=off')
        cursor.execute('SET LOCAL enable_indexonlyscan=off')
        cursor.execute('SET LOCAL enable_bitmapscan=off')
        cursor.execute('SET LOCAL enable_seqscan=on')
        cursor.execute('SET LOCAL max_parallel_workers_per_gather=0')
        cursor.execute('SET LOCAL constraint_exclusion=off')
        for row in indexes:
            definition, separator, predicate = row[2].partition(' WHERE ')
            if separator:
                cursor.execute(sql.SQL('EXPLAIN (FORMAT JSON, COSTS FALSE) SELECT 1 FROM {} WHERE ').format(
                    sql.Identifier('public', row[0])) + sql.SQL(predicate))
                row[2] = definition + ' WHERE ' + json.dumps(cursor.fetchone()[0], sort_keys=True)

        cursor.execute("""SELECT c.relname, k.conname, pg_get_constraintdef(k.oid), k.convalidated
            FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
            JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'
            ORDER BY c.relname,k.conname""")
        constraints = [list(row) for row in cursor.fetchall()]
        cursor.execute("""SELECT table_name,column_name,data_type,is_nullable,column_default
            FROM information_schema.columns WHERE table_schema='public'
            ORDER BY table_name,ordinal_position""")
        columns = [list(row) for row in cursor.fetchall()]
    return {'indexes': indexes, 'constraints': constraints, 'columns': columns}


def _check_sequences(connection: 'psycopg2.extensions.connection') -> int:
    # 仅恢复库写入：所有 serial/identity 序列实际取号，防止恢复后主键冲突。
    with connection.cursor() as cursor:
        cursor.execute("""SELECT s.oid::regclass::text, t.relname, a.attname
            FROM pg_class s JOIN pg_depend d ON d.objid=s.oid AND d.classid='pg_class'::regclass
            JOIN pg_class t ON t.oid=d.refobjid JOIN pg_namespace n ON n.oid=t.relnamespace
            JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=d.refobjsubid
            WHERE s.relkind='S' AND n.nspname='public' AND d.deptype IN ('a','i')""")
        rows = cursor.fetchall()
        for sequence, table, column in rows:
            cursor.execute('SELECT nextval(%s::regclass)', (sequence,))
            value = cursor.fetchone()[0]
            cursor.execute(sql.SQL('SELECT MAX({}) FROM {}').format(sql.Identifier(column), sql.Identifier('public', table)))
            maximum = cursor.fetchone()[0]
            if maximum is not None and value <= maximum:
                raise ValueError('restored sequence would reuse an existing key')
    return len(rows)


def _application_check(params: dict) -> dict:
    import sys
    # 子进程不继承应用密钥、生产 Redis/判题配置或 .env；连接通过 stdin 传递。
    env = {key: value for key, value in os.environ.items() if key in {'PATH', 'PGPASSFILE', 'PGSERVICEFILE', 'PGSYSCONFDIR'}}
    env.update(APP_ENV='test', JUDGE_BACKEND='local', ALLOW_UNSAFE_LOCAL_JUDGE='1', TZ='Asia/Shanghai')
    import signal
    process = subprocess.Popen([sys.executable, '-m', 'deploy.restored_smoke'],
        cwd=Path(__file__).resolve().parents[1], env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, _ = process.communicate(json.dumps(params), timeout=120)
    except subprocess.TimeoutExpired:
        # 子进程启动的 Redis 同组退出，避免超时后留下孤儿服务。
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=5)
        raise RuntimeError('restored application check timed out') from None
    if process.returncode:
        raise RuntimeError('restored application check failed')
    return json.loads(stdout.strip().splitlines()[-1])


def _create_backup(connection, directory, bindir=''):
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    started = time.monotonic()
    snapshot_at_unix = time.time()
    with connection:
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            cursor.execute('SELECT pg_export_snapshot()')
            snapshot = cursor.fetchone()[0]
        dump = directory / 'database.dump'
        _run(bindir, 'pg_dump', ['--format=custom', '--no-owner', '--no-acl',
            '--snapshot='+snapshot, '--file='+str(dump)], _environment(connection))
        os.chmod(dump, 0o600)
        with dump.open('rb') as stream:
            os.fsync(stream.fileno())
        tables = _fingerprint(connection)
        schema = _schema_fingerprint(connection)
    manifest = {'format_version': 2, 'postgresql_major': connection.server_version // 10000, 'snapshot_at_unix': snapshot_at_unix, 'sha256': _checksum(dump), 'tables': tables, 'schema': schema, 'created_at_unix': time.time(),
        'backup_seconds': time.monotonic()-started}
    manifest_file = directory / 'manifest.json'
    with manifest_file.open('x') as stream:
        os.chmod(manifest_file, 0o600)
        json.dump(manifest, stream, indent=2)
        stream.flush(); os.fsync(stream.fileno())
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return manifest


def create_backup(connection, directory, bindir=''):
    from psycopg2.extensions import TRANSACTION_STATUS_IDLE
    if connection.get_transaction_status() != TRANSACTION_STATUS_IDLE:
        raise ValueError('backup requires an idle dedicated connection')
    autocommit = connection.autocommit
    connection.autocommit = False
    try:
        return _create_backup(connection, directory, bindir)
    finally:
        connection.autocommit = autocommit


def verify_backup(admin_connection, directory, bindir=''):
    directory = Path(directory)
    manifest = json.loads((directory/'manifest.json').read_text())
    if manifest.get('format_version') != 2:
        raise ValueError('backup manifest lacks schema evidence; create a new version 2 backup')
    if manifest.get('postgresql_major') != admin_connection.server_version // 10000:
        raise ValueError('restore drill requires the same PostgreSQL major version')
    if _checksum(directory/'database.dump') != manifest['sha256']:
        raise ValueError('backup checksum mismatch')
    name = 'oj_restore_'+uuid4().hex
    started, created = time.monotonic(), False
    env = _environment(admin_connection)
    try:
        _run(bindir, 'createdb', ['--template=template0', name], env)
        created = True
        _run(bindir, 'pg_restore', ['--exit-on-error', '--no-owner', '--no-acl',
            '--dbname='+name, str(directory/'database.dump')], env)
        params = admin_connection.get_dsn_parameters()
        params['dbname'] = name
        restored = psycopg2.connect(**params)
        try:
            with restored:
                tables = _fingerprint(restored)
                schema = _schema_fingerprint(restored)
                if tables != manifest['tables'] or schema != manifest.get('schema'):
                    raise ValueError('restored data or schema fingerprint mismatch')
                sequences = _check_sequences(restored)
        finally:
            restored.close()
        report = {'passed': tables == manifest['tables'], 'tables_checked': len(tables),
            'schema_checked': True, 'sequences_checked': sequences,
            'restore_seconds': time.monotonic()-started, 'backup_created_at_unix': manifest['created_at_unix']}
        if not report['passed']:
            raise ValueError('restored database fingerprint mismatch')
        report['application_check'] = _application_check(params)
        report['restore_seconds'] = time.monotonic()-started
        return report
    finally:
        if created:
            _run(bindir, 'dropdb', [name], env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['backup', 'verify'])
    parser.add_argument('--service', required=True, help='verify 必须指向隔离的恢复演练集群')
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--pg-bindir', default='')
    args = parser.parse_args()
    connection = psycopg2.connect(service=args.service)
    try:
        if args.command == 'backup':
            result = create_backup(connection, args.directory, args.pg_bindir)
            print(json.dumps({'backup_seconds': result['backup_seconds'], 'tables': len(result['tables'])}))
        else:
            print(json.dumps(verify_backup(connection, args.directory, args.pg_bindir)))
    finally:
        connection.close()


if __name__ == '__main__':
    main()
