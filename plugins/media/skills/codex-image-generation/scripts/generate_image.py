#!/usr/bin/env python3
"""Generate or edit raster images with the built-in image tool of the Codex CLI.

The script drives `codex exec` with the user's own ChatGPT sign-in and Codex
configuration. It never calls an image API and never asks Codex to write files:

  1. Preconditions: the CLI is installed, signed in through ChatGPT, and the
     image_generation feature is not disabled.
  2. `codex exec` runs in an empty temporary directory with a read-only sandbox.
     The request goes through stdin, never through the command line.
  3. The images are taken from $CODEX_HOME/generated_images/<session id>/, so
     only files produced by this run are considered.
  4. Each file is checked by its signature, optionally resized, and copied to the
     destination without overwriting anything.

The only output on stdout is one JSON object. Exit status:

  0  every requested image was delivered (or --check passed)
  2  invalid arguments
  3  a precondition is not met; nothing was generated
  4  nothing was delivered
  5  only part of the requested images was delivered

Standard library only. Pillow is optional and used only for --size.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_PRECONDITION = 3
EXIT_FAILED = 4
EXIT_PARTIAL = 5

MAX_IMAGES = 8
MAX_INPUT_IMAGES = 5
MAX_INPUT_BYTES = 20 * 1024 * 1024
MAX_SIDE = 8192
PREFLIGHT_TIMEOUT = 60
DEFAULT_TIMEOUT = 600

# Removed from the child environment so that no run can be billed to an API key.
API_KEY_VARIABLES = ("OPENAI_API_KEY", "CODEX_API_KEY")

UNAVAILABLE_MARKER = "NATIVE_IMAGE_TOOL_UNAVAILABLE"
SESSION_ID_PATTERN = re.compile(r"\A[0-9A-Za-z][0-9A-Za-z_-]{7,127}\Z")
SECRET_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{10,}|Bearer\s+[A-Za-z0-9._~+/-]{10,}=*|eyJ[A-Za-z0-9._-]{20,}"
)
EXTENSIONS = {"png": (".png",), "jpeg": (".jpg", ".jpeg"), "webp": (".webp",)}
KNOWN_SUFFIXES = {suffix for group in EXTENSIONS.values() for suffix in group}


class SkillError(Exception):
    def __init__(self, status: str, message: str, exit_code: int):
        super().__init__(message)
        self.status = status
        self.exit_code = exit_code


def usage_error(message: str) -> SkillError:
    return SkillError("invalid_arguments", message, EXIT_USAGE)


def precondition_error(status: str, message: str) -> SkillError:
    return SkillError(status, message, EXIT_PRECONDITION)


# --- Image inspection ---------------------------------------------------------


def detect_format(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def image_size(data: bytes, kind: str) -> tuple[int, int] | None:
    try:
        if kind == "png":
            return struct.unpack(">II", data[16:24])
        if kind == "jpeg":
            position = 2
            while position + 9 < len(data):
                if data[position] != 0xFF:
                    position += 1
                    continue
                marker = data[position + 1]
                if marker == 0xFF:
                    position += 1
                    continue
                if marker == 0x01 or 0xD0 <= marker <= 0xD9:
                    position += 2
                    continue
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    height, width = struct.unpack(">HH", data[position + 5 : position + 9])
                    return width, height
                position += 2 + struct.unpack(">H", data[position + 2 : position + 4])[0]
            return None
        if kind == "webp":
            chunk = data[12:16]
            if chunk == b"VP8X":
                width = int.from_bytes(data[24:27], "little") + 1
                height = int.from_bytes(data[27:30], "little") + 1
                return width, height
            if chunk == b"VP8L":
                bits = int.from_bytes(data[21:25], "little")
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
            if chunk == b"VP8 ":
                width, height = struct.unpack("<HH", data[26:30])
                return width & 0x3FFF, height & 0x3FFF
    except (struct.error, IndexError):
        return None
    return None


def png_has_alpha(data: bytes) -> bool | None:
    """True when a PNG declares an alpha channel or a transparency chunk."""
    if detect_format(data) != "png" or len(data) < 26:
        return None
    if data[25] in (4, 6):
        return True
    position = 8
    while position + 8 <= len(data):
        length = int.from_bytes(data[position : position + 4], "big")
        chunk = data[position + 4 : position + 8]
        if chunk == b"tRNS":
            return True
        if chunk == b"IDAT":
            break
        position += 12 + length
    return False


# --- Processes ----------------------------------------------------------------


def find_codex() -> str | None:
    """Looks for codex in absolute PATH entries only.

    shutil.which also searches the current directory on Windows, which would let a
    repository ship its own `codex.cmd`.
    """
    if os.name == "nt":
        extensions = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
        names = ["codex" + extension for extension in extensions if extension]
    else:
        names = ["codex"]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        directory = entry.strip('"')
        if not directory or not os.path.isabs(directory):
            continue
        for name in names:
            candidate = os.path.join(directory, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return None


def child_environment() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key.upper() not in API_KEY_VARIABLES}


def kill_tree(process: subprocess.Popen) -> None:
    # codex may be a wrapper script, so killing only the direct child is not enough.
    if os.name == "nt":
        taskkill = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "taskkill.exe")
        subprocess.run([taskkill, "/T", "/F", "/PID", str(process.pid)], capture_output=True, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.kill()
    process.wait()


def run_process(command: list[str], work_dir: Path, log_dir: Path, timeout: float, stdin_text: str = ""):
    """Returns (exit status, stdout, stderr). The status is None after a timeout.

    Streams go through files, so a surviving grandchild cannot block the read.
    """
    stdin_path, stdout_path, stderr_path = (log_dir / name for name in ("stdin", "stdout", "stderr"))
    stdin_path.write_bytes(stdin_text.encode("utf-8"))
    with stdin_path.open("rb") as stdin, stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            process = subprocess.Popen(
                command,
                cwd=work_dir,
                env=child_environment(),
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                start_new_session=os.name != "nt",
            )
        except OSError as error:
            raise precondition_error("codex_not_runnable", f"Could not start the Codex CLI: {error}")
        try:
            status = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            kill_tree(process)
            status = None
        except BaseException:
            kill_tree(process)
            raise
    return (
        status,
        stdout_path.read_text("utf-8", errors="replace"),
        stderr_path.read_text("utf-8", errors="replace"),
    )


def preflight(codex: str, work_dir: Path, log_dir: Path) -> list[str]:
    status, stdout, stderr = run_process([codex, "login", "status"], work_dir, log_dir, PREFLIGHT_TIMEOUT)
    report = f"{stdout}\n{stderr}".lower()
    if status != 0 or "logged in using chatgpt" not in report:
        if "api key" in report:
            raise precondition_error(
                "api_key_login",
                "Codex is signed in with an API key, which would bill the OpenAI API. This skill only "
                "uses a ChatGPT sign-in. The user can switch with `codex logout` and `codex login`.",
            )
        raise precondition_error(
            "not_logged_in",
            "Codex is not signed in through ChatGPT. The user needs to run `codex login`.",
        )

    status, stdout, _ = run_process([codex, "features", "list"], work_dir, log_dir, PREFLIGHT_TIMEOUT)
    for line in stdout.splitlines():
        fields = line.split()
        if status == 0 and fields and fields[0] == "image_generation":
            if fields[-1].lower() != "true":
                raise precondition_error(
                    "feature_disabled",
                    "The image_generation feature is disabled in this Codex configuration. The user can "
                    "enable it with `codex features enable image_generation`.",
                )
            return []
    return ["Could not confirm that the image_generation feature is enabled; the run will show it."]


# --- Request ------------------------------------------------------------------


def parse_size(text: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{1,5})[xX](\d{1,5})", text.strip())
    if not match:
        raise usage_error("--size must look like 1080x1920.")
    width, height = int(match.group(1)), int(match.group(2))
    if not (1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE):
        raise usage_error(f"--size sides must be between 1 and {MAX_SIDE}.")
    return width, height


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt is not None:
        text = args.prompt
    elif args.prompt_file == "-":
        text = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
    elif args.prompt_file:
        try:
            text = Path(args.prompt_file).expanduser().read_text("utf-8-sig")
        except (OSError, UnicodeDecodeError) as error:
            raise usage_error(f"Could not read --prompt-file as UTF-8 text: {error}")
    else:
        raise usage_error("Provide --prompt or --prompt-file.")
    if not text.strip():
        raise usage_error("The prompt is empty.")
    return text.strip()


def load_inputs(args: argparse.Namespace) -> list[tuple[str, str, bytes]]:
    """Returns (role, format, content) for each input image, edit target first."""
    requested = ([("edit target", args.edit)] if args.edit else []) + [
        ("reference", path) for path in args.reference
    ]
    if len(requested) > MAX_INPUT_IMAGES:
        raise usage_error(f"At most {MAX_INPUT_IMAGES} input images are accepted.")
    inputs = []
    for role, name in requested:
        path = Path(name).expanduser()
        if not path.is_file():
            raise usage_error(f"Input image not found: {path}")
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise usage_error(f"Input image is larger than {MAX_INPUT_BYTES // (1024 * 1024)} MB: {path}")
        content = path.read_bytes()
        kind = detect_format(content)
        if kind is None:
            raise usage_error(f"Input is not a PNG, JPEG, or WebP image: {path}")
        inputs.append((role, kind, content))
    return inputs


def build_task(prompt: str, count: int, roles: list[str], size: tuple[int, int] | None) -> str:
    lines = [
        "You are running non-interactively to produce images with your built-in image generation tool.",
        "",
        "Rules:",
        f"- Produce exactly {count} image(s), with one built-in tool call per image.",
        "- Do not run shell commands and do not write, copy, move, or resize files. The caller collects",
        "  the generated images.",
        "- Do not use an API key, a command-line image fallback, or any substitute such as drawing the",
        "  picture with code or SVG.",
        f"- If the built-in tool is not available, reply only with {UNAVAILABLE_MARKER} and the reason.",
        "- Do not ask questions. If you cannot or will not generate the image, say why.",
    ]
    if count > 1:
        lines.append("- Make the images meaningfully different variations of the same request.")
    if size:
        lines += [
            f"- The result will later be scaled and center-cropped to {size[0]}x{size[1]} pixels. Compose",
            "  for that aspect ratio and keep important content and text away from the edges.",
        ]
    if roles:
        lines += ["", "Attached images, in order:"]
        lines += [f"- Image {index}: {role}" for index, role in enumerate(roles, start=1)]
        if "edit target" in roles:
            lines.append(
                "Edit the edit target. Change only what the request asks for and keep everything else as it is."
            )
        else:
            lines.append("Use the references as guidance for a new image; do not simply reproduce them.")
    lines += ["", "Image request:", "<request>", prompt, "</request>"]
    return "\n".join(lines) + "\n"


# --- Results ------------------------------------------------------------------


def parse_events(output: str) -> tuple[str | None, list[str], list[str]]:
    session_id, messages, errors = None, [], []
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        if kind == "thread.started":
            session_id = event.get("thread_id")
        elif kind == "item.completed" and item.get("type") == "agent_message":
            messages.append(str(item.get("text", "")))
        elif kind == "item.completed" and item.get("type") == "error":
            errors.append(str(item.get("message", "")))
        elif kind == "error":
            errors.append(str(event.get("message", "")))
        elif kind == "turn.failed":
            failure = event.get("error")
            errors.append(str(failure.get("message", "") if isinstance(failure, dict) else failure))
    return session_id, messages, errors


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser().resolve() if configured else Path.home() / ".codex"


def collect_images(session_id: str | None) -> list[tuple[Path, str, bytes]]:
    if not isinstance(session_id, str) or not SESSION_ID_PATTERN.match(session_id):
        return []
    directory = codex_home() / "generated_images" / session_id
    if not directory.is_dir():
        return []
    found = []
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file():
            continue
        content = path.read_bytes()
        kind = detect_format(content)
        if kind:
            found.append((path.stat().st_mtime_ns, path.name, path, kind, content))
    return [(path, kind, content) for _, _, path, kind, content in sorted(found, key=lambda f: f[:2])]


def resize(content: bytes, kind: str, size: tuple[int, int]) -> tuple[bytes, list[str]]:
    """Scales to cover the target and crops the center, without distortion."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return content, [
            "Pillow is not installed, so the image was delivered at its generated size. "
            "Install it with `python -m pip install pillow` to use --size."
        ]
    warnings = []
    try:
        with Image.open(io.BytesIO(content)) as source:
            source.load()
            width, height = source.size
            if size[0] > width or size[1] > height:
                warnings.append(f"The image was upscaled from {width}x{height}; expect some softness.")
            source_ratio, target_ratio = width / height, size[0] / size[1]
            lost = 1 - min(source_ratio, target_ratio) / max(source_ratio, target_ratio)
            if lost > 0.02:
                axis = "width" if source_ratio > target_ratio else "height"
                warnings.append(f"The center crop removed about {lost:.0%} of the {axis}; check the edges.")
            if source.mode not in ("RGB", "RGBA", "L", "LA"):
                source = source.convert("RGBA")
            method = getattr(Image, "Resampling", Image).LANCZOS
            fitted = ImageOps.fit(source, size, method=method)
            buffer = io.BytesIO()
            options = {"quality": 95} if kind in ("jpeg", "webp") else {}
            fitted.save(buffer, format=kind.upper(), **options)
    except (OSError, ValueError) as error:
        return content, [f"Resize failed, so the image was delivered at its generated size: {error}"]
    return buffer.getvalue(), warnings


