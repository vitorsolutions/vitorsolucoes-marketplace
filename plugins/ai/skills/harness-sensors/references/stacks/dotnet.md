# .NET stack reference for harness-sensors

## 1. Detection markers

| File | Meaning |
| --- | --- |
| `*.sln`, `*.slnx` | Solution. Use it as the unit for the verification command. When both exist for the same solution, ask which one to use. |
| `*.csproj`, `*.fsproj`, `*.vbproj` | Project. SDK-style projects start with `<Project Sdk="...">`. Non-SDK-style projects are legacy (see pitfalls). |
| `global.json` | Pins the SDK version. Never change it. |
| `Directory.Build.props` | Repository-wide MSBuild properties. The preferred place for the controls below. |
| `Directory.Build.targets`, `.editorconfig` | Read them for effective state. Style rules in `.editorconfig` belong to `harness-code-style`. |

## 2. Canonical commands

| Purpose | Command |
| --- | --- |
| Toolchain version | `dotnet --version` |
| Effective state of properties | `dotnet msbuild <project> -getProperty:<Name1>,<Name2>` (requires MSBuild 17.8 or later, which ships with SDK 8.0.100 or later). One property prints a plain value. Several print JSON. |
| Verification command | `dotnet build <solution> --no-incremental`. `<solution>` is the real file name: SDK 10 creates `.slnx`, and passing a `.sln` name that does not exist fails with `MSB1009` |
| Exit status | `0` success, non-zero failure. Always use `--no-incremental` when counting diagnostics, because an incremental build can skip analysis and hide warnings. |

An empty value does not mean the same thing for every property:

| Property | Empty means |
| --- | --- |
| `Nullable` | off |
| `AnalysisModeSecurity`, `AnalysisMode` | not set (default rule set) |
| `AnalysisLevel` | the SDK default, which follows the newest rules (it reads `latest`), so it is not a pin |
| `TreatWarningsAsErrors` | `false` |

Run the effective-state command against one project of each kind (application, library, test) because a project file can override a repository-wide property.

If the SDK is older than 8.0.100, `-getProperty` is not available. Read the property files directly, say the effective state is **unknown**, and rely on the verification command result.

## 3. Controls

| Control | Mechanism | Read effective state | Enable | Fails the command? |
| --- | --- | --- | --- | --- |
| Nullable reference checking | `Nullable` | `-getProperty:Nullable` | `<Nullable>enable</Nullable>` | Only with failure-on-warning |
| Built-in code-quality analyzers | `EnableNETAnalyzers`, `AnalysisLevel` | `-getProperty:EnableNETAnalyzers,AnalysisLevel,AnalysisMode` | On by default for .NET 5 and later. Set `AnalysisLevel` to `latest` or pin it to a version | Only with failure-on-warning |
| Security rules | `AnalysisMode<Category>` with category `Security` | `-getProperty:AnalysisModeSecurity` | `<AnalysisModeSecurity>All</AnalysisModeSecurity>` | Only with failure-on-warning |
| Failure on warning | `TreatWarningsAsErrors` | `-getProperty:TreatWarningsAsErrors,WarningsAsErrors,WarningsNotAsErrors` | `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` | Yes |
| Dependency vulnerability audit | `NuGetAudit`, `NuGetAuditMode`, `NuGetAuditLevel` | `-getProperty:NuGetAudit,NuGetAuditMode,NuGetAuditLevel` | On by default. Produces warnings `NU1901` to `NU1904` during restore | Only with failure-on-warning |

Put the properties in a `Directory.Build.props` at the repository root so they apply to every project. If one exists, add the properties to it. If a project file or a nearer `Directory.Build.props` sets the same property, that value wins, so read the effective state again after the change.

Setting `AnalysisModeSecurity` enables a whole category of rules without touching other categories. `AnalysisMode` set to `All` enables every category and usually produces too many diagnostics at once. Prefer the category form first.

