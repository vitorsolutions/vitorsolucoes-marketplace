# Python stack reference for harness-setup

## 1. Detection markers

`pyproject.toml`, `setup.cfg`, `setup.py`, `requirements*.txt`, `Pipfile`, `uv.lock`, `poetry.lock`, `.python-version`. Python projects have no build step, so the "verification command" is a set of tools (lint, type check, tests) that each fail through their own exit status.

## 2. Toolchain and read-only readouts

| Need | Command |
| --- | --- |
| Interpreter version | `python --version` (through the project's environment runner when there is one) |
| Linter present | `ruff --version` |
| Effective linter state | `ruff check --show-settings <file>`, which prints the configuration file in effect and the enabled rules |
| Type checker present | `mypy --version` |

Run tools without letting a runner change the project: use the tools on the PATH, or the tools of a virtual environment that already exists (`.venv`). `uv run --no-sync` is safe only when `.venv` already exists: with no `.venv` it still creates one in the repository (observed). Plain `uv run` and `poetry run` can create or sync the environment, which is a write and may use the network, so they need permission. Do not install anything. If a tool is missing, mark what depends on it **unknown**. An ephemeral run (`uv run --no-project --with ruff <command>`) touches neither the repository nor the system, but it downloads the tool, so use it only with the user's permission and say that the tool came from that run.

## 3. Signals by layer

| Layer | Signals that it exists | What makes it only partial |
| --- | --- | --- |
| Reproducible environment | A lock file (`uv.lock`, `poetry.lock`, `Pipfile.lock`) or pinned requirements; a pinned interpreter (`.python-version` or a `requires-python` bound); CI installs from the lock | Dependencies are unpinned ranges; the lock exists but CI installs without it |
| Checks that fail | A linter configuration with security and bug-finding rule families selected; a type checker with a strict setting; commands that are not wrapped in a bypass (`--exit-zero`, `|| true`, `continue-on-error`). Search for bypasses in CI files, `Makefile`, shell scripts such as `ci.sh`, `tox.ini`, `noxfile.py`, and `.pre-commit-config.yaml` | Tools configured but the commands in scripts or CI bypass failure; strict typing only on some modules |
| Style | A formatter configured (`[tool.ruff.format]` or the project's chosen formatter) and a format check (`ruff format --check .`) in scripts or CI | Formatter configured but no check runs in scripts or CI |
| Banned APIs | A banned-import configuration for the linter (in ruff, the `banned-api` setting under `flake8-tidy-imports`, rule `TID251`) with entries | The rule is not selected, or the table has no entries |
| Tests | A test runner configured (for example a `pytest` table or file) and a tests directory; a test command in scripts or CI | Tests exist but are not run in CI |
| Architecture rules | An import-contract tool configuration: `.importlinter`, `setup.cfg`, or a `[tool.importlinter]` table in `pyproject.toml`, with contracts, run by a command in scripts or CI | Configuration exists but no command runs it |
| Agent guide | `AGENTS.md`, `CLAUDE.md`, or tool-specific rule files | Commands in the file do not exist (read-only check), or fail (only when the user allowed running them) |
| Permissions | For Claude Code: a `permissions` entry in `.claude/settings.json` or `.claude/settings.local.json` | Only user-level settings exist, or broad allow lists with no deny rules for secrets or remote data |
| Hooks | For Claude Code: a `hooks` entry in `.claude/settings.json` or `.claude/settings.local.json` | Hooks exist but do not cover the definition of done or the protected files |
| CI | A pipeline definition in the host's usual place that runs the same lint, type, and test commands | The pipeline skips the checks, or marks them `continue-on-error` |
| Proof | A recorded probe result (the user can point to one) | Probe run before the last tool upgrade or configuration change. Compare the recorded probe date with `git log -1 --format=%cs -- pyproject.toml ruff.toml .ruff.toml uv.lock poetry.lock .python-version` |

## 4. Where to look for agent-specific files

For Claude Code: `.claude/settings.json` (shared with the team), `.claude/settings.local.json` (personal, not committed), and user-level settings in the user's home folder. For other agents, ask the user, and mark the layers unknown if they cannot say.

## 5. Pitfalls and limits

- `ruff.toml` or `.ruff.toml` in a directory shadows the ruff table in `pyproject.toml` there, and the two are not merged. Read the configuration the tool reports as in effect.
- Monorepos can have several projects with separate configurations. Assess each one.
- Python has no project reference graph, so the architecture layer depends entirely on an import-contract tool or is **missing**.
- The default rule set of the linter changes between versions. Read the enabled rules with the tool, do not assume them.
- The virtual environment folder is not part of the repository. Ignore it.

## 6. Verified on

2026-10-12: the ruff `banned-api` setting and `TID251` (ruff documentation), the import-linter configuration locations (`setup.cfg`, `.importlinter`, `pyproject.toml`) and its `lint-imports` command (import-linter documentation), and the `--show-settings` output and `ruff.toml` precedence (run against a throwaway sample with ruff 0.17.0).

Not verified in this pass: signals for formatters other than ruff, lock-file semantics of `uv` and `poetry` as CI inputs, and pipeline file locations.

Re-run on 2026-10-12 with ruff 0.17.0, mypy 2.4.0 and uv 0.12.7: `uv run --no-sync` creates `.venv` when none exists and does not when it exists; `uv run --no-project` creates nothing. The bypass search locations and the staleness command in the Proof row were not exercised in that run.
