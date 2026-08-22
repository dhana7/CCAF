# Lab 2.2 — Reflection Answers

## Exercise 1 — Two MCP Servers

**Why is declaring two MCP servers better than pasting the order JSON and the returns doc into the chat yourself — what do you gain across a long session?**
The agent fetches fresh, authoritative data on demand instead of working
from a snapshot that goes stale and bloats the context window. Across a
long session it can re-query any order or re-read any policy without you
re-pasting, and the same wiring serves every future question — the data
source is declared once, not copied per turn.

**The agent chose `get_order` for the order and `read_doc` for the policy. What makes that routing obvious — and how does it connect to the "strong tool interface" idea from Lab 2.1?**
`get_order` is named object+action and described as "look up an order by
ID"; `read_doc`/`search_docs` are scoped to policy text. The names and
descriptions are clear and non-overlapping, so the model routes on the
interface rather than guessing — exactly the strong-tool-interface
principle from Lab 2.1, now spanning two servers instead of one.

**The returns answer depended on the order containing boots. If the agent had only the returns doc (no orders server), what would it have to do — and where would that go wrong?**
With only the doc it would know the 30-day rule and the footwear caveat
but not *this* order's status, contents, or delivery date. It would have
to ask the customer or guess — and could easily miss that the order
contains boots (BOOT-GTX-M), the fact that triggers the worn-footwear
exclusion.

## Exercise 2 — Precise Refactor with Built-in Tools

**You used Glob, then Grep, then Read, then Edit — in that order. What would you have lost by skipping straight to "read every file" before changing anything?**
You'd burn context loading unrelated files, slow the turn, and raise the
chance of an incomplete or wrong edit. Glob→Grep→Read→Edit keeps the
working set to exactly the files that matter — two source files and one
definition — so the change is fast, cheap, and verifiable.

**The migration changed both the call (`logEvent(…)` → `track(…)`) and the import. Why is updating the import part of the same minimal edit, and what breaks if you forget it?**
`track` is a different export from `analytics.ts`. If you switch the call
to `track(...)` but leave `import { logEvent }`, the `track` symbol is
undefined and the file won't compile (and `logEvent` becomes an unused
import). The minimal *correct* edit changes the call and the import
together.

**Grep found four call sites across two files. How does Grep-before-Edit change your confidence that you have migrated everything, compared with reading files top to bottom looking for calls?**
Grep enumerates every call site deterministically, so you know the full
set (4 across 2 files) *before* editing and can re-Grep afterward to prove
zero live calls remain. Eyeballing files risks missing a call and gives no
proof of completeness.

**You used Edit to change existing files and Write to create MIGRATION.md. Why is Write the wrong tool for a two-line change inside an existing file — and Edit the wrong tool for a file that does not exist yet?**
Write replaces a whole file, so using it for a small in-place change is
needlessly broad and risks clobbering the rest of the file. Edit targets a
span inside an existing file, so it can't create one that isn't there.
Match the tool to the action: Edit for in-place changes, Write for new (or
fully-replaced) files.

## Exercise 3 — Explore Incrementally

**A one-letter rename and a whole-repo read produce the same final diff. For a real monorepo, why does the path you take to that diff matter as much as the diff itself?**
The path determines cost and risk. The incremental Grep→Read→Edit loop
touches one file and a few KB of context; "read everything" can load
hundreds of files, blow the context window, slow the turn, and raise the
odds of an unrelated accidental change. Same diff, far worse process — and
on a large repo the heavy path may not even fit in context.

**When would "read the whole file" (or several files) genuinely be the right call, and how do you tell that case apart from this one?**
Read-the-whole-file is right when the change needs structural
understanding — refactoring a function's internals, tracing control flow,
or when Grep hits are dense and interdependent. Tell them apart by scope:
a local, string- or symbol-scoped change is Grep+Edit; a change whose
correctness depends on surrounding logic warrants a Read first.

**Across all three exercises you gave the agent good sources (MCP) and then acted with precise tools. How do those two halves reinforce each other — what goes wrong if you have one without the other?**
MCP gives correct inputs; the built-in tools let it act narrowly and
accurately. Good sources without precise action → it reads everything and
wastes the context the data should have left room for. Precise tools
without good sources → it acts confidently on guessed data. Together:
correct inputs *and* minimal, accurate changes.
