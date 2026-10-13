# .NET stack reference for harness-banned-apis

## 1. Detection markers

`*.sln`, `*.slnx`, `*.csproj`. Look for an existing `Microsoft.CodeAnalysis.BannedApiAnalyzers` package reference and any `BannedSymbols.txt`.

## 2. The mechanism

The Roslyn banned API analyzers package turns a text file of forbidden symbols into diagnostics.

| Element | Detail |
| --- | --- |
| Package | `Microsoft.CodeAnalysis.BannedApiAnalyzers`, added as a `PackageReference` with `PrivateAssets` set to `all` (the `dotnet add package` command writes this) |
| Policy file | `BannedSymbols.txt`. One entry per line. |
| Wiring | The file must be included as an additional file in each project that should be checked: `<AdditionalFiles Include="BannedSymbols.txt" />`. For a repository-wide list, put the package reference and the `AdditionalFiles` item (pointing at the root file) in `Directory.Build.props`. |
| Diagnostic | `RS0030`, with the entry's message in its text. |
| Default severity | **Warning**. A warning does not fail the build. |

## 3. Making a ban fail the build

Either of these makes the ban a gate:

- Set the severity in `.editorconfig`, **inside a section**:

  ```ini
  root = true

  [*.cs]
  dotnet_diagnostic.RS0030.severity = error
  ```

  The same line written without a section header is ignored: the build keeps reporting a warning and exits `0`. Merge into an existing `.editorconfig` (add the line to its `[*.cs]` section) instead of creating a second file, and keep `root = true` only if the file is the top one. After the change, build and confirm the exit status is non-zero.
- Treat warnings as errors for the project (`TreatWarningsAsErrors`), which is the job of `harness-sensors`.

Setting the severity for this one diagnostic is the more targeted option, because it does not change anything else.

## 4. Entry syntax

`<documentation ID>;<message>`. Lines starting with `//` are comments.

| Kind | Form | Example |
| --- | --- | --- |
| Property | `P:<Type>.<Name>` | `P:System.DateTime.UtcNow;Use TimeProvider.GetUtcNow()` |
| Method | `M:<Type>.<Name>(<parameter types>)` with full type names | `M:System.Threading.Thread.Sleep(System.Int32);Use Task.Delay` |
| Constructor | `M:<Type>.#ctor` (add the parameter list to ban one overload) | `M:System.Net.Http.HttpClient.#ctor;Use IHttpClientFactory` |
| Generic method | Type parameters written with a double backtick and the count | ``M:Microsoft.EntityFrameworkCore.RelationalQueryableExtensions.FromSqlRaw``1(...)`` |
| Type | `T:<Type>` | |

Parameter types use full documentation names: `System.String`, not `string`. Generic arguments use braces: `System.Collections.Generic.IEnumerable{System.Object}`. Each overload needs its own line, and there is no wildcard for overloads.

## 5. Catalog of policies

| Policy | Entries | Relevant when |
| --- | --- | --- |
| Time from an injected clock | `P:System.DateTime.Now`, `P:System.DateTime.UtcNow`, `P:System.DateTimeOffset.Now`, `P:System.DateTimeOffset.UtcNow`, message pointing to `TimeProvider` | The project targets .NET 8 or later (where `TimeProvider` exists) |
| No blocking sleep | `M:System.Threading.Thread.Sleep(System.Int32)`, message pointing to `Task.Delay` | The project has asynchronous code |
| HTTP clients through a factory | `M:System.Net.Http.HttpClient.#ctor`, message pointing to `IHttpClientFactory` | The project uses dependency injection |
| Parameterized SQL only | `ExecuteSqlRaw`, `ExecuteSqlRawAsync` (on `RelationalDatabaseFacadeExtensions`), and `FromSqlRaw` (on `RelationalQueryableExtensions`), message pointing to the interpolated variants | `Microsoft.EntityFrameworkCore.Relational` is referenced |

Add one line per overload. The raw SQL overloads differ in their parameter lists, so list them from the version of the library the project uses.

To list the overloads of a symbol, ask the runtime or the package, never memory. For a type in the base library, a short throwaway program prints them as documentation IDs:

