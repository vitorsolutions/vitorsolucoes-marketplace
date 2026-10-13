---
name: harness-test-baseline
description: >-
  Establishes whether a repository has a test command that means something: it runs, it fails
  when a test fails, and it does not pass when no tests ran. Detects the stack and the test
  framework in use, runs the tests with permission, reads the number of tests that actually
  executed from structured output instead of localized text, and classifies the suite as usable,
  empty, all-skipped, failing, absent or not runnable. Scaffolds a test project only with approval
  and never adds a placeholder test that passes without checking anything. Currently supports
  .NET and Python. Use when the user asks to "check that the tests actually run", "set up tests
  for the agent", "does the test command mean anything", "why does dotnet test pass with no
  tests", "verificar se os testes realmente rodam", "criar a base de testes do projeto", "o
  comando de teste passa sem testes", or before relying on tests as part of a definition of done.
  Do NOT use it to write tests for specific behavior, to measure coverage, or to set up CI
  (harness-ci-pipeline).
---

# Harness test baseline

## What this skill does

"The tests pass" only means something if tests ran. Several common setups exit with success when the suite is empty, when no test project exists, or when every test is skipped. A coding agent that treats that exit status as proof gets a green light for nothing. This skill finds out what the test command really does and fixes the gap that matters: a suite that cannot fail.

Vocabulary:

- **Test command**: the command the agent runs to execute tests.
- **Executed count**: how many tests actually ran, read from structured output.
- **Suite states**:
  - **usable**: at least one test ran, none failed, and the command exited with success.
  - **failing**: tests ran and some failed.
  - **empty**: the command exited with success but zero tests ran.
  - **all-skipped**: tests exist but none executed.
  - **absent**: there is no test project or test configuration.
  - **not runnable**: the command could not run (missing tool, failed restore, failed build).
  - **unknown**: not evaluated, with the reason.

## Hard rules

- Never add a test that passes without checking anything just to turn the suite green. A placeholder is worse than an empty suite because it looks like coverage.
- Never edit, skip, ignore, or delete an existing test to make the suite pass.
- Ask before running tests. They can be slow, use the network or a database, write files, or change data.
- Never run tests that you have reason to think touch shared or remote systems. Ask what they need first.
- Write result files outside the repository (a temporary folder), and tell the user where.
- Never commit, push, or stage files. Never install packages without asking.
- Report counts from structured output only, never from text that changes with the tool's language.

## Workflow

### 1. Detect the stack and the test setup

Find the markers in each stack reference under `references/stacks/` and read only the matching pack. No matching pack: say the stack is not supported yet, explain the idea in concept, and change nothing.

Find: the test projects or configuration, the framework in use, where tests live, and how the test command is run today (scripts, CI, an existing agent guide).

Also look for signs that tests need an external system before asking to run them: connection strings, environment files, a compose file, fixtures that start a service. Report what you found when you ask.

### 2. Run and read the result

With the user's permission:

1. Run the test command with the structured-output option from the pack, writing results to a temporary location.
2. Record the exit status.
3. Read the executed count and the passed, failed and skipped counts from the structured output.
4. Open the test sources and check that the executed tests assert something. Counts cannot tell an empty placeholder from a real test.
5. Classify the suite.

If the test command cannot run, classify it **not runnable**, say why, and stop there. Do not fix the environment unless asked.

If the user declines to run the tests, or they need a shared system the user does not approve, classify the suite **unknown** and give the reason.

Record the exit status separately from the output: a pipe hides it.

### 3. Explain what the result means

State plainly what the exit status does and does not prove. For example: "the command exits with success, but zero tests ran, so a passing status proves nothing here".

If a template placeholder test is present (a test with no assertions), say it is a placeholder and do not count it as coverage. If every executed test is a placeholder, the suite is effectively **empty**, even when the counts say otherwise.

### 4. Propose the next step

- **usable**: nothing to build. Suggest how to make an empty or all-skipped run fail (see the pack), because a suite can become empty later.
- **failing**: report the failures. Do not touch the tests. Ask whether the baseline is known to be red.
- **empty or all-skipped**: explain, and propose either a real test or a guard that fails when nothing runs, or both. If `harness-ci-pipeline` is available, its `scripts/assert_tests_ran.py` is such a guard: it reads TRX or JUnit results and fails when zero tests executed or no result file exists. Otherwise use the check described in the stack pack.
- **absent**: propose the minimal structure (see step 5).
- **not runnable**: report the blocker.

### 5. Create the test structure (only with approval)

Follow the test framework already in use in the repository. If there is none, ask which one to use. Show the files to create and where, then apply.

Create the project structure and its wiring to the code under test. For the first test, ask the user for one real behavior to check (a public function, an endpoint, a rule). Write a test that fails if that behavior breaks. If the user cannot name one, leave the suite without a test, say that its state is **empty**, and do not invent one.

### 6. Confirm

Run the test command again (with permission) and read the executed count. If the suite is not usable, say so.

### 7. Report

| Item | Result | Evidence |
| --- | --- | --- |
| Framework | | |
| Test command | | exit status |
| Executed / passed / failed / skipped | | counts from structured output |
| Suite state | | |

Then say what changed (files), what did not, the guard that makes an empty run fail (if the user accepted one), and the limits below.

## Known limits to state

- A passing suite proves that these tests pass. It does not prove the code is correct or that important behavior is tested.
- This skill does not measure coverage or test quality.
- Tests that depend on external systems may behave differently in other environments.
- A single run does not reveal flaky tests.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers and how to recognize the framework
2. The test command and how to read its exit status
3. Structured output: how to get it and how to read executed, passed, failed and skipped counts
4. What exits with success when nothing ran
5. How to make an empty or all-skipped run fail
6. How to create the minimal test structure, and what the template generates
7. Pitfalls and limits
8. Verified on (date, and what was not re-verified)
