---
title: 'Introduction'
sidebar_position: 1
slug: /
---

## What Is CodeLeash?

CodeLeash is an opinionated full-stack development scaffold that demonstrates how to build web applications with AI coding agents using strong guardrails, Test-Driven Development, and architectural enforcement. The tagline says it all: _your coding agent, on a leash_.

AI coding agents are powerful but undisciplined. Left unchecked, they skip tests, write sprawling changes, introduce subtle regressions, and produce code that works but nobody can maintain. CodeLeash addresses this with a system of hooks, state machines, and lint rules that constrain the agent's behavior without limiting its productivity.

The scaffold includes a minimal "hello world" implementation that exercises every architectural pattern --- repository, service, container DI, React root mounting with initial data --- so you can see how the pieces fit together before building on top of them.

## Who Are These Docs For?

- **Developers adopting CodeLeash** as a starting point for their own projects
- **Teams experimenting with AI-assisted development** who want guardrails
- **Anyone curious about the systems** --- TDD enforcement, test infrastructure, code quality checks --- and how they work under the hood

## Technology Stack

| Layer         | Technology                                   |
| ------------- | -------------------------------------------- |
| Backend       | Python, FastAPI, Uvicorn                     |
| Frontend      | React 19, TypeScript, Vite, Tailwind CSS     |
| Database      | Supabase (PostgreSQL) with RLS               |
| Auth          | Supabase Auth with JWT tokens                |
| Observability | Prometheus metrics, OpenTelemetry, Sentry    |
| Testing       | pytest, Vitest, Playwright                   |
| CI/Quality    | pre-commit hooks, custom Python lint scripts |

## Chapter Overview

1. **Full-Stack Monorepo** --- How Vite and FastAPI work together, the `render_page()` pattern, and the initial data bridge from server to React.
2. **TDD Guard** --- The state machine that enforces Red-Green-Refactor, the hooks that drive it, and how it isolates per-agent state.
3. **How Tests Work** --- Three test levels (unit, integration, e2e), the 10ms timeout, and the e2e harness with isolated Supabase instances.
4. **Agent Optimizations** --- Deny rules, test pipe blocking, dot silencing, and other settings that shape agent behavior.
5. **Code Quality Checks** --- Custom Python scripts that run as pre-commit hooks: brand colors, unused routes, soft deletes, and more.
6. **Worktree Parallel Work** --- Port hashing, Supabase config isolation, and running multiple branches simultaneously.
7. **Future & Community** --- Migration testing framework, planned enhancements, and how to adopt these ideas.

## Key Files

| Area           | Files                                                                                                                                                                                                                                                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend entry  | [`main.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/main.py)                                                                                                                                                                                                                                             |
| App core       | [`app/core/container.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/container.py), [`app/core/templates.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/templates.py), [`app/core/vite_loader.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/app/core/vite_loader.py) |
| Frontend roots | [`src/roots/util.tsx`](https://github.com/cadamsdotcom/CodeLeash/blob/main/src/roots/util.tsx), [`src/roots/index.tsx`](https://github.com/cadamsdotcom/CodeLeash/blob/main/src/roots/index.tsx)                                                                                                                     |
| TDD guard      | [`scripts/tdd_common.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_common.py), [`scripts/tdd_pre_edit.py`](https://github.com/cadamsdotcom/CodeLeash/blob/main/scripts/tdd_pre_edit.py)                                                                                                       |
| Agent config   | [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json), [`CLAUDE.md`](https://github.com/cadamsdotcom/CodeLeash/blob/main/CLAUDE.md)                                                                                                                                   |
| Setup          | [`init.sh`](https://github.com/cadamsdotcom/CodeLeash/blob/main/init.sh), [`package.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/package.json)                                                                                                                                                         |

## Quick Start

```bash
git clone https://github.com/cadamsdotcom/CodeLeash.git
cd CodeLeash
./init.sh        # Install deps, start Supabase, configure .env
npm run dev      # Vite + FastAPI with hot reload
```

The application runs at `http://localhost:8000`.
