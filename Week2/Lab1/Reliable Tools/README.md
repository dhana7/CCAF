# Lab 2.1 — Designing Reliable Tools: Interfaces, Errors & Selection Control

**CCA-F · Module 2 — Reliable Tool Use**
**Scenario:** AI customer-support agent for NorthPeak Outfitters (outdoor gear)

## What this lab is about

1. **Tool interfaces (S1)** — the model chooses a tool from its name,
   description, and parameter schema alone. A weak toolset (vague names,
   overlapping descriptions, loose params) misroutes; a strong toolset
   (object+action names, explicit "when NOT to use," typed/patterned
   params) routes reliably — with the *same* model.
2. **Structured errors & retries (S2)** — tools return an
   `isError`/`isRetryable` envelope instead of raising, so a retry loop can
   back off on transient failures (timeouts, 503s) and stop immediately on
   permanent ones (404, 400).
3. **Selection control with `tool_choice` (S3)** — `auto` / `any` / a
   forced single tool scope exactly what the model may do on a turn; a
   triage step that must always classify uses the forced mode.

## My approach

- **Ex 1 (`exercise_1_tool_interfaces.py`)** — `WEAK_TOOLS` uses `search` /
  `lookup` with a vague `q` parameter; `STRONG_TOOLS` uses
  `search_products` / `get_order_status`, each description explicitly
  deferring to the sibling tool, and `order_id` is typed with
  `"pattern": "^NP-[0-9]{6}$"`. A harness runs six `TEST_CASES` through
  both sets with `tool_choice={"type": "any"}` and scores OK/MISS per
  question.
- **Ex 2 (`exercise_2_structured_errors.py`)** — `call_order_tool()` wraps
  the mock Orders service and never raises: it always returns
  `{"isError": False, ...}` or
  `{"isError": True, "isRetryable": bool, "status": int, "error": str}`.
  `run_with_retry()` retries only while `isRetryable` is `True`, with
  exponential backoff (`0.2s → 0.4s → 0.8s`) and a hard 4-attempt cap. An
  offline `--check` mode proves the envelope shape before any API calls are
  made.
- **Ex 3 (`exercise_3_tool_choice.py`)** — the same four sample tickets are
  run under `{"type": "auto"}`, `{"type": "any"}`, and
  `{"type": "tool", "name": "classify_ticket"}` against a two-tool set
  (`classify_ticket` + `draft_customer_reply`) to make the drift between
  modes visible.

## Files

| File | Exercise | Purpose |
|---|---|---|
| `src/exercise_1_tool_interfaces.py` | Ex 1 | Weak vs. strong toolset + scoring harness. |
| `src/exercise_2_structured_errors.py` | Ex 2 | `isError`/`isRetryable` envelope + retry-with-backoff loop. |
| `src/exercise_3_tool_choice.py` | Ex 3 | `classify_ticket` + `draft_customer_reply` under `auto`/`any`/forced. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install "anthropic>=0.40.0"
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-sonnet-4-6   # optional; this is the default

cd src
python exercise_1_tool_interfaces.py
python exercise_2_structured_errors.py --check   # offline self-check, no API key needed
python exercise_2_structured_errors.py
python exercise_3_tool_choice.py
```

See `REFLECTIONS.md` for the exercise reflection answers.
