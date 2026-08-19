from __future__ import annotations

import re
from typing import Iterable

from .models import WorkItem, clean_paths
from .roles import SessionRole


def _feature_key(value: str) -> str:
    key = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower()
    if not key:
        raise ValueError("feature_key must not be empty")
    return key


def default_feature_workstream(
    feature_key: str,
    *,
    code_paths: Iterable[str],
    test_paths: Iterable[str],
    doc_paths: Iterable[str] = ("README.md",),
) -> list[WorkItem]:
    """Build a four-wave pipeline with three parallel worker sessions."""
    key = _feature_key(feature_key)
    code = clean_paths(code_paths)
    tests = clean_paths(test_paths)
    docs = clean_paths(doc_paths)
    if not code or not tests:
        raise ValueError("code_paths and test_paths must not be empty")

    scout = WorkItem(
        key=f"{key}.scout",
        title=f"Audit repository context for {feature_key}",
        role=SessionRole.SCOUT,
        read_paths=tuple(dict.fromkeys(code + tests + docs)),
        instructions="Return constraints, likely failure modes, and exact evidence. Do not edit.",
    )
    impl = WorkItem(
        key=f"{key}.impl",
        title=f"Implement {feature_key}",
        role=SessionRole.IMPLEMENTER,
        read_paths=tuple(dict.fromkeys(code + tests)),
        write_paths=code,
        depends_on=(scout.key,),
        effort=3,
        instructions="Keep the implementation bounded to the assigned code scope.",
    )
    tester = WorkItem(
        key=f"{key}.tests",
        title=f"Write adversarial tests for {feature_key}",
        role=SessionRole.TESTER,
        read_paths=code,
        write_paths=tests,
        depends_on=(scout.key,),
        effort=2,
        instructions="Design tests independently from implementation; include negative cases.",
    )
    docs_item = WorkItem(
        key=f"{key}.docs",
        title=f"Document {feature_key}",
        role=SessionRole.DOCS,
        read_paths=tuple(dict.fromkeys(code + tests)),
        write_paths=docs,
        depends_on=(scout.key,),
        effort=1,
        instructions="Document intended behavior and usage; do not claim unverified results.",
    )
    review = WorkItem(
        key=f"{key}.review",
        title=f"Review integrated {feature_key} change",
        role=SessionRole.REVIEWER,
        read_paths=tuple(dict.fromkeys(code + tests + docs)),
        depends_on=(impl.key, tester.key, docs_item.key),
        effort=2,
        instructions="Review integrated outputs; report blockers with file-level evidence.",
    )
    integrate = WorkItem(
        key=f"{key}.integrate",
        title=f"Integrate verified {feature_key} outputs",
        role=SessionRole.INTEGRATOR,
        read_paths=tuple(dict.fromkeys(code + tests + docs)),
        write_paths=tuple(dict.fromkeys(code + tests + docs)),
        depends_on=(review.key,),
        effort=1,
        instructions="Merge only green outputs, resolve conflicts conservatively, run full suite.",
    )
    return [scout, impl, tester, docs_item, review, integrate]
