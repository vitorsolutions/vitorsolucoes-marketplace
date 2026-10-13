# Python stack reference for harness-permissions

## 1. Detection markers

`pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `.python-version`, `.env`. Find out which package manager and which environment runner the project uses (`uv run`, `poetry run`, or an activated environment), because the rules must match the commands as the agent will write them.

## 2. Verification commands to allow

Allow only what the project's definition of done runs. Rules are command prefixes with the wildcard after the subcommand.

| Rule | Notes |
| --- | --- |
| `Bash(ruff check *)` | Lint. Exit status `1` on violations. Without `--fix`, it does not modify files. |
| `Bash(ruff format --check *)` | Formatting check. The version without `--check` rewrites files, so do not allow `Bash(ruff format *)`. |
| `Bash(mypy *)` | Type check. |
| `Bash(pytest *)` | Runs the project's tests, which are arbitrary code. |
| `Bash(uv run ruff check *)`, `Bash(uv run mypy *)`, `Bash(uv run pytest *)` | The same, through the environment runner. Write one rule per tool. |

Never allow `Bash(uv run *)`, `Bash(python *)`, `Bash(python -m *)` or `Bash(poetry run *)`. They are general runners: they would let the agent run any program or script without asking.

## 3. Commands that act on remote systems or shared data

Use what the project actually has. Common candidates:

| Rule | Suggested list | Why |
| --- | --- | --- |
| `Bash(alembic upgrade *)` and `Bash(alembic downgrade *)` | ask | Changes a database schema. Fine against a local disposable database. |
| `Bash(python manage.py migrate *)` | ask | Changes a database (Django projects). |
| `Bash(pip install *)`, `Bash(uv add *)`, `Bash(uv pip install *)` | ask | Changes the environment and the dependency set. |
| `Bash(twine upload *)` and `Bash(uv publish *)` | deny | Publishes a package. |

These match the usual form. The same command through a different path, inside `sh -c`, or with options before the subcommand may not match, so pair the destructive ones with the command guard in `harness-hooks`.

## 4. Files that commonly hold secrets (by name)

Choose by name and location. Do not open them.

| Rule | Why |
| --- | --- |
| `Read(./.env)` and one rule per real variant found by name (for example `Read(./.env.local)`, `Read(./.env.production)`) | Environment files. Do not use `Read(./.env.*)`: it also matches `.env.example`, and a deny cannot be overridden by an allow. |
| `Read(**/*.pem)` and `Read(**/*.key)` | Certificates and private keys |
| `Read(~/.pypirc)` | Package index credentials (usually used by `twine`) |
| `Read(~/.aws/**)` | Cloud credentials, if the user's machine has them |

A read deny rule also blocks editing and writing those paths.

## 5. Configuration files that define the checks (edit protection)

Bare filenames in an ask or deny rule match at any depth.

| Rule | Why |
| --- | --- |
| `Edit(ruff.toml)` and `Edit(.ruff.toml)` | Lint and format rules |
| `Edit(mypy.ini)` | Type checker settings |
| `Edit(.python-version)` | The pinned interpreter |
| `Edit(uv.lock)`, `Edit(poetry.lock)` | Lock files, if the project uses them |
| `Edit(pyproject.toml)` | **Trade-off:** it holds the tool settings and also the dependency list. An ask rule prompts for every legitimate dependency edit too. Offer it, explain the cost, and let the user decide. |

Suggest **ask**, so that legitimate changes still happen with a confirmation.

## 6. The agent's own configuration

| Rule | Why |
| --- | --- |
| `Edit(/.claude/settings.json)` and `Edit(/.claude/settings.local.json)` | Without this the agent can remove its own rules and hooks |
| `Edit(/.claude/hooks/**)` | The hook scripts and their configuration |

## 7. Pitfalls and limits

- General runners cannot be allowed safely. If the definition of done goes through one, write one rule per exact command.
- Rules do not stop a Python program the agent runs from reading a file (a test or a script that loads `.env`). Use the sandbox for that.
- A deny for `.env` blocks the agent from reading it, which is the point, but also from helping with its structure. Offer an example file for the agent to read instead.
- Absolute paths need `//`. A single leading slash is relative to the settings file.
- An allow rule for the tests means the agent can run code that the repository defines.

## 8. Verified on

2026-10-12: rule syntax against the Claude Code documentation, and a startup validation run (see the agent reference) with every rule in sections 2 to 6 loaded together, which printed no warning. The command prefixes were not run against the real Python tools in an agent session, only checked for accepted syntax.

Not verified in this pass: migration and publishing command forms in real projects (named from common usage), `Read(~/.aws/**)` and `Read(~/.pypirc)` matching on each operating system, and runs through `poetry run`.
