# Lab 2.1 — Reflection Answers

## Exercise 1 — Tool Interfaces

**The weak and strong runs use the same model. If accuracy jumps from (say) 3/6 to 6/6, what does that tell you about where tool-selection reliability actually comes from — and what does that tell you about "just use a bigger model" as a fix?**
It tells you the reliability lived in the *interface*, not the model's raw
capability — the exact same weights routed almost every case correctly
once given precise names, descriptions with explicit negative contrast,
and typed parameters. "Use a bigger model" treats selection errors as a
capability problem when they're usually a specification problem; a bigger
model run over the same weak interface will still misroute a meaningful
fraction of the time, at higher cost.

**The strong order tool adds `"pattern": "^NP-[0-9]{6}$"` to `order_id`. What does that pattern buy you beyond helping the model route — what should happen to a malformed id like `100245` at call time?**
Beyond nudging the model to format the argument correctly, the pattern is
a schema-level contract: a malformed id like `100245` (missing the `NP-`
prefix) should be rejected before the tool's business logic even runs —
either by API-side schema validation or by the tool's own
`arg_validation`-style check — rather than being silently passed through
to a lookup that will fail in a less informative way.

**Every strong description ends with "Do NOT use this … use the other tool instead." Why is that explicit negative contrast more reliable than two good positive descriptions that leave the boundary implicit?**
Two positive descriptions can each sound correct in isolation while still
overlapping at the boundary case (e.g. "a customer asking about an item
they bought"). Explicitly naming the sibling tool and the case it does NOT
handle removes the ambiguity at exactly the point where two similar
options compete — the model doesn't have to infer the boundary, it's told
where it is.

## Exercise 2 — Structured Errors & Retries

**The tool returns errors as data instead of raising. What specifically breaks if a tool raises a Python exception mid-loop — and why can't the model recover from that the way it recovers from a `tool_result` marked `is_error`?**
An uncaught exception crashes the Python process running the agentic loop
before a `tool_result` is ever sent back — the model never receives
anything to reason about, so there is no "next turn" in which it could
retry, apologize, or ask a clarifying question. A `tool_result` with
`is_error` set is still a valid API turn: the model sees exactly what went
wrong and can decide what to do next within the same conversation.

**`run_with_retry` uses exponential backoff and a hard cap of 4 attempts. What goes wrong in production if you drop the cap? What goes wrong if you keep the cap but drop the backoff?**
Dropping the cap risks an unbounded retry loop against a service that is
down for an extended period — the request never resolves and resources
are held indefinitely. Keeping the cap but dropping the backoff means
every retry fires immediately, which can hammer an already-struggling
service with a tight retry storm and make the outage worse instead of
riding it out.

**404 and 400 are both non-retryable but mean different things to the customer. Should the agent phrase them identically? Sketch how the structured error could carry enough information for the model to respond differently.**
No — a 404 means "this order doesn't exist" (customer should double-check
the number or maybe placed it under a different account), while a 400
means "the ID I sent was malformed" (the agent itself needs a
correctly-formatted ID, not necessarily the customer's fault). The
envelope already carries `status` and `error`; the model can branch its
phrasing on `status == 404` ("I couldn't find that order — could you
confirm the order number?") vs. `status == 400` ("that doesn't look like a
valid order ID — it should be in the form NP-XXXXXX").

## Exercise 3 — Selection Control with `tool_choice`

**`auto`, `any`, and `FORCED` form a spectrum from least to most constrained. Why is "use the narrowest setting that still works" the right default, rather than always forcing a tool? What do you lose by over-constraining a turn that genuinely needed to ask a clarifying question?**
Forcing a tool on every turn removes the model's ability to ask a
clarifying question or respond in plain text when that's genuinely the
right move — e.g. an ambiguous ticket that needs more information before
it can be classified. The narrowest setting that still guarantees the
property you need (here: "must produce a classification") preserves
flexibility everywhere else.

**In `any` mode the model is required to call a tool but may pick `draft_customer_reply` instead of `classify_ticket`. For a triage step, why is "called the wrong tool" arguably worse than "called no tool"?**
"Called no tool" is a detectable, obviously-incomplete outcome your
pipeline can retry or flag. "Called the wrong tool" produces a
plausible-looking but semantically wrong result (a drafted reply where a
classification was needed) that can silently pass through downstream code
expecting a `classify_ticket` result — a much harder failure to catch.

**Forcing `classify_ticket` guarantees the shape of the turn but not the correctness of the category. Where in the pipeline would you put the safety net that catches a confident-but-wrong classification, and what would it look like?**
Downstream of the forced classification call: a lightweight validation or
audit step (rule-based checks against known keywords/patterns, a
confidence threshold on the classifier's own `reason` field, or periodic
human sampling of low-confidence/high-impact categories) that flags
mismatches for review before the ticket is fully routed — the same role
the Validator plays in Lab 1.1's pipeline.
