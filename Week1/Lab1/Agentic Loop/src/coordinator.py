"""coordinator.py — Hub-and-spoke coordinator (Exercise 2 / Step 2).

Calls four subagents in sequence: Classifier → CRM Enricher → Drafter → Validator.
Prints a labelled line after each step.

Coordinator model note (doc §Exercise 2):
  The lab guide specifies claude-opus-4-6 for the coordinator role. In these
  exercises the coordinator is implemented as plain Python orchestration — it
  delegates every Claude API call to the subagent functions and does not call
  the API itself. In a more advanced implementation the coordinator would call
  claude-opus-4-6 to make dynamic routing decisions (e.g. deciding which
  subagent to call next based on intermediate results).
"""

import json
from subagents import run_classifier, run_crm_enricher, run_drafter, run_validator

TEST_TICKET = """From: sarah.chen@globalcorp.com
Subject: Cannot access SSO login — entire team locked out

Our team of 40 has been unable to log in via SSO since 09:00 this morning.
We have a client demo in 3 hours. This is completely blocking us."""

CUSTOMER_EMAIL = "sarah.chen@globalcorp.com"


def run_pipeline(ticket: str, customer_email: str) -> dict:
    print("=" * 64)
    print("[COORDINATOR] Triage pipeline starting")
    print("=" * 64)

    # Step 1 — Classify
    print("\n[Classifier] → calling")
    classification = run_classifier(ticket)
    print(f"[Classifier] ← {classification}")

    # Step 2 — Enrich (explicit context: classification flows in)
    print("\n[CRM Enricher] → calling")
    crm = run_crm_enricher(customer_email, classification)
    print(f"[CRM Enricher] ← {crm}")

    # Step 3 — Draft (explicit context: ticket + classification + crm flow in)
    print("\n[Drafter] → calling")
    draft = run_drafter(ticket, classification, crm)
    print(f"[Drafter] ← ({len(draft)} chars)\n{draft}")

    # Step 4 — Validate (explicit context: draft + classification + crm flow in)
    print("\n[Validator] → calling")
    verdict = run_validator(draft, classification, crm)
    print(f"[Validator] ← {verdict}")

    return {
        "classification": classification,
        "crm":            crm,
        "draft":          draft,
        "verdict":        verdict,
    }


if __name__ == "__main__":
    result = run_pipeline(TEST_TICKET, CUSTOMER_EMAIL)
    print("\n" + "=" * 64)
    print("[FINAL PIPELINE RESULT]")
    print("=" * 64)
    print(json.dumps(result, indent=2))
