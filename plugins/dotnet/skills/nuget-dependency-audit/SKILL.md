---
name: nuget-dependency-audit
description: >
  Audits a .NET project or solution's NuGet dependencies for known vulnerabilities, deprecated
  packages, and outdated versions, using the dotnet CLI's built-in `dotnet list package
  --vulnerable/--deprecated/--outdated` — no external API calls or scraping involved. Use this
  whenever the user asks to "check for vulnerable packages", "audit NuGet dependencies", "are there
  outdated/deprecated packages in this project", "verifica se tem pacote NuGet vulnerável", "audita as
  dependências desse projeto", or before a release/PR that should be checked for known dependency
  risk. Distinguishes direct from transitive dependencies and reports severity as given by NuGet's
  advisory data (Low/Moderate/High/Critical) — never invents a severity or a fixed version when the
  CLI output doesn't provide one, and always states that a clean result means "no known advisories at
  the time of the check" rather than "provably safe," since NuGet's advisory database can be
  incomplete or the check can run against a stale/offline package cache. Read-only and advisory —
  never runs `dotnet add package` to apply an upgrade, never edits a `.csproj` — only reports what was
  found and what a fix would look like. Does NOT check license compatibility (not exposed by the
  dotnet CLI) — scoped strictly to what `dotnet list package` natively provides.
---

# NuGet Dependency Audit

## Your role

You are reporting what the dotnet CLI's own vulnerability/deprecation/outdated data says about a project's dependencies — not inventing risk assessments from package names you recognize. Every finding in this audit traces back to an actual `dotnet list package` invocation; if a package isn't flagged by that command, don't flag it yourself based on general impressions about it.

## Step 1 — Locate the target

Find the `.sln` (preferred, covers every project at once) or, if there's no solution file, the `.csproj` files in the repository. `dotnet list package` operates on whichever target is passed to it — a solution audits every project in one pass.

## Step 2 — Run the three native checks

```
dotnet list package --vulnerable --include-transitive
dotnet list package --deprecated
dotnet list package --outdated
```

Run all three against the located solution/project. `--include-transitive` on the vulnerable check matters — a vulnerability in a transitive dependency (pulled in indirectly by a direct package) is just as real as one in a direct reference, and the fix path is different (there may be no direct upgrade available; it might require bumping the direct package that pulls the vulnerable transitive one, or an explicit transitive pin).

If the vulnerable/deprecated checks return nothing, don't report "no vulnerabilities" as a flat guarantee — report it as "no known advisories at the time of this check," since NuGet's advisory data can lag behind newly disclosed CVEs, and the check itself depends on the local package cache/feed actually being reachable and current. If the command output indicates it couldn't reach the configured NuGet feed, say so explicitly instead of treating a network failure the same as a clean result.

## Step 3 — Classify the findings

For each vulnerable package reported:

- **Severity** — exactly as reported by the CLI output (Low/Moderate/High/Critical). Never round up or down, and never assign a severity to something the CLI didn't rate.
- **Direct vs. transitive** — whether the project references it directly or it's pulled in by another package; this changes what the fix actually looks like.
- **Fixed version available** — report the resolved/fixed version the CLI output shows, if any. If no fixed version is listed, say so explicitly rather than guessing one.

For each deprecated package: report the reason given (if the CLI surfaces one — legacy, critical bugs, or other) and any suggested alternative package the output includes.

For each outdated (but not vulnerable or deprecated) package: report current vs. latest version. This is informational, not a security finding — being outdated by itself isn't a vulnerability, and the report should not conflate the two categories.

## Step 4 — Report

Structure the report in three sections matching the three checks — **Vulnerable**, **Deprecated**, **Outdated** — since they carry different urgency and shouldn't be flattened into one undifferentiated list. Within "Vulnerable," sort by severity, highest first.

For each vulnerable finding, state what upgrading would look like (`dotnet add package <Name> --version <FixedVersion>`) as information, not as an action taken — never run this command yourself. If the fix requires bumping a transitive dependency indirectly (via the direct package that pulls it in), say that explicitly instead of suggesting a command that wouldn't actually work.

End the report with the caveat from Step 2 restated plainly: this audit reflects known advisories at the time it ran, using whatever package feed was reachable — it is not a guarantee that unlisted packages are safe, only that nothing currently known was found against them.
