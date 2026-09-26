# NuGet Dependency Audit

Audits a .NET project or solution's NuGet dependencies for known vulnerabilities, deprecated packages, and outdated versions, using the dotnet CLI's own built-in checks — no external API calls or scraping involved.

## What it is

`dotnet list package --vulnerable`, `--deprecated`, and `--outdated` already give the dotnet CLI's own view of dependency risk, sourced from NuGet's advisory data — but that output is easy to skim past or run inconsistently. This skill runs all three against the located solution or project, including transitive dependencies for the vulnerability check (a vulnerable package pulled in indirectly is just as real a risk as a direct one, and needs a different fix path), and organizes the result into three clearly separated sections instead of one undifferentiated list.

Every severity and fixed-version claim traces back to what the CLI actually reported — nothing is inferred from a package name or general reputation. A clean result is reported as "no known advisories at the time of this check," not as a guarantee, since the advisory database can lag behind newly disclosed vulnerabilities and the check depends on the configured package feed actually being reachable.

## When to use it

- Before a release or PR that should be checked for known dependency risk.
- Periodic hygiene check on an existing project's NuGet dependencies.

Not the right skill for checking license compatibility — that's not exposed by the dotnet CLI and is out of scope here.

## What it guarantees

- **Native CLI data only** — every finding comes from `dotnet list package --vulnerable/--deprecated/--outdated`; nothing is invented from package reputation.
- **Transitive dependencies included** — the vulnerability check covers indirectly-pulled packages, not just direct references, since a transitive vulnerability is just as real.
- **Severity reported as-is** — never rounds a severity up or down, never assigns one to something the CLI didn't rate.
- **Vulnerable, Deprecated, and Outdated kept separate** — outdated-but-not-vulnerable packages are reported as informational, never conflated with an actual security finding.
- **Read-only and advisory** — never runs `dotnet add package` to apply an upgrade, never edits a `.csproj`. Acting on a finding is always the user's decision.
