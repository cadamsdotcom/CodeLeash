# Future & Community

## Migration Testing Framework

A comprehensive migration testing framework is planned in [`tests/migration/FUTURE.md`](https://github.com/cadamsdotcom/CodeLeash/blob/main/tests/migration/FUTURE.md). The design includes:

- **MigrationRunner**: Programmatic execution of individual migrations forward and backward
- **DataGenerator**: Realistic production-like test data
- **DatabaseState**: Capture and compare full database state (schema, constraints, indexes, RLS policies, data checksums)
- **BaseMigrationTest**: A base class that tests forward migration, rollback, edge cases, and foreign key integrity

The key insight is that migration tests should run against an isolated Supabase instance (like e2e tests), resetting to just before the target migration, inserting test data, applying the migration, and verifying data transformations and schema changes.

## Philosophy

CodeLeash is built on a few core beliefs:

**AI agents need constraints, not freedom.** An unconstrained agent will skip tests, make sweeping changes, and produce code that works in isolation but breaks in context. The TDD guard, file edit restrictions, and test pipe blocking exist because freedom doesn't scale.

**Tests are the specification.** The 10ms timeout forces unit tests to be pure business logic. The e2e harness ensures full integration. The pre-commit hook runs everything on every commit. If it isn't tested, it doesn't exist.

**Lint rules should be code.** Instead of configuring complex tool options, CodeLeash writes Python scripts that walk ASTs and scan with regex. A script is easier to write, easier to debug, and easier to explain than a YAML configuration.

**The monorepo is the product.** Backend, frontend, database migrations, lint rules, test infrastructure, and CI/CD all live together. Changes that cross boundaries are normal, not exceptional.

## How to Adopt These Ideas

You don't have to use CodeLeash as a whole. Individual systems are designed to be understood and adapted:

- **TDD Guard**: The state machine in [`scripts/tdd_common.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_common.py) is about 80 lines. The pre-edit hook is about 250. You could adapt this for any Claude Code project by adjusting the file classification patterns.

- **10ms Timeout**: The `pytest_runtest_call` hook in [`tests/conftest.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/tests/conftest.py) is self-contained. Drop it into any pytest project and adjust the threshold.

- **Custom Lint Scripts**: Each [`scripts/check_*.py`](https://github.com/cadamsdotcom/CodeLeash/tree/main/scripts) is independent. Copy the pattern --- parse files, check a rule, exit nonzero on violations --- and add it to your [`.pre-commit-config.yaml`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.pre-commit-config.yaml).

- **Worker System**: The [jobs table migration](https://github.com/cadamsdotcom/CodeLeash/blob/main/supabase/migrations/20260223000002_create_jobs_table.sql), [`JobRepository`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/repositories/job.py), and [`QueueWorker`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/workers/queue_worker.py) are a complete job queue in about 400 lines total. No external broker required.

- **Worktree Port Hashing**: The port calculation logic in [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh) is about 20 lines. Apply it to any project that needs parallel development environments.

## Call to Action

Your coding agent, on a leash.

Not because agents are bad, but because good constraints produce good code. A TDD guard that forces Red-Green-Refactor is more reliable than a prompt that asks nicely. A 10ms timeout that rejects slow tests is more effective than a style guide that recommends mocking. A pre-commit hook that runs everything is more trustworthy than a CI pipeline that runs later.

The guardrails aren't overhead --- they're the product.
