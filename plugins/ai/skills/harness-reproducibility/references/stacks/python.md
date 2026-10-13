# Python stack reference for harness-reproducibility

## 1. Detection markers

`pyproject.toml`, `uv.lock`, `poetry.lock`, `Pipfile.lock`, `requirements*.txt`, `.python-version`, `.tool-versions`. The package manager decides the commands. Find out which one the project uses before proposing anything. This pack covers `uv` in depth (run and verified), `poetry` from its documentation only, and plain requirements files at a basic level.

## 2. Toolchain pin: the interpreter

| Element | Detail |
| --- | --- |
| Compatibility bound | `requires-python` in the `[project]` table of `pyproject.toml`. A lower bound, not an exact pin. |
| Exact pin for tools | `.python-version` at the repository root. With `uv`, `uv python pin` is meant to write it (not run in the tests; check its output). |
| Read the effective version | `python --version` (through the project's environment) |

The bound says what the code supports. The pin file says which version the tools use by default. Ask which one the user wants. Use the interpreter version that is in use today, not a newer one.

## 3. Dependency versions and lock: `uv`

| Purpose | Command | Reading the result |
| --- | --- | --- |
| Create or update the lock | `uv lock` | Writes `uv.lock`. Needs the network. Only on request. |
| **Locked check without changing anything** | `uv lock --check` | Exit `0` when the lock matches `pyproject.toml`, exit `1` when it is out of date. Exit `2` is an error such as an unparsable `uv.lock`, which is not a mismatch. It can need the network when the cache is cold, so ask first. With `--offline` or a cold cache, exit `1` can be a resolution failure ("network was disabled") and not a mismatch: read the message, because a mismatch says the lockfile needs to be updated. |
| **Locked install** | `uv sync --locked` | Exit `0` when in sync, exit `1` with a message that the lock needs updating when it is not. **It is not read-only**: it creates or updates the environment folder and installs packages, so it needs permission. For a pure check use `uv lock --check`. |
| Install without checking freshness | `uv sync --frozen` | Exit `0` even when the lock is out of date. **It does not verify anything.** Do not use it as a check. |

For projects without a build backend or package layout that `uv` can build, a sync can fail for reasons that are not about the lock. Separate the two when reading a failure.

`uv sync` without `--locked` can rewrite `uv.lock`. Never use it to verify.

## 4. Other managers (from documentation, not run)

- `poetry`: `poetry lock` creates the lock without installing, and `poetry install` uses the lock when present. `poetry check --lock` is documented as the consistency check (older versions: plain `poetry check`, or a warning on install). Confirm the installed version with `poetry --version` and read its help before relying on it. Do not use `poetry lock` or `poetry install` as a check: `poetry lock` rewrites the lock and `poetry install` writes the environment.
- Plain requirements files: pin exact versions (`==`), and record hashes if the project uses them. A requirements file with ranges floats. Do not generate a pinned file from an environment you do not control.

If the project uses a manager this pack does not cover, say so, and offer the concept only.

## 5. Checks that files are tracked and used

- `git ls-files uv.lock poetry.lock .python-version` lists what is tracked.
- `git check-ignore -v <file>` shows whether a rule ignores a file you expect to commit. Lock files are sometimes ignored by mistake.
- Look in CI and in the agent guide for the locked commands. An install without `--locked` (or the manager's equivalent) does not enforce the lock.

## 6. Pitfalls and limits

- **`--frozen` is not a check.** It installs from the lock whatever it says. If CI or a script uses `uv sync --frozen`, propose replacing it with `uv sync --locked`, preceded by `uv lock --check` when you also want a check that writes no environment. Show it as a proposal and wait for approval.
- **Different interpreter in CI.** A lock made on one interpreter can resolve differently under another. Pin the interpreter in CI.
- **Platform-specific dependencies.** Some packages differ by operating system. A lock may cover several platforms or only one, depending on the manager and settings.
- **Lock files hide fixes** until they are refreshed. Pair this with a dependency audit.
- **System libraries** that packages link against are outside the lock.
- **Do not run `uv lock --upgrade`** or any command that refreshes versions as part of this skill.

## 7. Verified on

2026-10-12, run in a throwaway sample (uv 0.12.7): `uv lock` created `uv.lock`; `uv lock --check` and `uv sync --locked` exited `0` when in sync and `1` after a dependency was added to `pyproject.toml` without re-locking; `uv sync --frozen` exited `0` in the out-of-sync state; `uv python pin` exists (its help ran), but the command itself was not run. Poetry from its documentation only (no run).

Re-run on 2026-10-12 (uv 0.12.7): `uv lock --check` exited `0` in sync and `1` on drift; with `--offline` and an empty cache the drift case exited `1` with a "network was disabled" resolution failure; an unparsable `uv.lock` exited `2`.

Not verified in this pass: `poetry check --lock` (poetry is not installed here), `poetry` commands in practice, requirements files with hashes, multi-platform lock behavior, and other `uv` versions.
