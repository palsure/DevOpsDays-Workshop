#!/usr/bin/env python3
"""
junit_to_allure.py

Convert a directory of JUnit / xUnit XML files into Allure 2 result JSON files
so `allure generate` can render a real HTML report.

Why: `allure generate` only consumes the Allure result format
(*-result.json + *-attachment.*). Frameworks like Swift's
`swift test --xunit-output` or plain XCTest emit JUnit XML, which Allure
ignores — producing an "Allure Report Unknown / 0 test cases" page.

This converter handles both common root shapes:
  • <testsuite>   ... </testsuite>            (Gradle TEST-*.xml, Surefire)
  • <testsuites>  <testsuite>…</testsuite> </testsuites>   (Swift, Jest,
                                                           Vitest, Playwright)

Usage:
  python3 junit_to_allure.py --input <dir-with-xml> --output <allure-results-dir>

The output directory is populated with one `<uuid>-result.json` per test case.
Existing files in the output directory are left in place; the directory is
created if needed.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path


def _now_ms() -> int:
    return int(time.time() * 1000)


def _stable_uuid(*parts: str) -> str:
    """Deterministic UUID so re-running on the same XML produces the same files
    (helps Allure's history/trend tracking)."""
    h = hashlib.sha1("\u0001".join(parts).encode("utf-8")).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _status_for(testcase: ET.Element) -> tuple[str, dict | None]:
    """Map JUnit testcase result into Allure (status, status_details)."""
    failure = testcase.find("failure")
    error = testcase.find("error")
    skipped = testcase.find("skipped")

    if failure is not None:
        return "failed", {
            "message": failure.attrib.get("message", "") or (failure.text or "").strip()[:500],
            "trace":   (failure.text or "").strip(),
        }
    if error is not None:
        return "broken", {
            "message": error.attrib.get("message", "") or (error.text or "").strip()[:500],
            "trace":   (error.text or "").strip(),
        }
    if skipped is not None:
        return "skipped", {
            "message": skipped.attrib.get("message", "") or "Skipped",
            "trace":   (skipped.text or "").strip(),
        }
    return "passed", None


def _suites(root: ET.Element):
    """Yield every <testsuite> regardless of root shape."""
    if root.tag == "testsuites":
        for s in root.findall("testsuite"):
            yield s
    elif root.tag == "testsuite":
        yield root


def _convert_file(xml_path: Path, out_dir: Path) -> int:
    """Convert one XML file and return the number of test cases written."""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        print(f"⚠️  {xml_path}: parse error — {exc}", file=sys.stderr)
        return 0

    written = 0
    for suite in _suites(root):
        suite_name = suite.attrib.get("name", "TestSuite")
        # Use whichever timestamp the runner provided; fall back to "now".
        try:
            base_ts = int(float(suite.attrib.get("timestamp", "")) * 1000)
        except (TypeError, ValueError):
            base_ts = _now_ms()

        for tc in suite.findall("testcase"):
            classname = tc.attrib.get("classname", suite_name)
            name = tc.attrib.get("name", "anonymous")
            full_name = f"{classname}.{name}" if classname else name
            try:
                duration_ms = int(float(tc.attrib.get("time", "0")) * 1000)
            except ValueError:
                duration_ms = 0

            status, details = _status_for(tc)
            test_uuid = _stable_uuid(xml_path.name, full_name)
            history_id = hashlib.md5(full_name.encode("utf-8")).hexdigest()

            result: dict = {
                "uuid":      test_uuid,
                "historyId": history_id,
                "name":      name,
                "fullName":  full_name,
                "status":    status,
                "stage":     "finished",
                "start":     base_ts,
                "stop":      base_ts + max(0, duration_ms),
                "labels": [
                    {"name": "suite",     "value": suite_name},
                    {"name": "testClass", "value": classname or suite_name},
                    {"name": "testMethod","value": name},
                    {"name": "framework", "value": "junit"},
                    {"name": "language",  "value": "swift"},
                ],
            }
            if details is not None:
                # Allure renders `statusDetails.message` and `.trace` in the UI.
                result["statusDetails"] = {
                    k: v for k, v in details.items() if v
                }

            (out_dir / f"{test_uuid}-result.json").write_text(
                json.dumps(result, indent=2), encoding="utf-8"
            )
            written += 1

    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input",  required=True, help="Directory containing JUnit XML files")
    ap.add_argument("--output", required=True, help="Allure results output directory")
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output)

    if not in_dir.exists():
        print(f"⚠️  Input directory not found: {in_dir}", file=sys.stderr)
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(
        set(glob.glob(str(in_dir / "**/*.xml"), recursive=True))
        - set(glob.glob(str(out_dir / "**/*.xml"), recursive=True))
    )
    if not xml_files:
        print(f"ℹ️  No XML files found under {in_dir}")
        return 0

    total = 0
    for xml in xml_files:
        n = _convert_file(Path(xml), out_dir)
        print(f"  • {xml} → {n} test case(s)")
        total += n

    # Drop a minimal environment.properties so Allure's "Environment" widget
    # isn't blank (the empty UI was the visible symptom).
    env_props = out_dir / "environment.properties"
    if not env_props.exists():
        env_props.write_text(
            "Source=junit_to_allure.py\n"
            f"Generated={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n",
            encoding="utf-8",
        )

    # And executor.json so the Allure header reads sensibly in CI.
    executor = out_dir / "executor.json"
    if not executor.exists():
        executor.write_text(json.dumps({
            "name":       os.environ.get("GITHUB_WORKFLOW", "CI"),
            "type":       "github",
            "url":        os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
            "buildOrder": int(os.environ.get("GITHUB_RUN_NUMBER", "0") or "0"),
            "buildName":  f"#{os.environ.get('GITHUB_RUN_NUMBER', '0')}",
            "buildUrl":   (
                f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
                f"{os.environ.get('GITHUB_RUN_ID', '')}"
            ),
            "reportName": os.environ.get("ALLURE_REPORT_NAME", "Allure Report"),
        }, indent=2), encoding="utf-8")

    print(f"✅ Converted {total} test case(s) → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
