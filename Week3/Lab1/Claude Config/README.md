# Lab 3.1 — Configuring Claude Code: CLAUDE.md Hierarchy, Commands & Skills

**CCA-F · Module 3 — Configuring & Customizing Claude Code**
**Scenario:** Setting up Claude Code for the NorthPeak pricing service

## What this lab is about

1. **CLAUDE.md hierarchy & `@import` (S1)** — project memory is kept short
   and modular: `CLAUDE.md` at the root `@import`s small rule files from
   `.claude/rules/`, and a user-level `~/.claude/CLAUDE.md` layers on top.
2. **Custom slash commands (S2)** — recurring chores (`/test`, `/review`)
   become one-word, versioned, shareable commands defined as Markdown files
   with YAML frontmatter in `.claude/commands/`.
3. **Skills (S2)** — a multi-step workflow (writing a changelog entry) is
   packaged as a skill Claude Code auto-invokes by matching the request
   against the skill's `description`, rather than being called by name.

## My approach

- **`CLAUDE.md`** stays a short table of contents that wires in
  `.claude/rules/style.md` and `.claude/rules/testing.md` via `@import`, so
  either file can be edited independently and picked up automatically.
- **`src/northpeak/pricing.py`** is the official starter library the lab
  operates on: `apply_member_discount(subtotal, is_member)` (flat 10% off
  for members), `shipping_cost(subtotal)` (free at/above
  `FREE_SHIPPING_THRESHOLD = 75.0`, otherwise a flat `STANDARD_SHIPPING =
  7.95`), and `order_total(subtotal, is_member=False)` (discount applied
  first, then shipping on the *discounted* subtotal). Money is float,
  rounded to 2 decimals at the boundary — per the root `CLAUDE.md`'s
  "Quick facts" and `.claude/rules/style.md`. `src/tests/test_pricing.py`
  is the starting green suite (`pytest -q` → 4 passed), matching the lab's
  environment check exactly.
- **`.claude/commands/test.md`** (`/test`) runs `pytest -q` with read-only
  tools and reports the result without ever editing code.
  **`.claude/commands/review.md`** (`/review`) runs `git diff` against a
  4-point checklist (tests, style, naming, scope) and reports
  blocker/suggestion/nit findings, also strictly read-only.
- **`.claude/skills/changelog/SKILL.md`** describes concrete trigger
  phrases ("update the changelog", "write release notes") so Claude Code
  reaches for it automatically, and defines the Keep-a-Changelog output
  format. `CHANGELOG.md` shows a worked example of what the skill produces
  for the pricing library.

## Files

| Path | Section | Purpose |
|---|---|---|
| `CLAUDE.md` | S1 | Root project memory; `@import`s the rule modules. |
| `.claude/rules/style.md`, `testing.md` | S1 | Modular style/testing rules. |
| `.claude/commands/test.md`, `review.md` | S2 | The `/test` and `/review` slash commands. |
| `.claude/skills/changelog/SKILL.md` | S2 | The changelog-entry skill. |
| `src/northpeak/pricing.py`, `src/tests/` | — | The pricing code and its green pytest suite. |
| `CHANGELOG.md` | S2 | Worked example of the changelog skill's output. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # pytest>=8.0.0
pytest -q                          # expect: 4 passed

claude   # start Claude Code FROM this folder so it finds CLAUDE.md and .claude/
```

Inside Claude Code:

```
/test
/review pricing.py
Update the changelog for this change.
```

To exercise the user-level memory layering (Ex 1, Step 3), add to
`~/.claude/CLAUDE.md`:

```
- Always explain a change in one sentence before editing files.
```

restart Claude Code, then ask it to add a small helper — it should explain
first (user rule), keep the function pure/validated (style.md), and add a
test (testing.md).

See `REFLECTIONS.md` for the exercise reflection answers.
