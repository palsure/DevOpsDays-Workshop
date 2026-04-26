#!/usr/bin/env python3
"""Build a Slack Block Kit payload from acceptance-gate-manifest.json."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def icon(ok: bool) -> str:
    return ":large_green_circle:" if ok else ":red_circle:"


def main() -> int:
    manifest_path = Path(sys.argv[1] if len(sys.argv) > 1 else "acceptance-gate-manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Failed to read {manifest_path}: {e}", file=sys.stderr)
        return 1

    approved = bool(manifest.get("approved", False))
    rate = float(manifest.get("overallPassRatePercent", 0.0))
    threshold = float(manifest.get("gateThresholdPercent", 80.0))
    platforms = manifest.get("platforms", [])

    repo = os.environ.get("GITHUB_REPOSITORY", "repo")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    sha = (os.environ.get("GITHUB_SHA", "") or "unknown")[:7]
    branch = os.environ.get("GITHUB_REF_NAME", "unknown")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if run_id else f"https://github.com/{repo}"

    rows = []
    for p in platforms:
        total = int(p.get("total", 0))
        passed = int(p.get("passed", 0))
        failed = int(p.get("failed", 0))
        skipped = int(p.get("skipped", 0))
        pr = (100.0 * passed / total) if total > 0 else 0.0
        rows.append(
            f"*{p.get('platform', 'unknown')}*: {passed}/{total} passed ({pr:.1f}%)"
            f" · failed {failed} · skipped {skipped}"
        )
    if not rows:
        rows = ["No platform summaries were found."]

    verdict = "RELEASED" if approved else "BLOCKED"
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Build Acceptance Results* — {icon(approved)} *{verdict}*",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Overall pass rate:* {rate:.2f}%  |  *Gate:* {threshold:.0f}%\n"
                        f"*Repo:* `{repo}`  |  *Branch:* `{branch}`  |  *Commit:* `{sha}`\n"
                        f"*Run:* <{run_url}|GitHub Actions>"
                    ),
                },
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(f"• {r}" for r in rows)},
            },
        ]
    }

    Path("acceptance-slack-payload.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote acceptance-slack-payload.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
