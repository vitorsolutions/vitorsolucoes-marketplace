#!/usr/bin/env python3
"""Fail when a test run executed no tests.

A test command can exit with success when nothing ran: an empty suite, a
solution with no test project, or a suite where every test is skipped. This
script reads the structured result files and turns that case into a failure.

Usage:
  python assert_tests_ran.py [--min N] [--glob PATTERN ...] FILE_OR_DIR [FILE_OR_DIR ...]

Each argument is a result file or a folder that is searched for result files.
Two formats are read:
  *.trx   Visual Studio test results. The executed count comes from the
          Counters element of the summary.
  *.xml   JUnit results (for example pytest --junitxml). Every testcase that
          has no skipped child counts as executed.

An XML file found by searching a folder whose root element is not testsuite or
testsuites (for example a coverage report) is skipped and listed, so it cannot
count as a run or break the parse. A file named explicitly on the command line
must be a valid result file. --glob limits the folder search to file names that
match a pattern (repeatable), for example --glob "junit*.xml".

Exit status: 0 when at least N tests (default 1) executed, 1 otherwise,
including when no result file was found. Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import sys
import xml.etree.ElementTree as ET


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_trx(path: str) -> tuple[int, int]:
    """Return (executed, total) from a TRX file."""
    root = ET.parse(path).getroot()
    for element in root.iter():
        if local(element.tag) == "Counters":
            return int(element.get("executed", "0")), int(element.get("total", "0"))
    raise ValueError("no Counters element found")


def read_junit(path: str) -> tuple[int, int]:
    """Return (executed, total) from a JUnit file."""
    root = ET.parse(path).getroot()
    executed = total = 0
    for case in root.iter():
        if local(case.tag) != "testcase":
            continue
        total += 1
        if not any(local(child.tag) == "skipped" for child in case):
            executed += 1
    return executed, total


def is_junit(path: str) -> bool:
    """True when the XML file's root element is testsuite or testsuites."""
    return local(ET.parse(path).getroot().tag) in ("testsuite", "testsuites")


def collect(arguments: list[str], globs: list[str]) -> list[tuple[str, bool]]:
    """Return (path, explicit) pairs. Files found by a folder search are not explicit."""
    files: list[tuple[str, bool]] = []
    for argument in arguments:
        if os.path.isdir(argument):
            for folder, _, names in os.walk(argument):
                for name in names:
                    if not name.lower().endswith((".trx", ".xml")):
                        continue
                    if globs and not any(fnmatch.fnmatch(name, pattern) for pattern in globs):
                        continue
                    files.append((os.path.join(folder, name), False))
        elif os.path.isfile(argument):
            files.append((argument, True))
    return sorted(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail when a test run executed no tests.")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--min", type=int, default=1, dest="minimum")
    parser.add_argument("--glob", action="append", default=[], help="only search folders for file names matching this pattern")
    args = parser.parse_args()

    files = collect(args.paths, args.glob)
    if not files:
        print("FAIL: no test result files found. Nothing proves that tests ran.", file=sys.stderr)
        return 1

    executed = total = 0
    read_any = False
    for path, explicit in files:
        try:
            if path.lower().endswith(".trx"):
                reader = read_trx
            else:
                if not is_junit(path):
                    if explicit:
                        print(f"FAIL: {path} is not a JUnit or TRX result file.", file=sys.stderr)
                        return 1
                    print(f"{path}: skipped (not a JUnit result file)")
                    continue
                reader = read_junit
            e, t = reader(path)
        except (ET.ParseError, ValueError, OSError) as error:
            print(f"FAIL: could not read {path}: {error}", file=sys.stderr)
            return 1
        print(f"{path}: executed {e} of {t}")
        read_any = True
        executed += e
        total += t

    if not read_any:
        print("FAIL: no test result files found among the XML files. Nothing proves that tests ran.", file=sys.stderr)
        return 1

    print(f"total: executed {executed} of {total} (minimum {args.minimum})")
    if executed < args.minimum:
        print(
            f"FAIL: {executed} tests executed, at least {args.minimum} required. "
            "An empty or fully skipped suite is not a passing suite.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
