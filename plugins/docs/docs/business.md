# Business

Turns a repository's source code into business documentation — rules, processes, and integrations explained in plain language, with no code, file paths, or technical tables, for readers who don't program.

## What it is

Most documentation skills go from code to *more* technical documentation: usage examples, API references, comments. This skill goes the other way — it reads the business logic (entities, validations, workflows, external integrations) and **translates** what it finds into the vocabulary of whoever will actually read the document: a manager, a business analyst, the compliance team, leadership. None of that audience is going to open the source code, and the document shouldn't require it.

It's not a summary of the code — it's a translation. A condition like `order.total > 0` doesn't show up as pseudocode; it becomes "every order must have a value greater than zero to be accepted." A call into a payment SDK becomes "the system charges the customer through a payment provider." The result is organized by business domain (not by technical folder), with an index file and one file per area, a glossary of terms, and — when a workflow branches a lot — a simple diagram of the process.

## When to use it

- Presenting a system to leadership, a client, or any non-technical stakeholder.
- Documenting business rules and workflows for compliance, audit, or legal.
- Onboarding a business analyst, PM, or operations person who will follow a project without reading code.
- Any request like "explain this repository to someone who isn't technical" — even without the word "documentation" in it.

It's not the right skill for developer-facing technical documentation (README, API reference, architecture guide) — those need code examples, which is exactly what this skill avoids.

## What it guarantees

- **No code, file paths, class/method names, or technical tables** in the final output — business prose only.
- **Organization by business domain**, not by the repository's folder structure.
- **Rules translated, not copied**: every technical validation becomes a plain-language policy statement.
- **A glossary** of the domain's specific terms.
- **Flow diagrams (Mermaid) only when they help** — a process with few branches reads better as prose.

## Validated against a real repository

This skill was tested by comparing runs with and without it against a real integration repository (a .NET service that syncs sales and products between a store system and a CRM), across three scenarios: an executive overview for leadership, a sales-sync flow for compliance, and onboarding a business analyst.

Result: 100% pass rate on the quality checks (absence of code/technical tables, glossary present, rules in plain language, workflows described step by step), versus 52% without the skill — the most common gap without the skill was using technical tables and code blocks to represent data that should have been prose.
