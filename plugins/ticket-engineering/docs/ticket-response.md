# Ticket Response

Drafts the message that goes back on a support ticket — a request for missing details, an answer, a status update, or a resolution — written for the requester and free of internal detail, and sends it only on request and after explicit confirmation.

## What it is

The earlier phases are written for an engineer: paths, identifiers, graded uncertainty. This skill turns them into what the requester needs to read — what was found, what happens next, and what, if anything, they need to do — in the language the ticket was written in and following any tone conventions the project defines.

It works in four modes. A clarification request asks only for what would change the work, as a few specific numbered questions. An answer or a resolution describes behavior in the requester's terms and carries the diagnosis's confidence through honestly, leaving clearly marked gaps for dates or commitments the developer hasn't given. A status update says where things stand. It won't compose a cause or a resolution that no earlier phase established.

Requester-facing text leaves out file paths, class and table names, stack traces, queries, hostnames, exploit details, other customers' information, and who changed what. Internal notes may carry technical detail and are kept strictly separate.

By default the output is a draft. Posting through a ticket tool happens only when the developer asks, and only after seeing the exact text, the destination ticket, and whether it is public or internal — and confirming.

## When to use it

- When a ticket has to go back to the requester for more information.
- When you have a conclusion and need to communicate it to someone non-technical.
- When you want a status update worded without committing to internals or dates.

Not the right skill for classifying a ticket (`ticket-triage`), gathering evidence (`ticket-investigation`), or reaching the conclusion being communicated (`ticket-diagnosis`).

## What it guarantees

- **Draft by default** — nothing is posted unless the developer explicitly asks.
- **Confirmation before sending** — the final text, destination, and visibility are shown first; an edit after confirmation requires confirming again; no other ticket field is changed as a side effect.
- **No internal detail in requester-facing text** — and a list, for the developer, of what was deliberately left out.
- **No invented commitments** — dates, versions, and compensation are left as marked gaps.
- **Credentials never repeated** — if the requester shared one, the reply asks them to change it without quoting it.
- **Ticket-system agnostic, no footprint** — no vendor or tool name is assumed; writes no files and saves nothing to memory.
