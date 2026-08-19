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
