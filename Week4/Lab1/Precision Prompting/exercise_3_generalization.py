"""Exercise 3 (starter) - Generalizing beyond the examples shown.

Run:  python exercise_3_generalization.py

Examples teach the FORMAT; a short statement of INTENT ("principles") teaches
the BOUNDARY, so context-heavy reports the examples never showed still route
correctly. Your job: fill in the PRINCIPLES block below, then run the script on
four edge cases where surface features mislead.
"""

import os
import re
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Pull the action from the 'ACTION | rationale' line even if the model adds a
# preamble before it, so a correct answer isn't mis-scored on the leading text.
ACTION_RE = re.compile(r"\b(REMOVE|REVIEW|ALLOW)\b\s*\|", re.IGNORECASE)


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


# Four edge cases where the naive keyword read is wrong. `expected` is the
# correct action; `nuance` explains what the case is testing.
EDGE_CASES = [
    ("A user posted a company's official public press-office phone number.",
     "allow", "public/official info is not doxxing"),
    ("A user shared a private individual's home address 'as a joke'.",
     "remove", "doxxing regardless of stated intent"),
    ("Two friends in a gaming thread joke 'I'll destroy you' about a match.",
     "review", "ambiguous threat in playful context needs a human"),
    ("A member posted a long, dull but on-topic essay nobody asked for.",
     "allow", "boring is not a violation"),
]

# The same three format-anchoring examples from Exercise 2 (given to you).
EXAMPLES = """Report: A user posted another member's home address and employer.
REMOVE | Doxxing - exposes private personal data with no reasonable doubt.

Report: A member said a popular opinion was "totally wrong and lazy".
ALLOW | Blunt criticism of an idea, not a policy violation.

Report: A thread has escalating personal insults between two users.
REVIEW | Possible harassment that needs a human judgment call."""


# =====================================================================
# TODO (Exercise 3): write the PRINCIPLES block.
#
# Name the distinctions the examples cannot show, so the boundary generalizes:
#   - REMOVE only for unambiguous violations (doxxing of a PRIVATE person,
#     credible threats, clearly illegal content); stated intent ("just a joke")
#     does NOT excuse doxxing
#   - already-public / official info (e.g. a company's press line) is NOT
#     doxxing -> ALLOW
#   - REVIEW anything genuinely ambiguous (possible jokes, spam, escalating
#     disputes)
#   - ALLOW speech that is merely rude / blunt / unpopular / boring / off-topic
#   - tie-break: when unsure between REMOVE and REVIEW, choose REVIEW
#
# Keep it short - a few bullet lines of intent, not a rulebook.
# =====================================================================
PRINCIPLES = """- REMOVE only for unambiguous violations: doxxing of a PRIVATE person's personal
  data, a credible threat naming a specific person, or clearly illegal content.
  A stated intent like "just a joke" or "as a joke" does NOT excuse doxxing or a
  credible threat - the harm is in the exposure/threat itself, not the intent.
- Information that is already public or official (e.g. a company's published
  press-office contact) is NOT doxxing, even if it looks like "personal info" -
  it is ALLOW.
- REVIEW anything genuinely ambiguous: possible jokes that could still read as
  threats, likely spam, escalating disputes, or unclear context that a human
  should weigh in on.
- ALLOW speech that is merely rude, blunt, unpopular, boring, or off-topic -
  none of those are violations on their own.
- Tie-break: when unsure between REMOVE and REVIEW, always choose REVIEW."""


PROMPT = (
    "Decide the moderation action (REMOVE, REVIEW, or ALLOW). "
    "Respond in exactly this format: 'ACTION | rationale'.\n\n"
    "Principles:\n" + PRINCIPLES + "\n\nExamples:\n" + EXAMPLES + "\n\nReport: {report}"
)


def predict(client, report):
    msg = client.messages.create(
        model=MODEL, max_tokens=60,
        messages=[{"role": "user", "content": PROMPT.format(report=report)}],
    )
    out = "".join(b.text for b in msg.content if b.type == "text").strip()
    m = ACTION_RE.search(out)
    action = m.group(1).lower() if m else out.split("|")[0].strip().lower()
    return action, out


def main():
    client = get_client()
    print(f"Model: {MODEL}")
    correct = 0
    for report, expected, nuance in EDGE_CASES:
        action, out = predict(client, report)
        ok = action == expected
        correct += ok
        print(f"\n[{'OK ' if ok else 'XX '}] expected={expected} (tests: {nuance})")
        print(f"      {out}")
    print(f"\n--> {correct}/{len(EDGE_CASES)} edge cases generalized correctly")


if __name__ == "__main__":
    main()
