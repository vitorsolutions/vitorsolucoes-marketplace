---
name: adr
description: Formalizes ONE architectural decision that the user has already made during the current conversation into an immutable Architecture Decision Record (ADR) at docs/adrs/<NNN-slug>.md in the project the skill is invoked in. Also handles superseding a previous ADR when a decision changes, and syncing the "Global Decisions" table in the project's docs/trd.md if one exists. Use this whenever the user asks to "write an ADR", "register this decision", "formalize this architectural choice", "documenta essa decisão", "grava isso como ADR", "supersede o ADR NNN", or wraps up a design discussion by saying something like "let's go with X, write it up." Do NOT use this skill to decide an architectural question or explore options — it only formalizes a decision that has already been reached in conversation. If the user is still weighing alternatives, keep discussing until a decision is actually made; don't invoke this skill to make the call for them. Also not the right skill for describing feature behavior or business rules (see the prd skill) or for documenting a codebase's current technical state (see the trd skill).
---

# ADR

## Your role

You are formalizing a decision the user already made — not making one. The decision, its drivers, and the alternatives that were actually discussed all come from the conversation that already happened. Do not re-derive the decision by reading the repository, and do not second-guess or reopen it. Your job is structure and completeness, not judgment.

This distinction matters because an ADR that quietly reinterprets or "improves" the user's decision stops being a record of what they decided — it becomes a record of what you think they should have decided. If something about the decision seems suboptimal, that's worth a comment in your reply to the user, never a silent change to the document.

## Step 1 — Extract the decision from the conversation

Pull three things out of what was actually discussed:

- **The decision** — the choice the user closed on.
- **The drivers** — the criteria that actually weighed on the choice (performance, cost, team familiarity, an existing constraint, whatever was actually named).
- **The alternatives debated** — the real options that were on the table, not a hypothetical list of everything that could have been considered.

If any of these three is genuinely thin or missing from the conversation, don't invent the missing part — ask the user before drafting, or draft with an explicit assumption marker (see Step 3) rather than filling the gap silently.

## Step 2 — Determine the file path

ADRs live at `docs/adrs/<NNN-slug>.md` in the project where the skill runs (not in this marketplace repo).

1. List the existing files in `docs/adrs/` (create the directory if this is the first ADR in the project).
2. Find the highest existing `NNN` prefix and increment it by one, zero-padded to 3 digits (`001`, `002`, … `010`, … `100`). Start at `001` if the directory is empty or doesn't exist yet.
3. Slugify the decision title: lowercase, ASCII, words separated by hyphens (e.g. "Adopt async queues for notifications" → `adopt-async-queues-notifications`).

## Step 3 — Draft-first, mark what you inferred

Fill in every section using what the conversation actually supports. For any line in Context, Alternatives Considered, or Consequences that you had to infer beyond what was explicitly said, append `*(assumption — confirm or correct)*` to that line. Never remove this marker yourself — only the user clears it, by confirming or correcting the line.

This is what makes draft-first safe: you can move fast and fill in reasonable connective tissue (a consequence that obviously follows, context that's implicit in what was said) without it silently passing as something the user actually stated.

## Step 4 — Keep implementation out of it

An ADR records a decision and its consequences, not how it's built. Leave out ports, specific numbers, variable or config names, and other implementation parameters — those belong in a TRD once the decision is implemented, not in the ADR. If the user's decision was framed with implementation details attached, keep the decision-level framing in the ADR and let the details live wherever the code and TRD already track them.

## Step 5 — The template

Reproduce this structure exactly — same frontmatter keys, same section headings, same order. Don't number the headings or use all-caps titles.

The document below is written in English; if the target project's existing docs are in another language, or the user asks for a different output language, translate the headings, labels, and prose into that language while keeping the frontmatter *keys* (`adr_number`, `status`, `created`, `supersedes`, `superseded_by`) in English — they're machine-readable identifiers, not prose, and other tooling (including the trd skill's ADR table) reads them literally.

```
---
adr_number: "<NNN>"
status: accepted
created: <YYYY-MM-DD>
supersedes: ""
superseded_by: ""
---

# ADR <NNN>: [Decision title in one line]

## Context

[The problem, constraints, and forces at play that require this decision. Why decide this now? What's in tension?]

## Alternatives Considered

- **[Alternative A]** — [pros and cons]
- **[Alternative B]** — [pros and cons]
- **[Alternative C]** *(if actually discussed)* — [pros and cons]

## Decision

[What was decided and the reasoning that weighed most. One clear choice, not a menu.]

## Consequences

- **Positive:** [what improves as a result of this decision]
- **Negative:** [the accepted cost — what gets worse or more constrained]
- **Neutral / accepted trade-offs:** [implications that are neither a win nor a cost]
```

`status` starts at `accepted` — the user already decided, there's no `proposed` state to pass through here.

## Step 6 — Superseding a previous ADR

When a decision replaces an earlier one, don't edit the old ADR's content — an accepted ADR is immutable once written, since erasing or rewriting it destroys the record of why the earlier decision made sense in its own context. Instead:

1. Write the new ADR normally (Steps 1–5), with `supersedes: "<old NNN>"` in its frontmatter.
2. In the old ADR, change only two frontmatter fields: `status: superseded` and `superseded_by: "<new NNN>"`. Leave every other line of the old ADR untouched.

## Step 7 — Sync the ADR table in the TRD, if one exists

Check whether `docs/trd.md` exists in this project.

- **If it doesn't exist:** say so and stop — don't create a TRD just to have somewhere to put this table. A partial TRD would violate that document's own rule of never asserting something unverified about the codebase. Mention that the user can run the trd skill first if they want one.
- **If it exists:** rebuild the "Global Decisions (ADRs)" table by scanning the frontmatter of every file in `docs/adrs/` — this is a mechanical projection of data that already exists on disk, not something you're inferring, so it's safe to regenerate in full each time. Show the user the proposed table (or just the diff, if the rest of the file is long) before writing it, the same way you'd show any other section for review. This keeps the pattern consistent with the rest of this skill: the ADR content itself is drafted and reviewed before saving, and touching a second file as a side effect deserves the same visibility even though the table itself required no judgment calls.

## Step 8 — Review before writing

Before saving anything to disk, show the user the ADR section by section, and separately list every line still carrying the `*(assumption — confirm or correct)*` marker so they can resolve each one. Only write the file after they've signed off (or explicitly told you to proceed as drafted).
