"""Exercise 2 (starter) - Few-shot examples to lock consistent output.

Run:  python exercise_2_few_shot.py

Instructions alone give inconsistent shapes. Your job: fill in
FEW_SHOT_EXAMPLES with three labeled examples in the EXACT target format, then
run the script and compare format compliance against the zero-shot prompt.

Compliance is scored with a strict regex:  ^(REMOVE|REVIEW|ALLOW) \\| .+
"""

import os
import re
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
FORMAT_RE = re.compile(r"^(REMOVE|REVIEW|ALLOW) \| .+")


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


REPORTS = [
    "A user posted screenshots of a member's private messages and real name.",
    "A member wrote 'your take is garbage' in a design critique thread.",
    "Repeated identical affiliate links posted across ten threads in a minute.",
    "Two users trading sarcastic jabs that are getting more personal.",
]

INSTRUCTION = (
    "Decide the moderation action (REMOVE, REVIEW, or ALLOW) and give one short "
    "rationale. Respond in exactly this format: 'ACTION | rationale'."
)

# --- Baseline: describes the format but does NOT demonstrate it.
ZERO_SHOT = INSTRUCTION + "\n\nReport: {report}"


# =====================================================================
# TODO (Exercise 2): write FEW_SHOT_EXAMPLES.
#
# Provide THREE labeled examples - one per action - in the exact target shape,
# so the model can pattern-match casing, the "|" separator, and a one-sentence
# rationale. Cover the label space: one REMOVE, one ALLOW, one REVIEW.
#
# Each example should look exactly like:
#     Report: <a short report>
#     ACTION | one short rationale
#
# Use UPPERCASE actions and a single " | " separator. Separate examples with a
# blank line. Do NOT include a "{report}" placeholder in here - the examples are
# fixed demonstrations; the live report is appended below.
# =====================================================================
FEW_SHOT_EXAMPLES = """Report: A user posted another member's home address and employer without consent.
REMOVE | Doxxing - exposes private personal data with no reasonable doubt.

Report: A member said a popular opinion in the thread was "totally wrong and lazy".
ALLOW | Blunt criticism of an idea, not a policy violation.

Report: A user keeps posting the same promotional link across many threads.
REVIEW | Looks like spam but needs a human to confirm intent and pattern."""


FEW_SHOT = INSTRUCTION + "\n\nExamples:\n" + FEW_SHOT_EXAMPLES + "\n\nReport: {report}"


def run(client, label, prompt):
    print(f"\n=== {label} ===")
    compliant = 0
    for report in REPORTS:
        msg = client.messages.create(
            model=MODEL, max_tokens=60,
            messages=[{"role": "user", "content": prompt.format(report=report)}],
        )
        out = "".join(b.text for b in msg.content if b.type == "text").strip()
        ok = bool(FORMAT_RE.match(out))
        compliant += ok
        print(f"[{'OK ' if ok else 'XX '}] {out!r}")
    print(f"--> {compliant}/{len(REPORTS)} matched the exact format")


def main():
    client = get_client()
    print(f"Model: {MODEL}")
    run(client, "ZERO-SHOT", ZERO_SHOT)
    run(client, "FEW-SHOT", FEW_SHOT)


if __name__ == "__main__":
    main()