def destination_for(out: Path, kind: str, index: int | None) -> tuple[Path, list[str]]:
    suffix = out.suffix.lower()
    warnings = []
    if suffix in KNOWN_SUFFIXES:
        stem = out.name[: -len(out.suffix)]
        if suffix in EXTENSIONS[kind]:
            suffix = out.suffix
        else:
            suffix = EXTENSIONS[kind][0]
            warnings.append(f"The generated file is {kind.upper()}, so the extension is {suffix}.")
    else:
        stem, suffix = out.name, EXTENSIONS[kind][0]
    if index is not None:
        stem = f"{stem}-{index}"
    return out.with_name(stem + suffix), warnings


def write_new_file(path: Path, content: bytes) -> Path:
    """Writes without replacing anything: name.png, name-v2.png, name-v3.png, ..."""
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate, version = path, 1
    while True:
        try:
            with candidate.open("xb") as handle:
                handle.write(content)
            return candidate
        except FileExistsError:
            version += 1
            candidate = path.with_name(f"{path.stem}-v{version}{path.suffix}")


def deliver(images, out: Path, requested: int, size: tuple[int, int] | None):
    numbered = requested > 1 or len(images) > 1
    delivered, warnings = [], []
    for index, (source, kind, content) in enumerate(images, start=1):
        if size:
            content, notes = resize(content, kind, size)
            warnings += notes
        target, notes = destination_for(out, kind, index if numbered else None)
        warnings += notes
        try:
            written = write_new_file(target, content)
        except OSError as error:
            warnings.append(f"Could not write {target}: {error}. The generated file is at {source}.")
            continue
        if written != target:
            warnings.append(f"{target.name} already exists; saved as {written.name}.")
        dimensions = image_size(content, kind)
        delivered.append(
            {
                "path": str(written.resolve()),
                "format": kind,
                "width": dimensions[0] if dimensions else None,
                "height": dimensions[1] if dimensions else None,
                "alpha_channel": png_has_alpha(content),
                "bytes": len(content),
                "source": str(source),
            }
        )
    return delivered, list(dict.fromkeys(warnings))


