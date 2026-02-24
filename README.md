CodeLeash is an opinionated framework for full stack web development in a monorepo using Claude Code exclusively. It is a full-stack monorepo with its backend in python using FastAPI, database in Supabase, and frontend in React, built with Vite. Your production environment only requires uvicorn and does not require a frontend server, as all React assets are built and served statically. Commits can atomically change the frontend and backend as well as all types used to exchange data between them.

The stack:

- Claude Code
- Supabase
- FastAPI & python & pydantic & pytest
- React, TypeScript & Vite & vitest & Tailwind
- prek (a faster, Rust-based pre-commit alternative)
- pydantic2ts (for converting python types to TypeScript)
- Linters & code formatters: black, ruff, eslint, vulture...

As opposed to being "unleashed", this framework revolves around the concept of not trusting the agent to do the right thing, but forcing it to. Why spend tokens validating things that can be validated deterministically with a little bit of code. The framework includes tools and linters to validate rather than trust LLM audits. Codifying the checks helps make building with AI more predictable, cheaper and faster. It is also a never-ending process, continuously iterating to improve the framework. The more checks and guardrails are in place the more the LLM's work can be trusted and the more work can be done with more cursory code review. However - you should still be reviewing every line of code. This is not about vibecoding; it's about removing yourself from progressively more and more loops over time so you can gain leverage, but doing it at a low level instead of a high one, to create _more_ predictability in the process, so you can reason about it and skip over steps you'd normally take as a conscientious professional software developer.

CodeLeash is intended as a counterpoint to everyone who wants to give LLMs more specs and let them non-deterministically create software from specs every time. Software is actually a collection of tiny details, codified and deliberately curated to make sure things work in a specific way. Spec-driven development pretends the opposite is possible: let's let the model decide how things work in the details! Oh but we'll provide lots of detail about the few things we care about. That's not how you make serious software, just hoping it'll be the same every time and if the model invents something we don't want, re-rolling for that part. CodeLeash uses Test Driven Development (red-green-refactor) to preserve implementation details in the codebase alongside the code, in the form of tests _that the agent has witnessed failing and then written the code to cause them to pass_.

To be effective at TDD, the agent has to run tests frequently. Unit tests have a 10ms timeout, and other types of tests have other higher timeouts where practical. The 10ms timeout forces the agent to refactor any tests it writes so they do not do any I/O. This is highly desirable as the test suite ends up CPU-bound and test leakage becomes very difficult. The agent is prevented from ever committing a test failure by a git hook installed by `init.sh` that runs all tests before allowing to commit. Of course as has always been the case, you or the agent can bypass with `git commit --no-verify`, so set your agent permissions accordingly, watch your agent working, and consider avoiding YOLO mode entirely.

There is a collection of Claude Code hooks that force the model through the red-green-refactor cycle, as well as a hook that assesses its plans for how well TDD has been taken into account. The plan exit hook asks Claude to design a cleanup step that removes cruft that accumulates during the TDD process.

There are many custom linters and checkers in the repo that ensure quality. It includes checkers for unused code and routes, and many lint checks. There is a checker for conformance with the architecture layering you'd expect in a backend repo - routes, a service layer, a repository layer. There is a checker to enforce only usage of brand colors, instead of whatever random Tailwind colors the model chooses. A custom set of colors - a custom yellow, red, blue, plus your brand colors - help software not look AI-created. All of these checkers have proven their worth and they're included because I truly believe they're useful to give you leverage when building with Claude Code.

Every time Claude stops or hits compaction, there is a hook that asks it to write any surprises to a learnings file. These learnings are signal to you as the engineer in charge of your repo to fix poorly named functions that tripped up the agent, or improve the guardrails that help it succeed, or otherwise smooth its path. Ideally you shouldn't commit the learnings but should make any fixes you think they prompt. It has served as a great source of signal for improvements to the codebase and the hooks, checks etc. that make up CodeLeash.

I (Chris Adams) don't recommend using CodeLeash as-is. After all, everyone's needs are different and everyone's repo works differently and there's path-dependency at play. Plus, you are unlikely to like every idea I've baked in. But if you like one or more of the ideas you see here, you can always point your agent at this repo and ask to pull that idea into your codebase. One thing you could quite easily grab wholesale that's an isolated piece is the TDD guard system and plan exit hook. It's fairly self contained.

If you do use any of these ideas I'd love to hear from you!

---

## Tech Stack

- **Backend**: FastAPI (Python) with Pydantic models
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth with JWT tokens
- **Observability**: Prometheus metrics, OpenTelemetry tracing, Sentry error tracking

## Prerequisites

- Python 3.12+
- Node.js 18+
- Supabase CLI
- Git

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd CodeLeash

# Run the setup script (installs deps, configures env, starts Supabase, installs git hooks)
./init.sh
```

The setup script copies `.env.example` to `.env` if one doesn't already exist. Edit `.env` with your Supabase credentials after setup.

## Running the Application

```bash
# Development mode (backend + frontend with hot reload)
npm run dev

# The application runs at http://localhost:8000
```

## Testing

```bash
# Run all tests (Python + TypeScript + E2E)
npm run test:all

# Run specific test suites
npm run test:python     # Python backend tests
npm test                # TypeScript frontend tests
npm run test:e2e        # End-to-end tests (fully automated)

# Run specific tests
npm run test:python -- tests/unit/services/test_greeting_service.py -v
npm test -- src/components/GreetingList.test.tsx
```

## Code Quality

```bash
# Run all pre-commit checks
npm run pre-commit
```

A git pre-commit hook runs `npm run test:all` on every commit.

## Project Structure

```
app/
  core/         # Core utilities (auth, config, metrics, tracing, templates)
  models/       # Pydantic models
  repositories/ # Database access layer
  routes/       # API and web routes
  services/     # Business logic
  templates/    # Jinja2 templates
src/
  components/   # React components
  contexts/     # React contexts
  pages/        # Page components
  roots/        # Root mounting components
  constants/    # Theme and configuration
scripts/        # Development tools, TDD hooks, linters
tests/
  unit/         # Fast unit tests (10ms timeout)
  integration/  # Database integration tests
  e2e/          # End-to-end Playwright tests
supabase/
  migrations/   # Database migrations
```

## Architecture

The codebase enforces a layered architecture via import-linter:

- **Routes** cannot import from repositories or Supabase directly
- **Services** cannot import from repositories or Supabase directly
- **Container** handles all dependency injection
- Routes depend on services via FastAPI `Depends()`

## License

This project is licensed under the MIT License.
