---
name: harness-reproducibility
description: >-
  Makes a repository resolve the same toolchain and the same dependency versions on every
  machine, in CI and in every agent session, so a result does not depend on who ran it or when.
  Detects the stack, finds what is pinned and what floats (toolchain version, direct and
  transitive dependencies, lock files, central version management), checks whether the lock files
  are really committed and used by CI, then adds the missing pins in small steps and verifies
  them with read-only commands that cannot rewrite a lock. Currently supports .NET and Python.
  Use when the user asks to "pin the SDK version", "add lock files", "make builds reproducible",
  "fix works-on-my-machine", "centralize package versions", "garantir as mesmas versões em todo
  lugar", "travar dependências", "fixar a versão do SDK ou do Python", or wants agent runs and CI
  to use the same versions as developers. Do NOT use it to audit dependencies for
  vulnerabilities, to upgrade packages, or to configure CI itself (harness-ci-pipeline).
---

# Harness reproducibility

## What this skill does

If the toolchain or a dependency can change between two runs, a check that passed yesterday can fail today with no code change, and an agent's result can differ from a developer's. This skill finds what floats and pins it, so a result means the same thing everywhere.

Vocabulary:

- **Toolchain pin**: the file or setting that fixes the language runtime or SDK version.
- **Lock file**: a generated file that records the exact versions of all dependencies, including transitive ones.
- **Locked verification**: a command that fails if the lock file does not match the project, without changing the lock file.
- **Floating**: allowed to change without any change in the repository.

## Hard rules

- Never upgrade or downgrade a dependency or toolchain version to make a pin pass. Pin what is resolved today, and report differences.
- Never run a command that can rewrite a lock file as a way to check it. Use the locked verification commands in the pack.
- Never change what a lock file contains unless the user asked to create or regenerate it.
- Merge into existing files. Never overwrite or reorder them.
- Ask before any command that needs the network, installs packages, writes lock files, or creates an environment. That includes locked verification commands: they can hit the network when the cache is cold, and some create an environment folder. Say which of them the pack marks as writing.
- Never commit, push, or stage files.
- Report versions only from real command output.

## Workflow

### 1. Detect the stack

Find the markers in each stack reference under `references/stacks/` and read every matching pack (a repository with .NET and Python gets both, and each stack is measured separately). No matching pack: say the stack is not supported yet, explain the layers in concept, and change nothing.

### 2. Measure what is pinned

For each of the three layers below, record what exists, from files and read-only commands:

1. **Toolchain**: is the runtime or SDK version fixed, and how loosely (exact, or any later version)?
2. **Direct dependencies**: are versions declared in one place or scattered, and are they ranges or exact?
3. **Full dependency set**: is there a lock file for all dependencies including transitive ones, and is it committed?

Also check:

- That the lock files are tracked by git and not ignored (`git ls-files`, `git check-ignore`, and `git ls-files --others --ignored --exclude-standard` to find lock files that exist on disk but are ignored, because `git ls-files` alone lists only tracked files).
- Whether CI or the agent's standard commands use the locked verification, or install without it.

Classify each layer as **pinned**, **partial**, **floating**, or **unknown**, with evidence.

### 3. Propose options per gap

For each gap, give options and trade-offs. Examples of the kind of trade-off to state:

- A strict toolchain pin gives identical builds but needs a deliberate update when the version changes. A looser pin allows newer patches automatically.
- Centralizing dependency versions needs reconciling projects that use different versions of the same package. That can change what a project resolves, so build and test afterwards.
- A lock file makes installs repeatable but needs someone to update it on purpose, and it can hide security fixes until it is refreshed.

Ask the user which option to use.

### 4. Present the plan, then apply

Show each file to create or change, the exact content, and the expected effect. Wait for confirmation. Apply one layer at a time.

After each layer, run the pack's verification (with permission where it needs the network). If the change altered what resolves, build and test and report.

### 5. Verify with read-only commands

Use only locked verification commands from the pack. They must not rewrite lock files. Record the exit statuses.

Say which failure paths you did not exercise. An exit status other than the documented mismatch status (for example a parse error) is an error to read, not a mismatch. For example, confirming that a mismatched lock fails requires changing a dependency, and you must not do that to the real project without the user asking. You can offer to try it in a throwaway copy.

### 6. Report

| Layer | Before | After | Verified how |
| --- | --- | --- | --- |

Then list what changed (files), what did not and why, versions that now resolve (from real output), failure paths not exercised, and the limits below. State the locked verification command that CI and agents should use, and list every failure path you did not exercise (at least the mismatch path).

## Known limits to state

- A lock file is only as good as the habit of updating it. It can hide a vulnerability fix until someone refreshes it.
- A pin does not fix a vulnerable version. Use a dependency audit for that.
- Pins cover what the project declares. Operating system packages, container base images and external services float unless handled separately.
- Developers can still bypass a pin locally. CI and the agent's commands must use the locked verification.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. Toolchain pin: mechanism, options, how to read the effective version
3. Dependency version management: mechanism and how to adopt it
4. Lock files: mechanism, how to create them, locked verification commands and their exit statuses
5. Checks that files are tracked and used
6. Pitfalls and limits
7. Verified on (date, and what was not re-verified)
