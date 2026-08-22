"""context.py — TicketContext dataclass (Exercise 3 / Step 1).

Required-at-intake fields have NO default. Constructing the dataclass
without them raises TypeError at the Python level — exactly the loud
failure the doc asks for.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TicketContext:
    # ── Required at intake (no default) ───────────────────────────────
    ticket_id:      str
    raw_ticket:     str
    customer_email: str

    # ── Populated by Classifier (Optional[str], default None) ─────────
    product_area: Optional[str] = None
    severity:     Optional[str] = None
    intent:       Optional[str] = None

    # ── Populated by CRM Enricher (Optional[str], default None) ───────
    account_tier:    Optional[str] = None
    sla_tier:        Optional[str] = None
    account_manager: Optional[str] = None

    # ── Populated by Drafter and Validator (Optional[str], default None) ──
    draft_response:    Optional[str] = None
    validation_result: Optional[str] = None

    # ── Completion helpers used by gates in Exercise 4 ────────────────
    def classification_complete(self) -> bool:
        return all(
            v is not None for v in (self.product_area, self.severity, self.intent)
        )

    def enrichment_complete(self) -> bool:
        return self.account_tier is not None and self.sla_tier is not None

    def draft_complete(self) -> bool:
        return self.draft_response is not None


if __name__ == "__main__":
    # Demo 1 — Construction without required field fails loudly.
    print("Demo 1: missing required field should raise TypeError")
    try:
        TicketContext(ticket_id="T-1")          # noqa
    except TypeError as e:
        print(f"  ✓ TypeError raised as expected: {e}")

    # Demo 2 — Valid construction; helper methods evolve from False → True.
    print("\nDemo 2: helper-method state transitions")
    ctx = TicketContext(
        ticket_id="T-1001",
        raw_ticket="Cannot access SSO...",
        customer_email="sarah.chen@globalcorp.com",
    )
    print(f"  classification_complete: {ctx.classification_complete()}")
    ctx.product_area = "Security"
    ctx.severity     = "P1-Critical"
    ctx.intent       = "Bug"
    print(f"  classification_complete: {ctx.classification_complete()}  (after writing 3 fields)")
    print(f"  enrichment_complete    : {ctx.enrichment_complete()}")
    ctx.account_tier = "Enterprise"
    ctx.sla_tier     = "Platinum"
    print(f"  enrichment_complete    : {ctx.enrichment_complete()}  (after writing 2 fields)")
    print(f"  draft_complete         : {ctx.draft_complete()}")
    ctx.draft_response = "Hi Sarah, ..."
    print(f"  draft_complete         : {ctx.draft_complete()}")
