# Multi-session ChatSOL

ChatSOL is structured so multiple independent GPT-5.6 Sol conversations can work on one repository without every session becoming a general-purpose agent.

The repository does **not** spawn ChatGPT conversations by itself. A human or a future API runner starts the sessions. ChatSOL's job is to make those sessions deterministic, branch-scoped, conflict-aware, and easy to integrate.

## Roles

| Role | Writes? | Responsibility |
| --- | --- | --- |
| coordinator | no | Decompose the goal, schedule waves, hand each session one packet |
| scout | no | Inspect repository evidence and constraints |
| implementer | yes | Change only assigned product-code paths |
| tester | yes | Build adversarial tests independently |
| docs | yes | Update docs/handoffs without changing behavior |
| reviewer | no | Review the integrated diff and report blockers |
| integrator | yes | Combine only green outputs and run the full suite |

The key rule is **one owner per write scope**. Sessions may read overlapping code, but two sessions are not placed in the same wave when their write paths overlap.

## Default feature pipeline

```text
Wave 1
└─ scout

Wave 2 (parallel)
├─ implementer  -> code branch
├─ tester       -> test branch
└─ docs         -> docs branch

Wave 3
└─ reviewer     -> reads integrated Wave 2 output

Wave 4
└─ integrator   -> merges green worker outputs + full verification
```

This makes the expensive middle of the development cycle parallel while keeping review and merge serialized.

## Generate session packets

```bash
python -m chatsol.session_cli feature \
  --key scheduler-v2 \
  --code chatsol/scheduler.py \
  --tests tests/test_scheduler.py \
  --docs docs/scheduler.md \
  --max-parallel 4
```

The JSON output contains waves plus one packet per conversation. Give **one packet to one ChatGPT session**. Each packet includes its role, branch, read/write scope, dependencies, completion gate, and handoff contract.

## Session handoff

Every worker should return a report with:

```json
{
  "status": "passed",
  "summary": "what changed",
  "evidence": ["tests or exact files"],
  "head_sha": "commit sha for writing roles",
  "blockers": []
}
```

Read-only roles can pass without a commit SHA. Writing roles cannot pass integration without one.

## Why branches matter

Parallel sessions should not share a mutable working tree. Each worker gets its own branch:

```text
session/implementer-...
session/tester-...
session/docs-...
```

The coordinator treats branches as isolated workspaces. The integrator combines them after their reports are green. This means the tester can design tests from the same starting point without being biased by the implementer's in-progress edits.

## Current limitation

Inside this single ChatGPT conversation, ChatSOL can plan the packets and act as one of the workers, but it cannot create several independent ChatGPT conversations on its own. The architecture intentionally keeps the transport layer separate so a future API/agent runner can submit the exact same packets concurrently without changing the scheduler.
