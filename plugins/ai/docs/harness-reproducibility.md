# Harness Reproducibility

Makes a repository resolve the same toolchain and the same dependency versions on every machine, in CI, and in every agent session, so a result means the same thing everywhere.

## Why this skill exists

If the toolchain or a dependency can change between two runs, a check that passed yesterday can fail today with no change in the code, and an agent can get a different result from a developer. This skill finds what floats and pins it.

## What it does

- Detects the stack and measures three layers: the toolchain version, how direct dependencies are declared, and whether a lock file covers the full dependency set.
- Checks that lock files are really tracked by git and used by CI, because a lock file that is ignored or bypassed protects nothing.
- Proposes options with their trade-offs and applies one layer at a time.
- Verifies with commands that cannot rewrite a lock file, and says which failure paths it did not exercise.

## Supported stacks

| Stack | Covered |
| --- | --- |
| .NET | The SDK pin, central package management, lock files and locked restore |
| Python | The interpreter pin and the `uv` lock with its checking commands. Poetry and plain requirements are covered from documentation only |

Each stack lives in a reference file under `references/stacks/`.

## What it will not do

- Upgrade or downgrade a dependency or a toolchain to make a pin pass.
- Run a command that can rewrite a lock file as a way to check it.
- Audit dependencies for vulnerabilities (a lock file can hide a fix until refreshed).
- Commit or stage anything, or use the network without asking.

## When to use it

When results differ between machines, CI and agent sessions: "pin the SDK", "add lock files", "make builds reproducible".

## Limits

A lock file is only as good as the habit of updating it. Pins cover what the project declares, so operating system packages, container images and external services still float. Developers can bypass a pin locally, so CI and the agent's commands must use the locked verification.
