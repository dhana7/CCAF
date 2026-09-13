# Lab 4.1 — Precision Prompting: Explicit Criteria & Few-Shot Consistency

**CCA-F · Module 4 · Sections S1–S2**
**Scenario:** A Trust & Safety triage classifier (REMOVE / REVIEW / ALLOW)

## What this lab is about

Making a classifier precise using **prompting alone** — no fine-tuning, no
extra tooling. Three self-contained scripts, each starts from a working
baseline and asks you to fill in exactly one prompt-engineering technique:

1. **Explicit, testable criteria (S1)** — replacing a vague instruction with
   narrow, literal definitions of each action, so REMOVE stops over-firing on
   things that are merely rude or unpopular.
2. **Few-shot examples (S2)** — demonstrating the exact output *format*
   (`ACTION | rationale`) instead of just describing it in prose, so the
   model's output shape becomes consistent and parseable.
3. **Principles for generalization (S2)** — a short statement of *intent*
   behind the categories, so edge cases the examples never showed (public vs.
   private information, "just a joke" doxxing, playful threats) still route
   correctly.

## My approach

- **`exercise_1_explicit_criteria.py`** — `EXPLICIT_PROMPT` defines REMOVE
  narrowly ("no reasonable doubt": doxxing, credible named threats, clearly
  illegal content only), REVIEW as "needs a human" (spam, borderline
  harassment, ambiguous threats), and ALLOW as "rude/blunt/off-topic but not a
  violation" — plus an explicit tie-break rule (when unsure, choose REVIEW,
  never REMOVE). This is compared against the intentionally vague
  `VAGUE_PROMPT` baseline on 8 labeled reports, tracking both overall accuracy
  and — the failure that actually matters — the count of wrongful "remove"
  calls.
- **`exercise_2_few_shot.py`** — `FEW_SHOT_EXAMPLES` provides one worked
  example per action (REMOVE, ALLOW, REVIEW), each in the exact
  `ACTION | rationale` target shape, so the model pattern-matches the
  casing and separator instead of guessing at a format only described in
  prose. Scored against a strict regex (`^(REMOVE|REVIEW|ALLOW) \| .+`) on 4
  new reports, compared against a zero-shot baseline that describes the
  format but never demonstrates it.
- **`exercise_3_generalization.py`** — `PRINCIPLES` states the *intent* behind
  each category in a few bullet lines (public/official info isn't doxxing;
  stated "joking" intent doesn't excuse doxxing or a credible threat;
  tie-break toward REVIEW) so that 4 edge cases — deliberately chosen so a
  naive keyword read gets them wrong — still route correctly even though the
  fixed few-shot examples never showed anything like them.

## Files

| File | Section | What was implemented |
|---|---|---|
| `exercise_1_explicit_criteria.py` | S1 | `EXPLICIT_PROMPT` — narrow, testable definitions + tie-break rule. |
| `exercise_2_few_shot.py` | S2 | `FEW_SHOT_EXAMPLES` — one worked example per action, exact target format. |
| `exercise_3_generalization.py` | S2 | `PRINCIPLES` — a short statement of intent so unseen edge cases generalize. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # anthropic>=0.40.0
export ANTHROPIC_API_KEY=sk-ant-...

python exercise_1_explicit_criteria.py
python exercise_2_few_shot.py
python exercise_3_generalization.py
```

**Expected outcome pattern** (exact model output varies run to run, since
LLM sampling isn't perfectly deterministic — see the note below):
- Exercise 1: the EXPLICIT prompt should show fewer (ideally zero) wrongful
  "remove" calls than the VAGUE baseline.
- Exercise 2: FEW-SHOT should match the strict format on more of the 4
  reports than ZERO-SHOT.
- Exercise 3: with PRINCIPLES in place, most/all of the 4 edge cases should
  route to their `expected` action despite surface features that would
  mislead a naive reading.

**A note on run-to-run variation:** because LLM outputs involve some
sampling randomness, a single run isn't guaranteed to show the full effect
every time — a strong model can sometimes get borderline cases right even
with a weaker prompt. Running each script two or three times and comparing
is a more reliable way to see the pattern than trusting any single run.

See `REFLECTIONS.md` for further discussion questions and answers.
