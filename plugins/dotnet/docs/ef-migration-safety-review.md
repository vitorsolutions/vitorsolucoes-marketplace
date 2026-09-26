# EF Migration Safety Review

Reviews the most recently generated Entity Framework Core migration for operational safety risks before it gets applied to a real database, using static analysis only — no database connection, no assumptions about table size.

## What it is

`dotnet ef migrations add` generates code that compiles and applies without complaint even when it's operationally dangerous — a `NOT NULL` column with no default on a table that already has rows, a rename implemented as a drop-and-recreate that silently loses data, a `Down()` that doesn't actually undo the `Up()`. This skill reads the most recent migration in `Migrations/` together with the project's `ModelSnapshot.cs`, and reports exactly those kinds of risk before anyone runs `dotnet ef database update` against a real database.

Every finding is labeled as Observed, Hypothesis, Risk, or Recommendation. Because the skill never connects to a database, it has no way to know a table's actual row count or contents — so a risk like "this index creation may lock the table" is reported as a Hypothesis conditioned on real-world table size, never stated as a certainty it can't back up. The skill never edits the migration and never applies it; it only reports.

## When to use it

- Right after `dotnet ef migrations add`, before running `dotnet ef database update` against a shared or production database.
- When reviewing a migration someone else generated, to catch what code review alone tends to miss (rollback asymmetry, disguised renames, missing defaults).

Not the right skill for generating a new migration, or for analyzing query performance — that's a separate concern.

## What it guarantees

- **Static analysis only** — reads the migration's `Up()`/`Down()` code and the project's `ModelSnapshot.cs`; never connects to a database and never assumes table size.
- **Pre-existing vs. brand-new tables distinguished** — risk checks only apply to tables/columns that existed before this migration; nothing on a table created in the same migration is flagged, since it can't have any data yet.
- **Every finding is labeled by evidence strength** — Observed, Hypothesis, Risk, or Recommendation, never presented as more certain than the evidence supports.
- **Read-only and advisory** — never edits the migration file, never runs `dotnet ef database update`. The decision to apply the migration always stays with the user.
