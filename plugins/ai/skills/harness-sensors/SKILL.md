---
name: harness-sensors
description: >-
  Makes a project's automated checks actually fail when they should, so an AI coding agent (and
  CI) cannot treat defective code as done. Detects the stack, measures which checks already exist
  and whether they fail the verification command or only warn, then enables security-focused
  static analysis, strict type or compiler checking, and failure-on-warning, one verified step at
  a time, with a gradual mode for legacy code that already has violations. Currently supports .NET
  and Python. Use when the user asks to "make the build fail on warnings", "enable analyzers",
  "turn on strict type checking or linting", "harden the build for coding agents", "configure
  sensors", "set up the harness checks", "fazer o build falhar em avisos", "ativar analyzers",
  "ativar verificação estrita", "configurar verificações para o agente", or wants objective checks
  to block an agent instead of its own self-assessment. Do NOT use it to write architecture rules
  (harness-architecture-guard), ban specific APIs (harness-banned-apis), configure formatting or
  style (harness-code-style), or fix the violations it surfaces.
---

# Harness sensors

## What this skill does

A coding agent normally treats a task as finished when its verification command exits with success. If a check only prints a warning, or is switched off, the agent sees success and moves on. This skill makes the relevant checks **fail the verification command** so the failure becomes an objective signal the agent has to fix.

Vocabulary used below:

- **Sensor**: an automated check that runs after code is written and reports through its exit status.
- **Verification command**: the command that runs the sensors (a build, a lint, a type check). The stack reference says which one applies.
- **Effective state**: what the tooling really resolves after merging every configuration file, not what one file says.
- **Suppression**: any mechanism that silences a diagnostic instead of fixing the code.

This skill covers correctness, type safety, security rules, failure-on-warning, and dependency vulnerability visibility. Formatting and style belong to `harness-code-style`.

## Hard rules

- Never assume the project has no checks. Measure the effective state first, then complete only what is missing.
- Never weaken an existing stricter setting. If the project already enforces more than this skill would add, report that and change nothing.
- Never add a suppression to make a check pass. If a rule looks wrong for the project, stop and tell the user.
- Never fix existing violations unless the user asks. Report them.
- Never commit, push, or stage files.
- Never install packages, change the pinned toolchain version, or run commands that need network access without asking first. If the user declines, report the control as "not run". If a tool the pack needs is not installed, report what depends on it as **unknown** and ask before installing it.
- Report counts and exit statuses only from real command output. Never estimate them.
- Match diagnostics by code, never by message text, because messages change with the tool's language and version.

## Workflow

### 1. Detect the stack

Look for the marker files listed in each stack reference under `references/stacks/`. Read every pack whose markers match.

- Several stacks in one repository: handle each separately and tell the user which one you are working on.
- No matching pack: explain what this skill would do in concept, state that the stack is not supported yet, and change nothing.
- A matching pack whose "Verified on" date is more than a few months old: say so before relying on it, and check the specific options you are about to use against current documentation.

### 2. Measure the effective state

Using the commands in the pack:

1. Confirm the toolchain runs (version command). If it does not, stop and report it.
2. Read the effective value of every control the pack lists. Do not infer it from a single file.
3. Run the verification command once and record the exit status and the number of diagnostics by code. When the stack has several commands (for example a linter and a type checker), record the exit status of each one separately.
4. Classify each control as one of: **enforced** (a violation fails the command), **reported** (a violation prints a warning only), **off**, or **unknown** (could not be determined; say why).

### 3. Decide the mode

- **Strict mode**: the verification command already passes with zero diagnostics, or the user accepts fixing what appears.
- **Gradual mode**: the baseline already has violations. Use it so new code is held to the standard without blocking on old code. Use only the mechanisms the pack lists for gradual adoption, and tell the user what each one costs (for example, markers added to source files, or a list that must be shrunk over time). Ask before adding any marker to source files, and never use inline suppression comments as the gradual mechanism.

If the user asks for an entire category or "all the rules", explain that this tends to produce mass suppression instead of fixes, and propose a smaller set to start with. Ask the user which scope they want when it is not obvious. The default scope is security-first, then type or compiler strictness, then failure-on-warning. Enabling every rule at once usually produces so much noise that people suppress instead of fixing.

### 4. Present the plan before writing

Show, for each change: the file, the exact lines to add or modify, the control it affects, and the expected effect on the verification command. Ask for confirmation. If the user asked for a dry run, stop here.

When a file already exists, merge into it. Never overwrite or reformat the rest of it.

### 5. Apply one control at a time

For each approved control:

1. Make the single change.
2. Run the verification command again.
3. Record the exit status and the diagnostics that appeared or disappeared, by code.
4. If the change breaks something unrelated to the control (a tool error, not a diagnostic), revert that change and report it.

Do not batch several controls into one step. The point is to show the user what each control costs.

### Optional: structured results

If the user wants the analyzer findings published by CI (for example as SARIF in a code-scanning view), ask once. This is not a sensor and changes no exit status. When it is wanted, add the wiring the stack reference describes, confirm that a build with it writes the files, and hand the publishing to `harness-ci-pipeline`. When the stack reference has no such section, say it is not supported for that stack.

### 6. Confirm the controls really fail

A control that is configured but does not fail the command is not a sensor. After applying, confirm each one is **enforced** by one of these, in order of preference:

- Reading the effective state again and checking the failure setting.
- Running the verification command and checking the exit status against a diagnostic that is known to exist.
- Suggesting `harness-sensor-probe` to prove it with a deliberately bad sample, when available.

If you cannot confirm a control, say it is configured but unconfirmed.

### 7. Report

Use this shape:

| Control | Before | After | Verified how |
| --- | --- | --- | --- |

Then list: what was changed (files), what was not changed and why, diagnostics left in the baseline (count by code), anything left unconfirmed, and the known limits below. State the verification command the agent should run to confirm completion.

## Known limits to state every time

- Sensors catch classes of defects. They do not know business rules or architecture.
- Static analysis here is local: limited data-flow coverage across methods and modules. It does not replace a dedicated security scanner, dependency auditing, or dynamic testing.
- Every suppression mechanism silences a sensor. Writing "do not suppress" in a guide is not the same as verifying it. A hook can enforce it (see `harness-hooks`).
- Newer tool versions can add rules and make a previously passing check fail. Say whether the project pins the rule set or follows the latest one.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline, so skills stay consistent and a new stack can be added by writing one file:

1. Detection markers (files and what each means)
2. Canonical commands (toolchain version, effective-state readout, verification command, and how to read its exit status)
3. Controls table (control, mechanism, how to read effective state, how to enable, whether it fails the command)
4. Gradual-adoption mechanisms and their cost
5. Pitfalls specific to the stack
6. Limits specific to the stack
7. Verified on (date, and which items were not re-verified)
