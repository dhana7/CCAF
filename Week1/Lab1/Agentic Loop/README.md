# Lab 1.1 — Building the Agentic Loop: Orchestration & Subagent Coordination

**CCA-F · Module 1 — Agentic Architecture & Orchestration**
**Scenario:** Enterprise Customer Support Triage Agent (Arctive)

## What this lab is about

This lab builds the four building blocks of a production-grade agentic
system, using an automated support-ticket triage pipeline as the running
example:

1. **The agentic loop (S1)** — a loop driven by `stop_reason`, not a fixed
   iteration count, that keeps calling tools until Claude is actually done.
2. **Coordinator → subagent orchestration (S2)** — one coordinator that
   delegates to four independent, memory-isolated specialist subagents
   (Classifier, CRM Enricher, Drafter, Validator).
3. **Explicit context passing (S3)** — a typed `TicketContext` dataclass
   that carries state through the pipeline instead of loose variables.
4. **Programmatic step enforcement (S4)** — gates that raise a named
   exception if a downstream step is attempted before its precondition is
   satisfied, instead of relying on a prompt instruction.

## My approach

- **Ex 1 (`tools.py`, `loop.py`)** — `classify_ticket` is registered as a
  tool with a strict JSON schema (`ticket_text`, `fields_needed`). The loop
  appends the assistant turn to `messages` *before* branching on
  `stop_reason` (the Lab 1.1 invariant), and only exits on `"end_turn"`.
- **Ex 2 (`subagents.py`, `coordinator.py`)** — each subagent is a single,
  isolated `client.messages.create()` call. `coordinator.py` wires them in
  sequence and prints each subagent's output. The "memory isolation"
  experiment (temporarily stripping `run_drafter`'s classification/CRM
  arguments so it only sees the raw ticket) is done **in place** exactly as
  the lab guide instructs — modify `run_drafter`, re-run `coordinator.py`,
  observe the drafter guessing/omitting the product area and SLA tier, then
  restore the original signature before moving on. No extra "_broken" files
  are kept in the repo; the observed behaviour is written up in
  `REFLECTIONS.md`.
- **Ex 3 (`context.py`, `coordinator_v2.py`)** — `TicketContext` groups
  fields into "required at intake" vs. "populated by X," with
  `classification_complete()`, `enrichment_complete()`, `draft_complete()`
  helper methods used by the gates in Ex 4.
- **Ex 4 (`gates.py`, `coordinator_v3.py`, `coordinator_v3_sabotage.py`)** —
  `PipelineGateError` is a named exception; each gate names the specific
  missing field(s) in its message. `coordinator_v3_sabotage.py` deliberately
  sets `ctx.severity = None` after classification to prove Gate 1 fires
  immediately and steps 2–4 never run.

## Files

| File | Exercise | Purpose |
|---|---|---|
| `src/tools.py` | Ex 1 | Simulated `classify_ticket` tool. |
| `src/loop.py` | Ex 1 | Agentic loop with correct `stop_reason` handling. |
| `src/subagents.py` | Ex 2 | Classifier, CRM Enricher, Drafter, Validator. |
| `src/coordinator.py` | Ex 2 | Calls all four subagents in sequence. |
| `src/context.py` | Ex 3 | `TicketContext` dataclass + completion helpers. |
| `src/coordinator_v2.py` | Ex 3 | Coordinator refactored to use `TicketContext`. |
| `src/gates.py` | Ex 4 | `PipelineGateError` + 3 gate functions. |
| `src/coordinator_v3.py` | Ex 4 | Final coordinator with all gates wired in. |
| `src/coordinator_v3_sabotage.py` | Ex 4 | Demo: Gate 1 fires when `severity` is nulled out. |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...

cd src
python loop.py
python coordinator.py
python coordinator_v2.py
python coordinator_v3.py
python coordinator_v3_sabotage.py   # proves the gate blocks
```

Test ticket used throughout (per the lab guide):

```
From: sarah.chen@globalcorp.com
Subject: Cannot access SSO login — entire team locked out
Our team of 40 has been unable to log in via SSO since 09:00 this morning.
We have a client demo in 3 hours. This is completely blocking us.
```

See `REFLECTIONS.md` for the answers to the exercise and self-check
reflection questions.
