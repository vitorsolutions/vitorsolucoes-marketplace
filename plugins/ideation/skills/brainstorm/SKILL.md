---
name: brainstorm
description: Explores multiple distinct ideas or options around a topic, feature, or problem, before any decision has been made. Generates at least 5-7 diverse ideas, each with a title, rationale, practical applications, and implementation considerations — balancing practical and creative angles instead of converging on the first obvious answer. Use this whenever the user asks to "brainstorm", "explore ideas", "generate options", "faz um brainstorm", "explora alternativas", wants a planning or ideation session, or is stuck and wants divergent thinking rather than a single recommendation. Do NOT use this skill when the user has already decided and wants that decision formalized (see the adr skill in the docs plugin), when they want a feature's behavior specified (see the prd skill), or when they want the project's current technical state documented (see the trd skill). This skill never writes files — its output lives in the conversation; if an idea from here needs to become a lasting decision or spec, the user runs adr or prd next.
---

# Brainstorm

## Your role

Generate a spread of genuinely different ideas, not a single best answer with minor variations. The value of this skill is divergence — if every idea narrows toward the same solution, the session failed at its purpose, even if that solution happens to be good.

This is the opposite mode from the docs plugin's skills (`adr`, `prd`, `trd`): those formalize something that's already settled or already exists. This skill runs *before* that — while options are still open. Never let it slide into deciding for the user; ideation ends with a list of live options, not a chosen one.

## Method

1. **Generate at least 5-7 distinct ideas** around the stated topic or problem. Balance practical and unconventional angles — don't self-censor toward the safe, obvious answer first. If every idea is a minor variant of the others, keep going until there's real spread.
2. **For each idea, cover:**
   - A clear title and one-line summary.
   - Why it's valuable — the reasoning behind it, not just a description.
   - Practical applications — what it would actually look like in use.
   - Implementation considerations — cost, complexity, risks, or dependencies worth flagging.
   - How it differs from the other ideas in the list (so the spread stays visible, not just implied).
3. **Ground ideas in what's realistic to build**, without abandoning the creative angle that makes brainstorming worth doing — a list of only safe, incremental ideas is as much a failure of the method as a list of only fantastical ones.

## Output

A short list of ideas (title + rationale + practical next step each) — not a single recommendation. Synthesis or narrowing down to one option is a separate, later step the user asks for explicitly; don't do it unprompted at the end of the list.

## Handoff to other skills

If, during or after the session, the user settles on one of the ideas:

- A technical/architectural choice → point them to the `adr` skill (in the `docs` plugin) to formalize it.
- A feature's expected behavior → point them to the `prd` skill (in the `docs` plugin).

Don't invoke those skills yourself — mention the handoff and let the user confirm the decision is actually final before anything gets formalized.
