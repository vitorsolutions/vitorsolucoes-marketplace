---
name: clean-architecture-audit
description: >
  Audits an EXISTING .NET solution against Clean Architecture's dependency rule — Domain must not
  depend on Application, Infrastructure, or Presentation; Application must not depend on
  Infrastructure or Presentation; EF Core/DbContext types must not leak outside Infrastructure;
  business logic sitting in controllers/endpoints instead of Domain or Application; outer-layer DTOs
  or framework types leaking into Domain entities. Use this whenever the user asks to "audit this
  project for Clean Architecture", "check if we're violating the dependency rule", "essa solução
  respeita Clean Architecture?", "audita a arquitetura desse projeto", "tem violação de camada
  aqui?", or wants to know how far an existing codebase has drifted from a layered architecture
  before deciding what to fix. Builds its findings from the real project/assembly reference graph
  (.csproj ProjectReference entries) and actual namespace/using dependencies inside the code — never
  infers a layer's correctness from a folder or project being named "Domain" or "Application", since
  a correctly named folder can still contain a wrong-direction dependency. Every finding is
  classified as Observed, Hypothesis, Risk, or Recommendation, matching the evidence-graded format
  used by this plugin's other advisory skills. Strictly read-only and advisory — never moves,
  renames, or edits a single file, never restructures projects, never creates a new project. Do NOT
  use this skill to scaffold Clean Architecture layers into a brand-new project (that's
  minimal-api-scaffold, for a project that doesn't exist yet) or to generate the architecture test
  project that guards against future regressions (that's netarchtest-guard-scaffold, which writes
  files — this skill never does). Also not the right skill for EF Core query performance
  (ef-core-query-performance-review) or migration safety (ef-migration-safety-review).
---

# Clean Architecture Audit

## Your role

You are auditing whether an existing .NET solution actually obeys Clean Architecture's dependency
rule — inner layers (Domain, then Application) must never depend on outer layers (Infrastructure,
Presentation) — not whether it *looks* like it does. A solution with projects named `MyApp.Domain`,
`MyApp.Application`, `MyApp.Infrastructure`, and `MyApp.Api` can still violate the rule badly if
`MyApp.Domain` references Entity Framework Core, or if a use-case class in `MyApp.Application`
calls `HttpContext.Current`. Names are a hint about intent, never evidence of compliance — the only
evidence that counts is the actual reference graph and the actual `using` statements inside the
code.

This is a read-only audit. It never moves a file, never edits a `.csproj`, never creates a project.
If the user wants the violations fixed, that's a separate, deliberate step they take after reading
this report — possibly with your help, but not as an automatic continuation of this skill.

## Step 1 — Map the solution's actual layers

1. Find the `.sln` file (or, if there isn't one, treat each top-level project folder as a candidate
   layer). List every `.csproj` in the solution.
2. For each project, read its `<ProjectReference>` entries — this is the real, compiler-enforced
   dependency graph, independent of what anyone intended. Build this graph before looking at a
   single class name.
3. Classify each project into a Clean Architecture layer (Domain, Application, Infrastructure,
   Presentation/API, or "other" — test projects, shared kernels, etc.) using a combination of:
   - Its position in the reference graph (a project nothing else references but that references
     several others is very likely Infrastructure or Presentation; a project many others reference
     but which itself references nothing internal is very likely Domain).
   - Its name, only as a secondary signal, never as the deciding one.
   - What it actually contains (entities and business rules vs. `DbContext`/repositories vs.
     controllers/endpoints) — skim representative files rather than relying on the folder name
     alone.

   If a project's role is genuinely ambiguous from evidence alone, say so in the report as an
   **Observed** ambiguity rather than silently guessing a layer for it. An audit that force-fits
   every project into a clean label it doesn't actually have is less useful than one that admits
   uncertainty.

## Step 2 — Check the dependency rule at the project level

Using the reference graph from Step 1, check every edge against the Clean Architecture dependency
rule (dependencies point inward only: Presentation → Application → Domain, and Infrastructure →
Application/Domain, never the reverse):

- **Domain referencing Application, Infrastructure, or Presentation** — Risk, always. This is the
  most severe violation possible under Clean Architecture, since it means the layer meant to be
  independent of everything else now depends on something volatile.
- **Application referencing Infrastructure or Presentation** — Risk. Application should depend only
  on abstractions (interfaces) that Infrastructure implements, never on Infrastructure directly.
- **Domain or Application referencing a framework/ORM package directly** (e.g. `Microsoft.EntityFrameworkCore`,
  `Microsoft.AspNetCore.*`, a specific message-broker SDK) via `<PackageReference>` — Risk, reported
  separately from project-to-project violations, since a `PackageReference` in the wrong layer is
  just as much a dependency-rule violation as a `ProjectReference` is, and is easy to miss if you
  only look at project references.

Every check in this step is **Observed** — it comes directly from `.csproj` contents, not inference.

## Step 3 — Check for violations inside the code, not just the project file

A project can pass Step 2's project-reference check and still violate the dependency rule inside
individual files, because C# doesn't require every `using` to correspond to a `ProjectReference` if
the type is reachable transitively, and because logic can be misplaced within a layer that's
otherwise correctly wired. Look for:

- **EF Core types (`DbContext`, `DbSet<T>`, `[Table]`/`[Column]` attributes, LINQ-to-Entities query
  logic) appearing outside Infrastructure** — Risk. This is the single most common Clean
  Architecture violation in real .NET codebases: a `DbContext` injected directly into a controller,
  or a Domain entity decorated with EF Core mapping attributes.
- **Business logic (validation, calculations, state transitions, branching on domain state) living
  in a controller or Minimal API endpoint handler instead of being delegated to Application/Domain**
  — Hypothesis, not Observed: judging what counts as "business logic" versus legitimate
  presentation-layer concern (input shaping, status codes) requires reading the actual code, and
  reasonable engineers can disagree on a borderline case. State the specific method and what it
  does, and let the user judge whether it crossed the line.
- **DTOs, view models, or request/response contracts from Presentation leaking into Domain method
  signatures** (a Domain entity or service method that takes or returns a Presentation-layer type)
  — Risk. This inverts the dependency rule at the method-signature level even if the project
  reference graph looks clean.
- **Domain entities exposing public setters or anemic structure with all logic living in
  Application services** — Hypothesis, and only worth flagging if the user's stated goal is a
  richer Domain model; report it as an observation about the current style, not an automatic defect,
  since an anemic-but-consistent model is a legitimate (if debated) choice some teams make
  deliberately.

Don't attempt to scan every file in a large solution line by line — sample representative files per
project (entities, a few services, a few controllers/endpoints) and say explicitly what was sampled
versus what wasn't, so the report doesn't imply exhaustive coverage it doesn't have.

## Step 4 — Produce the report

Structure the report as:

1. **Layer map** — which project was classified as which layer, and the confidence/evidence behind
   each classification from Step 1.
2. **Project-level dependency rule violations** (Step 2) — one entry per violating edge, each
   showing the specific `ProjectReference` or `PackageReference` responsible.
3. **Code-level violations** (Step 3) — one entry per finding, with file/type reference, evidence
   classification (Observed/Hypothesis/Risk/Recommendation), why it matters concretely (not a
   generic "this breaks Clean Architecture" line — state what actually becomes hard to change or
   test as a result), and a specific recommendation (e.g. "introduce an `IOrderRepository`
   interface in Application, implement it in Infrastructure, and inject the interface instead of
   `DbContext` directly").
4. **What was checked and found clean** — layers/edges that passed, so the report reads as a
   completed audit rather than only a list of problems.

Close by pointing out, if the user wants to prevent these violations from creeping back in after
they're fixed, that a separate skill (`netarchtest-guard-scaffold`) can generate an architecture
test project that fails the build automatically on future regressions — but don't generate it
yourself, and don't move or edit a single file as part of this audit.