def redact(text: str, limit: int = 2000) -> str:
    return SECRET_PATTERN.sub("[redacted]", text)[-limit:]


# --- Entry point --------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or edit images with the Codex CLI built-in image tool.",
        allow_abbrev=False,
    )
    parser.add_argument("--check", action="store_true", help="verify preconditions only; generates nothing")
    request = parser.add_mutually_exclusive_group()
    request.add_argument("--prompt", help="image description")
    request.add_argument("--prompt-file", help="UTF-8 file with the description, or - for stdin")
    parser.add_argument("--out", help="destination file; -1, -2, ... are appended for several images")
    parser.add_argument("--n", type=int, default=1, help=f"number of variations, 1 to {MAX_IMAGES}")
    parser.add_argument("--edit", help="existing image to modify; the original is left untouched")
    parser.add_argument("--reference", action="append", default=[], help="guidance image; repeatable")
    parser.add_argument("--size", help="final WIDTHxHEIGHT, applied locally with a center crop")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="seconds allowed for Codex")
    return parser


def run(args: argparse.Namespace, temp: Path) -> tuple[dict, int]:
    if not args.check:
        prompt = read_prompt(args)
        if not args.out:
            raise usage_error("Provide --out.")
        if not 1 <= args.n <= MAX_IMAGES:
            raise usage_error(f"--n must be between 1 and {MAX_IMAGES}.")
        if args.timeout < 1:
            raise usage_error("--timeout must be positive.")
        size = parse_size(args.size) if args.size else None
        out = Path(args.out).expanduser()
        if out.is_dir() or args.out.endswith(("/", os.sep)):
            raise usage_error("--out must be a file path, not a directory.")
        inputs = load_inputs(args)

    codex = find_codex()
    if codex is None:
        raise precondition_error(
            "codex_not_found",
            "The Codex CLI was not found on PATH. The user needs to install it "
            "(for example `npm install -g @openai/codex`) and run `codex login`.",
        )
    work_dir, log_dir = temp / "work", temp / "logs"
    work_dir.mkdir()
    log_dir.mkdir()
    warnings = preflight(codex, work_dir, log_dir)
    if args.check:
        return {"status": "ready", "codex": codex, "warnings": warnings}, EXIT_OK

    # Inputs get fixed names inside the work directory: no user-controlled text reaches the
    # command line, which matters because codex can be a .cmd wrapper on Windows.
    command = [codex, "exec"]
    for index, (_, kind, content) in enumerate(inputs, start=1):
        name = f"input-{index}{EXTENSIONS[kind][0]}"
        (work_dir / name).write_bytes(content)
        command += ["--image", name]
    command += ["--json", "--skip-git-repo-check", "--sandbox", "read-only"]

    task = build_task(prompt, args.n, [role for role, _, _ in inputs], size)
    status, stdout, stderr = run_process(command, work_dir, log_dir, args.timeout, task)
    session_id, messages, errors = parse_events(stdout)
    generated = collect_images(session_id)
    images, delivery_warnings = deliver(generated, out, args.n, size)
    warnings += delivery_warnings

    if status is None:
        warnings.append(f"Codex did not finish within {args.timeout} seconds and was stopped.")
    elif status != 0:
        warnings.append(f"Codex exited with status {status}.")
    if len(images) > args.n:
        warnings.append(f"Codex produced {len(images)} images, more than the {args.n} requested.")

    result = {
        "status": "ok",
        "requested": args.n,
        "delivered": len(images),
        "images": images,
        "session_id": session_id,
        "codex_reply": redact(messages[-1]) if messages else None,
        "warnings": warnings,
    }
    if len(images) >= args.n:
        return result, EXIT_OK
    if errors:
        result["errors"] = [redact(error, 600) for error in errors[-3:]]
    if status != 0 or not images:
        result["stderr_tail"] = redact("\n".join(stderr.splitlines()[-15:]))
    if images:
        result["status"] = "partial"
        return result, EXIT_PARTIAL
    if generated:
        # Usage was already consumed; the warnings say where the files are.
        result["status"] = "io_error"
    elif any(UNAVAILABLE_MARKER in message for message in messages):
        result["status"] = "tool_unavailable"
    elif status is None:
        result["status"] = "timeout"
    else:
        result["status"] = "no_image"
    return result, EXIT_FAILED


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    temp = Path(tempfile.mkdtemp(prefix="codex-image-"))
    try:
        result, exit_code = run(args, temp)
    except SkillError as error:
        result, exit_code = {"status": error.status, "message": str(error)}, error.exit_code
    except OSError as error:
        result, exit_code = {"status": "io_error", "message": str(error)}, EXIT_FAILED
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
