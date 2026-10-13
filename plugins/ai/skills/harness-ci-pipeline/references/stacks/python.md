# Python stack reference for harness-ci-pipeline

## 1. Detection markers

`pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `.python-version`. The package manager decides the install step. This pack covers `uv` in depth. For other managers, describe the steps in concept and say they were not verified.

## 2. Steps, in order

Commands run through the project's environment runner, as they do locally.

| Step | Command | Notes |
| --- | --- | --- |
| Toolchain | The host's setup step for the package manager (and the interpreter, if the project pins one) | With `uv`, the interpreter comes from the project's pin. A project with no pin should get one (see `harness-reproducibility`). |
| Install | `uv sync --locked` | Fails when `uv.lock` does not match `pyproject.toml`. Never use the frozen variant: it does not check the lock. |
| Lint | `uv run ruff check .` | Never add `--exit-zero` or `\|\| true`. |
| Format | `uv run ruff format --check .` | Only if the project uses the formatter. |
| Types | `uv run mypy <package>` | Only if the project uses the type checker. |
| Test | `uv run pytest --junitxml=<results folder>/junit.xml` | Writes the structured results that the count guard reads. |
| Guard | `python3 <path>/assert_tests_ran.py <results folder>` | Fails when no test executed, including when every test was skipped. |
| Architecture | `uv run lint-imports` | Only if the project has import contracts (see `harness-architecture-guard`). |

A step order that puts the cheap checks first (lint, format, types) gives faster feedback before the tests run.

## 3. Feeding the count guard

The guard reads `*.xml` JUnit files found in the folder. An XML file there that is not a JUnit result (a coverage report, for example) is listed and skipped, and `--glob "junit*.xml"` restricts the search by file name. It counts each test case that has no skipped marker. In the sample, a one-test run read `executed 1 of 1`, and a file whose only test was skipped read `executed 0 of 1` and failed. A run that stopped on a collection error still wrote a file, so the guard alone cannot replace the test step failing: both stay in the pipeline.

## 4. Pitfalls and limits

- **Dependencies for the checks.** The tools (`ruff`, `mypy`, `pytest`) must be in the project's lock, in a development group. If they are not, the install step passes and the run fails at the first tool.
- **The security family of lint rules flags `assert` in tests.** Projects that select it need a per-file exception for the tests folder, or lint fails in CI as it does locally.
- **The tests may not find the package** when it is not installed or the path is not configured. In the sample, a missing `pythonpath` made every test fail at collection.
- **Network.** Installing needs the package index. Ask about private indexes and their credentials, which belong in host secrets and not in the file.
- **Interpreter differences.** A lock made on one interpreter version can resolve differently under another. Pin the interpreter.
- **Plain requirements files and `poetry`** need different commands. They were not verified.

## 5. Verified on

2026-10-12, in a throwaway sample (uv 0.12.7, ruff 0.17.0, mypy and pytest from the latest releases at the time): with the sample's configuration fixed, `uv sync --locked`, lint, format check, type check and tests all exited `0`; the count guard read the real JUnit file; lint failed on `assert` in tests until a per-file exception was added; and tests failed at collection until `pythonpath` was set. The workflow around the commands passed `actionlint` (see the GitHub Actions reference).

Not verified in this pass: a real run on a hosted runner, `poetry` and requirements-file projects, private package indexes, and the architecture step inside a workflow.
