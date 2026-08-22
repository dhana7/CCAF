# CLAUDE.md

Project memory for the **NorthPeak Outfitters** pricing service. Claude Code
loads this file automatically when you work in this folder.

## Project overview

A small Python library for order pricing (member discounts, shipping, totals).
Source lives in `src/northpeak/`; tests in `src/tests/` run with `pytest`.

## How this file is organized

Instead of one giant file, the team keeps rules modular and pulls them in with
`@import`. Edit the small rule files in `.claude/rules/`; this file just wires
them together.

@.claude/rules/style.md
@.claude/rules/testing.md

## Quick facts

- Run tests with `pytest` from the project root (config is in `pytest.ini`).
- Public functions live in `src/northpeak/`; keep them pure and easy to test.
- Money is handled in float USD and rounded to 2 decimals at the boundaries.