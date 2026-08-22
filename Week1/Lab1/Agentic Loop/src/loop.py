"""loop.py — Agentic loop that drives the classifier (Exercise 1 / Step 2)."""

import json
import anthropic
from tools import classify_ticket

client = anthropic.Anthropic()

# Test ticket pinned by the lab guide — used across all four exercises.
TEST_TICKET = """From: sarah.chen@globalcorp.com
Subject: Cannot access SSO login — entire team locked out

Our team of 40 has been unable to log in via SSO since 09:00 this morning.
We have a client demo in 3 hours. This is completely blocking us."""

# Tool registration: what Claude sees when deciding whether to call the tool.
TOOLS = [
    {
        "name": "classify_ticket",
        "description": (
            "Classify a support ticket. Returns ONLY the fields listed in "
            "`fields_needed`. Valid fields: product_area, severity, intent. "
            "Call this tool until ALL THREE fields have been collected."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_text": {
                    "type": "string",
                    "description": "Full text of the support ticket to classify.",
                },
                "fields_needed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Subset of [product_area, severity, intent] to classify "
                        "on this call."
                    ),
                },
            },
            "required": ["ticket_text", "fields_needed"],
        },
    },
]


def _summarise_messages(messages: list) -> list:
    """Collapse a long message history into a single summary user turn.

    Called when stop_reason == 'max_tokens' so the next API call starts
    with a shorter context instead of a truncated one.
    """
    summary_lines = ["[Context summarised to avoid token limit]\n"]
    for m in messages:
        role = m["role"].upper()
        content = m["content"]
        if isinstance(content, str):
            summary_lines.append(f"{role}: {content[:200]}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        summary_lines.append(f"TOOL RESULT: {str(block.get('content', ''))[:200]}")
                    elif block.get("type") == "tool_use":
                        summary_lines.append(f"TOOL CALL: {block.get('name')}({block.get('input')})")
                elif hasattr(block, "type"):
                    if block.type == "text":
                        summary_lines.append(f"{role}: {block.text[:200]}")
    return [{"role": "user", "content": "\n".join(summary_lines)}]


def run_classifier_loop(ticket_text: str) -> dict:
    """Drive the agent until all three classification fields are collected."""
    messages = [{
        "role": "user",
        "content": (
            "Classify this support ticket fully. You MUST determine all three "
            "fields: product_area, severity, intent. Call the classify_ticket "
            "tool as many times as needed until all three are confirmed.\n\n"
            f"Ticket:\n{ticket_text}"
        ),
    }]

    collected = {}
    iteration = 0

    while True:
        iteration += 1

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            tools=TOOLS,
            messages=messages,
        )

        print(f"[Iteration {iteration}] stop_reason = {response.stop_reason!r}")

        # ── Invariant: assistant turn appended FIRST, before any branching ──
        messages.append({"role": "assistant", "content": response.content})

        # ── stop_reason: end_turn ─────────────────────────────────────────
        if response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "(no text returned)",
            )
            print("\n[Final assistant message]")
            print(final_text)
            return collected

        # ── stop_reason: tool_use ─────────────────────────────────────────
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → tool_use: {block.name}({block.input})")
                    result = classify_ticket(**block.input)
                    print(f"  ← result : {result}")
                    collected.update(result)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        # ── stop_reason: max_tokens ───────────────────────────────────────
        # Response was cut at the token limit. Log a warning and retry with
        # a summarised history so the next call has room to finish.
        if response.stop_reason == "max_tokens":
            print(
                "  ⚠ [max_tokens] Response truncated at token limit. "
                "Summarising message history and retrying."
            )
            messages = _summarise_messages(messages)
            continue

        # ── stop_reason: stop_sequence ────────────────────────────────────
        # A custom stop string was matched. Treat as end_turn unless you
        # have specific handling logic for the stop string.
        if response.stop_reason == "stop_sequence":
            print(
                "  ℹ [stop_sequence] Custom stop string matched. "
                "Treating as end_turn."
            )
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "(no text returned)",
            )
            print("\n[Final assistant message]")
            print(final_text)
            return collected

        # ── Fallback: unknown stop_reason ─────────────────────────────────
        print(f"  ⚠ Unknown stop_reason {response.stop_reason!r}; aborting loop.")
        return collected


if __name__ == "__main__":
    final = run_classifier_loop(TEST_TICKET)
    print("\n[Collected classification fields]")
    print(json.dumps(final, indent=2))
