# Azure Pipelines reference for harness-ci-pipeline

**Status: written from the Microsoft documentation and not validated by any tool.** No local linter for Azure Pipelines files was available. A schema check with a public third-party schema was attempted, and it rejected both a correct file and a deliberately wrong one, so it was discarded as unreliable. Say this to the user and tell them to run the pipeline once and read its errors.

## 1. Detection markers

`azure-pipelines.yml` at the repository root (or another YAML file referenced by the pipeline definition on the server), and a remote host under `dev.azure.com` or `visualstudio.com`. The pipeline is created on the server by pointing it at the file, which this skill does not do.

## 2. Resolving current versions

Tasks are referenced as `Name@major` (for example `UseDotNet@2`). Look up the current major version of every task in the Azure Pipelines task reference before using it, and do not rely on memory. The documentation also lists retired tasks and their replacements. If the user cannot say which versions are available on their agents, ask. Hosted images change over time, so a fixed image version is preferable to a moving label.

## 3. Skeleton

```yaml
trigger:
  branches:
    include:
      - main

pr:
  branches:
    include:
      - main

pool:
  vmImage: ubuntu-24.04

variables:
  results: $(Agent.TempDirectory)/test-results

jobs:
  - job: verify
    timeoutInMinutes: 30
    steps:
      - checkout: self
      # ... the stack steps ...
      - task: PublishTestResults@2
        displayName: Publish test results
        condition: succeededOrFailed()
        inputs:
          testResultsFormat: VSTest        # JUnit for JUnit-format files
          testResultsFiles: "**/*.trx"     # "**/*.xml" for JUnit
          searchFolder: $(results)

      - task: PublishPipelineArtifact@1
        displayName: Keep test results
        condition: succeededOrFailed()
        inputs:
          targetPath: $(results)
          artifact: test-results
```

### Stack steps for the skeleton

These replace the `# ... the stack steps ...` line. They use `script` steps so that the commands stay identical to the local ones (the stack files give the commands and the reasons). The task inputs were read on Microsoft Learn on 2026-10-12. **The snippets were not run on a server.**

.NET (read the SDK from `global.json`, so there is one source of truth for the version):

```yaml
      - task: UseDotNet@2
        displayName: Use the SDK pinned in global.json
        inputs:
          packageType: sdk
          useGlobalJson: true
      - script: dotnet restore <solution> --locked-mode
        displayName: Restore (locked)
      - script: dotnet build <solution> --no-restore --no-incremental
        displayName: Build
      - script: dotnet test <solution> --no-build --logger "trx;LogFileName=results.trx" --results-directory "$(results)"
        displayName: Test
      - script: dotnet format <solution> --verify-no-changes --no-restore
        displayName: Format check
```

`useGlobalJson` makes the task install the SDK that `global.json` asks for, honoring its `rollForward` policy. Check that the lock files exist before using the locked restore (see the .NET stack file). Put the count guard step of section 4 after the test step.

