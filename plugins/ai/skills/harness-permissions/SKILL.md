---
name: harness-permissions
description: >-
  Sets the permission rules of an AI coding agent for one project: which verification commands it
  may run without asking, which commands that act on remote systems or shared data it must ask
  about or never run, which secret-bearing files it must not read, and which configuration files,
  including its own settings and hooks, it must not edit without confirmation. Derives the rules
  from the project and its stack, shows the exact change before writing, merges into the project's
  settings without removing anything, lints every rule against the tool's syntax, and checks that
  the rules behave as written. Targets Claude Code, with stack content for .NET and Python. Use when
  the user asks to "set up agent permissions", "stop the agent from reading .env", "let the agent
  run the build without prompts", "protect the config files from the agent", "configurar
  permissões do agente", "bloquear leitura de segredos", "reduzir prompts de permissão com
  segurança", or wants allow, ask and deny rules for a project. Do NOT use it for logic that
  must inspect content or run a check (harness-hooks), to write the guide the agent reads
  (harness-agent-guide), or as an operating-system boundary.
---

# Harness permissions

## What this skill does

Permission rules are static: allow, ask, or deny, for tools, commands and paths. They are the simplest control over what the agent can do, and they also decide how often it interrupts you. This skill writes a small, deliberate rule set for the project instead of a pile of rules accumulated one prompt at a time.

Vocabulary:

- **Allow rule**: lets a matching action run without asking.
- **Ask rule**: always asks before a matching action.
- **Deny rule**: refuses a matching action. A deny rule at any level wins over any allow.
- **Rule**: a tool name, optionally with a specifier in parentheses, such as a command prefix or a path.

Division with `harness-hooks`: static rules belong here. Anything that has to look at content or run a check belongs in a hook. Protecting the hook files and the settings from edits is done here.

## Hard rules

- Never remove, reorder or move an existing rule between lists. Merge new rules in and skip duplicates. The one exception is a malformed rule that the tool ignores or warns about (see step 5): it may be corrected or replaced only as a previewed change that the user confirmed, keeping it in the same list.
- Never write broad allow rules: the bare tool name, a lone wildcard, or a command prefix that is also a general-purpose runner. An allow rule is a grant of capability.
- Never change the permission mode or enable any bypass of permissions.
- Never edit user-level or managed settings, and do not read them unless the user points to them. Write only to the project's settings, and ask whether it is the shared file (committed) or the local file (personal).
- Never open the contents of files you propose to deny. Choose them by name and location.
- Write JSON with the file-writing tool, never through a shell here-document, because backslashes get collapsed.
- Show the exact change and wait for confirmation. A dry run is the default.
- Never commit, push, or stage files.

## Workflow

### 1. Detect the agent and the stack

- **Question or review only**: if the user asks to review the existing rules, or asks what rules can and cannot do, run steps 1, 2 and 5 on the rules that exist (or answer from the known limits below), report the findings, and write nothing. For each malformed rule, show the corrected rule as a preview (see the replacement guidance in the agent reference) and apply it only after the user confirms, as a separate step.
- **Agent**: this skill supports Claude Code. Look for its project folder and instruction files. For another agent, say its rule format is not covered yet and stop.
- **Stack**: find the markers in each stack reference under `references/stacks/` and read each matching pack. A repository with two stacks gets the union of the rules, without duplicates. No matching pack: explain the idea in concept and stop.
- Read `references/claude-code.md` for the syntax, the evaluation order and the limits.

### 2. Read what exists

Read the project's settings files (the shared one and the local one) and report their permission rules. Do not rewrite them. Say that user-level and managed settings can also apply, and that a deny anywhere wins.

### 3. Gather the facts

From the repository and the user:

- **Verification commands** for the definition of done. Use the ones in the project's agent guide, and only those that were run and exited with success.
- **Commands that act on remote systems or shared data**, from the stack reference, plus the project's own deploy and release scripts.
- **Files that may hold secrets**, from the stack reference, found by name and location. Ask the user to confirm which are real. List the real variants by name (for example `.env` and `.env.local`) and leave out the example or sample files the agent should read. A pattern such as `.env.*` also matches `.env.example`, and a deny cannot be overridden by an allow, so a broad pattern would block the file you want it to read.
- **Configuration files that define the project's checks**, from the stack reference.
- **The agent's own configuration**: its settings files and its hooks folder.

