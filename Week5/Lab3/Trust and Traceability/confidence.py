"""
confidence.py — Bucket findings into auto_clear / human_review / contested.

WHY THIS EXISTS
---------------
A single LLM finding with a confidence number is not enough for a
regulated workflow. Production systems do two things:

  1. Apply a CONFIDENCE THRESHOLD — anything below it routes to a human.
  2. Cross-check across MULTIPLE PASSES — agreement raises confidence,
     disagreement marks the finding as "contested" so a human looks at it.

This file does both, deterministically, with no model calls.
"""

# Above this confidence we trust a confirmed finding without human review.
CONFIDENCE_THRESHOLD = 0.75


def bucket(pass_a: list[dict], pass_b: list[dict]) -> dict:
    """
    Compare two independent review passes and split findings into buckets.

    Two findings are considered "the same finding" if they refer to the
    same line number. (For a more sophisticated system you could match on
    semantic similarity, but line-level agreement is a strong signal.)
    """
    by_line_a = {f["line"]: f for f in pass_a}
    by_line_b = {f["line"]: f for f in pass_b}

    all_lines = sorted(set(by_line_a) | set(by_line_b))

    auto_clear: list[dict] = []
    human_review: list[dict] = []
    contested: list[dict] = []

    for line in all_lines:
        a = by_line_a.get(line)
        b = by_line_b.get(line)

        if a and b:
            # Both passes flagged this line — it's confirmed.
            avg_conf = (a["confidence"] + b["confidence"]) / 2
            entry = {
                "line": line,
                "quote": a["quote"],
                "flag": a["flag"],
                "confidence": round(avg_conf, 2),
                "agreement": "confirmed",
            }
            if avg_conf >= CONFIDENCE_THRESHOLD:
                auto_clear.append(entry)
            else:
                human_review.append(entry)
        else:
            # Only one pass flagged it — that's a disagreement.
            present = a or b
            contested.append({
                "line": line,
                "quote": present["quote"],
                "flag_pass_a": a["flag"] if a else None,
                "flag_pass_b": b["flag"] if b else None,
                "agreement": "contested",
            })

    return {
        "auto_clear": auto_clear,
        "human_review": human_review,
        "contested": contested,
    }