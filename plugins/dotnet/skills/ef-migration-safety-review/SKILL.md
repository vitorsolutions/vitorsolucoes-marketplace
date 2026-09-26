---
name: ef-migration-safety-review
description: >
  Reviews the most recently generated Entity Framework Core migration for operational safety risks
  before it gets applied to a real database — missing defaults on new NOT NULL columns, irreversible
  drops, renames disguised as drop+add, incomplete Down() rollback, and blocking index creation. Use
  this whenever the user asks to "review this migration", "check this EF Core migration before
  applying it", "is this migration safe to run", "revisa essa migration antes de aplicar", "essa
  migration é segura", or right after running `dotnet ef migrations add` and before `dotnet ef
  database update`. Static analysis only — reads the migration's Up()/Down() code and the project's
  ModelSnapshot.cs, never connects to a real database and never estimates actual table size. Always
  produces a report, classifying each finding as Observed, Hypothesis, Risk, or Recommendation — never
  silently declares something safe or dangerous without stating which category the claim falls into.
  Do NOT use this skill to generate a new migration (that's plain `dotnet ef migrations add`, or ask
  the user to run it) or to analyze query performance (see a dedicated EF Core performance skill for
  that). Never edits the migration file and never runs `dotnet ef database update` itself — this is a
  read-only, advisory skill; the decision to apply the migration always stays with the user.
---

# EF Migration Safety Review

## Your role

You are reviewing a migration that Entity Framework Core already generated — not writing one, not deciding whether it should exist. Your job is to surface operational risk *before* someone runs it against a real database, using only what's verifiable from the migration's own code and the project's current model snapshot.

This is a static-analysis skill by design: it never connects to a database, so it never knows the real row count of a table. That constraint shapes how findings must be reported — a risk that depends on unknown table size is a **Hypothesis**, not an **Observed** fact, and the report must say so explicitly. Blurring that line is worse than not flagging the risk at all, because it teaches the user to distrust every finding equally instead of trusting the ones that are actually certain.

## Step 1 — Locate the migration to review

1. List the files in the project's `Migrations/` folder (skip `*.Designer.cs` and `*ModelSnapshot.cs` — those are metadata, not the migration itself).
2. EF Core names migration files with a sortable timestamp prefix (`YYYYMMDDHHMMSS_Name.cs`). Pick the most recent one by that prefix.
3. Read that file's `Up()` and `Down()` methods, and read the project's `*ModelSnapshot.cs` in full — the snapshot reflects the schema's state *after* this migration, which you'll use in Step 2 to tell new tables/columns apart from pre-existing ones.

If `Migrations/` doesn't exist or is empty, say so and stop — there's nothing to review.

## Step 2 — Classify what's pre-existing vs. brand new

For every operation in `Up()` (`CreateTable`, `AddColumn`, `DropColumn`, `RenameColumn`, `AlterColumn`, `CreateIndex`, `DropIndex`, `AddForeignKey`, `DropForeignKey`, `DropTable`, raw `Sql(...)`, etc.), determine whether it targets a table that:

- **Is created in this same migration** (via a `CreateTable` earlier in the same `Up()`) — no existing rows are possible, so most of the risks below don't apply to it.
- **Already existed before this migration** — infer this by checking whether the table appears in the `ModelSnapshot` in a way that predates this migration's changes (e.g., a column being altered/dropped must already be a property on that entity in the snapshot, which only reflects the final state — cross-check that the operation is a *modification* of something the snapshot already describes, not the creation of something new in this same file).

Only operations against pre-existing tables get evaluated in Step 3 — flagging risk on a table that doesn't have any rows yet (because it's brand new) would be noise, not signal.

## Step 3 — Apply the risk checks

For each operation against a pre-existing table:

- **`AddColumn` with `nullable: false` and no `defaultValue`/`defaultValueSql`** — Risk. Existing rows have no value to put there; this either fails outright or requires a value EF Core can't infer. Recommendation: add a default, or split into two migrations (add nullable → backfill → a follow-up migration that tightens to `NOT NULL`).
- **`DropColumn` or `DropTable`** — Risk, always, regardless of anything else. This is irreversible data loss the moment it runs against real data. State this as Observed (the operation itself is unambiguous), and flag the consequence (data loss) as certain, not hypothetical.
- **A `DropColumn` immediately followed by an `AddColumn` of similar/same type** (same table, correlated names) — Risk: this is very likely a column rename implemented the "wrong" way by whatever generated it, which drops the data instead of preserving it via `RenameColumn`. Flag explicitly as "looks like a disguised rename — verify whether data preservation was intended."
- **`AlterColumn` changing type or tightening nullability** — Risk: conversion can fail or truncate existing values depending on the data currently in that column. Since you can't see the actual data, this is a Hypothesis, not an Observed fact — state that the failure is conditional on what's actually stored.
- **`CreateIndex` on a pre-existing table without an online/concurrent option** (e.g., missing `[Online = ON]` for SQL Server or not using `CONCURRENTLY` for PostgreSQL-targeted raw SQL) — Hypothesis: this can lock the table for the duration of the index build, but whether that's actually a problem depends entirely on the table's real size and traffic, which this skill cannot see. State the mechanism (why locking happens) as Observed, and the actual impact as a Hypothesis the user needs to confirm against their production table size.
- **`AddForeignKey` on a pre-existing table** — Risk: will fail if any existing row's foreign key value doesn't match a valid parent row. Flag as conditional on current data integrity.
- **Raw `Sql(...)` calls** — Flag as "not verifiable by static analysis — read this SQL manually," since arbitrary SQL can do anything and this skill isn't executing it.

Operations against tables created in this same migration are not risk-checked — mention them in the report only as context ("N new tables created, no pre-existing-data risk").

## Step 4 — Check Up()/Down() symmetry

For every operation in `Up()`, verify `Down()` contains a plausible inverse in reverse order (`CreateTable` ↔ `DropTable`, `AddColumn` ↔ `DropColumn`, `RenameColumn` ↔ `RenameColumn` with names swapped, `AddForeignKey` ↔ `DropForeignKey`, `CreateIndex` ↔ `DropIndex`). Any `Up()` operation without a corresponding undo in `Down()` is a Risk: rollback is incomplete, and reverting this migration won't fully restore the prior schema.

## Step 5 — Produce the report

Structure the report around the findings, not the steps above. For each finding, state:

- **What operation triggers it** (table/column, line reference if useful).
- **Classification**: Observed / Hypothesis / Risk / Recommendation — pick the ones that actually apply; a single finding often carries more than one (e.g., an unindexed `CreateIndex` is both an Observed mechanism and a Hypothesis about impact, paired with a Recommendation).
- **Why it matters** — the concrete failure mode, not a generic warning.
- **What to do about it**, when there's a clear fix.

End with an explicit reminder that this review is static-only: it doesn't know the real size or contents of any table, so any Hypothesis-tagged finding needs the user's own knowledge of their production data to resolve. Never run `dotnet ef database update` as part of this skill, and never edit the migration file — report only; the user decides what to do with the findings.
