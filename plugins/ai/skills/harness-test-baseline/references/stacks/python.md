# Python stack reference for harness-test-baseline

## 1. Detection markers

`pyproject.toml` (a `[tool.pytest.ini_options]` table), `pytest.ini`, `tox.ini`, `setup.cfg`, a `tests` directory, `conftest.py`, files named `test_*.py` or `*_test.py`. Follow the runner the project already uses. This pack covers `pytest`. If the project uses another runner, describe the idea in concept and configure only what you can verify.

Run through the project's environment (`uv run`, `poetry run`, or the activated virtual environment). `uv run` and `poetry run` can create or sync the environment, which installs packages and may use the network, so ask first, or use the tools on the PATH or in a `.venv` that already exists. `uv run --no-sync` is safe only when `.venv` exists: with none it still creates one in the repository. Do not install pytest without asking.

A cheap check that pytest is present is `python -m pytest --version` (exit `1` and "No module named pytest" when it is missing, verified). If it is missing, classify the suite **not runnable** and say so.

## 2. The test command

`pytest` (with the arguments the project uses).

| Result | Exit status |
| --- | --- |
| Tests ran and passed | `0` |
| At least one test failed | `1` |
| **No tests were collected** | **`5`** |
| **Every collected test was skipped** | **`0`** |

So pytest already fails a run that collects nothing, which is good, but it passes a run where everything is skipped. Check the skip count.

## 3. Structured output

```
pytest --junitxml=<temporary file>.xml
```

The first `testsuite` element carries `tests`, `failures`, `errors` and `skipped` attributes. The number executed is `tests` minus `skipped`. A run where `tests` equals `skipped` executed nothing, even though the exit status is `0`. The skip reasons are in the `message` attribute of the `skipped` child elements of each `testcase`.

`pytest --collect-only -q` lists the collected test ids and ends with a count line, useful for a quick look. Prefer the JUnit file for counting.

## 4. Making an empty or all-skipped run fail

- An empty run already fails (exit `5`). Make sure no script or CI step swallows it (`|| true`, `continue-on-error`, or treating `5` as success).
- For all-skipped runs, offer a short check in CI or in the definition of done that reads the JUnit counts and fails when the number executed (`tests` minus `skipped`) is zero.
- Check that skip markers are not being used to hide failing tests. Report how many tests are skipped, and why if the reason is given.

## 5. Creating a minimal test structure

- Put tests under a `tests` directory, with files named `test_*.py`.
- Configure `testpaths` in the pytest table of `pyproject.toml`, merged into the existing file.
- Import the code under test the way the project does (installed package or a source layout). Follow the existing layout.
- Add pytest as a development dependency only with approval, through the project's package manager.

Do not create a test that asserts nothing meaningful. Ask for one real behavior to test, or leave the suite empty and say so.

## 6. Pitfalls and limits

- **A missing `testpaths` or a wrong working directory** can make pytest collect nothing, or collect tests from places you did not mean.
- **Import errors during collection** make the run fail before any test executes. Classify it **not runnable**, not failing.
- **Plugins and markers** can change what is collected or skipped. Read the pytest configuration.
- **Tests that need services** (database, network) should be asked about before running. Look for the signs first: `.env*` files, a compose file, connection strings in settings, and fixtures in `conftest.py` that open connections or start containers.
- **Exit status behind a pipe.** `pytest | tail` reports the last command's status. Redirect to a file (works in every shell) or, in bash, read `PIPESTATUS[0]`.
- **Skipped on purpose.** Conditional skips (for example by platform) are normal. Look at the reasons before treating skips as a problem.
- A single run does not reveal flaky tests.

## 7. Verified on

2026-10-12, run in a throwaway sample (pytest from the latest release at the time, Python 3.14): no tests collected exited `5`; one passing test exited `0`; one failing test exited `1`; `--collect-only -q` listed the test id and a count line; the JUnit XML reported `tests`, `failures`, `errors` and `skipped`; a run with its only test skipped exited `0` with `skipped="1"` and `tests="1"`; a run with two skipped tests wrote `tests="2" skipped="2"` and a `message` on each skipped element (observed in an evaluation run); `python -m pytest --version` exited `1` when pytest was missing.

Re-run on 2026-10-12 (uv 0.12.7): `uv run --no-sync` creates `.venv` when none exists.

Not verified in this pass: other runners such as `unittest`, pytest plugins that change exit statuses, runs under `poetry run`, and parallel test runners.
