# Appsettings Secrets Audit

Audits an ASP.NET Core project's configuration files for hardcoded secrets and insecure configuration, cross-referencing every finding against git tracking status so a real committed exposure is never confused with a harmless local-only placeholder.

## What it is

A `Password` or `ConnectionString` key sitting in `appsettings.json` isn't automatically a problem — it depends on whether the value is a placeholder or something real, and whether the file is actually tracked by git or gitignored and local-only. This skill walks every `appsettings*.json` and `launchSettings.json` file in a project, checks each one's git tracking status first, then scans for key names that suggest a secret (passwords, API keys, connection strings, signing keys, tokens) and evaluates whether the value looks like a placeholder or something real.

Every finding is labeled Observed, Hypothesis, Risk, or Recommendation. The skill can observe a key's name, a value's shape, and whether a file is tracked by git — it cannot verify whether a credential is actually live, so it never claims that with more certainty than the evidence supports. It also checks for production-looking values sitting in the base `appsettings.json` that's typically committed and shared, instead of being layered in only at deploy time.

## When to use it

- Before a commit or PR that touches configuration files, to catch a secret before it's pushed.
- Auditing an existing project's configuration hygiene — hardcoded credentials, missing Dev/Prod separation, secrets in files that shouldn't have them.

Not the right skill for auditing NuGet package vulnerabilities, or for reviewing architectural use of `IOptions<T>` — this skill is scoped strictly to secret exposure and configuration security.

## What it guarantees

- **Git tracking checked first** — every finding is qualified by whether the file is actually tracked by git or gitignored/local-only, since those carry very different real-world risk.
- **Placeholders distinguished from real-looking values** — a `CHANGE_ME`-style value isn't flagged as a finding; only values that plausibly look real are.
- **Evidence-graded findings** — Observed / Hypothesis / Risk / Recommendation, never claiming a credential is confirmed-live when the skill has no way to verify that.
- **Read-only and advisory** — never edits a configuration file, never removes or rotates a secret, never attempts to use a credential to check if it's live. Acting on a finding is always the user's decision.
