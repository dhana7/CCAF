"""
Exercise 3 (solution) — Scoping behaviour with tool_choice
==========================================================

Run:  python solutions/exercise_3_tool_choice.py

Only the FORCED mode guarantees every ticket comes back as a clean
classify_ticket call on turn one — exactly what a routing pipeline needs. Use the
narrowest tool_choice that still lets the step do its job.
"""

import os
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (in your environment or .env).")
    return Anthropic()


CLASSIFY_TOOL = {
    "name": "classify_ticket",
    "description": "Classify a support ticket into exactly one routing category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["order_issue", "product_question", "return_request", "other"],
                "description": "The single best category.",
            },
            "reason": {"type": "string", "description": "One short justification."},
        },
        "required": ["category", "reason"],
    },
}

DRAFT_TOOL = {
    "name": "draft_customer_reply",
    "description": "Draft a customer-facing reply message.",
    "input_schema": {
        "type": "object",
        "properties": {"body": {"type": "string"}},
        "required": ["body"],
    },
}

TICKETS = [
    "My order NP-100245 still hasn't arrived and it's been two weeks!",
    "Do your boots come in wide sizes?",
    "I'd like to return the tent I bought, it's too small.",
    "Just wanted to say your customer service has been great, thanks!",
]


def classify(client, ticket, tool_choice):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system="You triage support tickets. When you classify, call classify_ticket.",
        tools=[CLASSIFY_TOOL, DRAFT_TOOL],
        tool_choice=tool_choice,
        messages=[{"role": "user", "content": ticket}],
    )
    calls = [b for b in msg.content if b.type == "tool_use"]
    if not calls:
        text = "".join(b.text for b in msg.content if b.type == "text")
        print(f"    -> no tool call (stop_reason={msg.stop_reason}); said {text[:60]!r}")
    elif calls[0].name == "classify_ticket":
        print(f"    -> classify_ticket: category={calls[0].input.get('category')!r}")
    else:
        print(f"    -> chose a DIFFERENT tool: {calls[0].name!r}")


def main():
    client = get_client()
    print(f"Model: {MODEL}")

    modes = {
        "auto": {"type": "auto"},
        "any": {"type": "any"},
        "FORCED": {"type": "tool", "name": "classify_ticket"},
    }

    for label, choice in modes.items():
        print(f"\n=== tool_choice = {label} ===")
        for ticket in TICKETS:
            print(f"  ticket: {ticket!r}")
            classify(client, ticket, choice)


if __name__ == "__main__":
    main()
