"""subagents.py — Four specialist subagents (Exercise 2 / Step 1).

Each function makes exactly one client.messages.create() call. None of these
agents share memory; the coordinator owns all state.
"""

import json
import anthropic

client = anthropic.Anthropic()

# Lab guide calls this model "claude-haiku-4-5"; the full API string is below.
HAIKU = "claude-haiku-4-5-20251001"

# ── Hardcoded CRM records (per lab guide: "can return a hardcoded dict") ────
# Keyed by customer email domain for demo realism; any unrecognised email
# falls back to the DEFAULT record. In production, replace this lookup with
# a real CRM API call via an MCP tool.
_CRM_DB = {
    "globalcorp.com": {
        "account_tier":    "Enterprise",
        "sla_tier":        "Platinum",
        "account_manager": "Maya Rodriguez",
        "contract_value":  "$240,000/yr",
    },
    "acme.com": {
        "account_tier":    "Business",
        "sla_tier":        "Gold",
        "account_manager": "James Okonkwo",
        "contract_value":  "$48,000/yr",
    },
    "startup.io": {
        "account_tier":    "Starter",
        "sla_tier":        "Bronze",
        "account_manager": "Priya Nair",
        "contract_value":  "$9,600/yr",
    },
}

_CRM_DEFAULT = {
    "account_tier":    "Business",
    "sla_tier":        "Silver",
    "account_manager": "Sam Ellison",
    "contract_value":  "$24,000/yr",
}


def _strip_code_fences(text: str) -> str:
    """Strip ```json fences if the model wrapped its reply in them.

    Required by the doc's defensive-parsing note for run_classifier.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


# ── 1. Classifier ─────────────────────────────────────────────────────
def run_classifier(ticket: str) -> dict:
    """Classify into product_area, severity, intent. Returns parsed dict."""
    response = client.messages.create(
        model=HAIKU,
        max_tokens=512,
        system=(
            "You are a support-ticket classification specialist. Classify the "
            "ticket into:\n"
            "- product_area : Billing | Platform | Integrations | Security | Onboarding\n"
            "- severity     : P1-Critical | P2-High | P3-Medium | P4-Low\n"
            "- intent       : Bug | Question | Feature Request | Billing Dispute\n\n"
            "Respond with ONLY a JSON object. No preamble, no explanation, no code fences."
        ),
        messages=[{"role": "user", "content": f"Classify this ticket:\n\n{ticket}"}],
    )
    return json.loads(_strip_code_fences(response.content[0].text))


# ── 2. CRM Enricher ───────────────────────────────────────────────────
def run_crm_enricher(customer_email: str, classification: dict) -> dict:
    """Return CRM data for the customer via a hardcoded lookup table.

    The lab guide specifies a hardcoded dict for this exercise; in production
    this function would call a real CRM API via an MCP tool.

    Fields returned: account_tier, sla_tier, account_manager, contract_value.
    """
    # Extract the email domain and look up the matching CRM record.
    domain = customer_email.split("@")[-1].lower() if "@" in customer_email else ""
    record = _CRM_DB.get(domain, _CRM_DEFAULT)

    print(f"  [CRM] looked up '{domain}' → {record['account_tier']} / {record['sla_tier']}")
    return dict(record)   # return a copy so callers can't mutate the table


# ── 3. Drafter ────────────────────────────────────────────────────────
def run_drafter(ticket: str, classification: dict, crm: dict) -> str:
    """Draft a professional first-response email referencing the SLA tier."""
    # Compose a single context string from all three arguments (per the doc's note).
    context = (
        f"--- Ticket ---\n{ticket}\n\n"
        f"--- Classification ---\n{json.dumps(classification, indent=2)}\n\n"
        f"--- CRM Record ---\n{json.dumps(crm, indent=2)}\n"
    )

    response = client.messages.create(
        model=HAIKU,
        max_tokens=1024,
        system=(
            "You are a support-response drafter. Write a professional, "
            "empathetic first-response email that:\n"
            "1. Acknowledges the severity\n"
            "2. References the SLA tier explicitly\n"
            "3. States concrete next steps and an SLA-aligned response time\n"
            "4. Signs off as the account manager\n\n"
            "Return ONLY the email body. No preamble, no subject line."
        ),
        messages=[{"role": "user", "content": f"Draft a first response based on:\n\n{context}"}],
    )
    return response.content[0].text.strip()


# ── 4. Validator ──────────────────────────────────────────────────────
def run_validator(draft: str, classification: dict, crm: dict) -> str:
    """Check the draft. Reply 'APPROVED' or list issues."""
    user_msg = (
        f"Classification product_area: {classification.get('product_area')!r}\n"
        f"CRM sla_tier  : {crm.get('sla_tier')!r}\n"
        f"CRM account_tier: {crm.get('account_tier')!r}\n\n"
        f"Draft to validate:\n{draft}"
    )

    response = client.messages.create(
        model=HAIKU,
        max_tokens=512,
        system=(
            "You are a quality validator for support responses. Verify that "
            "the draft:\n"
            "1. References the correct product area from the classification\n"
            "2. Mentions the SLA tier from the CRM record\n"
            "3. Has a tone appropriate to the severity\n\n"
            "If all three pass, reply with exactly the single line: APPROVED\n"
            "Otherwise list each issue on its own line, prefixed with '- '."
        ),
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text.strip()
