# NetArchTest Guard Scaffold

Generates a dedicated architecture test project inside an existing .NET solution, using NetArchTest.Rules (or whatever the current best-maintained equivalent is), so a Clean Architecture dependency violation fails the build automatically instead of being caught by hand later — or not at all.

## What it is

Layer boundaries drift over time: someone adds "just one" reference from Domain to Infrastructure under deadline pressure, and nothing in the build stops it. This skill closes that gap by generating a real test project — added to the `.sln`, referencing the layers it needs to inspect — with fluent assertions like "Domain must not depend on Infrastructure" or "Domain must not reference `Microsoft.EntityFrameworkCore`" that run as part of the normal test suite.

It detects the solution's actual project names and dependency graph first, rather than assuming a fixed `Domain`/`Application`/`Infrastructure`/`Presentation` naming convention, and confirms its inferred layer mapping with the user before generating anything — an architecture guard built against a wrong assumption is worse than no guard, since it creates false confidence. It also detects the test framework and target framework already used elsewhere in the solution, so the new project fits the solution's existing conventions.

This is the one of the two Clean-Architecture-focused skills in this plugin that actually writes to the repository — it creates a project, adds package references, and generates test files. It never decides how to split an unlayered project into Clean Architecture layers in the first place; that has to already be settled (see `clean-architecture-audit` for the diagnostic step that usually precedes this one).

## When to use it

- Right after fixing Clean Architecture violations (possibly ones surfaced by `clean-architecture-audit`), to make sure they don't come back.
- When a team already trusts their current layering and wants that trust enforced by the build going forward, without re-auditing by hand every time.

Not the right skill for a one-off diagnostic of current violations (that's `clean-architecture-audit`, which only reports and never writes files) or for deciding the layer split itself.

## What it guarantees

- **Detects real project names and the actual dependency graph** before generating any rule — never assumes fixed layer names.
- **Confirms the inferred layer mapping and rule scope with the user** before writing anything, including any intentional exclusions (shared kernels, legacy modules mid-migration).
- **Matches the solution's existing conventions** — target framework and test framework are detected, not assumed.
- **Always validated** — runs `dotnet build` and `dotnet test` after generation; a failing generated rule is reported to the user rather than silently loosened to force a green result.
