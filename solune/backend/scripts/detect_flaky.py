#!/usr/bin/env python3
"""Detect flaky tests by comparing multiple JUnit XML result files."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_junit_results(path: Path) -> dict[str, bool]:
    """Parse JUnit XML and return {test_name: passed} mapping.

    A test case is considered *failed* if it contains a ``<failure>`` or
    ``<error>`` child element; otherwise it is considered *passed*.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    results: dict[str, bool] = {}
    # Handle both <testsuites><testsuite>... and bare <testsuite>...
    testcases = root.iter("testcase")
    for tc in testcases:
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        full_name = f"{classname}.{name}" if classname else name

        failed = tc.find("failure") is not None or tc.find("error") is not None
        results[full_name] = not failed

    return results


def detect_flaky_tests(result_files: list[Path]) -> list[dict]:
    """Compare test results across runs, return flaky test info.

    A test is *flaky* if it passes in some runs and fails in others.
    """
    # test_name → list of (file_label, passed)
    all_results: dict[str, list[tuple[str, bool]]] = {}

    for path in result_files:
        run_results = parse_junit_results(path)
        for test_name, passed in run_results.items():
            all_results.setdefault(test_name, []).append((path.name, passed))

    flaky: list[dict] = []
    for test_name, outcomes in sorted(all_results.items()):
        passed_set = {passed for _, passed in outcomes}
        if len(passed_set) > 1:
            pattern = ", ".join(
                f"{label}: {'PASS' if passed else 'FAIL'}" for label, passed in outcomes
            )
            flaky.append({"test": test_name, "pattern": pattern})

    return flaky


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: detect_flaky.py <result1.xml> [result2.xml ...]", file=sys.stderr)
        sys.exit(2)

    paths = [Path(p) for p in sys.argv[1:]]
    for p in paths:
        if not p.exists():
            print(f"Error: file not found: {p}", file=sys.stderr)
            sys.exit(2)

    flaky_tests = detect_flaky_tests(paths)

    if not flaky_tests:
        print("No flaky tests detected.")
        sys.exit(0)

    print(f"Found {len(flaky_tests)} flaky test(s):\n")
    for entry in flaky_tests:
        print(f"  {entry['test']}")
        print(f"    Pattern: {entry['pattern']}\n")

    sys.exit(1)


if __name__ == "__main__":
    main()
