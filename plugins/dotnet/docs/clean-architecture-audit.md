# Clean Architecture Audit

Audits an existing .NET solution against Clean Architecture's dependency rule, using the real project reference graph and actual code — never the names of folders or projects — as evidence.

## What it is

A solution with projects named `Domain`, `Application`, `Infrastructure`, and `Api` can still violate Clean Architecture badly: a `DbContext` injected straight into a controller, a Domain entity decorated with EF Core mapping attributes, an Application service that calls into Infrastructure directly instead of through an abstraction. This skill builds the actual `ProjectReference`/`PackageReference` graph from every `.csproj` in the solution, classifies each project into a layer based on that graph (not its name), and checks every edge against the Clean Architecture dependency rule — inner layers must never depend on outer ones. It then samples representative code inside each project to catch violations that don't show up at the project-reference level, such as EF Core types leaking outside Infrastructure or business logic sitting in a controller instead of Application/Domain.

Every finding is labeled Observed, Hypothesis, Risk, or Recommendation — a project-reference violation is Observed fact; whether a specific method "counts" as misplaced business logic is a Hypothesis the user is asked to judge. The skill never edits, moves, or renames a single file; it only reports.

## When to use it

- Before deciding whether (and how) to refactor an existing project toward Clean Architecture.
- After a team believes it already follows Clean Architecture, to verify that belief against actual evidence instead of folder names.
- As a first pass before generating a permanent guard against regressions (see `netarchtest-guard-scaffold`).

Not the right skill for scaffolding a brand-new project's layers from scratch, generating the automated test project that guards a boundary going forward, or reviewing EF Core query performance or migration safety — those are separate skills in this plugin.

## What it guarantees

- **Evidence-first layer classification** — a project's layer is inferred from its actual dependency graph and sampled code, with name used only as a secondary signal, never the deciding one.
- **Project-level and code-level checks** — catches both wrong-direction `ProjectReference`/`PackageReference` edges and violations that only show up inside the code (EF Core leakage, misplaced business logic, Presentation DTOs leaking into Domain signatures).
- **Every finding labeled by evidence strength** — Observed, Hypothesis, Risk, or Recommendation, never presented as more certain than the evidence supports.
- **Read-only and advisory** — never edits, moves, or restructures a single file. The decision to act on any finding stays with the user.
