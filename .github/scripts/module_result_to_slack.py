#!/usr/bin/env python3
"""
Generate a Slack Block Kit payload for a single module build result.

Required env vars:
  MODULE_NAME          — display name, e.g. "API", "WEB", "ANDROID", "iOS", "Automation"
  STAGE1_NAME          — e.g. "Unit Tests"
  STAGE1_RESULT        — success | failure | skipped | cancelled
  STAGE2_NAME          — e.g. "E2E Tests" or "Build"
  STAGE2_RESULT        — success | failure | skipped | cancelled
  STAGE3_NAME          — optional third stage name
  STAGE3_RESULT        — optional third stage result
  GITHUB_REPOSITORY    — e.g. "org/repo"
  GITHUB_RUN_ID        — numeric run ID
  GITHUB_RUN_NUMBER    — sequential run number
  GITHUB_REF_NAME      — branch name
  GITHUB_SHA           — full commit SHA
  WORKFLOW_START_EPOCH — Unix timestamp when workflow started (for duration)

Output file: module-slack-payload.json
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


def result_icon(result: str) -> str:
    return {
        "success": ":large_green_circle:",
        "failure": ":red_circle:",
        "skipped": ":white_circle:",
        "cancelled": ":white_circle:",
    }.get(result.lower(), ":white_circle:")


def fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} sec"
    m, s = divmod(seconds, 60)
    return f"{m} min, {s:02d} sec"


def main() -> int:
    module  = os.environ.get("MODULE_NAME", "MODULE")
    s1_name = os.environ.get("STAGE1_NAME", "Unit Tests")
    s1_res  = os.environ.get("STAGE1_RESULT", "skipped")
    s2_name = os.environ.get("STAGE2_NAME", "Build / E2E")
    s2_res  = os.environ.get("STAGE2_RESULT", "skipped")
    s3_name = os.environ.get("STAGE3_NAME", "")
    s3_res  = os.environ.get("STAGE3_RESULT", "skipped")

    repo       = os.environ.get("GITHUB_REPOSITORY", "repo")
    run_id     = os.environ.get("GITHUB_RUN_ID", "")
    run_number = os.environ.get("GITHUB_RUN_NUMBER", "")
    sha_full   = os.environ.get("GITHUB_SHA", "unknown")
    sha        = sha_full[:7]
    branch     = os.environ.get("GITHUB_REF_NAME", "unknown")

    run_url    = (
        f"https://github.com/{repo}/actions/runs/{run_id}"
        if run_id else f"https://github.com/{repo}"
    )
    commit_url = f"https://github.com/{repo}/commit/{sha_full}"
    build_label = f"Build #{run_number}" if run_number else f"Run {run_id}"

    # Overall result — failure beats all, then cancelled, else success
    stage_results = [s1_res, s2_res] + ([s3_res] if s3_name else [])
    overall = "success"
    for r in stage_results:
        if r in ("failure", "cancelled"):
            overall = "failure"
            break

    verdict      = "PASSED" if overall == "success" else "FAILED"
    overall_icon = ":large_green_circle:" if overall == "success" else ":red_circle:"

    # Duration
    duration_str = ""
    start_epoch = os.environ.get("WORKFLOW_START_EPOCH", "")
    if start_epoch:
        try:
            elapsed = time.time() - float(start_epoch)
            duration_str = fmt_duration(elapsed)
        except ValueError:
            pass

    # Stage rows
    stage_rows = [
        f"{result_icon(s1_res)}  *{s1_name}:* {s1_res}",
        f"{result_icon(s2_res)}  *{s2_name}:* {s2_res}",
    ]
    if s3_name:
        stage_rows.append(f"{result_icon(s3_res)}  *{s3_name}:* {s3_res}")

    footer_parts = []
    if duration_str:
        footer_parts.append(f"*Duration:* {duration_str}")
    footer_parts.append(f"<{run_url}|:arrow_forward: View Run #{run_number or run_id}>")
    footer_text = "    ".join(footer_parts)

    payload = {
        "unfurl_links": False,
        "unfurl_media": False,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"[{module}] Build Results — {verdict}  |  {build_label}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{overall_icon}  "
                        f"*Branch:* `{branch}`  |  "
                        f"*Commit:* <{commit_url}|{sha}>"
                    ),
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(stage_rows)},
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": footer_text}],
            },
        ],
    }

    out = Path("module-slack-payload.json")
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
