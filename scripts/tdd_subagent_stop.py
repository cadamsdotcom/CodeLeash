"""TDD Guard - SubagentStop hook.

Writes a FINISHED marker to the per-agent TDD log file so that
tdd_pre_edit.py's fallback chain skips finished agent logs.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    input_data = json.load(sys.stdin)
    agent_id = input_data.get("agent_id", "")

    if not agent_id:
        return

    log_path = Path(f"tdd-agent-{agent_id}.log")

    if not log_path.exists():
        return

    timestamp = datetime.now(UTC).astimezone().isoformat(timespec="seconds")
    with open(log_path, "a") as f:
        f.write(f"\n## FINISHED - {timestamp}\n")


if __name__ == "__main__":
    main()