### 4. Propose the rule set

Build the rules in these groups, and for each rule say why, and what it will not cover:

| Group | List | Rule of thumb |
| --- | --- | --- |
| Verification commands | allow | Exact commands, or a command prefix with the wildcard after the subcommand. Only those the definition of done uses. |
| Remote and data commands | ask, or deny | Ask when the action is legitimate against a local target. Deny when it never belongs in an agent session, such as publishing a package. |
| Secret-bearing files | deny (read) | A read deny rule also blocks edits to the same path. |
| Check configuration files | ask (edit), or deny | Ask when changes are sometimes legitimate. Deny only if the user wants to edit them by hand. |
| The agent's own settings and hooks | ask (edit), or deny | So the agent cannot remove its guards without a human noticing. |

Let the user move any rule between lists, and drop any rule.

If the user asks for a broad allow (a whole tool, or a runner such as `dotnet *` or `uv run *`), decline it and say why: it grants every subcommand and every argument. Then ask for the commands the definition of done really uses and offer exact rules for those.

### 5. Lint every rule

Before showing the change, check each rule against the checklist in the agent reference: the tool name, the specifier form, the wildcard position, the path anchor, the `Write` versus `Edit` trap, and the `Bash` rules that the tool ignores. Fix or drop rules that fail.

### 6. Choose the file and preview

- **Shared file** (committed): good for deny and ask rules, which only restrict. Allow rules in a shared file take effect only after the folder is trusted, and are ignored in non-interactive runs where trust was never accepted.
- **Local file** (personal): good for allow rules you want without a trust step. Make sure it is not committed.

Show the file, the exact lines to add, and the merged result. Wait for confirmation. If the user asked for a dry run, stop here.

For continuous integration or other non-interactive runs, say what happens: ask rules refuse, and allow rules in the shared file are ignored until the folder is trusted. Mention the alternatives in the agent reference (section 5), and say that they were not verified.

### 7. Apply and validate

1. Merge the rules into the chosen file with the file-writing tool. Keep every other key, and keep the file valid JSON.
2. Parse the file again and check for duplicates.
3. Read the tool's own warnings about the rules. The tool reports malformed rules at startup, with the reason and the fix. A minimal non-interactive call prints them before its answer (see the agent reference). It uses the model for one short reply, so ask first. If the user declines, tell them to look at the permissions view and the diagnostics command themselves.
4. Fix every warning, and run it again until there is none.

### 8. Check the rules behave (optional, with permission)

Rules have limits that are easy to misjudge, so prove them. Offer the bounded non-interactive run described in the agent reference. It uses the model, so ask first. Check the side effects, not only what the agent says. Include a control that should be allowed. If the user declines, say that the rules were linted but not exercised.

### 9. Report

| Rule | List | Why | Covers | Does not cover |
| --- | --- | --- | --- | --- |

Then list: the file changed, what was left out, which rules need the trust step, what was exercised in a real run and what was not, and the limits below.

## Known limits to state

- **A command deny rule is not a security boundary.** It matches the command text. The same program through another path, inside `sh -c`, or with options before the subcommand may not match. Hooks that look at the full command text and the sandbox are the stronger controls.
- **Read and edit rules apply to the built-in file tools and to file commands the tool recognizes in the shell. They do not apply to arbitrary programs** that open files themselves, such as a script. Only the sandbox enforces access at the operating system level.
- **Ask rules prompt only when someone can answer.** In non-interactive runs an ask is a refusal.
- **Allow rules in the shared project file need the folder to be trusted**, and are ignored without it.
- **Rules are only as complete as the list of files and commands you know about.**
- **Another settings level can add or override.** Deny wins everywhere. A user's own settings can allow things the project does not.

## What a stack reference must contain

Each file in `references/stacks/` follows this outline:

1. Detection markers
2. Verification commands to allow, as rule prefixes
3. Commands that act on remote systems or shared data, with a suggested list (ask or deny)
4. Files that commonly hold secrets, by name pattern
5. Configuration files that define the checks, as edit-protection candidates
6. Pitfalls and limits
7. Verified on (date, and what was not re-verified)
