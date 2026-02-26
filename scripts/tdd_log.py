"""TDD Guard - CLI for writing Red/Green log declarations.

Replaces fragile echo chains with a single script invocation.
The --log flag specifies the log filename (resolved relative to project root).

Usage:
  uv run python -m scripts.tdd_log --log tdd-abc123.log red --test "path/to/test" --expects "why"
  uv run python -m scripts.tdd_log --log tdd-abc123.log green --change "what" --file "app/x.py"
  uv run python -m scripts.tdd_log --log tdd-abc123.log green --skip-red --change "Fix lint" --file "src/Foo.tsx"
"""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from .tdd_common import read_state

# Valid reasons for using --skip-red
VALID_SKIP_RED_REASONS = frozenset({"refactoring", "lint-only", "adding-coverage"})


def _now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def cmd_red(args: argparse.Namespace) -> None:
    log_path = Path(args.log)
    state = read_state(log_path)

    # Determine if this is an override (logging Red when not in initial state)
    phase_label = "Red"
    if state != "initial":
        phase_label = f"Red (override from {state})"

    with open(log_path, "a") as f:
        f.write("\n")
        f.write(f"## {phase_label} - {_now_iso()}\n")
        f.write(f"Test: {args.test}\n")
        f.write(f"Expects: {args.expects}\n")
        f.write("\n")


def cmd_green(args: argparse.Namespace) -> int:
    log_path = Path(args.log)
    skip_red = getattr(args, "skip_red", False)
    reason = getattr(args, "reason", None)

    # Read state upfront (needed for both validation and override detection)
    state = read_state(log_path)

    # Validate skip-red requires a valid reason
    if skip_red:
        if not reason:
            print(
                "ERROR: --skip-red requires --reason.\n"
                "Valid reasons: refactoring, lint-only, adding-coverage",
                file=sys.stderr,
            )
            return 1
        if reason not in VALID_SKIP_RED_REASONS:
            print(
                f"ERROR: Invalid --reason '{reason}'.\n"
                "Valid reasons: refactoring, lint-only, adding-coverage",
                file=sys.stderr,
            )
            return 1

    # Validate state: Green requires a preceding Red cycle (test must have failed)
    if not skip_red and state not in ("red", "making_tests_pass"):
        if state == "writing_tests":
            print(
                "ERROR: Run your failing test(s) before logging Green.\n"
                "You declared a writing-tests phase but haven't seen "
                "test(s) fail yet.",
                file=sys.stderr,
            )
        else:
            print(
                "ERROR: Cannot log Green without a preceding Red cycle.\n"
                "Start writing tests first, write failing test(s) or "
                "modify existing test(s) to fail, then run them.",
                file=sys.stderr,
            )
        return 1

    # Determine if this is an override
    is_override = state != "initial" if skip_red else state == "making_tests_pass"

    # Build phase label
    if skip_red:
        phase_label = (
            f"Green (skip-red, override from {state})"
            if is_override
            else "Green (skip-red)"
        )
    else:
        phase_label = f"Green (override from {state})" if is_override else "Green"

    with open(log_path, "a") as f:
        f.write("\n")
        f.write(f"## {phase_label} - {_now_iso()}\n")
        f.write(f"Change: {args.change}\n")
        for file in args.file:
            f.write(f"File: {file}\n")
        if skip_red and reason:
            f.write(f"Reason: {reason}\n")
        f.write("\n")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Write TDD log entries")
    parser.add_argument(
        "--log", required=True, help="Log filename (e.g. tdd-abc123.log)"
    )
    sub = parser.add_subparsers(dest="phase", required=True)

    red = sub.add_parser("red", help="Log Red phase declaration")
    red.add_argument("--test", required=True, help="Path to the test file")
    red.add_argument("--expects", required=True, help="What you expect to fail and why")

    green = sub.add_parser("green", help="Log Green phase declaration")
    green.add_argument("--change", required=True, help="What you plan to change")
    green.add_argument(
        "--file", required=True, action="append", help="File(s) you will edit"
    )
    green.add_argument(
        "--skip-red",
        action="store_true",
        default=False,
        help="Skip Red cycle requirement (requires --reason)",
    )
    green.add_argument(
        "--reason",
        choices=["refactoring", "lint-only", "adding-coverage"],
        help=(
            "Required with --skip-red. "
            "refactoring: renaming, moving code, no behavior change. "
            "lint-only: formatting, lint fixes, type annotations. "
            "adding-coverage: adding test coverage for code that already works."
        ),
    )

    args = parser.parse_args()

    if args.phase == "red":
        cmd_red(args)
    elif args.phase == "green":
        exit_code = cmd_green(args)
        if exit_code:
            sys.exit(exit_code)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
