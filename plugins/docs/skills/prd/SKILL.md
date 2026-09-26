---
name: prd
description: Writes a Product Requirements Document describing the BEHAVIOR and BUSINESS RULES of a feature that has already been fleshed out in the current conversation, at docs/prds/<slug>.md in the project the skill is invoked in — using Given/When/Then verifiable predicates, invariants, constraints, an explicit out-of-scope section, and observable acceptance criteria. Use this whenever the user asks to "write the PRD for this", "documenta esse comportamento", "spec out this feature", or wraps up a feature discussion wanting it captured as requirements. Never describes implementation, technology choices, or code — that belongs to the adr or trd skills. Do NOT use this skill to explore or decide what a feature should do — it only formalizes behavior that's already been discussed; if scope is still being debated, keep discussing before invoking it. Not the right skill for a single architectural decision (see adr) or a codebase's current technical baseline (see trd).
---

# PRD

## Your role

The conversation that already happened is the source of truth for what this feature does. Write from it — don't restart discovery or re-interview the user as if nothing had been discussed. Where the conversation left a gap, fill it with a reasonable inference and mark it (see below) rather than stalling the document on a question that could just as easily be answered in review.

## What belongs in a PRD, and what doesn't

A PRD describes the *what* and the *why* of behavior — what the system does, under what conditions, and the business reason it matters. It never describes the *how*: no code, no architecture, no named technology, no data structures. The moment you're about to write how something is implemented, that sentence belongs in an ADR (if it's a decision) or a TRD (if it's the current state of the system), not here.

## Structure

Generate the complete document in one pass, in this order:

1. **Context** — the product, its current state, and the business problem this feature addresses.
2. **Actors** — who or what interacts with the feature (a user role, an external system, a background process, a database — anything that takes an action or receives an effect).
3. **Verifiable predicates** — every meaningful behavior expressed as **Given/When/Then**, each one objectively testable and free of ambiguity. This is the core of the document; spend most of your effort here.
4. **Invariants** — what must always hold true, regardless of path taken (e.g. "an order that hasn't been paid never appears as fulfilled").
5. **Constraints** — business/behavioral limits, not technical ones (e.g. "a refund can only be requested within 30 days of delivery", not "the refund endpoint rate-limits to 10 req/s").
6. **Out of scope** — mandatory section, even if short. State explicitly what this feature does *not* cover, and why it was excluded (deferred, owned by another feature, deliberately rejected — say which).
7. **Acceptance criteria** — how to know the feature is "done," stated in observable terms someone could actually check.

## Quality bar for predicates and criteria

A vague criterion ("should perform well," "should work correctly," "should be user-friendly") is not acceptable anywhere in this document. If you catch yourself writing one, stop and reformulate it as a concrete Given/When/Then or a measurable acceptance criterion instead. "The API should be fast" isn't verifiable; "a search request over a catalog of up to 10,000 items returns results within 2 seconds" is.

## Mark what you inferred

For anything in Context, Actors, an individual predicate, an invariant, a constraint, or the out-of-scope reasoning that you filled in beyond what the conversation actually established, append `*(assumption — confirm or correct)*` to that line. Leave the marker in place until the user resolves it — don't quietly drop it because it seems obviously right to you.

## File path

Save to `docs/prds/<slug>.md` in the project the skill is invoked in, where `<slug>` is the feature name in kebab-case (lowercase, ASCII, hyphen-separated — e.g. "Bulk CSV export for orders" → `bulk-csv-export-orders`). Unlike an ADR, a PRD is a living document: if one already exists for this feature and the user is revising it, edit it in place rather than creating a new file, and consider adding a short "Updated: <date> — <what changed>" line near the top rather than silently rewriting history.

## Output language

Write the document in English by default. If the target project's existing docs are in another language, or the user says which language to use, write the whole document — headings, labels, and prose — in that language instead. This is purely a language choice, not a structural one: the seven sections above and their order stay fixed regardless of language.

## Review before writing

Show the complete draft to the user before saving. Since this skill generates the whole document in one pass rather than building it up interactively, this review step is where gaps and misreadings of the conversation actually get caught — don't skip it even when the draft feels solid.
