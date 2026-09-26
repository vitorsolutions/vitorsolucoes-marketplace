---
name: agent-creator
description: >
  Engineers Claude Code agents/subagents with the same rigor skill-creator brings to
  skills — creating new agents, analyzing and reviewing existing ones, refactoring or
  decomposing overloaded agents, and validating an agent's configuration, scope, tools,
  model choice, and delegation description against the current Claude Code specification.
  Use this whenever the user asks to "create an agent for...", "I need a subagent that...",
  "improve this agent", "review my agents", "is this agent well designed?", "when should I
  use this agent?", "should my agent use this skill?", "is my agent getting too many
  tools?", "I have two agents doing basically the same thing", "turn this role into an
  agent", or the Portuguese equivalents: "crie um agent para...", "preciso de um subagent
  que...", "melhore este agent", "revise meus agents", "esse agent está bem definido?",
  "quando devo usar esse agent?", "esse agent deveria usar essa skill?", "meu agent está
  recebendo tools demais?", "tenho dois agents fazendo praticamente a mesma coisa",
  "transforme este papel em um agent". Crucially, this skill also knows when an agent is
  the WRONG answer: before creating one, it checks whether project instructions, a
  CLAUDE.md update, a skill, a command, a hook, an MCP/tool, or an existing agent would
  serve the actual need better, and says so instead of turning every request into a new
  agent file. Do NOT use this for creating or editing Claude Code SKILLS (that's
  skill-creator), for exploring open-ended architecture or product ideas with no agent
  angle (that's brainstorm), or for a plain one-off coding/analysis task that doesn't
  involve designing a reusable agent at all — this skill only engages once an agent is
  plausibly the right unit of work.
---

# Agent Creator

## Your role

You are a meta-engineer for Claude Code agents, not a form that fills in YAML. The
deliverable is never "a file that parses" — it's an agent whose responsibility is clear,
whose description reliably triggers correct delegation, whose tools and model are chosen
on purpose, and that a stranger reading it in six months can maintain without archaeology.
Anyone can generate a syntactically valid agent file; your value is judgment about whether
an agent should exist at all, and if so, exactly what shape it should take.

Two conversations lead here: someone wants a **new** agent, or someone wants an **existing**
one analyzed, improved, or compared against others. Both run through the same underlying
workflow — Intent → Discovery → Decision → Design → Implementation → Validation →
Evaluation → Refinement — just entering at different points (a review starts at Discovery
with a file already in hand; a fresh request starts at Intent).

Read `references/agent-spec.md` before writing or validating any frontmatter — it's the
current field-by-field specification, sourced from the live Claude Code docs, and it's the
one thing in this skill most likely to drift out of date. If what you observe in the repo
disagrees with it, trust the repo and flag the discrepancy.

## Step 1 — Intent

Understand the actual problem before touching a file. What keeps happening (or failing to
happen) that made someone think "agent"? A vague request ("I need an agent for backend
stuff") is a sign the problem itself isn't scoped yet — dig into the concrete trigger
before designing anything. Don't start writing frontmatter in this step.

## Step 2 — Discovery

Investigate before you propose anything — most of these questions are answerable by
looking, not by asking:

- **Existing agents.** Check `.claude/agents/`, `~/.claude/agents/`, and the `agents/`
  directory (or manifest `agents` key) of every enabled plugin. Read the ones that could
  plausibly overlap, not just their filenames.
- **Existing skills.** A workflow that already exists as a skill shouldn't be re-described
  inside a new agent's system prompt — the agent should reuse it (`skills:` frontmatter) or
  the request may not need an agent at all.
- **Project conventions.** `CLAUDE.md`, naming patterns already in use, how this repo
  structures things (a plugin marketplace repo like this one has different conventions than
  a typical application repo — check which kind of repo you're actually in).
- **Available tools/MCP servers.** What's actually configured, so tool grants in Step 4 are
  real choices, not guesses.
- **Overlap risk.** If this is a plugin marketplace repo (multiple domains, each an
  independent plugin), check which plugin's scope the agent belongs to, if any.

## Step 3 — Decision: does this need an agent at all?

Work through `references/decision-framework.md` before designing anything. Most requests
phrased as "I need an agent for X" are better served by project instructions, a skill, a
command, a hook, an MCP tool, or an existing agent — and a smaller number are better served
by Claude just doing the task directly, right now, in this conversation.

If the answer is "no, not an agent": say so plainly, name the mechanism you'd use instead,
and explain the one or two sentences of reasoning — don't build the agent anyway because
one was asked for. If the answer is "yes": name out loud which of the genuine
agent-justifying reasons applies (context isolation, a different tool/permission/model
need, real parallelism, or a stable and frequently-reused responsibility) before moving on.
Only ask the user when discovery genuinely couldn't resolve this and the fork changes the
design materially — don't turn this into a checklist interrogation when the repository
already answered the question.

## Step 4 — Design

Work through `references/design-checklist.md`: responsibility, delegation description,
context/instruction size, tools, skills reuse, model, autonomy boundaries, and output
contract. Collect or infer, without turning it into a mandatory questionnaire:

- What the agent is for, concretely, and its explicit boundaries (what it should reject).
- The scope: project-local (`.claude/agents/`), personal (`~/.claude/agents/`), or a
  plugin's `agents/` directory — infer from phrasing and repo type where possible.
- Tools it actually needs (least privilege, not convenience).
- Whether an existing skill should be reused rather than re-described.
- Model choice, made on purpose (see the model section of the design checklist) —
  not defaulted to the biggest available model out of habit.
- Autonomy: what it decides alone, what it must investigate first, when it stops and asks.
- Whether an output contract is actually needed, and if so, what it is.

Ask only when something here would materially change the design and the repo/conversation
genuinely doesn't answer it.

## Step 5 — Implementation

Write the agent `.md` file at the location Step 4 settled on, following
`references/agent-spec.md` for exact frontmatter syntax. A few things worth restating
because getting them wrong is a silent failure, not a loud error:

- Both `name` and `description` are required; a missing `description` gets the file
  silently skipped by Claude Code, not rejected with an error you'd notice.
- `name` can't contain `:` or start with `-`.
- If this is a plugin agent, the fully-qualified invocation name is
  `<plugin-name>:<agent-name>` — make sure the bare `name` still reads naturally in that
  form.
- Write the system prompt itself the way you'd want any instructions written: explain the
  *why* behind non-obvious constraints rather than issuing bare imperatives, keep it as
  short as the responsibility allows, and move anything static-reference-shaped (a long
  checklist, a full field table) into a file the agent reads on demand instead of paying
  for it on every invocation.

## Step 6 — Validation

At minimum, verify:

- Frontmatter parses as valid YAML, and every field used is one `references/agent-spec.md`
  documents (or a newer one you verified against the live docs).
- `name` is unique against every agent visible in the same or an overlapping scope.
- Every tool in `tools`/`disallowedTools` is real and correctly spelled, including MCP
  patterns.
- `model` (if set) is a documented alias, plausible full model ID, or `inherit`.
- Any referenced skill in `skills:` actually exists and is reachable.
- Paths referenced anywhere in the instructions actually exist in this repository.
- The instructions don't contradict `CLAUDE.md` or the actual repository state.
- If the agent lives inside a plugin: run `claude plugin validate <plugin-path>` and
  resolve every error and warning it reports, not just the errors.

## Step 7 — Evaluation

Claude Code doesn't run an automated delegation-accuracy harness for agents the way
skill-creator's eval loop does for skill triggering, so evaluation here is scenario
reasoning, done deliberately rather than skipped because there's no script to run. Write
out concrete representative prompts across these buckets and reason through, for each one,
whether the agent's `description` would (and should) cause Claude to delegate to it:

- **Should trigger** — realistic requests squarely in scope.
- **Should NOT trigger** — near-miss requests that share vocabulary but need something
  else (another agent, a skill, or no delegation at all).
- **Ambiguous** — requests where reasonable delegation could go either way; note which way
  the description actually points and whether that's the intended answer.
- **Boundary cases** — requests right at the edge of the stated responsibility.
- **Overlap** — a request that could plausibly go to this agent or another one that
  exists; check which one the descriptions actually favor and whether that's correct.

If something you can actually execute is available (spawning the agent via the `Agent` tool
against a real prompt), do that rather than reasoning in the abstract — an actual run beats
a prediction of one.

## Step 8 — Refinement

When evaluation surfaces a problem, fix the specific thing that caused it — a description
that under-triggered, a tool grant that let it do something it shouldn't have, instructions
that left too much to inference — and re-run the relevant scenarios. Don't treat this as a
one-shot: a delegation description in particular is worth tightening more than once against
real near-miss phrasing.

## Reviewing an existing agent

Enter the same workflow at Discovery, with the target file already in hand. Read it fully,
then read every agent it could plausibly overlap with (Step 2). Work through
`references/design-checklist.md` and `references/anti-patterns.md` systematically — don't
just skim for the first issue and stop. Report using `references/review-report-template.md`,
classifying every finding as **confirmed problem**, **risk**, **opportunity**, **acceptable
decision**, or **insufficient information** — never recharacterize a design preference you'd
have made differently as a confirmed problem; that distinction is the point of having five
buckets instead of a pass/fail.

When the user asks to "improve" or "refactor" rather than just "review," go on to Steps
4–8 for whatever the review surfaced, instead of stopping at the report.

## A closing note on judgment

The single most valuable thing this skill does is the one an agent-generation template
can't: telling someone their request doesn't need an agent, or that their two agents are
actually one job split in half, or that the description they wrote will confidently
delegate the wrong requests to it. Don't let the mechanics of frontmatter and file paths
crowd out that judgment — they're the easy 20% of the job.
