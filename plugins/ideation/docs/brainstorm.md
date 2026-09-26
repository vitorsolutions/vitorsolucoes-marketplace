# Brainstorm

Explores multiple distinct ideas or options around a topic before any decision has been made, favoring divergence over a single early recommendation.

## What it is

Most technical or product work has a stage before anything gets formalized: options are still open, and the goal is breadth, not a verdict. This skill covers that stage. Given a topic, problem, or feature idea, it generates at least 5-7 genuinely different ideas — each with a title, the reasoning behind it, what it would look like in practice, and what it would cost or risk to build. It deliberately avoids collapsing into one recommendation; narrowing down is a separate step the user asks for explicitly, once the options are on the table.

It never writes files. The output lives in the conversation, because a brainstorm session is exploratory by nature — the moment an idea from it becomes a real decision or a specified feature, it belongs in the `docs` plugin instead: the `adr` skill formalizes an architectural choice, and the `prd` skill specifies a feature's behavior.

## When to use it

- Exploring feature ideas or solutions from multiple angles before committing to one.
- Planning or ideation sessions, including when the user is stuck and wants divergent thinking rather than a single answer.
- Generating a spread of options to bring into a design discussion, before that discussion produces an ADR.

Not the right skill once a decision is already made (see the `adr` skill) or once a feature's behavior is already agreed on and needs specifying (see the `prd` skill) — those skills formalize what this one deliberately leaves open.

## What it guarantees

- **At least 5-7 distinct ideas**, not variations on one theme — real spread across practical and unconventional angles.
- **Structure per idea**: title, rationale, practical applications, and implementation considerations.
- **No premature synthesis** — the session ends with a list of live options, not a single chosen answer, unless the user asks for that narrowing separately.
- **No file output** — brainstorming stays in the conversation; a chosen idea moves to `adr` or `prd` only when the user says it's settled.
