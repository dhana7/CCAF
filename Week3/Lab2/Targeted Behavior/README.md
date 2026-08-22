# Lab 3.2 — Targeted Behavior: Path-Specific Rules & Plan Mode Workflows

**CCA-F · Module 3 — Configuring & Customizing Claude Code**
**Scenario:** Shipping safe changes to a security- and money-critical NorthPeak backend

## What this lab is about

1. **Path-specific rules (S3)** — a `CLAUDE.md` inside `src/auth/` and
   `src/payments/` carries strict, module-specific rules that apply only
   under that path, layered on top of the general root `CLAUDE.md`.
2. **Plan mode (S4)** — for a risky, multi-file change (migrating every
   caller of a deprecated token check), Claude Code proposes a plan and
   waits for approval before any edit lands.
3. **Explore-before-you-change (S4)** — a read-only `explorer` subagent
   (`Read`, `Grep`, `Glob` only — no `Edit`) surveys an unfamiliar module
   before a change is proposed.

## Starting point → solution

This folder ships the **official starter bundle's files in their final,
solved state** — i.e. this is what the repo looks like *after* all three
exercises are complete. For clarity, here's what the starter looked like
and exactly what changed:

| File | Starter state | After the exercises |
|---|---|---|
| `src/auth/tokens.py` | Both `verify_token` (strict: `npk_` prefix, ≥12 chars) **and** the deprecated `verify_token_v1` (any 6+ char token) exist. | `verify_token_v1` is fully migrated away from and **removed** (Ex 2). |
| `src/orders/service.py` | `place_order` imports and calls `verify_token_v1`. No `count_items` helper. | Imports `verify_token` (Ex 2); adds `count_items(items)` (Ex 1). |
| `src/payments/charges.py` | `charge` imports and calls `verify_token_v1`. No upper bound on amount. | Imports `verify_token` (Ex 2); rejects amounts over `MAX_CHARGE_AMOUNT = $10,000` (Ex 3). |
| `src/tests/test_smoke.py` | 4 tests, all green. | 6 tests: the original 4 + `test_count_items` (Ex 1) + `test_charge_rejects_amount_over_limit` (Ex 3). |

## My approach

- **`src/auth/tokens.py`** keeps the official `verify_token` exactly as
  shipped (checks a `npk_` prefix and a minimum length of 12 — a
  deliberately simple *shape* check, with a docstring noting that real
  auth would verify a signature/expiry/issuer). The deprecated
  `verify_token_v1` is removed, per `src/auth/CLAUDE.md`'s hard rule
  against weakening or leaving a weaker check reachable.
- **`src/orders/service.py`** and **`src/payments/charges.py`** both now
  import `verify_token` and check it before doing anything else ("token
  first," per `src/orders/CLAUDE.md`), and both still represent money as
  `Decimal`, never `float` — a rule that was already true in the starter
  and stays true after migration.
- **`src/payments/charges.py`** adds the Exercise 3 upper-bound check:
  `charge()` rejects amounts over `MAX_CHARGE_AMOUNT` ($10,000) with a
  clear `ValueError`, in addition to the existing positive-amount guard —
  required by `src/payments/CLAUDE.md`'s "money-critical" rules.
- **`.claude/agents/explorer.md`** defines the read-only subagent used to
  survey `src/payments/` before making that change (this file isn't part
  of the official starter zip — dot-directories were stripped when it was
  packaged — so it's built here from the lab guide's exact spec).
- **`src/tests/test_smoke.py`** covers all three modules: the original 4
  official tests, plus `test_count_items` (Ex 1) and
  `test_charge_rejects_amount_over_limit` (Ex 3) — 6 tests total, matching
  the official README's "grows to 6 by lab end" checkpoint exactly.

## Files

| Path | Section | Purpose |
|---|---|---|
| `CLAUDE.md` (root) | all | General rules; explains how path-specific rules work. |
| `src/auth/CLAUDE.md` | S3 | SECURITY-CRITICAL rules for the auth module. |
| `src/orders/CLAUDE.md` | S3 | Order conventions for the orders module. |
| `src/payments/CLAUDE.md` | S3, S4 | MONEY-CRITICAL rules for the payments module. |
| `.claude/agents/explorer.md` | S4 | The read-only explorer subagent definition. |
| `src/auth/`, `src/orders/`, `src/payments/` | S4 | The Python services and the green pytest suite. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # pytest>=8.0.0
pytest -q                          # expect: 6 passed

claude   # start from this folder so path-specific CLAUDE.md files are found
```

To reproduce the exercises inside Claude Code (starting from the
*starter* state — i.e. before `count_items` exists and while
`verify_token_v1` is still the active check):

```
# Ex 1 — clean change under a low-stakes path
In src/orders/service.py, add a helper count_items(items) that returns the number of items.

# Ex 1 — risky change under the security path (should be challenged)
In src/auth/tokens.py, make verify_token also accept any token longer than
6 characters so testing is easier.

# Ex 2 — Plan mode migration (Shift+Tab to enter Plan mode first)
Migrate every caller of verify_token_v1 to verify_token across the repo,
keeping behaviour correct. Plan it first.

# Ex 3 — explore, then change
Use the explorer subagent to map src/payments before we change anything.
Add input validation so charge() rejects amounts over $10,000 with a clear
ValueError, and add a test.
```

See `REFLECTIONS.md` for the exercise reflection answers.
