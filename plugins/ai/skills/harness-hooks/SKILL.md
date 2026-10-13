---
name: harness-hooks
description: >-
  Creates run-time guards for an AI coding agent in the project: a definition-of-done check that
  blocks the agent from finishing while the project's checks fail, a guard that blocks edits adding
  diagnostic suppressions, a guard for commands that act on remote systems or destroy work, and a
  guard that stops credential-like text from being sent in a prompt. It installs one tested,
  configuration-driven script, writes the settings entries, validates the configuration, and
  proves each guard fires. Preview and confirmation first, never overwrites existing hooks. Targets
  Claude Code, with stack-specific content for .NET and Python. Use when the user asks to "create
  hooks", "block the agent from suppressing warnings", "make the agent run the tests before
  finishing", "stop destructive commands", "criar hooks para o agente", "bloquear supressão de
  diagnósticos", "rodar o critério de pronto antes de encerrar", or wants rules the agent cannot
  talk its way around. Do NOT use it for static allow or deny rules on files and commands
  (harness-permissions), to write the guide the agent reads (harness-agent-guide), or to enforce
  checks in CI (harness-ci-pipeline).
---

# Harness hooks

## What this skill does

An instruction in a guide asks the agent to behave. A hook makes the harness check. This skill sets up four guards that run automatically around the agent's actions:

| Guard | Event | What it does |
| --- | --- | --- |
| Definition of done | Stop | Runs the project's verification commands when the agent tries to finish. If one fails, the agent is told what failed and keeps working. Also scans the working tree for newly added suppressions, including ones added through the shell. |
| Suppression guard | Before edits and writes | Blocks an edit that adds a suppression marker (a pragma, a `noqa`, a type-ignore comment) to a file the rules cover. |
| Command guard | Before shell commands | Denies commands that match the configured patterns anywhere in the command text, or asks the user to confirm. Catches forms that a static permission rule misses. |
| Prompt guard | When a prompt is submitted | Blocks a prompt that appears to contain a credential, without echoing it. |

Vocabulary:

- **Hook**: a command the agent tool runs automatically on an event. It can block the action.
- **Guard**: one of the four behaviors above.
- **Configuration**: the data file that tells the script what to check. The script contains no project knowledge.
- **Fail closed**: when the hook itself breaks, it blocks and says why. A broken hook that silently allows protects nothing.

Division with `harness-permissions`: static rules on files and commands (allow, ask, deny) belong there. Hooks are for logic that has to inspect content or run something. Protecting the hook files and settings themselves is done with permission rules.

## Hard rules

- Never overwrite or reorder existing hooks, hook scripts or settings. Merge, and keep what is there.
- Show the exact files and settings entries before writing, and wait for confirmation. This skill writes to the agent's own configuration, so a dry run is the default and writing needs a yes.
- Write JSON files with the file-writing tool, never through a shell here-document. Backslashes in regular expressions are collapsed by some shells and produce invalid JSON.
- Never edit user-level or managed settings. Write to the project's settings, and ask whether the file is the shared one (committed) or the local one (personal).
- Never put secrets, tokens, or internal hostnames in the configuration.
- Every guard that blocks must give a message that says what to do instead.
- Do not run the project's checks for the definition of done until the user agrees, and do not run the guard tests against real data.
- Never commit, push, or stage files.
- Do not disable hooks, and do not use the settings that turn all hooks off.

## Workflow

### 1. Detect the agent, the stack and the runtime

- **Agent**: this skill supports Claude Code. Look for its project folder and instruction files. For another agent, say that the hook mechanism is not covered yet and stop.
- **Stack**: find the markers in each stack reference under `references/stacks/` and read only the matching pack. No matching pack: explain the guards in concept and stop.
- **Runtime**: the script needs Python 3 and nothing else (standard library). Check that it runs (`python --version`, or `python3`). If it is not available, say so and stop. Do not install it. A port to another runtime is possible only if the user asks and it is then checked against the same tests.
- **Claude Code version**: check `claude --version`. The settings entries use the argument-list form of the command and the `onFailure` option, which old versions may not accept. Read `references/claude-code.md` for the entry to write and for what to do on an older version.

### 2. Read what exists

Read the project's settings files for existing hooks, and the hooks folder. Report what is there. Existing hooks are kept as they are. If a guard already exists in another form, ask whether to keep it or replace it.

### 3. Choose the guards

Offer the four guards and let the user pick. Explain the cost of each in plain terms:

- The definition-of-done guard runs the project's commands whenever the agent tries to stop, so slow commands slow every finish. Ask how long each command takes and offer a faster subset for the guard (for example the unit tests only, or build and format without the full suite), leaving the slow suite to CI. Offer the "only when something changed" option, and say that it helps little in a working tree that is already dirty, because every stop then still runs the commands. Set a timeout above the real duration: the first configuration uses the user's estimate, and step 7 corrects it with the measured durations.
- The suppression guard can block a legitimate use. Ask which paths to ignore (generated code and migrations are the usual ones).
- The command guard and the prompt guard are pattern based. They stop common forms, not every form.

