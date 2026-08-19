# ChatSOL

A small sandbox for testing whether a normal ChatGPT conversation running **GPT-5.6 Sol** can act as the coding agent itself: inspect code, write changes, execute tests, react to failures, and push fixes through GitHub without handing the coding task to a separate Codex session.

## First experiment

The repository currently contains a GitHub repository-reference parser with adversarial tests. It exists mainly as a reproducible coding-loop target rather than as a finished library.

The loop used to build it was:

1. Sol wrote a minimal implementation and tests.
2. The tests reproduced two SSH parsing failures.
3. Sol revised the parser and reached 7/7 passing tests.
4. Sol added new adversarial cases instead of stopping at green.
5. An unsupported `ftp://` remote exposed another bug.
6. Sol restricted allowed remote schemes and reached 12/12 passing tests.
7. GitHub Actions independently verified the branch successfully.

## Run locally

```bash
python -m unittest discover -s tests -v
```

## Supported examples

```text
gptTini/ChatSOL
https://github.com/gptTini/ChatSOL.git
git@github.com:gptTini/ChatSOL.git
ssh://git@github.com/gptTini/ChatSOL.git
git://github.com/gptTini/ChatSOL.git
```

Non-GitHub hosts, deceptive hosts, unsupported URL schemes, and repository URLs with extra path components are rejected.

## What this proves

This repo is an experiment in the control loop:

```text
inspect -> implement -> execute -> observe -> critique -> revise -> verify
```

The model doing the reasoning and code generation is the Sol model in the ChatGPT conversation. GitHub and the execution environment provide the external read/write/test surfaces.
