# PRD

Writes a Product Requirements Document that captures a feature's behavior and business rules from a conversation that's already matured — not from a cold interview.

## What it is

By the time a feature is ready to be spec'd, most of the real thinking already happened in discussion. This skill takes that conversation and turns it into a requirements document built around **verifiable predicates** — every behavior expressed as Given/When/Then, testable and unambiguous, plus the invariants, constraints, and out-of-scope boundaries that keep the feature honest. It never restarts discovery, and it never describes implementation: no code, no architecture, no named technology. That belongs in an ADR or a TRD, not a PRD.

Vague acceptance criteria ("should perform well") aren't acceptable — the skill reformulates them into something concretely checkable before the document is considered done.

## When to use it

- Wrapping up a feature discussion: "write the PRD for this."
- Documenting business rules and expected behavior for a feature that's about to be built.
- Revising an existing PRD as behavior evolves — it edits in place rather than creating a parallel version.

Not the right skill for deciding what a feature should do (keep discussing until scope is settled) or for a single architectural decision (see the adr skill).

## What it guarantees

- **Given/When/Then predicates**, not prose descriptions of behavior.
- **An explicit "out of scope" section** on every PRD, with the reason something was excluded.
- **No implementation details** — technology, code, and architecture stay out.
- **Assumptions marked inline** for anything inferred beyond what was actually discussed.
