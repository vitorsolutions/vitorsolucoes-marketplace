# Harness Banned APIs

Turns "do not use X, use Y" project policies into checks that fail, with a message that names the alternative, and proves that every entry really fires.

## Why this skill exists

Some problems are not defects a general analyzer can see. They are decisions the team has made: time comes from an injected clock, SQL goes through the parameterized API, HTTP clients come from a factory. A coding agent does not know these decisions unless something stops it. This skill makes them executable.

## What it does

- Detects the stack and any existing banned-API mechanism.
- Proposes policies from a catalog filtered by what the project uses, and asks for your own policies first.
- Counts the existing uses of each forbidden symbol before changing anything.
- Wires the mechanism into the project and agrees on the severity and on a gradual option when there are existing uses.
- Validates every entry against a real use, because a malformed entry bans nothing and reports nothing.

## Supported stacks

| Stack | Mechanism |
| --- | --- |
| .NET | The Roslyn banned API analyzers, with a policy file wired as an additional file |
| Python | Ruff's banned-import rule (`TID251`) and its `banned-api` table |

Each stack lives in a reference file under `references/stacks/`.

## What it will not do

- Add a policy you did not approve, or ban a symbol without an alternative message.
- Fix the existing uses, suppress a ban, or edit generated files.
- Overwrite or reorder an existing policy list.
- Commit or stage anything, or use the network without asking.

## When to use it

When you have internal rules of the type "never use X": "forbid DateTime.Now", "block raw SQL", "make the agent stop using this API".

## Limits

A ban matches a symbol, not an intention. It also blocks safe uses and misses a forbidden behavior reached through a different symbol. Every suppression mechanism silences a ban, so pair it with a guard against suppressions when that matters.
