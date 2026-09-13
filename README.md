# CCAF

This repository follows the required submission structure: one folder per
week, with one subfolder per lab inside it. Each lab folder is
self-contained and includes:

- The complete lab solution (code + Claude Code configuration files).
- `REFLECTIONS.md` — answers to every reflection / self-check question in
  the lab guide.
- `README.md` — what the lab covers and how my solution approaches it,
  plus exact run instructions.
- Any supporting files needed to run the solution (`requirements.txt`,
  `pytest.ini`, sample data, etc.).

## Structure

```
Week1/
  Lab1/Agentic Loop/                 (Lab 1.1)
  Lab2/Controlling Execution/        (Lab 1.2)
Week2/
  Lab1/Reliable Tools/               (Lab 2.1)
  Lab2/MCP and Tools/                (Lab 2.2)
Week3/
  Lab1/Claude Config/                (Lab 3.1)
  Lab2/Targeted Behavior/            (Lab 3.2)
  Lab3/Iterative and CICD/           (Lab 3.3)
Week4/
  Lab1/Precision Prompting/          (Lab 4.1)
  Lab2/Structured Output/            (Lab 4.2)
  Lab3/Batch and Multipass/          (Lab 4.3)
Week5/
  Lab1/Context Management/           (Lab 5.1)
  Lab2/Resilient Systems/            (Lab 5.2)
  Lab3/Trust and Traceability/       (Lab 5.3)
```

## Beginner-friendly concept guides

Each week folder has its own `LAB.md` — a plain-language walkthrough of
what that week's labs actually teach, written for someone new to these
concepts (not just a summary of the files):

- `Week1/LAB.md` — the agentic loop, subagent delegation, explicit
  context passing, programmatic gates, hooks, fixed vs. adaptive
  decomposition, and session state.
- `Week2/LAB.md` — tool interfaces, structured errors/retries,
  `tool_choice`, MCP servers, and Claude Code's built-in tools.
- `Week3/LAB.md` — CLAUDE.md/`@import`, slash commands, skills,
  path-specific rules, Plan Mode, read-only subagents, TDD, and CI/CD.
- `Week4/LAB.md` — explicit prompting criteria, few-shot consistency,
  generalization principles, tool schemas, semantic validation,
  retry-and-feedback loops, batch processing, parallel threads, and
  multi-pass draft/critique/refine review.
- `Week5/LAB.md` — context preservation, tool-output optimization,
  ambiguity escalation, error-propagation envelopes, disk-backed state,
  crash recovery, confidence-based routing, provenance/quote attachment,
  and confirmed-vs-contested cross-checking.

**`CONCEPT_MAP.md`** (at the repo root) ties all five weeks together in
one place: a couple of sentences per lab on the core concept it teaches,
how each lab links to the ones before/after it, and exact run
instructions + expected output for every lab — useful as a quick-reference
revision sheet for the CCA-F exam and for your own understanding of how
the whole course connects.

## Quick verification

Every lab that ships a pytest suite passes cleanly and matches the pass
count stated in its lab guide:

| Lab | Command | Result |
|---|---|---|
| 1.1 Agentic Loop | `python loop.py` / `coordinator_v3.py` (interactive, needs `ANTHROPIC_API_KEY`) | runs the agentic loop + gated pipeline |
| 1.2 Controlling Execution | `python tool_hooks.py` (offline) / `agent_with_hooks.py` (live) | hook chain blocks policy violations |
| 2.1 Reliable Tools | `python exercise_2_structured_errors.py --check` | offline self-check passes |
| 2.2 MCP and Tools | run inside Claude Code (`/mcp`) | both MCP servers connect |
| 3.1 Claude Config | `pytest -q` | **4 passed** |
| 3.2 Targeted Behavior | `pytest -q` | **6 passed** |
| 3.3 Iterative and CI/CD | `pytest -q` | **8 passed** |
| 3.3 gate script | `python scripts/review_gate.py samples/sample_review.json` / `sample_review_fail.json` | exit 0 / exit 1 respectively |
| 4.1 Precision Prompting | `python exercise_1_explicit_criteria.py` (live) | EXPLICIT prompt shows fewer wrongful "remove" calls than VAGUE |
| 4.2 Structured Output | `python exercise_2_validation.py --check` / `exercise_3_retry_loop.py --demo` | both offline checks pass |
| 4.3 Batch and Multipass | `python exercise_2_parallel.py` (live) | parallel run is faster than sequential run |
| 5.1 Context Management | `python main.py` (live) | 3 demos: facts persist, tool output trimmed, ambiguity triggers a question |
| 5.2 Resilient Systems | `python main.py` (live, run twice) | second run skips already-`done`/`failed` claims |
| 5.3 Trust and Traceability | `python main.py` (live) | findings grouped into auto_clear / human_review / contested |

Each lab's own `README.md` has the full setup and run instructions.
