# Python stack reference for harness-sensors

Python has no build step. The verification command is a set of separate tools (a linter and a type checker), and each one fails through its own exit status. A control only works if the command that runs it is part of what the agent and CI actually execute.

## 1. Detection markers

| File | Meaning |
| --- | --- |
| `pyproject.toml` | Main configuration. Check for `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`. |
| `ruff.toml`, `.ruff.toml` | Ruff configuration. Takes precedence over `pyproject.toml` in the same directory. |
| `mypy.ini`, `setup.cfg`, `pyrightconfig.json` | Type checker configuration. |
| `uv.lock`, `poetry.lock`, `Pipfile.lock`, `requirements*.txt` | Which package manager the project uses. Run tools through it (`uv run`, `poetry run`, or the active virtual environment). |
| `.python-version`, `.tool-versions` | Pinned interpreter version. Never change it. |

Respect the tools the project already chose. If ruff or mypy is not installed, mark the controls that depend on it **unknown** and ask before installing. If it uses a type checker other than mypy, configure that one and do not add a second.

## 2. Canonical commands

| Purpose | Command |
| --- | --- |
| Interpreter version | `python --version` |
| Linter present | `ruff --version` |
| Effective linter state | `ruff check --show-settings <file>` prints the configuration file it resolved ("Settings path") and the list of enabled rules for that file |
| Verification: lint | `ruff check .` exits `0` with no violations, `1` with violations, `2` on abnormal termination such as invalid configuration |
| Verification: types | `mypy .` exits `0` with no errors and non-zero when errors are found |

Run the tools without letting a runner change the project: the tools on the PATH, or those of a `.venv` that already exists. `uv run --no-sync` is safe only when `.venv` exists, because with no `.venv` it still creates one in the repository. Plain `uv run` and `poetry run` can create or sync the environment, which needs permission. When the tools are not installed, an ephemeral run (`uv run --no-project --with ruff --with mypy <command>`) creates nothing in the repository, but it downloads the tools, so use it only with the user's permission and say that the result came from that run. Never install the tools globally and never add a dependency without asking.

Counting diagnostics: use the rule code printed by the tool (for example `S608`, `B006`, or a mypy error code), not the message text. Run mypy with `--show-error-codes` so the codes are always printed, and count distinct occurrences by file, line and code, for example `mypy --show-error-codes . | grep -oE '\[[a-z-]+\]$' | sort | uniq -c`.

## 3. Controls

