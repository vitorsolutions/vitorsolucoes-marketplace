# Claude Code reference for harness-hooks

Everything here was read from the official Claude Code documentation on 2026-10-12, and the parts marked "run" were exercised with Claude Code 2.1.296. Re-check the documentation before relying on a detail: events, fields, and options change between versions.

## 1. Where hooks are configured

| File | Scope |
| --- | --- |
| `.claude/settings.json` | The project, shared and committed |
| `.claude/settings.local.json` | The project, personal, not committed |
| `~/.claude/settings.json` | The user, all projects (do not edit from this skill) |
| Managed settings | The organization (never edit) |

Hook entries from every level are merged and the matching ones run in parallel. Identical handlers defined in several files run once. Edits to the files are picked up by a file watcher during a session.

## 2. Settings entry used by this skill

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/harness_hooks.py", "suppressions"],
            "onFailure": "block"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/harness_hooks.py", "bash-guard"],
            "onFailure": "block"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/harness_hooks.py", "prompt-guard"],
            "onFailure": "block"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/harness_hooks.py", "stop"],
            "timeout": 900
          }
        ]
      }
    ]
  }
}
```

The Stop `timeout` (900 here) is a value to recompute for each project, not to copy: see the `timeout` note below.

Notes on each part:

- **Argument-list form.** `command` is the program and `args` its arguments, with no shell involved. This avoids quoting problems with paths that contain spaces. It was run on Windows with `python` on the path. On Windows, this form needs a real executable (an `.exe`), not a `.cmd` or `.bat` shim. The shell form is `"command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/harness_hooks.py\" stop"`, which was not run here. Use it only for a version that does not accept `args`.
- **`${CLAUDE_PROJECT_DIR}`** is the project root where the session started. It was expanded inside `args` in the run.
- **Program name.** Use the interpreter name that works on the machine (`python`, `python3`, or the launcher). Check with its version command.
- **`onFailure: "block"`** makes the hook fail closed when it cannot run at all (for example the interpreter is not found). Documented from version 2.1.295. **Run:** with a missing interpreter and no `onFailure`, a shell command went through (the hook failed without blocking). With `"onFailure": "block"`, the same command was blocked and the agent was told the hook could not run. It does not apply to the Stop event, so the stop guard cannot fail closed this way.
- **`timeout`** is in seconds. The documented default for command hooks is 600, and 30 for the prompt event. The `900` on the Stop entry above is a placeholder: it must be larger than the sum of the configured `timeout` values (not of the measured durations) of the definition-of-done commands in `harness-hooks.config.json` (the script's per-command default is 600). An 8-minute suite takes 480 seconds, so a Stop `timeout` of 300 would cut it off. `python .claude/hooks/harness_hooks.py check` prints that sum.
- **Matcher.** Letters, digits, `_`, `-`, spaces, commas and `|` are matched exactly (so `Edit|Write` is a list of two tool names). Anything else is an unanchored regular expression.

## 3. Events used and their contract

| Event | Fires | Blocks? | Input fields used |
| --- | --- | --- | --- |
| `PreToolUse` | Before a tool call | Yes | `tool_name`, `tool_input` |
| `UserPromptSubmit` | When a prompt is submitted | Yes | `prompt` |
| `Stop` | When the agent finishes responding | Yes: the agent keeps working | `stop_hook_active`, `cwd` |

Common fields on the input: `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `permission_mode`.

Tool inputs: `Edit` has `file_path` (absolute, with backslashes on Windows), `old_string`, `new_string`, `replace_all`. `Write` has `file_path` and `content`. `Bash` has `command`.

Exit statuses:

- **0**: success. A JSON object on stdout is read for decisions. For `PreToolUse`, `hookSpecificOutput.permissionDecision` takes `allow`, `deny`, `ask` or `defer`, and the script uses `ask` to request a confirmation.
- **2**: blocking. stderr is the message. For `Stop`, it stops the agent from finishing. For `UserPromptSubmit`, the prompt does not reach the agent.
- **Any other status, including 1**: a non-blocking error. The action goes ahead. This is why the script never exits with 1.

Failure behavior: a hook that crashes or times out lets the action proceed (fail open), except where `onFailure` is set. A `PreToolUse` hook that times out does not block.

## 4. The stop event and loops

