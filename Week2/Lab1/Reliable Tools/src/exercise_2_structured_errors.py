"""
Exercise 2 (solution) — Structured errors the agent can recover from
====================================================================

Run:           python solutions/exercise_2_structured_errors.py
Offline check: python solutions/exercise_2_structured_errors.py --check

Key idea: tools return errors as DATA (isError / isRetryable), never raise to the
model. The loop retries transient failures with backoff and stops on permanent
ones — "retry a timeout, but stop on a 404."
"""

import json
import os
import sys
import time

# --- Tiny mock Orders service (stands in for a real, flaky API) -------------

ORDERS = {
    "NP-100245": {"status": "shipped", "items": ["TENT-2P-RX", "BAG-20F-DN"], "tracking": "1Z999AA10123456784"},
    "NP-100311": {"status": "processing", "items": ["STOV-CANX"], "tracking": None},
    "NP-100190": {"status": "delivered", "items": ["BOOT-GTX-M"], "tracking": "1Z999AA10198765432"},
}

RETRYABLE = {408, 429, 500, 502, 503, 504}

_next_failure = None


def queue_failure(status, message):
    global _next_failure
    _next_failure = (status, message)


class ServiceError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def orders_service(order_id):
    global _next_failure
    if _next_failure:
        status, message = _next_failure
        _next_failure = None
        raise ServiceError(status, message)
    order_id = (order_id or "").strip().upper()
    if not order_id.startswith("NP-"):
        raise ServiceError(400, f"Malformed order id '{order_id}'. Expected 'NP-XXXXXX'.")
    if order_id not in ORDERS:
        raise ServiceError(404, f"No order found with id '{order_id}'.")
    return {"order_id": order_id, **ORDERS[order_id]}


# --- The tool wrapper and retry loop ----------------------------------------

def call_order_tool(order_id):
    """Always return a structured result dict; never raise."""
    try:
        data = orders_service(order_id)
        return {"isError": False, **data}
    except ServiceError as err:
        return {
            "isError": True,
            "isRetryable": err.status in RETRYABLE,
            "status": err.status,
            "error": err.message,
        }


def run_with_retry(order_id, max_attempts=4):
    delay = 0.2
    for attempt in range(1, max_attempts + 1):
        result = call_order_tool(order_id)
        if not result["isError"]:
            print(f"    attempt {attempt}: success")
            return result
        if result["isRetryable"] and attempt < max_attempts:
            print(f"    attempt {attempt}: retryable (status={result['status']}) "
                  f"-> wait {delay:.1f}s and retry")
            time.sleep(delay)
            delay *= 2
            continue
        reason = "non-retryable" if not result["isRetryable"] else "out of attempts"
        print(f"    attempt {attempt}: {reason} (status={result['status']}) -> stop")
        return result


# --- Tool definition + agent turn -------------------------------------------

ORDER_TOOL = {
    "name": "get_order_status",
    "description": "Get the status of an existing order by ID (format 'NP-XXXXXX').",
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "e.g. 'NP-100245'"}},
        "required": ["order_id"],
    },
}


def get_client():
    from anthropic import Anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (in your environment or .env).")
    return Anthropic()


def agent_turn(message):
    client = get_client()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    messages = [{"role": "user", "content": message}]
    resp = client.messages.create(model=model, max_tokens=600, tools=[ORDER_TOOL], messages=messages)
    while resp.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            order_id = block.input.get("order_id", "")
            print(f"  tool_use: get_order_status({order_id!r})")
            result = run_with_retry(order_id)
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
                "is_error": result["isError"],
            })
        messages.append({"role": "user", "content": results})
        resp = client.messages.create(model=model, max_tokens=600, tools=[ORDER_TOOL], messages=messages)
    return "".join(b.text for b in resp.content if b.type == "text")


def main():
    print("CASE A — times out once, then recovers:")
    queue_failure(504, "Gateway timeout.")
    print("  reply:", agent_turn("What's the status of order NP-100245?"), "\n")

    print("CASE B — order does not exist (404):")
    print("  reply:", agent_turn("Where is my order NP-999999?"), "\n")

    print("CASE C — malformed id (400):")
    print("  reply:", agent_turn("Check order number 100245 please."), "\n")


def check():
    """Offline self-check — no API key needed."""
    ok = call_order_tool("NP-100245")
    assert ok["isError"] is False, ok
    nf = call_order_tool("NP-999999")
    assert nf["isError"] and nf["isRetryable"] is False, nf
    queue_failure(503, "outage")
    fl = call_order_tool("NP-100245")
    assert fl["isError"] and fl["isRetryable"] is True, fl
    print("offline check passed:")
    print(json.dumps(ok))
    print(json.dumps(nf))
    print(json.dumps(fl))


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        main()
