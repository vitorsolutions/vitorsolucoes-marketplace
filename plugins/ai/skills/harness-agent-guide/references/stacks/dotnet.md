# .NET stack reference for harness-agent-guide

## 1. Detection markers

| File | Meaning |
| --- | --- |
| `*.sln`, `*.slnx` | Solution. Use it as the unit for commands. When both exist for the same solution, ask which one is current. |
| `*.csproj`, `*.fsproj`, `*.vbproj` | Projects. |
| `global.json` | Pinned SDK version. Mention the version in the guide only if it is pinned. |
| `Directory.Build.props`, `Directory.Build.targets`, `Directory.Packages.props` | Repository-wide build and package configuration. |

## 2. Structure and dependency direction

| Need | Command | Notes |
| --- | --- | --- |
| Projects in the solution | `dotnet sln <solution> list` | Works with both solution formats. Paths are relative to the solution. |
| Dependency direction | `dotnet list <project> reference` for each project | Lists project references of that project. Combine the results into a direction map: project A depends on project B. |

Always build the direction map from the project reference graph, never from folder or project names. A project called "Domain" can still reference an outer layer.

Do not state a layering rule as fact just because the references look layered. Put it in the guide only if the user confirms it is a rule and not a coincidence.

## 3. Candidate verification commands

| Purpose | Command | Reading the result |
| --- | --- | --- |
| Build | `dotnet build <solution>` | Exit `0` success, non-zero failure. |
| Tests | `dotnet test <solution>` | Same. |
| Format and style check | `dotnet format <solution> --verify-no-changes` | Exit `0` when nothing would change. |

Rules for listing them:

- Command output is localized to the SDK's language. Never parse the text. Use the exit status.
- A build that exits `0` but prints warnings is **reported**, not enforced. If the user wants warnings to fail it, point to `harness-sensors` instead of writing a command into the guide that does not do that.
- Include the format check only if it exits `0` today. If the project has no style configuration, it checks very little. Say so rather than presenting it as a quality gate.
- A restore may need the network, and it also happens implicitly inside `dotnet build` and `dotnet test`. Ask before the first build or test run in an environment where packages are not cached.
- SDK 10 creates `.slnx` solution files, and the commands above accept them in place of `<solution>`.

## 4. Suppression mechanisms

List the ones that apply in this project, found by searching the source and configuration:

- `#pragma warning disable` in source files.
- `[SuppressMessage]` and `GlobalSuppressions.cs`.
- `<NoWarn>` in project or property files.
- `dotnet_diagnostic.<ID>.severity = none` (or `suppression`) in `.editorconfig` and global analyzer config files.

Generated code (migrations, designer output) can contain these markers written by a tool. Report them and let the user decide whether the restriction should carve them out.

## 5. Configuration files that define the checks

`Directory.Build.props`, `Directory.Build.targets`, `.editorconfig`, any global analyzer config, `BannedSymbols.txt` when present, `global.json`, `Directory.Packages.props`.

## 6. Commands that act on remote systems or shared data

- `dotnet ef database update` and `dotnet ef database drop`: change a database. Safe only against a local, disposable one.
- `dotnet nuget push`: publishes a package.
- Any deploy or publish command the project defines in scripts.

Also ask where connection strings and secrets live (configuration files, user secrets, environment variables) so the credentials restriction names the real places.

## 7. Pitfalls and limits

- Test projects reference production code, so a reference from a test project outward is normal. Do not read it as a layering violation.
- Multi-targeted projects can behave differently per target. Say which target a command ran against if it matters.
- Do not describe analyzer settings in the guide as active unless the effective state confirms them.

## 8. Verified on

2026-10-12, run against a throwaway sample solution (SDK 10.0.401): `dotnet sln <slnx> list`, `dotnet list <project> reference`, `dotnet format <slnx> --verify-no-changes` (exit `0` on a fresh solution), and `dotnet test <slnx>` (exit `0`). Observed that the output of these commands is localized.

Not verified in this pass: behavior of `dotnet sln list` on solution folders and nested solutions, and on `.sln` files with unusual structure.
