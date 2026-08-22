"""
Exercise 1 (solution) — Tool interfaces that guide correct selection
====================================================================

Run:  python solutions/exercise_1_tool_interfaces.py

Same model in both runs — only the interface changes. Clear names, descriptions
that say "use this / do NOT use this", and typed params are what drive reliable
tool selection.
"""

import os
from anthropic import Anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (in your environment or .env).")
    return Anthropic()


# Weak design: vague names, overlapping descriptions, loose params.
WEAK_TOOLS = [
    {
        "name": "search",
        "description": "Search for stuff in the system.",
        "input_schema": {
            "type": "object",
            "properties": {"q": {"type": "string", "description": "what to search"}},
            "required": ["q"],
        },
    },
    {
        "name": "lookup",
        "description": "Look up information.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "an id"}},
            "required": ["id"],
        },
    },
]

# Strong design: precise names, disambiguating descriptions, typed params.
STRONG_TOOLS = [
    {
        "name": "search_products",
        "description": (
            "Search the NorthPeak product CATALOG for items we sell (tents, "
            "sleeping bags, stoves, boots, etc.) by free-text query. Use this for "
            "availability, price, or whether a product exists. Do NOT use this to "
            "check something a customer already bought — for an existing purchase "
            "use get_order_status instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Free-text product query, e.g. '4 person tent'.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max catalog results to return (1-10).",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_order_status",
        "description": (
            "Retrieve the status of an EXISTING customer order by its order ID "
            "(shipping status, items, tracking). Use this whenever the customer "
            "gives an order number or references a purchase. Do NOT use this to "
            "browse the catalog — for products use search_products instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID in the format 'NP-XXXXXX', e.g. 'NP-100245'.",
                    "pattern": "^NP-[0-9]{6}$",
                }
            },
            "required": ["order_id"],
        },
    },
]

WEAK_EXPECTED = {"products": "search", "orders": "lookup"}
STRONG_EXPECTED = {"products": "search_products", "orders": "get_order_status"}

TEST_CASES = [
    ("Do you carry a four-person tent?", "products"),
    ("Where is my order NP-100245?", "orders"),
    ("How much is the down sleeping bag?", "products"),
    ("Has NP-100311 shipped yet?", "orders"),
    ("I want to buy a camp stove — do you have one in stock?", "products"),
    ("Can you check the tracking for order NP-100190?", "orders"),
]


def chosen_tool(client, tools, question):
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        tools=tools,
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": question}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return block.name
    return None


def run(client, label, tools, expected):
    print(f"\n=== {label} ===")
    correct = 0
    for question, intent in TEST_CASES:
        got = chosen_tool(client, tools, question)
        want = expected[intent]
        ok = got == want
        correct += ok
        print(f"[{'OK ' if ok else 'MISS'}] {question!r}  chose={got!r} expected={want!r}")
    print(f"--> {correct}/{len(TEST_CASES)} routed correctly")


def main():
    client = get_client()
    print(f"Model: {MODEL}")
    run(client, "WEAK design", WEAK_TOOLS, WEAK_EXPECTED)
    run(client, "STRONG design", STRONG_TOOLS, STRONG_EXPECTED)


if __name__ == "__main__":
    main()
