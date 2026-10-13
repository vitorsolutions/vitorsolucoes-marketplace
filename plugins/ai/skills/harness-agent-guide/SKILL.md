---
name: harness-agent-guide
description: >-
  Creates or reconciles the instruction file that tells an AI coding agent how to work in a
  repository (AGENTS.md as the single source, with a thin import file for tools that read their
  own file name). Builds it from the real project instead of from assumptions: structure and
  dependency direction, a definition of done made of commands that were actually run, and
  restrictions such as no suppressing diagnostics. In reconcile mode it compares an existing guide
  against the repository and reports what drifted, without overwriting it. Currently supports .NET
  and Python. Use when the user asks to "create AGENTS.md", "write the CLAUDE.md for this
  project", "set up agent instructions", "check if my AGENTS.md is up to date", "criar o
  AGENTS.md", "gerar o CLAUDE.md", "revisar as instruções do agente", or wants the agent to know
  what "done" means in this repository. Do NOT use it to enforce the rules in the guide
  (harness-hooks), to set tool permissions (harness-permissions), or to change build and lint
  configuration (harness-sensors).
---

# Harness agent guide

## What this skill does

An agent that does not know a repository's rules finds them by trial and error. This skill writes the short document that states them: what the project is, how it is laid out, which commands prove a task is done, and what the agent must not do.

The guide is **derived from the repository where possible and asked from the user where not**. A guide full of generic advice or invented conventions does harm: long guides get ignored, and wrong statements get followed.

Vocabulary:

- **Guide**: the instruction file for agents.
- **Definition of done**: the commands that must all exit with success before a task counts as finished.
- **Drift**: a statement in the guide that no longer matches the repository.

## Hard rules

- Never overwrite an existing guide. Propose changes as a diff and wait for approval.
- Never state a convention you did not read from configuration or get from the user. Mark anything unverified as such, or leave it out.
- Never list a command in the definition of done unless it was run in this session and its exit status was recorded. A command that currently fails is reported as failing, not listed as passing, and the agent never changes code, tests or configuration to make it pass. Ask whether to list it with a note that the baseline is red, or to leave it out until it is fixed. A command that was not run (tool missing, or approval declined) is marked as not run, never listed as passing and never silently dropped.
- Never put credentials, internal hostnames, or personal data in the guide.
- Never commit, push, or stage files.
- Keep it short. For each line ask whether removing it would make the agent make a mistake. If not, leave it out. Do not describe things the agent can read from the code, such as file-by-file summaries or standard language conventions, and do not repeat rules a tool already enforces.
- Ask before running commands that may use the network, take a long time, or write outside the repository (for example a package restore or a full test run).

## Workflow

### 1. Detect the stack and existing guides

- Find the marker files in each stack reference under `references/stacks/` and read each pack that matches. A repository with two stacks (for example .NET and Python) gets one set of commands per stack, each under its own heading, and one shared set of restrictions. No matching pack: say the stack is not supported, describe the guide in concept, and change nothing.
- Look for existing instruction files: `AGENTS.md`, `CLAUDE.md`, and any tool-specific rule files (for example under editor or assistant folders). Report what exists. Do not edit files that belong to tools other than the one you are generating for.

Choose the mode:

- **Create**: no guide exists.
- **Reconcile**: a guide exists. Go to the reconcile section.

### 2. Gather facts from the repository

Using the stack reference:

1. **Structure**: list the projects or packages, and where the dependency direction can be read, record it. If the stack does not expose a dependency graph, say so and ask the user whether there is a rule to state.
2. **Verification commands**: find the candidate commands for build, test, and lint or format checks. Run each (after the user agrees where the rules above require it) and record the exit status. An environment runner such as `uv run` may sync or install, so ask first, or use a form that does not sync (the pack says which). A restore also happens implicitly inside a build or a test run, so ask before the first one in an environment where packages are not cached.
3. **Enforced controls**: note which controls are enforced, using the stack's effective-state readout. A restriction about suppressions is only meaningful if the controls it protects exist.
4. **Risky operations**: list the commands in the pack that act on remote systems or shared data.
5. **Protected files**: list the configuration files that define the project's checks.

