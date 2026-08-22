# Lab 2.2 — Connecting the Ecosystem: MCP Servers & Built-in Claude Code Tools

**CCA-F · Module 2 — Tooling & Context for Coding Agents**
**Scenario:** Giving Claude Code real context at NorthPeak Outfitters (continues Lab 2.1)

## What this lab is about

1. **Multiple MCP servers (S4)** — `.mcp.json` declares two independent
   sources, `northpeak-orders` (live order data) and `northpeak-docs`
   (policy documents), so Claude Code can combine both in a single answer
   without anything being pasted into the chat.
2. **Built-in tools used deliberately (S5)** — `Glob` to map the project,
   `Grep` to find exact call sites of a deprecated function, `Read` to open
   only the file that defines the replacement's signature, `Edit` to
   migrate call sites in place, and `Write` to create a brand-new
   `MIGRATION.md`.
3. **Incremental exploration (S5)** — the `Grep → Read → Edit` loop, used to
   make a one-letter analytics-event rename touch exactly one file.

## My approach

- **Ex 1** — `.mcp.json` launches `mcp_servers/orders_server.py`
  (`get_order`, `find_orders_by_email`, reading `data/orders.json`) and
  `mcp_servers/docs_server.py` (`list_docs`, `read_doc`, `search_docs`,
  reading `data/docs/*.md`) over stdio via `FastMCP`. Both paths are
  resolved relative to the project root so the servers work regardless of
  which directory Claude Code is started from.
- **Ex 2 / Ex 3** — `sample_codebase/` is the pre-migration TypeScript
  project: `src/analytics.ts` defines the deprecated `logEvent(name,
  payload)` alongside its replacement `track({ name, props })`;
  `src/notifications.ts` and `src/orders.ts` are the two consumers with
  four total `logEvent` call sites. `MIGRATION.md` documents the
  `logEvent → track` migration and the follow-up `order_cancelled →
  order_canceled` rename, both driven from inside Claude Code using
  Glob/Grep/Read/Edit/Write against this codebase (Claude Code session
  transcripts are not stored here — this folder holds the *inputs* the
  session operates on and the resulting migrated code).

## Files

| Path | Section | Purpose |
|---|---|---|
| `.mcp.json` | S4 | Declares the two MCP servers Claude Code launches. |
| `mcp_servers/orders_server.py` | S4 | Orders source: `get_order`, `find_orders_by_email`. |
| `mcp_servers/docs_server.py` | S4 | Docs source: `list_docs`, `read_doc`, `search_docs`. |
| `data/orders.json`, `data/docs/*.md` | S4 | Order records and policy documents. |
| `sample_codebase/` | S5 | TypeScript project for the refactor exercises. |
| `requirements.txt` | Setup | `mcp>=1.2.0` |

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start Claude Code FROM this folder so it reads .mcp.json:
claude
# then inside Claude Code:
/mcp   # confirm both northpeak-orders and northpeak-docs show as connected
```

Then, inside the Claude Code session, ask the prompts from the lab guide,
e.g.:

```
What's the status of order NP-100245?
Order NP-100190 was delivered. The customer wants to return one item —
are they still inside the return window, and what condition rules apply?
```

and for the refactor exercises, drive Claude Code with:

```
Glob for all *.test.ts files under sample_codebase and list them.
Grep for `logEvent(` in sample_codebase/src and show the matches.
Read sample_codebase/src/analytics.ts so we know the track() signature.
In src/notifications.ts, replace each logEvent(...) call with track({ name, props }),
and update the import from logEvent to track.
```

See `REFLECTIONS.md` for the exercise reflection answers.
