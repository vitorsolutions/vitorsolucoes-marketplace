# .NET stack reference for harness-permissions

## 1. Detection markers

`*.sln`, `*.slnx`, `*.csproj`, `global.json`, `Directory.Build.props`, `appsettings*.json`.

## 2. Verification commands to allow

Allow only what the project's definition of done actually runs. Rules are command prefixes with the wildcard after the subcommand.

| Rule | Notes |
| --- | --- |
| `Bash(dotnet build *)` | Compiles and runs the project's build logic (analyzers, MSBuild targets). Allowing it lets the agent run code that is defined in the repository. |
| `Bash(dotnet test *)` | Runs the project's tests, which are arbitrary code. |
| `Bash(dotnet format <solution> --verify-no-changes)` | Write the exact command from the definition of done. A trailing wildcard here would also allow the form without `--verify-no-changes`, which rewrites files. |

Never allow `Bash(dotnet *)`: it covers `dotnet ef`, `dotnet nuget push`, `dotnet publish` and every tool installed as a `dotnet` extension.

## 3. Commands that act on remote systems or shared data

| Rule | Suggested list | Why |
| --- | --- | --- |
| `Bash(dotnet ef database update *)` | ask | Applies migrations to the database in the connection configuration. Fine against a local disposable database. |
| `Bash(dotnet ef database drop *)` | deny | Drops a database. |
| `Bash(dotnet-ef *)` | ask | The same tool invoked by its executable name, which the rules above do not match. Include it as ask by default, and tell the user it can also be used for harmless commands such as listing migrations. |
| `Bash(dotnet nuget push *)` | deny | Publishes a package. |
| `Bash(dotnet publish *)` | ask | Produces deployable output. Often harmless locally. |

These match the usual form. The same command through a different path, inside `sh -c`, or with options before the subcommand may not match (see the agent reference), so pair the destructive ones with the command guard in `harness-hooks`.

## 4. Files that commonly hold secrets (by name)

Choose by name and location. Do not open them.

| Rule | Why |
| --- | --- |
| `Read(./.env)` and one rule per real variant found by name (for example `Read(./.env.local)`, `Read(./.env.production)`) | Environment files. Do not use `Read(./.env.*)`: it also matches `.env.example`, and a deny cannot be overridden by an allow. |
| `Read(**/appsettings.Production.json)` | Production settings often carry connection strings. Check which `appsettings` files the project really uses before adding more. |
| `Read(**/*.pfx)`, `Read(**/*.snk)`, `Read(**/*.pem)`, `Read(**/*.key)` | Certificates and signing keys |
| `Read(~/AppData/Roaming/Microsoft/UserSecrets/**)` and `Read(~/.microsoft/usersecrets/**)` | Where the user-secrets store keeps values outside the repository (Windows and the other systems respectively). Whether the home-relative form matches these locations on each system was not verified. |

Do not deny reading `appsettings.json` or `appsettings.Development.json` unless the user confirms they hold secrets. The agent needs to read ordinary configuration to work.

A read deny rule also blocks editing and writing those paths.

## 5. Configuration files that define the checks (edit protection)

Bare filenames in an ask or deny rule match at any depth, so one rule per file name is enough.

| Rule | Why |
| --- | --- |
| `Edit(Directory.Build.props)` and `Edit(Directory.Build.targets)` | Where analyzers, warnings as errors and style enforcement are set |
| `Edit(Directory.Packages.props)` and `Edit(global.json)` | Package versions and the pinned SDK |
| `Edit(.editorconfig)` | Style and analyzer severities |
| `Edit(BannedSymbols.txt)` | The list of banned APIs |
| `Edit(packages.lock.json)` | Lock files, if the project uses them |

Suggest **ask**, so that legitimate changes can still happen with a confirmation. Use deny only if the user wants to make those edits by hand.

## 6. The agent's own configuration

| Rule | Why |
| --- | --- |
| `Edit(/.claude/settings.json)` and `Edit(/.claude/settings.local.json)` | Without this the agent can remove its own rules and hooks |
| `Edit(/.claude/hooks/**)` | The hook scripts and their configuration |

## 7. Pitfalls and limits

- A generic `Read(**/appsettings*.json)` also blocks ordinary configuration the agent needs.
- Project files are Windows paths on a Windows machine, but rules are written in POSIX form.
- Absolute paths need `//`. A single leading slash is relative to the settings file.
- Rules do not stop a program the agent runs from reading the file (for example a test that loads configuration). Use the sandbox for that.
- An allow rule for the build means the agent can run code that the repository defines.

## 8. Verified on

2026-10-12: rule syntax against the Claude Code documentation, and a startup validation run (see the agent reference) with every rule in sections 2 to 6 loaded together, which printed no warning. In a throwaway folder, an `Edit(Directory.Build.props)` ask rule refused an edit of a nested `src/sub/Directory.Build.props` and an unlisted file in the same folder was edited. The command prefixes were not run against the real .NET tools in an agent session, only checked for accepted syntax.

Not verified in this pass: that the user-secrets paths match on each operating system, and `Bash(dotnet-ef *)` behavior.
