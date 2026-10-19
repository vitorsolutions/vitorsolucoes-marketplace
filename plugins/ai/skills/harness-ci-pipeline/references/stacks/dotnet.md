# .NET stack reference for harness-ci-pipeline

## 1. Detection markers

`*.sln`, `*.slnx`, `global.json`, `Directory.Build.props`, `packages.lock.json`. The solution file is the unit for every command.

## 2. Steps, in order

Each command is the one used locally. Where the project has lock files, use the locked variant.

| Step | Command | Notes |
| --- | --- | --- |
| Toolchain | The host's .NET setup step, reading the SDK version from `global.json` | Do not set a version in the pipeline when `global.json` pins it, so there is one source of truth. If the project has no pin, suggest `harness-reproducibility`. |
| Restore | `dotnet restore <solution> --locked-mode` | Fails when a lock file does not match the project. Without lock files, use `dotnet restore <solution>` and say that the run can resolve different versions. Before using the locked mode, check that the lock files exist (`packages.lock.json` next to the projects, and `RestorePackagesWithLockFile` set) and that git tracks them (`git ls-files` and `git check-ignore`): the locked mode exits `0` when there is no lock file, so it protects nothing and the run only looks locked. |
| Build | `dotnet build <solution> --no-restore --no-incremental` | `--no-incremental` makes sure analysis runs. Failure on warning is configured in the project (see `harness-sensors`), not here. |
| Build with SARIF (optional) | `dotnet build <solution> --no-restore --no-incremental -p:SarifDir=<sarif folder>` | Replaces the plain build step, it is not an extra step: a second build doubles the time. Needs the `SarifDir` wiring in `Directory.Build.targets` (see `harness-sensors`). Create the folder before the build, because the compiler does not and every project fails with `CS0016`. Keep it outside the source tree. |
| Test | `dotnet test <solution> --no-build --logger "trx;LogFileName=results.trx" --results-directory <results folder>` | Writes the structured results that the count guard reads. |
| Guard | `python3 <path>/assert_tests_ran.py <results folder>` | Fails when no test executed. A solution with no test project writes no result file and also fails the guard. |
| Style | `dotnet format <solution> --verify-no-changes --no-restore` | Exits `2` when something would change. Only include it if it passes locally and the project configures style (see `harness-code-style`). |
| Architecture | The project's architecture tests are part of the test step | They run with the other tests. If they live in a separate project outside the solution, add their command. |

Keep the results folder outside the source tree or in a folder that the project ignores.

## 3. Feeding the count guard

The guard reads `*.trx` files found in the folder (and lists and skips any XML file that is not a JUnit result, such as a coverage report; `--glob "*.trx"` restricts the search). It sums the `executed` count from the summary of each file. In the sample the TRX of a five-test run read `executed 5 of 5`, a zero-test run read `executed 0 of 0` and failed, and a solution with no test project produced no file and failed.

### Feeding the SARIF publication

Check that the wiring exists before adding the property: `dotnet msbuild <project> -getProperty:ErrorLog -p:SarifDir=<folder>` must print a path ending in `.sarif,version=2.1`. An empty value means the project does not emit SARIF, and the pipeline must not paper over that (point to `harness-sensors`). The build writes one file per project and target framework. The publishing step must fail when the folder has no `.sarif` file, because a wiring that stopped working would otherwise publish nothing and stay green.

## 4. Pitfalls and limits

- **Restore needs the network** on a runner without a package cache.
- **The SDK pin and the runner image.** If the pinned SDK is not on the runner, the setup step installs it. A strict roll-forward policy makes a missing SDK fail the run, which is intended.
- **Failure on warning also covers restore warnings.** Vulnerability warnings can fail a build that passed yesterday. That is a decision for `harness-sensors`. In CI it shows up as a failing restore with a package audit code.
- **Format check** needs the same style configuration as local runs, or the results differ.
- **Test projects excluded from the solution** are not run. The guard reports a zero count only if no project ran any test.
- **Output text is localized to the runner's language.** Read exit statuses and result files only.
- **Paths in the SARIF files are absolute** (`file:///` plus the runner's workspace path). Whether a code-scanning view maps them to repository files was not verified. Check it on the first real run.
- **Several SARIF runs from the same tool** (the compiler appears once per project and target framework) may be treated by a code-scanning service as the same analysis. Check the host's current rules on categories and merging on the first real run.

## 5. Verified on

2026-10-12, in throwaway samples (SDK 10.0.401): the commands of sections 2 and 3 ran in order on a sample solution and all exited `0`, the count guard read the real TRX file, and the guard failed on a zero-test TRX and on a missing file. The workflow around them passed `actionlint` (see the GitHub Actions reference).

2026-10-19 (SDK 10.0.402): the build with `-p:SarifDir=<folder>` wrote one SARIF 2.1.0 file per project and target framework, `-getProperty:ErrorLog` printed the expected path with the property and was empty without it, and a missing folder failed with `CS0016` (details in the `harness-sensors` .NET reference). The publishing steps in the host references were not run.

Not verified in this pass: a real run on a hosted runner, the locked restore inside the workflow (the sample had no lock files, so that step was run in the plain form for the local replay), multi-targeted projects, and test projects on the Microsoft Testing Platform.
