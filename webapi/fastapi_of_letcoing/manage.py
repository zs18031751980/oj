"""部署命令：python manage.py migrate；专用判题进程：python manage.py worker。"""
import argparse
import signal
import threading

from app_factory import create_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['migrate', 'seed', 'worker', 'set-role', 'audit-export', 'archive-outboxes'])
    parser.add_argument('--user-id', type=int)
    parser.add_argument('--role', choices=['member', 'staff', 'manager', 'provider'])
    parser.add_argument('--directory')
    parser.add_argument('--after', type=int, default=0)
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--retain-days', type=int, default=30)
    parser.add_argument('--prune', action='store_true')
    args = parser.parse_args()
    if args.command in {'audit-export', 'archive-outboxes'} and not args.directory:
        parser.error('归档需要 --directory')
    if args.retain_days < 7:
        parser.error('最少保留七天')
    if args.command == 'set-role' and (not args.user_id or not args.role):
        parser.error('set-role 必须提供 --user-id 和 --role')
    app = create_app()
    with app.app_context():
        if args.command in {'audit-export', 'archive-outboxes'}:
            from services.retention import export_audit, archive_outboxes
            from datetime import datetime, timedelta
            import json
            result = (export_audit(args.directory, args.after, args.limit) if args.command == 'audit-export'
                else archive_outboxes(args.directory, datetime.now()-timedelta(days=args.retain_days), args.limit, args.prune))
            print(json.dumps(result))
        elif args.command == 'migrate':
            from models.db_models import run_schema_migrations
            run_schema_migrations()
        elif args.command == 'set-role':
            from models.db_models import User, AuthSession, get_database
            with get_database().atomic():
                user = User.select().where(User.id == args.user_id).for_update().get()
                user.local_role = None if args.role == 'provider' else args.role
                user.role = user.local_role or user.provider_role or 'member'
                user.save(only=[User.local_role, User.role])
                AuthSession.update(revoked=True).where(AuthSession.user == user.id).execute()
            print(f'用户 {user.id} 的角色来源已更新，旧会话已撤销')
        elif args.command == 'seed':
            from models.db_models import seed_problem_catalog
            seed_problem_catalog()
        else:
            from services.judge_service import start_judge_worker, get_judge_worker
            stopped = threading.Event()
            for signum in (signal.SIGINT, signal.SIGTERM):
                signal.signal(signum, lambda *_: stopped.set())
            start_judge_worker()
            stopped.wait()
            worker = get_judge_worker()
            if worker:
                if not worker.stop(timeout=30):
                    # 进程退出后由租约过期与 attempt 栅栏恢复，禁止提前重新投递活动任务。
                    raise SystemExit(1)


if __name__ == '__main__':
    main()
