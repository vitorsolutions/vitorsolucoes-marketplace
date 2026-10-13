"""Tests for scripts/harness_hooks.py.

Run from the skill folder:  python -m unittest discover -s tests -v

Each test starts the script as a separate process, feeds it a hook event on
stdin, and checks the exit status and the output, which is the contract Claude
Code relies on.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "harness_hooks.py")

CONFIG = {
    "version": 1,
    "done": {
        "when": "always",
        "commands": [{"name": "ok", "args": [sys.executable, "-c", "print('fine')"], "timeout": 30}],
    },
    "suppressions": {
        "rules": [
            {"globs": ["*.cs"], "pattern": r"#pragma\s+warning\s+disable", "label": "pragma warning disable"},
            {"globs": ["*.py"], "pattern": r"#\s*noqa\b", "label": "noqa"},
        ],
        "ignore_paths": ["*/Migrations/*"],
    },
    "commands": {
        "deny": [{"pattern": r"git\b.*\bpush\b.*(--force(?![-\w])|\s-f\b)", "reason": "force push is not allowed."}],
        "ask": [
            {"pattern": r"dotnet\s+ef\s+database\s+update", "reason": "this changes a database."},
            {"pattern": r"git\b.*\bpush\b.*--force-with-lease", "reason": "this rewrites remote history."},
        ],
    },
    "prompt_secrets": [
        {"pattern": r"(password|pwd)\s*=\s*[^;\s'\"]{4,}", "label": "password in a connection string"},
        {"pattern": r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "label": "private key"},
    ],
}


def run(mode, event, config=None, cwd=None, env_extra=None, raw_input=None):
    directory = tempfile.mkdtemp()
    try:
        config_path = os.path.join(directory, "config.json")
        if config is not False:
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(CONFIG if config is None else config, handle)
        env = dict(os.environ)
        env["HARNESS_HOOKS_CONFIG"] = config_path
        env.pop("CLAUDE_PROJECT_DIR", None)
        env.update(env_extra or {})
        return subprocess.run(
            [sys.executable, SCRIPT, mode],
            input=raw_input if raw_input is not None else json.dumps(event),
            capture_output=True,
            text=True,
            cwd=cwd or directory,
            env=env,
            timeout=120,
        )
    finally:
        shutil.rmtree(directory, ignore_errors=True)


class SuppressionsTests(unittest.TestCase):
    def edit(self, path, old, new):
        return {"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": old, "new_string": new}}

    def test_blocks_added_marker(self):
        result = run("suppressions", self.edit("/r/A.cs", "int a;", "#pragma warning disable CA2100\nint a;"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("suppression", result.stderr)

    def test_allows_edit_that_keeps_existing_marker(self):
        old = "#pragma warning disable CA2100\nint a;"
        new = "#pragma warning disable CA2100\nint b;"
        self.assertEqual(run("suppressions", self.edit("/r/A.cs", old, new)).returncode, 0)

    def test_allows_removing_marker(self):
        result = run("suppressions", self.edit("/r/A.cs", "#pragma warning disable CA2100\nint a;", "int a;"))
        self.assertEqual(result.returncode, 0)

    def test_marker_only_applies_to_matching_files(self):
        self.assertEqual(run("suppressions", self.edit("/r/readme.md", "x", "#pragma warning disable")).returncode, 0)

    def test_python_marker_blocked(self):
        result = run("suppressions", self.edit("C:\\r\\a.py", "x = 1", "x = 1  # noqa: S608"))
        self.assertEqual(result.returncode, 2)

    def test_ignored_path_allowed(self):
        result = run("suppressions", self.edit("/r/Migrations/M1.cs", "a", "#pragma warning disable 612"))
        self.assertEqual(result.returncode, 0)

    def test_write_new_file_with_marker_blocked(self):
        event = {"tool_name": "Write", "tool_input": {"file_path": "/nonexistent/Z.cs", "content": "#pragma warning disable X"}}
        self.assertEqual(run("suppressions", event).returncode, 2)

    def test_write_over_existing_file_compares_with_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "A.cs")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("#pragma warning disable X\nint a;")
            same = {"tool_name": "Write", "tool_input": {"file_path": path, "content": "#pragma warning disable X\nint b;"}}
            more = {"tool_name": "Write", "tool_input": {"file_path": path, "content": "#pragma warning disable X\n#pragma warning disable Y\n"}}
            self.assertEqual(run("suppressions", same).returncode, 0)
            self.assertEqual(run("suppressions", more).returncode, 2)


class BashGuardTests(unittest.TestCase):
    def cmd(self, text):
        return {"tool_name": "Bash", "tool_input": {"command": text}}

    def test_denies_force_push(self):
        result = run("bash-guard", self.cmd("git push origin main --force"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("force push", result.stderr)

    def test_denies_force_push_in_other_forms(self):
        for text in ["git -C . push -f origin x", "sh -c 'git push --force'", "/usr/bin/git push --force"]:
            self.assertEqual(run("bash-guard", self.cmd(text)).returncode, 2, text)

    def test_ask_returns_json_decision(self):
        result = run("bash-guard", self.cmd("cd src && dotnet ef database update"))
        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "ask")

    def test_force_with_lease_asks_instead_of_denying(self):
        result = run("bash-guard", self.cmd("git push --force-with-lease origin x"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_plain_force_after_lease_is_still_denied(self):
        self.assertEqual(run("bash-guard", self.cmd("git push --force-with-lease --force origin x")).returncode, 2)

    def test_allows_harmless_command(self):
        result = run("bash-guard", self.cmd("dotnet build"))
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_does_not_block_normal_push(self):
        self.assertEqual(run("bash-guard", self.cmd("git push origin feature")).returncode, 0)


class PromptGuardTests(unittest.TestCase):
    def test_blocks_password_without_echoing_it(self):
        result = run("prompt-guard", {"prompt": "use Server=x;Password=Sup3rSecret!;Db=y"})
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Sup3rSecret", result.stderr)

    def test_blocks_private_key(self):
        self.assertEqual(run("prompt-guard", {"prompt": "-----BEGIN RSA PRIVATE KEY-----\nabc"}).returncode, 2)

    def test_allows_normal_prompt(self):
        self.assertEqual(run("prompt-guard", {"prompt": "add a password reset endpoint"}).returncode, 0)


class StopTests(unittest.TestCase):
    def repo(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
            subprocess.run(["git", *args], cwd=folder, check=True, capture_output=True)
        with open(os.path.join(folder, "A.cs"), "w", encoding="utf-8") as handle:
            handle.write("int a;\n")
        subprocess.run(["git", "add", "."], cwd=folder, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=folder, check=True, capture_output=True)
        return folder

    def config(self, **done):
        config = json.loads(json.dumps(CONFIG))
        config["done"].update(done)
        return config

    def test_passes_when_commands_succeed(self):
        folder = self.repo()
        result = run("stop", {"cwd": folder}, config=self.config(), cwd=folder)
        self.assertEqual(result.returncode, 0)

    def test_blocks_when_command_fails_and_shows_output(self):
        folder = self.repo()
        failing = [{"name": "tests", "args": [sys.executable, "-c", "import sys; print('boom detail'); sys.exit(3)"]}]
        result = run("stop", {"cwd": folder}, config=self.config(commands=failing), cwd=folder)
        self.assertEqual(result.returncode, 2)
        self.assertIn("tests", result.stderr)
        self.assertIn("status 3", result.stderr)
        self.assertIn("boom detail", result.stderr)

    def test_skips_when_nothing_changed(self):
        folder = self.repo()
        failing = [{"name": "tests", "args": [sys.executable, "-c", "import sys; sys.exit(1)"]}]
        result = run("stop", {"cwd": folder}, config=self.config(when="changed", commands=failing), cwd=folder)
        self.assertEqual(result.returncode, 0)

    def test_runs_when_changed(self):
        folder = self.repo()
        with open(os.path.join(folder, "A.cs"), "a", encoding="utf-8") as handle:
            handle.write("int b;\n")
        failing = [{"name": "tests", "args": [sys.executable, "-c", "import sys; sys.exit(1)"]}]
        result = run("stop", {"cwd": folder}, config=self.config(when="changed", commands=failing), cwd=folder)
        self.assertEqual(result.returncode, 2)

    def test_detects_added_suppression_in_tracked_file(self):
        folder = self.repo()
        with open(os.path.join(folder, "A.cs"), "a", encoding="utf-8") as handle:
            handle.write("#pragma warning disable CA2100\n")
        result = run("stop", {"cwd": folder}, config=self.config(), cwd=folder)
        self.assertEqual(result.returncode, 2)
        self.assertIn("A.cs", result.stderr)

    def test_detects_suppression_in_untracked_file(self):
        folder = self.repo()
        with open(os.path.join(folder, "B.cs"), "w", encoding="utf-8") as handle:
            handle.write("#pragma warning disable CA2100\n")
        result = run("stop", {"cwd": folder}, config=self.config(), cwd=folder)
        self.assertEqual(result.returncode, 2)
        self.assertIn("B.cs", result.stderr)

    def test_ignores_suppression_in_ignored_path(self):
        folder = self.repo()
        os.makedirs(os.path.join(folder, "x", "Migrations"))
        with open(os.path.join(folder, "x", "Migrations", "M.cs"), "w", encoding="utf-8") as handle:
            handle.write("#pragma warning disable 612\n")
        result = run("stop", {"cwd": folder}, config=self.config(), cwd=folder)
        self.assertEqual(result.returncode, 0)

    def test_removed_suppression_is_not_a_finding(self):
        folder = self.repo()
        path = os.path.join(folder, "A.cs")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("#pragma warning disable X\n")
        subprocess.run(["git", "commit", "-qam", "marker"], cwd=folder, check=True, capture_output=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("int a;\n")
        self.assertEqual(run("stop", {"cwd": folder}, config=self.config(), cwd=folder).returncode, 0)

    def test_timeout_is_reported(self):
        folder = self.repo()
        slow = [{"name": "slow", "args": [sys.executable, "-c", "import time; time.sleep(20)"], "timeout": 1}]
        result = run("stop", {"cwd": folder}, config=self.config(commands=slow), cwd=folder)
        self.assertEqual(result.returncode, 2)
        self.assertIn("timed out", result.stderr)

    def test_missing_executable_is_reported(self):
        folder = self.repo()
        missing = [{"name": "nope", "args": ["definitely-not-a-real-program-xyz"]}]
        result = run("stop", {"cwd": folder}, config=self.config(commands=missing), cwd=folder)
        self.assertEqual(result.returncode, 2)
        self.assertIn("could not run", result.stderr)


class CheckModeTests(unittest.TestCase):
    def test_valid_configuration_reports_counts(self):
        result = run("check", None, raw_input="")
        self.assertEqual(result.returncode, 0)
        self.assertIn("configuration ok", result.stdout)
        self.assertIn("2 suppression rules", result.stdout)

    def test_does_not_wait_on_stdin(self):
        # raw_input="" would hang a mode that reads until EOF only if stdin stayed open; the helper closes it,
        # so this checks that check mode ignores the content entirely.
        result = run("check", None, raw_input="this is not json")
        self.assertEqual(result.returncode, 0)

    def test_bad_regex_is_reported(self):
        bad = {"commands": {"deny": [{"pattern": "(", "reason": "x"}]}}
        result = run("check", None, config=bad, raw_input="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid rule", result.stderr)

    def test_bad_command_entry_is_reported(self):
        bad = {"done": {"commands": [{"name": "x", "args": "dotnet build"}]}}
        result = run("check", None, config=bad, raw_input="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("args list", result.stderr)

    def test_missing_program_is_a_warning_not_an_error(self):
        config = {"done": {"commands": [{"name": "x", "args": ["definitely-not-a-real-program-xyz"], "timeout": 5}]}}
        result = run("check", None, config=config, raw_input="")
        self.assertEqual(result.returncode, 0)
        self.assertIn("warning", result.stdout)
        self.assertIn("definitely-not-a-real-program-xyz", result.stdout)

    def test_bad_timeout_type_is_reported(self):
        for bad in ["600", 0, -5, True, None]:
            config = {"done": {"commands": [{"name": "x", "args": [sys.executable], "timeout": bad}]}}
            result = run("check", None, config=config, raw_input="")
            self.assertEqual(result.returncode, 2, bad)
            self.assertIn("timeout", result.stderr)

    def test_reports_total_timeout_for_the_stop_hook(self):
        commands = [
            {"name": "a", "args": [sys.executable], "timeout": 100},
            {"name": "b", "args": [sys.executable], "timeout": 250},
        ]
        result = run("check", None, config={"done": {"commands": commands}}, raw_input="")
        self.assertEqual(result.returncode, 0)
        self.assertIn("350 seconds", result.stdout)

    def test_bad_when_value_is_reported(self):
        result = run("check", None, config={"done": {"when": "sometimes"}}, raw_input="")
        self.assertEqual(result.returncode, 2)

    def test_invalid_json_is_reported(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "c.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('{"x": "\\s"}')  # a lone backslash escape, the mistake seen in practice
        result = run("check", None, config=False, env_extra={"HARNESS_HOOKS_CONFIG": path}, raw_input="")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not valid JSON", result.stderr)


class FailClosedTests(unittest.TestCase):
    def test_missing_config_blocks_with_a_message(self):
        result = run("bash-guard", {"tool_input": {"command": "ls"}}, config=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not found", result.stderr)

    def test_invalid_json_config_blocks(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "c.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{ not json")
        result = run("bash-guard", {"tool_input": {"command": "ls"}}, env_extra={"HARNESS_HOOKS_CONFIG": path}, config=False)
        # config=False means the helper wrote nothing; env override points at the invalid file
        self.assertEqual(result.returncode, 2)

    def test_bad_regex_blocks(self):
        bad = {"commands": {"deny": [{"pattern": "(", "reason": "x"}]}}
        result = run("bash-guard", {"tool_input": {"command": "ls"}}, config=bad)
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid rule", result.stderr)

    def test_unknown_mode_blocks(self):
        self.assertEqual(run("nonsense", {}).returncode, 2)

    def test_garbage_stdin_blocks(self):
        self.assertEqual(run("bash-guard", None, raw_input="not json").returncode, 2)

    def test_stop_with_broken_config_and_active_flag_does_not_trap(self):
        result = run("stop", {"stop_hook_active": True}, config=False)
        self.assertEqual(result.returncode, 0)

    def test_stop_with_broken_config_blocks_the_first_time(self):
        self.assertEqual(run("stop", {"stop_hook_active": False}, config=False).returncode, 2)

    def test_never_exits_with_status_one(self):
        samples = [
            ("bash-guard", None, {"raw_input": "not json"}),
            ("stop", {}, {"config": False}),
            ("nonsense", {}, {}),
        ]
        for mode, event, kwargs in samples:
            self.assertNotEqual(run(mode, event, **kwargs).returncode, 1, mode)


if __name__ == "__main__":
    unittest.main()
