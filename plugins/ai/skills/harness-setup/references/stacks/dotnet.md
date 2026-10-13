# .NET stack reference for harness-setup

## 1. Detection markers

`*.sln`, `*.slnx` (SDK 10 creates `.slnx` by default), `*.csproj` (and `*.fsproj`, `*.vbproj`), `global.json`, `Directory.Build.props`. Legacy projects that do not start with an SDK reference are reported as limited: most signals below assume SDK-style projects.

## 2. Toolchain and read-only readouts

| Need | Command |
| --- | --- |
| SDK version | `dotnet --version`. If it fails because the `global.json` pin names an SDK that is not installed, mark the toolchain-dependent layers **unknown** and report the unresolvable pin as a finding for the reproducible-environment layer. Do not edit `global.json` to continue |
| Effective state of build properties | `dotnet msbuild <project> -getProperty:<Name1>,<Name2>` (MSBuild 17.8 or later; on an older MSBuild mark the property-based layers **unknown** and read the files instead). Read it for one project of each kind (application, library, test). If the output asks for a restore, stop and mark the result **unknown** instead of restoring |
| Projects in a solution | `dotnet sln <solution> list`. `<solution>` is the real file name, `.sln` or `.slnx`. With several solutions, ask which one is the repository's main one; with none, list the project files directly |
| Project references | `dotnet list <project> reference` |

Running a build, restore, or test is not read-only: ask first.

## 3. Signals by layer

| Layer | Signals that it exists | What makes it only partial |
| --- | --- | --- |
| Reproducible environment | `global.json` pinning the SDK; `Directory.Packages.props` with `ManagePackageVersionsCentrally` set to `true`; `packages.lock.json` files or `RestorePackagesWithLockFile` set to `true`; CI uses the pinned SDK | Only some of these exist; the pin allows a wide roll-forward; lock files exist but restore is not run in locked mode |
| Checks that fail | Effective `TreatWarningsAsErrors` is `true` (or a `WarningsAsErrors` list that goes beyond the SDK default `;NU1605;SYSLIB0011`, which every project reports); `AnalysisModeSecurity` or `AnalysisMode` set above the default; `Nullable` enabled | Analyzer settings on but warnings do not fail the build; failure on warning on but security rules at the default mode |
| Style | `.editorconfig` with severities for style rules; `EnforceCodeStyleInBuild` effective `true`; a format check (`dotnet format ... --verify-no-changes`) in scripts or CI | `.editorconfig` present but `EnforceCodeStyleInBuild` not on and no format check |
| Banned APIs | `Microsoft.CodeAnalysis.BannedApiAnalyzers` package reference and a `BannedSymbols.txt` included as an additional file | The package exists but no symbols file, or the diagnostic `RS0030` is not an error |
| Tests | A project referencing a test SDK package and a test framework; a `dotnet test` command in scripts or CI | A test project exists with no tests, or tests are excluded from CI |
| Architecture rules | A test project referencing an architecture-test package (common ones are `NetArchTest.Rules` and `TngTech.ArchUnitNET`) with rules about project or namespace dependencies | The package is referenced but there are no rules, or the project is not run in CI |
| Agent guide | `AGENTS.md`, `CLAUDE.md`, or tool-specific rule files | Commands in the file do not exist (read-only check), or fail (only when the user allowed running them) |
| Permissions | For Claude Code: a `permissions` entry in `.claude/settings.json` or `.claude/settings.local.json` | Only user-level settings exist, or rules are broad allow lists with no deny rules for secrets or remote data |
| Hooks | For Claude Code: a `hooks` entry in `.claude/settings.json` or `.claude/settings.local.json` | Hooks exist but do not cover the definition of done or the protected files |
| CI | A pipeline definition in the host's usual place (for example `.github/workflows`, `azure-pipelines.yml`, `.gitlab-ci.yml`) that runs the same build and test commands | The pipeline skips the checks, or marks them `continue-on-error` |
| Proof | A recorded probe result (the user can point to one) | Probe run before the last tool upgrade or configuration change. Compare the recorded probe date with `git log -1 --format=%cs -- global.json Directory.Build.props Directory.Packages.props .editorconfig` |

## 4. Where to look for agent-specific files

For Claude Code: `.claude/settings.json` (shared with the team), `.claude/settings.local.json` (personal, not committed), and user-level settings in the user's home folder. For other agents, ask the user where they keep rules, permissions, and hooks, and mark the layers unknown if they cannot say.

## 5. Pitfalls and limits

- A property set in a project file overrides `Directory.Build.props`. Read the effective state, not a single file.
- Several nested `Directory.Build.props` files: the nearest wins unless it imports its parent.
- Test projects have different settings legitimately. Do not mark a layer partial because a test project differs.
- Package names for architecture tests change over time. Treat the two names above as common examples, not a complete list.

## 6. Verified on

2026-10-12: the MSBuild property readout, solution listing, project reference listing, and properties for central package management and lock files (Microsoft Learn: central package management, locking dependencies, MSBuild properties). The readout and listing commands were also run in throwaway samples (SDK 10.0.401).

Not verified in this pass: the architecture-test package names (from common usage), pipeline file locations for hosts other than the ones named, and signals in non-SDK-style projects.

Re-run on 2026-10-12 (SDK 10.0.401): a project with no settings reports `WarningsAsErrors` as `;NU1605;SYSLIB0011` and `TreatWarningsAsErrors` as `false`, and with a `global.json` pin to a missing SDK `dotnet --version` fails. Added after the eval pass and not re-run: the staleness command in the Proof row, the stop-on-restore rule for the readout, and the `.slnx` and several-solutions handling.