`stop_hook_active` is true when the agent is already continuing because of a stop hook. Claude Code ends the turn after 8 consecutive blocks (an environment variable raises that cap, and the count resets when the agent calls a tool). **Run:** a stop guard whose check failed told the agent what was missing, the agent created the missing file, and the next stop passed. The stop guard re-runs the checks on every stop. It does not return early when `stop_hook_active` is true, because a failure that the agent can fix should keep blocking. The only exception is the guard's own failure, where it lets go to avoid a loop.

The stop event fires whenever the agent finishes responding, including a response that changed nothing. The script's default (`"when": "changed"`) skips the checks when the working tree has no changes.

## 5. Self-test commands

Run from the project folder. Replace the paths if the hooks folder differs. These check the script only, not the wiring.

Build the sample events with Python's `json.dumps`, not with `echo` or a quoted JSON string: a shell can mangle backslashes (a Windows path such as one ending in `\Migrations` is a common victim) and the result is then a false "blocked" or a false "allowed".

In a POSIX shell:

```sh
python -c "import json; print(json.dumps({'tool_name':'Bash','tool_input':{'command':'git push --force'}}))" | python .claude/hooks/harness_hooks.py bash-guard; echo "exit=$?"
python -c "import json; print(json.dumps({'tool_name':'Bash','tool_input':{'command':'git status'}}))" | python .claude/hooks/harness_hooks.py bash-guard; echo "exit=$?"
python .claude/hooks/harness_hooks.py check
```

In PowerShell:

```powershell
python -c "import json; print(json.dumps({'tool_name':'Bash','tool_input':{'command':'git push --force'}}))" | python .claude/hooks/harness_hooks.py bash-guard; "exit=$LASTEXITCODE"
python .claude/hooks/harness_hooks.py check
```

Expect exit `2` and a message for the first, `0` for the second, and a line starting with "configuration ok" for the check. The check also prints a `warning:` line for each done command whose program is not found on the machine, and a `note:` line with the total of the command timeouts. A command whose `timeout` is not a positive number is an error. Build one blocked sample and one allowed sample for each guard that was installed. For the suppression guard, use an `Edit` event whose `new_string` contains a configured marker. For the prompt guard, use a fake credential that you made up.

## 6. Proving the wiring in the real agent

A bounded non-interactive run proves that the settings entry works. It uses the model, so ask first. The pattern used here:

```sh
claude -p "<a prompt that triggers the guard, and asks for a one-sentence report quoting any block message>" \
  --model haiku --max-budget-usd 0.30 --permission-mode acceptEdits --no-session-persistence < /dev/null
```

Run it in the project folder. Redirecting input from nothing avoids a wait for standard input. The spending cap bounds the cost. Check the side effect too (the blocked file should not exist), not only what the agent says. Also run one control that should pass, to show the guard is not blocking everything.

Runs that were performed with Claude Code 2.1.296 on Windows:

- A shell command matching a deny pattern was blocked and the agent quoted the message.
- Writing a source file containing a suppression marker was blocked and no file was created. Writing a file without one succeeded.
- A stop guard with a failing check blocked the finish, and the agent fixed it and finished.
- A hook whose interpreter was missing let a command through without `onFailure`, and blocked it with `"onFailure": "block"`.

## 7. Cautions from the documentation

- Command hooks run arbitrary commands with the user's permissions. Review what they run.
- The `if` field on a handler (a permission-rule filter) is best-effort. The script does its own matching instead.
- Hooks in project settings run for a trusted folder. Hooks can be turned off with `disableAllHooks`, or for one run with a command-line settings override, and only managed settings can force them on. A guard is a guard rail, not a security boundary.
- Write context returned to the agent as factual statements. Text written as commands can trigger the tool's prompt-injection defenses.
- Output over about ten thousand characters is saved to a file and replaced by a preview. The script keeps its messages short.

## 8. Verified on

2026-10-12. Documentation read: the hooks reference (events, exit statuses, JSON output, handler fields, matchers, timeouts, failure behavior, settings locations, environment variables, Windows notes, the stop event and its loop cap, tool input fields), up to the portion of the page that describes the configuration-change event's input, which was not read. The four runs listed in section 6 were executed with Claude Code 2.1.296 on Windows.

Not verified in this pass: the configuration-change event, HTTP and prompt-type handlers, the shell form of the command, other operating systems, and any Claude Code version other than 2.1.296.
