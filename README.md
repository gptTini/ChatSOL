# ChatSOL

A small sandbox for testing whether a normal ChatGPT conversation running **GPT-5.6 Sol** can act as the coding agent itself: inspect code, write changes, execute tests, react to failures, choose follow-up work, and push fixes through GitHub without handing the coding task to a separate Codex session.

## First experiment: coding feedback loop

The repository started with a GitHub repository-reference parser and adversarial tests.

1. Sol wrote a minimal implementation and tests.
2. The tests reproduced two SSH parsing failures.
3. Sol revised the parser and reached 7/7 passing tests.
4. Sol added new adversarial cases instead of stopping at green.
5. An unsupported `ftp://` remote exposed another bug.
6. Sol restricted allowed remote schemes and reached 12/12 passing tests.
7. GitHub Actions independently verified the branch successfully.

## Second experiment: autonomous work selection

`chatsol.autodev` adds a small deterministic policy layer for deciding what to work on next.

A task has impact, urgency, confidence, effort, risk, and blocked state. ChatSOL scores candidates, refuses blocked work, fits work into an effort budget, validates hostile/invalid inputs, and can generate candidates from repository-health signals.

The second build loop deliberately strengthened its own tests after reaching green:

1. Initial prioritizer: 8 tests, 2 failures because blocked work could still be selected.
2. Blocked-work fix: 8/8 passing and GitHub Actions green.
3. Adversarial validation suite: 15 tests exposed invalid numeric state, duplicate task IDs, and invalid budget handling.
4. Validation fix: 15/15 passing and GitHub Actions green.
5. Repository-signal task generation added; the full local suite reached 23/23.
6. The new planner was then applied to ChatSOL itself. It selected `document-public-api` as the next feasible task, which produced this README update.

### Public API

- `TaskCandidate`: immutable candidate work item.
- `RepoSignals`: validated snapshot of repository-health counters.
- `score_task(task)`: calculate deterministic utility.
- `rank_tasks(tasks)`: rank unique candidates deterministically.
- `choose_next(tasks, budget)`: choose the best feasible, unblocked task.
- `plan_cycle(tasks, budget)`: greedily build a bounded work cycle.
- `propose_tasks(signals)`: generate development candidates from repository signals.
- `plan_from_signals(signals, budget)`: generate and prioritize a complete bounded cycle.

Example:

```python
from chatsol.autodev import RepoSignals, plan_from_signals

signals = RepoSignals(failing_tests=2, todo_count=12, coverage_gap=15)
plan = plan_from_signals(signals, budget=5)

for task in plan:
    print(task.key, task.title, task.effort)
```

## Run locally

```bash
python -m unittest discover -s tests -v
```

## Repository-reference examples

```text
gptTini/ChatSOL
https://github.com/gptTini/ChatSOL.git
git@github.com:gptTini/ChatSOL.git
ssh://git@github.com/gptTini/ChatSOL.git
git://github.com/gptTini/ChatSOL.git
```

Non-GitHub hosts, deceptive hosts, unsupported URL schemes, and repository URLs with extra path components are rejected.

## Control loop

```text
inspect -> propose -> prioritize -> implement -> execute -> observe -> critique -> revise -> verify -> repeat
```

The reasoning and code generation in these experiments is performed by the Sol model in the ChatGPT conversation. GitHub and the execution environment provide the external read/write/test surfaces.
