# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeLeash is an opinionated full-stack development scaffold that demonstrates how to build web applications with Claude Code using strong guardrails, Test-Driven Development, and architectural enforcement. It includes a minimal "hello world" implementation that exercises all architectural patterns (repository, service, container DI, React root mounting with initial data).

## Technology Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with TypeScript, Vite build system, Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth with JWT tokens
- **Observability**: Prometheus metrics, OpenTelemetry tracing, Sentry error tracking

## Key Commands

### Running the Application

To run the application:

#### Development Mode

```bash
# Run both backend and frontend with hot reload
npm run dev
```

#### Preview Mode (Production Build)

```bash
# Build frontend and run the full application
npm run preview
```

#### Docker Mode (Production-like)

```bash
# Run in containers
docker compose up --build

# View logs
docker compose logs -f web
```

The application runs on http://localhost:8000 in all local modes.

**IMPORTANT FOR CLAUDE**: Always check if the server is running on port 8000 before testing.

### Important Restrictions

**IMPORTANT FOR CLAUDE**:

- NEVER deploy the application to production. Deployment is the user's responsibility.
- NEVER run Docker commands on production systems. Only provide guidance and troubleshooting advice.

### Key Development Commands

```bash
# Install dependencies
uv sync --all-extras        # All dependencies
uv add package-name         # Add new package

# Generate TypeScript types from Pydantic models
npm run types

# Database operations
supabase migration up       # Apply migrations
supabase db reset          # Reset database
```

### Initial Setup

```bash
# Install dependencies, configure environment, install git pre-commit hook
./init.sh
```

**IMPORTANT FOR CLAUDE**: When starting work in a fresh repo or worktree, run `./init.sh` first. It installs dependencies, configures the environment for the worktree, starts Supabase, and installs a git pre-commit hook that runs `npm run test:all` on every commit.

### Code Quality Checks

```bash
# Run all pre-commit hooks
npm run pre-commit
```

```bash
# Run pre-commit and all tests
npm run test:all
```

A git pre-commit hook (installed by `./init.sh`) runs `npm run test:all` automatically on every commit, which includes pre-commit checks, vitest, pytest, and e2e tests in parallel. `npm run pre-commit` remains available for running just the linting/formatting checks.

After making any code changes, prefer running pre-commit hooks to verify code quality, formatting, and type checking, over other tools. This ensures all changes meet the project's coding standards and prevents issues in the CI/CD pipeline.

### Running Tests

```bash
# Run all tests
npm run test:all           # Python + TypeScript + E2E
npm run test:python        # Python backend tests
npm test                   # TypeScript frontend tests
npm run test:e2e          # End-to-end tests in parallel (fully automated)
npm run test:e2e:serial   # End-to-end tests in serial mode (slower)

# Run specific test files
npm run test:python -- tests/unit/services/test_greeting_service.py
npm run test:python -- tests/unit/services/test_foo.py -k "test_name" -v
npm test -- src/components/GreetingList.test.tsx
npm run test:e2e -- tests/e2e/test_hello_world.py -k "test_name" -v
```

**IMPORTANT FOR CLAUDE**: Always run tests as above. Running tests via `uv run pytest` or `npx vitest` will fail with permissions errors.

**CRITICAL TEST OUTPUT REQUIREMENT FOR CLAUDE**:

**A PreToolUse hook BLOCKS any test command that contains `|`, `;`, or `>`.** Running `npm test ... | grep`, `npm run test:python ... | tail`, `npm run test:e2e > /tmp/output.txt`, or any piped/chained/redirected variant will be rejected by the hook and the command will not execute. Do not attempt workarounds -- just run the test command by itself with no pipes or redirection.

Test output in this project is already minimal and informative. Run test commands directly:

```bash
# Correct - runs directly, full output
npm run test:python -- tests/unit/services/test_foo.py -k "test_name" -v

# BLOCKED by hook - do not attempt
npm run test:python -- tests/unit/services/test_foo.py | tail -20
npm test -- src/components/Foo.test.tsx | grep FAIL
npm run test:e2e 2>&1 | head -50
npm run test:e2e > /tmp/test_output.txt 2>&1
```

**IMPORTANT FOR CLAUDE**:

