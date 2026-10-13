# Python stack reference for harness-agent-guide

## 1. Detection markers

| File | Meaning |
| --- | --- |
| `pyproject.toml` | Main configuration. Read `[project]` for name, interpreter requirement, and dependencies. Read tool tables for ruff, mypy, and pytest. |
| `uv.lock`, `poetry.lock`, `Pipfile.lock`, `requirements*.txt` | Which package manager the project uses. Commands in the guide must run through it. |
| `.python-version`, `.tool-versions` | Pinned interpreter. Mention it in the guide only if it is pinned. |
| `ruff.toml`, `.ruff.toml`, `mypy.ini`, `setup.cfg`, `pytest.ini`, `tox.ini` | Tool configuration. |

## 2. Structure and dependency direction

| Need | How | Notes |
| --- | --- | --- |
| Packages and layout | List the top-level directories that contain `__init__.py`, and check for a `src` layout | Report the layout the project actually uses. |
| Dependency direction | Not available from the project files | Python has no project reference graph. The guide states a direction rule only if the user gives one. Mention `harness-architecture-guard` as the way to enforce it. |
| Entry points | `[project.scripts]` and the application entry module | Include only if it is not obvious. |

## 3. Candidate verification commands

Run every command through the project's environment runner (`uv run`, `poetry run`, or the activated virtual environment), and write the guide's commands the same way. `uv run` and `poetry run` can create or sync the environment, which is a network and write operation, so ask first. To only use what is already installed, use the tools on the PATH or in a `.venv` that already exists. `uv run --no-sync` is safe only when `.venv` exists: with none it still creates one in the repository (observed). An ephemeral run (`uv run --no-project --with ruff --with mypy <command>`) creates nothing in the repository but downloads the tools, so use it only with the user's permission, and only to record an exit status. The guide keeps the project's own runner form (`uv run <tool>`), and the report says how each command was verified.

| Purpose | Command | Reading the result |
| --- | --- | --- |
| Lint | `ruff check .` | Exit `0` no violations, `1` violations, `2` abnormal termination. |
| Format check | `ruff format --check .` | Exit `0` when nothing would change, `1` when files would be reformatted. |
| Types | `mypy .` (or the project's configured type checker) | Exit `0` no errors, non-zero otherwise. |
| Tests | `pytest` (or the project's runner) | Exit `0` all passed. |

Rules for listing them:

- Only list tools the project already uses. Do not add a tool to the guide that is not configured.
- If a script or CI job runs a command with `--exit-zero`, `|| true`, or `continue-on-error`, the guide must not present that command as a gate. Report the bypass and point to `harness-sensors`.
- Some of these commands may need dependencies that are not installed. Do not install anything without asking. If a tool is missing, report it as "not run".
- A format check that exits `1` is a failing command like any other: report it as failing, ask whether to list it with a "baseline is red" note, and do not reformat the code.

## 4. Suppression mechanisms

Search the source and configuration for the ones that apply:

- `# noqa` (line level) and `# ruff: noqa` (file level).
- `# type: ignore` and `ignore_errors = true` in per-module type checker overrides.
- `per-file-ignores` entries in the ruff configuration.
- Rules removed from the selection or added to an ignore list.

## 5. Configuration files that define the checks

`pyproject.toml` (ruff, mypy, and pytest tables), `ruff.toml`, `.ruff.toml`, `mypy.ini`, `setup.cfg`, `tox.ini`, `.python-version`, lock files.

## 6. Commands that act on remote systems or shared data

These depend on what the project uses. Look for the migration and release tooling in dependencies and scripts, and list what is present. Common examples:

- Database migration runners applying migrations (for example `alembic upgrade`, or a framework's `migrate` command).
- Package publishing commands (for example `twine upload` or `uv publish`).
- Any deploy script the project defines.

Ask where credentials live (environment files, secret managers, CI variables) so the credentials restriction names the real places.

## 7. Pitfalls and limits

- A virtual environment folder is not part of the repository's structure. Leave it out.
- `ruff.toml` shadows the ruff table in `pyproject.toml`. When both exist, say which one is in effect. Use `ruff check --show-settings <file>` to read it.
- A monorepo can have several projects with separate configurations. Describe each one.
- The guide must not claim a type checker is strict unless its configuration says so.

## 8. Verified on

2026-10-12. The `ruff check` exit statuses, the `--show-settings` output, and `ruff format --check` (exit `1` on an unformatted file, `0` on a clean one) were run against a throwaway sample (ruff 0.17.0). The `mypy` exit behavior was run on the same sample.

Re-run on 2026-10-12 with ruff 0.17.0, mypy 2.4.0 and uv 0.12.7: `uv run --no-sync` creates `.venv` when none exists (so it is not a safe read-only form), and `uv run --no-project --with` creates nothing in the repository.

Not verified in this pass: `pytest` exit behavior, `poetry run`, and the migration and publishing commands listed in section 6 (named from common usage).
