# EF Core Query Performance Review

Diagnoses and reviews the performance of Entity Framework Core / LINQ code the user points to, working strictly from evidence — every finding is labeled Observed, Hypothesis, Risk, or Recommendation, and no bottleneck is ever declared without generated SQL, an execution plan, or a measured metric backing it.

## What it is

EF Core code can look fine and still hide N+1 loading, unnecessary tracking, premature materialization, or an unstable pagination strategy — and just as often, a suspected "slow query" turns out to have its root cause in a missing index, stale statistics, or the data model, not the LINQ itself. This skill follows the full path a query takes — from C# through the expression tree, EF Core's translation, the generated SQL, the execution plan, and materialization — instead of stopping at "does the LINQ look reasonable."

Every claim is graded by the strength of its evidence. When static analysis of the code and generated SQL text isn't enough to confirm something — most commonly, whether N+1 is actually issuing extra queries — the skill can build a disposable SQLite in-memory context using the project's real entity model to measure the actual query count. That evidence is always labeled as SQLite-specific: it confirms query count and shape, which is provider-independent, but it never stands in for execution-plan-level evidence (index usage, logical reads) that only the project's real database provider can provide.

## When to use it

- A specific query or repository method is suspected of being slow, or is confirmed slow and needs root-cause diagnosis.
- Comparing two implementations of the same data access logic to decide which is actually better, based on generated SQL, query count, and materialization — not code appearance.
- Reviewing EF Core/LINQ code for tracking strategy, `Include`/`AsSplitQuery` trade-offs, or set-based write operations before merging.

Not the right skill for reviewing a migration's operational safety (see `ef-migration-safety-review`) or for scanning an entire project unprompted — it only analyzes what's pointed to. Also out of scope: database server administration (HA, backup, patching, server configuration) and layered/stack architecture decisions.

## What it guarantees

- **Evidence-graded findings** — every claim is labeled Observed, Hypothesis, Risk, or Recommendation; when evidence is missing, the skill states exactly what would need to be collected instead of rounding up to a conclusion.
- **No blanket recommendations** — `AsNoTracking()`, `AsSplitQuery()`, compiled queries, new indexes, or set-based writes are never suggested as a default rule, always conditioned on the concrete scenario.
- **Provider-aware** — never assumes SQL Server, PostgreSQL, MySQL, SQLite, Oracle, or Cosmos DB behave the same; flags when a recommendation is provider-dependent.
- **SQLite in-memory evidence used sparingly and labeled honestly** — only as a deeper step when static analysis can't confirm a hypothesis, and always flagged as not identical to the project's real provider.
- **Never edits code** — delivers diagnosis and suggested code for the user to apply themselves.
