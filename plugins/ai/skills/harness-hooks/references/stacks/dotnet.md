# .NET stack reference for harness-hooks

## 1. Detection markers

`*.sln`, `*.slnx`, `*.csproj`, `global.json`, `Directory.Build.props`. Source files are `.cs`.

## 2. Candidate definition-of-done commands

Each command is a program and an argument list. Use the solution file as the unit. Prefer the commands that the project's agent guide already lists, and only commands that were run and exited `0`.

| Name | Program and arguments | Notes |
| --- | --- | --- |
| build | `dotnet build <solution> --no-incremental` | Fails on errors. Fails on warnings only if failure on warning is configured (see `harness-sensors`). `--no-incremental` makes sure analysis runs. |
| tests | `dotnet test <solution>` | Exits `0` with zero tests. Pair it with `harness-test-baseline`. |
| format | `dotnet format <solution> --verify-no-changes` | Exits `2` (not `1`) when something would change. The hook treats any non-zero status as a failure. Never use the version without `--verify-no-changes`: it rewrites files. |

The hook runs these commands as the project's directory, with the user's permissions. They compile and run project code, which is the same trust the agent already needs.

Restore may need the network. If the packages are not cached, the first run can be slow or fail. Set a timeout above the real duration.

## 3. Suppression markers

| Pattern (in the configuration, with doubled backslashes) | File globs | Label |
| --- | --- | --- |
| `#pragma\s+warning\s+disable` | `*.cs` | pragma warning disable |
| `\[(assembly:\s*)?(System\.Diagnostics\.CodeAnalysis\.)?SuppressMessage` | `*.cs` | SuppressMessage |
| `<NoWarn>` | `*.csproj`, `*.props`, `*.targets` | NoWarn |
| `dotnet_diagnostic\.[A-Za-z0-9]+\.severity\s*=\s*(none\|suggestion\|silent)` | `*.editorconfig`, `.editorconfig`, `*.globalconfig` | severity lowered in editorconfig |

(In the editorconfig pattern, the vertical bars separate alternatives. The backslash before each bar in the table is only markdown table escaping: write a plain `|` in the configuration and do not copy the backslash.)

Ignore paths for generated code, which tools write and which can contain markers: `*/Migrations/*`, `*.g.cs`, `*.Designer.cs`, `*/obj/*`, `*/bin/*`. Ask the user about others. The EF Core migration generator writes a `#pragma warning disable` into migration files, so ignoring the migrations folder is usually needed.

The glob matching normalizes backslashes to forward slashes and uses `fnmatch`, where `*` also matches path separators. `*.cs` matches any file ending in `.cs`.

## 4. Commands that act on remote systems or shared data

Patterns match anywhere in the command text, so they also catch `sh -c '...'` and full-path forms.

| Pattern | Suggested | Reason to show |
| --- | --- | --- |
| `dotnet\s+ef\s+database\s+update` | ask | Applies migrations to a database. Safe only against a local, disposable one. |
| `dotnet\s+ef\s+database\s+drop` | deny | Drops a database. |
| `dotnet\s+nuget\s+push` | deny | Publishes a package. |
| `dotnet\s+publish` | ask, if the project's deploy goes through it | Produces deployable output. Often harmless locally, so confirm with the user. |

Add the project's own deploy or release scripts by name.

## 5. Pitfalls and limits

- A pattern matches text, not intent. `dotnet ef database update` inside a comment or an echo also matches.
- The suppression guard looks at the text an edit adds. A suppression written through a shell command is not seen by the edit guard and is caught by the stop guard's diff scan at the end of the turn.
- A new `<NoWarn>` can be legitimate (for example a package-version warning). Make exceptions in the configuration by path rather than by weakening the rule.
- `dotnet format` and `dotnet build` can write files under `obj` and `bin`. Those are normal build outputs.
- The stop guard's diff scan counts markers added in changed and new files. A file that already has a marker and is only touched elsewhere is not a finding.

## 6. Verified on

2026-10-12: the command exit statuses (`dotnet format --verify-no-changes` exits `2`, `dotnet test` exits `0` with no tests, `dotnet build` exits `1` on errors and on warnings treated as errors) were observed in throwaway samples with SDK 10.0.401 (see the other harness skills). The hook script and its patterns were tested with sample events in the script's test suite. The suppression and command guards were run through the real agent (see the agent reference).

Each pattern listed in sections 3 and 4 was also checked against one line that should match and one that should not (for example `#pragma warning restore` and `[Fact]` do not match).

Not verified in this pass: that the editorconfig and `SuppressMessage` patterns match every spelling in real projects, F# and Visual Basic projects, and other SDK versions.
