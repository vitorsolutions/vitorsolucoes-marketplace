# Harness Hooks

Creates run-time guards for an AI coding agent in your project: it cannot finish while the checks fail, cannot add diagnostic suppressions, cannot run configured destructive commands, and cannot send credential-like text in a prompt.

## Why this skill exists

A line in an instructions file asks the agent to behave. A hook makes the harness check. The agent's usual shortcut when a check fails is to silence the check, and a request not to do that is not enforcement. This skill installs guards that run automatically and block, with a message that says what to do instead.

## The guards

| Guard | When it runs | What it does |
| --- | --- | --- |
| Definition of done | When the agent tries to finish | Runs the project's verification commands. If one fails, the agent keeps working. Also scans the working tree for newly added suppressions, including ones written through the shell. |
| Suppression guard | Before edits and writes | Blocks an edit that adds a suppression marker to a covered file. |
| Command guard | Before shell commands | Denies or asks about commands that match patterns anywhere in the command text. |
| Prompt guard | When a prompt is submitted | Blocks a prompt that looks like it contains a credential, without repeating it. |

## How it works

- Installs one tested script, unchanged, and a configuration file that holds everything project-specific.
- Writes the settings entries, merging into what already exists.
- Merges into an existing configuration file instead of replacing it, and sets the timeouts from the measured duration of your checks.
- Validates the configuration (the check also warns about a program that is not installed and about timeouts), runs a blocked and an allowed sample for each guard, and, with your permission, proves the wiring with a short capped run of the real agent.
- Every guard fails closed: if the hook breaks, it blocks and says why. Where the tool supports it, a hook that cannot even start is also set to block.

## Supported agent and stacks

Claude Code, with stack content for .NET and Python in `references/stacks/`. The agent details are in `references/claude-code.md`.

## What it will not do

- Overwrite or reorder existing hooks, scripts or settings, or edit user-level and managed settings.
- Write anything without showing it first and getting your confirmation.
- Disable hooks, or run the project's checks without your agreement.
- Commit or stage anything.

## When to use it

When you want rules the agent cannot talk its way around: "block suppressions", "run the tests before finishing", "stop destructive commands".

## Limits

Only an exit status of 2 blocks, and a hook that times out or cannot start lets the action through, except where the failure option is set. The stop guard cannot use that option and has a loop cap. Pattern guards stop common forms, not every form. The agent can edit its own hooks unless permission rules protect them, and hooks can be turned off, so they are guard rails and not a security boundary.
