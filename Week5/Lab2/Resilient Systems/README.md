# Lab 5.2 — Resilient Systems: Error Propagation & Large Codebase Exploration

**CCA-F · Module 5 · Sections S3–S4**
**Scenario:** A healthcare-claims pipeline (intake → validation → adjudication)

## What this lab is about

Three resilience techniques so a long batch of claims **fails loudly** (not
silently), **writes everything to disk as it goes** (so nothing is lost),
and **survives a crash without redoing finished work**:

1. **Error propagation via an envelope (S3)** — every subagent returns a
   `StageResult` (`stage`, `ok`, `data`, `error`) and never raises into the
   coordinator. Failures become first-class data the coordinator can react
   to, not exceptions that crash the whole batch.
2. **The disk-backed scratchpad (S4)** — every mutation (a log entry, a
   status change) is flushed to a JSON file immediately, so the pipeline's
   state exists outside of process memory at all times.
3. **Crash recovery (S4)** — on restart, the pipeline checks each claim's
   persisted status and skips anything already `done` or `failed`,
   processing only what's still outstanding.

## My approach

- **`agents.py`** — `StageResult` is a small dataclass with a `to_dict()`
  helper. `run_intake()` calls Claude to extract structured fields from the
  claim narrative, tolerantly strips markdown fences if present, and wraps
  *any* exception (parse failure, API error) in a `try/except` so it always
  returns a `StageResult(ok=False, error=...)` rather than raising.
  `run_validation()` and `run_adjudication()` are deterministic business
  rules (active-member check, covered-procedure check, amount-based
  approve/hold/deny) — kept rule-based rather than LLM-based so the lab
  doesn't burn tokens on logic that doesn't need a model.
- **`scratchpad.py`** — `Scratchpad` loads its JSON file on init (tolerating
  a corrupted file by starting fresh rather than crashing), and every
  mutating method (`log`, `mark_done`, `mark_failed`) calls `_flush()`
  immediately afterward, writing the full state back to disk. I verified
  this myself: after marking one claim `done` and one `failed`, creating a
  **brand-new** `Scratchpad` instance pointed at the same file (simulating
  a process restart) correctly reported the same statuses back — proving
  state genuinely survives a crash, not just an in-memory session.
- **`main.py`** — `process_claim()` walks the three stages in order,
  logging each `StageResult` to the scratchpad as it goes and marking the
  claim `done` or `failed` at the end. The coordinator loop checks
  `scratchpad.status(claim_id)` before processing each claim and skips
  anything already `done`/`failed` — so re-running `python main.py` after
  an interruption picks up only unfinished claims instead of reprocessing
  everything from scratch.

## Verified offline (no API key needed for this piece)

```
>>> sp = Scratchpad(path="test.json")
>>> sp.log("claim-001", "intake", {"summary": "auto accident claim"})
>>> sp.mark_done("claim-001")
>>> sp.mark_failed("claim-002", "policy not found")
>>> sp.status("claim-001"), sp.status("claim-002"), sp.status("claim-003")
('done', 'failed', 'new')

# Simulating a crash/restart with a brand-new instance reading the same file:
>>> sp2 = Scratchpad(path="test.json")
>>> sp2.status("claim-001")
'done'   # <- correctly recovered without re-running claim-001
```

## Files

| File | Section | What was implemented |
|---|---|---|
| `agents.py` | S3 | `StageResult` envelope + `run_intake`/`run_validation`/`run_adjudication`. |
| `scratchpad.py` | S4 | `log`, `mark_done`, `mark_failed`, `_flush` — disk-backed persistence. |
| `main.py` | S4 | `process_claim()` + the skip-if-already-processed recovery rule. |
| `sample_claims.py` | — | Mock claims + covered-procedures data (provided scaffolding). |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # anthropic + python-dotenv
cp .env.example .env              # then paste your key into .env

python main.py                    # run once
python main.py                    # run again — watch it skip already-done claims
```

**Expected output:** each claim moves through intake → validation →
adjudication, with each stage's result logged. On a second run, claims that
finished successfully (or failed permanently) the first time are skipped
entirely — you should see a message like "already processed, skipping" for
those, with only genuinely unfinished claims reprocessed. State persists in
`scratchpad.json`; delete that file by hand to reset (the lab never deletes
it automatically, by design — that's your manual reset switch).

See `REFLECTIONS.md` for further discussion questions and answers.
