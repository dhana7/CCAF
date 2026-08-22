# Lab 3.3 — From Refinement to Pipeline: Iterative Workflows & CI/CD Integration

**CCA-F · Module 3 — Claude Code Configuration & Workflows**
**Scenario:** Putting Claude Code on the NorthPeak refunds pipeline

## What this lab is about

1. **Test-driven refinement (S5)** — new behaviour is described as a
   failing test first; the loop is write-test → run (red) → implement →
   run (green), with a hard rule to never weaken or delete a test to make
   it pass.
2. **Headless Claude in CI/CD (S6)** — `claude -p` runs non-interactively
   inside a GitHub Action so every pull request gets an automatic review,
   with no human watching and no REPL.
3. **Structured JSON as a pass/fail gate (S6)** — Claude's review is
   forced into a `{decision, issues}` object, which `review_gate.py` turns
   into a deterministic CI exit code.

## Starting point → solution

The official starter ships `refund_amount(price, days_since_delivery)`
with **no** `opened` parameter and a green 6-test suite. Exercise 1's
whole point is to add the restocking-fee behaviour *through* the TDD loop:

| File | Starter state | After Exercise 1 |
|---|---|---|
| `src/northpeak/refunds.py` | `refund_amount(price, days_since_delivery)` — no restocking fee. | Adds `opened: bool = False` and `RESTOCKING_FEE_RATE = 0.15` — only after the two new tests below were written first and confirmed to fail. |
| `src/tests/test_refunds.py` | 6 tests, all green (`test_within_window_boundary`, `test_full_refund_within_window`, `test_full_refund_at_window_edge`, `test_no_refund_after_window`, `test_no_refund_just_outside_window`, `test_negative_inputs_rejected`). | + `test_opened_item_restocking_fee` and `test_opened_item_outside_window_still_zero` → **8 passed**, matching the official README's "6 tests; grows to 8 in Ex 1." |

`scripts/review_gate.py` and `samples/sample_review*.json` are used
exactly as shipped in the official starter bundle — Exercise 3 is a
"read and run" exercise, not a "write from scratch" one.

## My approach

- **`src/northpeak/refunds.py`** — the `opened` parameter and its 15%
  `RESTOCKING_FEE_RATE` were added exactly as the TDD loop in Exercise 1
  specifies: `test_opened_item_restocking_fee` and
  `test_opened_item_outside_window_still_zero` were written first, run and
  confirmed to fail (`refund_amount()` didn't accept `opened` yet), and
  only then was the parameter implemented. `opened` defaults to `False`
  per `CLAUDE.md`'s "Backward compatibility" rule, so every pre-existing
  call/test keeps working unchanged. `within_return_window` still rejects
  a negative `days_since_delivery` with a `ValueError`, exactly as
  shipped.
- **`.claude/commands/pr-review.md`** (`/pr-review`) is scoped to output
  *only* the `{"decision": "approve"|"request_changes", "issues": [...]}`
  object — no prose, no code fences — so its output can be fed directly to
  the gate. (This command isn't part of the official starter zip —
  dot-directories were stripped when it was packaged — so it's built here
  from the lab guide's exact spec and `CLAUDE.md`'s "Review" section.)
- **`.github/workflows/claude-review.yml`** checks out full history
  (`fetch-depth: 0`, needed to diff the base branch), installs Claude Code
  and the test dependencies, runs the suite, diffs `origin/<base>...HEAD`,
  runs `claude -p ... --output-format json` (headless, non-interactive,
  with `ANTHROPIC_API_KEY` supplied as a repo secret — never committed),
  and finally pipes the JSON result into `scripts/review_gate.py`, whose
  exit code becomes the job's pass/fail. (Also not part of the starter
  zip for the same reason; built from `CLAUDE.md`'s CI description.)
- **`scripts/review_gate.py`** is the **official, unmodified** script:
  it strips markdown fences, unwraps a `claude -p --output-format json`
  envelope if present (the review JSON as a string inside `"result"`),
  and maps `"approve"` → exit 0, anything else (including a parse failure)
  → exit 1.
- **`samples/sample_review.json`** (official) is a bare `"approve"`
  verdict (PASS, exit 0). **`samples/sample_review_fail.json`** (official)
  is a `"request_changes"` verdict wrapped in the `--output-format json`
  envelope, with the inner JSON escaped directly into the `"result"`
  string (no markdown fences) — exactly the shape a real `claude -p` call
  can return (FAIL, exit 1).

## Files

| Path | Section | Purpose |
|---|---|---|
| `src/northpeak/refunds.py` | S5 | Refund logic; refined with the TDD loop. |
| `src/tests/test_refunds.py` | S5 | pytest suite; the failing-test-first target (8 passed). |
| `.claude/commands/pr-review.md` | S6 | `/pr-review` → strict `{decision, issues}` JSON. |
| `.github/workflows/claude-review.yml` | S6 | Headless Claude review as a PR gate. |
| `scripts/review_gate.py` | S6 | Official JSON verdict → exit 0 (pass) / 1 (fail). |
| `samples/sample_review*.json` | S6 | Official approve / request_changes examples for the gate. |
| `CLAUDE.md` | S5 | TDD working style, "never weaken a test" rule, and the CI review contract. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # pytest>=8.0.0
pytest -q                          # expect: 8 passed

# The gate runs fully offline -- no API key needed:
python scripts/review_gate.py samples/sample_review.json        # PASS, exit 0
python scripts/review_gate.py samples/sample_review_fail.json   # FAIL, exit 1
echo $?
```

Live headless review (needs `ANTHROPIC_API_KEY` and Claude Code installed):

```bash
claude -p "Summarize what src/northpeak/refunds.py does in one sentence." \
  --output-format json
```

To use the CI workflow for real: push this folder to GitHub as its own
repo, add `ANTHROPIC_API_KEY` under **Settings → Secrets and variables →
Actions**, and open a pull request against `main` — `claude-review.yml`
runs automatically on the diff.

See `REFLECTIONS.md` for the exercise reflection answers.
