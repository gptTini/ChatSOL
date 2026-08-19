from __future__ import annotations

from dataclasses import dataclass
import ast
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable

from .autodev import RepoSignals


_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist", ".pytest_cache"}


@dataclass(frozen=True)
class LocalRepoSnapshot:
    python_files: int
    test_files: int
    public_apis: tuple[str, ...]
    undocumented_public_apis: tuple[str, ...]
    todo_count: int
    failing_tests: int


def _iter_files(root: Path, suffix: str) -> Iterable[Path]:
    for path in root.rglob(f"*{suffix}"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def _public_api_names(path: Path, root: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []

    rel = path.relative_to(root).with_suffix("")
    module = ".".join(rel.parts)
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            names.append(f"{module}.{node.name}")
    return names


def _documentation_corpus(root: Path) -> str:
    chunks: list[str] = []
    readme = root / "README.md"
    if readme.exists():
        chunks.append(readme.read_text(encoding="utf-8", errors="ignore"))
    docs = root / "docs"
    if docs.exists():
        for path in docs.rglob("*.md"):
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def _count_todos(paths: Iterable[Path]) -> int:
    pattern = re.compile(r"\b(?:TODO|FIXME)\b", re.IGNORECASE)
    total = 0
    for path in paths:
        try:
            total += len(pattern.findall(path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
    return total


def _run_unittest(root: Path) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return 0

    output = f"{proc.stdout}\n{proc.stderr}"
    match = re.search(r"FAILED \(([^)]*)\)", output)
    if not match:
        return 1

    failures = 0
    for part in match.group(1).split(","):
        count = re.search(r"=(\d+)", part)
        if count:
            failures += int(count.group(1))
    return max(1, failures)


def inspect_local_repo(root: str | Path, *, run_tests: bool = False) -> LocalRepoSnapshot:
    root_path = Path(root).resolve()
    python_paths = list(_iter_files(root_path, ".py"))
    test_paths = [p for p in python_paths if "tests" in p.relative_to(root_path).parts]

    api_paths = [
        p
        for p in python_paths
        if p.relative_to(root_path).parts
        and p.relative_to(root_path).parts[0] == "chatsol"
    ]
    public_apis = sorted(
        name
        for path in api_paths
        for name in _public_api_names(path, root_path)
    )

    corpus = _documentation_corpus(root_path)
    undocumented = []
    for qualified in public_apis:
        simple = qualified.rsplit(".", 1)[-1]
        if simple not in corpus and qualified not in corpus:
            undocumented.append(qualified)

    # Product debt should not be inflated by TODO examples in tests or docs.
    todo_count = _count_todos(api_paths)
    failing_tests = _run_unittest(root_path) if run_tests else 0

    return LocalRepoSnapshot(
        python_files=len(python_paths),
        test_files=len(test_paths),
        public_apis=tuple(public_apis),
        undocumented_public_apis=tuple(undocumented),
        todo_count=todo_count,
        failing_tests=failing_tests,
    )


def signals_from_snapshot(
    snapshot: LocalRepoSnapshot,
    *,
    flaky_tests: int = 0,
    security_alerts: int = 0,
    stale_dependencies: int = 0,
    coverage_gap: float = 0.0,
) -> RepoSignals:
    return RepoSignals(
        failing_tests=snapshot.failing_tests,
        flaky_tests=flaky_tests,
        security_alerts=security_alerts,
        stale_dependencies=stale_dependencies,
        undocumented_public_apis=len(snapshot.undocumented_public_apis),
        todo_count=snapshot.todo_count,
        coverage_gap=coverage_gap,
    )
