#!/usr/bin/env python3
"""review_gate.py - turn a Claude review (JSON) into a CI pass/fail.

Reads JSON on stdin (or a file path arg) and exits 0 to PASS or 1 to FAIL,
printing a short summary. Accepts two shapes:
  1. the review object: {"decision": ..., "issues": [...]}
  2. the `claude -p --output-format json` envelope, where the review object is a
     JSON string in the top-level "result" field (unwrapped automatically).
"""

from __future__ import annotations

import json
import sys


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def extract_review(raw: str) -> dict:
    data = json.loads(_strip_fences(raw))
    if isinstance(data, dict) and "decision" not in data and "result" in data:
        data = json.loads(_strip_fences(str(data["result"])))
    if not isinstance(data, dict) or "decision" not in data:
        raise ValueError("Could not find a 'decision' field in the input.")
    return data


def main() -> int:
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    try:
        review = extract_review(raw)
    except (json.JSONDecodeError, ValueError) as err:
        print(f"review-gate: could not parse review JSON: {err}")
        return 1

    decision = str(review.get("decision", "")).lower()
    issues = review.get("issues", []) or []
    print(f"review-gate: decision = {decision!r}, {len(issues)} issue(s)")
    for issue in issues:
        print(f"  - [{issue.get('severity','info')}] {issue.get('message','')}")
    if decision == "approve":
        print("review-gate: PASS")
        return 0
    print("review-gate: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())