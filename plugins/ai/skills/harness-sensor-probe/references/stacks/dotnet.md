# .NET stack reference for harness-sensor-probe

## 1. Detection markers

`*.sln`, `*.slnx`, `*.csproj`. Read `Directory.Build.props` and the project file to know whether default compile items are on.

## 2. Placement rules

- Put the probe inside an existing **non-test** project that is part of the solution, at the project root or in a source folder. Prefer an application or library project.
- Name it `HarnessSensorProbe.cs`. If that path exists, do not touch it: use `HarnessSensorProbe2.cs`, then `3`, and so on, and change the class name to match. Never use a `.g.cs` or `.designer.cs` suffix, or the word "auto-generated", in an alternative name or header (see the generated-code point below). If the alternative path also exists, ask.
- The file must be compiled. SDK-style projects include `*.cs` files by default. If the project sets `EnableDefaultCompileItems` to `false`, the probe will not be compiled: report **inconclusive**.
- Analyzers skip generated code. Do not name the file with a generated suffix (`.g.cs`, `.designer.cs`) and do not put the words "auto-generated" in the header comment, because a header like that marks the file as generated and every rule is skipped.
- A `Directory.Build.props` or `.editorconfig` can turn rules off for specific paths. If the probe lands in such a path, say so in the report.

## 3. Probe snippets

One file with one class holds all snippets so a single build tests them together.

```csharp
// Deliberately defective sample created by a harness probe. It is removed after the check.
using System.Data.Common;
using System.Security.Cryptography;

namespace <ProjectRootNamespace>;

public class HarnessSensorProbe
{
    public void Query(DbConnection connection, string userInput)
    {
        using var command = connection.CreateCommand();
        command.CommandText = "SELECT * FROM t WHERE owner = '" + userInput + "'";
        command.ExecuteNonQuery();
    }

    public byte[] Hash(byte[] data) => MD5.HashData(data);

    public int UnsafeLength(string? value) => value.Length;
}
```

Use the project's root namespace for the placeholder. The snippets use only types from the base class library, so they compile without extra packages.

| Snippet | Control targeted | Expected code |
| --- | --- | --- |
| `Query` (SQL built from input) | Security rules | `CA2100` |
| `Hash` (broken hash algorithm) | Security rules | `CA5351` |
| `UnsafeLength` (dereference of a possibly null value) | Nullable reference checking | `CS8602` |

The nullable snippet only fires if nullable checking is on. If it does not fire and the project has it off, report it as **silent** with that explanation.

## 4. Running the check with guaranteed cleanup

Run the project's verification command (usually `dotnet build <solution> --no-incremental`) inside a construct that removes the probe afterwards, for example in a POSIX shell:

```sh
PROBE="<project folder>/HarnessSensorProbe.cs"
OUT="${TMPDIR:-${TEMP:-/tmp}}/probe_out.txt"
( trap 'rm -f "$PROBE"' EXIT
  cp "<the probe snippet file kept outside the repository>" "$PROBE"
  dotnet build <solution> --no-incremental > "$OUT" 2>&1; echo "exit=$?" )
```

The output goes to a temporary folder, not the repository, so the probe stays the only file the run adds. `<solution>` is the actual file name: a `.slnx` file on SDK 10, a `.sln` file on older SDKs. The `trap` removes the file on a normal exit or an interrupt, but not on SIGKILL or a power loss, so confirm afterwards that the probe is gone (step 5 of the workflow).

In PowerShell, use `try { ... } finally { Remove-Item $probe -ErrorAction SilentlyContinue }`, with the output also written to a temporary folder. On Windows with Git Bash the `trap` form worked in the sample, and the PowerShell form was not run. Do not delete `bin` or `obj` outputs, which are normal build artifacts.

Read the result from the exit status and from lines that carry the probe's file name and a diagnostic code. The lines use the form `<file>(<line>,<col>): error|warning <CODE>: ...`. Diagnostic messages are localized to the SDK's language, so match the code and the `error` or `warning` word, not the message.

Each diagnostic can appear more than once in the output. Count distinct file, line and code.

## 5. Classifying results

| Observation | Class |
| --- | --- |
| Code appears as `error` and the exit status is non-zero | enforced |
| Code appears as `warning` and the exit status is zero | reported |
| Code does not appear and the build compiled the file | silent |
| The build failed on a compile error unrelated to the probe before analysis, or the file was not compiled | inconclusive |

If the probe's diagnostics appear as errors but the command the agent runs exits with success (for example a wrapper that ignores the status), report the mismatch as a bypass.

If the baseline (the run without the probe) already exits with failure, do not classify by exit status: every control is **inconclusive**, even when the probe's diagnostics appear as errors in a build that kept analyzing (independent projects are built in parallel and can still report). Report the probe's diagnostics, matched by code and by the probe's path, as a separate observation, and ask for the baseline to be made green first. A diagnostic with the same code in other files of the baseline is attributed by file path, never by code alone.

## 6. Pitfalls and limits

- Incremental builds can skip analysis. Always use `--no-incremental` for the probe run.
- A restore may need the network on a fresh machine. Ask before the first build there.
- Warnings treated as errors also cover restore-time audit warnings, so the baseline can fail for reasons unrelated to the probe. Attribute by the probe's file path.
- The probe covers three defect classes. Rules for architecture, banned APIs, and style need their own checks.

## 7. Verified on

2026-10-12, run in a throwaway sample project (SDK 10.0.401) with `AnalysisModeSecurity` set to `All` and failure on warning enabled: the clean baseline built with exit `0`, the probe build exited `1` with `CA2100`, `CA5351` and `CS8602` reported as errors, the file was removed by a shell `trap`, and the next build exited `0` again.

Also confirmed in the same sample: a file with the same defects but an `<auto-generated>` header comment, and another with a `.g.cs` suffix, produced no diagnostics and the build exited `0`. Both generated-code exemptions are real.

In a later pass, the cleanup form of section 4 (probe copied in, output written to a temporary folder, probe removed by the `trap`, `.slnx` solution) was run in a throwaway sample with Git Bash on Windows: the probe was gone afterwards and the only new files were the normal `bin` and `obj` outputs. The default of that sample reported `CS8602` as a warning with exit `0`, which is the **reported** class.

Not verified in this pass: the PowerShell cleanup form, SIGKILL during the run, projects with `EnableDefaultCompileItems` disabled, and other SDK versions.
