# Harness Setup

Assesses how well a repository is prepared for AI coding agents and produces an ordered adoption plan, without changing anything. It is the entry point of the harness skills, and each step it recommends is carried out by its own skill.

## Why this skill exists

A coding agent is only as reliable as what surrounds it: checks that fail, instructions it can read, limits it cannot cross, and evidence that these work. Most repositories have some of that and not the rest, and it is not obvious which piece to add first. This skill looks, reports with evidence, and proposes an order.

## What it does

- Detects the stack and reads the repository without modifying it.
- Classifies each harness layer as present, partial, missing, unknown, or not applicable, citing what it read or ran.
- Recommends strict or gradual adoption for the checks layers, depending on how many violations the project already has.
- Produces an ordered plan: which skill to run, why, in which mode, whether it writes to the repository, its risk, and what it depends on.
- Hands off to the chosen skill. Each skill also works on its own, so you can skip the plan when you already know what you want.

## The layers

| Layer | Skill |
| --- | --- |
| Reproducible environment | `harness-reproducibility` |
| Checks that fail | `harness-sensors` |
| Style | `harness-code-style` |
| Banned APIs | `harness-banned-apis` |
| Tests | `harness-test-baseline` |
| Architecture rules | `harness-architecture-guard` |
| Agent guide | `harness-agent-guide` |
| Permissions | `harness-permissions` |
| Hooks | `harness-hooks` |
| CI | `harness-ci-pipeline` |
| Proof that checks fire | `harness-sensor-probe` |

## Supported stacks

.NET and Python. Each stack lives in a reference file under `references/stacks/`. Repositories with more than one stack get one plan per stack.

## What it will not do

- Create, edit, delete, commit, or stage anything.
- Run a build, restore, or test without asking.
- Claim the harness is complete or secure.
- Do the work of the other skills itself.

## When to use it

When you want to prepare a repository for coding agents and do not know where to start, or when you want to check what changed: "set up the harness", "what is missing for agents to work well here".

## Limits

The assessment reads files and settings. It does not measure how well the harness works, and the proof layer only counts when a probe result exists. A complete set of layers does not make code correct or secure.
