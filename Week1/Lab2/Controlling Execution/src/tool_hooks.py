"""tool_hooks.py — PostToolUse hook engine for NorthGate Capital's SOC agent.

Three hook functions sit between the agent's tool-use decision and the actual
side-effect on production:

    logging_hook         — never blocks; records the call for SOX/SOC2 audit
    arg_validation_hook  — blocks malformed arguments (missing fields, bad IPs)
    protected_asset_hook — blocks actions targeting NorthGate's critical assets

Every hook returns (allowed: bool, reason: str). A False from any hook stops
the call before the real tool runs.

This module is pure Python and runs without an Anthropic API key.
"""

import ipaddress
import json


# ─── NorthGate-specific protection lists (fixed by SOC policy) ─────────────────

# Hosts that must NEVER be quarantined or have their user accounts disabled
# without dual approval. Quarantining trading-prod-01 during market hours has
# happened exactly once at this firm. It cost $3.4M. Hence the hook.
PROTECTED_HOSTS = [
    "trading-prod-01", "trading-prod-02", "trading-prod-03",
    "market-data-relay", "order-router-prime",
    "ceo-laptop", "cfo-laptop", "ciso-laptop",
]

# IPs we must never block at the perimeter firewall — these are our market-data
# providers and prime-broker endpoints. Blocking one kills trading.
PROTECTED_IPS = [
    "198.51.100.10",   # Reuters market-data feed
    "198.51.100.11",   # Bloomberg terminal endpoint
    "192.0.2.55",      # Prime broker API
    "192.0.2.56",      # Clearing house webhook
]


# ─── The hooks (each is a simple function) ─────────────────────────────────────

def logging_hook(tool_name, tool_input):
    """LOG only: never blocks, just records what was called."""
    print(f"  [Hook:log] {tool_name} called with keys {list(tool_input.keys())}")
    return True, ""


def arg_validation_hook(tool_name, tool_input):
    """VALIDATE: reject calls with obviously bad arguments."""
    if tool_name == "block_ip":
        ip = tool_input.get("ip", "")
        if not ip:
            return False, "missing 'ip' argument"
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return False, f"'{ip}' is not a valid IP address"

    if tool_name == "quarantine_host":
        if not tool_input.get("hostname"):
            return False, "missing 'hostname' argument"

    if tool_name == "disable_user":
        if not tool_input.get("username"):
            return False, "missing 'username' argument"

    return True, ""


def protected_asset_hook(tool_name, tool_input):
    """BLOCK: stop any action that targets a NorthGate-critical asset."""
    if tool_name == "quarantine_host":
        host = str(tool_input.get("hostname", "")).lower()
        for protected in PROTECTED_HOSTS:
            if protected in host:
                return False, (
                    f"host '{tool_input.get('hostname')}' is on the PROTECTED_HOSTS list "
                    f"('{protected}') — quarantine requires dual approval"
                )

    if tool_name == "disable_user":
        user = str(tool_input.get("username", "")).lower()
        if user in {"ceo", "cfo", "ciso"} or user.endswith("@northgate-exec"):
            return False, f"user '{tool_input.get('username')}' is an executive — requires CISO approval"

    if tool_name == "block_ip":
        ip = tool_input.get("ip", "")
        if ip in PROTECTED_IPS:
            return False, (
                f"IP '{ip}' is a PROTECTED endpoint (market-data or broker) — "
                f"blocking it would halt trading"
            )

    return True, ""


# ─── Running a tool through the hooks ──────────────────────────────────────────

def run_tool(tool_name, tool_input, tool_fn, hooks, audit_log):
    """
    Run a tool, but only AFTER it passes every hook.

      1. Pass the call through each hook in the list.
      2. If any hook blocks it, do NOT run the tool — return the reason.
      3. If all hooks allow it, run the real tool and return its result.

    Every outcome is recorded in `audit_log` (a plain list) for SOX/SOC2 review.
    """
    for hook in hooks:
        allowed, reason = hook(tool_name, tool_input)
        if not allowed:
            audit_log.append({"tool": tool_name, "input": tool_input, "blocked": True, "reason": reason})
            print(f"  [Hook] BLOCKED '{tool_name}': {reason}")
            return f"BLOCKED by policy: {reason}"

    # All hooks passed — run the real tool.
    audit_log.append({"tool": tool_name, "input": tool_input, "blocked": False, "reason": "allowed"})
    print(f"  [Hook] ALLOWED '{tool_name}'")
    return tool_fn(tool_input)


def print_audit_log(audit_log):
    """Print a SOX/SOC2-style trace of every tool call that was attempted."""
    print("\n" + "-" * 60)
    print("AUDIT LOG (every tool call that passed through the hooks)")
    print("-" * 60)
    for i, entry in enumerate(audit_log, 1):
        status = "BLOCKED" if entry["blocked"] else "allowed"
        args = json.dumps(entry["input"])[:60]
        print(f"  {i}. [{status:>7}] {entry['tool']}({args}) - {entry['reason']}")


# ─── Demo SOC tools (these would call real APIs in production) ─────────────────

def tool_block_ip(tool_input):
    return f"[FW] IP {tool_input['ip']} added to deny-list (simulated)"

def tool_quarantine_host(tool_input):
    return f"[EDR] Host {tool_input['hostname']} isolated from network (simulated)"

def tool_disable_user(tool_input):
    return f"[IAM] User {tool_input['username']} account disabled (simulated)"

def tool_query_siem(tool_input):
    return f"[SIEM] Query '{tool_input.get('query', '')[:40]}' returned 17 events (simulated)"


DEMO_TOOLS = {
    "block_ip":        tool_block_ip,
    "quarantine_host": tool_quarantine_host,
    "disable_user":    tool_disable_user,
    "query_siem":      tool_query_siem,
}


# ─── Entry point: watch the hooks intercept tool calls ──────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("DEMO: PostToolUse Hooks - log, validate, and block SOC tool calls")
    print("=" * 60)

    hooks = [logging_hook, arg_validation_hook, protected_asset_hook]
    audit_log = []

    # A series of tool calls the "agent" wants to make against the test alert.
    attempted_calls = [
        # ALLOWED — quarantine the suspicious analyst laptop
        ("quarantine_host", {"hostname": "research-analyst-laptop-04"}),
        # ALLOWED — block the suspicious external IP from the alert
        ("block_ip",        {"ip": "203.0.113.47"}),
        # ALLOWED — pull related SIEM events
        ("query_siem",      {"query": "src_ip=203.0.113.47 last 24h"}),
        # BLOCKED — production trading server is on the protected list
        ("quarantine_host", {"hostname": "trading-prod-01"}),
        # BLOCKED — market-data IP must never be blocked
        ("block_ip",        {"ip": "198.51.100.10"}),
        # BLOCKED — malformed IP
        ("block_ip",        {"ip": "203.0.113.999"}),
        # BLOCKED — missing username
        ("disable_user",    {"username": ""}),
        # BLOCKED — executive account requires CISO approval
        ("disable_user",    {"username": "ceo"}),
    ]

    for name, args in attempted_calls:
        print(f"\n[Agent] wants to call: {name}({json.dumps(args)[:50]})")
        tool_fn = DEMO_TOOLS.get(name)
        result = run_tool(name, args, tool_fn, hooks, audit_log)
        print(f"  [Result] {result}")

    print_audit_log(audit_log)

    blocked = sum(1 for e in audit_log if e["blocked"])
    print(f"\n[Summary] {len(audit_log)} calls attempted, {blocked} blocked by policy.")
