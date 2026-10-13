# Claude Code reference for harness-permissions

Read from the official Claude Code documentation on 2026-10-12. Parts marked "run" were exercised with Claude Code 2.1.296 on Windows. Re-check the documentation before relying on a detail: rule syntax and defaults change between versions.

## 1. Where permission rules live

| File | Scope |
| --- | --- |
| `.claude/settings.json` | The project, shared and committed |
| `.claude/settings.local.json` | The project, personal, not committed |
| `~/.claude/settings.json` | The user, all projects (do not edit from this skill) |
| Managed settings | The organization (never edit) |

Rules from all levels apply together. **A deny at any level cannot be overridden by an allow at another.** Managed settings are highest. Settings files must be strict JSON (no comments).

```json
{
  "permissions": {
    "allow": ["Bash(npm run *)"],
    "ask": ["Bash(git push *)"],
    "deny": ["Read(./.env)"]
  }
}
```

Evaluation order: deny first, then ask, then allow.

## 2. Rule syntax

A rule is `Tool` or `Tool(specifier)`. Parentheses inside a specifier are literal.

| Rule | Effect |
| --- | --- |
| `Bash` or `Bash(*)` | All shell commands. As a deny, it removes the tool. Never use as an allow. |
| `Bash(npm run build)` | Exactly that command |
| `Bash(npm run *)` | A command prefix, with a wildcard |
| `Read(./.env)` | Reading that file |
| `Edit(/Directory.Build.props)` | Editing that file (see section 4 for the path anchors) |
| `WebFetch(domain:example.com)` | Fetching from a domain |

Bash wildcard rules:

- `*` matches any text, including spaces, anywhere in the rule.
- **Put the wildcard after the subcommand.** `Bash(git log *)` allows only `git log`. `Bash(git *)` allows every git command. A wildcard before the subcommand, such as `Bash(git * main)`, matches far more than intended, and the tool warns about it in an allow rule.
- A trailing ` *` with a space also matches the bare command. The space matters: `Bash(ls *)` does not match `lsof`, and `Bash(ls*)` does.
- `Bash(ls:*)` is an equivalent way to write a trailing wildcard, recognized only at the end.
- Compound commands (`&&`, `||`, `;`, `|`, `&`, newlines) are split. An allow rule must match each part. A deny or ask rule applies when any part matches, including inside a subshell or a loop body.
- A fixed set of wrappers is stripped before matching (for example `timeout`, `time`, `nice`, `nohup`, `stdbuf`). Environment runners such as `npx`, `docker exec` or `devbox run` are not stripped, so a rule for them matches whatever comes after.
- A `Bash(command:...)` rule is ignored with a warning. Match the command text directly.
- For a rule that looks at one top-level parameter of a tool, deny and ask rules accept `Tool(param:value)`. The tool's main content field (command, file path, URL) cannot be matched this way.
- Rules for MCP tools do not accept parentheses.

## 3. What the rules do not cover (limits)

**Run:** with a deny rule `Bash(echo FORBIDDEN *)`, the direct command was refused with a "denied" message. A command wrapped in `sh -c '...'` was **not matched by the deny rule**: the agent was refused only because it had no allow rule, and the message was that approval was required. In a session where Bash is allowed or approvals are given, the wrapped form would have run. The documentation lists the same gap for other forms: a full path to the program, `sh -c`, and options placed before the subcommand (for example `git -C . push`).

So a Bash deny rule is a guard on the form the agent usually writes, not a security boundary. Stronger controls: a hook that inspects the full command text (see `harness-hooks`), and the sandbox for filesystem and network enforcement.

Read and edit rules:

- Apply to the built-in file tools and to file commands the tool recognizes in the shell (such as `cat`, `head`, `tail`, `sed`, `tee`) and to redirection targets.
- Do not apply to a program that opens files on its own (a script in any language), or to commands that read without naming files.
- A `Read` deny rule also blocks editing and writing that path, including creating a new file there.
- The tool makes a best-effort attempt to apply `Read` rules to Grep, Glob and `@file` mentions.
- A `.claudeignore` file has no effect. Use `Read` deny rules.

## 4. Path patterns for Read and Edit

Patterns follow `.gitignore` syntax.

| Pattern | Meaning |
| --- | --- |
| `//path` | Absolute path from the filesystem root |
| `~/path` | From the user's home directory |
| `/path` | Relative to the settings file that defines the rule. In project settings: the project folder. In user settings: the user's config folder. |
| `path` or `./path` | Relative to the current directory |

A single leading slash is **not** an absolute path. A bare filename matches at any depth, so `Read(.env)` and `Read(**/.env)` are equivalent. For a single-segment directory pattern such as `secrets/**`, a deny or ask rule matches that directory at any depth, while an allow rule matches only at the top. On Windows, paths are normalized to POSIX form before matching (`C:\Users\x` becomes `/c/Users/x`).

**Use `Edit(path)`, not `Write(path)`.** The tool consults only `Edit` and `Read` path rules. A path rule for `Write`, `NotebookEdit` or `Glob` is accepted and never used, and the tool warns at startup. `Edit` rules apply to all built-in tools that edit files.

**Run:** an `Edit(/protected.txt)` ask rule in project settings made the edit refuse in a non-interactive run, and an edit of an unlisted file went through. A `Read(./.env)` deny rule refused the read.

