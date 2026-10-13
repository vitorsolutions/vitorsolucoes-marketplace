---
name: harness-code-style
description: >-
  Makes code style verifiable by a tool and makes violations fail, so a coding agent's output
  matches the project's conventions without a human reviewer pointing out indentation, import
  order, brace usage or namespace style. Detects the stack, reads the existing style
  configuration, measures how far the code is from it, then adds a deliberately small set of
  rules that fail the style check, never reformats the codebase without explicit approval, and
  keeps style separate from correctness and security rules. Currently supports .NET and Python.
  Use when the user asks to "enforce code style", "make the build check formatting", "set up
  editorconfig", "add a formatter check", "make the agent follow our style", "configurar o
  .editorconfig", "verificar formatação no build", "padronizar o estilo do código", or wants style
  rules that fail instead of being suggestions. Do NOT use it to enable security, type or
  correctness checks (harness-sensors), to ban specific APIs (harness-banned-apis), or to
  reformat the whole codebase as a side effect.
---

# Harness code style

## What this skill does

Style rules are cheap to state and expensive to review by hand. When the style check fails, an agent corrects its own output before a person ever sees it. This skill sets that up: a configuration file the tools read, a check that exits with failure, and a small rule set that the team has chosen on purpose.

Vocabulary:

- **Style check**: the command that reports style violations and fails when there are any.
- **Style rule**: a rule about form, such as indentation, import order, braces, or namespace layout. Rules about bugs, types, or security are not style rules.
- **Existing drift**: how many violations the current code already has.

Boundary with `harness-sensors`: that skill owns correctness, type, and security checks and the "fail on any warning" switch. This skill owns style rules and gives each chosen style rule its own failure condition, so style does not depend on the other switch.

## Hard rules

- Keep the rule set small. Each rule that fails the check must be worth blocking work. Do not enable a whole style category at once. If the user asks for a whole category or "all the rules", say that this usually ends in mass suppressions instead of fixes, and offer a small subset instead.
- Never reformat existing code as a side effect. Formatting the codebase is a separate step with its own approval (see step 6).
- Never relax an existing stricter setting.
- Never add a suppression to make the check pass.
- Merge into existing configuration files. Never overwrite or reorder them.
- Never commit, push, or stage files. Never install packages or use the network without asking.
- Report counts only from real command output.

## Workflow

### 1. Detect the stack and the current state

Find the markers in each stack reference under `references/stacks/` and read only the matching pack. No matching pack: say the stack is not supported yet, explain in concept, and change nothing.

If the style tool is not installed, report the style check as **unknown** and ask before installing it.

Read the configuration in effect (not just one file): the style configuration file, any nested ones, and the setting that decides whether style is checked in the verification command. Classify the style check as **enforced**, **reported**, **off**, or **unknown**.

### 2. Measure existing drift

With the user's agreement where the rules require it, run the style check in verify-only mode and record the exit status and the violations by rule. Verify-only means no file changes. If a command would modify files, do not run it.

### 3. Choose the scope

Offer a minimal default and let the user add rules:

- Formatting basics: indentation, line endings, final newline, charset.
- Import or `using` ordering.
- A short list of consistency rules the team already follows (for example brace usage, namespace layout).

Ask which conventions the team actually uses. Do not import a popular style guide wholesale.

### 4. Choose the mode

- **Strict**: no existing drift, or the user accepts reformatting in step 6.
- **Gradual**: drift exists. Use the pack's gradual options. State what each costs.

### 5. Present the plan, then apply

Show each file, the exact lines to add, and the expected effect on the check. Wait for confirmation. Apply one rule at a time and re-run the style check after each. Record the violations that appear. Record the exit status of every command that makes up the style check (a stack can have a lint command and a formatter command).

### 6. Reformat existing code (only if the user asks)

This is a separate, explicit step. Before doing it:

- Tell the user how many files will change, using verify-only output.
- Recommend doing it in its own change, so the diff of the real work stays readable, and mention that git can be told to ignore such a commit in blame (a file listing the revisions to ignore).
- Do the reformat only after approval, then re-run the style check.

### 7. Confirm the check fails

A rule that is configured but does not fail the command is not enforced. Confirm by one of:

- Reading the effective state again.
- Running the check against a known violation. Do not edit the user's code for this: create one throwaway file with a violation, run the check, and remove the file afterwards.
- Suggesting `harness-sensor-probe` for a full proof.

### 8. Report

| Rule | Where configured | Before | After | Verified how |
| --- | --- | --- | --- | --- |

Then state what changed, what did not, the violations left in the baseline, anything unconfirmed, the command the agent should run, and the limits below.

## Known limits to state

- Style rules say nothing about correctness. A well-formatted program can be wrong.
- A tool applies only the rules it supports. Conventions it cannot express stay in the agent guide.
- Every suppression mechanism silences a rule. Use `harness-hooks` to block them.
- A formatter version change can reformat code. Pin the tool version if stability matters (see `harness-reproducibility`).

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. Where style is configured and how to read the effective state
3. Style check commands and how to read their exit status
4. How a rule is made to fail
5. Gradual-adoption options and their cost
6. How to reformat, and the cost
7. Pitfalls and limits
8. Verified on (date, and what was not re-verified)
