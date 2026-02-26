---
title: 'How Tests Work'
sidebar_position: 4
---

CodeLeash has three test levels --- unit, integration, and end-to-end --- plus frontend component tests via Vitest. The full suite runs automatically on every git commit via a pre-commit hook installed by [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh).

## Test Levels

| Level       | Directory            | Framework                | Timeout | What It Tests                     |
| ----------- | -------------------- | ------------------------ | ------- | --------------------------------- |
| Unit        | `tests/unit/`        | pytest                   | 10ms    | Pure business logic               |
| Integration | `tests/integration/` | pytest                   | None    | Service + repository interactions |
| Component   | `src/**/*.test.tsx`  | Vitest + Testing Library | None    | React component rendering         |
| E2E         | `tests/e2e/`         | pytest + Playwright      | None    | Full application flows            |

## Running Tests

```bash
# All tests (pre-commit + vitest + pytest + e2e, in parallel)
npm run test:all

# Individual suites
npm run test:python         # Unit + integration (excludes e2e)
npm test                    # Vitest (React components)
npm run test:e2e            # E2E with parallel workers
npm run test:e2e:serial     # E2E in sequential mode

# Specific files
npm run test:python -- tests/unit/services/test_greeting_service.py -k "test_name" -v
npm test -- src/components/GreetingList.test.tsx
npm run test:e2e -- tests/e2e/test_hello_world.py -k "test_name" -v
```

Tests must be run through `npm run` wrappers --- direct `uv run pytest` and `npx vitest` are blocked by deny rules in [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json).

`npm run test:all` runs all four suites in parallel:

```json
"test:all": "concurrently --kill-others-on-fail 'npm run pre-commit' 'npm test' 'npm run test:python' 'npm run test:e2e'"
```

> [`package.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/package.json)

## The 10ms Unit Test Timeout

Unit tests in `tests/unit/` enforce a strict 10ms timeout on test logic execution. This forces tests to be true unit tests focused on business logic, with all I/O mocked.

### How It Works

The timeout is implemented as a pytest hook in [`tests/conftest.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/tests/conftest.py). The core timing check profiles each test and raises on timeout:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    if "tests/unit/" not in item.fspath.strpath:
        yield; return

    profiler = cProfile.Profile()
    profiler.enable()
    start_time = time.perf_counter_ns()
    try:
        yield
    finally:
        end_time = time.perf_counter_ns()
        duration_ms = (end_time - start_time) / 1_000_000
        profiler.disable()

    if duration_ms > 10.0:
        # Auto-retry once, then generate flamegraph and raise
        ...
```

> [`tests/conftest.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/tests/conftest.py)

### Automatic Retry

Tests that exceed 10ms get one automatic retry. This handles transient performance issues like first-time module imports or JIT compilation. Only after the retry also exceeds 10ms does the test fail.

### Flamegraph on Failure

When a test times out after retry, the profiler data is saved as an SVG flamegraph via `flameprof`:

```
test_profiles/tests_unit_services_test_greeting_service_TestGetAll_test_returns_greetings_12.3ms.svg
```

Opening this SVG in a browser reveals exactly where the time was spent --- typically in `@patch` decorator import chains or accidental I/O.

### Common Causes

1. **`@patch` decorators trigger imports**: `@patch("app.module.dependency")` loads the entire module chain. Use dependency injection instead.
2. **Heavy module imports**: Importing routes or services triggers FastAPI/Pydantic initialization. Keep test imports lightweight.
3. **Database or external calls**: Any real I/O will exceed 10ms. Mock everything.

### Fixture Prewarming

The [`conftest.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/tests/conftest.py) imports commonly-used models at module load time (not inside test functions), so the import cost is paid once and excluded from individual test timing:

```python
from app.models.greeting import Greeting
from app.models.user import User
```

## E2E Test Harness

The e2e test runner ([`scripts/run_e2e_tests.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/run_e2e_tests.py)) is fully automated. It:

1. **Finds available ports** for both the application server and an isolated Supabase instance
2. **Starts Supabase and builds the frontend** in parallel using `ThreadPoolExecutor`
3. **Starts the server** (uvicorn)
4. **Runs pytest** with parallel workers (`-n auto` by default)
5. **Analyzes server logs** for unexpected HTTP errors or Python exceptions
6. **Cleans up** everything (server processes, Supabase instance, temp directories)