## 5. Trust and where allow rules take effect

`allow` rules and `additionalDirectories` in the shared project file grant capability, so they apply only after the folder is trusted in an interactive session. `deny` and `ask` rules always apply, because they only restrict.

**Run:** in a non-interactive run in a folder that had never been trusted, an allow rule in `.claude/settings.json` was ignored, with a warning that the workspace has not been trusted. The same allow rule in an untracked `.claude/settings.local.json` took effect and a matching command ran without approval, while a command not matching any rule was refused. The documentation says a local settings file that is tracked by git is treated as repository-supplied and held until trust, and that the local file must not be committed.

Consequence: put the allow rules you rely on in the local file, or accept that they are ignored in continuous integration and scripted runs, and keep deny and ask rules in the shared file. The local file is not committed, so it is absent from a continuous-integration checkout: it helps developers on their own machines, not the pipeline.

For continuous integration, other ways to grant a command exist, such as passing the allowed tools on the command line (`--allowedTools`) or generating a local settings file in the job. **Not verified here**: check the current documentation and try it before recommending one. Deny and ask rules in the shared file still apply, and an ask refuses because nobody can answer.

## 6. Hooks and permissions together

A hook that blocks (exit status 2) stops a call before permission rules are evaluated, even when an allow rule would have approved it. A hook cannot override a deny or an ask rule by returning allow. So deny rules and blocking hooks stack, and an allow can never loosen a deny.

## 7. Lint checklist

Before writing a rule, check:

- The tool name is spelled as in the tool list (for example `Bash`, `Read`, `Edit`, `WebFetch`), with no label text.
- Path rules use `Edit` or `Read`, never `Write`, `NotebookEdit`, `MultiEdit` or `Glob`.
- A Bash rule matches the command text with a wildcard after the subcommand, and no `command:` parameter form.
- An absolute path starts with `//`. A single leading slash means relative to the settings file.
- On Windows, absolute drive paths are written in the normalized form (`//c/...`).
- No allow rule is the bare tool name, a lone wildcard, or a prefix that is a general runner (a shell, an interpreter, an environment runner).
- The rule does not rely on matching an argument of a network tool, which is easily bypassed.
- A secret-file pattern does not also cover the example file the agent should read. `Read(./.env.*)` matches `.env.example` too, and a deny wins over any allow, so name the real variants instead.
- The settings file stays valid JSON with no comments, and rules are not duplicated.

Replacement guidance for the usual malformed rules (always shown as a preview and confirmed, in the same list as the original):

| Malformed | Replace with |
| --- | --- |
| `Write(<path>)` (and other non-path tool names) | `Edit(<path>)` |
| `Bash(command:<text>)` | `Bash(<text>)` |
| A wildcard in the middle or at the start of a command, such as `Bash(git * main)` | A narrow rule that names the command, for example `Bash(git push origin main)`, kept in the same list (`ask` or `deny`) |

## 8. Startup warnings as a validator

The tool checks the rules when a session starts and prints a warning for each malformed one, with the reason and the fix. In a non-interactive call they appear before the answer. The cheapest check is a one-line call:

```sh
claude -p "Reply with the single word: ok" --model haiku --max-budget-usd 0.10 --no-session-persistence < /dev/null
```

It uses the model for a short reply, so ask first. No warning means the syntax is accepted, not that the rules do what you intend. For that, run the exercise in section 9.

**Run:** a settings file with `Write(./protected.txt)`, `Bash(command:rm *)` and an allow rule `Bash(git * main)` produced three warnings: the `Write` path rule is not consulted (use `Edit`), the `command:` form targets a raw string and will not match, and the wildcard before the subcommand also matches inserted options and approves them. A well-formed `Edit(/protected.txt)` rule in the same file produced no warning.

## 9. Proving the rules in a real run

A bounded non-interactive session, with the permission mode left at its default so that allow rules are what grants things:

```sh
claude -p "<steps that try each rule, asking for a numbered report that quotes each refusal and says not to try alternatives>" \
  --model haiku --max-budget-usd 0.40 --permission-mode default --no-session-persistence < /dev/null
```

It uses the model, so ask first. Run it in the project folder. Check files afterward to see which actions really happened. Remember that ask rules refuse in non-interactive runs, and that allow rules in the shared file are ignored there until the folder is trusted.

## 10. Verified on

2026-10-12. Documentation read: the permissions page (rule syntax, wildcard rules, compound commands, wrappers, what a Bash rule does not match, read and edit rules and path anchors, symlinks, hooks interplay, settings precedence, trust for allow rules). Runs with Claude Code 2.1.296: a `Read` deny, a `Bash` deny and its `sh -c` gap, an `Edit` ask in a non-interactive run, the allow rule ignored in the untrusted shared file, the same allow rule honored from the untracked local file, and the startup warnings for three malformed rules.

Also checked on the same date, with git's own matcher: the pattern `.env.*` matches `.env.example`. The documentation says path rules follow `.gitignore` syntax, so the same applies here, but the rule was not run in Claude Code.

Not verified in this pass: WebFetch and MCP rules, CI alternatives for allow rules (`--allowedTools` and a generated local file), symlink behavior, protected-path behavior in each permission mode, managed settings, interactive prompts, and any other Claude Code version.
