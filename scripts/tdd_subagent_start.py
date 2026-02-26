"""TDD Guard - SubagentStart hook.

Creates a per-agent TDD log file and injects additionalContext so the
subagent knows which log file to use for its TDD cycles.
"""

import json
import sys
from pathlib import Path


def main() -> None:
    input_data = json.load(sys.stdin)
    agent_id = input_data.get("agent_id", "")

    if not agent_id:
        # No agent_id - nothing to do
        return

    log_name = f"tdd-agent-{agent_id}.log"
    log_path = Path(log_name)

    # Create the empty log file (or touch if it exists)
    log_path.touch()

    # Build usage instructions for the subagent
    context = f"""TDD SUBAGENT: Your TDD log file is: {log_name}
Use --log "{log_name}" with all tdd_log commands.

TDD Red-Green-Refactor cycle:

  1. Start writing tests (declare what you expect to fail):
     uv run python -m scripts.tdd_log --log "{log_name}" red \\
       --test "path/to/test_file" \\
       --expects "test_name fails because ..."

  2. Write the failing test, then run it to confirm it fails.

  3. Start making tests pass (declare what you will change):
     uv run python -m scripts.tdd_log --log "{log_name}" green \\
       --change "what you plan to do" \\
       --file "path/to/file1.py" --file "path/to/file2.py"

  4. Edit only the declared files, then run tests to confirm they pass.

  For refactoring, lint-only, or adding-coverage (no Red cycle needed):
     uv run python -m scripts.tdd_log --log "{log_name}" green --skip-red \\
       --reason=refactoring --change "what you plan to do" \\
       --file "path/to/file.py"

BEFORE YOU FINISH: Write a reflection file at .claude/learnings/{{date}}-{{slug}}.md
if you learned anything noteworthy. Include surprises about the codebase, key
learnings, and review your TDD log for inappropriate overrides or skip-red usage."""

    output = {"hookSpecificOutput": {"additionalContext": context}}

    print(json.dumps(output))


if __name__ == "__main__":
    main()
