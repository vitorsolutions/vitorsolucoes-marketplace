# .NET stack reference for harness-test-baseline

## 1. Detection markers

`*.sln`, `*.slnx`, `*.csproj`. A project is a test project if it references `Microsoft.NET.Test.Sdk` (or sets `IsTestProject`) and a framework package. Common frameworks: xUnit (`xunit`), NUnit (`NUnit`), MSTest (`MSTest` or `MSTest.TestFramework`). Follow the one already in the repository.

The reference tests used a template whose project is built on the VSTest platform (`Microsoft.NET.Test.Sdk`). Projects built on the newer Microsoft Testing Platform can use different options and different exit statuses. Check how the project is set up before applying the commands below.

## 2. The test command

`dotnet test <solution>` (the solution file is `.slnx` on SDK 10 and later, and `.sln` before; both are accepted).

| Result | Exit status |
| --- | --- |
| Tests ran and passed | `0` |
| Tests ran and at least one failed | `1` |
| **Zero tests ran** (a test project with no tests) | **`0`** |
| **The solution has no test project at all** | **`0`** |

The last two are the point of this skill: a passing status does not mean tests ran.

Output text is localized to the SDK's language. Never parse it.

Capture the exit status on its own. A pipe such as `dotnet test ... | tail` reports the status of the last command in the pipe, so a failing run looks successful. Redirect the output to a file, or read the first command's status (`PIPESTATUS[0]` in bash).

## 3. Structured output

```
dotnet test <solution> --logger "trx;LogFileName=<name>.trx" --results-directory <temporary directory>
```

The TRX file contains a `Counters` element with the totals:

```xml
<Counters total="1" executed="1" passed="1" failed="0" ... />
```

Read `total`, `executed`, `passed` and `failed`. A run with zero tests still writes the file, with `total="0"`. A solution with no test project writes no TRX file at all, so a missing file in a run that exited `0` means nothing ran. The same holds when the results directory was never created.

`dotnet test <solution> --list-tests` prints the test names, but its header text is localized, so use it only to see names, not to count.

**The counts cannot tell a placeholder from a real test.** The template's empty `Test1` is reported as `total="1" executed="1" passed="1"`. After reading the counts, open the test source files and look for test methods with no assertion (an empty body, or a body that only returns). Do not classify the suite as usable on the counts alone: if every executed test is a placeholder, report the suite as effectively **empty** and say why.

Skipped tests count in `total` but not in `executed`: a run with one skipped and one normal test reported `total="2" executed="1"`, and `notExecuted` stayed `0`. Compare `total` with `executed`, and do not rely on `notExecuted` to find skips.

## 4. Making an empty run fail

The VSTest-based command has no built-in minimum. Options, to offer to the user:

- A short script in CI or in the agent's definition of done that reads the TRX `total` and `executed` values and fails when `executed` is zero. This is the portable option and uses only the structured output above.
- For projects on the Microsoft Testing Platform, check that platform's documentation for an option that fails when fewer than a given number of tests run. It was not verified here.

## 5. Creating a minimal test project

| Step | Command |
| --- | --- |
| Create | `dotnet new xunit -n <Name>.Tests -o tests/<Name>.Tests` (use the template that matches the framework in use. Other templates were not verified) |
| Add to the solution | `dotnet sln <solution> add tests/<Name>.Tests` |
| Reference the code under test | `dotnet add tests/<Name>.Tests reference <project>` |

**The xUnit template generates a placeholder test with an empty body.** It passes and checks nothing. Do not count it as coverage. Replace it with a real test, or remove it. If it stays, say so in the report.

## 6. Pitfalls and limits

- A test project is not built or run by a solution-level command if it is not in the solution.
- Test projects with a build error make the command fail before any test runs. Classify it **not runnable**, not failing.
- Integration tests can need a database or a service. Look for the signs before running (see the skill's step 1: connection strings in `appsettings*.json` or environment files, a compose file, a test fixture that starts a container) and ask.
- A restore can need the network on a fresh machine.
- A single run does not reveal flaky tests.
- Parallel test runs can interact through shared state. Do not read a one-off failure as a code defect without a second look.

## 7. Verified on

2026-10-12, run in throwaway samples (SDK 10.0.401, xUnit template with `Microsoft.NET.Test.Sdk`): the template's single empty test passed with exit `0`; a project with no tests exited `0`, printed that no tests were available, and wrote a TRX with `total="0"`; a solution with no test project exited `0` and wrote no TRX file; a failing assertion exited `1`; a run with one skipped and one normal test exited `0` with `total="2" executed="1"`; with one test the TRX reported `total="1" executed="1" passed="1"`, which is also what the placeholder gives; `dotnet test` on an `.slnx` solution with no test project exited `0`; a piped command reported the last command's status (bash); the template's `UnitTest1.cs` contains an empty `Test1` method.

Not verified in this pass: NUnit and MSTest templates, Microsoft Testing Platform projects and their options, and test projects that target several frameworks.
