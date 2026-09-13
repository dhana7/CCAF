# Lab 4.2 — Enforcing Structure: tool_use Schemas with Validation & Retry

**CCA-F · Module 4 · Sections S3–S4**
**Scenario:** A recruiting candidate-screening evaluator

## What this lab is about

Making a `{name, recommendation, score, reason}` object **guaranteed valid**
every time — not "usually valid JSON," but structurally and semantically
correct on every single call:

1. **Tool schemas as structure (S3)** — defining the target record *as* a
   tool's `input_schema` and forcing `tool_choice`, so the model's tool
   arguments **are** the structured object — no markdown fences, no stray
   preambles, no parsing required.
2. **Semantic validation (S4)** — a JSON Schema can enforce syntax ("score is
   an integer 0–10") but cannot enforce cross-field business policy ("a
   `strong_hire` must score ≥ 8"). That lives in a `validate()` function.
3. **Retry-and-feedback loop (S4)** — when validation fails, the failure is
   fed back to the model as a `tool_result` with `is_error=True`, so it can
   self-correct, capped at a fixed number of attempts.

## My approach

- **`exercise_1_tool_schema.py`** — `EVALUATE_TOOL`'s `input_schema` fully
  describes all four fields: `name` (string), `recommendation` (string,
  `enum: [strong_hire, hire, no_hire]`), `score` (integer, `minimum: 0`,
  `maximum: 10`), `reason` (string) — all four listed in `required`. Because
  the call also forces `tool_choice={"type": "tool", "name":
  "record_evaluation"}`, the API itself rejects any tool call that doesn't
  match this schema, which is what actually guarantees the shape (not
  hoping the model formats its output correctly).
- **`exercise_2_validation.py`** — `validate(payload)` returns `(ok, errors)`
  and never raises. It checks each field's type/range/enum individually,
  explicitly excludes booleans from the integer check (`isinstance(True,
  int)` is `True` in Python — a real trap), and then applies the two
  cross-field policy rules a JSON Schema alone cannot express:
  `strong_hire ⇒ score ≥ 8` and `no_hire ⇒ score ≤ 4`. Verified offline with
  `python exercise_2_validation.py --check` — a good payload passes, a
  malformed payload and a cross-field violation both correctly fail.
- **`exercise_3_retry_loop.py`** — `assess_with_retry()` loops up to
  `max_attempts` times: calls the model with the forced tool, validates the
  result, and on failure appends the assistant's own tool call *and* a
  `tool_result` block with `is_error=True` describing exactly what was
  wrong — echoing the same `tool_use_id` the assistant just used, which the
  API requires. This lets the model see its own mistake and correct it on
  the next attempt, rather than the caller silently discarding a bad
  response. Verified offline with `python exercise_3_retry_loop.py --demo`,
  which simulates a rejected `strong_hire, score=5` attempt followed by an
  accepted `strong_hire, score=9` attempt.

## Files

| File | Section | What was implemented |
|---|---|---|
| `exercise_1_tool_schema.py` | S3 | `EVALUATE_TOOL.input_schema` — full JSON Schema for all four fields. |
| `exercise_2_validation.py` | S4 | `validate(payload)` — type/enum/range checks + cross-field policy. |
| `exercise_3_retry_loop.py` | S4 | `assess_with_retry()` — the retry-and-feedback loop, capped attempts. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # anthropic>=0.40.0
export ANTHROPIC_API_KEY=sk-ant-...

# Offline first — no API key needed for these:
python exercise_2_validation.py --check
python exercise_3_retry_loop.py --demo

# Then live:
python exercise_1_tool_schema.py
python exercise_2_validation.py
python exercise_3_retry_loop.py
```

**Verified offline output** (I ran both of these myself):
```
$ python exercise_2_validation.py --check
offline validation check passed
bad -> ['name must be a non-empty string', "recommendation must be one of [...]", 'score must be an integer 0..10']
cross -> ["a 'strong_hire' must score >= 8"]

$ python exercise_3_retry_loop.py --demo
attempt 1: {"name": "Alex Park", "recommendation": "strong_hire", "score": 5, ...}
  -> invalid: ["a 'strong_hire' must score >= 8"]
  -> feedback to model: 'Validation failed: ...'
attempt 2: {"name": "Alex Park", "recommendation": "strong_hire", "score": 9, ...}
  -> valid, stop
```

See `REFLECTIONS.md` for further discussion questions and answers.
