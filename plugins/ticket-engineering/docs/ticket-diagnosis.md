# Ticket Diagnosis

Draws the conclusion for a support ticket from the evidence gathered — a probable cause, an answer, or a feasibility and impact assessment — with every claim graded and "inconclusive" treated as a valid result.

## What it is

Diagnosis says what the evidence means and how sure that is. What it concludes depends on the kind of ticket: for an incident, how the reported behavior follows from the facts and which alternatives were ruled out; for a question, the current behavior with its conditions and edge cases; for an improvement, what would have to change, what it would affect, and which requirements are still open; for a service request, whether the code offers a supported way to do what's asked.

Each statement is labeled Observed (visible in the code or ticket, with a reference), Hypothesis (fits the facts but unverified, with what would confirm it), Risk, or Recommendation. Overall confidence is stated as confirmed, probable, or inconclusive, set by the weakest link the conclusion depends on. For incidents, the explanation is tested against the ticket — does it account for what was seen, when, and for whom — and whatever it leaves unexplained is listed.

The failure this skill exists to prevent is the confident, plausible, wrong cause. When the decisive evidence lies outside the repository, it says so, lists the candidate explanations, and names what would discriminate between them.

## When to use it

- After an investigation, to turn findings into a conclusion you can act on.
- When deciding whether a reported behavior is a defect or works as designed.
- When a ticket asks for something new and you need to know what it would touch.

Not the right skill for classifying a ticket (`ticket-triage`), collecting the facts (`ticket-investigation`), or writing the reply (`ticket-response`).

## What it guarantees

- **Evidence-graded claims** — Observed / Hypothesis / Risk / Recommendation, never merged.
- **Honest confidence** — confirmed, probable, or inconclusive; no cause is fabricated to close a ticket.
- **Type-aware conclusion** — a cause for incidents, an answer for questions, an impact assessment for improvements.
- **No invented estimates** — size is described relative to what was observed, not in hours or days.
- **Works without prior phases** — a missing investigation is stated and the minimum evidence is gathered and cited.
- **Read-only, no footprint** — recommends, never applies a fix; writes no files and saves nothing to memory.
