# Harness Agent Guide

Creates or reconciles the instruction file that tells an AI coding agent how to work in a repository, built from the real project instead of from assumptions.

## Why this skill exists

An agent that does not know a repository's rules discovers them by trial and error. A short, accurate guide gives it the definition of done, the project layout, and the limits from the first attempt. A long or wrong guide does the opposite: it gets ignored, or its mistakes get followed.

## What it does

- Detects the stack and any existing instruction files.
- Derives structure and dependency direction from the project, where the stack exposes them.
- Runs the verification commands and lists in the definition of done only the ones that exited with success. A command that fails is reported and you decide whether to list it with a red-baseline note. A command that was not run is marked as not run.
- Asks a few questions for what cannot be derived, each with a default that lets you skip it.
- Drafts a short guide with fixed sections and shows it for approval before writing.
- Uses `AGENTS.md` as the single source, with a minimal import file for tools that read a different file name.
- In reconcile mode, compares an existing guide against the repository and reports what is stale, missing, redundant, or unverifiable, without overwriting it.

## Supported stacks

| Stack | What it reads |
| --- | --- |
| .NET | Solution projects, project reference graph, build, test and format commands, suppression markers |
| Python | Package layout, configured tools (linter, type checker, test runner), the project's environment runner |

Each stack lives in a reference file under `references/stacks/`.

## What it will not do

- Overwrite an existing guide, invent conventions, or list a command it did not run.
- Add credentials, internal hostnames, or personal data to the guide.
- Enforce the rules it writes. The guide is advice for the agent. Enforcement belongs to hooks and permissions.
- Commit or stage anything.

## When to use it

Ask for it when a repository has no instructions for agents, or when the existing ones may have drifted: "create AGENTS.md", "check if my agent instructions are up to date".

## Limits

The guide is advisory and an agent can ignore it. Dependency direction is only derived where the stack exposes a reference graph. The guide reflects the repository on the day it was written, so reconcile it when the project changes.
