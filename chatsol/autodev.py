from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class TaskCandidate:
    """A development task that ChatSOL may choose for the next work cycle."""

    key: str
    title: str
    impact: float
    urgency: float
    confidence: float
    effort: float
    risk: float = 0.0
    blocked: bool = False

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("task key must not be empty")
        if not self.title.strip():
            raise ValueError("task title must not be empty")

        numeric = {
            "impact": self.impact,
            "urgency": self.urgency,
            "confidence": self.confidence,
            "effort": self.effort,
            "risk": self.risk,
        }
        for name, value in numeric.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

        if self.impact < 0:
            raise ValueError("impact must be non-negative")
        if self.urgency < 0:
            raise ValueError("urgency must be non-negative")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.effort <= 0:
            raise ValueError("effort must be positive")
        if self.risk < 0:
            raise ValueError("risk must be non-negative")


@dataclass(frozen=True)
class RepoSignals:
    """Small, tool-friendly snapshot of repository health."""

    failing_tests: int = 0
    flaky_tests: int = 0
    security_alerts: int = 0
    stale_dependencies: int = 0
    undocumented_public_apis: int = 0
    todo_count: int = 0
    coverage_gap: float = 0.0

    def __post_init__(self) -> None:
        counters = {
            "failing_tests": self.failing_tests,
            "flaky_tests": self.flaky_tests,
            "security_alerts": self.security_alerts,
            "stale_dependencies": self.stale_dependencies,
            "undocumented_public_apis": self.undocumented_public_apis,
            "todo_count": self.todo_count,
        }
        for name, value in counters.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

        if not math.isfinite(self.coverage_gap) or not 0 <= self.coverage_gap <= 100:
            raise ValueError("coverage_gap must be between 0 and 100")


def _validate_budget(budget: float) -> None:
    if not math.isfinite(budget) or budget < 0:
        raise ValueError("budget must be a finite non-negative number")


def score_task(task: TaskCandidate) -> float:
    """Return a deterministic utility score for a candidate task."""
    return (
        task.impact * 2.0
        + task.urgency
        + task.confidence * 5.0
        - task.effort * 1.5
        - task.risk * 2.0
    )


def rank_tasks(tasks: Iterable[TaskCandidate]) -> list[TaskCandidate]:
    """Rank tasks by utility, then prefer lower effort and stable keys."""
    materialized = list(tasks)
    keys = [task.key for task in materialized]
    if len(keys) != len(set(keys)):
        raise ValueError("task keys must be unique within a cycle")

    return sorted(materialized, key=lambda task: (-score_task(task), task.effort, task.key))


def choose_next(tasks: Iterable[TaskCandidate], budget: float) -> TaskCandidate | None:
    """Choose the highest-ranked unblocked task that fits the effort budget."""
    _validate_budget(budget)
    for task in rank_tasks(tasks):
        if not task.blocked and task.effort <= budget:
            return task
    return None


def plan_cycle(tasks: Iterable[TaskCandidate], budget: float) -> list[TaskCandidate]:
    """Greedily fill one development cycle from highest utility downward."""
    _validate_budget(budget)
    remaining = budget
    chosen: list[TaskCandidate] = []

    for task in rank_tasks(tasks):
        if task.blocked:
            continue
        if task.effort <= remaining:
            chosen.append(task)
            remaining -= task.effort

    return chosen


def propose_tasks(signals: RepoSignals) -> list[TaskCandidate]:
    """Turn repository-health signals into deterministic development candidates."""
    tasks: list[TaskCandidate] = []

    if signals.security_alerts:
        tasks.append(
            TaskCandidate(
                key="security-alerts",
                title=f"Resolve {signals.security_alerts} security alert(s)",
                impact=10,
                urgency=12,
                confidence=0.95,
                effort=min(8.0, 1.0 + signals.security_alerts),
                risk=0.5,
            )
        )

    if signals.failing_tests:
        tasks.append(
            TaskCandidate(
                key="repair-failing-tests",
                title=f"Repair {signals.failing_tests} failing test(s)",
                impact=10,
                urgency=10,
                confidence=0.95,
                effort=min(8.0, 1.0 + signals.failing_tests),
                risk=1,
            )
        )

    if signals.flaky_tests:
        tasks.append(
            TaskCandidate(
                key="stabilize-flaky-tests",
                title=f"Stabilize {signals.flaky_tests} flaky test(s)",
                impact=8,
                urgency=7,
                confidence=0.8,
                effort=min(8.0, 1.0 + signals.flaky_tests),
                risk=1,
            )
        )

    if signals.coverage_gap:
        tasks.append(
            TaskCandidate(
                key="close-coverage-gap",
                title=f"Close {signals.coverage_gap:g}% coverage gap",
                impact=6,
                urgency=4,
                confidence=0.9,
                effort=min(8.0, max(1.0, signals.coverage_gap / 10.0)),
                risk=0.5,
            )
        )

    if signals.stale_dependencies:
        tasks.append(
            TaskCandidate(
                key="refresh-dependencies",
                title=f"Review {signals.stale_dependencies} stale dependency(ies)",
                impact=6,
                urgency=5,
                confidence=0.75,
                effort=min(8.0, 1.0 + signals.stale_dependencies / 2.0),
                risk=2,
            )
        )

    if signals.undocumented_public_apis:
        tasks.append(
            TaskCandidate(
                key="document-public-api",
                title=f"Document {signals.undocumented_public_apis} public API(s)",
                impact=4,
                urgency=3,
                confidence=0.95,
                effort=min(8.0, 1.0 + signals.undocumented_public_apis / 3.0),
                risk=0.2,
            )
        )

    if signals.todo_count:
        tasks.append(
            TaskCandidate(
                key="reduce-todo-debt",
                title=f"Resolve or triage {signals.todo_count} TODO(s)",
                impact=4,
                urgency=2,
                confidence=0.7,
                effort=min(8.0, 1.0 + signals.todo_count / 4.0),
                risk=0.5,
            )
        )

    return tasks


def plan_from_signals(signals: RepoSignals, budget: float) -> list[TaskCandidate]:
    """Generate and prioritize one bounded autonomous development cycle."""
    return plan_cycle(propose_tasks(signals), budget)
