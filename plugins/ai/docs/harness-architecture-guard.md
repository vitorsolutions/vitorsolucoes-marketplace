# Harness Architecture Guard

Turns the dependency rules between a project's layers or modules into automated checks that fail, so a coding agent cannot quietly reach across an architectural boundary.

## Why this skill exists

A coding agent takes the shortest path to a working result, and the shortest path often crosses a boundary: core logic starts using a framework type, an inner layer imports an outer one. Review does not scale with an agent's speed. This skill makes the boundary a check that fails the build.

## What it does

- Reads the real dependency structure of the code and asks you to confirm the intended layering. It never trusts folder names.
- Proposes a small set of rules (direction, library leak, independence), each with a stated reason, and measures what already breaks before adding anything.
- Creates the guard as new files only: a test project, or a configuration file for the import checker.
- Adds controls that stop a rule from passing because it looked at nothing: layers are scanned and not empty, forbidden names that belong to the project exist, and one real allowed dependency is visible.
- Proves every rule fires by planting a violation in a throwaway copy of the repository, then deletes the copy. A rule that cannot be proven this way is reported as written but not proven.
- Registers the new guard project in the solution (with your approval) and checks that its own tests show up in the result, because an unregistered guard is skipped silently.
- Records existing breaches in a list that can only shrink: new breaches fail, and a listed breach that is fixed must leave the list.

## Supported stacks

| Stack | Tool |
| --- | --- |
| .NET | `NetArchTest.Rules`, in a new test project that loads each layer by name |
| Python | `import-linter`, with layers and forbidden contracts in `pyproject.toml` |

Each stack lives in a reference file under `references/stacks/`.

## What it will not do

- Edit production code, move code, or add or remove project references or imports.
- Write a rule without a control that shows it can see code, or report a rule as working without proving it.
- Install packages or use the network without asking.
- Commit or stage anything.

## When to use it

When layering matters and an agent keeps crossing it: "enforce the dependency rule", "stop the domain from depending on infrastructure", "add architecture tests".

## Limits

The guard sees the dependencies the tool can analyze: compiled types or import statements. Dynamic loading, reflection, configuration-driven wiring and business logic in the wrong layer without a forbidden dependency are invisible to it. The agent can edit or delete the guard unless permission rules protect it. A passing guard means these rules hold, not that the architecture is good.
