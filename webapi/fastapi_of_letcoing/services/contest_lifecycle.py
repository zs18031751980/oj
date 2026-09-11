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
    return bool(is_manager or (is_public and lifecycle_state not in {'DRAFT', 'CANCELLED'}))
