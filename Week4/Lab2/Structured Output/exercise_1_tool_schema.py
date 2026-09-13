"""Exercise 1 (starter) - Force structured output with tool_use + JSON Schema.

Run:  python exercise_1_tool_schema.py

Asking the model to "return JSON" in prose is unreliable (markdown fences, stray
preambles, missing fields). Defining the target object AS a tool's input_schema
and forcing tool_choice means the model's tool arguments ARE your structured
object. Your job: complete EVALUATE_TOOL's input_schema so it describes the
target record exactly, then run it on three candidates.

The target record (all four fields required):
    name           - string, non-empty
    recommendation - string, one of: strong_hire | hire | no_hire
    score          - integer, minimum 0, maximum 10
    reason         - string, one-sentence justification
"""

import json
import os
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


CANDIDATES = [
    "Role: Senior Backend Engineer. Maya Chen - 8 years Python/Go, led a 6-person "
    "team, scaled a payments system to 1M users, strong system-design answers.",
    "Role: Senior Backend Engineer. Tom Ruiz - bootcamp grad, 1 year support "
    "engineering, two small portfolio apps, no backend production experience.",
    "Role: Data Analyst. Priya Nair - 4 years SQL and dashboards, solid "
    "stakeholder communication, some Python, no ML background.",
]


# =====================================================================
# TODO (Exercise 1): complete input_schema below.
#
# Describe the target record exactly, using JSON Schema inside "properties":
#   - name:           {"type": "string", ...}
#   - recommendation: {"type": "string", "enum": ["strong_hire", "hire", "no_hire"], ...}
#   - score:          {"type": "integer", "minimum": 0, "maximum": 10, ...}
#   - reason:         {"type": "string", ...}
# Then mark ALL FOUR fields required in the "required" list.
#
# The API rejects any tool call that doesn't match this schema, so getting the
# schema right is what guarantees the shape.
# =====================================================================
EVALUATE_TOOL = {
    "name": "record_evaluation",
    "description": "Record a structured screening evaluation for one job candidate.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The candidate's full name, non-empty.",
            },
            "recommendation": {
                "type": "string",
                "enum": ["strong_hire", "hire", "no_hire"],
                "description": "The hiring recommendation for this candidate.",
            },
            "score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 10,
                "description": "Overall fit score from 0 (poor fit) to 10 (excellent fit).",
            },
            "reason": {
                "type": "string",
                "description": "A one-sentence justification for the recommendation and score.",
            },
        },
        "required": ["name", "recommendation", "score", "reason"],
    },
}


def evaluate(client, candidate):
    msg = client.messages.create(
        model=MODEL, max_tokens=300, tools=[EVALUATE_TOOL],
        tool_choice={"type": "tool", "name": "record_evaluation"},
        messages=[{"role": "user", "content": f"Evaluate this candidate:\n{candidate}"}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return block.input   # this IS the structured object
    return None


def main():
    client = get_client()
    print(f"Model: {MODEL}")
    for candidate in CANDIDATES:
        payload = evaluate(client, candidate)
        print(f"\ncandidate: {candidate[:55]}...")
        print("structured:", json.dumps(payload))


if __name__ == "__main__":
    main()
