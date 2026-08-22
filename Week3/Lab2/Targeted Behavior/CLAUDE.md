# CLAUDE.md

Project memory for the **NorthPeak Outfitters** services monorepo.

## Overview

Three modules under `src/`: `auth/` (token verification), `orders/` (order
placement), and `payments/` (charges). Tests are in `src/tests/` and run with
`pytest`.

## How rules are targeted

This repo keeps **path-specific rules** in a `CLAUDE.md` inside each module. When
you work on a file, Claude Code applies the rules for that path. The strictest
rules live in `src/auth/` and `src/payments/` because they touch security and
money. General rules below apply everywhere.

## General rules

- Python 3.10+, clear over clever.
- Every behaviour change ships with a test; run `pytest -q` before finishing.
- Validate inputs early; raise `ValueError`/`PermissionError` with clear messages.