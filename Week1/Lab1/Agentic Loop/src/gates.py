"""gates.py — PipelineGateError + three gate functions (Exercise 4 / Step 1).

Each gate inspects the TicketContext and either:
  - returns None (success → pipeline continues), or
  - raises PipelineGateError with a message that NAMES the missing fields.

This is the runtime enforcement of step order. Prompt rules are advisory;
these gates are not.
"""

from context import TicketContext


class PipelineGateError(Exception):
    """Raised when a pipeline gate's precondition is not satisfied."""


def gate_classification(ctx: TicketContext) -> None:
    """Block the pipeline if classification fields are missing."""
    if ctx.classification_complete():
        return None

    missing = [
        name for name, value in (
            ("product_area", ctx.product_area),
            ("severity",     ctx.severity),
            ("intent",       ctx.intent),
        )
        if value is None
    ]
    raise PipelineGateError(
        f"Classification incomplete. Missing field(s): {missing}. "
        "Rerun the Classifier before proceeding to enrichment."
    )


def gate_enrichment(ctx: TicketContext) -> None:
    """Block the pipeline if enrichment fields are missing.

    Per the doc, this gate checks account_tier and sla_tier specifically.
    A partial CRM response (one of the two None) is a fail.
    """
    if ctx.enrichment_complete():
        return None

    missing = [
        name for name, value in (
            ("account_tier", ctx.account_tier),
            ("sla_tier",     ctx.sla_tier),
        )
        if value is None
    ]
    raise PipelineGateError(
        f"Enrichment incomplete. Missing field(s): {missing}. "
        "Rerun the CRM Enricher before proceeding to drafting."
    )


def gate_draft(ctx: TicketContext) -> None:
    """Block the pipeline if the draft was not produced."""
    if ctx.draft_complete():
        return None

    raise PipelineGateError(
        "Draft incomplete: ctx.draft_response is None. "
        "Rerun the Drafter before proceeding to validation."
    )
