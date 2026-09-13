# Lab 5.1 — Managing Context: Preservation, Optimization & Escalation

**CCA-F · Module 5 · Sections S1–S2**
**Scenario:** An e-commerce support agent handling customer C-1001 (Aarti Sharma)

## What this lab is about

Building three production context-management techniques into one agent, so
the same code behaves correctly whether it's turn 3 of a conversation or
turn 30:

1. **Preservation (S1)** — a `[CASE FACTS]` block, pinned into the system
   prompt on every single turn, so confirmed facts (customer ID, tier) are
   never re-asked for or lost as the conversation grows.
2. **Optimization (S1)** — bulky tool outputs are trimmed down to a
   per-tool whitelist of relevant fields *before* they ever reach the
   model, so the context window doesn't fill up with data nobody asked
   for.
3. **Escalation on ambiguity (S2)** — the agent is instructed to ask a
   clarifying question rather than guess when a request is genuinely
   ambiguous (e.g. "cancel my order" when the customer has multiple open
   orders).

## My approach

- **`case_facts.py`** — `CaseFacts.as_system_block()` renders every pinned
  fact as a `[CASE FACTS - these are confirmed and must be preserved]`
  block, one line per fact. `set()`/`get()` are simple dict operations. The
  block is deliberately short — every token here is paid for on every
  single API call for the rest of the conversation, so it holds only
  confirmed, load-bearing facts (customer ID, tier), not general
  conversation history.
- **`tool_optimizer.py`** — `optimize(tool_name, raw_result)` looks up the
  tool's whitelist in `RELEVANT_FIELDS`, and rebuilds the result (whether
  it's a list of records or a single dict) keeping only whitelisted keys.
  Unknown tools pass through untouched. I verified this myself offline: a
  raw order record with a large `tracking_full_history` field gets trimmed
  down to just `order_id`, `status`, `placed_on`, `total` when run through
  `optimize("lookup_orders", raw)`.
- **`main.py`** — `SYSTEM_BASE` instructs the agent to ask a clarifying
  question on ambiguity instead of guessing, and to treat the `[CASE
  FACTS]` block as authoritative (never re-ask for something already
  pinned). `chat()` assembles the system prompt from `SYSTEM_BASE` plus
  the current `facts.as_system_block()` on every turn, and every tool
  result is passed through `optimize()` before being sent back to the
  model. Three demos exercise each idea end to end: facts surviving 4
  turns of unrelated small talk, a side-by-side raw-vs-optimized tool
  output comparison, and an ambiguous cancel request that should trigger a
  clarifying question rather than a guess.

## Verified offline (no API key needed for these two pieces)

```
>>> optimize("lookup_orders", [{"order_id": "C-1001-A", "status": "shipped",
...            "placed_on": "2026-01-01", "total": 89.99,
...            "tracking_full_history": "huge blob..." * 20}])
[{'order_id': 'C-1001-A', 'status': 'shipped', 'placed_on': '2026-01-01', 'total': 89.99}]

>>> cf = CaseFacts(); cf.set("customer_id", "C-1001")
>>> cf.as_system_block()
[CASE FACTS - these are confirmed and must be preserved]
- customer_id: C-1001
```
Both ran exactly as designed — the bulky field was correctly dropped, and
the facts block rendered correctly.

## Files

| File | Section | What was implemented |
|---|---|---|
| `case_facts.py` | S1 | `as_system_block()` — renders pinned facts for the system prompt. |
| `tool_optimizer.py` | S1 | `optimize()` — trims tool output to a per-tool whitelist. |
| `main.py` | S2 | `SYSTEM_BASE` — the ask-on-ambiguity + case-facts-authoritative rules. |
| `sample_data.py` | — | Mock customer/order data (provided scaffolding). |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # anthropic + python-dotenv
cp .env.example .env              # then paste your key into .env

python main.py
```

**Expected output:** three labeled demos run in sequence — Demo 1 shows the
agent correctly recalling the customer's ID and tier at turn 4 without
re-asking; Demo 2 prints the raw tool output side-by-side with the trimmed
version, then shows the agent using the trimmed data normally; Demo 3 shows
the agent asking *which* order to cancel instead of guessing, since the
customer has multiple open orders.

See `REFLECTIONS.md` for further discussion questions and answers.
