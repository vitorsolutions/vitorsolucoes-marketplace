# Eval fixtures

Two small, invented codebases used by the eval cases of the `ticket-engineering` skills. They
implement the same fictional subscription-billing domain in two stacks, so the same ticket can be
run against either and the skills' stack-agnostic claim is actually exercised.

- `dotnet-billing/` — C# / .NET
- `python-billing/` — Python

Each skill's `evals/evals.json` references these folders through its `files` field, relative to the
skill root (`../../fixtures/<stack>`).

Everything here is made up: the company, the domain rules, the names, and every value that looks
like a credential or a personal detail in the eval prompts. The code is deliberately incomplete and
is not meant to build or run — it exists to be read. It contains a few intentional mismatches
between documented and implemented behavior; they are not marked in the source, because finding
them is what the evals measure. Don't "fix" them.
