#!/usr/bin/env python3
"""Configuration-driven hook handler for Claude Code.

One script, five modes, selected by the first argument:

  check           Run by hand after writing the configuration. Validates it and
                  exits 2 with a message if anything is wrong.
  stop           Stop event. Runs the definition-of-done commands and blocks the
                  stop (exit 2) when one fails. Also scans the working tree diff
                  for newly added suppression markers.
  suppressions    PreToolUse on Edit|Write. Blocks an edit that adds a suppression
                  marker to a file the rules cover.
  bash-guard      PreToolUse on Bash. Denies or asks for commands that match the
                  configured patterns anywhere in the command text.
  prompt-guard    UserPromptSubmit. Blocks a prompt that contains something that
                  looks like a credential.

Behavior contract (Claude Code hooks):
  exit 0   success. For PreToolUse a JSON object on stdout can ask for a prompt.
  exit 2   blocking error. The message on stderr is shown to the agent or user.
  other    non-blocking error: the action proceeds. This script never exits 1
           on purpose, because that would protect nothing.

Failure policy: every mode fails closed. An internal error or a broken
configuration blocks (exit 2) with a message that says what to fix. The one
exception is the stop mode when the event reports stop_hook_active, so that a
broken configuration cannot trap the agent in a loop.

Configuration file: harness-hooks.config.json next to this script (override with
the HARNESS_HOOKS_CONFIG environment variable). Schema:

  {
    "version": 1,
    "done": {
      "when": "changed" | "always",
      "commands": [{"name": str, "args": [str, ...], "timeout": seconds}]
    },
    "suppressions": {
      "rules": [{"globs": [str], "pattern": regex, "label": str}],
      "ignore_paths": [glob]
    },
    "commands": {
      "deny": [{"pattern": regex, "reason": str}],
      "ask":  [{"pattern": regex, "reason": str}]
    },
    "prompt_secrets": [{"pattern": regex, "label": str}]
  }

Only the Python standard library is used.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any

MAX_OUTPUT_LINES = 30
MAX_OUTPUT_CHARS = 3000


class ConfigError(Exception):
    """The configuration file is missing or invalid."""


def block(message: str) -> None:
    """Block with exit status 2. The message goes to stderr."""
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(2)


def allow() -> None:
    sys.exit(0)


def ask(reason: str) -> None:
    """Ask the user for confirmation through a PreToolUse JSON decision."""
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(payload))
    sys.exit(0)


def load_config() -> dict[str, Any]:
    path = os.environ.get("HARNESS_HOOKS_CONFIG") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "harness-hooks.config.json"
    )
    try:
        with open(path, encoding="utf-8") as handle:
            config = json.load(handle)
    except FileNotFoundError as error:
        raise ConfigError(f"configuration file not found: {path}") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigError(f"configuration file is not valid JSON: {path} ({error})") from error
    if not isinstance(config, dict):
        raise ConfigError(f"configuration root must be an object: {path}")
    return config


def compile_rules(items: Any, key: str, where: str) -> list[tuple[re.Pattern[str], dict[str, Any]]]:
    compiled = []
    for item in items or []:
        try:
            compiled.append((re.compile(item[key], re.IGNORECASE), item))
        except (re.error, KeyError, TypeError) as error:
            raise ConfigError(f"invalid rule in {where}: {item!r} ({error})") from error
    return compiled


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def path_matches(path: str, globs: list[str]) -> bool:
    normalized = normalize_path(path)
    return any(fnmatch.fnmatch(normalized, normalize_path(glob)) for glob in globs)


def project_dir(event: dict[str, Any]) -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


# --------------------------------------------------------------------------- #
# suppressions (PreToolUse on Edit|Write)
# --------------------------------------------------------------------------- #

def count(pattern: re.Pattern[str], text: str) -> int:
    return len(pattern.findall(text))


def mode_suppressions(event: dict[str, Any], config: dict[str, Any]) -> None:
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        allow()
    section = config.get("suppressions") or {}
    if path_matches(file_path, section.get("ignore_paths", [])):
        allow()

    if event.get("tool_name") == "Write":
        new_text = tool_input.get("content", "") or ""
        old_text = read_text(file_path) if os.path.exists(file_path) else ""
    else:
        new_text = tool_input.get("new_string", "") or ""
        old_text = tool_input.get("old_string", "") or ""

    found = []
    for pattern, rule in compile_rules(section.get("rules"), "pattern", "suppressions.rules"):
        if not path_matches(file_path, rule.get("globs", ["*"])):
            continue
        if count(pattern, new_text) > count(pattern, old_text):
            found.append(rule.get("label", rule["pattern"]))
    if found:
        block(
            "Blocked: this edit adds a diagnostic suppression ("
            + ", ".join(sorted(set(found)))
            + f") to {normalize_path(file_path)}. Fix the code instead. If the rule really does not "
            "fit this project, stop and explain why to the user."
        )
    allow()


# --------------------------------------------------------------------------- #
# bash-guard (PreToolUse on Bash)
# --------------------------------------------------------------------------- #

def mode_bash_guard(event: dict[str, Any], config: dict[str, Any]) -> None:
    command = (event.get("tool_input") or {}).get("command", "") or ""
    section = config.get("commands") or {}
    for pattern, rule in compile_rules(section.get("deny"), "pattern", "commands.deny"):
        if pattern.search(command):
            block("Blocked command: " + rule.get("reason", "this command is not allowed in this project."))
    for pattern, rule in compile_rules(section.get("ask"), "pattern", "commands.ask"):
        if pattern.search(command):
            ask(rule.get("reason", "This command needs confirmation."))
    allow()


# --------------------------------------------------------------------------- #
# prompt-guard (UserPromptSubmit)
# --------------------------------------------------------------------------- #

def mode_prompt_guard(event: dict[str, Any], config: dict[str, Any]) -> None:
    prompt = event.get("prompt", "") or ""
    labels = []
    for pattern, rule in compile_rules(config.get("prompt_secrets"), "pattern", "prompt_secrets"):
        if pattern.search(prompt):
            labels.append(rule.get("label", "credential-like text"))
    if labels:
        # Never echo the matched text: it is the thing we do not want to repeat.
        block(
            "Prompt blocked: it looks like it contains a credential ("
            + ", ".join(sorted(set(labels)))
            + "). Remove the secret and describe it instead, for example by naming the setting "
            "that holds it. Rotate the secret if it is real."
        )
    allow()


# --------------------------------------------------------------------------- #
# stop (Stop)
# --------------------------------------------------------------------------- #

def git(args: list[str], cwd: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, errors="replace", timeout=60
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def working_tree_changed(cwd: str) -> bool | None:
    """True or False when git can tell, None when it cannot."""
    result = git(["status", "--porcelain"], cwd)
    if result is None or result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def added_suppressions(cwd: str, config: dict[str, Any]) -> list[str]:
    """Net suppression markers added in the working tree, per file."""
    section = config.get("suppressions") or {}
    rules = compile_rules(section.get("rules"), "pattern", "suppressions.rules")
    if not rules:
        return []
    ignore = section.get("ignore_paths", [])
    findings: list[str] = []

    diff = git(["diff", "-U0", "--no-color", "HEAD"], cwd)
    if diff is None or diff.returncode != 0:
        diff = git(["diff", "-U0", "--no-color"], cwd)
    per_file: dict[str, dict[str, int]] = {}
    current = None
    if diff is not None and diff.returncode == 0:
        for line in diff.stdout.splitlines():
            if line.startswith("+++ b/"):
                current = line[6:]
                continue
            if line.startswith("+++") or line.startswith("---") or current is None:
                continue
            if line and line[0] in "+-":
                sign = 1 if line[0] == "+" else -1
                for pattern, rule in rules:
                    if path_matches(current, rule.get("globs", ["*"])) and pattern.search(line[1:]):
                        label = rule.get("label", rule["pattern"])
                        per_file.setdefault(current, {})
                        per_file[current][label] = per_file[current].get(label, 0) + sign

    untracked = git(["ls-files", "--others", "--exclude-standard"], cwd)
    if untracked is not None and untracked.returncode == 0:
        for name in untracked.stdout.splitlines():
            text = read_text(os.path.join(cwd, name))
            for pattern, rule in rules:
                if path_matches(name, rule.get("globs", ["*"])):
                    n = count(pattern, text)
                    if n:
                        label = rule.get("label", rule["pattern"])
                        per_file.setdefault(name, {})
                        per_file[name][label] = per_file[name].get(label, 0) + n

    for name, labels in sorted(per_file.items()):
        if path_matches(name, ignore):
            continue
        added = [label for label, net in labels.items() if net > 0]
        if added:
            findings.append(f"{normalize_path(name)}: {', '.join(sorted(added))}")
    return findings


def tail(text: str) -> str:
    lines = text.strip().splitlines()[-MAX_OUTPUT_LINES:]
    joined = "\n".join(lines)
    return joined[-MAX_OUTPUT_CHARS:]


def mode_stop(event: dict[str, Any], config: dict[str, Any]) -> None:
    cwd = project_dir(event)
    done = config.get("done") or {}
    commands = done.get("commands") or []

    if done.get("when", "changed") == "changed":
        changed = working_tree_changed(cwd)
        if changed is False:
            allow()  # nothing to verify: no change in the working tree

    problems: list[str] = []

    for item in commands:
        name = item.get("name", " ".join(item.get("args", [])))
        args = item.get("args")
        if not isinstance(args, list) or not args or not all(isinstance(a, str) for a in args):
            raise ConfigError(f"done.commands entry '{name}' needs a non-empty args list")
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=int(item.get("timeout", 600)),
            )
        except subprocess.TimeoutExpired:
            problems.append(f"[{name}] timed out after {item.get('timeout', 600)} seconds")
            continue
        except OSError as error:
            problems.append(f"[{name}] could not run: {error}")
            continue
        if result.returncode != 0:
            output = tail((result.stdout or "") + "\n" + (result.stderr or ""))
            problems.append(f"[{name}] exited with status {result.returncode}\n{output}")

    suppressions = added_suppressions(cwd, config)
    if suppressions:
        problems.append(
            "[suppressions] new diagnostic suppressions were added. Fix the code instead of "
            "silencing the check:\n  " + "\n  ".join(suppressions)
        )

    if problems:
        block(
            "The definition of done is not met. Fix this before finishing:\n\n"
            + "\n\n".join(problems)
        )
    allow()


# --------------------------------------------------------------------------- #
# check (run by hand, not by Claude Code)
# --------------------------------------------------------------------------- #

def mode_check(event: dict[str, Any], config: dict[str, Any]) -> None:
    """Validate the configuration: every regex compiles and every command is well formed."""
    suppressions = config.get("suppressions") or {}
    commands = config.get("commands") or {}
    counts = {
        "suppression rules": len(compile_rules(suppressions.get("rules"), "pattern", "suppressions.rules")),
        "denied command patterns": len(compile_rules(commands.get("deny"), "pattern", "commands.deny")),
        "ask command patterns": len(compile_rules(commands.get("ask"), "pattern", "commands.ask")),
        "prompt secret patterns": len(compile_rules(config.get("prompt_secrets"), "pattern", "prompt_secrets")),
    }
    done = config.get("done") or {}
    warnings: list[str] = []
    total_timeout = 0
    for item in done.get("commands") or []:
        args = item.get("args")
        if not isinstance(args, list) or not args or not all(isinstance(a, str) for a in args):
            raise ConfigError(f"done.commands entry '{item.get('name', '?')}' needs a non-empty args list of strings")
        timeout = item.get("timeout", 600)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigError(f"done.commands entry '{item.get('name', '?')}' has a timeout that is not a positive number of seconds")
        total_timeout += timeout
        program = args[0]
        found = os.path.exists(program) if os.sep in program or "/" in program else shutil.which(program)
        if not found:
            warnings.append(
                f"warning: the program '{program}' of done.commands entry '{item.get('name', '?')}' was not found; "
                "the stop guard will block with 'could not run' until it is available"
            )
    counts["definition-of-done commands"] = len(done.get("commands") or [])
    if done.get("when", "changed") not in ("changed", "always"):
        raise ConfigError("done.when must be 'changed' or 'always'")
    if total_timeout:
        warnings.append(
            f"note: the done commands may take up to {total_timeout:g} seconds in total; "
            "the Stop hook 'timeout' in the settings must be larger than that"
        )
    sys.stdout.write("configuration ok: " + ", ".join(f"{n} {k}" for k, n in counts.items()) + "\n")
    for line in warnings:
        sys.stdout.write(line + "\n")
    sys.exit(0)


MODES = {
    "check": mode_check,
    "stop": mode_stop,
    "suppressions": mode_suppressions,
    "bash-guard": mode_bash_guard,
    "prompt-guard": mode_prompt_guard,
}


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    handler = MODES.get(mode)
    event: dict[str, Any] = {}
    try:
        if handler is None:
            raise ConfigError(f"unknown mode '{mode}'. Use one of: {', '.join(MODES)}")
        raw = "" if mode == "check" else sys.stdin.read()  # check is run by hand: never wait on stdin
        event = json.loads(raw) if raw.strip() else {}
        if not isinstance(event, dict):
            raise ConfigError("the hook input is not a JSON object")
        config = load_config()
        handler(event, config)
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001 - fail closed on anything unexpected
        if mode == "stop" and event.get("stop_hook_active"):
            sys.stderr.write(f"harness hook error ignored to avoid a stop loop: {error}\n")
            sys.exit(0)
        block(
            f"The harness hook '{mode}' failed and is blocking on purpose so the problem is not "
            f"silent: {error}. Ask the user to fix the hook or its configuration."
        )


if __name__ == "__main__":
    main()
