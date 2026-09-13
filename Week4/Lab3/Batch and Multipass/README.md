# Lab 4.3 — Scaling Output: Batch Processing & Multi-Pass Review

**CCA-F · Module 4 · Sections S5–S6**
**Scenario:** A news/media-monitoring pipeline for "Helix Robotics" coverage

## What this lab is about

Three different patterns for scaling Claude output beyond a single
request-response call, each suited to a different shape of workload:

1. **The Message Batches API (S5)** — for large, non-urgent, overnight-style
   workloads: submit many requests at once, let them process asynchronously,
   and collect results later by a stable `custom_id`. Trades latency for
   cost/scale.
2. **Parallel processing with a thread pool (S6)** — for a smaller,
   time-sensitive burst (like breaking news): since waiting on the API is
   I/O-bound, a `ThreadPoolExecutor` overlaps those waits so a batch of
   requests finishes in roughly the time of the *slowest* one, not the
   *sum* of all of them.
3. **Multi-pass review — draft → critique → refine (S6)** — for output
   *quality* rather than throughput: separating "generate" from "judge"
   catches issues (imbalance, vagueness, missing figures) a single pass
   tends to gloss over, and gives the refine step a concrete checklist to
   act on instead of vaguely "trying to do better."

## My approach

- **`exercise_1_message_batches.py`** — `build_requests()` returns one
  `{custom_id, params}` dict per headline, with `custom_id` built from
  `enumerate()` (`f"headline-{i}"`) so results can be joined back to their
  input reliably regardless of processing order. The polling loop in
  `main()` retrieves the batch, prints its `processing_status` and
  `request_counts`, breaks once status is `"ended"`, and — critically —
  has a fail-safe: if a 10-minute deadline passes before the batch ends, it
  prints a `--fetch <batch_id>` hint and returns cleanly instead of hanging
  or losing track of the batch, since batch processing continues on
  Anthropic's side even if this script stops watching it.
- **`exercise_2_parallel.py`** — `run_parallel()` uses
  `ThreadPoolExecutor(max_workers=workers)` with `pool.map()`, which
  preserves input order automatically (no manual result-tagging needed,
  unlike the batch API's `custom_id` approach) since `map()` returns
  results in the same order as the inputs it was given. The script prints
  a direct sequential-vs-parallel wall-clock comparison and computed
  speedup.
- **`exercise_3_multipass.py`** — `critique()` builds a prompt combining the
  editorial `STANDARDS`, the original headlines, and the draft, explicitly
  instructing the model to **list problems only, never rewrite** — keeping
  this step to judging-only is what gives `refine()` a concrete, actionable
  checklist rather than a vague "make it better." `refine()` then combines
  the standards, headlines, draft, *and* critique, instructing the model to
  fix every listed point and output only the final briefing text (no
  meta-commentary).

## Files

| File | Section | What was implemented |
|---|---|---|
| `exercise_1_message_batches.py` | S5 | `build_requests()` + the polling loop with a fail-safe deadline. |
| `exercise_2_parallel.py` | S6 | `run_parallel()` — `ThreadPoolExecutor`, order-preserving. |
| `exercise_3_multipass.py` | S6 | `critique()` (list-only) and `refine()` (fix-every-point). |

## How to run

**Important: all three exercises make real, live API calls — there is no offline mode for this lab.**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # anthropic>=0.40.0
export ANTHROPIC_API_KEY=sk-ant-...

python exercise_1_message_batches.py
# If it times out waiting (batches can take a while), fetch later with:
#   python exercise_1_message_batches.py --fetch <batch_id>

python exercise_2_parallel.py
python exercise_3_multipass.py
```

**Expected outcome pattern:**
- Exercise 1: 8 headlines submitted as one batch; final output lists each
  `custom_id` with its sentiment classification (`positive`/`neutral`/`negative`).
- Exercise 2: a `Sequential: X.Xs` line followed by a `Parallel: Y.Ys` line
  where Y is meaningfully smaller than X, and a computed `Speedup: Nx`
  (with `workers=5`, expect roughly 3–5x on this 8-headline batch, though
  exact speedup varies with API latency at the time you run it).
- Exercise 3: three clearly distinct sections — `DRAFT`, `CRITIQUE` (a
  bullet list of specific issues, no rewritten text), and `REFINED` (a
  tightened briefing that addresses the critique's points and fits the
  120-word standard).

See `REFLECTIONS.md` for further discussion questions and answers.
