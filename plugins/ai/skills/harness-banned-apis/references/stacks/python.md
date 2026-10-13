# Python stack reference for harness-banned-apis

## 1. Detection markers

`pyproject.toml`, `ruff.toml`, `.ruff.toml`. Check which configuration file is in effect with `ruff check --show-settings <file>`: a `ruff.toml` in the same directory shadows the ruff table in `pyproject.toml`, and the two are not merged.

If the project does not use ruff, this pack does not apply. Say so and offer to describe the idea in concept. Do not add ruff for this alone without asking.

## 2. The mechanism

Ruff's banned-import rule (`TID251`, from the tidy imports family).

| Element | Detail |
| --- | --- |
| Rule | `TID251`. It must be selected for the check to run. |
| Entries | A table under the ruff lint settings, `flake8-tidy-imports.banned-api`, one key per forbidden module or member, each with a `msg` |
| Extending | `extend-banned-api` adds to an existing table instead of replacing it |
| Failure | A violation makes `ruff check` exit `1`, so it fails the lint command. No extra severity step is needed. |

## 3. Entry syntax

In `pyproject.toml`:

```toml
[tool.ruff.lint]
extend-select = ["TID251"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"datetime.datetime.utcnow".msg = "Use datetime.datetime.now(datetime.UTC)"
"typing.List".msg = "Use the built-in list"
```

In `ruff.toml` the same table is `[lint.flake8-tidy-imports.banned-api]`. Keys are fully qualified names of a module or a member.

## 4. Catalog of policies

| Policy | Entry | Relevant when |
| --- | --- | --- |
| No naive UTC timestamps | `datetime.datetime.utcnow` and `datetime.datetime.utcfromtimestamp`, message pointing to timezone-aware calls | The project targets a Python version where these are deprecated (3.12 and later) |

The rest comes from the user. Common project-specific cases are a legacy client library replaced by an internal one, a module that must go through a wrapper, or an unsafe function used by a framework.

## 5. Finding existing uses

After selecting the rule in a throwaway run, the lint output counts exact violations: `ruff check --select TID251 --output-format concise .` reports each one. Use that. Text search is only a fallback.

`--select` replaces the configured selection for that run. It is fine for counting, but it proves nothing about the project's own configuration (see section 7).

## 6. Gradual options

| Option | How | Cost |
| --- | --- | --- |
| Ignore legacy paths | `per-file-ignores` for `TID251` on the legacy directories | Protection applies only to the rest. The list must shrink over time. |
| Mark existing uses | `--add-noqa` for `TID251` | Writes suppression markers into source files. Ask first and record them as debt. |
| Ban only new modules | Keep the table small and add entries as the code is migrated | Slower adoption. |

## 7. Validating entries

Validate in two steps:

1. Run `ruff check --select TID251 --output-format concise .` and look for the `TID251` code at the use. This proves the entry is well formed.
2. Run the project's own command, `ruff check --output-format concise .`, without `--select`, and confirm the `TID251` code is reported there too. This proves the rule is selected in the configuration in effect. Also confirm with `ruff check --show-settings <file> | grep TID251`. `--select` overrides the configuration, so a populated table with the rule missing from `select` and `extend-select` passes step 1 and reports nothing in step 2. That silent step 2 (`All checks passed!`, exit `0`, and no `TID251` in `--show-settings`) is the sign that `extend-select = ["TID251"]` is missing.

If no existing use exists, create the one temporary file described in the skill with one use per unvalidated entry, then remove it.

## 8. Pitfalls and limits

- **Imports and member access are covered, other forms may not be.** Both an import of `typing.List` and a call to `datetime.datetime.utcnow()` were reported in the test. Aliased or dynamic access (`getattr`, a module imported under another name and passed around) may not be.
- **The rule must be selected.** A populated table does nothing if `TID251` is not in the active selection.
- **The configuration file in effect.** Entries in a shadowed file are silent.
- **Default rule set.** In the version tested, other rules (for example date-and-time and upgrade rules) were already active and can report the same line. Entries and existing rules can overlap.
- **Dynamic code and other packages** that call the forbidden member are not caught.

## 9. Verified on

2026-10-12, ruff documentation (the `banned-api` setting, `extend-banned-api`, and `TID251`), plus a throwaway run (ruff 0.17.0) in which `typing.List` (import) and `datetime.datetime.utcnow` (call) were both reported as `TID251` with their messages and the command exited `1`.

Re-run on 2026-10-12 (ruff 0.17.0): with the table filled and `TID251` absent from the selection, `ruff check --output-format concise .` printed "All checks passed!" with exit `0`, `--show-settings` had no `TID251`, and `ruff check --select TID251 .` reported the use (exit `1`); after adding `extend-select = ["TID251"]`, the project command reported it (exit `1`) and `--show-settings` listed the rule.

Not verified in this pass: `extend-banned-api` in practice, aliased imports, `--add-noqa` for this rule, and Python versions older than 3.12.
