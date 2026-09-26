# CLAUDE.md

Guide for Claude Code in this repository.

## About this repository

This is the **Vitor Soluções** plugin marketplace for Claude Code, following the official plugin
marketplace format. Each domain is an independent plugin that can contain skills, agents, hooks,
and commands.

It ships with a local catalog site (Astro, in `catalog/`) that is a **pure projection** of the
repo's files — adding a plugin/skill/doc updates the catalog on the next build, with no duplicated
content.

## Structure

```
.
├── .claude-plugin/marketplace.json   # plugin registry
├── plugins/<domain>/
│   ├── .claude-plugin/plugin.json    # plugin manifest (name, version, description, author)
│   ├── skills/<skill>/SKILL.md       # skills (instructions the agent follows)
│   └── docs/<skill>.md               # catalog documentation for the skill
└── catalog/                          # local catalog site (Astro) — pure projection of the repo
```

## Skill format

`SKILL.md` with minimal frontmatter (`name`, `description`). Version/author live in `plugin.json`
and `marketplace.json`. The documentation shown in the catalog comes from `docs/<skill>.md` (the
first paragraph becomes the card blurb; the whole file becomes the detail page).

## Rules

- Skills live in `plugins/<domain>/skills/<name>/SKILL.md`; docs live in `plugins/<domain>/docs/<name>.md`.
- Version/author metadata lives in the domain's `plugin.json`.
- New skills go inside their corresponding plugin/domain.
- **A skill's name is unique across the entire repository** — the catalog uses the name as the URL
  (`/skills/<name>`), and the loader deliberately breaks the build on a duplicate between plugins.
- Every plugin listed in `marketplace.json` needs a matching folder with a `plugin.json`.
- Write all documentation, skill instructions, and code comments in English. Eval fixtures
  (`evals/evals.json`) are the one exception — they may stay in whatever language matches the
  real-world scenario they test.
- **This repository is public. Never commit identifiable data.** Eval fixtures, docs, and examples
  must not contain real client/partner/employer names, real local or network paths, internal
  identifiers from private codebases (namespaces, class/table/enum names), hostnames, URLs of
  internal systems, credentials, or personal data. Use invented placeholders (`Acme.Integracao`,
  "the partner") that keep the scenario realistic without identifying anyone.

## Current plugins

- **docs** — the documentation domain. See `plugins/docs/`. Skills:
  - `business` — generates business-facing documentation from a source code
    repository: business rules, processes, and integrations explained in plain language, without
    code or technical tables.
  - `adr` — architecture decision records.
  - `prd` — product requirements documents.
  - `trd` — technical requirements documents.

Any new documentation-related skill belongs to this plugin instead of a new domain.

- **ideation** — the pre-decision exploration domain. See `plugins/ideation/`. Skills:
  - `brainstorm` — explores multiple distinct ideas or options around a topic before any
    decision has been made, without writing files. Once an idea is settled, the user moves it
    into the `docs` plugin (`adr` or `prd`) to formalize it.

Any new ideation/exploration skill (divergent, pre-decision) belongs to this plugin instead of `docs`.

- **dotnet** — the .NET domain. See `plugins/dotnet/`. Skills:
  - `minimal-api-scaffold` — scaffolds a brand-new ASP.NET Core Minimal API project via the
    `dotnet` CLI, following current Microsoft and community best practices for the SDK version
    actually installed. Checks the environment first, asks about persistence/auth/documentation/
    versioning before generating, and validates the result with `dotnet build`.
  - `ef-migration-safety-review` — static-analysis review of the most recently generated EF Core
    migration for operational risk (missing defaults on new NOT NULL columns, irreversible drops,
    disguised renames, incomplete Down() rollback, blocking index creation) before it's applied to
    a real database. Never connects to a database, never edits the migration, never applies it —
    read-only and advisory.
  - `aspnet-observability-setup` — adds vendor-neutral observability (structured logging,
    distributed tracing, metrics via OpenTelemetry + OTLP) to an existing ASP.NET Core project.
    Detects existing instrumentation first and only completes what's missing; never hardcodes a
    specific backend, vendor SDK, endpoint, or credential.
  - `ef-core-query-performance-review` — evidence-graded diagnosis of EF Core/LINQ query
    performance for a query/method the user points to (never scans a project unprompted). Every
    finding is labeled Observed/Hypothesis/Risk/Recommendation; falls back to a disposable SQLite
    in-memory context only when static analysis can't confirm a hypothesis (e.g. N+1), always
    flagged as not equivalent to the project's real provider. Never edits code directly.
  - `appsettings-secrets-audit` — audits appsettings*.json/launchSettings.json for hardcoded
    secrets and insecure configuration, cross-referencing every finding against git tracking
    status (tracked vs. gitignored/local-only) before classifying it as real exposure risk.
    Evidence-graded (Observed/Hypothesis/Risk/Recommendation); read-only and advisory.
  - `nuget-dependency-audit` — audits NuGet dependencies (including transitive) for known
    vulnerabilities, deprecated packages, and outdated versions using the dotnet CLI's native
    `dotnet list package --vulnerable/--deprecated/--outdated` — no external API calls. Severity
    reported exactly as the CLI gives it; a clean result is reported as "no known advisories at
    the time of the check," never as a safety guarantee. Read-only and advisory.
  - `clean-architecture-audit` — audits an existing .NET solution against Clean Architecture's
    dependency rule, building the layer map from the real `.csproj` project/package reference
    graph and sampled code — never from folder or project names. Flags inner-to-outer layer
    references, EF Core types leaking outside Infrastructure, and business logic misplaced in
    Presentation. Read-only and advisory; never edits, moves, or restructures a file.
  - `netarchtest-guard-scaffold` — generates a dedicated architecture test project
    (NetArchTest.Rules, or the current best-maintained equivalent) inside an existing solution, so
    a Clean Architecture dependency-rule regression fails the build automatically. Detects the
    solution's real layer names and confirms the rule scope with the user before writing anything.
    The one Clean-Architecture-focused skill in this plugin that writes to the repository; always
    validates with `dotnet build`/`dotnet test`.

Any new .NET-focused skill belongs to this plugin instead of a new domain.

- **ai** — the AI-tooling domain: meta-skills for engineering the AI tooling itself, as
  opposed to skills that produce project deliverables (docs, .NET code, etc.). See
  `plugins/ai/`. Skills:
  - `agent-creator` — creates, reviews, refactors, and validates Claude Code
    agents/subagents. Checks first whether a request actually needs an agent at all
    (versus project instructions, `CLAUDE.md`, a skill, a command, a hook, an MCP tool, or
    an existing agent), and only designs/writes an agent when that's genuinely the right
    mechanism — covering responsibility scope, delegation description quality, least-
    privilege tool selection, model choice, autonomy boundaries, output contracts, overlap
    with other agents, and common anti-patterns (overly generic agents, duplicated
    responsibilities, duplicated skills, excessive tool grants, circular delegation, and
    more).

Any new AI-tooling/meta skill (agent engineering, and similar meta-concerns as they arise)
belongs to this plugin instead of a new domain.
