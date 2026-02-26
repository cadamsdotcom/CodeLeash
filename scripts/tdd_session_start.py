"""TDD Guard - SessionStart hook.

Outputs the TDD log file name so Claude knows it from the start of the session.
"""

import json
import sys

from .tdd_common import get_log_path


def main() -> None:
    input_data = json.load(sys.stdin)
    log_path = get_log_path(input_data)
    log = log_path.name
    print(f"Your TDD log file is: {log}")
    print(f'Use --log "{log}" with all tdd_log commands.')
    print()
    print("TDD Red-Green-Refactor cycle:")
    print()
    print("  1. Start writing tests (declare what you expect to fail):")
    print(f'     uv run python -m scripts.tdd_log --log "{log}" red \\')
    print('       --test "path/to/test_file" \\')
    print('       --expects "test_name fails because ..."')
    print()
    print("  2. Write the failing test, then run it to confirm it fails.")
    print()
    print("  3. Start making tests pass (declare what you will change):")
    print(f'     uv run python -m scripts.tdd_log --log "{log}" green \\')
    print('       --change "what you plan to do" \\')
    print('       --file "path/to/file1.py" --file "path/to/file2.py"')
    print()
    print("  4. Edit only the declared files, then run tests to confirm they pass.")
    print()
    print("  For refactoring, lint-only, or adding-coverage (no Red cycle needed):")
    print(f'     uv run python -m scripts.tdd_log --log "{log}" green --skip-red \\')
    print('       --reason=refactoring --change "what you plan to do" \\')
    print('       --file "path/to/file.py"')
    print()
    print("Files subject to TDD (edits blocked until Red/Green declaration logged):")
    print("  Prod:  src/  app/  scripts/*.py  main.py  worker.py")
    print(
        "  Test:  *.test.{ts,tsx,js,jsx}  test_*.py  tests/  src/test-utils/  conftest.py"
    )
    print("  Bypass (not subject to TDD):  tests/e2e/  and all other files")


if __name__ == "__main__":
    main()
