from __future__ import annotations

import argparse
import json

from .sessions import build_execution_plan, default_feature_workstream, packets_for_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate branch-scoped packets for parallel ChatSOL sessions."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    feature = sub.add_parser("feature", help="plan a standard feature workstream")
    feature.add_argument("--key", required=True)
    feature.add_argument("--code", action="append", required=True)
    feature.add_argument("--tests", action="append", required=True)
    feature.add_argument("--docs", action="append", default=[])
    feature.add_argument("--base", default="main")
    feature.add_argument("--max-parallel", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "feature":
        items = default_feature_workstream(
            args.key,
            code_paths=args.code,
            test_paths=args.tests,
            doc_paths=args.docs or ("README.md",),
        )
        plan = build_execution_plan(items, max_parallel=args.max_parallel)
        output = {
            "base_branch": args.base,
            "waves": [
                [assignment.session_id for assignment in wave]
                for wave in plan.waves
            ],
            "packets": packets_for_plan(plan, base_branch=args.base),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