### 4. Gather the content

From the stack reference and from the user:

- **Definition of done**: the commands. Prefer the ones in the project's agent guide or in `harness-agent-guide`'s output, and those that were run and passed. Each command is a program and an argument list, never a shell string.
- **Suppression rules**: the markers, with the file patterns they apply to.
- **Commands**: patterns for the commands to deny and to ask about. Start from the generic list below and the pack's remote and data commands, then add the user's.
- **Prompt secrets**: patterns, starting from the generic list below.

Generic starting points (the user accepts, edits, or drops each one):

- Deny: a force push to a remote. Decide with the user whether `--force-with-lease` is allowed. A bare `--force` pattern also matches `--force-with-lease`. The regular expression `git\b.*\bpush\b.*(--force(?![-\w])|\s-f\b)` denies a plain force push and lets the lease form through, and an ask rule `git\b.*\bpush\b.*--force-with-lease` can confirm the lease form (both tested in the script's test suite; double the backslashes for JSON).
- Ask: discarding all local changes (`git reset --hard`).
- Prompt secrets: a `password` or `pwd` setting with a value, a private key header, a long token with a recognizable vendor prefix.

Regular expressions are written inside JSON, so every backslash is doubled. After writing, the check step catches mistakes.

### 5. Preview

Show:

- The files to create: the script copied unchanged, and the configuration.
- The settings entries to add, with the matcher and the command for each.
- For each guard, one sentence on what it will block and one on what it will not.

Wait for confirmation. If the user asked for a dry run, stop here.

### 6. Install

1. Copy `scripts/harness_hooks.py` to the project's hooks folder, unchanged. If a file with that name exists, compare. Keep it if identical, ask if it differs.
2. Write the configuration file next to it, with the file-writing tool. If `harness-hooks.config.json` already exists, read it first, add the new rules and commands to its lists, keep every existing entry, and show the merged result in the preview. Never replace it.
3. Merge the settings entries into the chosen settings file. Add, do not replace. Keep every other key.
4. On the guards that run before an action or on a prompt, set `"onFailure": "block"` when the version supports it. Without it, a hook that cannot start (for example the interpreter is not found) lets the action through. The stop guard cannot use it. Say so in the report.

### 7. Validate

1. Run the script in check mode. It must report the counts of rules and commands, and exit with success. Fix any error it reports.
2. Run a self-test for each guard you installed: feed the script a sample event that should be blocked and one that should pass, and check the exit status. Use the example commands in `references/claude-code.md`. For the definition-of-done guard, also run the commands themselves once, with permission, and report their exit statuses and how long each took. Use the measured durations to set each command's `timeout` in the configuration, and set the Stop hook `timeout` in the settings above the sum of the configured command timeouts, not of the measured durations (check mode prints that sum). Build the sample events with a JSON-aware tool (`python -c "import json; print(json.dumps(...))"`), not `echo`: shells mangle backslashes in Windows paths and give false results.
3. Confirm the settings file is valid JSON.

### 8. Prove it in the real agent (optional, with permission)

The self-tests prove the script. Only a real run proves the wiring in the agent. Offer a bounded run, as described in `references/claude-code.md`: a short non-interactive session with a spending cap, using a prompt that should be blocked. It uses the model, so ask first. If the user declines, tell them how to check by hand.

### 9. Report

| Guard | Event | Configured with | Self-test | Real run |
| --- | --- | --- | --- | --- |

Then list: the files created and changed, what each guard will not catch, the commands to re-validate, and the limits below.

## Known limits to state

- **Only exit status 2 blocks.** Any other failing status lets the action go ahead. The script is built never to exit with 1 for this reason.
- **A hook that times out lets the action proceed** for the before-action event. Set timeouts, and keep guards fast.
- **A hook that cannot start lets the action proceed** unless `onFailure` is set to block, and the stop guard cannot use that option. If the interpreter disappears, the stop guard stops working silently. The self-test and `harness-sensor-probe`-style checks should be repeated after environment changes.
- **Pattern guards are partial.** A forbidden command written in an unusual form, or a secret in an unusual shape, can pass. Use sandboxing or credential scoping for hard boundaries.
- **The agent can edit its own hooks** unless permission rules protect the hook files and settings. Pair this skill with `harness-permissions` for that.
- **Hooks can be turned off** by a setting or a command-line option. They are guard rails, not a security boundary.
- **The stop guard has a loop cap.** After a number of consecutive blocks the tool ends the turn anyway. A check that cannot be fixed will not trap the agent forever, and it will not be enforced beyond the cap either.
- **Writes made by a shell command** are not seen by the edit guard. The stop guard's diff scan covers them at the end of the turn.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. Candidate definition-of-done commands (program and arguments)
3. Suppression markers and the file patterns they apply to, with the ignore paths for generated code
4. Commands that act on remote systems or shared data, as patterns, with suggested deny or ask
5. Pitfalls and limits
6. Verified on (date, and what was not re-verified)
