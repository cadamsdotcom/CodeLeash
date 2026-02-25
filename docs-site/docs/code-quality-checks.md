---
title: 'Code Quality Checks'
sidebar_position: 6
---

CodeLeash enforces code quality through custom Python scripts that run as pre-commit hooks. Each script is a focused lint rule implemented with AST walking, regex scanning, or both. This "Python script as lint rule" pattern makes rules easy to write, test, and understand.

## Integration Chain

```
.pre-commit-config.yaml
  → npm run pre-commit (runs all hooks)
  → npm run test:all (includes pre-commit)
  → git pre-commit hook (runs test:all)
```

Every commit triggers the full chain. A failing check blocks the commit.

## The "Python Script as Lint Rule" Pattern

Each custom check is registered as a local hook in [`.pre-commit-config.yaml`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.pre-commit-config.yaml). Here's a representative entry:

```yaml
- id: check-brand-colors
  name: Check for non-permitted Tailwind color classes
  entry: uv run python scripts/check_brand_colors.py
  language: system
  files: \.(ts|tsx)$
  pass_filenames: true
```

> [`.pre-commit-config.yaml`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.pre-commit-config.yaml)

The pattern: a Python script that reads files, checks a rule, and exits nonzero on violations. No plugin API to learn --- just stdin/stdout and exit codes.

## Third-Party Hooks

Standard tools run first:

| Hook                    | Purpose                                        |
| ----------------------- | ---------------------------------------------- |
| **black**               | Python code formatting                         |
| **isort**               | Python import sorting (black profile)          |
| **ruff**                | Python linting with auto-fix                   |
| **prettier**            | JS/TS/JSON/CSS/MD formatting                   |
| **djlint**              | HTML template formatting                       |
| **trailing-whitespace** | Remove trailing whitespace                     |
| **vulture**             | Dead Python code detection (min-confidence 80) |

## Custom Checks

### Brand Colors ([`check_brand_colors.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_brand_colors.py))

Scans TypeScript/TSX files for Tailwind color classes that aren't from the approved brand palette. The script maintains a set of disallowed standard Tailwind colors and uses fast string matching:

```python
DISALLOWED_COLORS = {
    "amber", "blue", "cyan", "emerald", "fuchsia", "gray",
    "green", "indigo", "lime", "neutral", "orange", "pink",
    "purple", "red", "rose", "sky", "slate", "stone",
    "teal", "violet", "yellow", "zinc",
}
```

> [`scripts/check_brand_colors.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_brand_colors.py)

Prevents agents from using arbitrary colors like `bg-blue-500` when they should use `bg-brand-blue`.

### Unused Routes ([`check_unused_routes.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_unused_routes.py))

Scans backend route definitions and frontend TypeScript for API calls. Flags backend JSON API routes that have no frontend callers.

The TypeScript scanner uses regex patterns to find all frontend API references:

```python
patterns = [
    r"fetch\s*\(\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
    r"fetch\s*\(\s*`([^`]*\/[^`]*)`",
    r"href\s*=\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
    r"action\s*=\s*['\"`]([^'\"`]*\/[^'\"`]*)['\"`]",
    ...
]
```

> [`scripts/check_unused_routes.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_unused_routes.py)

Routes used by external callers can be whitelisted in `find_unused_routes()`.

### Unused Code ([`check_unused_code.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_unused_code.py))

Detects unused functions and methods in Python files. Uses AST walking to find function definitions, then searches for call sites across the codebase. Escape hatch:

```python
# check_unused_code: ignore
```

Add this comment on the function definition to suppress the warning.

### Dynamic Imports ([`check_dynamic_imports.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_dynamic_imports.py))

Flags Python imports that aren't at the top of the file. Dynamic imports make dependency graphs unpredictable and slow down test startup. `TYPE_CHECKING` blocks are allowed.

### Soft Deletes ([`check_soft_deletes.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_soft_deletes.py))

Ensures repository code uses soft deletes (setting `deleted_at`) instead of hard deletes on tables that support soft deletion.

### Code Quality ([`check_code_quality.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_code_quality.py))

Catches common code quality issues: fixed waits in e2e tests, conditional logic issues, and direct repository client access outside of repository classes.

### Obsolete Terms ([`check_obsolete_terms.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_obsolete_terms.py))

Scans filenames and file content for terms that have been renamed or deprecated. Prevents stale references from accumulating after renames.

### Dashboard Metrics ([`check_dashboard_metrics.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/check_dashboard_metrics.py))

Verifies that the Grafana dashboard JSON includes panels for all metrics defined in `app/core/metrics.py`. Prevents metrics from being added to code without corresponding dashboard visibility.

## Type Checking

Two type checkers run as pre-commit hooks:

| Checker                         | Language   | Hook         |
| ------------------------------- | ---------- | ------------ |
| **TypeScript (`tsc --noEmit`)** | TypeScript | `type-check` |
| **Pyrefly**                     | Python     | `pyrefly`    |

### Initial Data Type Sync

The `check-initial-data` hook runs `scripts/generate_types.py --check` to verify that TypeScript type definitions for initial data match the current Pydantic models. If they've drifted, the hook fails.

## Dead Code Detection

Two complementary tools detect dead code:

| Tool        | Language   | What It Finds                                 |
| ----------- | ---------- | --------------------------------------------- |
| **vulture** | Python     | Unused variables, functions, imports, classes |
| **knip**    | TypeScript | Unused exports, imports, dependencies, files  |

Both are configured to minimize false positives --- vulture uses a whitelist file (`.vulture_whitelist.py`) and an 80% confidence threshold.

## Import Architecture

The `import-linter` hook (`uv run lint-imports`) enforces architectural boundaries via contracts in [`pyproject.toml`](https://github.com/cadamsdotcom/CodeLeash/blob/main/pyproject.toml):

```toml
[[tool.importlinter.contracts]]
name = "Routes should not directly import Supabase"
type = "forbidden"
source_modules = ["app.routes"]
forbidden_modules = ["app.core.supabase", "supabase"]

[[tool.importlinter.contracts]]
name = "Routes should not directly import Repositories"
type = "forbidden"
source_modules = ["app.routes"]
forbidden_modules = ["app.repositories"]

[[tool.importlinter.contracts]]
name = "Services should not directly import Repositories"
type = "forbidden"
source_modules = ["app.services"]
forbidden_modules = ["app.repositories"]
```

> [`pyproject.toml`](https://github.com/cadamsdotcom/CodeLeash/blob/main/pyproject.toml)

This ensures:

- Routes cannot import repositories or the Supabase client directly
- Services cannot import repositories directly
- The container ([`app/core/container.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/container.py)) is the only place that wires dependencies
