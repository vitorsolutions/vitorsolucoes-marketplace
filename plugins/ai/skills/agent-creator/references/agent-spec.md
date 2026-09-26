# Current Claude Code agent/subagent specification

Verified against `https://code.claude.com/docs/en/sub-agents` and
`https://code.claude.com/docs/en/plugins-reference` on 2026-09-25, running Claude Code
2.1.248. **Re-check the live docs before relying on this for anything version-sensitive** —
this file is a snapshot, not the source of truth. If what you observe in the actual
repository (an existing agent using a field not listed here, or `claude plugin validate`
rejecting something this file says is valid) disagrees with this snapshot, trust what you
observe and update this file.

## File format and location

An agent is a Markdown file with YAML frontmatter. Location determines scope and load
priority (highest to lowest):

| Location | Scope | Notes |
|---|---|---|
| Managed settings | Organization-wide | Set by org admins, not by this skill |
| `--agents` CLI flag | Current session only | Not a persisted file |
| `.claude/agents/<name>.md` | Current project | **Default choice for most requests** — check into version control for team sharing |
| `~/.claude/agents/<name>.md` | Every project for this user | For personal, cross-project agents |
| A plugin's `agents/` directory (or the manifest's `agents` key) | Wherever the plugin is enabled | Namespaced as `<plugin-name>:<agent-name>` |

Ask (or infer from context) which scope the user actually wants before defaulting — a
request phrased as "add an agent to this project" almost always means `.claude/agents/`,
not a new plugin.

## Frontmatter fields

### Required

| Field | Type | Rules |
|---|---|---|
| `name` | string | Unique identifier. No `:` (reserved for plugin namespacing) and can't start with `-`. |
| `description` | string | When Claude should delegate to this agent. Counts toward a combined 15,000-token budget across all custom agents — Claude Code warns at startup if exceeded, so don't pad it. |

A file missing `name` is treated as plain documentation, not an agent. A file missing
`description` is silently skipped. A `name` violating the `:`/`-` rule is silently skipped.
None of these produce a loud error — check for them explicitly during validation.

### Optional

| Field | Type | Valid values | What it's for |
|---|---|---|---|
| `tools` | string or YAML list | Comma-separated or list of tool names; `mcp__<server>` / `mcp__<server>__*` for MCP tools, `mcp__*` for all MCP tools | Allowlist. Omit to inherit everything available. |
| `disallowedTools` | string or YAML list | Same shape as `tools` | Denylist, applied before `tools` is resolved. |
| `model` | string | `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit` | Which model runs this agent. Resolution order: per-invocation param → this field → `CLAUDE_CODE_SUBAGENT_MODEL` env var → main conversation's model. |
| `permissionMode` | string | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` | Overrides the inherited permission mode for this agent. |
| `maxTurns` | integer | Positive whole number | Caps agentic turns; output is marked partial if hit. |
| `skills` | array | Skill names | Preloads full skill content into the agent's context at startup — the mechanism for "agent should reuse this skill's workflow instead of re-describing it." |
| `mcpServers` | array/object | Server names or inline configs | MCP servers scoped to just this agent. |
| `hooks` | object | Hook definitions | Lifecycle hooks active only while this agent runs. |
| `memory` | string | `user`, `project`, `local` | Persistent memory directory across the agent's invocations. |
| `background` | boolean | `true`/`false` (default `false`) | Keeps the agent backgrounded even when Claude wants it foregrounded. Background agents get a reduced tool set (no `Agent`, `AskUserQuestion`, and a few others — see the live docs for the exact list). |
| `effort` | string | `low`, `medium`, `high`, `xhigh`, `max` | Reasoning effort override for this agent. |
| `isolation` | string | `worktree` | Runs the agent in its own git worktree branched from default. |
| `color` | string | `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan` | Cosmetic — display color in the task list. |
| `omitClaudeMd` | boolean | `true`/`false` | Skips loading user/project/local `CLAUDE.md` (requires a recent-enough Claude Code build). |
| `initialPrompt` | string | free text | Auto-submitted first turn, only relevant when the agent is invoked as the main session agent. |
| `experimental` | object | e.g. `{ cacheTtl: "5m" \| "1h" }` | Experimental knobs; don't rely on these being stable. |

Tools always removed from every subagent regardless of `tools`: `Agent` (except when the
agent itself is the top-level session), `AskUserQuestion`, `EndConversation`,
`EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`, and a
couple of other session-level-only tools. Don't design an agent around one of these being
available — it won't be.

## Plugin-provided agents

If the target is a plugin (not a bare project), the plugin's `agents/` directory is the
default scan location — one `.md` file per agent, `.md` required (directories aren't
accepted as agent entries). Subfolders under `agents/` become part of the agent's
namespaced name. Alternatively, `plugin.json` can declare an explicit `agents` key (a path
or array of `.md` paths, each relative to the plugin root and prefixed `./`) — this
*replaces* the default `agents/` scan rather than adding to it, so if you use the manifest
key and also want the default folder scanned, list it explicitly:
`"agents": ["./agents/", "./agents/extra-reviewer.md"]`.

A plugin's agent is invoked by Claude as `<plugin-name>:<agent-name>` — factor that into the
`name` you choose so the fully-qualified form still reads naturally.

## Minimal valid example

```markdown
---
name: code-improver
description: Scans files and suggests improvements for readability, performance, and best practices. Use after writing or modifying code.
tools: Read, Grep, Glob
model: sonnet
---

You are a code improvement specialist. For each issue you find, explain
the problem, show the current code, and provide an improved version.
```

## Validation checklist derived from this spec

- `name` and `description` both present.
- `name` has no `:`, doesn't start with `-`, and doesn't collide with an existing agent
  visible in the same scope (project `.claude/agents/`, user `~/.claude/agents/`, and any
  enabled plugin's `agents/`).
- Every entry in `tools`/`disallowedTools` is a real tool name or a valid `mcp__...`
  pattern — check against what's actually configured, not a guess.
- `model` (if set) is one of the documented aliases, a plausible full model ID, or `inherit`.
- Any `skills:` entry names a skill that actually exists and is reachable from where the
  agent will run.
- If this agent lives inside a plugin, run `claude plugin validate <plugin-path>` and
  resolve every reported error or warning, not just errors.