- E2E tests are fully automated - never ask users to start the server manually
- E2E tests automatically build the frontend before running (in scripts/run_e2e_tests.py) - no need to run `npm run build` before e2e tests
- Unit tests enforce a 10ms timeout - expensive imports are prewarmed in conftest.py
- E2E test suites take up to 3 minutes to complete even when run in parallel

## Architecture Overview

### Core Models (in app/models/)

- **User**: User identity with email, full_name, timestamps
- **Greeting**: Sample model demonstrating the Pydantic model pattern with soft-delete support

### Main Application Routes

- `/` - Hello world page (React, server-rendered initial data)
- `/health` - Health check endpoint

### Current Structure

- React components in `src/` directory
- Built assets served from `dist/` directory
- Static files in `static/` directory
- Tests using pytest (in `tests/` directory)

### Architectural Patterns

The scaffold demonstrates these patterns that should be followed for all new features:

1. **Repository Pattern**: `BaseRepository` provides CRUD with soft-delete support. New repositories extend it.
2. **Service Pattern**: Services accept repositories via constructor injection. Business logic lives here.
3. **Container DI**: `app/core/container.py` wires repositories and services. FastAPI `Depends()` provides them to routes.
4. **Server-Side Rendering with React**: Routes use `render_page()` to pass initial data to React components via `data-initial` attribute.
5. **Import-Linter Enforcement**: Routes cannot import repositories or Supabase directly. Services cannot import repositories directly. The container is the only place that wires dependencies.
6. **Unused Routes Checker**: `scripts/check_unused_routes.py` scans frontend TypeScript for API calls and flags backend routes with no frontend callers. JSON API endpoints that aren't called from the React frontend generally signal unused code. If the endpoint is not unused (eg. used by callers external to the product) add a whitelist entry in `find_unused_routes()`.

## Development Guidelines

### Test-Driven Development (TDD)

**CRITICAL FOR CLAUDE**:

1. **Always watch tests fail FIRST** - Run the test and verify it fails for the RIGHT reason (missing feature), NOT wrong reasons (syntax, imports, setup)
2. **Never proceed with broken tests** - If tests fail for technical reasons, fix those issues before implementing
3. **When debugging test failures: roll back recent changes** to isolate the root cause
4. **Use failing tests to debug issues** instead of creating temporary scripts or debug files
5. **When reproducing bugs: Write tests that EXPECT the CORRECT behavior** - The test should fail because the bug prevents the correct behavior, then fix the code to make the test pass

**For Bug Reproduction Tests:**

- Write tests that demonstrate the bug by expecting the CORRECT behavior
- The test will initially FAIL because the bug prevents the correct behavior
- Then fix the underlying issue to make the test PASS
- Do NOT write tests that expect the buggy behavior to continue

Example: If deletion fails with "immutable history" error, write a test that expects deletion to succeed, watch it fail with the error, then fix the code.

Remember: A test that fails for the wrong reason teaches you nothing about the code.

**TDD Planning Checklist (review before finalizing any plan):**

1. Write e2e tests FIRST before implementation
2. Plan TDD at unit/integration/component level for all changes
3. Can existing e2e tests be enhanced to cover this work instead of writing new ones?
4. Can planned e2e tests be unit/integration/component tests instead?

**Red Intent Honesty:**

- **Red intent must describe expected failure.** If you're adding tests that will pass immediately, use `--skip-red` on the Green intent instead. Don't log a Red intent for tests you expect to pass.
- Do NOT use `--skip-red` to avoid TDD, even if you already have e2e coverage.
- The TDD guard enforces that `tdd_log green` requires a preceding Red cycle (Red intent -> failing test -> Green intent). The `--skip-red` flag is the escape hatch for changes that genuinely don't need a failing test first.

**Using --skip-red (requires --reason):**

The `--skip-red` flag requires a `--reason` to constrain its use. Only these three reasons are valid:

| Reason            | When to Use                                                         | Examples                                         |
| ----------------- | ------------------------------------------------------------------- | ------------------------------------------------ |
| `refactoring`     | Renaming, moving code, restructuring WITHOUT changing behavior      | Rename variable, extract function, move file     |
| `lint-only`       | Formatting, lint fixes, type annotations that don't affect behavior | Fix indentation, add type hints, reorder imports |
| `adding-coverage` | Adding test coverage for code that ALREADY works correctly          | Writing tests for untested existing functions    |

