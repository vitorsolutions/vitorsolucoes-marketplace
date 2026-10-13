---
name: harness-ci-pipeline
description: >-
  Creates or reviews the continuous integration pipeline so that it repeats the project's local
  definition of done on every change: the same locked install, build or lint, tests, and style
  commands, with no step that can fail silently, least-privilege access, a pinned toolchain and
  runner, evidence kept as an artifact, and a guard that fails when a test run executed no tests.
  Detects the CI host and the stack, reviews an existing pipeline against a checklist before
  proposing a patch, resolves action and task versions at generation time instead of from memory,
  validates the file with the host's linter where one exists, and runs the same commands locally.
  Currently supports .NET and Python on GitHub Actions and Azure Pipelines. Use when the user asks
  to "create the CI pipeline", "make CI run the same checks as local", "review our pipeline",
  "make the pipeline fail when tests don't run", "criar o pipeline de CI", "revisar o pipeline",
  "o CI deve repetir o critério de pronto", or wants agent changes verified on every push. Do NOT
  use it to add deployment steps, to configure repository or branch settings, or to manage
  secrets.
---

# Harness CI pipeline

## What this skill does

Local checks depend on someone, a person or an agent, running them. CI makes them run on every change and gives the result a place outside the author's machine. This skill builds a pipeline whose job is the definition of done, repeated faithfully, and reviews an existing pipeline for the ways it can look green and prove nothing.

Vocabulary:

- **Definition of done**: the commands that must all succeed before a change counts as finished.
- **Locked install**: installing dependencies in a mode that fails if the lock file does not match the project.
- **Silent failure**: a step whose failure does not fail the run, such as one marked to continue on error or one that ignores an exit status.
- **Evidence**: result files kept as an artifact so a failure can be inspected.

## Hard rules

- The pipeline verifies. It never deploys, publishes, signs, or touches environments.
- Never put a secret, token, or credential in the file. Do not create secrets, and do not change repository or branch settings.
- If the user pastes a token or credential into the conversation, do not repeat it, store it, or write it anywhere. Say it must be treated as exposed and rotated if it is real, that secrets belong in the host's secret store, and offer verification-only changes instead.
- No step may fail silently: no continue-on-error, no `|| true`, no exit status that is thrown away.
- Run with the minimum token permissions the job needs. For checking code, read access to the repository contents is enough.
- Never copy action or task versions from memory. Resolve them when you generate the file (see the host reference).
- Never overwrite an existing pipeline file. Review it and propose a patch.
- Never push, trigger a run, commit, or stage files.
- Do not claim the pipeline works because it is syntactically valid. Say what was validated and what was not.

## Workflow

### 1. Detect the host and the stack

- **Host**: look for pipeline definitions in the usual places (`.github/workflows`, `azure-pipelines.yml`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci`, `bitbucket-pipelines.yml`), and the host name of the repository's remote. If several or none, ask. Read the matching host file directly under `references/` (`github-actions.md`, `azure-pipelines.md`). A host without a reference file is not supported: say so, describe the steps in concept, and change nothing.
- **Stack**: find the markers in each file under `references/stacks/` and read only the matching one. No matching stack file: say so and stop.

### 2. Establish the definition of done

Take it from the project's agent guide or from the user. Use the commands as they run locally. If there is a locked variant (from `harness-reproducibility`), use that variant in CI. Check that each command passes locally (ask first where it uses the network, takes long, or writes files). If a command fails locally, say so, because CI will fail on it too. Do not add a command that has not been run.

### 3. If a pipeline already exists, review it first

Read it and report against this checklist, with evidence:

| Check | Why |
| --- | --- |
| Runs every command of the definition of done | CI that skips one of them proves less than the local run |
| Uses the locked install, and the lock files exist and are tracked | Otherwise the run can resolve different versions. A locked mode can exit with success when no lock file exists, which protects nothing (check the stack file) |
| No silent failure | A step that cannot fail adds nothing |
| Fails when no tests ran | An empty or fully skipped suite exits with success |
| Toolchain version comes from the project's pin | The runner's default version can drift |
| Runner version is fixed | A moving runner label changes under you |
| Permissions are minimal | Default tokens are often broader than needed |
| Third-party steps are pinned (first-party ones follow the pinning policy the user chose) | A moving tag can change what runs |
| Evidence is kept even on failure | The failure is when it matters |
| A time limit is set | A hung step should not run forever |

Propose a patch for the gaps, as a diff shown in the reply and not applied. Do not rewrite the file. Any action or task version the patch adds or changes is resolved the same way as in step 5.1, and the first-party pinning policy is asked once (see the host reference), so the patch never carries a remembered version.

### 4. Decide the scope with the user

Ask about the triggers (which branches, pull requests), whether to cancel superseded runs, the retention of artifacts, and whether the pipeline should also run the architecture guard or the import checker if they exist. Defaults are in the host reference.

### 5. Generate

Create the file from the host reference and the stack file:

1. Resolve the current version of every action or task you use, following the host reference. If you cannot resolve it (no network or no tool), say so and ask the user for the version. Do not guess.
2. Copy `scripts/assert_tests_ran.py` into the project (the host reference says where), unchanged, and wire it after the test step. It reads the test result files and fails when no test executed.
3. Keep the commands identical to the local ones, except where the stack file explains a CI variant (the locked install, results output).

Show the file and wait for approval before writing.

### 6. Validate

1. If the host has a linter, run it (the host reference names it). Fix every finding.
2. Run the commands of the pipeline locally in the same order, with permission. Report each exit status.
3. Check that the guard against empty test runs would fail: run it on an empty result file, or point to its own tests.
4. State what you could not validate: the real run on the host, the secrets or permissions the host needs, the branch protection that makes the check required.

### 7. Report

| Step | Command | Local result | Why it is there |
| --- | --- | --- | --- |

Then list: the file created or the patch proposed, the versions resolved and how, what was validated and what was not, the settings the user has to change on the host (for example requiring the check before merging), and the limits below.

## Known limits to state

- **A valid file is not a working pipeline.** Only a real run proves it.
- **CI does nothing unless it is required.** Making the check mandatory before merging is a host setting that this skill does not change.
- **Pinned versions age.** Pinned third-party steps need someone to update them.
- **Local and CI environments differ.** A command that passes locally can fail on the runner because of the operating system, the network, or the cache.
- **The count guard checks that tests ran, not that they are good.**

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. The steps, in order, with the locked variant and the results output
3. How the empty-run guard is fed (which result files)
4. Pitfalls and limits
5. Verified on (date, and what was not re-verified)

## What a host reference must contain

Each host file directly under `references/` follows this outline:

1. Detection markers and where the file lives
2. How to resolve current versions of actions or tasks
3. The skeleton: triggers, permissions, runner, limits, concurrency, evidence
4. Where the guard script goes and how it is called
5. The linter to run, or the statement that none was available
6. Pitfalls and limits
7. Verified on (date, and what was not re-verified)
