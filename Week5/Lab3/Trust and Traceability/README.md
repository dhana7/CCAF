# Lab 5.3 — Trust & Traceability: Human Review, Confidence & Provenance

**CCA-F · Module 5 · Sections S5–S6 (Optional)**
**Scenario:** A command-line AI compliance reviewer for quarterly financial reports

## What this lab is about

Making every finding an AI compliance reviewer produces **trustworthy**
three separate ways:

1. **Confidence-based routing (S5)** — a numeric confidence score decides
   whether a finding can be auto-cleared or needs a human to look at it,
   using a fixed threshold.
2. **Provenance — never-hallucinated quotes (S6)** — every finding cites
   its exact source line, but the quoted text is always attached **locally**
   from the actual report data, never trusted from the model's own output —
   so a finding can never cite text that doesn't really exist in the
   report.
3. **Confirmed vs. contested findings (S5+S6)** — two independent review
   passes (different prompts, same report) are cross-checked: agreement on
   a line raises confidence and marks it "confirmed"; disagreement marks it
   "contested" and routes it to a human regardless of either pass's
   individual confidence score.

## My approach

- **`confidence.py`** — `bucket(pass_a, pass_b)` indexes both passes by line
  number, then for every line either pass flagged: if **both** passes
  flagged it, it's "confirmed" and gets averaged confidence, routed to
  `auto_clear` if that average is ≥ `CONFIDENCE_THRESHOLD` (0.75) or
  `human_review` otherwise; if **only one** pass flagged it, it's
  "contested" (a disagreement between the two independent reviews) and
  always routed to a separate `contested` bucket regardless of confidence.
  I verified this myself offline with synthetic data: a line flagged by
  both passes at high confidence correctly landed in `auto_clear`, while
  lines each pass flagged independently correctly landed in `contested`.
- **`reviewer.py`** — `_parse_json_array()` tolerantly strips markdown code
  fences before parsing, and returns an empty list (rather than crashing)
  on a genuine parse failure. `review()` runs one pass with either
  `PROMPT_STRICT` or `PROMPT_GENERAL` (two meaningfully different prompts,
  so the two passes are genuinely independent reviews, not just the same
  question asked twice), then — critically — **attaches the quote itself**
  from `get_quote(line)` using the model's reported line number, discarding
  any finding whose line number is out of range. The model never gets to
  supply its own quote text directly into a finding; the quote always
  comes from the real report data.
- **`main.py`** — runs both passes (`strict` and `general`) over the same
  report, then calls `bucket()` to split results into `auto_clear`,
  `human_review`, and `contested`, printing each bucket clearly labeled.

## Verified offline (no API key needed for this piece)

```
>>> pass_a = [{"line": 5, "quote": "Revenue grew 40%", "flag": "unverified claim", "confidence": 0.9}]
>>> pass_b = [{"line": 5, "quote": "Revenue grew 40%", "flag": "unverified claim", "confidence": 0.85}]
>>> bucket(pass_a, pass_b)
{'auto_clear': [{'line': 5, ..., 'confidence': 0.88, 'agreement': 'confirmed'}],
 'human_review': [],
 'contested': []}
```
Both passes agreeing on line 5 with high confidence correctly routed
straight to `auto_clear` with the averaged confidence score.

## Files

| File | Section | What was implemented |
|---|---|---|
| `confidence.py` | S5, S6 | `bucket()` — threshold routing + confirmed/contested cross-check. |
| `reviewer.py` | S6 | `_parse_json_array()` (tolerant parsing) + local quote attachment in `review()`. |
| `main.py` | — | Runs both passes and prints the bucketed results (provided scaffolding). |
| `sample_report.py` | — | Mock report + `get_quote`/`get_numbered_report` (provided scaffolding). |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # anthropic + python-dotenv
cp .env.example .env              # then paste your key into .env

python main.py
```

**Expected output:** two review passes run over the same mock report;
findings are printed grouped into three sections — `auto_clear` (both
passes agreed, high confidence), `human_review` (both passes agreed, but
confidence fell below the threshold), and `contested` (only one of the two
passes flagged that line). Every finding shown includes its exact quoted
source line, guaranteed to be real text from the report.

**Note:** findings have the shape `{line, quote, flag, confidence}` — the
`quote` field is always attached locally from `sample_report.py`, never
copied verbatim from the model's own output, by design.

See `REFLECTIONS.md` for further discussion questions and answers.
