# Lab 1.2 — Controlling Execution: Hooks, Decomposition & Session State

**CCA-F · Module 1 — Agentic Architecture & Orchestration**
**Scenario:** AI SOC Copilot for NorthGate Capital (financial services)

## What this lab is about

1. **PostToolUse hooks (S5)** — deterministic Python functions that run
   *between* the model's decision and the actual side-effect, so a dangerous
   tool call can be logged, validated, or blocked before it ever executes.
2. **Fixed vs. adaptive decomposition (S6)** — a hard-coded 3-step pipeline
   for work whose shape never changes (the morning threat-intel digest) vs.
   a classify-then-branch router for work whose shape depends on the input
   (alert triage).
3. **Session state (S7)** — `save` / `resume` / `fork` / `summarize`
   primitives so a multi-day SOC investigation survives shift changes, can
   split into parallel hypotheses, and stays small as it grows.

## My approach

- **Ex 1 (`tool_hooks.py`, `agent_with_hooks.py`)** — `run_tool()` pushes
  every call through `logging_hook` → `arg_validation_hook` →
  `protected_asset_hook` in order; the first `False` short-circuits the real
  tool and records a `BLOCKED` entry in the audit log. `agent_with_hooks.py`
  reuses the Lab 1.1 `stop_reason` loop, routing every `tool_use` block
  through `run_tool()` instead of calling the tool directly, and is driven
  with a task that contains a deliberate trap (an extra request to
  quarantine `trading-prod-01`) to prove the hook — not the prompt — is what
  stops it.
- **Ex 2 (`decompose.py`)** — `run_fixed_intel_digest()` runs three
  hard-coded steps (extract IoCs → enrich against the asset inventory →
  write an exec brief) every time. `run_adaptive_triage()` classifies the
  alert into one of six fixed branches with `classify_alert()`, then
  dispatches to the matching specialist prompt in `TRIAGE_BRANCHES` —
  falling back to `false_positive` (the safe default) for an unrecognized
  label.
- **Ex 3 (`session_manager.py`)** — a session is a plain
  `{id, parent_id, messages, summary}` dict, serialized to JSON under
  `./sessions/`. `fork_session()` copies `parent["messages"]` with
  `list(...)` (never aliases the reference — the single most common bug in
  this exercise). `summarize_session()` calls Haiku with a strict
  `DECISIONS: / FACTS: / OPEN:` format and an explicit instruction to never
  drop concrete values (IPs, hostnames, hashes, legal-hold IDs).

## Files

| File | Exercise | Purpose |
|---|---|---|
| `src/tool_hooks.py` | Ex 1 | Hook engine: log / validate / block, pure Python, no API. |
| `src/agent_with_hooks.py` | Ex 1 | Live agentic loop with hooks wired in. |
| `src/decompose.py` | Ex 2 | Fixed intel digest + adaptive alert-triage router. |
| `src/session_manager.py` | Ex 3 | `new_session`, `save_session`, `resume_session`, `fork_session`, `summarize_session`. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install "anthropic>=0.40.0"
export ANTHROPIC_API_KEY=sk-ant-...

cd src
python tool_hooks.py          # pure Python, no API key needed
python agent_with_hooks.py    # live agent, proves the hook blocks under real API conditions
python decompose.py
python session_manager.py     # demos save/resume, fork, summarize
```

The live test alert used throughout:

```
Alert ID: NG-2027-1142 | Severity: HIGH (pre-triage) | Source: EDR (CrowdStrike Falcon)
Asset: research-analyst-laptop-04 (owner: Maya Iyer)
Event: Outbound transfer of 8.3 GB to external IP 203.0.113.47 (Singapore, AS65000)
```

See `REFLECTIONS.md` for the exercise reflection answers.
