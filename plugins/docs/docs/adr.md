# ADR

Formalizes a single architectural decision the user already made in conversation into an immutable Architecture Decision Record, without re-deciding or reinterpreting it.

## What it is

Most of the work of writing an ADR happens before the ADR — a team debates alternatives, weighs drivers, and lands on a choice. This skill picks up right after that moment: it takes the decision, the drivers that mattered, and the alternatives that were actually on the table, and turns them into a structured, dated record at `docs/adrs/<NNN-slug>.md`. It never re-opens the decision or reads the repository to "discover" it — the conversation is the source of truth, and the skill's job is formalization, not judgment.

Anything the skill has to infer beyond what was explicitly discussed gets flagged inline with an assumption marker, so nothing invented quietly passes as something the user actually said. The document is always shown for review, section by section, before it's written to disk.

## When to use it

- Right after a design discussion lands on a choice: "let's go with X, write it up."
- Registering a decision that's already been made, so future readers understand why.
- Replacing an earlier decision — the skill handles superseding an old ADR (marking it `superseded`, linking to its replacement) instead of editing history.

Not the right skill for exploring which option to pick — only for recording one that's already chosen — nor for feature behavior (see the prd skill) or a project's current technical state (see the trd skill).

## What it guarantees

- **One ADR per decision**, numbered sequentially and immutable once accepted — a changed decision gets a new ADR that supersedes the old one, never an edit to it.
- **No implementation parameters** (ports, config values, variable names) — those belong in a TRD, not here.
- **Assumptions marked inline**, never silently resolved on the skill's own judgment.
- **The project's TRD stays in sync**: if `docs/trd.md` exists, its ADR table is refreshed after every new or superseded ADR — shown for review first.
