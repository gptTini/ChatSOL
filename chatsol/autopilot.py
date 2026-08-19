from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from .autodev import RepoSignals, TaskCandidate, choose_next, propose_tasks
from .inspector import LocalRepoSnapshot, inspect_local_repo, signals_from_snapshot
from .sessions import (
    ExecutionPlan,
    SessionRole,
    WorkItem,
    build_execution_plan,
    default_feature_workstream,
    packets_for_plan,
)


@dataclass(frozen=True)
class AutopilotDecision:
    snapshot: LocalRepoSnapshot
    signals: RepoSignals
    candidates: tuple[TaskCandidate, ...]
    selected: TaskCandidate | None
    execution_plan: ExecutionPlan | None


def _docs_workstream(task: TaskCandidate) -> list[WorkItem]:
    scout = WorkItem(
        key=f"{task.key}.scout",
        title=f"Inspect documentation gap for {task.title}",
        role=SessionRole.SCOUT,
        read_paths=("chatsol", "README.md", "docs"),
        instructions="Identify exact undocumented public APIs with file-level evidence.",
    )
    docs = WorkItem(
        key=f"{task.key}.docs",
        title=task.title,
        role=SessionRole.DOCS,
        read_paths=("chatsol",),
        write_paths=("README.md", "docs"),
        depends_on=(scout.key,),
        effort=max(1, int(round(task.effort))),
        instructions="Document only verified public behavior.",
    )
    reviewer = WorkItem(
        key=f"{task.key}.review",
        title=f"Review {task.title}",
        role=SessionRole.REVIEWER,
        read_paths=("chatsol", "README.md", "docs"),
        depends_on=(docs.key,),
        instructions="Reject claims not supported by code or tests.",
    )
    integrator = WorkItem(
        key=f"{task.key}.integrate",
        title=f"Integrate {task.title}",
        role=SessionRole.INTEGRATOR,
        read_paths=("README.md", "docs"),
        write_paths=("README.md", "docs"),
        depends_on=(reviewer.key,),
        instructions="Integrate only a green docs report.",
    )
    return [scout, docs, reviewer, integrator]


def workstream_for_candidate(task: TaskCandidate) -> list[WorkItem]:
    if task.key == "document-public-api":
        return _docs_workstream(task)
    return default_feature_workstream(
        task.key,
        code_paths=("chatsol",),
        test_paths=("tests",),
        doc_paths=("README.md", "docs"),
    )


def decide_autonomous_cycle(
    root: str | Path,
    *,
    budget: float = 4,
    max_parallel: int = 4,
    run_tests: bool = False,
    security_alerts: int = 0,
    stale_dependencies: int = 0,
    flaky_tests: int = 0,
    coverage_gap: float = 0.0,
) -> AutopilotDecision:
    snapshot = inspect_local_repo(root, run_tests=run_tests)
    signals = signals_from_snapshot(
        snapshot,
        security_alerts=security_alerts,
        stale_dependencies=stale_dependencies,
        flaky_tests=flaky_tests,
        coverage_gap=coverage_gap,
    )
    candidates = tuple(propose_tasks(signals))
    selected = choose_next(candidates, budget)
    plan = None
    if selected is not None:
        plan = build_execution_plan(
            workstream_for_candidate(selected),
            max_parallel=max_parallel,
        )
    return AutopilotDecision(snapshot, signals, candidates, selected, plan)


def _serialize(decision: AutopilotDecision) -> dict[str, object]:
    return {
        "snapshot": asdict(decision.snapshot),
        "signals": asdict(decision.signals),
        "candidates": [asdict(candidate) for candidate in decision.candidates],
        "selected": asdict(decision.selected) if decision.selected else None,
        "waves": (
            [[assignment.session_id for assignment in wave] for wave in decision.execution_plan.waves]
            if decision.execution_plan
            else []
        ),
        "packets": packets_for_plan(decision.execution_plan) if decision.execution_plan else [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect ChatSOL and plan one autonomous cycle.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--budget", type=float, default=4)
    parser.add_argument("--max-parallel", type=int, default=4)
    parser.add_argument("--run-tests", action="store_true")
    args = parser.parse_args(argv)

    decision = decide_autonomous_cycle(
        args.root,
        budget=args.budget,
        max_parallel=args.max_parallel,
        run_tests=args.run_tests,
    )
    print(json.dumps(_serialize(decision), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
