---
title: 'TDD Guard'
sidebar_position: 3
---

The TDD Guard is a state machine enforced through Claude Code hooks. It ensures agents follow the Red-Green-Refactor cycle by blocking file edits and tracking test outcomes. The guard is implemented entirely in Python scripts that run as hook handlers.

## State Machine

The guard maintains four states:

```
initial ──→ writing_tests ──→ red ──→ making_tests_pass ──→ initial
   │            │                       │
   │         (write       (tests      (edit prod
   │          test)        fail)       files)
   │                                    │
   └────────────────────────────────────┘
                 (tests pass)
```

| State               | Meaning                                       | Allowed Actions               |
| ------------------- | --------------------------------------------- | ----------------------------- |
| `initial`           | No active TDD cycle                           | Log Red declaration only      |
| `writing_tests`     | Agent declared what test should fail          | Edit test files only          |
| `red`               | Test ran and failed (as expected)             | Log Green declaration only    |
| `making_tests_pass` | Agent declared what to change and which files | Edit declared prod files only |

When tests pass after a Green phase, the state returns to `initial`.

### State Derivation

State is derived by scanning the TDD log file bottom-up. The last significant line determines the current state:

```python
def read_state(log_path: Path) -> str:
    """Scan log bottom-up for the last significant line to derive state."""
    lines = log_path.read_text().strip().splitlines()

    for i, line in enumerate(reversed(lines)):
        stripped = line.rstrip()
        if stripped.startswith("[test]") and stripped.endswith("— SUCCEEDED"):
            return "initial"
        if stripped.startswith("[test]") and "— FAILED" in stripped:
            preceding = _find_preceding_declaration(lines, len(lines) - 1 - i)
            if preceding == "green":
                return "making_tests_pass"
            return "red"
        if stripped.startswith("## Red"):
            return "writing_tests"
        if stripped.startswith("## Green"):
            return "making_tests_pass"
    return "initial"
```

