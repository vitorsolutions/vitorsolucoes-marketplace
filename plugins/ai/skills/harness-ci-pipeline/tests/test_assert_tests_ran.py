"""Tests for scripts/assert_tests_ran.py.

Run from the skill folder:  python -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "assert_tests_ran.py")

TRX = """<?xml version="1.0" encoding="UTF-8"?>
<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">
  <ResultSummary outcome="Completed">
    <Counters total="{total}" executed="{executed}" passed="{executed}" failed="0" error="0" timeout="0"
              aborted="0" inconclusive="0" passedButRunAborted="0" notRunnable="0" notExecuted="0"
              disconnected="0" warning="0" completed="0" inProgress="0" pending="0" />
  </ResultSummary>
</TestRun>
"""

JUNIT_RUN = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="2">
<testcase classname="a" name="t1" time="0.01"/><testcase classname="a" name="t2" time="0.01"/>
</testsuite></testsuites>
"""

JUNIT_ALL_SKIPPED = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="1" tests="1">
<testcase classname="a" name="t1" time="0.0"><skipped type="pytest.skip" message="x"/></testcase>
</testsuite></testsuites>
"""

JUNIT_MIXED = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="outer" tests="3">
<testsuite name="inner" tests="3">
<testcase name="ran"/><testcase name="failed"><failure message="x"/></testcase>
<testcase name="skipped"><skipped/></testcase>
</testsuite></testsuite></testsuites>
"""


def run(files: dict[str, str], extra=None, args_override=None):
    with tempfile.TemporaryDirectory() as folder:
        paths = []
        for name, content in files.items():
            path = os.path.join(folder, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)
            paths.append(path)
        arguments = args_override(folder) if args_override else [folder]
        return subprocess.run(
            [sys.executable, SCRIPT, *(extra or []), *arguments], capture_output=True, text=True, timeout=60
        )


class AssertTestsRanTests(unittest.TestCase):
    def test_trx_with_tests_passes(self):
        self.assertEqual(run({"r.trx": TRX.format(total=3, executed=3)}).returncode, 0)

    def test_trx_with_zero_tests_fails(self):
        result = run({"r.trx": TRX.format(total=0, executed=0)})
        self.assertEqual(result.returncode, 1)
        self.assertIn("at least 1", result.stderr)

    def test_trx_with_only_skipped_tests_fails(self):
        self.assertEqual(run({"r.trx": TRX.format(total=2, executed=0)}).returncode, 1)

    def test_junit_with_tests_passes(self):
        self.assertEqual(run({"junit.xml": JUNIT_RUN}).returncode, 0)

    def test_junit_all_skipped_fails(self):
        result = run({"junit.xml": JUNIT_ALL_SKIPPED})
        self.assertEqual(result.returncode, 1)
        self.assertIn("executed 0 of 1", result.stdout)

    def test_junit_nested_suites_are_not_double_counted(self):
        result = run({"junit.xml": JUNIT_MIXED})
        self.assertEqual(result.returncode, 0)
        self.assertIn("executed 2 of 3", result.stdout)

    def test_no_files_fails(self):
        result = run({"notes.txt": "nothing"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("no test result files", result.stderr)

    def test_missing_path_fails(self):
        result = subprocess.run([sys.executable, SCRIPT, "definitely-not-a-folder-xyz"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_corrupt_file_fails(self):
        result = run({"r.trx": "<TestRun"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("could not read", result.stderr)

    def test_minimum_is_respected(self):
        self.assertEqual(run({"r.trx": TRX.format(total=2, executed=2)}, extra=["--min", "3"]).returncode, 1)
        self.assertEqual(run({"r.trx": TRX.format(total=3, executed=3)}, extra=["--min", "3"]).returncode, 0)

    def test_several_files_are_summed(self):
        result = run({"a/r.trx": TRX.format(total=1, executed=1), "b/junit.xml": JUNIT_RUN})
        self.assertEqual(result.returncode, 0)
        self.assertIn("executed 3 of 3", result.stdout)

    def test_coverage_xml_in_the_folder_is_skipped(self):
        coverage = '<coverage line-rate="0.5"><packages/></coverage>'
        result = run({"junit.xml": JUNIT_RUN, "coverage.xml": coverage})
        self.assertEqual(result.returncode, 0)
        self.assertIn("skipped (not a JUnit result file)", result.stdout)
        self.assertIn("executed 2 of 2", result.stdout)

    def test_only_non_junit_xml_fails(self):
        result = run({"coverage.xml": '<coverage line-rate="0.5"/>'})
        self.assertEqual(result.returncode, 1)
        self.assertIn("no test result files", result.stderr)

    def test_explicit_non_junit_file_fails(self):
        result = run({"coverage.xml": '<coverage/>'}, args_override=lambda folder: [os.path.join(folder, "coverage.xml")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a JUnit or TRX", result.stderr)

    def test_corrupt_xml_in_the_folder_still_fails(self):
        result = run({"junit.xml": JUNIT_RUN, "broken.xml": "<testsuite"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("could not read", result.stderr)

    def test_glob_limits_the_folder_search(self):
        files = {"junit-a.xml": JUNIT_RUN, "broken.xml": "<testsuite"}
        self.assertEqual(run(files, extra=["--glob", "junit*.xml"]).returncode, 0)
        self.assertEqual(run(files).returncode, 1)

    def test_a_trx_without_counters_fails(self):
        self.assertEqual(run({"r.trx": '<TestRun xmlns="x"><ResultSummary/></TestRun>'}).returncode, 1)


if __name__ == "__main__":
    unittest.main()
