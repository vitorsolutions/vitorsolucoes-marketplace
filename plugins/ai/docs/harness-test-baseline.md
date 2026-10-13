# Harness Test Baseline

Establishes whether a repository has a test command that means something: it runs, it fails when a test fails, and it does not pass when no test ran.

## Why this skill exists

"The tests pass" only matters if tests ran. Several common setups exit with success when the suite is empty, when the solution has no test project, or when every test is skipped. A coding agent that reads that status as proof gets a green light for nothing. The default template for a new test project even ships with an empty test that passes.

## What it does

- Detects the stack and the test framework already in use.
- Runs the tests, with your permission, and reads the executed count from structured output, never from localized text.
- Classifies the suite as usable, failing, empty, all-skipped, absent, not runnable, or unknown.
- Explains what the exit status does and does not prove.
- Offers a guard that fails when nothing executed, and, with approval, creates the minimal test structure.

## Supported stacks

| Stack | Covered |
| --- | --- |
| .NET | `dotnet test`, TRX counters, the empty-suite and no-test-project cases, the template placeholder |
| Python | `pytest` exit statuses, JUnit counters, the empty and all-skipped cases |

Each stack lives in a reference file under `references/stacks/`.

## What it will not do

- Add a placeholder test that passes without checking anything.
- Edit, skip, ignore or delete an existing test to turn the suite green.
- Run tests that need shared or remote systems without asking.
- Write tests for specific behavior beyond one you name, measure coverage, or set up CI.
- Commit or stage anything.

## When to use it

Before relying on tests as a definition of done: "does the test command mean anything", "check that the tests actually run".

## Limits

A passing suite proves that these tests pass, not that the code is correct or that the important behavior is tested. Tests that depend on external systems can behave differently elsewhere, and a single run does not reveal flaky tests.
