# Python stack reference for harness-architecture-guard

## 1. Detection markers

`pyproject.toml`, a package directory with `__init__.py`, optionally a `src` layout. A guard needs a top-level package that contains at least two sub-packages with a dependency direction, or a package that must stay free of a library.

If the project already has import-contract configuration (`.importlinter`, or an import-linter table in `pyproject.toml` or `setup.cfg`), read it first and extend it rather than replacing it.

## 2. Reading the structure

Python has no project reference graph. Read it from the code:

| Need | How |
| --- | --- |
| Modules | The top-level package and its sub-packages (directories with `__init__.py`) |
| Dependencies between them | The import statements. The guard tool builds the graph, so in check mode a contract run reports what breaks |
| Libraries used | The project's declared dependencies and the imports found in the code |

Ask the user for the intended direction. Do not infer layers from directory names.

## 3. The guard tool

`import-linter` (a PyPI package, installed command `lint-imports`) builds the import graph of a root package and checks contracts against it. Add it as a development dependency with the project's package manager, and only after asking. If the project already uses it, nothing to install. With uv: `uv add --dev import-linter` (it worked in an evaluation run, and it changes `pyproject.toml` and the lock file, so it needs approval). Read the version it resolves.

Configuration location: `pyproject.toml` (a `[tool.importlinter]` table), `.importlinter`, or `setup.cfg`. The command looks in the current directory.

## 4. The guard template

In `pyproject.toml`, merged into the existing file:

```toml
[tool.importlinter]
root_package = "<root>"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Layers: infra -> app -> domain"
type = "layers"
layers = ["<root>.infra", "<root>.app", "<root>.domain"]

[[tool.importlinter.contracts]]
name = "Domain must not use the network libraries"
type = "forbidden"
source_modules = ["<root>.domain"]
forbidden_modules = ["urllib", "http"]
allow_indirect_imports = true
```

Observed semantics:

- **`layers`**: listed from the outermost to the innermost. A lower layer must not import a higher one. The sample's broken contract named the offending import and its line.
- **`forbidden`**: the source modules must not import the forbidden modules. A standard-library module (`urllib`) was detected.
- **`include_external_packages = true`** is required when any forbidden module is outside the root package. Without it the tool stops with a message saying so.
- **`allow_indirect_imports = true`** limits the check to direct imports. Leave it out to also forbid transitive imports, and tell the user what that changes.
- Check how contracts treat imports used only for type checking (the tool has an option for it) and ask the user which behavior they want.

### Existence check for external modules

A short script, run next to the contracts, fails when a forbidden external module cannot be found in the environment:

```python
import importlib.util, sys
missing = [m for m in sys.argv[1:] if importlib.util.find_spec(m.split(".")[0]) is None]
print("missing:", missing)
sys.exit(1 if missing else 0)
```

Call it with the forbidden external names. In the sample, `urlib htp` exited `1` and `urllib http` exited `0`. It only finds modules installed in that environment, so a library that is forbidden precisely because it is not a dependency makes it fail, and for those use the planted proof. Ask which network libraries the project really uses (section 2) before choosing the list: `urllib` and `http` do not cover `requests`, `httpx`, `aiohttp` or `socket`.

Adding the tool with `uv add --dev import-linter` changes `pyproject.toml` and `uv.lock`, creates `.venv`, and a run creates `.import_linter_cache`. List these as new or changed files in the report, and suggest adding `.import_linter_cache` to `.gitignore` instead of doing it.

## 5. Gradual adoption

Existing breaches go into the contract's `ignore_imports` list, written as `"<importer module> -> <imported module>"`:

```toml
ignore_imports = ["<root>.domain.leak -> <root>.infra.repo"]
```

The sample showed that the listed import was ignored (the report said "1 ignored import") and that a **new** violation of the same contract still failed with its own line. It also showed that a listed import that no longer exists **fails the run** (`No matches for ignored import <importer> -> <imported>.`, exit `1`), so, as with the .NET template, the list can only shrink: when a breach is fixed, its entry must be removed in the same change. Tell the user.

## 6. Command and result

Run through the project's environment: `lint-imports`, or `uv run --no-sync lint-imports` when the project uses uv, so the run does not resolve or install anything (verified with the tool already installed in the environment; `--no-sync` still creates `.venv` when none exists, so use it only when `.venv` is there). A plain `uv run` may sync the environment, so ask first. Exit `0` when every contract is kept and non-zero when one is broken. The report ends with `Contracts: <n> kept, <m> broken.`. A broken contract lists the importer, the imported module and the line. Read the exit status and the count line, and check that the number of contracts equals the number written.

## 7. Planting a violation in a copy

1. Copy the repository to a temporary directory, without the virtual environment, caches, and `.git`.
2. In the copy, add a new module in the inner package that imports from the outer one (or imports the forbidden library).
3. Run `lint-imports` in the copy. Expect a non-zero exit, and the broken contract naming the new module and the import.
4. Delete the copy.

In the sample, a new module in the domain that imported the infrastructure broke the layers contract (exit `1`) and one that imported `urllib.request` broke the forbidden contract.

## 8. Pitfalls and limits

- **A contract on a module of the project that does not exist fails** (the tool reports `Module '<name>' does not exist.` and exits `1`). That is stricter than the .NET tool for the project's own modules, and it means a renamed package breaks the guard on purpose.
- **A misspelled external module passes silently.** With `forbidden_modules = ["urlib", "htp"]` the run reported `1 kept, 0 broken` and exited `0`. For every forbidden module outside the project, add the existence check below, or prove the contract with a planted import (section 7), which is the only proof that the name is right.
- **Only import statements are seen.** Dynamic imports, `importlib`, plugin loading and string-based wiring are invisible.
- **The root package must be importable** by the tool from the project's environment. If it is not, the run fails before checking anything.
- **Several root packages** (monorepos) need separate configuration. This was not verified.
- **External packages** are only considered when the option in section 4 is set.
- The configuration can be edited or deleted by the agent. Protect it with permission rules.

## 9. Verified on

2026-10-12, run in throwaway samples (import-linter from the latest release at the time, Python 3.14): the clean run exited `0` with `2 kept, 0 broken`; a new domain module importing infrastructure broke the layers contract (exit `1`, showing the import and line); a domain module importing `urllib.request` broke the forbidden contract; the missing-option message for external modules; a contract on a missing module exiting `1`; and the `ignore_imports` behavior in section 5 (an ignored import is skipped, a new violation still fails, and an entry that matches nothing fails the run). Import Linter documentation: configuration locations and the `lint-imports` command.

Also verified on the same date: a contract with misspelled external modules passed with exit `0`, the `find_spec` check in section 4 caught it, and `uv run --no-sync lint-imports` ran against an existing environment.

Not verified in this pass: the `independence` contract type, several root packages, the type-checking-imports option, a `src` layout, `poetry run`, plain `uv run` (which can sync), and other versions of the tool.
