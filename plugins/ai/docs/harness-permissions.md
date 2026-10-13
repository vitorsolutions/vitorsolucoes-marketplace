# Harness Permissions

Sets the permission rules of an AI coding agent for one project: what it may run without asking, what it must ask about or never run, which secret-bearing files it must not read, and which configuration files it must not edit without confirmation.

## Why this skill exists

Permission rules are the simplest control over what the agent can do, and they decide how often it interrupts you. Most projects end up with a pile of rules accumulated one prompt at a time, some too broad and some malformed. This skill writes a small, deliberate set derived from the project instead.

## What it does

- Detects the agent and the stack and reads the existing project settings.
- Proposes rules in five groups: verification commands to allow, remote and data commands to ask about or deny, secret-bearing files to deny reading, check configuration files to protect from edits, and the agent's own settings and hooks to protect.
- Lints every rule against the tool's syntax, including the traps (a path rule that is never consulted, a command form that never matches, a wildcard in the wrong place).
- Shows the exact merged change and writes it only after confirmation, without removing or reordering anything.
- Answers review and "what can rules do" questions without writing anything, and declines broad allow rules while offering exact ones for the commands your definition of done uses.
- Reads the tool's startup warnings to validate the rules and, with your permission, exercises them in a short capped run.

## Supported agent and stacks

Claude Code, with stack content for .NET and Python in `references/stacks/`. The agent details are in `references/claude-code.md`.

## What it will not do

- Write broad allow rules, such as a bare tool name or a prefix that is a general runner.
- Change the permission mode, enable any bypass, or edit user-level or managed settings.
- Open the contents of the files it proposes to protect.
- Commit or stage anything.

## When to use it

When you want fewer prompts without giving up control: "stop the agent from reading .env", "let the agent run the build without asking", "protect the config files".

## Limits

A command deny rule matches text. It is not a security boundary, because other forms of the same command may not match. Read and edit rules cover the built-in file tools and recognized file commands, not programs that open files themselves. Allow rules in the shared project file need a trusted folder and are ignored in non-interactive runs. Ask rules refuse when nobody can answer. For hard boundaries use hooks and the sandbox.
