"""比赛生命周期的授权边界。

发布即冻结比赛资产；取消或结算不会让历史比赛重新变为可编辑资源。
"""

EDITABLE_STATES = frozenset({'DRAFT', 'READY'})


def can_edit_contest_assets(lifecycle_state: str | None) -> bool:
    """只有尚未发布的比赛允许改题、改测试数据或改规则。"""
    return lifecycle_state in EDITABLE_STATES


def can_delete_contest(lifecycle_state: str | None) -> bool:
    """发布后的比赛必须保留审计记录，只能取消，不能物理删除。"""
    return lifecycle_state == 'DRAFT'


def can_view_rankings(lifecycle_state: str | None, *, is_public: bool, is_manager: bool) -> bool:
    """草稿和私有比赛榜单仅赛事管理员可见。"""
    return bool(is_manager or (is_public and lifecycle_state not in {'DRAFT', 'READY', 'CANCELLED'}))


from functools import wraps
from contextlib import contextmanager


@contextmanager
def timed_transaction():
    import time
    from flask import g, has_request_context
    from models.db_models import get_database
    started = time.monotonic()
    try:
        with get_database().atomic() as transaction:
            yield transaction
    finally:
        if has_request_context():
            g.contest_transaction_seconds = (getattr(g, 'contest_transaction_seconds', 0.)
                                             + time.monotonic()-started)


def transactional(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        from models.db_models import get_database
        with timed_transaction() as transaction:
            result = function(*args, **kwargs)
            status = result[1] if isinstance(result, tuple) and len(result) > 1 else getattr(result, 'status_code', 200)
            if isinstance(status, int) and status >= 400:
                transaction.rollback()
            return result
    return wrapped


def lock_contest(contest_id):
    from models.db_models import Contest, get_database
    query = Contest.select().where(Contest.id == contest_id)
    if get_database().__class__.__name__ != 'SqliteDatabase':
        query = query.for_update()
    import time
    from flask import g, has_request_context
    started = time.monotonic()
    try:
        return query.get()
    finally:
        if has_request_context():
            g.contest_lock_wait = getattr(g, 'contest_lock_wait', 0.) + time.monotonic()-started
