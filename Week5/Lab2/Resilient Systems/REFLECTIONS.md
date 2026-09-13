# Lab 5.2 — Reflection Answers

## Error Propagation

**Why must every subagent return a `StageResult` and never raise an exception into the coordinator — what would break if `run_intake()` just let a parsing error propagate normally?**
If `run_intake()` raised on a parse failure, that exception would bubble up
through the coordinator and — unless caught somewhere generic — crash the
entire batch, taking down every other claim's progress along with it, even
though the failure was specific to one claim. Returning `StageResult(ok=False,
error=...)` keeps a single claim's failure contained: the coordinator can
log it, mark that one claim as `failed`, and continue on to the next claim
in the batch without any risk to the rest of the run.

**Why does `run_validation()` and `run_adjudication()` use deterministic business rules instead of also calling Claude, when `run_intake()` does use Claude?**
Extracting structured facts from unstructured claim narrative text is
genuinely a task suited to an LLM — the input varies in wording and
requires real language understanding. Checking "is this member active" or
"is this procedure on the covered list," by contrast, are simple lookups
against known data with no ambiguity to resolve — using an LLM for those
would add cost, latency, and a new source of non-determinism to a decision
that a plain `if` statement already handles perfectly and repeatably.

**What does the `StageResult` envelope's `stage` field actually buy you that just having `ok`/`data`/`error` wouldn't?**
When something fails partway through a claim's three-stage journey,
`stage` tells you *which* step failed without having to infer it from the
error message's wording alone — this matters for both automated logic
(the coordinator can react differently depending on which stage failed)
and for a human later auditing the scratchpad's history, who can see at a
glance exactly where in the pipeline each claim's failure occurred.

## The Disk-Backed Scratchpad

**Why does `_flush()` write the *entire* state dictionary back to disk on every single mutation, rather than appending just the new change to the file?**
Appending would require the reader to replay a sequence of incremental
changes to reconstruct current state, which is more complex and more
fragile (a corrupted or partial append could break replay). Rewriting the
full state on every mutation keeps the on-disk file always a complete,
self-consistent snapshot — simpler to read back correctly, at the cost of
slightly more disk I/O, which the code comment explicitly notes is "cheap
for small batches."

**Why does `Scratchpad.__init__` handle a `json.JSONDecodeError` by starting fresh rather than crashing or automatically deleting the corrupted file?**
Crashing on a corrupted file would block all further progress, including
on claims that have nothing to do with whatever caused the corruption.
But automatically deleting the file would silently destroy whatever
historical record was salvageable in it. Starting fresh in memory while
leaving the corrupted file on disk untouched keeps the pipeline running
while preserving evidence for a human to investigate what went wrong —
the code comment explicitly notes "in real systems you would alert here."

**Why is this pattern specifically called a "scratchpad" rather than, say, a database — what does that word choice signal about its intended scope?**
"Scratchpad" signals that this is a lightweight, working-memory mechanism
for a single pipeline's in-progress record-keeping — not a
general-purpose, queryable, concurrent-access data store. For a real
production system at larger scale, this JSON-file approach would likely
be replaced by an actual database offering proper concurrency control and
querying; the lab uses a scratchpad because it's the simplest thing that
demonstrates the crash-recovery *concept* without requiring a database
setup.

## Crash Recovery

**Why does the recovery logic check status *before* processing a claim, rather than just re-running every claim and letting cheap "already done" work happen again?**
For a claim pipeline that calls a real LLM in its intake stage, re-running
already-completed claims would mean paying for and waiting on API calls
that produce no new information — pure waste, and it scales badly as a
batch grows larger. Checking status first and skipping already-finished
claims means a restart only pays for the work that's actually still
needed.

**Why does the design skip claims marked `failed`, not just `done` — isn't a permanently failed claim something you'd want to retry?**
This depends on *why* the claim failed. If a claim failed due to a genuine
business-rule rejection (e.g. the procedure isn't covered), retrying
identical logic on identical data will produce the identical failure every
time — retrying is pure waste. The lab's design treats `failed` as a
terminal state a human should look at and decide what to do about, rather
than something the automated pipeline should keep hammering on its own.

**What real production failure does the crash-recovery pattern actually protect against, concretely, in this healthcare-claims scenario?**
Imagine a batch of 100 claims where the process crashes (a server restart,
a network blip, an out-of-memory error) partway through, after claim #47
has already been fully adjudicated. Without persisted, checkable status,
restarting the batch would either lose track of what had already been
decided (re-adjudicating claim #47 and potentially reaching a different,
inconsistent decision) or require a human to manually figure out where
processing left off. The scratchpad plus the skip-if-already-processed
check makes restart-after-crash a fully automatic, safe operation.
