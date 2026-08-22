# Lab 3.1 — Reflection Answers

## Exercise 1 — CLAUDE.md Hierarchy and @import

**Why keep rules in small `@import`ed files instead of pasting everything into one big CLAUDE.md?**
Small modules are independently editable and reviewable in a pull request
— a style change doesn't touch the testing rules diff. They're also
reusable: the same `style.md` could be `@import`ed into other NorthPeak
repos. A single giant file becomes a dumping ground nobody wants to edit
and easy to skim past.

**Claude answered the testing-rules question without opening testing.md. What does that tell you about when project memory is loaded, and why does that matter for every later request?**
Project memory (including `@import`ed files) is loaded once, automatically,
at session start — not read on demand per question. That means every rule
in it is already "in mind" for every subsequent request in the session,
without a separate file-read tool call each time.

**A user-level rule and a project rule could conflict. How does the hierarchy resolve that, and when would you put a rule at the user level vs. the project level?**
The more specific level wins: project memory overrides user memory on
conflict. Put a rule at the user level when it's a personal working
preference that should apply everywhere you work (e.g. "explain before
editing"); put it at the project level when it's a team convention or
domain requirement that must be consistent for everyone touching this
repo (e.g. "money is float, rounded to 2 decimals at the boundary").

## Exercise 2 — Slash Commands

**The `/review` command lists read-only allowed-tools and says "do not edit files." Why scope a command's tools so tightly — what does least privilege buy you here?**
A review step should never be able to silently change the thing it's
reviewing — that would defeat the point of a second, independent check.
Restricting `allowed-tools` to `git diff`/`git status`/`Read`/`Grep` makes
that guarantee structural rather than relying on the prompt telling it not
to edit.

**`/test` and `/review` are just Markdown files in the repo. What do you gain by checking them in versus each person typing the prompt by hand every time?**
Consistency (everyone runs the exact same checklist/command), version
control (the checklist can be improved via PR and the history is visible),
and zero setup cost for a new team member — the commands are just there
the moment they open the repo in Claude Code.

**What is `$ARGUMENTS` for in review.md, and how does it let one command serve many situations?**
`$ARGUMENTS` injects whatever text the user typed after `/review` (e.g.
`pricing.py`) into the command's prompt, so the same command definition can
scope a review to a specific file, directory, or "everything" depending on
what's passed — one file, many use cases.

## Exercise 3 — Skills

**A skill is auto-invoked by its description; a slash command is called explicitly by name. When is each the right way to package a piece of work?**
Use a slash command when the action is deliberate and the user should
consciously choose to trigger it (running tests, starting a formal
review). Use a skill when the workflow should happen naturally as a side
effect of a plain-language request, without the user needing to remember a
specific command name — like "update the changelog," which people phrase
many different ways.

**Why does the quality of the description field matter so much for a skill — what happens if it's too narrow, or too broad?**
The description is the only signal Claude Code uses to decide whether to
invoke the skill. Too narrow and it never fires on requests that should
trigger it (e.g. only matching the literal phrase "changelog entry" and
missing "release notes"). Too broad and it fires on unrelated requests,
producing unwanted or confusing behavior.

**The SKILL.md bakes in judgment ("user-facing sentences," "skip formatting-only edits"). Why encode that in the skill rather than leaving it to each run — how does this connect to why rules live in CLAUDE.md?**
Encoding judgment in the skill makes the output consistent every time it
runs, regardless of who triggered it or how they phrased the request —
the same reason team conventions live in CLAUDE.md rather than being
re-explained in every prompt. Both are ways of making good practice the
default instead of something each person has to remember and re-specify.