```bash
# Refactoring example
uv run python -m scripts.tdd_log --log tdd-abc.log green --skip-red --reason=refactoring --change "Rename foo to bar" --file "src/module.py"

# Lint-only example
uv run python -m scripts.tdd_log --log tdd-abc.log green --skip-red --reason=lint-only --change "Fix formatting" --file "src/Foo.tsx"

# Adding coverage example
uv run python -m scripts.tdd_log --log tdd-abc.log green --skip-red --reason=adding-coverage --change "Add tests for existing helper" --file "tests/test_helper.py"
```

**IMPORTANT**: If your change introduces NEW behavior or fixes a bug, you MUST use the full Red-Green cycle. The `--skip-red` flag is NOT a shortcut for avoiding tests -- it's for changes where tests would pass immediately because behavior is unchanged.

**Key Principle for skip-red:**

The `--reason=refactoring` flag means "tests continue to pass without modification." If existing tests would FAIL after your change, you need the full Red-Green cycle -- not `--skip-red`. This applies even when the change feels minor (updating constants, changing timeouts, adjusting limits). If a test documents the current behavior and your change alters that behavior, update the test first, watch it fail, then implement the change.

**Discovering the TDD Log File Name:**

The TDD log file name and full usage examples are provided automatically at session start via the `SessionStart` hook. Look for the message at the top of your session that says `Your TDD log file is: tdd-<id>.log` followed by copy-pasteable Red, Green, and skip-red commands with the correct `--log` value already filled in. Use those examples as templates for all `tdd_log` commands.

**Overriding TDD State:**

You can force the TDD state into any other state by logging a Red or Green intent by running tdd_log with your desired arguments as normal. Your override will be logged for later review. Useful if you get stuck in the wrong TDD state (e.g., you logged the wrong expectation or made a mistake).

### Unit Test Performance & Timeouts

**CRITICAL**: This project enforces a **10ms timeout** on all unit tests to ensure they remain true unit tests focused on business logic only.

**Automatic Retry**: Tests that exceed 10ms get one automatic retry to handle transient performance issues (like JIT compilation, import caching). Only after the retry fails will a `TestTimeoutError` be raised with a flamegraph for debugging.

**Common Timeout Causes & Solutions:**

1. **@patch Decorators Trigger Imports**

   - **Problem**: `@patch("app.module.dependency")` loads the entire module chain
   - **Solution**: Use dependency injection instead of patching
   - **Example**: Pass mocked dependencies directly to functions rather than patching imports

2. **Heavy Module Imports**

   - **Problem**: Importing routes, services, or config triggers FastAPI/Pydantic dependencies
   - **Solution**: Mock at the boundary, keep imports lightweight in test files

3. **Database/External Dependencies**
   - **Problem**: Any real I/O operations will exceed 10ms
   - **Solution**: Mock all external dependencies (database, APIs, file system)

**Quick Debugging:**

- If a test times out, check the generated flamegraph SVG file
- Look for `@patch` decorators that trigger expensive imports
- Run the test in isolation - if it passes alone, it's an import chain issue
- Consider if the test belongs in `tests/integration/` instead

**Architecture Guidance:**

- Prefer dependency injection over `@patch` for testability
- Design code to accept dependencies as parameters
- Use the Container pattern for production dependency wiring
- For fast unit tests of routes, use `FastAPI()` + `include_router()` + `dependency_overrides` to avoid full app startup with middleware, Supabase, etc. (see `tests/unit/routes/test_greetings_api.py` for the pattern)

### Database Considerations

- Uses Supabase (PostgreSQL) for both development and production
- Database migrations in `supabase/migrations/`
- Row-level security (RLS) enabled for data protection
- Direct Supabase client usage (not SQLAlchemy)

### Security Notes

- JWT authentication via Supabase Auth
- Environment-based configuration for secrets
- Input validation via Pydantic models

### Frontend Development

- React with TypeScript for UI components
- Vite for fast development and optimized builds
- Tailwind CSS for styling
- Component-based architecture in `src/components/`
- Pages in `src/pages/` with corresponding root mounting files in `src/roots/`
