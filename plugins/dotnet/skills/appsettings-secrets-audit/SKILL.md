---
name: appsettings-secrets-audit
description: >
  Audits an ASP.NET Core project's configuration files (appsettings*.json, launchSettings.json) for
  hardcoded secrets and insecure configuration — real-looking connection strings, API keys, signing
  keys, or passwords sitting in a file that's actually tracked by git, versus placeholders or
  local-only files that never leave the machine. Use this whenever the user asks to "check for exposed
  secrets", "audit appsettings for secrets", "is this connection string safe to commit", "verifica se
  tem segredo exposto na configuração", "audita esse appsettings.json", or before a commit/PR that
  touches configuration files. Cross-references every finding against git tracking status (a
  suspicious value in a gitignored file is a different risk level than the same value in a tracked
  file) and classifies each finding as Observed, Hypothesis, Risk, or Recommendation — never declares
  a value a "real secret" with certainty it can't back up; a string that merely looks
  credential-shaped could be a placeholder, and the skill says so when it can't be sure. Read-only and
  advisory — never edits configuration files, never removes or rotates a secret, only reports. Do NOT
  use this skill to audit NuGet package vulnerabilities (a separate concern) or to review general
  architectural use of IOptions<T> — this skill is scoped strictly to secret exposure and
  configuration security, not configuration style.
---

# Appsettings Secrets Audit

## Your role

You are looking for configuration that would hurt if it leaked — not grading code style. A `Password` key with the literal value `CHANGE_ME` is not a finding; the same key with something that looks like an actual credential, sitting in a file `git` actually tracks, is. The distinction between "looks like a secret" and "is exposed" matters enough to drive the whole structure of this audit — don't collapse it into a single flat list of scary-looking strings.

## Step 1 — Locate the files to audit

1. Find every `appsettings*.json` file in the project (`appsettings.json`, `appsettings.Development.json`, `appsettings.Production.json`, any other environment variant) and `Properties/launchSettings.json`.
2. Check the `.csproj` for a `<UserSecretsId>` element. Its presence is a good sign — it means the project has a Secret Manager configured for local development — but don't treat its absence as a finding on its own; just note it in the report as context (a project without it is more likely to lean on `appsettings.Development.json` for local secrets instead, which changes how much Step 2 matters for that file).

## Step 2 — Determine real exposure risk per file

For each file found in Step 1, check whether it's actually tracked by git (`git check-ignore <path>` or `git status --porcelain -- <path>` combined with checking `.gitignore` patterns) rather than assuming based on filename convention alone. This distinction is the difference between two very different risk levels:

- **Tracked by git** (or about to be, if untracked and not gitignored) — anything sensitive here is a real, committed exposure the moment it's pushed.
- **Gitignored / local-only** — a real-looking secret here is still worth flagging (it's still a secret sitting in plaintext on disk, and someone could `git add -f` it by mistake), but it's a materially lower-risk finding than the same value in a tracked file. Say this difference explicitly in the report instead of treating every file the same.

## Step 3 — Scan for secret-shaped values

Recursively walk each file's JSON structure. For every key, check whether the key name suggests a secret — case-insensitively matching things like `password`, `secret`, `apikey`, `api_key`, `token`, `connectionstring`, `privatekey`, `clientsecret`, `signingkey`, `accesskey`, `credential` — and inspect its value:

- **Looks like a placeholder** — contains things like `CHANGE_ME`, `YOUR_`, `xxx`, `<...>`, `TODO`, `REPLACE`, is empty, or is an obvious example value (`password123`, `test`) — not a finding, but worth a quick mention in the report as "placeholder, no action needed" so the user knows it was checked, not missed.
- **Looks like a real value** — non-trivial length, no placeholder markers, plausible shape for what the key claims to be (e.g., a connection string with an actual-looking host/user, a base64-looking signing key, a JWT-shaped token). This is where the Observed/Hypothesis distinction matters: the key name and value shape are **Observed** facts; whether it's an actually-live, currently-valid credential is a **Hypothesis** — this skill has no way to verify a secret is live, only that it looks real and isn't obviously a placeholder.

Also flag connection strings specifically, even under a generic key name (`ConnectionStrings` section entries) — these often carry a password inline (`Password=...`, `Pwd=...`) regardless of whether the section key itself contains the word "secret."

## Step 4 — Check for missing Dev/Prod separation

Look for values in `appsettings.json` (the base file, typically shipped/committed) that look environment-specific or production-shaped — a real hostname, a non-`localhost` connection string, a production-looking API endpoint — when the project also has `appsettings.Production.json` or environment variable-based overrides available. This suggests production configuration is living in the file most likely to be committed and shared, instead of being layered in only at deploy time.

## Step 5 — Report

For each finding:

- **File and key path** (e.g., `appsettings.json → Jwt:Key`).
- **Git tracking status** — tracked / gitignored, and what that implies for real exposure.
- **Classification** — Observed (what's directly visible: key name, value shape, tracking status) / Hypothesis (whether it's a live credential) / Risk (what happens if it's real and someone finds it) / Recommendation (move to User Secrets for local dev, environment variables or a secret manager for deployed environments — specific to what's actually missing, not a generic "use a vault" line).
- Note explicitly what was checked and found clean (placeholders, gitignored files with low-risk content) so the report reads as a completed audit, not just a list of problems.

Never edit any configuration file, never remove or rotate a value, never attempt to validate whether a credential is actually live by using it — this is a read-only, advisory audit; acting on a finding is always the user's call.