### Isolated Supabase

Each e2e test run gets its own Supabase instance with unique ports and project ID:

```python
unique_project_id = f"e2e-{timestamp}-{random_id}"
config_replacements = [
    (r"^project_id = .*$", f'project_id = "{unique_project_id}"'),
    (r"^port = 54321$", f'port = {port_mapping["api"]}'),
    (r"^port = 54322$", f'port = {port_mapping["db"]}'),
    (r"^shadow_port = 54320$", f'shadow_port = {port_mapping["db_shadow"]}'),
    ...
]
```

> [`scripts/run_e2e_tests.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/run_e2e_tests.py)

- Port ranges are allocated from 55000 in blocks of 10 (supporting up to 10 concurrent runs)
- A temporary directory is created with a copy of `supabase/` and patched `config.toml`
- Each instance gets a unique `project_id` to ensure fresh Docker volumes
- Unnecessary services (studio, edge-runtime, logflare, vector, imgproxy, realtime) are excluded to speed up startup

### Server Log Analysis

After tests complete, the harness analyzes server logs for unexpected errors:

```python
http_error_pattern = re.compile(r'"\w+\s+[^"]+"\s+(4\d{2}|5\d{2})')
error_log_pattern = re.compile(r"\bERROR\b|\bException\b|\bTraceback\b")

for prefix, line in log_lines:
    if http_error_pattern.search(line):
        # Check against expected-errors list
        ...
```

> [`scripts/run_e2e_tests.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/run_e2e_tests.py)

If unexpected errors are found, the test suite fails even if all pytest assertions passed. This catches server-side issues that client tests might miss.

### Output Suppression

Setup output (Supabase startup, frontend build, server startup) is captured in a `QuietSetup` buffer. If setup succeeds, none of it is shown. If setup fails, the full captured output is printed for debugging.

### Cleaning Up Orphaned E2E Resources

Each E2E run creates an isolated Supabase instance with its own Docker containers, volumes, and networks. If a run is interrupted (Ctrl-C, crash, timeout), these resources can be left behind. Over time, stale volumes and containers from past runs can accumulate and cause E2E tests to start failing unexpectedly - typically with port conflicts, Supabase startup errors, or database state issues. If E2E tests begin failing and the cause isn't obvious, orphaned resources from previous runs are a likely culprit.

Run the cleanup script to remove them:

```bash
bash scripts/cleanup_orphaned_e2e.sh
```

The script targets only E2E test resources and is safe to run at any time. It cleans up:

- **E2E containers** - Docker containers with `_e2e-` in their name
- **Random-named Supabase containers** - Exited containers from `public.ecr.aws/supabase/` images that aren't part of a named project
- **E2E volumes** - Docker volumes with `_e2e-` in their name
- **Dangling Supabase volumes** - Volumes prefixed with `supabase_` not referenced by any container
- **E2E networks** - Docker networks with `_e2e-` in their name
- **Temporary directories** - Contents of `/tmp/supabase-e2e/`

## Dot Silencing

The `pytest_report_teststatus` hook in [`conftest.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/tests/conftest.py) suppresses the default progress dots for passing tests:

```python
def pytest_report_teststatus(report, config):
    if report.passed and report.when == "call":
        return report.outcome, "", report.outcome.upper()
```

This keeps test output minimal --- agents only need exit codes, not visual progress indicators.

## Test Command Reference

| Command                   | What It Runs                       | Parallel           |
| ------------------------- | ---------------------------------- | ------------------ |
| `npm run test:all`        | pre-commit + vitest + pytest + e2e | Yes (concurrently) |
| `npm run test:python`     | pytest (unit + integration)        | No                 |
| `npm test`                | Vitest (component tests)           | No                 |
| `npm run test:e2e`        | E2E with auto workers              | Yes (pytest-xdist) |
| `npm run test:e2e:serial` | E2E sequentially                   | No                 |
| `npm run pre-commit`      | Linting, formatting, type checks   | No                 |
