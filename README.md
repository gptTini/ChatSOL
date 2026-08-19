# ChatSOL

A sandbox for testing whether a normal ChatGPT conversation running **GPT-5.6 Sol** can act as the coding agent itself: inspect code, write changes, execute tests, react to failures, choose follow-up work, split work into session-scoped branches, and push verified fixes through GitHub without handing the coding task to a separate Codex session.

## Experiment 1: coding feedback loop

The repository started with a GitHub repository-reference parser and adversarial tests.

1. Sol wrote a minimal implementation and tests.
2. Tests reproduced SSH parsing failures.
3. Sol revised the parser and reached green.
4. Sol added new adversarial cases instead of stopping.
5. An unsupported `ftp://` remote exposed another bug.
6. Sol fixed it and GitHub Actions independently verified the result.

## Experiment 2: autonomous work selection

`chatsol.autodev` adds a deterministic policy layer for deciding what to work on next.

A task has impact, urgency, confidence, effort, risk, and blocked state. ChatSOL scores candidates, refuses blocked work, fits work into a cycle budget, validates hostile inputs, and generates candidates from `RepoSignals`.

Core API:

- `TaskCandidate`
- `RepoSignals`
- `score_task`
- `rank_tasks`
- `choose_next`
- `plan_cycle`
- `propose_tasks`
- `plan_from_signals`

## Experiment 3: repository autopilot + multi-session orchestration

The third experiment separates **decision**, **execution**, **review**, and **integration** instead of making one conversation own every concern.

`inspect_local_repo` scans repository state and converts it into health signals. `decide_autonomous_cycle` ranks the resulting candidate work and creates an `ExecutionPlan`. If an important task is larger than the current cycle budget, the autopilot takes a bounded slice instead of starving the task forever.

The session scheduler then decomposes work into branch-scoped packets:

```text
Wave 1
└─ scout

Wave 2 (parallel)
├─ implementer   -> product-code scope
├─ tester        -> test scope
└─ docs          -> documentation scope

Wave 3
└─ reviewer

Wave 4
└─ integrator
```

`build_execution_plan` prevents sessions with overlapping write scopes from entering the same wave. `assignment_packet` gives each worker only its role, branch, read/write scope, dependencies, completion gate, and handoff contract. Writing sessions must return a commit SHA before `integration_ready` can become true.

GitHub Actions mirrors this separation with independent `core`, `autodev`, `sessions`, and `autopilot` test lanes, followed by an autopilot dry run.

### Self-loop evidence

The autopilot was applied to ChatSOL itself during this build:

1. The first scan falsely counted TODO text from fixtures/docs as product debt.
2. The scanner was narrowed to product code, which exposed a second self-reference bug: its own `"TODO"` string was being counted.
3. TODO detection was replaced with Python comment-token inspection; the next scan reported `todo_count = 0` and `failing_tests = 0`.
4. The remaining task was `Document 24 public API(s)`, estimated above a cycle budget of 4.
5. Starvation protection converted it into a bounded effort-4 slice.
6. The generated docs worker branch added the first API slice through PR #4, passed the parallel CI lanes, and merged into the integration branch.
7. The next scan measured the documentation gap dropping from **24 to 16 APIs** and selected the next bounded slice.

This is the closed control loop:

```text
inspect
  -> propose
  -> prioritize
  -> split into session packets
  -> execute on isolated branches
  -> verify in parallel
  -> review
  -> integrate
  -> inspect again
```

## Multi-session usage

Generate packets for a feature:

```bash
python -m chatsol.session_cli feature \
  --key scheduler-v2 \
  --code chatsol/scheduler.py \
  --tests tests/test_scheduler.py \
  --docs docs/scheduler.md \
  --max-parallel 4
```

Run one autonomous repository decision:

```bash
python -m chatsol.autopilot --root . --budget 4 --max-parallel 4 --run-tests
```

See [`docs/MULTI_SESSION.md`](docs/MULTI_SESSION.md) for the role/branch/handoff protocol and [`docs/API.md`](docs/API.md) for the API reference slices.

### Current transport limitation

ChatSOL can generate packets, branches, conflict rules, reports, and integration gates, but **one ChatGPT conversation cannot spawn several independent ChatGPT conversations by itself**. To get true multi-Sol concurrency today, start separate chats (or a future API runner) with one generated packet per chat. The repository side is already designed so those sessions can work concurrently without sharing a mutable write scope.

## Run tests

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

The reasoning and code generation in these experiments is performed by the Sol model in the ChatGPT conversation. GitHub and the execution environment provide the external read/write/test surfaces.
