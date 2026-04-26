#!/usr/bin/env python3
"""
Build a Slack Block Kit payload for the API test run.

Matches the format:

  [ENV] QoE — API Automation Tests Report
  Branch: main | Test Type: unit | Stage: pre-deploy
  -----------------------------------------------
  Passed(%)   Failed  Skipped  Total  Status  Reports   Platform
  -----------------------------------------------
  271 (95%)   12      7        290    🔴      Allure    androidphone
  274 (96%)   11      6        291    🔴      Allure    iphone
  -----------------------------------------------
  Duration: 6 min, 17 sec
  BuildUrl: <link>
  Artifacts: UnitReport | E2EReport

Input (stdin or first argument): JSON file with schema:
{
  "env":      "stage",           // optional, default "stage"
  "testType": "unit | e2e",
  "stage":    "pre-deploy | post-deploy",
  "branch":   "main",
  "duration": "6 min 17 sec",   // optional
  "allureUrl": "https://...",   // optional Allure hosted URL or Actions URL
  "platforms": [
    {
      "platform": "androidphone",
      "passed":   271,
      "failed":   12,
      "skipped":  7,
      "total":    290,
      "allureUrl": "https://..."   // per-platform override (optional)
    }
  ]
}
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path


PASS_THRESHOLD = float(os.environ.get("QUALITY_GATE_THRESHOLD", "80"))


def status_icon(passed: int, total: int) -> str:
    rate = (100.0 * passed / total) if total > 0 else 0.0
    return ":large_green_circle:" if rate >= PASS_THRESHOLD else ":red_circle:"


def pct(passed: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{math.floor(100.0 * passed / total)}%"


def main() -> int:
    # ------------------------------------------------------------------
    # Read input
    # ------------------------------------------------------------------
    src = sys.argv[1] if len(sys.argv) > 1 else "api-test-report.json"
    try:
        data = json.loads(Path(src).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read {src}: {e}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # Context from input + GitHub env
    # ------------------------------------------------------------------
    repo       = os.environ.get("GITHUB_REPOSITORY", data.get("repo", "repo"))
    run_id     = os.environ.get("GITHUB_RUN_ID", data.get("runId", ""))
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "")
    branch     = os.environ.get("GITHUB_REF_NAME", data.get("branch", "unknown"))
    sha        = (os.environ.get("GITHUB_SHA", "") or "")[:7] or "unknown"
    env_name   = data.get("env", "STAGE").upper()
    test_type  = data.get("testType", "e2e").upper()
    stage      = data.get("stage", "post-deploy")
    duration   = data.get("duration", "")
    platforms  = data.get("platforms", [])

    build_url = (
        f"https://github.com/{repo}/actions/runs/{run_id}"
        if run_id else f"https://github.com/{repo}"
    )
    default_allure = data.get("allureUrl", build_url)

    # ------------------------------------------------------------------
    # Aggregate totals
    # ------------------------------------------------------------------
    total_passed  = sum(int(p.get("passed",  0)) for p in platforms)
    total_failed  = sum(int(p.get("failed",  0)) for p in platforms)
    total_skipped = sum(int(p.get("skipped", 0)) for p in platforms)
    total_total   = sum(int(p.get("total",   0)) for p in platforms)
    overall_ok    = (total_passed / total_total * 100 >= PASS_THRESHOLD) if total_total > 0 else False

    # ------------------------------------------------------------------
    # Build table rows (monospace, aligned)
    # ------------------------------------------------------------------
    col_w = {"pct": 11, "fail": 7, "skip": 8, "tot": 6, "st": 7, "rep": 9, "plat": 14}
    sep = "-" * 64

    header = (
        f"{'Passed(%)'.ljust(col_w['pct'])}"
        f"{'Failed'.ljust(col_w['fail'])}"
        f"{'Skipped'.ljust(col_w['skip'])}"
        f"{'Total'.ljust(col_w['tot'])}"
        f"{'Status'.ljust(col_w['st'])}"
        f"{'Reports'.ljust(col_w['rep'])}"
        f"Platform"
    )

    rows: list[str] = []
    for p in platforms:
        ps  = int(p.get("passed",  0))
        pf  = int(p.get("failed",  0))
        pk  = int(p.get("skipped", 0))
        pt  = int(p.get("total",   0))
        plat = p.get("platform", "unknown")
        icon = status_icon(ps, pt)
        allure_url = p.get("allureUrl", default_allure)
        passed_col = f"{ps} ({pct(ps, pt)})"

        # For Slack mrkdwn we use inline link for Reports column
        rows.append(
            f"{passed_col.ljust(col_w['pct'])}"
            f"{str(pf).ljust(col_w['fail'])}"
            f"{str(pk).ljust(col_w['skip'])}"
            f"{str(pt).ljust(col_w['tot'])}"
            f"{icon}      "          # status icon + padding
            f"<{allure_url}|Allure>  "
            f"{plat}"
        )

    if not rows:
        rows = ["No platform results were collected."]

    table_text = "\n".join([sep, header, sep] + rows + [sep])

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    footer_parts = []
    if duration:
        footer_parts.append(f"*Duration:* {duration}")
    build_label = f"Run #{run_number}" if run_number else f"Run {run_id}"
    footer_parts.append(f"<{build_url}|:arrow_forward: {build_label}>")
    artifact_url = f"{build_url}#artifacts" if run_id else build_url
    footer_parts.append(f"<{artifact_url}|:page_facing_up: Artifacts>")
    footer_text = "    ".join(footer_parts)

    # ------------------------------------------------------------------
    # Slack payload (Block Kit)
    # ------------------------------------------------------------------
    overall_icon = ":large_green_circle:" if overall_ok else ":red_circle:"
    build_label  = f"Build #{run_number}" if run_number else f"Run {run_id}"
    title = f"*[{env_name}] QoE — API Automation Tests  |  {build_label}*"

    payload = {
        "unfurl_links": False,
        "unfurl_media": False,
        "blocks": [
            # Title + overall verdict
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{title} {overall_icon}",
                },
            },
            # Metadata row
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Branch:* `{branch}`  |  "
                        f"*Test Type:* `{test_type}`  |  "
                        f"*Stage:* `{stage}`  |  "
                        f"*Commit:* `{sha}`"
                    ),
                },
            },
            {"type": "divider"},
            # Per-platform table (monospace block)
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```\n{table_text}\n```",
                },
            },
            {"type": "divider"},
            # Footer
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": footer_text},
            },
        ]
    }

    out_path = Path("api-slack-payload.json")
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
