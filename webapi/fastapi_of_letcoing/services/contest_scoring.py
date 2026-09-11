"""ICPC/ACM 排名领域规则。

本模块不依赖 Flask 或数据库。控制器、异步榜单消费者和复判任务复用同一套
纯函数，避免不同路径对 CE、罚时及 tie-break 的解释出现偏差。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


ACCEPTED_VERDICTS = frozenset({"AC", "Accepted"})
PENALIZED_REJECTIONS = frozenset(
    {"WA", "RE", "TLE", "MLE", "OLE", "NO_OUTPUT", "Partial"}
)


def _as_datetime(value: Any) -> datetime | None:
    parsed = None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed is None:
        return None
    # 排名域统一使用 UTC naive，兼容历史数据库墙钟与 API ISO 时间，避免排序时
    # aware/naive 混用导致整个榜单 500。
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _minutes_since(submitted_at: datetime | None, start_at: datetime) -> int:
    if submitted_at is None:
        return 0
    try:
        return max(0, int((submitted_at - start_at).total_seconds() // 60))
    except TypeError:
        # 不混用 aware / naive。生产路径统一由数据库 UTC 时间传入；异常值不应
        # 令榜单服务不可用，后续可通过审计任务修复该条数据。
        return 0


def compute_acm_scoreboard(
    *,
    entries: Iterable[Mapping[str, Any]],
    problem_indexes: Iterable[str],
    submissions: Iterable[Mapping[str, Any]],
    start_at: datetime,
    penalty_minutes: int = 20,
    cutoff_at: datetime | None = None,
) -> list[dict[str, Any]]:
    """按 ICPC/ACM 规则计算榜单。

    ``entries`` 必须包含所有有效参赛实体，所以没有提交的参赛者也会出现在榜单。
    ``submissions`` 只应包含比赛有效窗口内、最终判题完成的提交。
    """
    problem_order = list(problem_indexes)
    state_by_entry: dict[int, dict[str, Any]] = {}
    for entry in entries:
        entry_id = int(entry["entry_id"])
        state_by_entry[entry_id] = {
            "entry": dict(entry),
            "problems": {
                problem_index: {
                    "solved": False,
                    "wrong_before_ac": 0,
                    "first_ac_at": None,
                    "solve_minutes": None,
                    "submissions": 0,
                    "status": "—",
                }
                for problem_index in problem_order
            },
        }

    ordered_submissions = sorted(
        submissions,
        key=lambda row: (_as_datetime(row.get("received_at")) or datetime.max, int(row.get("id", 0))),
    )
    for submission in ordered_submissions:
        entry_id = int(submission["entry_id"])
        problem_index = str(submission["problem_index"])
        entry_state = state_by_entry.get(entry_id)
        if entry_state is None or problem_index not in entry_state["problems"]:
            continue
        problem = entry_state["problems"][problem_index]
        verdict = str(submission.get("verdict") or submission.get("status") or "")
        submitted_at = _as_datetime(submission.get("received_at"))
        if cutoff_at is not None and submitted_at is not None and submitted_at > cutoff_at:
            continue
        problem["submissions"] += 1

        if problem["solved"]:
            continue
        if verdict in ACCEPTED_VERDICTS:
            problem["solved"] = True
            problem["first_ac_at"] = submitted_at
            problem["solve_minutes"] = _minutes_since(submitted_at, start_at)
            problem["status"] = "AC"
        elif verdict in PENALIZED_REJECTIONS:
            problem["wrong_before_ac"] += 1
            problem["status"] = verdict

    rows: list[dict[str, Any]] = []
    for entry_id, entry_state in state_by_entry.items():
        problems = entry_state["problems"]
        solved = [problem for problem in problems.values() if problem["solved"]]
        penalty = sum(
            int(problem["solve_minutes"] or 0)
            + int(problem["wrong_before_ac"]) * penalty_minutes
            for problem in solved
        )
        last_ac_at = max(
            (problem["first_ac_at"] for problem in solved if problem["first_ac_at"] is not None),
            default=None,
        )
        row = dict(entry_state["entry"])
        row.update(
            {
                "entry_id": entry_id,
                "solved_count": len(solved),
                "penalty": penalty,
                "last_ac_at": last_ac_at,
                "problems": problems,
            }
        )
        rows.append(row)

    rows.sort(
        key=lambda row: (
            -row["solved_count"],
            row["penalty"],
            row["last_ac_at"] or datetime.max,
            row["entry_id"],
        )
    )
    for position, row in enumerate(rows, 1):
        row["rank"] = position
    return rows
