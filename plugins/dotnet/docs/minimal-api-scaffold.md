# Minimal API Scaffold

Scaffolds a brand-new ASP.NET Core Minimal API project from scratch using the real `dotnet` CLI, following current Microsoft and community best practices for the .NET SDK version actually installed on the machine.

## What it is

Running `dotnet new webapi` alone gets you a generic starting point, not a project shaped around the decisions that actually matter for a real API — persistence, authentication, documentation, versioning. This skill picks those decisions up front, checks current Microsoft guidance for the SDK version that's actually installed (Minimal API conventions have shifted across recent .NET releases), and only then generates the project: official template as the base, endpoints reorganized into extension methods instead of everything inline in `Program.cs`, and the packages the chosen decisions require.

It never assumes the environment is ready. Before anything else, it checks whether the .NET SDK is installed; if it isn't, it walks the user through installing it for their own operating system, but never runs the installation itself. And it never calls the job done at file-generation time — the last step always runs `dotnet build` to prove the result actually compiles.

## When to use it

- Starting a brand-new ASP.NET Core Minimal API project and wanting it to follow current best practices instead of the bare template output.
- Bootstrapping a project where the shape depends on real decisions — a database, authentication, API documentation, versioning — that should be settled before code is generated, not patched in afterward.

Not the right skill for adding best practices to a project that already exists — it only creates new projects from an empty state. Also not the right choice for MVC controllers or Razor Pages, or for deciding between architectural styles in the abstract (see the brainstorm skill for that).

## What it guarantees

- **Environment checked before anything else** — the .NET SDK's presence is verified first; if missing, the skill only guides the user through setup (OS-appropriate instructions) and never installs or configures anything on its own.
- **Decisions gathered before generation** — persistence, authentication, API documentation, and versioning needs are asked up front, so the generated project matches the real use case instead of a generic default.
- **Best practices grounded in the installed SDK version** — guidance is checked against the .NET version actually detected on the machine, not assumed to be the newest release on the market.
- **Compilation verified, not assumed** — the project is built (`dotnet build`) before the task is considered complete; a scaffold that doesn't compile is not a finished result.
