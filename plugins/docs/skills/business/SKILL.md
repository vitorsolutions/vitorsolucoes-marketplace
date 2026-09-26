---
name: business
description: Generates business-facing documentation from a source code repository — explaining business rules, processes/workflows, external integrations, and domain terminology in plain language, for readers who don't code. It deliberately avoids code snippets, file paths, class/function/method names, and technical schema/parameter tables. Use this whenever the user asks to document a repository "for the business", "para o negócio", "para stakeholders", wants a functional overview a product manager, business analyst, compliance officer, or executive can read, needs onboarding material for non-technical audiences, or asks to explain "what does this system actually do" in plain terms. Trigger even without the word "documentation" — e.g. "explain this codebase to our CFO", "I need to walk legal through our refund flow", "translate this repo into something my boss can understand", "document the business rules in this project". Do NOT use this for developer/technical documentation, API references, READMEs, or architecture docs meant for engineers — those need code examples and belong to a different skill.
---

# Business

## What this skill produces

Documentation that describes what a system *does for the business* — not how it's built. The reader is a product manager, business analyst, compliance officer, auditor, or executive. They will never open the code, and they shouldn't need to. If a sentence in the output would confuse someone who has never programmed, it doesn't belong.

This is a translation task, not a summarization task. The source material is code; the output is business prose. Every technical fact needs to be re-expressed in terms of what it means for the business — a rule, a process, a policy, a relationship — before it goes in the document.

## Step 1: Establish scope

Default to documenting the whole repository. Only narrow the scope if the user names a specific area ("just the billing module", "the checkout flow"). Don't ask the user to enumerate folders up front — that's your job in the next step.

If the repo is large enough that a full pass would be shallow (many independent services, a large monorepo), say so and propose documenting the top few business domains first, then ask whether to continue — don't silently truncate.

## Step 2: Find the business domains, not the folder structure

Your job is to discover the business shape of the system, which usually does *not* line up one-to-one with the technical folder structure. Look at:

- **Domain models / entities** — the nouns the code is built around (Order, Patient, Invoice, Shipment, Policy). These usually point directly at business concepts.
- **Service / use-case / handler layers** — the verbs (CreateOrder, ApproveClaim, IssueRefund). These are your business processes.
- **API routes or public entry points** — what the outside world can trigger. Each meaningful group of endpoints is often a business capability.
- **README files, package/module descriptions, code comments** — often state the business purpose directly; use them as a starting point, not a substitute for reading the logic.
- **Validation, error/exception classes, and conditional branches in service code** — this is where business rules live (limits, eligibility checks, required fields, statuses that block an action).
- **Config, environment variables, and any SDK/client wrappers for outside services** — this is where integrations live (payment processors, notification providers, identity providers, external registries).

Group your findings into business domains (e.g. "Order Management", "Customer Onboarding", "Billing & Invoicing") rather than mirroring package/directory names like `services/` or `utils/`. A domain can span multiple technical layers and even multiple technical modules — trace the full path of a process (entry point → business logic → any side effects like charging a card or sending an email) before writing about it, rather than documenting one file at a time.

If the codebase is small or genuinely single-purpose, one domain covering the whole thing is fine — don't force artificial subdivisions.

## Step 3: For each domain, extract four kinds of content

