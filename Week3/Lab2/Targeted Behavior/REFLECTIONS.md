# Lab 3.2 — Reflection Answers

## Exercise 1 — Path-Specific Rules

**Why put SECURITY-CRITICAL rules in `src/auth/CLAUDE.md` instead of the root CLAUDE.md — what do you gain by scoping them to the path?**
Scoping keeps the strict rules relevant exactly when they're needed:
Claude Code layers them into context only when you're editing under
`src/auth/`, instead of loading (and potentially diluting) them for every
file in the repo. It also keeps the rule next to the code it governs, so
anyone reading `src/auth/` sees the constraint in place, and the root file
stays short and general.

**The auth request was challenged while the orders helper was made cleanly. What made Claude treat them differently, and why is "refuse and offer a safe alternative" the right behaviour?**
The path-specific `src/auth/CLAUDE.md` loaded a hard rule ("never weaken a
credential check") because the edit target was under `src/auth/`; no such
rule applied under `src/orders/`. Refusing and redirecting to a safe
alternative (a valid fake test token) satisfies the *underlying need*
("make testing easier") without actually weakening production security —
better than either blindly complying or a bare refusal with no path
forward.

**A strict rule in `src/payments/CLAUDE.md` and a looser root rule could seem to conflict. How does path scoping decide which applies?**
The more specific (nearest-directory) CLAUDE.md wins for files under that
path — the root rule still applies everywhere else in the repo, but for
anything under `src/payments/`, the module's stricter rule takes
precedence.

## Exercise 2 — Plan Mode for a Multi-File Migration

**Why is Plan mode worth the extra step for a multi-file migration, when you could just ask for the edits directly?**
A multi-file migration touches several places that all need to change
consistently; Plan mode surfaces the *approach* (which files, what order,
whether the deprecated function gets removed, whether tests run at the
end) for review before any edit lands, so a wrong assumption is caught
before it's applied across the repo instead of after.

**The plan lists "run the tests" as an explicit step. Why bake verification into the plan rather than assume it?**
Baking it in makes "the migration isn't done until it's proven not to have
broken anything" part of the definition of done, not an afterthought that
might get skipped. It also gives the plan (and the person approving it) a
concrete, checkable completion criterion.

**After migrating all callers, `verify_token_v1` became dead code and was removed. Why is removal part of finishing the migration, not optional cleanup?**
A deprecated, weaker function left in the codebase is a standing
temptation — a future caller (human or agent) could reach for it again,
silently reintroducing the weaker check. Removing it once it has zero
callers closes that door permanently and is what actually completes the
migration rather than leaving the vulnerability dormant.

## Exercise 3 — Explore Before You Change

**The explorer's tools are Read, Grep, Glob — no edit/write/bash. Why constrain a subagent like that?**
It makes the survey provably harmless: no matter what the subagent
"decides" to do, it structurally cannot modify anything. That guarantee
lets you run it freely on any module, including money- or
security-critical ones, without any risk to the code itself.

**Why run exploration in a separate subagent instead of having the main agent read all the files itself?**
It cleanly separates "gathering context" from "making changes" as two
distinct steps with two distinct tool scopes, and keeps the main agent's
context focused on the explorer's structured report rather than every raw
file it read along the way — a smaller, more relevant context for the
change that follows.

**The explorer flagged the money-critical rules and the dependency on auth before any edit. How does "explore first" change the quality of the change that follows?**
The follow-up edit is informed rather than guessed: it already knows
`charge()`'s existing validation, that it depends on `verify_token`, and
that the module is money-critical — so the new upper-bound check is added
consistently with what's already there (matching style, not duplicating
the positive-amount guard) instead of risking a change that conflicts with
undiscovered existing logic.
