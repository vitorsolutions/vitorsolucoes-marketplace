---
name: trd
description: Documents the CURRENT technical baseline of the project already open in the workspace — stack, architecture, folder structure, modules, routes, data model, non-functional requirements, external dependencies, testing/code-style/logging/auth patterns, and an index of its ADRs — at docs/trd.md, by reading the actual repository files (never by inference, external framework conventions, or assumption). Use this when the user asks to "generate the TRD", "document this project's technical baseline", "documenta a arquitetura atual desse projeto", or wants a snapshot of what the system technically *is* today. Do NOT use this to propose improvements, refactors, migrations, or future architecture — baseline only, current state only. Also not the right skill for recording a single decision (see adr) or a feature's behavior (see prd).
---

# TRD

## Your role

The repository already open in the workspace is the only source of truth. Read the actual code, config files, and folder structure — don't reach for what a typical project of this kind "usually" looks like, and don't fill gaps with framework conventions you happen to know from elsewhere. This document is a photograph of what exists, not a description of best practice.

Ignore commit history entirely — the TRD describes the current state, not how it got there.

## The verification discipline

Before writing any statement in the document, confirm it against a real file in the repository. This checking is your own internal reasoning — it does not appear in the output. The final document carries no source column, no `file:line` citations, and no assumption markers of the kind the adr and prd skills use. Those skills mark inferred lines because their source is a conversation that can't be re-checked mechanically; here the source is code sitting right there, so an unconfirmed claim isn't a judgment call to flag — it's just not something you get to write.

Concretely:

- If no file supports a statement, don't write it. Don't infer it, don't complete the gap with a plausible guess.
- Where the code doesn't define a value the template expects, write "Not defined" or "Not applicable" — never invent one.
- Whatever seems relevant but you couldn't confirm, don't put it in the document at all. Raise it to the user during review instead, as a separate note outside the file, so they can decide.

## Template

Reproduce this structure exactly — same headings, same order, same table columns. Don't number the headings or use all-caps titles. Write the whole document in English by default, unless the project's existing docs are in another language or the user asks for a different one — in that case translate headings and prose accordingly, keeping the same structure.

```
# TRD — <Project>

> Global technical document for the project. Low granularity: covers what is global and stable.
> Fine-grained rules live in ADRs.

## Stack

| Dimension | Value |

Rows: Primary language, Runtime/platform, Main framework, Database, Build tooling, Package manager.

## Architecture

### Architectural pattern

The layering pattern (router → service, or whatever it actually is) in 1-2 lines, and why — only if the "why" is something the code or its own docs actually state, not your own rationale for why it's a good pattern.

### Dominant folder structure

A 2-level tree in a code block, with a 1-line responsibility per folder.

### Main modules / layers

| Module | Responsibility |

### Routes

| Method | Route | Handler |

Split API and page routes into separate tables if the project has both.

### Data model

One table per entity/table, with columns: | Column | Type | Constraints/Default |

## Non-Functional Requirements

| Dimension | Requirement |

Always include these five rows, in this order: Performance, Availability/SLA, Scalability, Security, Observability. Where the code doesn't support a value for one, write "Not defined" — never omit the row.

## External Dependencies

| Service / System | Type | Relevant constraint | Owner |

Only services/systems that impose a real contract (e.g. PostgreSQL, a payment gateway). Don't list build-time libraries from the lockfile. If there are none, write "None".

## Standards

### Testing

| Item | Value |

Rows: Framework, Full command, Minimum coverage, Strategy.

### Code style

Bullets: Linter, Formatter, Naming conventions. Whatever doesn't exist: "Not applicable".

### Error handling

Short prose describing the actual pattern in use.

### Logging

Bullets: Format, Default level, Library.

### Authentication / authorization

Short prose — or "Not applicable".

## Global Decisions (ADRs)

| # | Title | Date | Status | Link |
```

## The "Global Decisions (ADRs)" table

Populate it by scanning the frontmatter of every file in `docs/adrs/` in this project — `adr_number`, the title from the ADR's `# ADR NNN: ...` heading, `created`, `status`, and a relative link to the file. This is a mechanical projection of files that already exist, not an inference, so build it fresh from what's on disk. If `docs/adrs/` doesn't exist or is empty, leave a single row: *(no ADR recorded yet)*.

This table uses the same scanning logic as the adr skill's post-write sync step — the two skills should always produce the same table for the same set of ADR files, whether the table was just refreshed incrementally by the adr skill or rebuilt from scratch here.

## Review before writing

Show the document to the user section by section before saving `docs/trd.md`. Separately — outside the document itself, in the conversation — list everything you noticed but couldn't confirm from the repository, so the user can decide whether it's worth adding by hand.
