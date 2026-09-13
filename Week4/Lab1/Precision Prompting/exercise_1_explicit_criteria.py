"""Exercise 1 (starter) - Explicit criteria to cut false positives.

Run:  python exercise_1_explicit_criteria.py

Same model, two prompts. A VAGUE prompt lets REMOVE sprawl into wrongful
takedowns (false positives). Your job: replace the EXPLICIT_PROMPT placeholder
below with clear, TESTABLE definitions of each action plus a fail-safe
tie-break, then run the script and compare.

The scorer tracks two things on eight labeled reports:
  1. overall accuracy
  2. the count of wrongful "remove" calls (the failure that actually matters)
"""

import os
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


# Eight labeled reports. `gold` is the correct action for scoring.
REPORTS = [
    ("A user posted another member's home address and workplace without consent.", "remove"),
    ("A member wrote a credible threat of violence naming a specific user.", "remove"),
    ("A post shares a screenshot exposing a private person's phone number.", "remove"),
    ("A member called someone's argument 'completely stupid' during a debate.", "allow"),
    ("A user disagreed strongly but politely with a moderator's decision.", "allow"),
    ("A slightly off-topic reply in a discussion thread.", "allow"),
    ("A user keeps posting the same 'Buy crypto here!' link in every thread.", "review"),
    ("Several members report a heated but on-topic political argument.", "review"),
]

# --- Baseline: intentionally vague. Read it, then run it and watch REMOVE over-fire.
VAGUE_PROMPT = """Decide the moderation action for this reported post: remove, review, or allow.

Report: {report}

Answer with one word only."""


# =====================================================================
# TODO (Exercise 1): write EXPLICIT_PROMPT.
#
# Replace the placeholder string below with clear, testable definitions of each
# action. Your prompt should:
#   - define REMOVE narrowly (only unambiguous violations - e.g. doxxing /
#     exposure of private personal data, a credible threat against a specific
#     person, or clearly illegal content; "no reasonable doubt")
#   - define REVIEW as "needs a human" (likely spam, borderline harassment,
#     ambiguous threats, heated arguments)
#   - define ALLOW as rude/blunt/off-topic/unpopular but NOT a violation
#   - include a tie-break rule: if unsure between remove and review, choose review
#   - keep "{report}" as a placeholder and ask for one word only
#
# The prompt MUST contain the substring "{report}" so .format(report=...) works.
# =====================================================================
EXPLICIT_PROMPT = """You are a Trust & Safety moderator. Decide the moderation action for this
reported post: remove, review, or allow.

Definitions (apply narrowly and literally):
- remove: ONLY for unambiguous violations, with no reasonable doubt. This means:
  doxxing (posting a private person's home address, phone number, workplace, or
  other private personal data without consent), a credible threat of violence
  naming a specific person, or content that is clearly illegal.
- review: anything that needs a human judgment call. This includes likely spam
  or repeated promotional links, borderline or escalating harassment, ambiguous
  or contextual threats (e.g. said in jest, unclear target), and heated but
  on-topic disputes.
- allow: content that is rude, blunt, unpopular, off-topic, or simply annoying,
  but does NOT meet the bar for a violation above. Disagreement, criticism, and
  bluntness are not violations.

Tie-break rule: if you are unsure whether something is "remove" or "review",
always choose "review" — never guess "remove".

Report: {report}

Answer with one word only: remove, review, or allow."""


def classify(client, prompt_template, report):
    msg = client.messages.create(
        model=MODEL, max_tokens=10,
        messages=[{"role": "user", "content": prompt_template.format(report=report)}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip().lower()
    for label in ("remove", "review", "allow"):
        if label in text:
            return label
    return text


def score(client, label, prompt):
    print(f"\n=== {label} ===")
    correct = false_removes = 0
    for report, gold in REPORTS:
        pred = classify(client, prompt, report)
        ok = pred == gold
        correct += ok
        if pred == "remove" and gold != "remove":
            false_removes += 1
        print(f"[{'OK ' if ok else 'XX '}] gold={gold:6} pred={pred:6} | {report[:48]}")
    print(f"--> accuracy {correct}/{len(REPORTS)}, wrongful 'remove' calls: {false_removes}")


def main():
    client = get_client()
    print(f"Model: {MODEL}")
    score(client, "VAGUE prompt", VAGUE_PROMPT)
    score(client, "EXPLICIT prompt", EXPLICIT_PROMPT)


if __name__ == "__main__":
    main()
