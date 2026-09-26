# Review report structure

Use this shape when reporting findings about an existing agent (or a proposed new one).
Keep it lean — a two-agent review doesn't need every section padded out, and an agent with
no problems shouldn't have a manufactured "opportunity for improvement" invented just to
fill the template.

```markdown
# Review: <agent-name>

## Responsibility
One or two sentences: what this agent's job actually is, as observed from its description
and instructions — not as advertised, if the two disagree.

## Findings
For each finding, one line: **[Confirmed problem | Risk | Opportunity | Acceptable decision
| Insufficient information]** — the finding, and why it matters. Order by severity, most
important first.

## Overlap check
Named against every other agent found in .claude/agents/, ~/.claude/agents/, and enabled
plugins' agents/ directories: none, partial (name the overlapping agent and the shared
territory), or duplicate (name which one should be removed/merged and why).

## Recommendation
What to actually do: keep as-is, adjust <specific field/section>, split into <N> agents,
merge with <agent>, or remove. If "keep as-is" despite findings above, say why those
findings don't rise to something worth changing.
```

## The five finding classifications

Use these consistently — they carry real meaning, and blurring them (e.g., calling a
stylistic preference a "confirmed problem") erodes trust in the review.

- **Confirmed problem** — objectively wrong or broken: invalid frontmatter, a tool the
  agent's instructions rely on but doesn't have access to, a name collision, instructions
  that contradict the actual repository.
- **Risk** — not yet broken, but exposes the agent (or its user) to a bad outcome under
  plausible conditions: a reviewer holding `Edit`, an unbounded tool grant, an unstated
  dependency on a file that might not exist.
- **Opportunity** — the agent works, but a change would make it meaningfully better:
  tightening a vague description, moving a static checklist into a reference file, pointing
  it at a skill instead of duplicating that skill's workflow.
- **Acceptable decision** — something that looks unusual but is actually a reasoned,
  defensible trade-off given the agent's real constraints (e.g., a deliberately broad tool
  set because the agent's job really is open-ended troubleshooting). State the reasoning
  you're accepting, not just "this is fine" — a future reviewer needs to know it was
  considered, not skipped.
- **Insufficient information** — can't judge without something you don't have: a live run
  to observe actual behavior, confirmation from the user about intended scope, visibility
  into another system the agent depends on. Say exactly what's missing rather than guessing
  a verdict.

Never recharacterize a design preference you'd have made differently as a "confirmed
problem" — that's what the "acceptable decision" bucket exists to prevent.
