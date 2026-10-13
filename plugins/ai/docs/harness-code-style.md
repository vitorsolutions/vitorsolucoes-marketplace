# Harness Code Style

Makes code style verifiable by a tool and makes violations fail, so a coding agent's output matches the project's conventions before a person reviews it.

## Why this skill exists

Style rules are cheap to state and expensive to enforce by review. When the style check fails, an agent corrects its own output. Many projects have a detailed style configuration that nothing checks in the command line build, or a formatter that only runs in editors. This skill closes that gap with a deliberately small rule set.

## What it does

- Detects the stack and reads the style configuration actually in effect.
- Runs the style check in verify-only mode and counts existing drift by rule.
- Adds a small set of style rules, each configured to fail on its own, one at a time.
- Offers gradual options when the code already deviates from the rules.
- Keeps reformatting of existing code as a separate step that needs its own approval.

## Supported stacks

| Stack | What it configures |
| --- | --- |
| .NET | `.editorconfig` severities, the property that enables style rules in the build, and the format verification command |
| Python | Ruff formatting check and the style rule families in the lint selection |

Each stack lives in a reference file under `references/stacks/`.

## What it will not do

- Reformat the codebase as a side effect, or run any command that rewrites files as part of the check.
- Enable a whole rule category at once.
- Cover correctness, type or security rules (see `harness-sensors`) or banned APIs (see `harness-banned-apis`).
- Commit or stage anything, install packages, or use the network without asking.

## When to use it

When you want the agent held to your conventions: "enforce code style", "make the build check formatting", "set up the editorconfig".

## Limits

Style rules say nothing about correctness. A tool applies only the rules it supports, so other conventions stay in the agent guide. Every suppression mechanism silences a rule.
