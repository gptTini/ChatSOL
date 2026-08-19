from __future__ import annotations

from .models import ExecutionPlan, SessionAssignment
from .roles import ROLE_SPECS


def assignment_packet(
    assignment: SessionAssignment,
    *,
    base_branch: str = "main",
) -> dict[str, object]:
    spec = ROLE_SPECS[assignment.item.role]
    return {
        "session_id": assignment.session_id,
        "role": assignment.item.role.value,
        "mission": spec.mission,
        "task": assignment.item.title,
        "task_key": assignment.item.key,
        "base_branch": base_branch,
        "branch": assignment.branch,
        "wave": assignment.wave,
        "read_paths": list(assignment.item.read_paths),
        "write_paths": list(assignment.item.write_paths),
        "depends_on": list(assignment.item.depends_on),
        "instructions": assignment.item.instructions,
        "completion_gate": spec.completion_gate,
        "handoff": {
            "required": ["status", "summary", "evidence", "head_sha", "blockers"],
            "rule": (
                "Do not edit outside write_paths. "
                "Report blockers instead of stealing another session's scope."
            ),
        },
    }


def packets_for_plan(
    plan: ExecutionPlan,
    *,
    base_branch: str = "main",
) -> list[dict[str, object]]:
    return [assignment_packet(a, base_branch=base_branch) for a in plan.assignments]
