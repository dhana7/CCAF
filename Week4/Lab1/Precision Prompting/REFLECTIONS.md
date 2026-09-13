# Lab 4.1 — Reflection Answers

## Exercise 1 — Explicit Criteria

**Why does a vague prompt cause wrongful "remove" calls specifically, rather than random errors spread across all three categories?**
A vague instruction ("decide remove, review, or allow") gives the model no
signal about how *conservative* to be with the most consequential action.
Without an explicit narrow definition, the model tends to treat "remove" as
the default response to anything that merely feels negative or
uncomfortable — rudeness, strong disagreement, off-topic content — because
nothing in the prompt tells it those don't qualify. The error concentrates
on false "remove" calls specifically because that's the action with the
lowest implicit bar in a vague prompt.

**Why is the tie-break rule ("if unsure, choose review, not remove") an important part of the design, not just a nice-to-have?**
Because the two possible mistakes have very different costs. A wrongful
"review" just adds a queued item for a human to look at — low cost, fully
recoverable. A wrongful "remove" is an unjustified takedown that directly
harms a real user and erodes trust in the platform — high cost, often not
fully recoverable (the user has already been told their post was removed).
When a system must guess under uncertainty, the tie-break should always
point toward the cheaper, more recoverable mistake.

**What's the actual mechanism by which "explicit and testable" criteria improve accuracy — why does *specificity* help, not just *length*?**
A vague prompt leaves the boundary between categories to the model's own
implicit judgment, which varies run to run and drifts under ambiguous
input. Explicit, testable criteria ("no reasonable doubt," "credible threat
naming a specific person") give the model a concrete test it can apply
consistently — it's checking against a rule, not making a fresh judgment
call each time. Length alone doesn't help; a long but still-vague prompt
would show the same problem. What matters is whether each category has a
clear, checkable boundary.

## Exercise 2 — Few-Shot Consistency

**Why does describing the format in prose ("respond in exactly this format: 'ACTION | rationale'") often fail to produce a consistent format, while showing examples works better?**
Prose descriptions of formatting are themselves ambiguous — "exactly this
format" leaves the model to interpret capitalization, spacing around the
separator, whether to include extra commentary, etc. Examples remove that
ambiguity entirely: the model can directly pattern-match the literal
casing, the exact `" | "` separator, and the absence of any preamble,
because it's copying a demonstrated shape rather than inferring one from a
verbal description.

**Why is it important that the few-shot examples cover all three categories (one REMOVE, one ALLOW, one REVIEW), not just show the format once?**
If every example demonstrated the same action, the model might associate
the *format* with that specific action's content rather than generalizing
the format across all three labels. Showing one example of each action
proves the shape is independent of which label is chosen, so the model
correctly applies the same `ACTION | rationale` structure regardless of
which of the three categories it lands on.

**What's the risk of using too many few-shot examples, or examples that are too similar to each other?**
Beyond a certain point, more examples cost more tokens on every single call
without adding new information — diminishing returns. Worse, if the
examples are too similar to each other (or too similar to the live report
being classified), the model can start pattern-matching on superficial
similarity to a specific example rather than applying the underlying rule,
which actually hurts generalization to genuinely different cases.

## Exercise 3 — Generalization

**Why do the few-shot examples alone fail on the edge cases in this exercise, even though the examples technically demonstrate correct behavior?**
The few-shot examples only ever showed *unambiguous* instances of each
category — a clear case of doxxing, a clear case of blunt allowed
criticism. None of the edge cases in this exercise are surface-level
similar to those examples; they specifically test distinctions the
examples never illustrated (public vs. private information, stated intent
not excusing a violation, playful phrasing masking an ambiguous threat).
Examples teach *format*, not *boundary logic* — for that, the model needs
an explicit statement of the underlying principle.

**Why does "a company's public press-office phone number" need to be explicitly called out as an exception, rather than trusting the model to infer that public information isn't doxxing?**
Because "posting someone's phone number" is exactly the kind of surface
pattern the REMOVE examples train the model to recognize — without an
explicit carve-out, the model may over-generalize "phone number posted" to
"doxxing" regardless of whether the number is private or already public.
Naming the distinction directly closes that gap rather than hoping the
model reasons its way to the same conclusion unprompted.

**Why is "if unsure, choose review" repeated in both Exercise 1's and Exercise 3's design, rather than being a one-time rule?**
Because it's a general safety property of the *system*, not a fix for one
specific prompt — every additional layer of nuance (explicit criteria, then
principles for generalization) introduces new opportunities for genuine
ambiguity, and the tie-break rule needs to hold at every layer to keep the
overall system's error profile safely biased toward the cheaper mistake
(an unnecessary human review) rather than the expensive one (a wrongful
takedown).
