# Lab 5.1 — Reflection Answers

## Preservation

**Why does the `[CASE FACTS]` block need to be re-sent on every single API call, rather than just mentioned once at the start of the conversation?**
Each call to the API is stateless from the model's perspective — it only
knows what's actually included in that specific request's `messages` and
`system` prompt. If a fact were only mentioned in turn 1's system prompt
and the system prompt changed on turn 15, that fact would simply be gone
from what the model can see, regardless of how important it was earlier.
Re-including it in the system prompt on every turn is what makes it
genuinely persistent rather than a one-time mention that eventually falls
out of context.

**Why does the design deliberately keep the CaseFacts block *short*, rather than logging the entire conversation history into it?**
Every token in the system prompt is paid for — in cost and in
latency — on every single API call for the rest of the conversation. A
short block of confirmed, load-bearing facts (customer ID, tier) is worth
that recurring cost. Dumping the entire conversation history into it would
be redundant (the history is often already in `messages` anyway) and
would make the system prompt grow unboundedly as the conversation gets
longer, defeating the purpose of a lightweight, pinned summary.

**What real production failure does this technique prevent that a naive agent (no case-facts mechanism) would suffer from?**
A naive agent relying purely on scrollback conversation history can
"forget" a fact that was established many turns ago, especially once a
long conversation gets summarized or truncated for context-length
reasons — the customer might have to repeat their ID or tier multiple
times, which feels broken and erodes trust. Pinning confirmed facts
outside the regular scrollback guarantees they survive regardless of what
happens to the rest of the history.

## Optimization

**Why trim the tool's *output* rather than just asking the tool to return less data in the first place?**
In many real systems, the tool is a wrapper around an existing API or
database that returns whatever *it* returns — you may not control or want
to change that underlying service just to serve one particular agent's
context budget. Trimming at the boundary between "raw tool output" and
"what the model sees" keeps the optimization logic in one place, specific
to what each Claude-facing tool actually needs, without having to modify
upstream services.

**Why is `RELEVANT_FIELDS` defined per-tool rather than as one global whitelist applied to everything?**
Different tools return meaningfully different kinds of data for different
purposes — `lookup_orders` needs enough to summarize orders in a list,
while `get_order_details` needs the full item breakdown for one specific
order. A single global whitelist would either be too narrow (dropping
fields some tools genuinely need) or too broad (defeating the whole point
of trimming). Per-tool whitelists let each tool's context footprint match
exactly what it's actually used for.

**What's the risk of trimming too aggressively — of the whitelist accidentally excluding something the model actually needed?**
If a whitelist is missing a field the model needs to answer correctly, the
agent will either give an incomplete answer or have to make an additional
tool call to get the missing information — worse for both cost and user
experience than including it in the first place. This is why the
whitelist needs to be chosen deliberately against what the agent's actual
tasks require, not just "whatever seems small."

## Escalation on Ambiguity

**Why is "ask a clarifying question" the correct behavior here, rather than picking the most likely order and proceeding?**
Cancelling the wrong order is a costly, hard-to-reverse mistake that
directly and negatively affects a real customer — guessing wrong here has
real consequences, unlike a low-stakes guess elsewhere. When an action is
both consequential and the input is genuinely ambiguous (multiple valid
matches, no way to disambiguate from what's been said), asking is strictly
safer than guessing, even at the cost of one extra conversational turn.

**How does the "[CASE FACTS] is authoritative" instruction interact with the ask-on-ambiguity rule — why are both needed together?**
They handle two different failure modes. Without the "CASE FACTS is
authoritative" rule, the agent might re-ask for information it already has
(annoying, wastes a turn) even when it's *not* ambiguous. Without the
ask-on-ambiguity rule, the agent might guess on things that genuinely
require clarification. Together they draw a clear line: things that are
already confirmed should never be re-asked; things that are genuinely
unresolved should always be asked, never guessed.

**Why might a system prompt instruction alone not be fully reliable for enforcing "always ask on ambiguity" in a production system — connecting back to earlier weeks' lessons on gates and hooks?**
Just like the earlier lessons on hooks (Week 1) and gates (Week 1) showed,
a prompt instruction is advice the model can occasionally get wrong or
override under pressure, especially on borderline-ambiguous cases where
reasonable judges might disagree about whether clarification is truly
needed. A more bulletproof production system might pair this instruction
with a deterministic check — e.g., if a tool call would act on one of
several ambiguous matching records without an explicit selection, block
the action programmatically rather than relying solely on the model
choosing to ask.