Python with `uv` (the interpreter version comes from the project's pin, which the task cannot read, so copy it into `versionSpec`):

```yaml
      - task: UsePythonVersion@0
        displayName: Use the pinned Python
        inputs:
          versionSpec: "<the version the project pins>"
      - script: python3 -m pip install "uv==<the uv version the project uses>"
        displayName: Install uv (pinned)
      - script: uv sync --locked
        displayName: Install (locked)
      - script: uv run ruff check .
        displayName: Lint
      - script: uv run ruff format --check .
        displayName: Format check
      - script: uv run pytest --junitxml="$(results)/junit.xml"
        displayName: Test
```

Keep only the tools the project uses (see the Python stack file) and put the count guard step after the test step. `UsePythonVersion@0` takes a version range, not a file, and does not download versions on a self-hosted agent.

Points taken from the documentation:

- **`trigger` and `pr`** are the continuous integration and pull request triggers.
- **`pool.vmImage`** selects a hosted image. A Ubuntu 24.04 image exists, and `latest` labels move over time.
- **`timeoutInMinutes`** on the job bounds it.
- **`condition: succeededOrFailed()`** makes a step run when an earlier step failed, unless the run was canceled. `always()` also runs after cancellation. Use the first for publishing results.
- **`PublishTestResults@2`** reads `VSTest` (which means TRX files) and `JUnit` among other formats. Its inputs are `testResultsFormat`, `testResultsFiles` and `searchFolder`.
- **`script`** runs with `cmd.exe` on Windows and Bash elsewhere. `bash` runs Bash on all platforms. A step fails when its script exits with a non-zero status.
- **`continueOnError`** turns a failure into a success for later steps. Never use it.
- **`Agent.TempDirectory`** is a temporary folder that is cleaned after each pipeline job and that tasks use to hold test results before they are published. The results folder lives there, outside the source tree, so no result file can be committed by accident.
- **`checkout: self`** checks out the repository. The skeleton leaves the option for keeping credentials after checkout out, so it keeps its default. The `checkout` documentation confirms that `persistCredentials` defaults to not leaving the token in the Git config.

## 4. The count guard

Copy `scripts/assert_tests_ran.py` to a folder in the repository (for example `.azure/scripts/`), unchanged, and call it after the test step:

```yaml
      - script: python3 .azure/scripts/assert_tests_ran.py "$(results)"
        displayName: Fail when no tests ran
```

Check that the hosted image has Python 3, and add the version-selection task (`UsePythonVersion@0`) if it does not.

## 5. SARIF publication (optional)

Azure Pipelines has no built-in view for SARIF, so there are three destinations. Ask which one:

- **Artifact named `CodeAnalysisLogs`** (default). The Microsoft documentation for the Microsoft Security DevOps extension says that Defender for Cloud monitors an artifact with this name for SARIF output, and that the optional SARIF SAST Scans Tab extension (installed on the organization by an administrator) shows SARIF results in the pipeline's Scans tab. Without either, the files are still downloadable from the run.
- **GitHub Advanced Security for Azure DevOps**: the `AdvancedSecurity-Publish@1` task, with `SarifsInputDirectory` (an absolute path) and an optional `Category`. It needs that product enabled on the repository, and the task page describes it as working with the Infrastructure-as-Code scanning tasks, so confirm it accepts compiler SARIF before relying on it.
- **Artifact with any other name**: the same as the first, without the integrations.

Variables, build and publishing for the default destination (these replace the plain `dotnet build` line of the .NET stack steps and go after the test step):

```yaml
variables:
  results: $(Agent.TempDirectory)/test-results
  sarif: $(Agent.TempDirectory)/sarif

      - script: mkdir -p "$(sarif)"
        displayName: Create the SARIF folder
      - script: dotnet build <solution> --no-restore --no-incremental -p:SarifDir="$(sarif)"
        displayName: Build
      # ... tests, count guard ...
      - task: PublishBuildArtifacts@1
        displayName: Publish SARIF
        condition: succeededOrFailed()
        inputs:
          PathtoPublish: $(sarif)
          ArtifactName: CodeAnalysisLogs
      - script: test -n "$(find "$(sarif)" -name '*.sarif' -print -quit)"
        displayName: Fail when no SARIF was written
```

Notes:

- `PublishBuildArtifacts@1` is the task the Microsoft page uses for the `CodeAnalysisLogs` artifact, so it is used here instead of the `PublishPipelineArtifact@1` step of the skeleton. Whether the integrations also read a pipeline artifact of the same name was not checked.
- The check runs after the publishing step on purpose: it fails the run without skipping the publication.
- The folder lives under `Agent.TempDirectory`, outside the source tree, like the test results.
- Paths inside the files are absolute paths of the agent. See the .NET stack file.

## 6. The linter

None was available. State that the file was **not validated** by a tool, and that the local run of its commands (section 7 of the skill workflow) is the only check performed.

## 7. Pitfalls and limits

- **Branch policies** make a pipeline required before merging. They are set on the server. This skill does not change them.
- **A task that publishes results automatically** (for example the .NET CLI task, for its own test command) makes a separate publishing step unnecessary or duplicated. Using `script` steps with the CLI, as in the skeleton, keeps the commands identical to the local ones, and needs the explicit publishing steps.
- **Variables and secrets** are defined on the server. The skeleton needs none.
- **Agent pools and images** differ by organization. A self-hosted agent may lack tools that hosted images carry.
- **Task input names change between versions.** Read the documentation page for the version that you use.
- **Templates and multi-stage pipelines** are outside this skill. The skeleton has one job.

## 8. Verified on

2026-10-12, against the Microsoft Learn documentation: `UseDotNet@2` (including `useGlobalJson`), `UsePythonVersion@0` (in the task list and in an example), `PublishTestResults@2` (inputs and the `VSTest` and `JUnit` formats), step conditions, the `script` and `bash` steps, the Ubuntu 24.04 image, and the pipeline-level `trigger`, `pr`, `pool` and job `timeoutInMinutes`. The commands of the .NET and Python templates were run locally in order (see the GitHub Actions reference).

The inputs used by the stack-step snippets (`UseDotNet@2`: `packageType`, `useGlobalJson`; `UsePythonVersion@0`: `versionSpec`) were read again on Microsoft Learn on 2026-10-12. The snippets as a whole were not run.

Also checked against the documentation in a later pass: `PublishPipelineArtifact@1` inputs (`targetPath`, and `artifact`, whose alias is `artifactName`) and the `checkout` step (`self` is the default, `persistCredentials` is off by default).

The `Agent.TempDirectory` predefined variable (a temporary folder cleaned after each job, used by tasks to hold test results before publishing) was read on Microsoft Learn on 2026-10-12. Using it as the `results` variable was not run on a server.

Section 5 (SARIF publication) was written on 2026-10-19 from Microsoft Learn: the `CodeAnalysisLogs` artifact name, the `PublishBuildArtifacts@1` usage and the optional SARIF SAST Scans Tab extension (Microsoft Security DevOps extension page), and the `AdvancedSecurity-Publish@1` task with `SarifsInputDirectory` and `Category` (code scanning with third-party tools, and the task reference). The snippet was **not run on a server and not validated by a tool**.

Not verified: the pipeline file itself on a server; Windows agents; templates; and the current task versions on any particular organization.
