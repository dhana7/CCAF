# NorthPeak Refunds — Working Style

This repo holds the refunds service for NorthPeak Outfitters. A wrong refund
number is a real customer-facing bug, so every change ships behind a test and a
review.

## Test-driven by default
- New behaviour starts as a **failing test** that captures the spec.
- Loop: write-test -> run (red) -> implement -> run (green).
- Implement just enough to make the suite go green; do not gold-plate.

## Hard rule: never weaken a test to go green
- If a test fails, **fix the code**, not the test.
- Do not delete, comment out, loosen, or rewrite an assertion just to make the
  bar move. That replaces the spec with whatever the code happens to do.

## Backward compatibility
- New parameters land with safe defaults so existing callers keep working
  (e.g. `opened: bool = False`).

## Review
- The `/pr-review` command emits a strict `{decision, issues}` JSON object.
- CI runs Claude headless on every PR and gates on that verdict via
  `scripts/review_gate.py` (exit 0 = approve, exit 1 = request_changes).
