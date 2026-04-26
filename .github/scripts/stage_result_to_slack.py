#!/usr/bin/env python3
"""
stage_result_to_slack.py

Generates a Slack Block Kit thread-reply payload for a single pipeline stage.
Parses JUnit-compatible XML (Gradle test results, Maven Surefire) for real stats.
Optionally parses a Playwright JSON report for web E2E stats.

Required env vars:
  MODULE_NAME    — display name e.g. "ANDROID", "WEB", "iOS", "API"
  STAGE_NAME     — e.g. "Unit Tests", "E2E Tests", "Automation E2E"

Optional env vars:
  JUNIT_DIR      — directory containing TEST-*.xml or surefire TEST-*.xml files
  PLAYWRIGHT_JSON — path to Playwright JSON report file (web E2E)
  REPORT_URL     — link to the HTML report artifact
  STAGE_RESULT   — success | failure | skipped (fallback when no XML found)
  THREAD_TS      — Slack thread_ts for the reply (set to post as thread reply)
  GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_RUN_NUMBER, GITHUB_SHA

Output: stage-slack-payload.json
"""
from __future__ import annotations

import glob
import json
import math
import os
import xml.etree.ElementTree as ET
from pathlib import Path


PASS_THRESHOLD = 80.0


def parse_junit(junit_dir: str) -> tuple[int, int, int, int]:
    """Return (passed, failed, skipped, total) from JUnit XML files."""
    total = passed = failed = skipped = 0
    for f in glob.glob(f"{junit_dir}/**/TEST-*.xml", recursive=True):
        try:
            root = ET.parse(f).getroot()
            t  = int(root.attrib.get("tests",    0))
            fa = int(root.attrib.get("failures", 0)) + int(root.attrib.get("errors", 0))
            s  = int(root.attrib.get("skipped",  0))
            total   += t
            failed  += fa
            skipped += s
            passed  += max(0, t - fa - s)
        except Exception:
            pass
    return passed, failed, skipped, total


def parse_playwright(json_path: str) -> tuple[int, int, int, int]:
    """Return (passed, failed, skipped, total) from Playwright JSON report."""
    try:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        passed = data.get("passed",  0)
        failed = data.get("failed",  0)
        skipped = data.get("skipped", 0)
        total  = data.get("total",   passed + failed + skipped)
        return passed, failed, skipped, total
    except Exception:
        return 0, 0, 0, 0


def status_icon(passed: int, total: int) -> str:
    if total == 0:
        return ":white_circle:"
    rate = 100.0 * passed / total
    if rate >= PASS_THRESHOLD:
        return ":large_green_circle:"
    if rate >= 50.0:
        return ":large_yellow_circle:"
    return ":red_circle:"


def pct(passed: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{math.floor(100.0 * passed / total)}%"


def main() -> int:
    module       = os.environ.get("MODULE_NAME", "MODULE")
    stage        = os.environ.get("STAGE_NAME", "Stage")
    junit_dir    = os.environ.get("JUNIT_DIR", "")
    pw_json      = os.environ.get("PLAYWRIGHT_JSON", "")
    report_url   = os.environ.get("REPORT_URL", "")
    stage_result = os.environ.get("STAGE_RESULT", "unknown")
    thread_ts    = os.environ.get("THREAD_TS", "")

    repo       = os.environ.get("GITHUB_REPOSITORY", "repo")
    run_id     = os.environ.get("GITHUB_RUN_ID", "")
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "")
    sha_full   = os.environ.get("GITHUB_SHA", "unknown")
    sha        = sha_full[:7]

    run_url    = (
        f"https://github.com/{repo}/actions/runs/{run_id}"
        if run_id else f"https://github.com/{repo}"
    )
    commit_url  = f"https://github.com/{repo}/commit/{sha_full}"
    build_label = f"Build #{run_number}" if run_number else f"Run {run_id}"

    # ── Parse test results ────────────────────────────────────────────────────
    passed = failed = skipped = total = 0
    has_stats = False

    if pw_json and Path(pw_json).exists():
        passed, failed, skipped, total = parse_playwright(pw_json)
        has_stats = total > 0

    if not has_stats and junit_dir:
        passed, failed, skipped, total = parse_junit(junit_dir)
        has_stats = total > 0

    # ── Determine verdict ─────────────────────────────────────────────────────
    if has_stats:
        verdict = "PASSED" if failed == 0 else "FAILED"
        icon    = status_icon(passed, total)
    else:
        verdict = {
            "success": "PASSED", "failure": "FAILED",
            "skipped": "SKIPPED", "cancelled": "CANCELLED",
        }.get(stage_result.lower(), "UNKNOWN")
        icon = {
            "PASSED": ":large_green_circle:", "FAILED": ":red_circle:",
            "SKIPPED": ":white_circle:",       "CANCELLED": ":white_circle:",
        }.get(verdict, ":white_circle:")

    # ── Stats text ────────────────────────────────────────────────────────────
    if has_stats:
        stats_text = (
            f"{icon}  "
            f"*Passed:* {passed}  |  *Failed:* {failed}  |  "
            f"*Skipped:* {skipped}  |  *Total:* {total}  |  "
            f"*Pass Rate:* {pct(passed, total)}"
        )
    else:
        stats_text = f"{icon}  *Result:* {verdict}"

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_parts = [f"<{commit_url}|{sha}>  •  {build_label}"]
    if report_url:
        footer_parts.append(f"<{report_url}|:bar_chart: View Report>")
    footer_parts.append(f"<{run_url}|:arrow_forward: View Run>")
    footer_text = "    ".join(footer_parts)

    # ── Payload ───────────────────────────────────────────────────────────────
    payload: dict = {
        "unfurl_links": False,
        "unfurl_media": False,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"[{module}] {stage} — {verdict}  |  {build_label}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": stats_text},
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": footer_text}],
            },
        ],
    }

    if thread_ts:
        payload["thread_ts"] = thread_ts

    out = Path("stage-slack-payload.json")
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
