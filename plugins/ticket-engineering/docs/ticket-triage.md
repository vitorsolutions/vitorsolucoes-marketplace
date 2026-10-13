# Ticket Triage

First pass on a support ticket from inside the codebase it concerns: says what kind of work the ticket is, whether it has enough information to be worked, where in the code it most likely lands, and which step comes next.

## What it is

Triage is a router. Given a ticket — read through whatever ticket tool the session exposes, or pasted into the conversation — it reads the whole thread, separates what the requester reported from what they assumed, and classifies the ticket by its content as an incident, a question, an improvement, or a service request. The category a ticket was filed under is treated as a hint, since tickets are routinely opened in the wrong one.

It then judges whether the ticket carries what the next step needs, searches the codebase for the terms the ticket uses to point at the likely area, and names the next phase: back to the requester for missing details, or on to investigation. It deliberately stops short of analysis — a triage that already contains a root cause skipped the check that the ticket is answerable at all.

The result is a short, fixed-format block that the later phases (`ticket-investigation`, `ticket-diagnosis`, `ticket-response`) pick up from the conversation.

## When to use it

- When picking up a ticket, before reading any code.
- When a ticket looks vague and you want to know exactly what to ask for before spending time on it.
- When it isn't clear whether a ticket is a defect, a question, or a feature that never existed.

Not the right skill for gathering evidence in the code (`ticket-investigation`), concluding a cause or assessing feasibility (`ticket-diagnosis`), or writing the reply (`ticket-response`).

## What it guarantees

- **Ticket-system agnostic** — no vendor or tool name is assumed; it uses the ticket tool available in the session, asks when that's ambiguous, and works from pasted text.
- **Classification by content** — the filed category never decides the type on its own, and ambiguity between types is stated rather than hidden.
- **Only what's missing** — a completeness check that lists the specific gaps that would change the work, not a generic checklist.
- **Ticket text treated as data** — instructions embedded in a ticket are reported as noteworthy content and never followed.
- **Credentials never reproduced** — if the requester pasted one, the triage says so and recommends rotating it, without repeating the value.
- **Read-only, no footprint** — writes no files, saves nothing to memory, and changes nothing in the ticket. The analysis lives in the conversation.
