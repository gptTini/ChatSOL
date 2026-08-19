from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class SessionRole(str, Enum):
    COORDINATOR = "coordinator"
    SCOUT = "scout"
    IMPLEMENTER = "implementer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DOCS = "docs"
    INTEGRATOR = "integrator"


@dataclass(frozen=True)
class RoleSpec:
    role: SessionRole
    mission: str
    may_write: bool
    completion_gate: str


ROLE_SPECS: Mapping[SessionRole, RoleSpec] = {
    SessionRole.COORDINATOR: RoleSpec(
        SessionRole.COORDINATOR,
        "Decompose work, assign non-overlapping scopes, track dependencies, and stop unsafe merges.",
        False,
        "Every task has an owner, dependencies, and an explicit integration gate.",
    ),
    SessionRole.SCOUT: RoleSpec(
        SessionRole.SCOUT,
        "Inspect repository state and produce evidence-backed candidate work without editing product code.",
        False,
        "Findings include exact paths/evidence and a ranked recommendation.",
    ),
    SessionRole.IMPLEMENTER: RoleSpec(
        SessionRole.IMPLEMENTER,
        "Implement one bounded code change inside the assigned write scope.",
        True,
        "Targeted tests pass and the diff stays inside assigned write paths.",
    ),
    SessionRole.TESTER: RoleSpec(
        SessionRole.TESTER,
        "Create adversarial tests and verification evidence independently of the implementation session.",
        True,
        "Tests cover the stated failure modes and fail for the intended reason before the fix when possible.",
    ),
    SessionRole.REVIEWER: RoleSpec(
        SessionRole.REVIEWER,
        "Review the integrated diff for correctness, regressions, security, and scope violations.",
        False,
        "No unresolved blocker remains; evidence references concrete files/tests.",
    ),
    SessionRole.DOCS: RoleSpec(
        SessionRole.DOCS,
        "Update public documentation and handoff notes without changing product behavior.",
        True,
        "Docs match verified behavior and expose no secrets.",
    ),
    SessionRole.INTEGRATOR: RoleSpec(
        SessionRole.INTEGRATOR,
        "Combine green worker outputs and verify the integration branch before merge.",
        True,
        "All required reports are green and integration tests pass.",
    ),
}
