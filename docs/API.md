# ChatSOL API reference — slice 1

This page documents the first bounded slice of the multi-session orchestration API. The goal is to keep worker sessions small enough to finish inside one development-cycle budget while still reducing a measurable documentation gap.

## `SessionRole`

Enum of the supported worker roles: coordinator, scout, implementer, tester, reviewer, docs, and integrator. Role policy such as whether a role may write is defined separately in `ROLE_SPECS`.

## `WorkItem`

Immutable description of one schedulable task. It carries a stable key, role, read paths, write paths, dependencies, effort, and instructions. Read-only roles are rejected if they claim a write scope.

## `SessionReport`

Handoff returned by a worker session. Status is one of `passed`, `failed`, or `blocked`; writing sessions additionally need a commit SHA before integration can be considered ready.

## `ExecutionPlan`

Container for dependency waves. Its `assignments` property flattens all waves into the ordered set of session assignments.

## `build_execution_plan`

Builds a conflict-aware wave plan from `WorkItem` objects. Dependencies are honored, `max_parallel` limits each wave, and overlapping write scopes are never scheduled in the same wave.

## `write_scopes_conflict`

Returns whether two work items claim overlapping write paths. Parent/child paths such as `src/core` and `src/core/file.py` conflict.

## `assignment_packet`

Converts one scheduled assignment into the JSON-friendly contract given to a worker conversation: role, mission, branch, read/write scope, dependencies, completion gate, and handoff requirements.

## `default_feature_workstream`

Creates the standard four-wave feature pipeline:

```text
scout
  ↓
implementer + tester + docs   (parallel)
  ↓
reviewer
  ↓
integrator
```

The middle workers receive disjoint write scopes so they can be executed by separate sessions concurrently.
