# Python stack reference for harness-sensor-probe

## 1. Detection markers

`pyproject.toml`, `ruff.toml`, `.ruff.toml`, `mypy.ini`, `setup.cfg`, lock files. Read the tool configuration for `exclude`, `extend-exclude`, `per-file-ignores`, and per-module overrides that could hide the probe.

## 2. Placement rules

- Put the probe in an existing package directory that holds production code, named `_harness_sensor_probe.py`. Refuse to run if the path exists.
- The path must be inside what the tools analyze. Check that no `exclude` or `extend-exclude` pattern, `per-file-ignores` entry, or type checker override matches it. Before creating the file, list what ruff will check (`ruff check --show-files` prints the files it would analyze, and the probe folder must show up in it) and read the settings in effect with `ruff check --show-settings <an existing file in the same folder>`. If the intended path is excluded, do not run the probe there: say that the control does not apply to that path, propose another package directory that is analyzed, and ask for confirmation before using it. If every package directory is excluded, report the controls as **inconclusive** and stop.
- If `_harness_sensor_probe.py` already exists, do not touch it: use `_harness_sensor_probe_2.py`, then `_3`, and so on. If the alternative also exists, ask.
- Do not put it under a test directory unless the project applies the same rules there.
- If there is a `src` layout, place the probe inside the package under `src`.

## 3. Probe snippets

```python
# Defective sample created by a harness probe. Removed after the check.
import hashlib
import sqlite3


def probe_query(conn: sqlite3.Connection, owner: str):
    return conn.execute("SELECT * FROM t WHERE owner = '" + owner + "'").fetchall()


def probe_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def probe_default(item: int, bucket: list[int] = []) -> list[int]:
    bucket.append(item)
    return bucket


def probe_untyped(value):
    return value
```

The snippets use only the standard library. Keep every line of the probe at 88 characters or fewer: with the line-length rule selected, a longer comment adds a spurious `E501` at the probe's first line (observed with a 90-character header). Ignore codes that are not in the table above.

| Snippet | Control targeted | Expected code |
| --- | --- | --- |
| `probe_query` (SQL built from input) | Security rules | `S608` |
| `probe_hash` (weak hash algorithm) | Security rules | `S324` |
| `probe_default` (mutable default argument) | Correctness rules | `B006` |
| `probe_untyped` (no annotations) | Strict type checking | `no-untyped-def` |

The type snippet only fires under strict settings (or at least a rule that requires annotations). `probe_query` also has no return annotation, so a strict type checker reports it too. That is expected.

## 4. Running the check with guaranteed cleanup

Run the lint and type commands the project uses, through its environment runner, inside a construct that removes the probe afterwards, for example in a POSIX shell:

```sh
PROBE="<package dir>/_harness_sensor_probe.py"
OUT="${TMPDIR:-${TEMP:-/tmp}}"
( trap 'rm -f "$PROBE"' EXIT
  cp "<the probe snippet file kept outside the repository>" "$PROBE"
  ruff check --output-format concise . > "$OUT/probe_ruff.txt" 2>&1; echo "ruff exit=$?"
  mypy <package-dir> > "$OUT/probe_mypy.txt" 2>&1; echo "mypy exit=$?" )
```

The tool outputs go to a temporary folder, so the probe stays the only file the run adds. Run each tool without letting the runner change the project: the tools on the PATH, or the executables of a `.venv` that already exists. `uv run --no-sync` is safe only when `.venv` exists, because with no `.venv` it still creates one in the repository. A plain `uv run` or `poetry run` can create or sync an environment, which needs approval. If a script in the project calls `ruff` or `mypy` from the PATH, run the script under the same environment as the direct runs, so both give comparable results. The `trap` does not run on SIGKILL or a power loss, so confirm afterwards that the probe is gone.

Match the probe's path in the output with either separator: on Windows the tools print `\` (for example `acme_billing\_harness_sensor_probe.py`).

Check cheaply that each tool exists before the run (`ruff --version`, `mypy --version`). A missing tool is reported as **not run** for its controls (inconclusive), the other tool is still run, and nothing is installed without asking.

In PowerShell, use `try { ... } finally { Remove-Item $probe -ErrorAction SilentlyContinue }`. The `trap` form was run with Git Bash on Windows, and the PowerShell form was not.

Read the result from each tool's exit status and from the lines that carry the probe's path:

- Ruff concise lines look like `<path>:<line>:<col>: <CODE> <message>`.
- Mypy lines look like `<path>:<line>: error: <message>  [<code>]`.

Use the exact commands from the project's definition of done, including any extra flags. If a script wraps a command with a bypass such as `--exit-zero` or `|| true`, run the script too and compare.

## 5. Classifying results

| Observation | Class |
| --- | --- |
| Code appears and the tool's exit status is non-zero, and the project's real command also fails | enforced |
| Code appears and the tool fails when run directly, but the project's real command exits with success | reported (a bypass sits in the command, name it) |
| Code does not appear and the probe file was analyzed | silent |
| The probe path is excluded, or the tool failed before analysis (invalid configuration, missing tool) | inconclusive |

A missing tool is reported as not run. Do not install it without asking.

If the baseline (the run without the probe) already exits with failure for a tool, do not classify that tool's controls by exit status: report them as **inconclusive** and list the probe's diagnostics separately. When a script runs both tools, run each tool directly too, so each one has its own exit status, and say which command produced which status.

## 6. Pitfalls and limits

- Run the tools from the project's environment. A different environment can change results.
- `ruff.toml` shadows the ruff table in `pyproject.toml`. If the tool does not behave as the file in front of you suggests, check which configuration file is in effect with `ruff check --show-settings <file>`.
- The type checker only reports on code it is asked to check. Use the same target the project uses.
- Ruff's `exclude` and `extend-exclude` do not affect mypy: `mypy <excluded package>` still analyzes it. Check the exclusion per tool, and read mypy's own `exclude` and overrides for the type checker.
- `ruff check <path>` with an explicit path to an excluded file ignores the exclusion and reports the probe's diagnostics, which gives a false "enforced". Run `ruff check .` (or the project's real command), or add `--force-exclude` if you must pass the path.
- The probe covers four defect classes. Banned imports, architecture contracts, and style need their own checks.

## 7. Verified on

2026-10-12, run in a throwaway sample project (ruff 0.17.0, mypy from the latest release at the time, Python 3.14) with the `S` and `B` families selected and strict type checking: the clean baseline exited `0` for both tools, the probe produced `S608`, `S324` and `B006` from ruff and two `no-untyped-def` errors from mypy, both tools exited `1`, and the file was removed by a shell `trap`.

In a later pass, `ruff check --show-files` (ruff 0.17.0) was run in a throwaway sample with `extend-exclude`: the excluded folder was absent from the list and the other folder was present, and `--show-settings <file>` printed the settings path in effect.

Re-run on 2026-10-12 with ruff 0.17.0, mypy 2.4.0 and uv 0.12.7 in throwaway samples: a 90-character header comment adds `E501`; `ruff check <excluded file>` with an explicit path reports diagnostics, and with `--force-exclude` it reports no Python files and exits `0`; `ruff check .` ignores the excluded folder; `mypy <excluded package>` still analyzes it; `uv run --no-sync` creates `.venv` when none exists.

Not verified in this pass: the PowerShell cleanup form, SIGKILL during the run, `src` layouts, projects that use pyright instead of mypy, and runs through `poetry run`.