> [`scripts/tdd_common.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_common.py)

Summary of state derivation rules:

- `[test] ... — SUCCEEDED` → `initial`
- `[test] ... — FAILED` after a `## Green` header → `making_tests_pass` (test failed during Green)
- `[test] ... — FAILED` after a `## Red` header → `red` (test failed as expected)
- `## Red ...` → `writing_tests`
- `## Green ...` → `making_tests_pass`

## The CLI: `tdd_log`

Agents interact with the TDD guard through [`scripts/tdd_log.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_log.py), invoked as:

```bash
# Declare Red (writing-tests) phase
uv run python -m scripts.tdd_log --log "tdd-abc123.log" red \
  --test "path/to/test_file" \
  --expects "test_name fails because ..."

# Declare Green (making-tests-pass) phase
uv run python -m scripts.tdd_log --log "tdd-abc123.log" green \
  --change "what you plan to do" \
  --file "path/to/file1.py" --file "path/to/file2.py"

# Skip Red cycle (for refactoring, lint, or coverage)
uv run python -m scripts.tdd_log --log "tdd-abc123.log" green --skip-red \
  --reason=refactoring --change "what you plan to do" \
  --file "path/to/file.py"
```

### Green Validation

The `green` subcommand enforces prerequisites:

- Without `--skip-red`: requires state to be `red` (test must have failed) or `making_tests_pass` (re-logging)
- With `--skip-red`: requires a `--reason` from `{refactoring, lint-only, adding-coverage}`

### Overrides

Logging a Red or Green declaration at any time overrides the current state. This is useful when the agent gets stuck in the wrong state. Overrides are recorded in the log for later review.

## Pre-Edit Hook

The [`scripts/tdd_pre_edit.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_pre_edit.py) script runs as a `PreToolUse` hook on every `Edit` or `Write` tool call. It reads the current state from the TDD log and decides whether to allow or block the edit.

### File Classification

Every file is classified into one of four categories based on pattern matching:

```python
PROD_PATTERNS = [
    r"^src/",
    r"^app/",
    r"^scripts/.*\.py$",
    r"^main\.py$",
    r"^worker\.py$",
]
```

> [`scripts/tdd_common.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_common.py)

| Category   | Patterns                                                       | TDD Enforced |
| ---------- | -------------------------------------------------------------- | ------------ |
| `e2e_test` | `tests/e2e/`                                                   | No (bypass)  |
| `test`     | `*.test.{ts,tsx,js,jsx}`, `test_*.py`, `tests/`, `conftest.py` | Yes          |
| `prod`     | `src/`, `app/`, `scripts/*.py`, `main.py`, `worker.py`         | Yes          |
| `other`    | Everything else                                                | No (bypass)  |

### Permission Table

| State               | Test Files  | Prod Files                |
| ------------------- | ----------- | ------------------------- |
| `initial`           | Blocked     | Blocked                   |
| `writing_tests`     | **Allowed** | Blocked                   |
| `red`               | Blocked     | Blocked                   |
| `making_tests_pass` | Blocked\*   | Allowed (if in allowlist) |

\* Test files are allowed during `making_tests_pass` only if the Green was logged with `--skip-red`.

### Green Allowlist

During the Green phase, only files explicitly declared in the `--file` arguments are allowed. The hook scans the log backwards from the last `## Green` header, collecting `File:` lines to build the allowlist. If the agent tries to edit a file not in the allowlist, the edit is blocked with a message showing the declared files.

A warning is emitted if the allowlist exceeds 5 files, encouraging smaller increments.

## Post-Bash Hook

The [`scripts/tdd_post_bash.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_post_bash.py) script runs as a `PostToolUse` (and `PostToolUseFailure`) hook on every `Bash` tool call. It classifies commands and records outcomes:

| Command Pattern                | Tag                | Effect on State          |
| ------------------------------ | ------------------ | ------------------------ |
| `npm run test:e2e*`            | `ignored e2e test` | No state change          |
| `npm test*` or `npm run test*` | `test`             | Drives state transitions |
| Everything else                | `bash`             | Logged, no state change  |

Test commands tagged as `test` with `SUCCEEDED` status reset the state to `initial`. Test commands that `FAILED` during a writing-tests phase confirm the state as `red`.

### Example TDD Log

A full Red-Green cycle produces log entries like this:

```
## Red — 2026-02-24 10:30:00
Test: tests/unit/services/test_greeting_service.py
Expects: test_create_greeting fails because create() method doesn't exist yet

[test] npm run test:python -- tests/unit/services/test_greeting_service.py -v — FAILED

## Green — 2026-02-24 10:32:00
Change: Add create() method to GreetingService
File: app/services/greeting.py

[test] npm run test:python -- tests/unit/services/test_greeting_service.py -v — SUCCEEDED
```

## Plan Exit Hook

The [`scripts/plan_exit_hook.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/plan_exit_hook.py) runs as a `PreToolUse` hook on `ExitPlanMode`. On the first invocation per session:

1. Outputs a TDD Planning Checklist to stderr (reminding the agent to consider test levels, automation, cleanup)
2. Invokes a nested Claude CLI instance to review the plan for TDD coverage gaps:

```python
result = subprocess.run(
    ["claude", "-p", prompt],
    capture_output=True, text=True, timeout=60,
)
```

> [`scripts/plan_exit_hook.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/plan_exit_hook.py)

3. Blocks the tool call (exit 2), forcing the agent to address feedback

On the second invocation, the hook allows the call through. State is tracked per session ID in a temp file.

## Session Start Hook

The [`scripts/tdd_session_start.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_session_start.py) runs at `SessionStart` and outputs:

- The TDD log filename (derived from transcript path hash)
- Copy-pasteable Red, Green, and skip-red command examples with the correct `--log` value

This ensures agents know their log file from the very beginning of a session.

## Per-Agent Isolation

Each Claude Code session gets a unique TDD log file based on an MD5 hash of the transcript path:

```python
def get_log_path(input_data: dict) -> Path:
    transcript = input_data.get("transcript_path", "")
    if transcript:
        key = hashlib.md5(transcript.encode()).hexdigest()[:8]
        return Path(f"tdd-{key}.log")
    return Path("tdd.log")
```

> [`scripts/tdd_common.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_common.py)

This means multiple agents working in the same repo (e.g., in different worktrees or parallel sessions) each maintain their own TDD state without interference. All `tdd-*.log` files are gitignored.
