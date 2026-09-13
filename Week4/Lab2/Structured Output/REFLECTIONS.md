# Lab 4.2 — Reflection Answers

## Exercise 1 — Tool Schemas

**Why does defining the record as a tool's `input_schema` and forcing `tool_choice` guarantee structure, when asking the model to "return JSON" in prose does not?**
Asking for "JSON" in prose is a *request* the model tries to satisfy in
free text — it can still wrap the JSON in markdown fences, add an
explanatory preamble, or produce a field name that's slightly off. A tool
schema is different: it's a contract enforced by the API itself. When
`tool_choice` forces that specific tool, the API validates the model's
tool call against the schema before ever returning it — a call that
doesn't match (wrong type, missing required field) is rejected at the
API level, not left for you to catch afterward.

**What would happen if you left `tool_choice` at the default (`auto`) instead of forcing the specific tool?**
The model could choose to respond in plain text instead of calling the
tool at all — especially if the input is ambiguous or it wants to ask a
clarifying question. For a workflow that requires a structured record
every single time (like this screening evaluator), that unpredictability
defeats the purpose; forcing the tool is what makes the output shape
deterministic.

**Why does the schema specify `"minimum": 0, "maximum": 10` for score instead of just `"type": "integer"`?**
A bare `"type": "integer"` would accept any integer, including nonsensical
values like `-5` or `500`. Encoding the valid range directly in the schema
means malformed values are rejected by the API before they ever reach your
code — one less category of error your own validation logic has to guard
against later.

## Exercise 2 — Semantic Validation

**Why can't the cross-field rules ("a `strong_hire` must score ≥ 8") be expressed in the JSON Schema itself?**
Standard JSON Schema validates each field largely in isolation — it can
constrain what `score` looks like, and separately what `recommendation`
looks like, but expressing a *relationship* between two fields' values
("if this field is X, that field must satisfy Y") goes beyond what a
schema's built-in keywords cleanly support for this kind of business
logic. Those relationships are domain policy, not structural syntax, so
they belong in code that runs after the schema-valid object comes back.

**Why does the exercise call out the "bool trap" (`isinstance(True, int)` is `True`) specifically — why would this actually cause a bug in practice?**
If the model (or a bug elsewhere) ever produced `score: true` instead of a
number, a naive `isinstance(score, int)` check would incorrectly accept it
as valid, since Python treats booleans as a subtype of integers under the
hood. Then downstream code doing arithmetic or comparisons on `score`
would silently misbehave (e.g. `True <= 10` evaluates fine, but `True` was
never meant to be a valid score). Explicitly excluding bools closes a real,
easy-to-miss gap.

**Why does `validate()` return `(ok, errors)` instead of raising an exception on the first problem it finds?**
Two reasons: first, returning a full list of errors (rather than stopping
at the first one) means the caller — or the retry loop's feedback message
— can tell the model about *every* problem in one shot, rather than
forcing multiple attempts to discover issues one at a time. Second, this
mirrors the "return failures as data, not exceptions" pattern from earlier
in the course — the caller decides what to do with an invalid result;
`validate()` itself never crashes the calling code.

## Exercise 3 — Retry and Feedback

**Why is it important to append the assistant's own tool-call content back into `messages` before appending the `tool_result`, rather than just sending the error message alone?**
The Anthropic API's conversation format requires that a `tool_result`
block always immediately follow the `assistant` turn that contained the
matching `tool_use` block with that same `id`. Skipping the assistant turn
would break that required structure and the next API call would be
rejected — this is the same "append the assistant turn first" invariant
from the very first agentic-loop lab, just showing up again here.

**Why does the feedback message describe *what* was wrong (`"a 'strong_hire' must score >= 8"`) instead of just saying `"invalid, try again"`?**
A generic "try again" gives the model no information to act on — it might
retry with an equally wrong answer, or fix the wrong thing entirely.
Naming the specific violated rule lets the model make a targeted
correction on the very next attempt, which is exactly what happened in the
`--demo` run: told specifically that `strong_hire` needs `score >= 8`, the
second attempt raised the score to 9 rather than guessing randomly.

**Why cap `max_attempts` instead of retrying indefinitely until the model produces a valid payload?**
An uncapped retry loop risks looping forever (and accumulating API cost)
on a case the model genuinely cannot resolve — for example, if the
candidate description itself is contradictory or unclear enough that no
consistent evaluation is possible. A hard cap ensures the pipeline
eventually gives up and returns the last attempt plus its errors, so a
human can look at the specific case rather than the system hanging
indefinitely.