1. **What it is** — one or two sentences on the purpose of this area of the business, in plain language.
2. **Business rules and validations** — the conditions and policies the code enforces. Look for anything that decides whether an action is allowed, what happens next, or what value is valid. State each rule as a plain-language policy statement.
3. **Processes and workflows** — multi-step sequences as the business experiences them (e.g. an order's lifecycle from placement to delivery, an approval chain, an onboarding sequence). Describe the steps, who/what triggers each one, and what decisions or branches happen along the way.
4. **External integrations** — what outside systems or parties this domain interacts with, described by *purpose and vendor/category* (e.g. "charges the customer through a payment processor", "sends confirmation emails via a transactional email provider", "verifies identity against a third-party KYC service") rather than by SDK, client class, or endpoint.

Also keep a running list of **domain terms** as you go — the vocabulary the business uses for its own concepts (statuses, roles, document types, any term a newcomer would need defined). You'll consolidate these into a glossary at the end.

## Step 4: Translate technical facts into business language

This is the part most likely to go wrong, so slow down here. A rule extracted correctly from the code but expressed in technical form has failed the assignment just as much as one that's missing.

**Read the logic, then re-derive its intent — don't paraphrase the code's syntax.** Ask "what business outcome is this line trying to guarantee?" and write that.

Examples of the transformation:

- Code enforces `order.total > 0 && order.items.length > 0` → "An order must contain at least one item and have a value greater than zero to be accepted."
- Code calls a payment SDK's charge method with a token → "When an order is confirmed, the customer's saved payment method is charged the full order amount."
- Code has a status enum `PENDING_REVIEW`, `APPROVED`, `REJECTED` gating a claim → "Every claim is reviewed before it can be approved or rejected; until a decision is made, it stays in a pending state and no payout occurs."
- A background job reconciles records nightly → "Records are automatically checked for consistency once a day; discrepancies are flagged for manual follow-up."

If you can't tell what the business intent of a piece of logic is, don't guess and don't skip it silently — either state it at the level of confidence you actually have ("the system appears to limit X to once per day, though the exact reason isn't documented in the code") or flag it as an open question in the output rather than inventing a rationale.

## What to leave out entirely

None of the following belong in the output, even as an aside or in parentheses:

- Code blocks or inline code snippets of any kind
- File paths, line numbers, repository/module names
- Class, function, method, or variable names
- Database table/column names or schema details
- HTTP methods, endpoint paths, request/response payload shapes
- Config keys, environment variable names
- Programming languages, frameworks, or libraries — *unless* the tool itself is a business fact (e.g. naming the payment processor or a named external vendor is fine and often useful; naming the HTTP client library used to call it is not)
- Technical tables of any kind (schema tables, parameter tables, field-type-description grids)

If you find yourself about to write a table to summarize something, write it as prose or a bulleted list of plain sentences instead. The one graphical exception is process flow diagrams — see below.

## Diagrams: allowed, sparingly

A Mermaid flowchart or sequence-at-a-business-level diagram is welcome when a process has enough branching steps that prose alone would be hard to follow (e.g. an approval workflow with multiple outcomes). Label nodes with business steps and decisions ("Order placed" → "Payment charged" → "Payment declined?"), never with function names, class names, or technical states that wouldn't mean anything to the reader. Don't add a diagram to every section reflexively — use one only where it earns its place over prose.

## Step 5: Write the output

Organize by business domain, one file per domain, plus an index.

```
docs/business/
├── index.md              (overview: what the system does, list of domains with one-line summaries)
├── order-management.md
├── customer-onboarding.md
├── billing-and-invoicing.md
└── ...
```

Each domain file follows this shape:

```markdown
# [Domain name]

[One or two paragraphs: what this area of the business does and why it exists.]

## Business rules
[Plain-language policy statements, as prose or a bullet list — not a table.]

## Processes
[Each significant workflow, described step by step. Use a Mermaid diagram only where branching makes prose hard to follow.]

## External integrations
[What outside systems/parties this domain touches and why, in business terms.]

## Glossary
[Terms specific to this domain, each as "**Term** — definition." Skip this section if there's nothing beyond what's already in the top-level glossary.]
```

If several domains share a lot of vocabulary, put a consolidated glossary in `index.md` instead of repeating it everywhere.

Before finishing, reread every file and check it against the "What to leave out" list above — it's easy for a stray file path or field name to slip in while writing quickly. Also check that someone with zero engineering background could read straight through without hitting a term you haven't defined.

## When the user wants a different file format

The default and primary output is Markdown, since it's easy to version and review in the repo itself. If the user asks for a Word document or another format from this same business-language content, use the appropriate skill for that file type to produce it (e.g. the docx skill) — don't hand-roll formatting. Generate the Markdown content first regardless; it's the source of truth and the easiest to iterate on with the user.
