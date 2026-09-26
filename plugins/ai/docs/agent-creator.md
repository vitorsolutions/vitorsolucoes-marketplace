# Agent Creator

Engineers Claude Code agents and subagents with the same rigor a skilled reviewer brings to a pull request — creating new agents, analyzing existing ones, refactoring overloaded agents, and validating configuration against the current Claude Code specification, instead of just generating a file that happens to parse.

## What it is

Most requests phrased as "I need an agent for X" don't actually need an agent — they need a `CLAUDE.md` update, a skill, a command, a hook, an MCP tool, or an existing agent that already does 90% of the job. This skill checks that first, using a decision framework, and says plainly when an agent is the wrong answer instead of building one because one was asked for.

When an agent genuinely is the right shape, the skill works through a full engineering pass: a clear, bounded responsibility; a delegation description built to trigger correctly (and to *not* trigger on near-miss requests); least-privilege tool grants; a deliberate model choice; explicit autonomy boundaries; and an output contract only where something downstream actually consumes it. It also knows the common failure shapes to watch for — the "specialist in everything" generalist, multiple independent responsibilities stitched into one file, a job-title description that tells Claude nothing about when to delegate, duplicated agents or duplicated skills, tool grants handed out for convenience instead of need, and more — cataloged with the reasoning behind each one, not just a name.

Reviewing an existing agent (or two agents suspected of doing the same job) runs through the same lens: every finding is classified as a confirmed problem, a risk, an opportunity, an acceptable design decision, or something that needs more information before judging — so a legitimate trade-off never gets flagged the same way as an actual defect.

## When to use it

- "Create an agent for..." / "I need a subagent that..." — before writing frontmatter, this skill checks whether an agent is even the right mechanism.
- "Review my agents" / "Is this agent well designed?" / "When should I use this agent?"
- "I have two agents doing basically the same thing" — decomposition and overlap analysis.
- "My agent is getting too many tools" / "Should this agent use that skill instead?"
- "Turn this role into an agent" — evaluated against the decision framework first, not assumed.

Not the right skill for creating or editing Claude Code *skills* (that's `skill-creator`), for open-ended brainstorming with no agent angle (that's `brainstorm`), or for a plain one-off task that doesn't involve designing a reusable agent at all.

## What it guarantees

- **Never assumes an agent is the answer.** Works through project instructions, `CLAUDE.md`, skills, commands, hooks, MCP tools, and existing agents first, and recommends the cheaper mechanism when it fits better.
- **Grounds every frontmatter field in the current Claude Code specification** (`references/agent-spec.md`), sourced from the live docs rather than assumed from memory, and flagged for re-verification if the repo ever disagrees with it.
- **Classifies review findings by severity and certainty** — confirmed problem, risk, opportunity, acceptable decision, or insufficient information — instead of a single pass/fail verdict.
- **Applies least-privilege tool grants and deliberate model selection**, reasoned against the agent's actual job rather than granted by convenience.
- **Validates before declaring done** — frontmatter syntax, naming rules, tool/model validity, skill references, and (for plugin-hosted agents) `claude plugin validate`.
