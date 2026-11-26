"""Tests for scripts/generate_image.py.

Run from the skill folder:  python -m unittest discover -s tests -v

A fake `codex` is placed first on PATH (a .cmd wrapper on Windows, like the npm
install), so no test needs the real CLI, a sign-in, or plan usage. Each test runs
the script as a separate process and checks the exit status, the JSON on stdout,
and what the fake received.
"""

import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import zlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "generate_image.py"
SESSION = "00000000-1111-2222-3333-444444444444"
HAS_PILLOW = importlib.util.find_spec("PIL") is not None

FAKE_CODEX = r'''
import json, os, sys, time
from pathlib import Path

root = Path(__file__).resolve().parent
scenario = json.loads((root / "scenario.json").read_text("utf-8"))
args = sys.argv[1:]

if args[:2] == ["login", "status"]:
    sys.stderr.write(scenario["login"] + "\n")
    sys.exit(scenario["login_exit"])
if args[:2] == ["features", "list"]:
    if scenario["feature"] is not None:
        print("image_generation    stable    " + scenario["feature"])
    sys.exit(0)

record = {
    "args": args,
    "stdin": sys.stdin.buffer.read().decode("utf-8"),
    "api_keys": sorted(k for k in os.environ if k.upper() in ("OPENAI_API_KEY", "CODEX_API_KEY")),
    "cwd_files": sorted(p.name for p in Path.cwd().iterdir()),
}
(root / "record.json").write_text(json.dumps(record), "utf-8")

session = scenario["session"]
print(json.dumps({"type": "thread.started", "thread_id": session}), flush=True)
folder = Path(os.environ["CODEX_HOME"]) / "generated_images" / session
for index, hex_content in enumerate(scenario["files"]):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ("exec-%d.png" % index)).write_bytes(bytes.fromhex(hex_content))
time.sleep(scenario["sleep"])
for text in scenario["messages"]:
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": text}}))
if scenario["failure"]:
    print(json.dumps({"type": "turn.failed", "error": {"message": scenario["failure"]}}))
sys.stderr.write(scenario["stderr"])
sys.exit(scenario["exit"])
'''


def make_png(width=8, height=4, color_type=2):
    channels = {2: 3, 6: 4}[color_type]

    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data))

    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    pixels = (b"\x00" + b"\x80" * width * channels) * height
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")


class GenerateImageTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="codex-image-test-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bin = self.root / "bin"
        self.home = self.root / "codex-home"
        self.output = self.root / "output"
        for directory in (self.bin, self.home, self.output):
            directory.mkdir()
        (self.bin / "fake_codex.py").write_text(FAKE_CODEX, "utf-8")
        if os.name == "nt":
            wrapper = self.bin / "codex.cmd"
            wrapper.write_text(f'@"{sys.executable}" "%~dp0fake_codex.py" %*\n', "utf-8")
        else:
            wrapper = self.bin / "codex"
            wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$(dirname "$0")/fake_codex.py" "$@"\n', "utf-8")
            wrapper.chmod(0o755)
        self.scenario = {
            "login": "Logged in using ChatGPT",
            "login_exit": 0,
            "feature": "true",
            "session": SESSION,
            "files": [make_png().hex()],
            "messages": ["Done."],
            "failure": None,
            "stderr": "",
            "sleep": 0,
            "exit": 0,
        }

    def run_script(self, *args, path=None, python_flags=(), extra_env=None):
        (self.bin / "scenario.json").write_text(json.dumps(self.scenario), "utf-8")
        env = dict(os.environ)
        env["PATH"] = str(self.bin) + os.pathsep + env.get("PATH", "") if path is None else path
        env["CODEX_HOME"] = str(self.home)
        env.update(extra_env or {})
        process = subprocess.run(
            [sys.executable, *python_flags, str(SCRIPT), *args],
            capture_output=True,
            env=env,
            cwd=self.root,
            timeout=120,
        )
        stdout = process.stdout.decode("utf-8")
        result = json.loads(stdout) if stdout.strip() else None
        return process.returncode, result

    def generate(self, *extra, name="picture.png", **kwargs):
        return self.run_script("--prompt", "a red circle", "--out", str(self.output / name), *extra, **kwargs)

    def record(self):
        return json.loads((self.bin / "record.json").read_text("utf-8"))

    # --- preconditions --------------------------------------------------------

    def test_check_passes_without_generating(self):
        code, result = self.run_script("--check")
        self.assertEqual((code, result["status"]), (0, "ready"))
        self.assertFalse((self.bin / "record.json").exists())

    def test_missing_cli(self):
        code, result = self.run_script("--check", path=str(self.output))
        self.assertEqual((code, result["status"]), (3, "codex_not_found"))

    def test_codex_in_current_directory_is_ignored(self):
        for name in ("codex", "codex.cmd"):
            shutil.copy(self.bin / ("codex.cmd" if os.name == "nt" else "codex"), self.root / name)
        code, result = self.run_script("--check", path=os.pathsep.join([".", ""]))
        self.assertEqual((code, result["status"]), (3, "codex_not_found"))

    def test_api_key_login_is_refused(self):
        self.scenario["login"] = "Logged in using an API key - sk-proj-***"
        code, result = self.generate()
        self.assertEqual((code, result["status"]), (3, "api_key_login"))
        self.assertFalse((self.bin / "record.json").exists())

    def test_not_logged_in(self):
        self.scenario.update(login="Not logged in", login_exit=1)
        code, result = self.generate()
        self.assertEqual((code, result["status"]), (3, "not_logged_in"))

    def test_disabled_feature(self):
        self.scenario["feature"] = "false"
        code, result = self.generate()
        self.assertEqual((code, result["status"]), (3, "feature_disabled"))
        self.assertFalse((self.bin / "record.json").exists())

    def test_unknown_feature_state_only_warns(self):
        self.scenario["feature"] = None
        code, result = self.generate()
        self.assertEqual(code, 0)
        self.assertTrue(any("image_generation" in warning for warning in result["warnings"]))

    # --- the request ----------------------------------------------------------

    def test_success_and_isolation(self):
        code, result = self.generate(extra_env={"OPENAI_API_KEY": "placeholder", "CODEX_API_KEY": "placeholder"})
        self.assertEqual((code, result["status"], result["delivered"]), (0, "ok", 1))
        image = result["images"][0]
        self.assertEqual((image["width"], image["height"], image["format"]), (8, 4, "png"))
        self.assertFalse(image["alpha_channel"])
        self.assertEqual(Path(image["path"]).read_bytes(), make_png())

        record = self.record()
        self.assertEqual(record["args"], ["exec", "--json", "--skip-git-repo-check", "--sandbox", "read-only"])
        self.assertEqual(record["api_keys"], [])
        self.assertEqual(record["cwd_files"], [])
        self.assertIn("a red circle", record["stdin"])

    def test_shell_metacharacters_stay_in_stdin(self):
        prompt = 'a sign reading "A & B" | %PATH% $(whoami) ção'
        prompt_file = self.root / "prompt.txt"
        prompt_file.write_text(prompt, "utf-8-sig")
        code, _ = self.run_script("--prompt-file", str(prompt_file), "--out", str(self.output / "sign.png"))
        self.assertEqual(code, 0)
        record = self.record()
        self.assertIn(prompt, record["stdin"])
        self.assertNotIn("whoami", " ".join(record["args"]))

    def test_inputs_are_attached_under_fixed_names(self):
        edit = self.root / "my photo & notes.png"
        reference = self.root / "style.png"
        edit.write_bytes(make_png())
        reference.write_bytes(make_png(4, 4))
        code, _ = self.generate("--edit", str(edit), "--reference", str(reference))
        self.assertEqual(code, 0)
        record = self.record()
        self.assertEqual(record["args"][1:5], ["--image", "input-1.png", "--image", "input-2.png"])
        self.assertEqual(record["cwd_files"], ["input-1.png", "input-2.png"])
        self.assertIn("Image 1: edit target", record["stdin"])
        self.assertIn("Image 2: reference", record["stdin"])
        self.assertEqual(edit.read_bytes(), make_png())

    def test_invalid_arguments(self):
        text_file = self.root / "notes.png"
        text_file.write_text("not an image", "utf-8")
        for extra in (
            ("--size", "big"),
            ("--size", "0x10"),
            ("--n", "99"),
            ("--reference", str(self.root / "absent.png")),
            ("--reference", str(text_file)),
        ):
            with self.subTest(extra=extra):
                code, result = self.generate(*extra)
                self.assertEqual((code, result["status"]), (2, "invalid_arguments"))
        self.assertFalse((self.bin / "record.json").exists())

    # --- delivery -------------------------------------------------------------

    def test_existing_files_are_never_overwritten(self):
        existing = self.output / "picture.png"
        existing.write_bytes(b"original")
        code, result = self.generate()
        self.assertEqual(code, 0)
        self.assertEqual(existing.read_bytes(), b"original")
        self.assertEqual(Path(result["images"][0]["path"]).name, "picture-v2.png")

    def test_unwritable_destination_points_to_the_generated_file(self):
        (self.output / "blocker").write_bytes(b"a file where a folder is needed")
        code, result = self.generate(name="blocker/picture.png")
        self.assertEqual((code, result["status"]), (4, "io_error"))
        self.assertTrue(any(SESSION in warning for warning in result["warnings"]))

    def test_variations_are_numbered(self):
        self.scenario["files"] = [make_png().hex(), make_png(4, 4).hex()]
        code, result = self.generate("--n", "2")
        self.assertEqual(code, 0)
        self.assertEqual([Path(i["path"]).name for i in result["images"]], ["picture-1.png", "picture-2.png"])

    def test_extension_follows_the_real_format(self):
        code, result = self.generate(name="picture.jpg")
        self.assertEqual(code, 0)
        self.assertEqual(Path(result["images"][0]["path"]).name, "picture.png")

    def test_dotted_name_without_image_extension_is_kept(self):
        code, result = self.generate(name="banner.v1")
        self.assertEqual(code, 0)
        self.assertEqual(Path(result["images"][0]["path"]).name, "banner.v1.png")

    def test_alpha_channel_is_reported(self):
        self.scenario["files"] = [make_png(color_type=6).hex()]
        _, result = self.generate()
        self.assertTrue(result["images"][0]["alpha_channel"])

    def test_images_from_other_sessions_are_ignored(self):
        other = self.home / "generated_images" / "99999999-aaaa-bbbb-cccc-dddddddddddd"
        other.mkdir(parents=True)
        (other / "old.png").write_bytes(make_png())
        self.scenario["files"] = []
        code, result = self.generate()
        self.assertEqual((code, result["status"]), (4, "no_image"))
        self.assertEqual(list(self.output.iterdir()), [])

    def test_non_image_output_is_ignored(self):
        self.scenario["files"] = [b"plain text".hex()]
        code, result = self.generate()
        self.assertEqual((code, result["status"]), (4, "no_image"))

    def test_session_id_cannot_leave_the_images_folder(self):
        self.scenario["session"] = "../../outside"
        code, result = self.generate()
        self.assertEqual((code, result["delivered"]), (4, 0))

    def test_partial_result(self):
        code, result = self.generate("--n", "3")
        self.assertEqual((code, result["status"], result["delivered"]), (5, "partial", 1))

    def test_unavailable_tool(self):
        self.scenario.update(files=[], messages=["NATIVE_IMAGE_TOOL_UNAVAILABLE: not offered"])
        code, result = self.generate()
        self.assertEqual((code, result["status"]), (4, "tool_unavailable"))

    def test_failure_is_reported_with_secrets_redacted(self):
        token = "Bearer abcdefghijklmnop"
        self.scenario.update(files=[], failure="usage limit reached", stderr=f"header: {token}\n", exit=1)
        code, result = self.generate()
        self.assertEqual((code, result["status"]), (4, "no_image"))
        self.assertEqual(result["errors"], ["usage limit reached"])
        self.assertNotIn(token, result["stderr_tail"])

    def test_timeout_stops_the_process_tree(self):
        self.scenario.update(files=[], sleep=60)
        started = time.monotonic()
        code, result = self.generate("--timeout", "3")
        self.assertEqual((code, result["status"]), (4, "timeout"))
        self.assertLess(time.monotonic() - started, 30)

    def test_images_finished_before_a_timeout_are_kept(self):
        self.scenario["sleep"] = 60
        code, result = self.generate("--timeout", "3")
        self.assertEqual((code, result["delivered"]), (0, 1))
        self.assertTrue(any("did not finish" in warning for warning in result["warnings"]))

    # --- resize ---------------------------------------------------------------

    @unittest.skipUnless(HAS_PILLOW, "Pillow is not installed")
    def test_resize_covers_and_crops(self):
        code, result = self.generate("--size", "4x4")
        self.assertEqual(code, 0)
        image = result["images"][0]
        self.assertEqual((image["width"], image["height"]), (4, 4))
        self.assertTrue(any("crop" in warning for warning in result["warnings"]))
        self.assertIn("4x4", self.record()["stdin"])

    def test_resize_without_pillow_delivers_original(self):
        # -S skips site-packages, which hides Pillow from the script.
        code, result = self.generate("--size", "4x4", python_flags=("-S",))
        self.assertEqual(code, 0)
        self.assertEqual(result["images"][0]["width"], 8)
        self.assertTrue(any("Pillow" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
