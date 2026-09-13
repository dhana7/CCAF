# Lab 4.3 — Reflection Answers

## Exercise 1 — Message Batches API

**Why is a stable `custom_id` (built from `enumerate()`) essential to this pattern, when the batch processes requests asynchronously?**
Because the batch doesn't guarantee results come back in submission order —
requests are processed independently and asynchronously, potentially by
different workers finishing at different times. Without a stable id
attached to each request up front, there would be no reliable way to match
a given result back to the specific headline that produced it. `custom_id`
is the join key that makes an unordered, asynchronous result set usable.

**Why does the polling loop need a deadline/fail-safe instead of looping forever until the batch ends?**
A batch can genuinely take longer than expected (the lab notes "usually
minutes, can take longer"), and if the script's own session or terminal
closes while polling, you don't want to have "lost" the batch — it keeps
processing on Anthropic's servers regardless of whether anything is
watching it. The fail-safe (print a `--fetch <batch_id>` hint and return)
means the batch's work is never wasted even if this particular script run
can't wait for it to finish.

**What's the actual tradeoff the Message Batches API is making — why would you choose this over just calling the API 8 times in a normal loop?**
The tradeoff is latency for cost and throughput at scale: batch requests
are typically discounted compared to synchronous calls, and the pattern is
built for workloads where you don't need the answer back in real time
(overnight processing, non-urgent bulk classification). For a small
handful of requests needed immediately, a normal loop (or the parallel
approach in Exercise 2) is simpler and faster to get an answer from; the
batch API becomes worthwhile as volume grows and immediacy matters less.

## Exercise 2 — Parallel Processing

**Why does a thread pool actually help here, when Python is famous for the GIL (Global Interpreter Lock) preventing true parallel execution of Python code?**
The GIL prevents two threads from executing Python *bytecode* at the exact
same instant, but it's released while a thread is blocked waiting on
network I/O — which is exactly what's happening during an API call. So
while one thread is idle waiting for Claude's response, another thread can
make its own request in the meantime. The work here is I/O-bound, not
CPU-bound, which is precisely the case where Python threading provides a
real speedup despite the GIL.

**Why does `pool.map()` preserve input order automatically, and why does that matter compared to the Message Batches approach in Exercise 1?**
`ThreadPoolExecutor.map()` is documented to return results in the same
order as the iterable of inputs it was given, regardless of which thread
happens to finish first — it handles the ordering internally. This means,
unlike the batch API, there's no need for a manual `custom_id`-style
tagging scheme; the correspondence between input and output is implicit
and free.

**Why does the lab warn "too many workers will hit 429s" — what's actually happening when that occurs?**
Anthropic enforces rate limits (requests per minute, tokens per minute) on
API usage. Firing off too many concurrent requests at once can exceed
those limits within a short window, and the API responds with a `429 Too
Many Requests` error for the excess calls. Raising `workers` blindly
doesn't scale throughput indefinitely — past a certain point you're just
converting "slow but successful" into "fast but partially failing."

## Exercise 3 — Multi-Pass Review

**Why does separating "critique" from "refine" tend to produce a better final result than asking the model to draft and improve it in a single pass?**
Asking for a draft and its own improvement in one breath tends to blend
generation and judgment together, so subtle issues (a slight positive
lean, a missing key figure, a buried lead) can slip past the same pass
that produced them — it's hard for the same generative act to also
rigorously self-critique. Splitting them into separate calls forces a
distinct "judging" step that isn't distracted by simultaneously trying to
write good prose, which tends to surface more specific, actionable issues.

**Why must the critique step be instructed to list problems only, never rewrite — what would go wrong if it were allowed to also fix things?**
If the critique step both identifies and fixes issues, the refine step no
longer has a clean list of distinct problems to work from — it either
just repeats the critique's already-fixed text (redundant), or has to
untangle which parts were "the problem" versus "the proposed fix," making
its own job murkier. Keeping critique to listing-only produces a crisp,
actionable checklist that the refine step can apply directly.

**Why does the refine step need to see the *original headlines* again, not just the draft and the critique?**
The critique may point out an omission (e.g. "omits the 12% figure") that
can only be corrected by going back to the source material — the draft and
critique alone don't contain the missing information, only the fact that
it's missing. Without the original headlines available, the refine step
would have no way to actually supply what the critique flagged as absent.
