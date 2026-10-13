# Python stack reference for harness-hooks

## 1. Detection markers

`pyproject.toml`, `ruff.toml`, `.ruff.toml`, `mypy.ini`, `setup.cfg`, `uv.lock`, `poetry.lock`, `.python-version`. Source files are `.py`.

## 2. Candidate definition-of-done commands

Each command is a program and an argument list. Run them through the project's environment runner when it has one (for example `uv run ruff check .` is the program `uv` with the arguments `run`, `ruff`, `check`, `.`). Only list tools that the project already uses, and only commands that were run and exited `0`.

| Name | Program and arguments | Notes |
| --- | --- | --- |
| lint | `ruff check .` | Exit `0` no violations, `1` violations, `2` abnormal termination. |
| format | `ruff format --check .` | Exit `1` when files would be reformatted. Never use the version without `--check`: it rewrites files. |
| types | `mypy <package-dir>` | Exit `0` no errors, non-zero otherwise. |
| tests | `pytest` | Exit `0` pass, `1` failures, `5` nothing collected. Exits `0` when every test is skipped. Pair it with `harness-test-baseline`. |

If a script already wraps these commands with a bypass such as `--exit-zero` or `|| true`, do not call that script. Call the tools directly.

## 3. Suppression markers

| Pattern (in the configuration, with doubled backslashes) | File globs | Label |
| --- | --- | --- |
| `#\s*noqa\b` | `*.py` | noqa |
| `#\s*ruff:\s*noqa` | `*.py` | file-level ruff noqa |
| `#\s*type:\s*ignore` | `*.py` | type: ignore |
| `ignore_errors\s*=\s*true` | `pyproject.toml`, `mypy.ini`, `setup.cfg` | mypy ignore_errors |
| `per-file-ignores` | `pyproject.toml`, `ruff.toml`, `.ruff.toml` | ruff per-file-ignores |

The `noqa` pattern also matches the file-level form, so the second row is a more specific label for the same text. Keep both only if the distinction matters to the user.

Ignore paths: generated or vendored code, for example `*/migrations/*`, `*/_vendor/*`, `*/build/*`. Ask the user. Framework migration tools write files that can contain markers.

## 4. Commands that act on remote systems or shared data

Patterns match anywhere in the command text. Use what the project actually has. Common candidates:

| Pattern | Suggested | Reason to show |
| --- | --- | --- |
| `alembic\s+(upgrade\|downgrade)` | ask | Changes a database schema. Safe only against a local, disposable one. |
| `manage\.py\s+(migrate\|flush)` | ask | Changes or empties a database. |
| `twine\s+upload` | deny | Publishes a package. |
| `uv\s+publish` | deny | Publishes a package. |
| `pip\s+install\|uv\s+(add\|pip\s+install)` | ask | Changes the environment and the dependency set. |

(Vertical bars separate alternatives. The backslash before a bar in the tables is only markdown table escaping: write a plain `|` in the configuration and do not copy the backslash.)

Add the project's own deploy and release scripts by name.

## 5. Pitfalls and limits

- A pattern matches text, not intent.
- The suppression guard sees the text an edit adds. A suppression written by a shell command, or by a tool such as a formatter's `--add-noqa` option, is only caught by the stop guard's diff scan.
- A configuration file such as `pyproject.toml` can legitimately mention these words in comments or unrelated settings. Review the matches before treating them as errors, and narrow the globs if needed.
- Do not call a command through a wrapper script that hides the tool's exit status.
- Running tools needs the project's environment. If a tool is missing, the stop guard reports it could not run the command, and that blocks. Decide with the user whether a missing tool should block or be left out of the list.

## 6. Verified on

2026-10-12: the command exit statuses (`ruff check` `0` and `1`, `ruff format --check` `0` and `1`, `mypy` `1` with errors, `pytest` `0`, `1`, `5` and `0` for all-skipped) were observed in throwaway samples (ruff 0.17.0). The hook script and its patterns were tested with sample events in the script's test suite, using the `#pragma` and `noqa` patterns. The suppression and command guards were run through the real agent (see the agent reference).

Each pattern listed in sections 3 and 4 (except `per-file-ignores`, which is plain text) was also checked against one line that should match and one that should not.

Not verified in this pass: the `type: ignore`, `ignore_errors` and `per-file-ignores` patterns against real configuration files, migration tool patterns (named from common usage), and runs through `uv run` or `poetry run`.
