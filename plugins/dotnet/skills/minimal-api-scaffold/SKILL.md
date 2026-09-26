---
name: minimal-api-scaffold
description: >
  Scaffolds a brand-new ASP.NET Core Minimal API project from scratch using the dotnet CLI, following
  current Microsoft and community best practices for the .NET SDK version actually installed on the
  machine. Use this whenever the user asks to "create a new Minimal API", "scaffold a new ASP.NET Core
  project", "start a new .NET Web API", "cria um novo projeto Minimal API", "monta um projeto ASP.NET
  Core novo", or wants to bootstrap a new .NET HTTP API and have it follow recommended structure and
  packages instead of the bare `dotnet new` output. Always checks whether the .NET SDK is installed
  before doing anything else, and always asks the user about database, authentication, API
  documentation, and versioning needs before generating code. Do NOT use this skill to modify,
  refactor, or add best practices to an EXISTING .NET project — it only creates new projects from an
  empty state. Also not the right skill for non-Minimal-API ASP.NET Core styles (MVC controllers,
  Razor Pages) unless the user explicitly wants the Minimal API hosting model, nor for choosing
  between architectural styles in the abstract — that's a job for the brainstorm or adr skills.
---

# Minimal API Scaffold

## Your role

You are creating a new ASP.NET Core Minimal API project from an empty state, using the real `dotnet` CLI on the user's machine — not writing files that merely look like a .NET project. Every step below produces an actual command execution or an actual file written to disk in the target directory, and the final step proves the result compiles.

Treat "best practices" as something to verify against current Microsoft guidance for the SDK version actually installed, not as a fixed checklist memorized once and never revisited — .NET's recommended Minimal API patterns (route grouping, typed results, OpenAPI support) have changed across recent releases, and what was current advice a few major versions ago is not necessarily current advice now.

## Step 1 — Verify the .NET SDK is installed

Run `dotnet --version` (or `dotnet --list-sdks` if you need to see every installed version). This check always comes first — there is no point asking the user about database or auth preferences for a project that can't be created yet.

- **SDK found:** note the version and proceed to Step 2. Keep the version in mind for Step 3 — the best-practices research is filtered by what's actually available, not by whatever is newest on the market.
- **SDK not found:** ask the user whether they want guidance on setting up the .NET SDK.
  - **If yes:** give step-by-step installation instructions suited to their operating system (detect it from the environment rather than assuming — Windows commonly via `winget install Microsoft.DotNet.SDK.<version>`, Linux via the distro's package manager or Microsoft's apt/dnf feed, macOS via `brew install dotnet` or the official installer). Never run an installation or configuration command yourself, even if the user seems to expect it — point them to the exact command and let them execute it, then ask them to confirm once it's done before continuing.
  - **If no:** stop here. Do not attempt to generate a project without a working SDK.

## Step 2 — Ask about project decisions before generating anything

Before running `dotnet new`, ask the user about the choices that actually change the shape of the generated project. Don't generate a generic project and hope it fits — a Minimal API with a database and JWT auth looks structurally different from a bare one, and re-doing the scaffold after the fact costs more than asking up front. At minimum, cover:

- **Persistence:** no database, or a specific one (SQL Server, PostgreSQL, SQLite, etc.) — this decides whether EF Core and a provider package get added.
- **Authentication/authorization:** none, JWT bearer, ASP.NET Core Identity, or an external provider — this decides middleware and package references.
- **API documentation:** built-in OpenAPI document generation, Scalar, Swashbuckle/Swagger UI, or none.
- **API versioning:** whether the project needs versioned routes from the start.
- **Project name and target directory.**

Ask only what's relevant — if the user already stated some of these in their request, don't re-ask, just confirm your understanding. Skip questions that don't apply (e.g., don't ask about database provider if they already said "no database").

## Step 3 — Ground the scaffold in current best practices

Before generating files, check current Microsoft guidance for Minimal API project structure and the packages chosen in Step 2, filtered to the SDK version detected in Step 1. If a documentation lookup tool is available, use it — don't rely purely on memorized conventions, since Minimal API guidance has shifted across .NET releases (route grouping via `MapGroup`, `TypedResults` for typed responses, built-in OpenAPI document generation, native rate limiting and output caching, etc.). If no lookup tool is available, say so explicitly and proceed using your best current knowledge, rather than silently presenting memorized conventions as freshly verified.

What you're looking for specifically: the recommended way to organize endpoints for a project of this size, the currently recommended OpenAPI/documentation approach for the detected SDK version, and any package that has been superseded or deprecated since your training data.

## Step 4 — Generate the project

1. Run `dotnet new webapi` with the flag that selects the Minimal API template for the detected SDK (the exact flag name has varied across SDK versions — verify it against the installed version rather than assuming), targeting the project name and directory from Step 2.
2. Add the packages the Step 2 answers require (EF Core + provider, authentication packages, documentation packages) via `dotnet add package`.
3. Reorganize the generated `Program.cs` so it stays maintainable as the API grows: extract endpoint registration into extension methods (e.g. `MapXxxEndpoints`) grouped by resource, instead of leaving every route inline in `Program.cs`. Keep `Program.cs` itself limited to composition — building the app, wiring middleware, and calling the endpoint-mapping extensions.
4. Set up environment-specific configuration (`appsettings.Development.json` alongside `appsettings.json`) if not already present from the template.
5. Wire in whatever Step 2 decided — connection string placeholders and `DbContext` registration for persistence, authentication middleware and scheme configuration for auth, the chosen documentation middleware.

Never invent a client name, internal hostname, or real connection string in generated code or comments — use clearly fake placeholders (`YourApp`, `localhost`, `Server=.;Database=AppDb;Trusted_Connection=True;`).

## Step 5 — Validate before declaring done

Run `dotnet build` in the generated project directory. A scaffold that doesn't compile is not a finished task, regardless of how closely it followed best practices on paper.

- **Build succeeds:** if it's reasonable to do so quickly, also run the project and hit a basic endpoint (or the built-in health/OpenAPI endpoint) to confirm it actually starts, then stop it.
- **Build fails:** fix the issue if it's a straightforward scaffold mistake (missing `using`, missing package reference). If the failure points to something more fundamental (e.g., an incompatible package version for the detected SDK), tell the user what failed and why instead of silently working around it with an unrelated change.

Report back what was generated, which decisions were made in Step 2, and confirm the build result — don't just say "done."
