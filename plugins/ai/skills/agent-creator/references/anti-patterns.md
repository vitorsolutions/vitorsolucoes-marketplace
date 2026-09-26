# Agent anti-patterns

Recognize these when creating or reviewing an agent. Each entry names the smell, why it
hurts, and what to do about it. Not every instance is a hard blocker — some are risks worth
naming and letting the user accept knowingly — but every instance should at least be
surfaced, not silently waved through.

- **The generalist.** "Handles anything related to the backend" / "your all-purpose coding
  assistant." No request is clearly out of scope, so Claude can't judge when delegating
  actually helps versus just adding a hop. Fix: narrow the responsibility to something you
  could reject three concrete requests from.

- **Multiple independent responsibilities.** An agent that reviews security *and* writes
  documentation *and* runs deployments. These don't reinforce each other — they're three
  agents sharing one name, one tool list (now bloated to cover all three jobs), and one
  system prompt that's three times longer than any single job needs. Fix: split, or pick
  the one responsibility this agent actually owns and route the rest elsewhere.

- **Vague description.** "Helps with code stuff." Under-triggers when it should fire,
  over-triggers when it shouldn't, and gives the calling Claude nothing to reason with. Fix:
  name the concrete task type, the trigger conditions, and the near-miss cases that should
  go elsewhere.

- **Job-title description.** "Architecture specialist." "Senior code reviewer." A title
  describes seniority, not a task boundary — it tells Claude nothing about what request
  should route here versus to the main conversation. Fix: describe the task, not the role.

- **Duplicate of another agent.** Near-identical responsibility to an agent that already
  exists, usually because the new one was written without checking what's already in
  `.claude/agents/`, `~/.claude/agents/`, or the enabled plugins' `agents/` directories.
  Splits delegation traffic unpredictably between the two and doubles the maintenance
  surface for one job. Fix: extend or rename the existing agent instead of adding a second.

- **Duplicate of a skill.** An agent whose entire system prompt is a workflow a skill
  already implements, just re-typed with "you are an agent that..." framing. Now there are
  two copies of the same procedure that will drift the moment one gets updated and the
  other doesn't. Fix: have the agent invoke or preload the skill (`skills:` frontmatter)
  instead of re-describing it.

- **Tools granted by convenience, not need.** `tools:` omitted (inheriting everything) or
  set to "just give it everything" for a job that only ever reads. The cost isn't
  hypothetical — a reviewer that can `Edit` will eventually edit, whether by explicit
  instruction drift or by finding editing the path of least resistance to "fix" what it
  was asked to critique. Fix: allowlist the minimum, add `disallowedTools` for anything
  merely risky rather than granting a smaller inherited set some other way.

- **Instructions bloated with static reference material.** A system prompt with a 200-line
  checklist, an exhaustive field table, or a full style guide pasted inline, paid for on
  every single invocation whether or not that section is ever needed this run. Fix: move it
  to a file the agent reads on demand — the same progressive-disclosure move a skill makes
  with its `references/` directory.

- **Agent for a trivial task.** A one-off, unambiguous, single-turn task ("format this
  JSON," "rename this variable everywhere") wrapped in an agent definition. The context
  fork and extra invocation cost more than just doing the task inline bought. Fix: don't
  build the agent; do the task, or point to a skill if it truly repeats often enough to
  deserve a shared workflow.

- **Agent as a reusable prompt, not a role.** The whole "agent" is a single instruction
  ("always respond in pirate voice") with no actual task logic, tool needs, or isolation
  benefit — a prompt snippet wearing agent configuration for no functional reason. Fix: a
  saved prompt, a command, or (for something stylistic across a whole session) an output
  style is the right shape, not an agent.

- **Circular delegation.** Agent A's instructions tell it to delegate to Agent B for part
  of its job, and Agent B's instructions delegate back to A (or to a third agent that
  eventually loops back). Depending on the runtime this either fails outright or burns
  turns/budget with no forward progress. Fix: redraw the boundary so delegation is a
  one-directional chain, or fold the two responsibilities into one agent if they're this
  entangled.

- **Implicit dependencies.** The agent's instructions assume a file, an MCP server, a repo
  convention, or another agent exists, without checking or stating that assumption. Works
  fine wherever it was written, breaks silently wherever that assumption doesn't hold. Fix:
  state the dependency explicitly, and have the agent verify it (or fail loudly) rather than
  assume it.

- **Output contract that doesn't need to exist.** A rigid, multi-section required template
  imposed on output nothing downstream actually parses or reuses. Costs the agent flexibility
  for no one's benefit. Fix: only mandate structure when there's a real consumer of that
  structure.

- **Unfounded business inference.** The agent is asked (or infers on its own) to fill a gap
  with a business rule, threshold, or policy that isn't actually stated anywhere in the
  repo or the conversation — "assume a 30-day retention window" invented from nothing. Fix:
  state in the agent's autonomy section which inferences are safe (technical defaults
  inferable from the codebase) versus which require asking (business/product decisions).

- **Instructions that conflict with the project.** The agent's system prompt states a
  convention, path, or rule that contradicts what `CLAUDE.md` or the actual repository
  says. Usually happens when the agent was copied from another project verbatim. Fix: cross
  check the agent's stated assumptions against the actual repo before shipping it.
