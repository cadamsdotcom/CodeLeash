---
title: 'Agent Optimizations'
sidebar_position: 5
---

CodeLeash configures Claude Code to prevent common agent misbehaviors through deny rules, hooks, and environment settings. These are defined in [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json) and enforced automatically.

## Deny Rules

The `permissions.deny` list blocks commands that agents should never run directly:

```json
{
  "permissions": {
    "deny": [
      "Bash(pre-commit *)",
      "Bash(uv run pre-commit*)",
      "Bash(npx vitest*)",
      "Bash(uv run pytest*)"
    ]
  }
}
```

> [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json)

| Blocked Command                    | Why                                             | Correct Alternative   |
| ---------------------------------- | ----------------------------------------------- | --------------------- |
| `uv run pytest`                    | Bypasses npm wrapper, may fail with permissions | `npm run test:python` |
| `npx vitest`                       | Bypasses npm wrapper                            | `npm test`            |
| `pre-commit` / `uv run pre-commit` | Bypasses npm wrapper                            | `npm run pre-commit`  |

The `npm run` wrappers ensure consistent environment setup and output formatting.

## PreToolUse Bash Hooks

Five `PreToolUse` hooks on `Bash` commands block common mistakes:

### Test Pipe Blocking

The hook uses a regex to detect any test command followed by `|`, `;`, or `>`:

```bash
if [[ "$cmd" =~ ^(npm run test|npm test).*(\\||;|>) ]]; then
  echo "BLOCKED: Test commands must not be piped, chained, or redirected." >&2
  exit 2
fi
```

> [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json)

This forces agents to see complete test output --- no filtering, no redirection. Agents that can't see full output make worse debugging decisions.

### Direct Python Blocking

```bash
if [[ "$cmd" =~ ^python ]]; then
  echo "BLOCKED: python must be run via uv." >&2; exit 2
fi
```

> [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json)

All Python execution must go through `uv run` to ensure the correct virtual environment and dependencies.

### py_compile Blocking

Agents sometimes try to syntax-check files before running tests. This is unnecessary since syntax errors surface immediately in test runs.

### Timeout Wrapper Blocking

Wrapping commands in `timeout` changes the command string, preventing it from matching against permission allowlist entries and forcing unnecessary permission prompts.

### Supabase Production Guard

Commands that modify production Supabase resources (`db push --linked`, `functions deploy`, `secrets set`) are blocked. Deployment is the user's responsibility.

## Allow Rules

The `permissions.allow` list grants pre-approval for specific commands:

```json
{
  "permissions": {
    "allow": ["Bash(uv run python -m scripts.tdd_log:*)"]
  }
}
```

This allows the TDD log commands to run without prompting the user for approval each time.

## Git Commit Hook

The [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh) script installs a git pre-commit hook that runs `npm run test:all` on every commit:

```bash
#!/bin/bash
# Pre-commit hook installed by init.sh
set -e
npm run test:all
```

> [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh)

This means every commit runs:

1. Pre-commit checks (black, isort, ruff, prettier, eslint, type-check, all custom checks)
2. Vitest (React component tests)
3. pytest (unit + integration tests)
4. E2E tests (with isolated Supabase instance)

If any of these fail, the commit is rejected.

## Environment Settings

```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  }
}
```

These disable feedback surveys and non-essential network requests, keeping the agent focused on the task.

## PostToolUse Hooks

Both `PostToolUse` and `PostToolUseFailure` hooks on `Bash` run [`tdd_post_bash.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_post_bash.py), which logs every command execution to the TDD log with its outcome. This provides a complete audit trail and drives state transitions in the TDD guard.

## Stop and PreCompact Hooks

- **Stop hook**: Fires when a session ends. Prompts the agent to write learnings to `.claude/learnings/` and review its TDD log for inappropriate overrides.
- **PreCompact hook**: Fires before context compaction. Same prompt as Stop --- ensures learnings are captured before context is compressed.

The Stop hook prompt:

```
SESSION ENDING -- If you learned anything noteworthy,
create .claude/learnings/{date}-{slug}.md. Include surprises,
key learnings, hook/workflow recommendations. Also review your
TDD log for inappropriate overrides or skip-red usage.
```

> [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json)

Both hooks encourage the agent to reflect on its session, producing structured notes that benefit future sessions.

## Dot Silencing

Test progress dots (`.....F..`) are suppressed in pytest output via the `pytest_report_teststatus` hook in [`tests/conftest.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/tests/conftest.py):

```python
def pytest_report_teststatus(report, config):
    if report.passed and report.when == "call":
        return report.outcome, "", report.outcome.upper()
```

Agents don't need visual progress --- they need structured pass/fail results. This reduces output noise and context window usage.
