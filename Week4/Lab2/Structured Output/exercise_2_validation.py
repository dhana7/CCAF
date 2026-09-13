"""Exercise 2 (starter) - Schema plus semantic validation.

Run live:       python exercise_2_validation.py
Offline check:  python exercise_2_validation.py --check

A JSON Schema is a syntax check: it can say "score is an integer 0-10" but it
CANNOT say "a strong_hire must score at least 8." Cross-field policy lives in
code. Your job: implement validate(payload) so it returns (ok, errors), then
verify it offline with --check before spending an API call.

Rules to enforce:
    name is a non-empty string
    recommendation in {strong_hire, hire, no_hire}
    score is an integer in 0..10
    reason is a non-empty string
    strong_hire => score >= 8       (cross-field policy)
    no_hire     => score <= 4       (cross-field policy)
"""

import json
import os
import sys

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
RECS = {"strong_hire", "hire", "no_hire"}


def get_client():
    from anthropic import Anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


# =====================================================================
# TODO (Exercise 2): implement validate(payload).
#
# Return a tuple (ok: bool, errors: list[str]) - do NOT raise.
#   1. If payload is not a dict, return (False, ["payload is not an object"]).
#   2. Check each field and append a clear message for every failure:
#        - name:   non-empty string
#        - recommendation: must be in RECS
#        - score:  integer in 0..10  (see the bool trap below)
#        - reason: non-empty string
#   3. Cross-field policy:
#        - strong_hire => score >= 8
#        - no_hire     => score <= 4
#   4. Return (len(errors) == 0, errors).
#
# BOOL TRAP: in Python, isinstance(True, int) is True, so score=True would pass
# as an int. Filter it out explicitly:
#     is_int = isinstance(score, int) and not isinstance(score, bool)
# =====================================================================
def validate(payload):
    """Return (ok: bool, errors: list[str]) for a candidate evaluation."""
    if not isinstance(payload, dict):
        return False, ["payload is not an object"]

    errors = []

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name must be a non-empty string")

    rec = payload.get("recommendation")
    if rec not in RECS:
        errors.append(f"recommendation must be one of {sorted(RECS)}")

    score = payload.get("score")
    # BOOL TRAP: isinstance(True, int) is True in Python, so exclude bools explicitly.
    is_int = isinstance(score, int) and not isinstance(score, bool)
    if not is_int or not (0 <= score <= 10):
        errors.append("score must be an integer 0..10")

    reason = payload.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("reason must be a non-empty string")

    # Cross-field policy: a JSON Schema alone cannot express these relationships.
    if rec == "strong_hire" and is_int and score < 8:
        errors.append("a 'strong_hire' must score >= 8")
    if rec == "no_hire" and is_int and score > 4:
        errors.append("a 'no_hire' must score <= 4")

    return (len(errors) == 0), errors


EVALUATE_TOOL = {
    "name": "record_evaluation",
    "description": "Record a structured screening evaluation for one job candidate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "recommendation": {"type": "string", "enum": ["strong_hire", "hire", "no_hire"]},
            "score": {"type": "integer", "minimum": 0, "maximum": 10},
            "reason": {"type": "string"},
        },
        "required": ["name", "recommendation", "score", "reason"],
    },
}

CANDIDATES = [
    "Role: Staff Engineer. Dana Lee - 12 years, architected a high-traffic platform, "
    "mentors widely, outstanding system design.",
    "Role: Staff Engineer. Sam Ortiz - 1 year experience, no architecture work, "
    "struggled with the design exercise.",
]


def evaluate(client, candidate):
    msg = client.messages.create(
        model=MODEL, max_tokens=300, tools=[EVALUATE_TOOL],
        tool_choice={"type": "tool", "name": "record_evaluation"},
        messages=[{"role": "user", "content": f"Evaluate this candidate:\n{candidate}"}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return block.input
    return None


def main():
    client = get_client()
    print(f"Model: {MODEL}")
    for candidate in CANDIDATES:
        payload = evaluate(client, candidate)
        ok, errors = validate(payload)
        print(f"\ncandidate: {candidate[:55]}")
        print("payload:", json.dumps(payload))
        print("valid:", ok, "" if ok else f"-> {errors}")


def check():
    good = {"name": "Dana Lee", "recommendation": "strong_hire", "score": 9,
            "reason": "Deep architecture experience, strong design."}
    bad = {"name": "", "recommendation": "maybe", "score": 12, "reason": "Great."}
    cross = {"name": "Sam Ortiz", "recommendation": "strong_hire", "score": 4,
             "reason": "Limited experience."}
    assert validate(good) == (True, []), validate(good)
    assert validate(bad)[0] is False
    assert validate(cross)[0] is False
    print("offline validation check passed")
    print("bad ->", validate(bad)[1])
    print("cross ->", validate(cross)[1])


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        main()