### 3. Ask only what cannot be derived

Keep it to a few questions, each with a default that lets the user skip it:

- Naming or language conventions that differ from the defaults.
- Branch, commit, or review conventions the agent must follow.
- Anything the agent must never touch.
- Whether to include the standard restrictions below.

### 4. Draft the guide

Use the sections below in this order. Omit a section that would be empty.

```markdown
# AGENTS.md

## Project
<one to three lines: what it is, main technology and version>

## Structure and dependency rules
<only what is not obvious from the folder names; dependency direction if one exists>

## Definition of done
A task is done only when these commands all exit with status 0:
<commands that were run>

Not run (tool missing or not approved): <commands, with the reason>, only when there are any

## Conventions
<only rules that differ from the defaults, each from configuration or from the user>

## Restrictions
<the restrictions the user accepted>
```

Standard restrictions to offer (the user accepts, edits, or drops each one):

- Do not suppress diagnostics to make a check pass. List the suppression mechanisms from the pack. If a rule looks wrong, stop and explain why.
- Do not change the configuration files that define the checks to relax them without an explicit request. List them.
- Do not add credentials to tracked files.
- Do not run the risky operations from the pack against anything other than a local environment.

Add one sentence saying that restrictions written here guide the agent but are not enforced by the guide itself, and name `harness-hooks` as the way to enforce them.

### 5. Multi-tool setup

Use `AGENTS.md` as the single source. For a tool that reads a differently named file, create a minimal file that imports it. Claude Code reads `CLAUDE.md` and supports importing another file with `@path/to/file`, so its file contains the single line `@AGENTS.md`. For other tools, ask the user which files they need, and do not assume how they import.

If a tool-specific file already has content, do not replace it. Offer two options: move the shared content into `AGENTS.md` and leave an import line, or keep both and tell the user which one wins in practice. If the user has not said which other tools need a file, stop at that question and create no tool-specific file.

### 6. Show the diff, then write

Present the full file or the diff, and wait for approval. Then write the file.

### 7. Validate

After writing, check every path and command mentioned in the guide: each path exists and each command was run. Report the result. Also tell the user to check what the agent actually loads (for example with the tool's context command) because a file in the wrong place is silently ignored.

## Reconcile mode

Read the existing guide and test each statement against the repository. Report, in a table, one row per finding:

| Statement | Status | Evidence |
| --- | --- | --- |

Statuses: **current**, **stale** (the path, project, or command no longer exists or no longer passes), **missing** (the repository has something important the guide does not mention, such as a new enforced control), **redundant** (a rule that a tool already enforces, or something the agent can read from the code), **unverifiable** (a convention that cannot be checked).

To find **missing** items, re-run the pack's readouts of enforced controls, suppression mechanisms, protected files and risky operations, and compare them with the guide. A control that is enforced today and absent from the guide, or a new suppression mechanism in use, is a finding. To mark a command **current**, run it (with the same approvals as in create mode) and record its exit status. A command that does not run or fails is **stale**, or **unverifiable** if it could not be run.

Propose a patch for the stale and missing items and list the redundant ones as candidates for removal. Do not apply anything without approval.

## Final report

State: the mode used, the files created or changed, the commands run and their exit statuses, what was left out and why, the questions the user skipped, and the known limits below.

## Known limits to state

- The guide is advisory. An agent can ignore it. Enforcement needs hooks or permissions.
- Dependency direction is only derived where the stack exposes it. Elsewhere it comes from the user.
- The guide reflects the repository on the day it was written. Reconcile it when the project changes.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. How to list structure, and how to read dependency direction (or that it cannot be read)
3. Candidate verification commands and how to read their exit status
4. Suppression mechanisms
5. Configuration files that define the checks
6. Commands that act on remote systems or shared data
7. Pitfalls and limits
8. Verified on (date, and what was not re-verified)
