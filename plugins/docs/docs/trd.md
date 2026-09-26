# TRD

Documents a project's current technical baseline — stack, architecture, data model, and operating standards — by reading its actual files, never by assumption.

## What it is

A TRD answers "what is this system, technically, today" — not what it should become. This skill reads the repository directly (code, config, folder structure) and writes a single `docs/trd.md` covering the stack, architectural pattern, folder structure, modules, routes, data model, non-functional requirements, external dependencies, and the team's testing/code-style/logging/auth conventions. Every statement has to be confirmed against a real file before it's written; where the code simply doesn't define something the template expects, the document says "Not defined" instead of guessing. Commit history and outside knowledge of "how projects like this usually work" play no role — only what's actually in the repository.

The document also carries a table indexing the project's ADRs, built by scanning `docs/adrs/` — the same mechanical logic the adr skill uses to keep that table in sync after each new decision.

## When to use it

- Establishing a technical baseline for a project that doesn't have one yet.
- Getting a new engineer, or a fresh Claude Code session, oriented on a codebase's current shape without reading it end to end.
- Refreshing the baseline after the codebase has changed enough that the existing TRD is stale.

Not the right skill for proposing improvements or future architecture (baseline only), a single decision (see the adr skill), or a feature's behavior (see the prd skill).

## What it guarantees

- **Every claim traceable to a real file** — nothing inferred, nothing borrowed from generic framework conventions.
- **"Not defined" instead of a guess** wherever the codebase doesn't specify something the template asks for.
- **A fixed template**: same headings, same tables, every time, so TRDs are comparable across projects.
- **An always-current ADR index**, cross-linked with the adr skill's own sync step.