| Control | Mechanism | Read effective state | Enable | Fails the command? |
| --- | --- | --- | --- | --- |
| Security rules | Ruff rule families that follow the Bandit rules (prefix `S`) | `ruff check --show-settings` | Add the family to `extend-select` (or to the existing `select` list) under `[tool.ruff.lint]` in `pyproject.toml`. The top-level `[tool.ruff]` form still works but prints a deprecation warning | Yes, a violation makes `ruff check` exit `1` |
| Correctness rules | Ruff families such as `B` (likely bugs) and `F` (undefined names, unused imports) | Same | Same | Yes |
| Strict type checking | `strict = true` in `[tool.mypy]` (or the existing checker's strict mode) | Read `[tool.mypy]` and any `[[tool.mypy.overrides]]` | Set `strict = true`, then handle legacy modules with overrides | Yes, errors make `mypy` exit non-zero |
| Failure on lint violations | `ruff check` exit status | Look at every place the command is run (CI definitions such as `.github/workflows` and `azure-pipelines.yml`, shell scripts such as `ci.sh`, `Makefile`, `tox.ini`, `noxfile.py`, `.pre-commit-config.yaml`, hooks) for `--exit-zero`, `|| true`, or `continue-on-error` | Remove the bypass, or report it and ask | Yes, if no bypass exists |
| Dependency vulnerability audit | A package audit tool such as `pip-audit` (not re-verified) | Check whether it is configured | Requires network access and usually a new dev dependency. Ask first. If the user declines, report "not run" | Yes, when it finds advisories |

Select rules by family rather than turning everything on. Do not assume what the default rule set contains, because it changes between versions: read the enabled-rule list with `--show-settings`. In the version tested (see section 7), the defaults already included several `B` and `F` rules and a few `S` rules, plus rules from other families (for example `I001`, `UP031` and `PLR0133`), but not the SQL-injection rule (`S608`) or the weak-hash rule (`S324`), which only appeared after the `S` family was added to the selection. Count the baseline by rule code and do not assume it only holds security and bug families.

## 4. Gradual adoption

Use when the baseline already has violations.

| Mechanism | How | Cost |
| --- | --- | --- |
| Ignore legacy paths for a rule | `per-file-ignores` in the ruff table, scoped to the legacy directories | Protection applies only to the rest of the code. The list must be shrunk over time. |
| Mark existing violations | `ruff check --select <rule> --add-noqa .` adds a `noqa` marker to every current violation of that rule, so only new violations fail | **This writes suppression markers into source files.** Show the planned diff size and get explicit approval first. Record that these markers are debt. |
| Type checking per module | Keep the global setting strict and add `[[tool.mypy.overrides]]` entries with `ignore_errors = true` for legacy modules, or enable strictness first for modules that are already clean | Same as above: the list of exempt modules is debt to be shrunk. |
| Rules by family, one at a time | Add one family to the selection per step | Slower, but the user sees each family's cost. |

Never run any autofix (`--fix`) as part of this skill. Do not use `# type: ignore` comments as a gradual mechanism: use per-module overrides, and ask before adding them.

## 5. Pitfalls

- **Configuration precedence.** A `ruff.toml` or `.ruff.toml` in the same directory takes precedence over `pyproject.toml`, and the two are not merged: when a `ruff.toml` exists, the ruff table in `pyproject.toml` is ignored. Edit the file that "Settings path" reports. Nested configurations apply to their subtree, so check for several files before editing.
- **`select` replaces, `extend-select` adds.** Replacing the project's `select` list with a shorter one silently turns rules off. Edit the existing list or use `extend-select`.
- **The security family flags `assert` in tests (`S101`).** Selecting the family in a project that tests with plain `assert` statements (pytest) makes the lint fail on every test file. Add a `per-file-ignores` entry for `S101` scoped to the tests folder, and tell the user it is a deliberate exception. Observed in a sample project with pytest.
- **The type checker only sees annotated code.** Unannotated functions are not checked unless strict mode requires annotations.
- **Merge into `pyproject.toml`.** Add tables and keys. Never replace the file, and keep existing comments and ordering.
- **Wrong environment.** Running a tool from a different environment than the project's can give different results or fail on missing stubs.
- **A bypass in another place.** The lint command may already exist in CI with `|| true`. Configuration in `pyproject.toml` does not help if the command never fails.
- **Interpreter version.** Some options depend on the interpreter or tool version. State the versions found in the report.

## 6. Limits

- Pattern-based security rules do not follow data flow between functions.
- Rules do not know business logic or the intended dependency direction between packages.
- These suppressions silence the controls above: `# noqa`, `# type: ignore`, per-file ignores, and `ignore_errors` overrides.

## 7. Verified on

2026-10-12, against the Ruff documentation (exit codes and their flags, `per-file-ignores`, `--add-noqa`, `--select`) and the mypy documentation (`--strict`, `strict` in the configuration file, per-module overrides, guidance for existing codebases).

Also run in a throwaway sample project with ruff 0.17.0, mypy installed from the latest release at the time, and Python 3.14: `ruff check` exit `1` with violations, the `--exit-zero` bypass returning `0`, `--show-settings` output, `ruff.toml` shadowing `pyproject.toml`, the `S` family adding `S608` and `S324`, and `strict = true` making mypy exit `1` with bracketed error codes.

Not verified in this pass: `--add-noqa` behavior in practice (taken from the documentation only), the `pip-audit` tool, a pyright-based setup, and mypy exit statuses other than zero and one.

Re-run on 2026-10-12 with ruff 0.17.0, mypy 2.4.0 and uv 0.12.7 (the first pass ran without the tools): the `uv run --no-sync` behavior (it creates `.venv` when none exists), the top-level `[tool.ruff]` `extend-select` deprecation warning, the defaults that include `I001`, `UP031` and `PLR0133`, the `uv run --no-project --with` ephemeral route, and, in an earlier eval re-run, the mypy counting command, `[[tool.mypy.overrides]]` with `ignore_errors`, and the `S101` finding on pytest asserts.

Not re-run: `--add-noqa`, `pip-audit`, pyright, and the extra bypass search locations.
