"""coordinator_v3.py — Gated coordinator (Exercise 4 / Step 2).

Calls each gate between steps. If any gate raises PipelineGateError, the
remaining steps never execute.

Coordinator model note (doc §Exercise 2):
  This coordinator orchestrates via Python logic and does not call the Claude
  API directly. See coordinator.py docstring for full explanation.
"""

from dataclasses import asdict
import json

from context import TicketContext
from subagents import run_classifier, run_crm_enricher, run_drafter, run_validator
from gates import PipelineGateError, gate_classification, gate_enrichment, gate_draft


RAW_TICKET = """From: sarah.chen@globalcorp.com
Subject: Cannot access SSO login — entire team locked out

Our team of 40 has been unable to log in via SSO since 09:00 this morning.
We have a client demo in 3 hours. This is completely blocking us."""


def main() -> int:
    """Run the fully gated triage pipeline."""
    ctx = TicketContext(
        ticket_id      = "T-1001",
        raw_ticket     = RAW_TICKET,
        customer_email = "sarah.chen@globalcorp.com",
    )

    print("=" * 64)
    print(f"[COORDINATOR v3] Ticket {ctx.ticket_id} → starting gated pipeline")
    print("=" * 64)

    try:
        # ── Step 1: Classify ──────────────────────────────────────────
        print("\n[Step 1] Classifier")
        classification = run_classifier(ctx.raw_ticket)
        ctx.product_area = classification["product_area"]
        ctx.severity     = classification["severity"]
        ctx.intent       = classification["intent"]
        print(f"  ← {classification}")

        # ── Gate 1 ────────────────────────────────────────────────────
        gate_classification(ctx)
        print("  ✓ Gate 1 passed (classification_complete)")

        # ── Step 2: Enrich ────────────────────────────────────────────
        print("\n[Step 2] CRM Enricher")
        crm = run_crm_enricher(
            ctx.customer_email,
            {"product_area": ctx.product_area, "severity": ctx.severity,
             "intent": ctx.intent},
        )
        ctx.account_tier    = crm["account_tier"]
        ctx.sla_tier        = crm["sla_tier"]
        ctx.account_manager = crm["account_manager"]
        print(f"  ← {crm}")

        # ── Gate 2 ────────────────────────────────────────────────────
        gate_enrichment(ctx)
        print("  ✓ Gate 2 passed (enrichment_complete)")

        # ── Step 3: Draft ─────────────────────────────────────────────
        print("\n[Step 3] Drafter")
        ctx.draft_response = run_drafter(
            ctx.raw_ticket,
            {"product_area": ctx.product_area, "severity": ctx.severity,
             "intent": ctx.intent},
            {"account_tier": ctx.account_tier, "sla_tier": ctx.sla_tier,
             "account_manager": ctx.account_manager},
        )
        print(f"  ← draft ({len(ctx.draft_response)} chars)")

        # ── Gate 3 ────────────────────────────────────────────────────
        gate_draft(ctx)
        print("  ✓ Gate 3 passed (draft_complete)")

        # ── Step 4: Validate ──────────────────────────────────────────
        print("\n[Step 4] Validator")
        ctx.validation_result = run_validator(
            ctx.draft_response,
            {"product_area": ctx.product_area, "severity": ctx.severity,
             "intent": ctx.intent},
            {"account_tier": ctx.account_tier, "sla_tier": ctx.sla_tier,
             "account_manager": ctx.account_manager},
        )
        print(f"  ← {ctx.validation_result}")

        print("\n" + "=" * 64)
        print("[FINAL TicketContext]")
        print("=" * 64)
        print(json.dumps(asdict(ctx), indent=2))
        return 0

    except PipelineGateError as e:
        print("\n" + "=" * 64)
        print(f"[PIPELINE BLOCKED] {e}")
        print("=" * 64)
        print("\nState of TicketContext at block point:")
        print(json.dumps(asdict(ctx), indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
