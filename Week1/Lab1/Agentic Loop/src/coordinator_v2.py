"""coordinator_v2.py — Coordinator refactored to use TicketContext (Exercise 3 / Step 2).

The coordinator never passes the whole ctx to a subagent — only the specific
fields each subagent needs.

Coordinator model note (doc §Exercise 2):
  This coordinator orchestrates via Python logic and does not call the Claude
  API directly. See coordinator.py docstring for full explanation.
"""

from dataclasses import asdict
import json

from context import TicketContext
from subagents import run_classifier, run_crm_enricher, run_drafter, run_validator


RAW_TICKET = """From: sarah.chen@globalcorp.com
Subject: Cannot access SSO login — entire team locked out

Our team of 40 has been unable to log in via SSO since 09:00 this morning.
We have a client demo in 3 hours. This is completely blocking us."""


def main():
    # Construct context with all required-at-intake fields.
    ctx = TicketContext(
        ticket_id      = "T-1001",
        raw_ticket     = RAW_TICKET,
        customer_email = "sarah.chen@globalcorp.com",
    )

    print("=" * 64)
    print(f"[COORDINATOR v2] Ticket {ctx.ticket_id} → starting pipeline")
    print("=" * 64)

    # ── Step 1: Classify ──────────────────────────────────────────────
    print("\n[Classifier] → calling")
    classification = run_classifier(ctx.raw_ticket)   # passes only what's needed
    ctx.product_area = classification["product_area"]
    ctx.severity     = classification["severity"]
    ctx.intent       = classification["intent"]
    print(f"[Classifier] ← product_area={ctx.product_area}, "
          f"severity={ctx.severity}, intent={ctx.intent}")

    # ── Step 2: Enrich ────────────────────────────────────────────────
    print("\n[CRM Enricher] → calling")
    crm = run_crm_enricher(
        ctx.customer_email,
        {"product_area": ctx.product_area, "severity": ctx.severity, "intent": ctx.intent},
    )
    ctx.account_tier    = crm["account_tier"]
    ctx.sla_tier        = crm["sla_tier"]
    ctx.account_manager = crm["account_manager"]
    print(f"[CRM Enricher] ← account_tier={ctx.account_tier}, "
          f"sla_tier={ctx.sla_tier}, account_manager={ctx.account_manager}")
    # contract_value is also in `crm` per Ex 2 spec, but TicketContext does
    # not store it (per Ex 3 spec). It's available locally if a downstream
    # step ever needs it.

    # ── Step 3: Draft ─────────────────────────────────────────────────
    print("\n[Drafter] → calling")
    ctx.draft_response = run_drafter(
        ctx.raw_ticket,
        {"product_area": ctx.product_area, "severity": ctx.severity, "intent": ctx.intent},
        {"account_tier": ctx.account_tier, "sla_tier": ctx.sla_tier,
         "account_manager": ctx.account_manager},
    )
    print(f"[Drafter] ← ({len(ctx.draft_response)} chars)\n{ctx.draft_response}")

    # ── Step 4: Validate ──────────────────────────────────────────────
    print("\n[Validator] → calling")
    ctx.validation_result = run_validator(
        ctx.draft_response,
        {"product_area": ctx.product_area, "severity": ctx.severity, "intent": ctx.intent},
        {"account_tier": ctx.account_tier, "sla_tier": ctx.sla_tier,
         "account_manager": ctx.account_manager},
    )
    print(f"[Validator] ← {ctx.validation_result}")

    # ── Final ctx dump ────────────────────────────────────────────────
    print("\n" + "=" * 64)
    print("[FINAL TicketContext]")
    print("=" * 64)
    print(json.dumps(asdict(ctx), indent=2))


if __name__ == "__main__":
    main()
