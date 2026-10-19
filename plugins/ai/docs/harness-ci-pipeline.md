# Harness CI Pipeline

Creates or reviews the continuous integration pipeline so that it repeats your local definition of done on every change, and so that it cannot look green while proving nothing.

## Why this skill exists

Local checks depend on someone, a person or an agent, running them. CI makes them run on every change and puts the result outside the author's machine. A pipeline that skips a command, ignores an exit status, installs without a lock, or passes when no test ran gives false confidence, and an agent will happily work against it.

## What it does

- Detects the CI host and the stack, and takes the definition of done from your agent guide or from you.
- Reviews an existing pipeline against a checklist (every command present, locked install, no silent failure, fails when no tests ran, pinned toolchain and runner, minimal permissions, pinned third-party steps, evidence kept on failure, time limit) and proposes a patch instead of rewriting it.
- Generates a new pipeline when there is none, resolving action and task versions when it writes the file rather than from memory.
- Includes a tested script that fails the run when a test run executed no tests, including a suite where everything was skipped. It skips XML files that are not test results, such as a coverage report.
- Checks that the lock files exist before using a locked install, because a locked restore can succeed when there is no lock file.
- Validates the file with the host's linter where one exists, and replays the same commands locally.
- Publishes static-analysis results (SARIF) when the project emits them, as an artifact or to the host's code-scanning view. The write permission that publishing needs is confined to a separate job that runs no project code, and the run fails when the build wrote no SARIF file.

## Supported hosts and stacks

| Hosts | Stacks |
| --- | --- |
| GitHub Actions (validated with `actionlint`), Azure Pipelines (written from documentation, not validated by a tool) | .NET, Python |

Hosts live in `references/` and stacks in `references/stacks/`.

## What it will not do

- Add deployment steps, publish packages, or touch environments.
- Write secrets or tokens into a file, create secrets, or change repository or branch settings. A token pasted into the conversation is not repeated, and is treated as exposed.
- Overwrite an existing pipeline, push, trigger a run, commit, or stage anything.
- Claim the pipeline works because the file is valid.

## When to use it

When you want every change verified the same way as on your machine: "create the CI pipeline", "review our pipeline", "make the pipeline fail when tests don't run".

## Limits

A valid file is not a working pipeline: only a real run proves it. Publishing SARIF shows findings and does not fail the run. The SARIF publishing steps were written from documentation and were not run on a host. CI protects nothing until the check is required before merging, which is a setting on the host. Pinned versions age and need updating. The count guard shows that tests ran, not that they are good tests.
