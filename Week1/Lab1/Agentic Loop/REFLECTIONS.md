# Lab 1.1 — Reflection Answers

## Exercise 1 — The Agentic Loop

**How many tool calls does Claude make? Is this consistent across runs? Why might it vary?**
Typically 1–3. The most efficient path is one tool call with
`fields_needed=["product_area","severity","intent"]`. Claude may instead
call once per field, or split into two calls. Variation comes from
non-determinism in the model and the prompt's tolerance — this is exactly
why `stop_reason`, not iteration count, drives the loop.

**What happens if you append tool results before appending the assistant turn?**
The next `client.messages.create()` raises a 400. Every `tool_result` must
follow the `tool_use` block from the prior assistant turn; the API enforces
this strict ordering.

**Replace `while True` with `for i in range(2)`. What breaks?**
Two iterations may not be enough to reach `end_turn`. The loop exits in the
middle of a tool_use cycle, no final message is emitted, and the collected
dict is incomplete. Lesson: an agent decides when it's done — iteration
counts cannot.

## Exercise 2 — Coordinator & Subagents

**Could you pass the entire `messages` list from Exercise 1's loop to each subagent instead of structured results? Token cost and accuracy implications?**
Yes, but you'd pay for every token in every prior tool call and assistant
message on every subagent call — usually a 5–10× cost increase for the
downstream agents. Worse, the subagent now has to extract the relevant
facts from a long, noisy transcript, which hurts accuracy. Structured
results (dict / dataclass) are cheaper *and* more reliable.

**The Validator never uses tools. What `stop_reason` will it always return, and how does that simplify its caller code in the coordinator?**
Always `"end_turn"`. The coordinator can therefore call `run_validator(...)`
as a single synchronous function and read `response.content[0].text`
directly — no `while True` loop, no `tool_use` dispatch, no message-history
management.

**Memory isolation experiment observation.**
The broken drafter has no idea what the SLA tier is, who the account
manager is, or what tier the account belongs to. It either invents
plausible-but-wrong values or omits them entirely. The validator typically
flags this with a `- missing SLA tier` line. This is the production-grade
failure mode that explicit context passing eliminates.

## Exercise 3 — Explicit Context Passing

**The dataclass `TypeError` is raised at construction time. When would a missing key in a plain dict be discovered? Which failure mode is safer in a pipeline that runs unattended overnight?**
A missing dict key surfaces only when something *reads* it — possibly
several steps later, possibly as a hallucinated value if the read is
defensive (e.g. `d.get("severity", "P3-Medium")`). The dataclass fails the
moment context is built — at the *boundary* of the pipeline. For
unattended overnight runs the dataclass is far safer: the run aborts before
any expensive downstream calls are made, and the stack trace points
directly to the bad input.

**The helper methods return `bool`. How will you use these in Exercise 4 to decide whether to allow the next step to proceed?**
Each gate inverts the helper:
`if not ctx.classification_complete(): raise PipelineGateError(...)`.
The bool is the gate's pass/fail signal; the gate translates a `False`
into a named exception with a precise error message.

## Exercise 4 — Programmatic Step Enforcement

**Why is a named exception with context better than a bare `assert` statement?**
`assert` produces a generic `AssertionError` and can be globally disabled
with `python -O`. `PipelineGateError` is a domain-specific type the caller
can catch precisely; it carries a message that names the missing fields,
which is exactly the diagnostic an on-call engineer needs at 3 AM.

**Should a gate failure automatically retry the failed step, or immediately alert a human?**
Depends on the failure mode and the cost of a wrong action. A transient
Classifier glitch → retry with backoff (idempotent, cheap, recoverable). A
persistent failure or a logic error (e.g. ambiguous ticket) → alert a
human, because automated retries on the same input will produce the same
failure. Production systems usually have *both*: bounded retries first,
alert second.

**What if the CRM returns partial data — `account_tier` present but `sla_tier` None? Modify `gate_enrichment` to handle this case explicitly.**
`gate_enrichment` already names exactly which of `account_tier` /
`sla_tier` is `None`, so the caller's "rerun CRM Enricher" branch knows
which field it still needs. For partial-acceptance logic instead, add an
SLA-default policy in the gate body — e.g. "if `sla_tier is None and
account_tier == 'Starter'`, default to `Bronze` and proceed" — or downgrade
the exception to a warning that records the field as `inferred`.

## Self-Check Before You Leave

**1. Name all four `stop_reason` values. For each, what does your loop do?**
- `"tool_use"`: execute every tool_use block, append the results as a
  single user turn, loop again.
- `"end_turn"`: extract the final text from `content[]` and break.
- `"max_tokens"`: log a warning; consider summarising history and
  retrying.
- `"stop_sequence"`: treat as `end_turn` unless you have custom logic.

**2. You have a Drafter subagent. What exact data do you pass to it — and why not the entire conversation history from the coordinator?**
Pass exactly: `raw_ticket`, classification (`product_area`, `severity`,
`intent`), CRM record (`account_tier`, `sla_tier`, `account_manager`).
Passing the full coordinator history wastes tokens, leaks irrelevant
context, and gives the drafter more chances to focus on the wrong fact.

**3. Explain why the `TypeError` from a missing `TicketContext` field is a better failure than a Claude hallucination caused by missing context.**
`TypeError` is loud, immediate, and points at the boundary where the input
was malformed. A hallucination is silent: the pipeline finishes
"successfully" with a wrong answer, and the bug only surfaces when a
customer complains.

**4. Your team lead says: "Just put DO NOT DRAFT BEFORE CLASSIFYING in the system prompt — that's the same as a gate." How do you respond?**
The prompt is *advice* the model can ignore under token pressure, model
drift, or ambiguous input. A gate is *enforced* by Python and cannot be
bypassed. The prompt belongs in the system message too — but as a hint for
the model, not as the safety mechanism. The gate is the safety net.

**5. Without looking at the code: after two tool calls and their results, how many messages are in the `messages` array? What are their roles?**
Five messages, in order: `user` (initial prompt) → `assistant` (tool_use
#1) → `user` (tool_result #1) → `assistant` (tool_use #2) → `user`
(tool_result #2).
