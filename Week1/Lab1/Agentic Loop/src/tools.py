"""tools.py — Simulated ticket classification tool (Exercise 1 / Step 1).

The function returns ONLY the fields named in `fields_needed`. The Anthropic
SDK calls this when the agentic loop in loop.py emits a tool_use.
"""

# Field vocabulary fixed by the lab guide
PRODUCT_AREAS = ["Billing", "Platform", "Integrations", "Security", "Onboarding"]
SEVERITIES    = ["P1-Critical", "P2-High", "P3-Medium", "P4-Low"]
INTENTS       = ["Bug", "Question", "Feature Request", "Billing Dispute"]


def _pick_product_area(text: str) -> str:
    t = text.lower()
    if "sso" in t or "login" in t or "auth" in t or "security" in t:
        return "Security"
    if "bill" in t or "invoice" in t or "charge" in t:
        return "Billing"
    if "integration" in t or "api" in t or "webhook" in t:
        return "Integrations"
    if "onboard" in t or "getting started" in t:
        return "Onboarding"
    return "Platform"


def _pick_severity(text: str) -> str:
    t = text.lower()
    if "entire team" in t or "blocking" in t or "production down" in t:
        return "P1-Critical"
    if "demo" in t or "urgent" in t or "outage" in t:
        return "P2-High"
    if "slow" in t or "intermittent" in t:
        return "P3-Medium"
    return "P4-Low"


def _pick_intent(text: str) -> str:
    t = text.lower()
    if "cannot" in t or "broken" in t or "error" in t or "failing" in t:
        return "Bug"
    if "would be nice" in t or "feature" in t or "could you add" in t:
        return "Feature Request"
    if "refund" in t or "invoice" in t and "wrong" in t:
        return "Billing Dispute"
    if "?" in text or "how do" in t or "what is" in t:
        return "Question"
    return "Bug"


def classify_ticket(ticket_text: str, fields_needed: list) -> dict:
    """Return ONLY the requested fields with simulated classification values.

    Parameters
    ----------
    ticket_text : str
        Full ticket text.
    fields_needed : list[str]
        Subset of {"product_area", "severity", "intent"} the caller wants.

    Returns
    -------
    dict
        One entry per requested field.
    """
    pickers = {
        "product_area": _pick_product_area,
        "severity":     _pick_severity,
        "intent":       _pick_intent,
    }
    return {
        field: pickers[field](ticket_text)
        for field in fields_needed
        if field in pickers
    }


if __name__ == "__main__":
    sample = "Cannot access SSO — entire team locked out, demo in 3 hours."
    print(classify_ticket(sample, ["product_area", "severity", "intent"]))