`AnalysisLevel` set to `latest` gives the newest rules after every SDK upgrade, which can turn a passing build into a failing one with no code change. Pinning it to a version (for example `8.0`) avoids that. Ask which behavior the user wants and state the trade-off. Because the default already follows the newest rules, the pinning question applies to every project that has not set `AnalysisLevel`.

### Structured results (SARIF)

SARIF output is not a control: it does not change whether the verification command passes. It writes the compiler and analyzer diagnostics to a file in the SARIF format so that CI can publish them (see `harness-ci-pipeline`). Add it only when the user wants the findings published somewhere. Keep it off by default so local builds write nothing extra.

The compiler option is the MSBuild property `ErrorLog`: a path, optionally followed by `,version=2.1`. Valid versions are `1`, `2` and `2.1`. The default is `1`, and `2` and `2.1` both mean SARIF 2.1.0, so always set the version.

Wire it in `Directory.Build.targets`, switched on by a property that only CI sets:

```xml
<Project>
  <PropertyGroup Condition="'$(SarifDir)' != ''">
    <ErrorLog>$(SarifDir)/$(MSBuildProjectName)-$(TargetFramework).sarif,version=2.1</ErrorLog>
  </PropertyGroup>
</Project>
```

CI then builds with `-p:SarifDir=<absolute folder>`. A local build does not set it and writes nothing. If a `Directory.Build.targets` already exists, merge into it. Read the effective state afterwards with `dotnet msbuild <project> -getProperty:ErrorLog -p:SarifDir=<folder>`. Without `SarifDir` the value is empty.

Why this shape (each point was observed in a sample, see section 7):

- **`.targets`, not `.props`.** Properties in `Directory.Build.props` are evaluated before the project body, so `$(TargetFramework)` is still empty for a single-target project and the file is named `Name-.sarif`.
- **Not `-p:ErrorLog=...` on the command line.** A global property is not expanded per project, so `$(MSBuildProjectName)` reaches the compiler as literal text. A fixed path would also be shared by every project and target framework.
- **One file per project and target framework.** A solution with a single-target library and a library targeting two frameworks produced three files.
- **The folder must exist before the build.** The compiler does not create it, and every project fails with `CS0016`.
- **The files are written even when the build fails** (checked with `-warnaserror`, exit `1`), which is when they matter most.
- **Paths inside the files are absolute `file:///` URIs** of the machine that built. Consumers that expect repository-relative paths need to resolve them (see the CI host reference).
- Use it with `--no-incremental`, as for every diagnostic count: a compilation that is skipped does not run the analyzers.

## 4. Gradual adoption

Use when the baseline already has warnings.

| Mechanism | How | Cost |
| --- | --- | --- |
| Failure on selected codes only | `<WarningsAsErrors>` with an explicit list of diagnostic codes instead of enabling failure on all warnings | The list must be extended over time. Codes not listed stay as warnings. |
| Failure on everything except current debt | `TreatWarningsAsErrors` set to `true` plus `<WarningsNotAsErrors>` listing the codes that exist in the baseline | New occurrences of those codes are also tolerated. The list must be shrunk as code is fixed. |
| Per-project opt-in | Set the properties in each project file instead of repository-wide, starting with new projects | Uneven protection across the solution. |

Record the baseline counts by code in the report so the user can track progress.

## 5. Pitfalls

