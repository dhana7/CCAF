"""
agents.py - Three subagents + the StageResult envelope.

KEY IDEA
--------
Every subagent returns a `StageResult`. It NEVER raises into the
coordinator. The coordinator then decides how to react - log it, retry,
escalate to a human - but it always knows what happened and why.

The intake subagent uses Claude to extract structured fields from the
claim narrative (a realistic LLM use case). The other two stages use
deterministic business rules so the lab still runs without burning lots
of tokens.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Any

from anthropic import Anthropic
from sample_claims import COVERED_PROCEDURES

MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5")
_client = Anthropic()  # picks up ANTHROPIC_API_KEY from env


@dataclass
class StageResult:
    """Envelope every subagent must return. Failures are first-class."""
    stage: str
    ok: bool
    data: Any = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Stage 1: Intake - use Claude to extract structured fields from narrative.
# ---------------------------------------------------------------------------

INTAKE_SYSTEM = (
    "You are a claims intake assistant. Given a claim record, extract "
    "the key facts as JSON with these fields: "
    "claim_id, member_id, procedure_code, amount, summary. "
    "Respond with JSON only, no prose."
)


def run_intake(claim: dict) -> StageResult:
    """Call Claude to produce a clean structured summary of the claim."""
    try:
        response = _client.messages.create(
            model=MODEL_NAME,
            max_tokens=400,
            system=INTAKE_SYSTEM,
            messages=[{"role": "user", "content": json.dumps(claim)}],
        )
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        # Be forgiving about ```json fences.
        if text.startswith("```"):
            text = text.strip("`")
            text = text.split("\n", 1)[1] if "\n" in text else text
            if text.endswith("```"):
                text = text[:-3]
        parsed = json.loads(text)
        return StageResult(stage="intake", ok=True, data=parsed)
    except Exception as exc:
        # Catch-all so the subagent NEVER raises into the coordinator.
        return StageResult(stage="intake", ok=False, error=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Stage 2: Validation - deterministic business rules.
# ---------------------------------------------------------------------------

def run_validation(claim: dict) -> StageResult:
    """Check policy rules. Fail fast and loudly."""
    if not claim.get("member_active", False):
        return StageResult(
            stage="validation",
            ok=False,
            error="member_not_active",
        )
    if claim.get("procedure_code") not in COVERED_PROCEDURES:
        return StageResult(
            stage="validation",
            ok=False,
            error=f"procedure_not_covered:{claim.get('procedure_code')}",
        )
    return StageResult(stage="validation", ok=True, data={"checks_passed": True})


# ---------------------------------------------------------------------------
# Stage 3: Adjudication - simple amount-based decision.
# ---------------------------------------------------------------------------

def run_adjudication(claim: dict) -> StageResult:
    """Approve small claims, hold large ones for human review."""
    amount = claim.get("amount", 0)
    if amount < 500:
        decision = "approved"
    elif amount < 5000:
        decision = "hold_for_review"
    else:
        decision = "denied"
    return StageResult(
        stage="adjudication",
        ok=True,
        data={"decision": decision, "amount": amount},
    )
