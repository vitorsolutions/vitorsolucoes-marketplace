# GitHub Actions reference for harness-ci-pipeline

## 1. Detection markers

Workflow files in `.github/workflows/*.yml` (or `.yaml`), and a remote whose host is `github.com`. One file per workflow. A new file is the default, and an existing workflow is reviewed and patched, never replaced.

## 2. Resolving current versions

Never copy an action version from memory or from an example. Resolve each one when you generate the file:

```sh
gh api repos/<owner>/<repo>/releases/latest --jq '.tag_name'
gh api repos/<owner>/<repo>/git/ref/tags/<tag> --jq '.object.type + " " + .object.sha'
```

If the object type is `commit`, the printed SHA is the commit. If it is `tag` (an annotated tag), dereference it with `gh api repos/<owner>/<repo>/git/tags/<sha> --jq '.object.sha'`. Both cases were seen in tooling generally, and only the `commit` case occurred in the samples.

Then read the action's input names from its `action.yml` at that commit before using them:

```sh
gh api "repos/<owner>/<repo>/contents/action.yml?ref=<sha>" --jq '.content' | base64 -d
```

Pinning policy (ask the user): **pin every third-party action to the full commit SHA**, with the tag in a trailing comment, because a tag can be moved. First-party actions (under the `actions` organization) can follow the same rule for consistency, or use the tag if the user prefers. A pinned file needs someone to update it.

If `gh` is not available or not logged in, ask the user for the versions. Do not guess.

## 3. Skeleton

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  verify:
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    env:
      RESULTS: ${{ github.workspace }}/test-results
    steps:
      - uses: actions/checkout@<sha> # <tag>
        with:
          persist-credentials: false
      # ... the stack steps ...
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@<sha> # <tag>
        with:
          name: test-results
          path: ${{ env.RESULTS }}
          retention-days: 7
          if-no-files-found: warn
```

Why each piece:

- **`permissions: contents: read`** limits the token to reading the repository.
- **A fixed runner version** (`ubuntu-24.04`) instead of a moving label keeps the environment reproducible. Say the user must update it when the version is retired.
- **`timeout-minutes`** keeps a hung step from running for hours.
- **`concurrency` with `cancel-in-progress`** cancels superseded runs of the same branch. Ask before using it on a branch where every run matters.
- **`persist-credentials: false`** on checkout keeps the token out of the local git configuration after checkout.
- **`if: always()`** on the upload keeps the evidence when a step fails. The retention is short on purpose, because artifacts count against storage.
- **Triggers on both push to the main branch and pull requests** avoids running twice for the same commit on a feature branch.

The job-level `env` block defines `RESULTS`, the results folder inside the workspace, which the test step writes to, the count guard reads, and the upload step publishes. A folder inside the workspace is the case that was linted; the stack file's test command writes there through `$RESULTS`. Define other names reused across steps (the solution file) in the same block, and refer to them in `run:` steps as shell variables rather than inserting `${{ }}` expressions into scripts. The linter warns about untrusted values inserted directly into scripts. The results folder shows up as untracked in a local run, so the project can add it to `.gitignore`.

## 4. The count guard

Copy `scripts/assert_tests_ran.py` to `.github/scripts/assert_tests_ran.py`, unchanged, and call it after the test step:

```yaml
      - name: Fail when no tests ran
        run: python3 .github/scripts/assert_tests_ran.py "$RESULTS"
```

The hosted Ubuntu runners include Python 3. If the user chooses a runner without it, add a setup step.

## 5. The linter

`actionlint`, run for example with `uv run --with actionlint-py actionlint .github/workflows/ci.yml`. It exits `0` on a clean file and non-zero with findings. In the samples, both templates passed with exit `0`, and a deliberately bad workflow was rejected for an untrusted expression inserted in a script and for an undefined variable. Fix every finding.

Linting does not prove that the workflow runs. Only a real run does.

## 6. Pitfalls and limits

- **A required status check** has to be configured in the repository settings before merging is blocked on it. This skill does not change settings. Say so.
- **Workflows triggered by pull requests from forks** run with reduced permissions and no secrets. The skeleton needs none.
- **Caching** is left out on purpose because it is an optimization that can hide missing dependencies. Add it only if the user asks.
- **Action inputs differ between versions.** Read them from `action.yml` at the pinned commit.
- **Artifact quotas** can be exhausted by other repositories of the same account, which makes uploads fail. Keep retention short.
- **Windows and macOS runners** need different shells and path syntax. The skeleton assumes Linux.
- **A step with `continue-on-error`, or a script that ignores an exit status, is a silent failure.** The default shell of a `run` step fails on the first failing command.

## 7. Verified on

2026-10-12. Releases and commit SHAs were resolved with `gh` for `actions/checkout`, `actions/setup-dotnet`, `actions/setup-python`, `astral-sh/setup-uv` and `actions/upload-artifact`, and the input names used (`global-json-file`, `persist-credentials`, `retention-days`, `if-no-files-found`, `python-version`, and others) were read from each `action.yml` at the pinned commit. Both workflow templates passed `actionlint` 1.7.12, and the commands of each template were run locally in the same order on sample projects, with the count guard reading their real result files.

Not verified in this pass: a real run on GitHub, annotated tags, reusable workflows, self-hosted runners, and other operating systems.
