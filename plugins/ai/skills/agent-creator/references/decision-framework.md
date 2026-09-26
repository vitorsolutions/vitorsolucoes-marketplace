# Decision framework: does this need an agent?

An agent is the heaviest mechanism Claude Code offers. It forks a fresh context, costs a
full model invocation (or more, if it spawns its own subagents), and adds a piece of
configuration someone has to maintain, namespace, and eventually deprecate. Reach for it
only when something about the task genuinely needs that isolation or that persistent,
reusable framing — not because "agent" is the trendiest unit of configuration available.

Work through the alternatives below in order. Each one is cheaper than an agent and covers
the majority of requests that arrive dressed as "I need an agent for X."

## The alternatives, cheapest first

| If the need is really... | The right mechanism is... | Because... |
|---|---|---|
| A fact Claude should always know about this project (stack, conventions, where things live) | **Project instructions / `CLAUDE.md`** | It's static context, not a task to delegate. An agent that just repeats "we use X" in its system prompt is a worse `CLAUDE.md`. |
| A repeatable multi-step workflow triggered by phrasing, run in the *current* context | **A skill** | Skills load progressively into the same conversation — no context fork, no extra invocation, and they compose with whatever else is happening. Most "I want Claude to always do Y when I say Z" requests are this. |
| A fixed, explicitly-invoked prompt template (`/foo arg`) | **A command** | Commands are for short, user-triggered snippets, not for anything that needs its own judgment or investigation loop. |
| Something that must fire automatically on an event (before a tool runs, after a session starts) | **A hook** | Hooks are deterministic and event-driven; an agent can't guarantee it gets invoked at the right moment the way a hook can. |
| Access to an external system's data or actions | **An MCP server / tool** | The gap is capability, not reasoning strategy. Wrapping an MCP call in an agent adds a context fork with no benefit if the main conversation could just call the tool. |
| A job an existing agent already does, maybe with slightly different phrasing | **The existing agent** (possibly with a description tweak) | A near-duplicate agent splits delegation traffic and doubles the maintenance surface for the same responsibility. |
| A short, one-off task with no real ambiguity | **Direct execution by Claude in the main conversation** | If the main agent can just do it in a turn or two, delegating adds latency and token cost for zero isolation benefit. |
| Something whose real problem is unclear or unscoped | **More conversation, not a file** | Writing an agent definition too early locks in a shape for a problem that hasn't been understood yet. |

## When an agent genuinely earns its cost

Create one only when at least one of these is true, and say which one when you propose it:

- **Context isolation is the point.** The task would otherwise pollute the main
  conversation with a large volume of intermediate noise (raw search output, long tool
  transcripts) that the calling context never needs to see again.
- **The task benefits from a different tool allowlist, permission mode, or model** than
  the main conversation, and that difference is load-bearing (e.g., a read-only reviewer
  that must never hold `Edit`/`Write`, or a cheap high-volume classification pass that
  doesn't need a frontier model).
- **The task is genuinely parallelizable** — several independent instances can run at once
  without shared state, and the caller only needs the final synthesis.
- **The responsibility is stable and reused often enough** to justify a maintained
  definition, rather than a prompt that would be rewritten by hand each time.

If none of these apply, say so plainly and recommend the cheaper mechanism instead of
building the agent anyway because it was asked for. A user who asked for "an agent" is
naming the shape they're used to, not necessarily the one their problem needs — the same
courtesy skill-creator extends to "can you make a skill for this" applies here.

## How to raise this with the user

Don't turn this into an interrogation. If discovery already answered the question — the
repo has a `CLAUDE.md`, an obviously-matching skill, or an existing agent doing 90% of
this — say what you found and propose the cheaper path directly, explaining the trade-off
in one or two sentences. Ask only when the repository genuinely doesn't resolve it and the
choice would materially change the design (e.g., "context isolation" vs. "just a skill" is
a real fork, not a formality).
