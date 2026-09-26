# Design dimensions for a well-built agent

Work through these when designing a new agent or evaluating an existing one. They're
dimensions to reason about, not a form to fill in mechanically — a good agent might make a
deliberate, defensible call that looks unusual on one dimension because another dimension
demanded it. Note the trade-off when that happens instead of forcing every dimension to a
"correct" default.

## Responsibility

State the agent's job as one sentence a colleague could repeat back correctly. If it takes
"and" more than once, it's probably two agents wearing one name. Watch for the "specialist
in everything about X" phrasing — "architecture specialist," "backend expert" — which
sounds like a responsibility but is actually a job title. A job title doesn't tell Claude
when to delegate or what the agent will actually do with a given request; a responsibility
does.

Test: can you name three concrete requests the agent should reject? If every request
sounds plausibly in-scope, the boundary probably isn't real yet.

## Delegation (the `description` field)

This is the only thing the calling Claude sees before deciding to delegate — everything
else in the file is invisible until that decision is already made. It has to answer, for a
Claude that has never read the rest of the file:

- What does this agent do, concretely?
- What kind of request should trigger delegating to it?
- What should specifically **not** go to it (the near-miss cases, not just the obviously
  unrelated ones)?

Vague descriptions under-trigger (Claude can't tell when it applies) or over-trigger
(Claude sends it things it can't actually do well). "Use proactively" / "use when" phrasing
measurably increases delegation for tasks that do match — but only helps if the boundary
underneath is actually accurate; padding a vague description with "use proactively" just
over-triggers with more confidence.

## Context (what goes in the system prompt)

Everything in the agent's instructions is what the agent starts every invocation with —
tokens spent here are spent on every single run, forever. Ask, for each paragraph: does the
agent need this to *do* its job, or is this something Claude would already know from
`CLAUDE.md`, the skill it should be invoking, or general competence? Re-explaining project
conventions the main conversation already has in `CLAUDE.md` is pure duplication that will
drift out of sync the first time someone updates one copy and not the other.

Static reference material (a long checklist, a field table, an anti-pattern catalog) that
the agent only needs *sometimes* belongs in a file the agent reads on demand, not inlined
into the system prompt it pays for on every invocation — the same progressive-disclosure
principle skills use.

## Tools

Grant the minimum set the responsibility requires, not the maximum available. Every tool
beyond what the job needs is attack surface, a chance of an unintended side effect, and
noise in what the agent might reach for. A read-only reviewer holding `Edit`/`Write`
"just in case" can quietly turn into something that rewrites the code it was supposed to
only critique. If the agent should never spawn its own subagents, say so — an agent with
`Agent` access it doesn't need can create delegation chains nobody asked for.

Prefer an explicit `tools:` allowlist for anything with a narrow job; reserve "inherit
everything" for agents whose job is genuinely open-ended (e.g., a general troubleshooting
agent). `disallowedTools` is the right shape when the job needs "everything except a
specific dangerous thing" rather than a short fixed list.

## Skills

If a skill already encodes the workflow the agent needs (e.g., a project has an `ef-migration-safety-review`
skill and someone wants an agent that reviews migrations), the agent should invoke or
preload that skill instead of re-describing the same steps in its own system prompt. Two
independent copies of the same procedure — one in a skill, one duplicated into an agent's
instructions — will diverge the first time either one is updated alone.

## Model

Pick deliberately, and be able to say why, considering:

- **Task complexity** — does this genuinely need frontier reasoning, or is it classification
  / extraction / formatting that a smaller, faster, cheaper model handles just as well?
- **Latency** — is this on a path where the user is waiting synchronously, or does it run
  in the background where a slower model is invisible?
- **Cost at volume** — an agent invoked constantly (e.g., from a hook on every commit)
  multiplies its per-call cost far more than one invoked rarely.

Don't hardcode a model out of habit ("just use the biggest one") or superstition ("small
models can't be trusted with X") without checking whether the task actually needs it. When
there's no real reason to pin one, `inherit` (or omitting `model` entirely) is a legitimate,
deliberate choice — it says "this agent's needs track whatever the user is already paying
for," which is itself a reasoned position, not a default to fill in later.

## Autonomy

Spell out, in the agent's own instructions:

- What it can decide on its own.
- What it must investigate (read files, run commands) before acting, rather than assume.
- When it should stop and hand back to the user instead of guessing forward.
- Which inferences are safe to make (e.g., "infer the test framework from existing test
  files") versus which aren't (e.g., "don't infer a business rule that isn't in the code
  or the conversation").

An agent with no stated autonomy boundary will happily fill every gap with a plausible
guess, and "plausible" is exactly what makes a wrong guess hard to catch later.

## Output

Only impose a strict output contract (a fixed template, a required set of sections) when
something downstream actually consumes that structure — another tool, a report format the
team already expects, a UI that renders specific fields. A rigid template on an agent whose
output is read once by a human and never parsed is a cost with no payoff: it constrains the
agent's phrasing for no one's benefit. When there is a real consumer, state the contract
explicitly and unambiguously, the same way this plugin's other skills do (e.g., a fixed
Markdown template with named sections).
