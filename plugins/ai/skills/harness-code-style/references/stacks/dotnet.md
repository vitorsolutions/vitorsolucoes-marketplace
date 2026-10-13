# .NET stack reference for harness-code-style

## 1. Detection markers

`*.sln`, `*.slnx`, `*.csproj`, `.editorconfig`, `Directory.Build.props`. Several `.editorconfig` files can exist: the nearest one wins for a file, and the search stops at one marked `root = true`.

## 2. Where style is configured

| Element | Role |
| --- | --- |
| `.editorconfig` | Formatting basics (`indent_style`, `indent_size`, `charset`, `insert_final_newline`, `end_of_line`) and severities for style rules |
| `EnforceCodeStyleInBuild` (MSBuild property) | Makes style rules (diagnostics starting with `IDE`) run in the command-line build. It is off by default, so a build ignores style unless this is set. |
| `dotnet format` | Verifies and applies formatting and style. |

Read the effective state of the property with `dotnet msbuild <project> -getProperty:EnforceCodeStyleInBuild` (MSBuild 17.8 or later). Read it for each project, because a project file can override a shared one. An empty value or `false` means the default, which is off (SDK 10 prints `false`).

To turn it on for the whole solution, set `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>` in the `Directory.Build.props` at the solution root, merged into the file if one exists (never overwritten). Then read the property again with `-getProperty` on each project.

## 3. Style check commands

| Purpose | Command | Reading the result |
| --- | --- | --- |
| Verify only | `dotnet format <solution> --verify-no-changes` | Exit `0` when nothing would change. Exit **`2`** when it would (not `1`). The output lists the rule IDs and files. |
| Build with style rules | `dotnet build <solution> --no-incremental` | Style diagnostics (`IDE...`) appear only when `EnforceCodeStyleInBuild` is `true` and the rule has severity `warning` or `error`. |

Output text is localized to the SDK's language. Read the exit status and the rule IDs, not the messages. Whitespace findings carry no `IDE` rule ID: they are reported with the word `WHITESPACE`.

Plain `dotnet format --verify-no-changes` shows only whitespace findings when the style rules are at `suggestion` severity, so it cannot give the per-rule drift. To measure the drift for each style rule, raise the severities to `warning` in a throwaway copy of the repository and run `dotnet format style <solution> --verify-no-changes` there. Never raise them in the user's files just to measure.

The verify-only output has several lines per file (a one-file sample printed fourteen lines). To count files, count distinct file paths, never lines. The solution file is `.slnx` on SDK 10 and later, and `.sln` before.

## 4. Making a rule fail

A style rule fails the build only when its severity is `error`, or when its severity is `warning` and warnings are treated as errors.

Set a rule to fail on its own, in `.editorconfig`:

```ini
[*.cs]
csharp_style_namespace_declarations = file_scoped:error
dotnet_diagnostic.IDE0161.severity = error
```

Both forms work. Use `dotnet_diagnostic.<ID>.severity` when you want to name the diagnostic explicitly. The option form (`option = value:severity`) is honored at build time from .NET 9 onward.

Common choices to offer (the user picks): file-scoped namespaces (`IDE0161`), braces always (`IDE0011`), readonly fields (`IDE0044`), import order (`dotnet_sort_system_directives_first`, `dotnet_separate_import_directive_groups`).

Do not set a whole category to `error`. Choose rules one by one.

## 5. Gradual options

| Option | How | Cost |
| --- | --- | --- |
| Rule as warning only | Severity `warning` without failure on warning | Violations are reported but not blocked. Needs a date or condition to tighten. |
| Per-folder severity | A nearer `.editorconfig` raises severity to `error` for new code folders | Needs care with `root = true`. Uneven protection. |
| One rule at a time | Raise severities as drift for each rule reaches zero | Slower. |

## 6. Reformatting

`dotnet format <solution>` (without `--verify-no-changes`) rewrites files. Check the number of files first with verify-only. Do it as a separate change.

The plain command also applies code fixes for style diagnostics (it added braces and `readonly` in a sample), which changes structure and not only spacing. Offer two steps, each with its own approval:

1. `dotnet format whitespace <solution>`: only whitespace. In a sample it reformatted indentation and spacing and left braces, `readonly` and the namespace form untouched. Verify with `dotnet format whitespace <solution> --verify-no-changes`.
2. `dotnet format style <solution>`: applies the style code fixes. Verify with `dotnet format style <solution> --verify-no-changes`. Look at the diff before accepting.

## 7. Pitfalls and limits

- **Style is off in the build by default.** A project with a detailed `.editorconfig` and no `EnforceCodeStyleInBuild` has style checked only in editors.
- **Verify-only exits with `2`**, so a script that only treats `1` as failure misses it.
- **A handful of style rules run only in the Visual Studio IDE** and never in the command-line build, even with the property on.
- **Warnings as errors** also turns on audit warnings from restore. If you rely on that to fail style rules, remember the side effect, or set the severities to `error` instead (preferred here).
- **Line endings:** `end_of_line` in `.editorconfig` can disagree with git's line-ending settings and cause a flood of violations on a machine with different defaults. Check the git setting before adding the rule.
- **Generated code** is mostly exempt from analyzers, and tools can emit code that violates your rules. Do not edit generated files.

## 8. Verified on

2026-10-12, run in a throwaway sample (SDK 10.0.401): with a style rule configured as `warning` and `EnforceCodeStyleInBuild` unset, the build exited `0` and reported no style diagnostic; `dotnet format --verify-no-changes` exited `2` and listed `IDE0011` and `IDE0161`; with the property on, both appeared as warnings (exit `0`); with failure on warning, they became errors (exit `1`); with the severity set to `error` and no failure on warning, `IDE0161` failed the build (exit `1`) and a rule set to `suggestion` did not report. Microsoft Learn, overview of .NET source code analysis (enabling style analysis on build).

Also run in a throwaway sample (same SDK): `dotnet format whitespace --verify-no-changes` exited `2` and listed only whitespace findings, `dotnet format style --verify-no-changes` exited `2` and listed `IDE0011`, `IDE0044` and `IDE0161`, applying `dotnet format whitespace` changed only spacing and indentation, and a one-file verify-only run printed fourteen lines.

Re-run in an eval pass on 2026-10-12 (same SDK): `-getProperty:EnforceCodeStyleInBuild` printed `false`; in a 60-file sample with the rules at `suggestion`, plain `dotnet format --verify-no-changes` exited `2` with whitespace findings only and `dotnet format style --verify-no-changes` exited `0`, and in a copy with the rules raised to `warning` the per-rule drift appeared (`IDE0011`, `IDE0044`, `IDE0161`).

Not verified in this pass: the `dotnet format analyzers` subcommand, applying `dotnet format style`, the effect of `end_of_line` against git settings, and SDKs older than 9.