- **Failure on warning also affects restore.** NuGet audit warnings (`NU1901` to `NU1904`) become errors. A vulnerability published tomorrow can break a build that passes today with no code change. Microsoft documents `<WarningsNotAsErrors>NU1901;NU1902;NU1903;NU1904</WarningsNotAsErrors>` to keep them as warnings, and a separate audit pipeline that treats them as errors only there. Present both options and the trade-off, and let the user choose. Do not decide silently.
- **Transitive packages are audited by default for projects that target .NET 10 or later.** Expect more audit diagnostics after retargeting.
- **A property in a project file overrides `Directory.Build.props`.** Always read the effective state afterwards.
- **Several `Directory.Build.props` files** in nested folders: the nearest one wins unless it imports its parent. Check for them before editing.
- **Generated code** (migrations, designer files, files marked auto-generated) is mostly exempt from analyzers, but tools can emit suppression directives inside it. Report them. Do not remove them.
- **Legacy non-SDK-style projects** do not understand `AnalysisLevel`. Report them as unsupported by this pack and suggest migrating them separately.
- **Diagnostic text depends on the SDK language.** Always match by code (`CS8602`, `CA2100`, `NU1903`).
- **`dotnet build` without `--no-incremental`** can report fewer warnings than a clean build.
- **A SARIF folder that is not empty at the start of a run** can mix files from an earlier run with the current ones. Use a new or emptied folder, outside the source tree.
- **Restore-time diagnostics (`NU1901` to `NU1904`)** come from NuGet, not from the compiler. This pass did not check whether they appear in the compiler's SARIF files. Do not tell the user that the SARIF covers dependency vulnerabilities (see `nuget-dependency-audit`).
- **Each diagnostic appears twice in the build output** (once inline and once in the summary). Count distinct occurrences by file, line and code, and never by counting matching lines. For example (the compiler prefix `warning`/`error` stays in English, the message text does not): `grep -E ': (warning|error) [A-Z]+[0-9]+' out.txt | sed -E 's/^ +//; s/ \[[^]]*\]$//' | sort -u | grep -oE '(warning|error) [A-Z]+[0-9]+' | sort | uniq -c`.

## 6. Limits

- Analyzers have limited data-flow coverage across methods and assemblies.
- Business rules and project dependency direction are not visible to them.
- These suppressions silence every control above: `#pragma warning disable`, `[SuppressMessage]`, `<NoWarn>`, and `dotnet_diagnostic.<ID>.severity = none` in `.editorconfig`.

## 7. Verified on

2026-10-12, against Microsoft Learn: MSBuild properties for .NET SDK projects (code analysis properties), overview of .NET source code analysis, NuGet auditing and the `NU1901` to `NU1904` warnings, and the MSBuild evaluation switches (`-getProperty`).

Also run in a throwaway sample project with SDK 10.0.401: the multi-property `-getProperty` readout (JSON output), the default state (`AnalysisMode` empty, `TreatWarningsAsErrors` false, `NuGetAuditMode` `all`), `AnalysisModeSecurity` set to `All` adding `CA2100` and `CA5351` as warnings with exit `0`, `TreatWarningsAsErrors` turning them into errors with exit `1`, and `WarningsNotAsErrors` keeping `CS8602` as a warning while the others still failed.

Verified later (Microsoft Learn, .NET SDK, MSBuild, and Visual Studio versioning): SDK 8.0.100 ships with Visual Studio and MSBuild 17.8, and `-getProperty` is documented as available in MSBuild 17.8 and later. The counting command above was run on sample text only.

2026-10-19, against Microsoft Learn (C# compiler options to report errors and warnings): the `ErrorLog` property, the `version` values `1`, `2` and `2.1`, and the default `1`. Run in a throwaway sample solution (SDK 10.0.402, `AnalysisModeSecurity` set to `All`) with one single-target library and one library targeting two frameworks: with `ErrorLog` set in `Directory.Build.props` the single-target file was named `Lib-.sarif`, and in `Directory.Build.targets` it was `Lib-net10.0.sarif`; a command-line `-p:ErrorLog=` with a `$(...)` value was written literally; a missing output folder failed every project with `CS0016`; the three files reported `"version": "2.1.0"` and the rules `CA1822`, `CA1850` and `CA5351`, with absolute `file:///` URIs; with `-warnaserror` the build exited `1` and the three files were still written; without `SarifDir` the build wrote nothing and `-getProperty:ErrorLog` was empty. Only the Git Bash shell on Windows was used.

Not verified in this pass: whether restore diagnostics appear in the files, Visual Basic and F# projects, behavior on SDKs older than 10, and which individual `CA` rules are in the security category for other SDK versions.
