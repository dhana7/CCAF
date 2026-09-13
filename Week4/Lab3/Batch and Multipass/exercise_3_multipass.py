"""Exercise 3 (starter) - Multi-pass review for higher quality.

Run:  python exercise_3_multipass.py

Draft -> critique -> refine. Separating "generate" from "judge" tends to catch
issues a single pass glosses over (imbalance, vagueness, length), and the refine
step has concrete fixes to act on. Your job: implement critique() and refine().
The critique step must LIST problems (not rewrite); the refine step must apply
every point and return only the final briefing text.

NOTE: this makes real API calls. draft() is provided; complete critique() and
refine() before running end-to-end.
"""

import os
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


HEADLINES = [
    "Helix Robotics beats earnings expectations, shares jump 12%.",
    "Regulators open probe into Helix Robotics data practices.",
    "Analysts downgrade Helix Robotics on slowing growth.",
    "Helix Robotics partners with major retailer for nationwide rollout.",
    "Lawsuit alleges safety defects in Helix Robotics products.",
]

STANDARDS = (
    "Briefing standards: lead with the single most important development; balance "
    "positive and negative coverage fairly; be specific (numbers, who/what); stay "
    "neutral in tone; no speculation beyond the headlines; keep it under 120 words."
)


def ask(client, prompt, max_tokens=500):
    msg = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def draft(client, headlines):
    joined = "\n".join(f"- {h}" for h in headlines)
    return ask(client, f"Write a short morning media briefing from today's "
                       f"headlines about Helix Robotics:\n{joined}")


# =====================================================================
# TODO (Exercise 3, piece 1 of 2): critique().
#
# Build a prompt that includes STANDARDS, the headlines, and the draft, then asks
# the model to LIST specific, actionable problems as short bullets (e.g. "buries
# the regulatory probe", "omits the 12% figure", "too long", "leans positive").
# End the instruction with: "Do NOT rewrite - only list issues." Return ask(...).
# Keeping this step to judging-only is what gives refine() a concrete checklist.
# =====================================================================
def critique(client, headlines, draft_text):
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = (
        f"{STANDARDS}\n\n"
        f"Today's headlines about Helix Robotics:\n{joined}\n\n"
        f"Draft briefing:\n{draft_text}\n\n"
        "List specific, actionable problems with this draft against the "
        "standards above, as short bullets (e.g. 'buries the regulatory "
        "probe', 'omits the 12% figure', 'too long', 'leans positive'). "
        "Do NOT rewrite - only list issues."
    )
    return ask(client, prompt)


# =====================================================================
# TODO (Exercise 3, piece 2 of 2): refine().
#
# Build a prompt that includes STANDARDS, the headlines, the draft, AND the
# critique, then asks the model to rewrite the briefing so it fixes every point
# in the critique and meets the standards. End with: "Output only the final
# briefing text." Return ask(...).
# =====================================================================
def refine(client, headlines, draft_text, critique_text):
    joined = "\n".join(f"- {h}" for h in headlines)
    prompt = (
        f"{STANDARDS}\n\n"
        f"Today's headlines about Helix Robotics:\n{joined}\n\n"
        f"Draft briefing:\n{draft_text}\n\n"
        f"Critique of the draft:\n{critique_text}\n\n"
        "Rewrite the briefing so it fixes every point in the critique and "
        "fully meets the standards above. Output only the final briefing text."
    )
    return ask(client, prompt)


def main():
    client = get_client()
    print(f"Model: {MODEL}\n")

    d = draft(client, HEADLINES)
    print("--- DRAFT ---\n" + d)

    c = critique(client, HEADLINES, d)
    print("\n--- CRITIQUE ---\n" + c)

    f = refine(client, HEADLINES, d, c)
    print("\n--- REFINED ---\n" + f)


if __name__ == "__main__":
    main()
