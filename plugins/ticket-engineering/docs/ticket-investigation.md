# Ticket Investigation

Gathers evidence from the codebase about what a support ticket describes and reports it as facts with file and line references — without concluding a cause or proposing a solution.

## What it is

Investigation turns a ticket into concrete questions the code can answer — what happens in the reported scenario, what the current behavior is, where a requested behavior would live — and traces the relevant path through the code: entry point, rules applied, data read and written, calls that leave the repository. It reads the code rather than inferring from names, and checks tests, configuration defaults, and project documentation for stated intent, surfacing any gap between what is documented and what is implemented.

Its defining constraint is that it stops at observation. Every finding carries a reference the developer can open; anything that depends on production data, deployed configuration, an external service, or an unseen caller is listed separately as not verifiable from the repository. Keeping observation apart from conclusion lets the evidence be checked before an explanation is built on it.

It picks up the triage from the conversation when there is one, and proceeds without it — stating the gap — when there isn't.

## When to use it

- After triage has routed an incident, question, or improvement here.
- When you want to know what the code actually does in the situation a ticket describes, before forming an opinion.
- When a ticket's claim needs to be checked against documented behavior.

Not the right skill for classifying a ticket (`ticket-triage`), stating a root cause, feasibility, or fix (`ticket-diagnosis`), or writing the reply (`ticket-response`).

## What it guarantees

- **Facts with references** — every finding points to a file and line; a statement without one isn't reported as a fact.
- **No conclusions** — causes, blame, and fixes are left to the diagnosis phase.
- **Explicit edges** — what the repository cannot answer is listed, not filled in with a plausible story.
- **Stack agnostic** — no assumption about language, framework, or project layout.
- **Works without prior phases** — a missing triage is stated and the minimum is redone; it doesn't refuse.
- **Read-only, no footprint** — never edits code, writes files, saves to memory, or touches the ticket.
