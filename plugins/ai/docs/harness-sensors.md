# Harness Sensors

Makes a project's automated checks fail when they should, so an AI coding agent and CI cannot treat defective code as done. It measures what already exists, enables security and type checks one step at a time, and offers a gradual mode for legacy code.

## Why this skill exists

A coding agent usually considers a task finished when its verification command exits with success. Many projects have good checks that only print warnings, or that are switched off. This skill connects those checks to a failure condition, so the failure becomes an objective signal instead of the agent's own opinion.

## What it does

- Detects the stack and reads the effective configuration, not just a single file.
- Classifies each control as enforced, reported, off, or unknown.
- Proposes changes as a plan, applies them one control at a time, and re-runs the verification command after each one.
- Handles legacy code with a gradual mode that holds new code to the standard without blocking on old violations.
- Confirms that each control really fails the command, or says it could not.
- Optionally wires the compiler's SARIF output behind a switch that only CI sets, so findings can be published by `harness-ci-pipeline`. It is not a sensor and changes no exit status (.NET only).

## Supported stacks

| Stack | Controls covered |
| --- | --- |
| .NET | Nullable checking, built-in analyzers, security rule category, failure on warning, NuGet audit |
| Python | Security and bug-finding lint rules, strict type checking, lint failure status, optional dependency audit |

Each stack lives in a reference file under `references/stacks/`. Adding a stack means adding one file that follows the outline in the skill.

## What it will not do

- Fix existing violations, add suppressions, or weaken a stricter setting that is already there.
- Install packages, change the pinned toolchain version, or use the network without asking.
- Commit or stage anything.
- Cover formatting or style, API bans, or architecture rules. Those belong to separate harness skills.

## When to use it

Ask for it when you want a coding agent to be blocked by objective checks: "make the build fail on warnings", "turn on strict type checking", "harden the build for agents".

## Limits

Sensors catch classes of defects, not business rules. Local static analysis has limited data-flow coverage and does not replace a dedicated security scanner. Every suppression mechanism silences a sensor, so pair this skill with a guard that blocks suppressions when that matters.
