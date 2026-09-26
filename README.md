# Vitor Soluções — Claude Code Marketplace

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin%20Marketplace-5A67D8?style=flat-square)](https://github.com/vitorsolutions/vitorsolucoes-marketplace)
[![Plugins](https://img.shields.io/badge/plugins-4-2563eb?style=flat-square)](./plugins)
[![Skills](https://img.shields.io/badge/skills-14-2563eb?style=flat-square)](./plugins)

A [Claude Code](https://claude.com/claude-code) plugin marketplace maintained by **Vitor
Soluções**, following the official plugin marketplace format. Each domain is an independent
plugin that can bundle skills, agents, hooks, and commands.

It ships with a local, browsable catalog site (Astro, in `catalog/`) that is a **pure projection**
of this repository's files — adding a plugin, skill, or doc updates the catalog on the next build,
with nothing duplicated by hand.

## What's in the box

```
.
├── .claude-plugin/marketplace.json   # plugin registry
├── plugins/
│   ├── docs/                         # documentation domain: business docs, ADR, PRD, TRD
│   ├── ideation/                     # pre-decision exploration domain: brainstorm
│   ├── dotnet/                       # .NET domain: scaffolding, EF Core, observability, audits
│   └── ai/                           # AI-tooling domain: agent-creator
├── catalog/                          # Astro catalog site (pure projection of the repo)
├── LICENSE
├── CLAUDE.md                         # repo guide for Claude Code
└── README.md
```

## Plugins

| Plugin | What it does |
|---|---|
| [`docs`](./plugins/docs) | Documentation domain. Bundles `business` (business-facing documentation generated from a source code repository — rules, processes, and integrations in plain language, without code snippets or technical tables) and the design document skills `adr`, `prd`, and `trd`, each following a fixed template. |
| [`ideation`](./plugins/ideation) | Pre-decision exploration domain. Bundles `brainstorm` (explores multiple distinct ideas or options around a topic before any decision has been made, without writing files — once an idea is settled, it feeds into the `docs` plugin's `adr` or `prd` skill). |
| [`dotnet`](./plugins/dotnet) | .NET domain. Bundles `minimal-api-scaffold` (scaffolds a brand-new ASP.NET Core Minimal API project via the `dotnet` CLI, following current Microsoft and community best practices for the SDK version actually installed), `ef-migration-safety-review` (static-analysis review of the latest EF Core migration for operational risk — missing defaults, irreversible drops, disguised renames, incomplete rollback — before it's applied to a real database), `aspnet-observability-setup` (adds vendor-neutral logging/tracing/metrics via OpenTelemetry to an existing ASP.NET Core project, detecting and completing only what's missing), `ef-core-query-performance-review` (evidence-graded diagnosis of EF Core/LINQ query performance the user points to, comparing implementations or confirming hypotheses like N+1 via a disposable SQLite in-memory context when static analysis isn't enough), `appsettings-secrets-audit` (audits appsettings*.json/launchSettings.json for hardcoded secrets, cross-referenced against git tracking status so real exposure is never confused with a gitignored placeholder), `nuget-dependency-audit` (audits NuGet dependencies for known vulnerabilities, deprecated packages, and outdated versions via the dotnet CLI's native checks — no external API calls), `clean-architecture-audit` (audits an existing solution's real project-reference graph against the Clean Architecture dependency rule), and `netarchtest-guard-scaffold` (generates a NetArchTest-based test project that fails the build automatically on a layering regression). |
| [`ai`](./plugins/ai) | AI-tooling domain. Bundles `agent-creator` (engineers Claude Code agents/subagents — creating, reviewing, and refactoring them — starting from whether an agent is even the right mechanism versus project instructions, a skill, a command, a hook, an MCP tool, or an existing agent, then covering responsibility scope, delegation description quality, least-privilege tools, model choice, autonomy, and known anti-patterns when one is warranted). |

## Installing skills

`npx skills add <package>` doesn't understand "plugin" as a filter — it flattens every
`SKILL.md` it finds under the given path and lets you narrow the result with `--skill`, or
you can point it straight at a plugin's `skills/` folder to install everything in that
domain.

Install every skill in one domain:

```bash
npx skills add vitorsolutions/vitorsolucoes-marketplace/plugins/docs/skills --full-depth
```

```bash
npx skills add vitorsolutions/vitorsolucoes-marketplace/plugins/ideation/skills --full-depth
```

```bash
npx skills add vitorsolutions/vitorsolucoes-marketplace/plugins/dotnet/skills --full-depth
```

```bash
npx skills add vitorsolutions/vitorsolucoes-marketplace/plugins/ai/skills --full-depth
```

Or install one specific skill by name:

```bash
npx skills add vitorsolutions/vitorsolucoes-marketplace --full-depth --skill agent-creator
```

Or install every skill in the repo:

```bash
npx skills add vitorsolutions/vitorsolucoes-marketplace --full-depth
```

## Running the catalog site

```bash
cd catalog
npm install
npm run dev        # http://localhost:4321
npm run build      # generates dist/ + Pagefind search index
npm run preview    # serves dist/ with search working
```

## Adding a new plugin

```
plugins/<domain>/
├── .claude-plugin/plugin.json    # { name, version, description, author }
├── skills/<skill>/SKILL.md       # minimal frontmatter: name, description
└── docs/<skill>.md               # 1st paragraph = card blurb; the rest = detail page
```

1. Create the plugin folder following the format above.
2. Register it in `.claude-plugin/marketplace.json`.
3. Run the catalog (see above) to confirm the new plugin/skill shows up correctly.

Important rules:

- **A skill's name is unique across the whole repository** (it becomes the URL `/skills/<name>`).
- A skill **without** `docs/<skill>.md` shows up in the catalog flagged as *undocumented* — it
  also works as a completeness dashboard.
- The loader reads files at a **fixed depth**; anything deeper (`.venv`, snapshots, eval outputs)
  is ignored.

See `CLAUDE.md` for the full guide Claude Code itself follows in this repository.

## License

[MIT](./LICENSE) © Vitor Soluções
