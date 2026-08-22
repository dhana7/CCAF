# Lab 1.2 — Reflection Answers

## Exercise 1 — PostToolUse Hooks

**The model was told to quarantine `trading-prod-01`. The hook overruled it. Why is hook-level enforcement strictly safer than a system-prompt rule like "never quarantine trading-prod-*"?**
A system-prompt rule is advice the model can ignore under token pressure,
an ambiguous instruction, prompt injection, or model drift — and there is
no code path that stops the tool call if it does. A hook is deterministic
Python that runs between the model's decision and the real side-effect: if
it returns `False`, the tool physically never executes, regardless of what
the model "wanted." The prompt is a hint; the hook is the enforcement
mechanism.

**All three hooks return `(bool, str)`. What would change if `arg_validation_hook` raised an exception instead of returning `False`?**
An uncaught exception would crash the loop (or require a broad
`try/except` around every tool call), and — critically — the attempt would
never be recorded in `audit_log`, because the code that appends the audit
entry never runs. Returning `(False, reason)` keeps the failure inside the
normal control flow: `run_tool()` can log the block, return a clean
`"BLOCKED by policy: ..."` string the model can reason about, and the
SOX/SOC2 record stays complete.

**`protected_asset_hook` checks substrings (`if protected in host`). What kind of asset-naming mistake could let a malicious or hallucinated hostname slip through? How would you tighten it?**
A substring check can both over- and under-match: `trading-prod-01-backup`
would incorrectly match `trading-prod-01`'s protection (over-broad), while
a typo'd or case-different hostname (`Trading-Prod-01`, `trading_prod_01`)
could slip through the *other* way if the comparison isn't
case/format-normalized. Tighten it with an exact-match (or normalized,
case-folded) comparison against a canonical asset inventory rather than a
raw substring test, and validate the hostname against a known-good format
before checking membership.

## Exercise 2 — Fixed vs. Adaptive Decomposition

**If you replaced the fixed digest with adaptive routing, what's the cost in tokens/latency — and what does it buy you?**
Every step would need an extra classification call to decide what happens
next, adding a full model round-trip (tokens + latency) per step, and a
new failure mode: the router could pick the wrong "next step." For a task
whose steps are already certain (the same three every morning), that cost
buys nothing — it only pays off when the input genuinely determines a
different path.

**The classifier falls back to `false_positive` for unknown labels. What's the failure mode in production if it silently picks `false_positive` for a real data-exfiltration event? How would you detect that?**
A real high-severity incident would be silently closed out instead of
escalated — the worst possible failure mode for a SOC. Detect it with a
confidence/uncertainty signal from the classifier (log low-confidence or
"forced fallback" classifications separately), periodic human audit of the
`false_positive` bucket, and correlation with other signals (e.g. an alert
marked `false_positive` that still shows large outbound transfer volume
should be flagged for review).

**Could the morning digest be made partially adaptive — same three steps, but step 2 branches based on what step 1 returned? Sketch it.**
Yes: keep step 1 (extract IoCs) and step 3 (exec brief) fixed, but let step
2 choose an enrichment strategy based on the IoC types found — e.g. if
step 1 returns only `domain`/`hash` IoCs, call a malware-enrichment prompt;
if it returns `ip`/`cve`, call a network-enrichment prompt. The *shape*
(3 steps) stays fixed; only the *content* of step 2 adapts to step 1's
output.

## Exercise 3 — Session Management

**Why is "never drop a concrete value" critical for a SOC investigation specifically — what goes wrong if the digest reads "escalated to legal" but loses the hold ID?**
A legal hold is only actionable if it can be referenced — auditors,
opposing counsel, or a follow-up analyst need the exact ID to verify the
hold is in force. A digest that says "escalated to legal" without the ID
looks complete but is operationally useless: nobody can confirm which hold
covers this investigation, and re-deriving it later may not be possible if
the original message is gone.

**What kind of bug appears if you fork by assignment instead of copy?**
Both branches share the same underlying list object, so a message added to
Branch A also appears in Branch B (and vice versa) — the two "independent"
hypotheses silently merge back into one shared history, defeating the
entire purpose of forking.

**The session is serialized as JSON. Suppose `messages[]` contained Anthropic-SDK content objects instead of plain strings — what extra step would you need?**
SDK content blocks aren't natively JSON-serializable, so you'd need to
convert them to plain dicts/strings first (e.g. via `.model_dump()` or by
extracting `.text`) before `json.dump`, and reconstruct the SDK objects
(if needed) on load. Storing plain strings from the start avoids this
serialize/deserialize step entirely — which is why the demo does it that
way.
