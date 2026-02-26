---
title: 'Self-Reflection System'
sidebar_position: 6
---

Coding agent sessions start from zero. Context windows compact and learnings vanish. The agent makes the same mistakes; encounters the same surprises; forgets workarounds - over and over.

CodeLeash helps improve this over time with a self-reflection system built from Claude Code hooks. It captures agent learnings before they're lost, carries them forward into future sessions, and provides a command to integrate the best insights permanently into the codebase.

The idea is NOT to keep learnings as a reference, but to include what is learned into the code and guardrails.

## How It Works

The system has four phases:

```
Capture  -->  Carry Forward  -->  Integrate  -->  Clean Up
 (hooks)      (context injection)  (/learnings)    (delete files)
```

### 1. Capture

When a session ends or context is about to be compacted, hooks prompt the agent to write a learnings file to `.claude/learnings/`. Each file is named `{date}-{slug}.md` (e.g., `2025-05-14T10-30-tdd-guard-state-edge-case.md`) and includes:

- **Surprises** about the codebase
- **Key learnings** for future sessions
- **Hook/workflow recommendations** for improving the development process
- **Skill recommendations** for better tool usage
- **TDD log review** - inappropriate overrides, skip-red misuse, or BLOCKED edits

Two hooks trigger this:

- **Stop hook**: Fires when a session ends. Blocks the agent from stopping until it has reflected.
- **PreCompact hook**: Fires before context compaction. Ensures learnings are captured before the context window is compressed and older content is lost.

Both hooks pass the TDD log file path so the agent can review its own TDD discipline.

### 2. Carry Forward

Learnings files in `.claude/learnings/` are automatically available to future sessions. When a new session starts, the agent can read these files and avoid repeating past mistakes. The files act as a persistent memory across the agent's otherwise stateless sessions.

But this is a _temporary state of affairs_; the goal of generating learnings is to integrate them, and never commit learnings files to your repo.

### 3. Integrate

The user runs the `/learnings` command, which enters plan mode and:

1. Examines all files in `.claude/learnings/`
2. Identifies which learnings warrant permanent changes - better naming, documentation updates, new checks, script improvements, simplified architecture
3. Plans those changes for user approval
4. Implements the approved changes
5. Deletes the learnings files

Anything the agent would simply relearn on the job is discarded rather than turned into permanent changes. The goal is to improve the codebase itself, not maintain a growing pile of notes.

### 4. Clean Up

Once a learning's value has been absorbed into the codebase (as documentation, a check script, a hook, or a code improvement), the learnings file is deleted. The `.claude/learnings/` directory is meant to be temporary - a staging area, not an archive.

## Subagent Awareness

Subagents (launched via the Task tool) also participate in the reflection system:

- **SubagentStart hook**: Injects `additionalContext` into subagents so they know how to write learnings files. This means even short-lived subagents can capture surprises.
- **SubagentStop hook**: Marks agent logs as finished, maintaining a clean audit trail.

## Hook Configuration

The relevant hooks from [`.claude/settings.json`](https://github.com/cadamsdotcom/CodeLeash/blob/main/.claude/settings.json):

**PreCompact** - prompts the agent to reflect before context compaction:

```
COMPACTION INCOMING - Reflect on this session.
Create .claude/learnings/{date}-{slug}.md (kebab-case topic slug).
Include: 1) Surprises about the codebase
         2) Key learnings for future sessions
         3) Hook/workflow recommendations
         4) Skill recommendations.
Also review your TDD log for inappropriate overrides or
skip-red usage, or BLOCKED edits. Keep it concise.
```

**Stop** - blocks session end until the agent reflects:

```
SESSION ENDING - If you learned anything noteworthy,
create .claude/learnings/{date}-{slug}.md (kebab-case topic).
Include surprises, key learnings, hook/workflow recommendations,
skill recommendations. Also review your TDD log for
inappropriate overrides or skip-red usage, or BLOCKED edits.
Skip if nothing noteworthy.
```

Both hooks dynamically compute the TDD log file path from the session's transcript path, so the agent reviews the correct log.

## The `/learnings` Command

The `/learnings` [slash command](https://docs.anthropic.com/en/docs/claude-code/slash-commands) is defined in `.claude/commands/learnings.md`. When invoked, it:

1. Enters plan mode (so the user approves changes before they're made)
2. Reads all files in `.claude/learnings/`
3. Filters out non-actionable learnings (things the agent would relearn naturally)
4. Plans permanent improvements: documentation, naming, scripts, checks, tooling, architecture simplifications
5. After user approval, implements the changes and deletes the learnings files

This completes the loop: hooks capture knowledge, files carry it forward, and the command integrates the best insights back into the codebase permanently.

## What Makes Good Learnings

**Capture:**

- Codebase surprises that caused wasted time (unexpected patterns, hidden dependencies)
- Workflow friction that a hook, script, or check could eliminate
- TDD discipline issues worth flagging (skip-red for behavioral changes, ignored BLOCKED edits)
- Tool or skill usage that was more or less effective than expected

**Skip:**

- Things the agent would rediscover quickly on its own (obvious file locations, standard patterns)
- Session-specific context that won't generalize (specific variable names, one-off debugging steps)
- Learnings already covered by existing documentation or checks
