---
name: harness-banned-apis
description: >-
  Turns "do not use X" project policies into checks that fail, with a message that tells the
  developer or the coding agent what to use instead. Detects the stack, proposes policies from a
  catalog filtered by what the project actually uses (such as reading the clock directly, raw SQL,
  creating HTTP clients by hand), measures how many existing uses each policy would hit, wires the
  mechanism into the project, and validates every entry against a real use, because a wrong entry
  bans nothing and reports nothing. Currently supports .NET and Python. Use when the user asks to
  "ban an API", "forbid DateTime.Now", "block raw SQL", "enforce a coding policy in the build",
  "make the agent stop using X", "proibir o uso de uma API", "bloquear DateTime.UtcNow", "criar
  política de código verificável", or wants internal rules of the type "never use X, use Y"
  checked automatically. Do NOT use it to enable general security or type rules (harness-sensors),
  to enforce formatting (harness-code-style), or to enforce dependency direction between modules
  (harness-architecture-guard).
---

# Harness banned APIs

## What this skill does

Some problems are not defects the compiler or a general-purpose analyzer can see. They are decisions the team has made: "time comes from an injected clock", "SQL goes through the parameterized API", "HTTP clients are created by a factory". This skill makes those decisions executable: a use of the forbidden symbol fails the check, and the message names the alternative.

Vocabulary:

- **Policy**: one rule of the form "do not use X, use Y instead".
- **Entry**: the line or setting that expresses one policy in the stack's mechanism.
- **Validation**: proving that an entry reports a real use of the symbol it names.
- **Existing uses**: places where the project already calls the forbidden symbol.

## Hard rules

- A policy belongs to the user. Propose from the catalog, but never add one the user did not approve.
- Every entry needs a message with the alternative. A ban without an alternative only produces confusion.
- Never assume an entry works. Validate each one (see step 6). A malformed entry is silent: it bans nothing and reports nothing.
- Never fix existing uses unless the user asks. Report where they are.
- Never suppress a ban to make the check pass.
- Never commit, push, or stage files. Never install packages or use the network without asking.
- Merge into existing files. Never overwrite or reorder a policy list that already exists.

## Workflow

### 1. Detect the stack and the current state

Find the markers in each stack reference under `references/stacks/` and read only the matching pack. No matching pack: say the stack is not supported yet, explain the idea in concept, and change nothing.

Then read what already exists: the mechanism's package or setting, the policy list, and how its severity is set. Report it. If the mechanism is already in place, you are adding or fixing entries, not installing it.

### 2. Propose policies

1. List the catalog entries from the pack whose condition is true for this project (for example, a package that provides the forbidden API is referenced).
2. Ask the user for their own policies. These are the main source. The catalog only gives starting points.
3. For each policy, agree on the symbol and the alternative message.

### 3. Measure existing uses

For each approved policy, search the source for uses of the forbidden symbol and report the count and the locations. Use the pack's search hints. Where the stack can only match by text, say that the count is approximate.

An exact count comes from the tool itself, which needs the entry wired as a warning first. That is a change to project files, so ask for approval to wire it (step 5) before counting, or report the text count as approximate and say so. Count distinct locations (file, line and column), because tools may print a diagnostic more than once.

### 4. Decide the severity and the mode

A ban is only a gate when it fails the verification command.

- If there are no existing uses, the ban can fail immediately (strict mode).
- If there are existing uses, offer gradual options from the pack, and say what each costs. Do not turn them into failures without the user's approval.

State plainly which option leaves existing uses reported but not failing, because that is a decision about risk.

### 5. Present the plan, then apply

Show, for each file: the exact lines to add or change, the policy each line serves, and the expected effect. Ask for confirmation. Then apply one policy at a time.

### 6. Validate every entry

For each entry, prove it reports a real use:

- If an existing use exists, run the verification command and check that the entry reports it. The use must match the entry's exact signature: for a symbol with overloads, one use per overload listed. A use of a different overload proves nothing.
- If none exists, create one temporary file containing one use of each unvalidated symbol, run the command, and remove the file afterwards. Follow these rules: exactly one new file, refuse if the path exists, cleanup that also runs on failure, and confirm afterwards that nothing else changed.

Validate with the project's own verification command, not with a flag that overrides its configuration, because an override can pass while the real command reports nothing.

An entry that reports nothing is **silent**. Tell the user which entries are silent and why they are probably wrong (see the pack's pitfalls). Fix them with approval and validate again.

### 7. Report

| Policy | Symbol | Alternative | Existing uses | Validated | Severity |
| --- | --- | --- | --- | --- | --- |

Then list what was changed (files), what was left out, silent entries, and the limits below. Tool output may be localized: match diagnostic codes, never message text. Say which command the agent should run to see the bans.

## Known limits to state

- A ban matches the symbol, not the intent. It also blocks safe uses, and it misses a forbidden behavior reached through a different symbol.
- Some mechanisms only match imports or attribute access, not every form of call. The pack lists what its mechanism cannot see.
- Every suppression mechanism silences a ban. See `harness-hooks` to block suppressions.
- A policy list is project knowledge. Review it when the project's decisions change.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. The mechanism: how a ban is expressed, where it lives, how it is wired, what its default severity is
3. Entry syntax, with examples
4. Catalog of policies, each with the condition that makes it relevant
5. How to find existing uses
6. Gradual-adoption options and their cost
7. How to validate entries
8. Pitfalls and limits
9. Verified on (date, and what was not re-verified)
