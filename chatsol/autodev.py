from __future__ import annotations

from dataclasses import dataclass
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
    return sorted(tasks, key=lambda task: (-score_task(task), task.effort, task.key))


def choose_next(tasks: Iterable[TaskCandidate], budget: float) -> TaskCandidate | None:
    """Choose the highest-ranked task that fits inside the effort budget."""
    for task in rank_tasks(tasks):
        if task.effort <= budget:
            return task
    return None


def plan_cycle(tasks: Iterable[TaskCandidate], budget: float) -> list[TaskCandidate]:
    """Greedily fill one development cycle from highest utility downward."""
    remaining = budget
    chosen: list[TaskCandidate] = []

    for task in rank_tasks(tasks):
        if task.effort <= remaining:
            chosen.append(task)
            remaining -= task.effort

    return chosen
