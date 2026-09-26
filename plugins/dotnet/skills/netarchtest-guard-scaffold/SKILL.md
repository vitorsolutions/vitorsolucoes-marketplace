---
name: netarchtest-guard-scaffold
description: >
  Generates a dedicated architecture test project (using NetArchTest.Rules, or whatever equivalent
  package is currently the best-maintained choice for the installed .NET SDK) inside an EXISTING
  .NET solution, with fluent assertions that fail the build whenever a Clean Architecture dependency
  rule regresses — e.g. Domain referencing Infrastructure, Application referencing Presentation, or
  EF Core types leaking outside Infrastructure. Use this whenever the user asks to "add architecture
  tests", "stop us from breaking Clean Architecture again", "create a guard against layer
  violations", "cria um projeto de teste de arquitetura", "garante que ninguém quebre a separação de
  camadas", or already knows their layering is correct (or has just fixed it, possibly via
  clean-architecture-audit) and wants that correctness enforced automatically going forward instead
  of re-checked by hand every time. This is the one of the two Clean-Architecture-focused dotnet
  skills that actually WRITES to the repository — it adds a new test project to the .sln, adds
  package references, and generates test files; if the user wants a report instead of a new project,
  they want clean-architecture-audit, not this skill. Detects the solution's actual project names
  and layer boundaries first — it does not assume a fixed Domain/Application/Infrastructure/
  Presentation naming convention, since real solutions vary. Does NOT decide how to split an
  unlayered project into Clean Architecture layers in the first place — that decision must already
  be made (or in progress) before this skill runs; it only guards a boundary that already exists.
  Always validates the generated test project with `dotnet build` and runs the new tests with
  `dotnet test` to confirm they compile and pass against the current (presumably compliant) code.
---

# NetArchTest Guard Scaffold

## Your role

You are adding a permanent, automated guard against Clean Architecture regressions to a solution
that already has (or is in the process of establishing) layer boundaries — not deciding what those
boundaries should be. Unlike `clean-architecture-audit`, which only reports, this skill writes a
real test project to disk and touches the `.sln`. Treat that difference seriously: confirm you
understand the solution's actual layering before generating anything, since a wrong assumption here
doesn't just mislead a report, it ships an assertion that's wrong and will either false-fail forever
or (worse) pass while allowing exactly the kind of violation it was meant to catch.

## Step 1 — Detect the solution's real layers, don't assume names

1. Find the `.sln` and list every `.csproj` referenced by it.
2. For each project, read its `<ProjectReference>` entries to build the actual dependency graph —
   the same evidence-first approach `clean-architecture-audit` uses. Do not assume the layers are
   named `Domain`/`Application`/`Infrastructure`/`Presentation`; real solutions use `Core`,
   `Business`, `Data`, `Api`, `Web`, company-specific prefixes, etc.
3. Propose your inferred mapping (which project is Domain-equivalent, Application-equivalent, and so
   on) to the user and confirm it before proceeding, unless the user's own request already stated
   the mapping unambiguously (e.g. they named the exact projects). Generating dependency-rule
   assertions against the wrong project is worse than not generating them, since a false sense of
   protection is worse than no protection.

## Step 2 — Confirm scope with the user

Ask, or infer from context if already answered, which rules the guard project should enforce. Don't
silently generate every rule imaginable — confirm the set, since some solutions intentionally allow
exceptions (e.g. a shared `Common`/`SharedKernel` project referenced by everything). At minimum,
cover:

- The core dependency-direction rules from Step 1's layer mapping (inner layers must not reference
  outer ones).
- Whether to also guard against specific framework leakage (e.g. "Domain must not reference
  `Microsoft.EntityFrameworkCore`" as a package-level rule, not just a project-level one) — this is
  usually the most valuable single rule to add, since it catches the most common real-world
  violation.
- Any known, intentional exceptions the user wants excluded from the rules (a specific
  cross-cutting project, a legacy module mid-migration, etc.) — bake these in explicitly as
  documented exclusions in the generated test, not as a silent gap.

## Step 3 — Ground the scaffold in the current package ecosystem

Before generating code, verify (via a documentation/package lookup tool if available) that
`NetArchTest.Rules` is still the best-maintained choice for the .NET SDK version this solution
targets, rather than assuming it from memory — architecture-testing packages in the .NET ecosystem
have shifted over time (forks, successors, or better-maintained alternatives can emerge). If a
lookup tool isn't available, say so explicitly and proceed with `NetArchTest.Rules` as the
well-established default, rather than silently presenting an unverified assumption as freshly
checked.

Detect the target framework(s) of the existing projects (`<TargetFramework>` in their `.csproj`s)
and the test framework already in use elsewhere in the solution (xUnit, NUnit, MSTest — check
existing test projects before defaulting to one), so the new project matches the solution's existing
conventions instead of introducing a second, inconsistent test framework.

## Step 4 — Generate the architecture test project

1. Create a new test project (e.g. `dotnet new xunit` or matching whatever framework Step 3
   detected) named consistently with the solution's naming convention (e.g.
   `<SolutionPrefix>.ArchitectureTests`).
2. Add it to the `.sln`.
3. Add the `NetArchTest.Rules` package reference (or the alternative chosen in Step 3) plus the
   detected test framework's packages.
4. Add project references from the new test project to every project the rules need to inspect —
   typically all layers being guarded.
5. Generate one test method per rule confirmed in Step 2, using descriptive test names that state
   the rule in plain terms (e.g. `Domain_Should_Not_Depend_On_Infrastructure`,
   `Domain_Should_Not_Reference_EntityFrameworkCore`), each asserting on `result.IsSuccessful` and
   including `result.FailingTypeNames` in the failure message so a future violation is immediately
   actionable instead of just "a test failed somewhere."
6. Add a short comment at the top of the generated file explaining that this project exists to catch
   Clean Architecture regressions automatically and pointing to `clean-architecture-audit` for a
   one-off deeper look — a future maintainer who's never heard of either skill should be able to
   understand why the file exists from the file itself.

Never invent a client name, internal hostname, or real namespace in generated code or comments — use
the solution's actual (already-public-in-this-repo) project/namespace names, since this project is
being generated inside the user's real repository, not as a documentation example.

## Step 5 — Validate before declaring done

1. Run `dotnet build` on the solution. A guard project that doesn't compile protects nothing.
2. Run `dotnet test` scoped to the new project. Every generated rule is expected to **pass** against
   the current code — if the solution's layering was accurate going in, these assertions should be
   green immediately, confirming both that the test project works and that the current code is
   actually compliant with what it asserts.
   - **A generated test fails:** this means either the Step 1 layer mapping was wrong, or the
     solution has an existing violation that was missed (possibly one `clean-architecture-audit`
     would have caught first). Report this to the user rather than silently loosening the rule to
     make it pass — weakening a newly created guard to avoid a red test defeats the purpose of
     building it.
3. Report back exactly which rules were generated, which projects they cover, the build/test result,
   and any known exclusions baked into the rules from Step 2 — don't just say "done."
