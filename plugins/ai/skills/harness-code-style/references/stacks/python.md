# Python stack reference for harness-code-style

## 1. Detection markers

`pyproject.toml`, `ruff.toml`, `.ruff.toml`, `setup.cfg`, `.flake8`, `.pre-commit-config.yaml`, and tool names in dependencies (`black`, `isort`, `flake8`, `ruff`). Respect the tools the project already uses. This pack covers ruff in depth. If the project uses other formatters or linters, describe the idea in concept, configure only what you can verify, and say what you could not.

A `ruff.toml` (or `.ruff.toml`) in a directory shadows the ruff table in `pyproject.toml`, and the two are not merged. Check which one is in effect with `ruff check --show-settings <file>`.

## 2. Where style is configured

| Element | Role |
| --- | --- |
| Ruff formatter settings (line length, quote style) in the ruff table | Controls how `ruff format` writes code |
| Ruff lint rule selection (`select`, `extend-select`, `ignore`) | Controls which style rules fail the lint check |
| Editor settings file (`.editorconfig`) | Optional, for editors and for indentation and final-newline basics |

Read the rules in effect with `ruff check --show-settings <file>`. The default rule set depends on the ruff version, and in the version tested it already included some upgrade and date-and-time rules, so read it rather than assuming.

## 3. Style check commands

Run through the project's environment (`uv run`, `poetry run`, or the activated virtual environment). `uv run` and `poetry run` can create or sync the environment, so ask first, or use the tools on the PATH or in a `.venv` that already exists. `uv run --no-sync` is safe only when `.venv` exists: with none it still creates one in the repository. If ruff is not available, report the style check as **unknown** and ask before installing it.

| Purpose | Command | Reading the result |
| --- | --- | --- |
| Formatting check | `ruff format --check .` | Exit `0` when nothing would change, `1` when files would be reformatted. Does not modify files. |
| Style lint | `ruff check .` | Exit `0` no violations, `1` violations, `2` abnormal termination (for example invalid configuration). |
| Import order only | `ruff check --select I .` | Reports `I001` when imports are unsorted. |

## 4. Making a rule fail

A ruff lint violation already fails the lint command, so there is no extra severity step. A rule fails when it is **selected** and the command is not bypassed.

```toml
[tool.ruff.lint]
extend-select = ["I", "UP"]
```

Use `extend-select` to add families to what the project already selects. Replacing the existing `select` list with a shorter one silently turns rules off. Offer families one by one, such as import order (`I`), upgrade rules (`UP`), naming (`N`), and the basic pycodestyle families (`E`, `W`).

Then check that no script or CI step bypasses the command (`--exit-zero`, `|| true`, `continue-on-error`). Look in `.github/workflows`, `azure-pipelines.yml`, a `Makefile`, `tox.ini`, `noxfile.py`, `.pre-commit-config.yaml` and any `scripts` directory. If one bypasses it, report it and propose the fix as a previewed change that needs approval. `harness-sensors` explains the bypass problem in detail.

**Where the formatter check goes.** `ruff format --check .` is not a lint rule, so selecting rules never runs it. Add it as its own step to the project's verification command (the script, CI step or pre-commit hook that already runs `ruff check`), merged into what exists, and record its exit status next to the lint status.

## 5. Gradual options

| Option | How | Cost |
| --- | --- | --- |
| Ignore legacy paths | `per-file-ignores` for the style families on the legacy directories | Protection applies only to the rest. The list must shrink over time. |
| Mark existing violations | `ruff check --select <rule> --add-noqa .` | Writes suppression markers into source files. Ask first and record them as debt. |
| One family at a time | Add one family to the selection per step | Slower, but the cost of each family is visible. |
| Formatter check only on changed files | Run the check with the list of files changed in the branch | Needs a way to get that list in the project's workflow. Not tested here. |

## 6. Reformatting

`ruff format .` rewrites files, and `ruff check --fix` also rewrites files. Never run either as part of the check. First count the files with `ruff format --check .`, do the reformat as its own change, and tell the user that formatter output can change between ruff versions, so the version should be pinned.

## 7. Pitfalls and limits

- **`select` replaces and `extend-select` adds.** Editing the wrong one changes what is checked.
- **Style and lint overlap in ruff.** The same line can be reported by a style family and by a general rule. Do not count them twice when reporting drift.
- **Which tool wins.** If the project also runs another formatter, two formatters can undo each other's output. Ask which one is the authority.
- **Version drift.** Ruff's default rules and formatting can change between versions.
- **Monorepos** can have several configurations. Check each project.
- **Generated or vendored code** should be excluded through the project's existing exclusion settings. Do not edit those files.

## 8. Verified on

2026-10-12, run in throwaway samples (ruff 0.17.0): `ruff format --check` exited `1` for an unformatted file and `0` for a formatted one; selecting `I` reported `I001` for unsorted imports with exit `1`; selecting `UP` reported upgrade rules; `--show-settings` printed the configuration file in effect and the enabled rules; `ruff.toml` shadowed the `pyproject.toml` ruff table. Ruff documentation: exit codes for `ruff check`.

Re-run on 2026-10-12 with ruff 0.17.0 and uv 0.12.7: the formatter check as its own step (`ruff format --check .` exits `1` when files would change), `extend-select = ["I"]` next to an existing `select`, the `|| true` bypass, and `ruff.toml` shadowing the `pyproject.toml` table. `uv run --no-sync` creates `.venv` when none exists, so it is safe only with an existing `.venv`; the exit `0` case of the formatter check was not re-run.

Not verified in this pass: `--add-noqa`, conflicts between selected rules and the formatter, behavior with other formatters, and other ruff versions.
