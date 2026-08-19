from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .roles import ROLE_SPECS, SessionRole


def clean_paths(values: Iterable[str]) -> tuple[str, ...]:
    cleaned = []
    for value in values:
        v = value.strip().strip("/")
        if v:
            cleaned.append(v)
    return tuple(dict.fromkeys(cleaned))


@dataclass(frozen=True)
class WorkItem:
    key: str
    title: str
    role: SessionRole
    read_paths: tuple[str, ...] = ()
    write_paths: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    effort: int = 1
    instructions: str = ""

    def __post_init__(self) -> None:
        key = self.key.strip()
        title = self.title.strip()
        if not key or not re.fullmatch(r"[A-Za-z0-9._-]+", key):
            raise ValueError("work item key must use letters, numbers, dot, underscore, or dash")
        if not title:
            raise ValueError("work item title must not be empty")
        if self.effort <= 0:
            raise ValueError("effort must be positive")
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "read_paths", clean_paths(self.read_paths))
        object.__setattr__(self, "write_paths", clean_paths(self.write_paths))
        object.__setattr__(self, "depends_on", clean_paths(self.depends_on))
        if not ROLE_SPECS[self.role].may_write and self.write_paths:
            raise ValueError(f"{self.role.value} role is read-only")


@dataclass(frozen=True)
class SessionAssignment:
    session_id: str
    branch: str
    wave: int
    item: WorkItem


@dataclass(frozen=True)
class ExecutionPlan:
    waves: tuple[tuple[SessionAssignment, ...], ...]

    @property
    def assignments(self) -> tuple[SessionAssignment, ...]:
        return tuple(assignment for wave in self.waves for assignment in wave)


@dataclass(frozen=True)
class SessionReport:
    session_id: str
    status: str
    head_sha: str = ""
    summary: str = ""
    evidence: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in {"passed", "failed", "blocked"}:
            raise ValueError("status must be passed, failed, or blocked")
        if self.status == "passed" and self.blockers:
            raise ValueError("passed report cannot contain blockers")