```csharp
foreach (var m in typeof(System.Threading.Thread).GetMethods().Where(m => m.Name == "Sleep"))
    Console.WriteLine($"M:{m.DeclaringType!.FullName}.{m.Name}({string.Join(",", m.GetParameters().Select(p => p.ParameterType.FullName))})");
```

For a package type, load the assembly from the version the project restored. Generic and array parameters need the braces and bracket forms from section 4, so check each printed ID by validating it (section 8). An entry whose overload was not listed is treated as unvalidated.

These are starting points. The user's own policies come first.

## 6. Finding existing uses

Search the source for the member name (for example `UtcNow`, `Sleep(`, `new HttpClient(`, `ExecuteSqlRaw`). Text search can miss aliases and extension-method forms, and can count unrelated members with the same name, so label the count approximate. The compiler is the authoritative count: after wiring the entry as a warning (with approval), the number of distinct `RS0030` locations is exact. Count file, line and column, not output lines, because each diagnostic is printed more than once.

## 7. Gradual options

| Option | How | Cost |
| --- | --- | --- |
| Keep the diagnostic as a warning | Do not set it to error yet | New uses are reported but not blocked. Needs a date or condition to tighten. |
| Strict only in new projects | Wire the file in the new projects only | Existing projects stay unprotected. |
| Per-folder severity | A nearer `.editorconfig` sets `RS0030` to `error` in new code folders | Needs care with `root = true` and folder layout. |

## 8. Validating entries

Run `dotnet build <solution> --no-incremental` (the solution file is `.slnx` on SDK 10 and later, `.sln` before) and look for `RS0030` at the use. Match the diagnostic code and the line. The message text is localized to the SDK language (the `error` and `warning` prefix and the code stay in English), so match the code, not the message.

The compiler prints each diagnostic more than once (a sample with two uses printed four lines). Count distinct file, line and column, never output lines.

For a symbol with no existing use, create the one temporary file described in the skill. Each entry needs one use that matches the exact overload: a use of a different overload does not prove the entry (a sample with a `Sleep(System.Int32)` entry reported the integer call and not the `TimeSpan` call). One use per listed overload.

## 9. Pitfalls and limits

- **A wrong signature is silent.** `M:System.Console.WriteLine(string)` used the C# keyword instead of `System.String` and banned nothing, with no error or warning.
- **Without the `AdditionalFiles` line the whole list is silent.** The package restores, the file exists, and no diagnostic appears. Always confirm that at least one entry fires.
- **A wired file that does not exist breaks the build** with `CS2001`. Wire the correct path.
- **Package version** is chosen by the package manager. Under central package management, the version belongs in `Directory.Packages.props`.
- **The ban matches symbols**, so reflection, dynamic invocation and code in other assemblies that call the symbol are not caught.
- **Generated code is checked too.** Unlike the built-in quality analyzers, this analyzer reported banned uses in a file with a `.g.cs` suffix and in a file with an `<auto-generated>` header. Code written by tools (migrations, designers) that uses a banned symbol will fail the check. Report those uses to the user. Do not edit generated files, and offer a path-scoped severity or an exclusion as the options.

## 10. Verified on

2026-10-12, run in throwaway samples (SDK 10.0.401, `Microsoft.CodeAnalysis.BannedApiAnalyzers` 5.6.0): `RS0030` reported as a warning with exit `0` by default and as an error with exit `1` after the `.editorconfig` severity change written inside a `[*.cs]` section (the same line without a section kept the warning and exit `0`); a build with two banned uses printed four `RS0030` lines, in the warning form and in the error form; the reflection listing printed both `Thread.Sleep` overloads and an entry for the `System.Int32` overload fired only on the integer call; entries for a property, a method with a parameter, and a constructor all fired and included their message; a `string` keyword entry fired nothing; removing the `AdditionalFiles` item silenced the list; a wired file that did not exist caused `CS2001`; a file with a `.g.cs` suffix and a file with an `<auto-generated>` header were both still reported; entries for `ExecuteSqlRaw` and `FromSqlRaw` (EF Core relational, including the generic form with a double backtick) fired.

Not verified in this pass: other package versions, F# and Visual Basic projects, and every overload of the raw SQL methods in other EF Core versions.
