from __future__ import annotations

import hashlib
import re
from typing import Iterable, Sequence

from .models import ExecutionPlan, SessionAssignment, SessionReport, WorkItem
from .roles import ROLE_SPECS


def _path_overlaps(a: str, b: str) -> bool:
    a = a.strip("/")
    b = b.strip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def write_scopes_conflict(a: WorkItem, b: WorkItem) -> bool:
    return any(_path_overlaps(x, y) for x in a.write_paths for y in b.write_paths)


def _slug(value: str) -> str:
    readable = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower() or "task"
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:6]
    return f"{readable}-{digest}"


def _validate_graph(items: Sequence[WorkItem]) -> dict[str, WorkItem]:
    by_key: dict[str, WorkItem] = {}
    for item in items:
        if item.key in by_key:
            raise ValueError(f"duplicate work item key: {item.key}")
        by_key[item.key] = item

    for item in items:
        for dep in item.depends_on:
            if dep == item.key:
                raise ValueError(f"work item {item.key} cannot depend on itself")
            if dep not in by_key:
                raise ValueError(f"unknown dependency {dep} for {item.key}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(key: str) -> None:
        if key in visiting:
            raise ValueError("dependency cycle detected")
        if key in visited:
            return
        visiting.add(key)
        for dep in by_key[key].depends_on:
            visit(dep)
        visiting.remove(key)
        visited.add(key)

    for key in by_key:
        visit(key)
    return by_key


def build_execution_plan(
    items: Iterable[WorkItem],
    *,
    max_parallel: int = 4,
    branch_prefix: str = "session",
) -> ExecutionPlan:
    if max_parallel <= 0:
        raise ValueError("max_parallel must be positive")
    prefix = branch_prefix.strip().strip("/")
    if not prefix or re.search(r"[\s~^:?*\[\\]", prefix):
        raise ValueError("branch_prefix contains characters unsafe for Git refs")

    pending = list(items)
    _validate_graph(pending)
    completed: set[str] = set()
    waves: list[tuple[SessionAssignment, ...]] = []
    wave_no = 1

    while pending:
        ready = [item for item in pending if set(item.depends_on) <= completed]
        if not ready:
            raise ValueError("no schedulable work; dependency graph is inconsistent")

        chosen: list[WorkItem] = []
        for item in ready:
            if len(chosen) >= max_parallel:
                break
            if any(write_scopes_conflict(item, other) for other in chosen):
                continue
            chosen.append(item)

        if not chosen:
            chosen = [ready[0]]

        assignments = []
        for item in chosen:
            session_id = f"{item.role.value}-{_slug(item.key)}"
            assignments.append(
                SessionAssignment(
                    session_id=session_id,
                    branch=f"{prefix}/{session_id}",
                    wave=wave_no,
                    item=item,
                )
            )

        waves.append(tuple(assignments))
        for item in chosen:
            pending.remove(item)
            completed.add(item.key)
        wave_no += 1

    return ExecutionPlan(tuple(waves))


def integration_ready(plan: ExecutionPlan, reports: Iterable[SessionReport]) -> bool:
    by_session = {report.session_id: report for report in reports}
    for assignment in plan.assignments:
        report = by_session.get(assignment.session_id)
        if report is None or report.status != "passed":
            return False
        if ROLE_SPECS[assignment.item.role].may_write and not report.head_sha.strip():
            return False
    return True
