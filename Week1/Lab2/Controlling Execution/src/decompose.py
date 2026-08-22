"""decompose.py — Fixed vs. Adaptive decomposition for the NorthGate SOC.

FIXED:    Morning threat-intel digest. Same 3 steps every shift:
          fetch overnight IoCs -> enrich against our asset inventory -> brief.

ADAPTIVE: Live alert triage. The alert type is unknown until the classifier
          reads it; the specialist playbook is chosen at runtime.
"""

import anthropic

client = anthropic.Anthropic()


def ask_claude(system, user, max_tokens, model="claude-haiku-4-5-20251001"):
    """One-shot Claude call used by both styles below."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


# ─── FIXED decomposition: morning threat-intel digest ──────────────────────────
# Same three steps every morning. No routing decision needed.

def run_fixed_intel_digest(overnight_feed: str, asset_inventory: str) -> dict:
    """
    Pre-market threat-intel digest. The order never changes:

        Step 1: extract structured IoCs from the overnight feed
        Step 2: enrich — which IoCs match assets NorthGate actually owns?
        Step 3: write a 3-bullet exec brief for the SOC manager's 08:00 standup
    """
    print("\n" + "=" * 60)
    print("FIXED DECOMPOSITION - morning threat-intel digest")
    print("=" * 60)

    results = {}

    # Step 1 — extract IoCs as structured JSON
    print("\n[Fixed] Step 1: extract IoCs from overnight feed...")
    iocs = ask_claude(
        system="Extract every indicator of compromise from the threat-intel "
               "feed as a JSON list of {\"type\": \"ip\"|\"hash\"|\"domain\"|\"cve\", "
               "\"value\": str, \"context\": str}. Return ONLY the JSON array.",
        user=overnight_feed,
        max_tokens=512,
    )
    results["iocs"] = iocs
    print(f"[Fixed] IoCs extracted: {iocs[:100]}...")

    # Step 2 — enrich against NorthGate's asset inventory
    print("\n[Fixed] Step 2: enrich — match IoCs against our asset inventory...")
    matches = ask_claude(
        system="You are given (1) a JSON list of IoCs and (2) NorthGate's "
               "asset inventory. List every IoC that matches something we "
               "own or use (by IP, hash, domain, or CVE). Be concise — one "
               "bullet per match in the form: '<ioc value> -> <matched asset>'.",
        user=f"IoCs:\n{iocs}\n\nAsset inventory:\n{asset_inventory}",
        max_tokens=512,
    )
    results["matches"] = matches
    print(f"[Fixed] Matches: {matches[:100]}...")

    # Step 3 — exec brief for the 08:00 SOC standup
    print("\n[Fixed] Step 3: write 3-bullet exec brief for SOC standup...")
    brief = ask_claude(
        system="Write a 3-bullet executive brief for the SOC manager's 08:00 "
               "standup. Each bullet: one line, plain English, name the asset "
               "and the recommended next action. No filler.",
        user=f"IoCs:\n{iocs}\n\nAsset matches:\n{matches}",
        max_tokens=300,
    )
    results["exec_brief"] = brief
    print(f"[Fixed] Brief:\n{brief}")

    return results


# ─── ADAPTIVE decomposition: alert triage ──────────────────────────────────────
# The path is decided at runtime by classifying the alert first.

TRIAGE_BRANCHES = {
    "phishing":          "You are a phishing analyst. Identify the lure, the requested action, and the impersonated brand. List immediate containment steps (block sender, search mailbox, reset affected users).",
    "malware":           "You are an EDR specialist. Identify the malware family if possible from the IoCs. List containment steps (isolate host, collect memory image, scope lateral movement).",
    "lateral_movement":  "You are a threat-hunting analyst. Map the attacker's movement across hosts using the available telemetry. List containment and credential-rotation steps.",
    "data_exfiltration": "You are a DLP / insider-threat analyst. Identify the data volume, destination, and likely sensitivity tier. List immediate containment steps (quarantine source, block destination IP, preserve forensic evidence). Flag whether legal counsel must be notified.",
    "brute_force":       "You are an identity-security analyst. Identify the targeted accounts and source IPs. List containment steps (rate-limit, lock accounts, force MFA re-enrolment).",
    "false_positive":    "You are a Tier-1 SOC analyst. Briefly explain why this is a false positive, what tuning would prevent the next one, and close the alert.",
}


def classify_alert(alert_text: str) -> str:
    """Decide which playbook this alert needs (the routing step)."""
    label = ask_claude(
        system="Classify the security alert into exactly one of: "
               "phishing, malware, lateral_movement, data_exfiltration, "
               "brute_force, false_positive. Reply with ONLY the label.",
        user=alert_text,
        max_tokens=16,
    ).strip().lower()

    # If the classifier returns something unexpected, fall back to a safe default.
    if label not in TRIAGE_BRANCHES:
        label = "false_positive"
    return label


def run_adaptive_triage(alert_text: str) -> dict:
    """
    Adaptive alert triage. Path is decided at runtime:

        Step 1: classify the alert
        Step 2: branch to the matching specialist playbook
    """
    print("\n" + "=" * 60)
    print("ADAPTIVE DECOMPOSITION - alert triage (branch by alert type)")
    print("=" * 60)
    print(f"\n[Adaptive] Alert: {alert_text[:90]}...")

    # Step 1 — routing decision
    branch = classify_alert(alert_text)
    print(f"[Adaptive] Routed to playbook: '{branch}'")

    # Step 2 — run the specialist for the chosen branch
    answer = ask_claude(
        system=TRIAGE_BRANCHES[branch],
        user=alert_text,
        max_tokens=512,
    )
    print(f"[Adaptive] Playbook output:\n{answer[:200]}...")

    return {"branch": branch, "answer": answer}


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── Demo 1: Fixed — daily threat-intel digest ──────────────────────────────
    print("=" * 60)
    print("DEMO 1: Fixed decomposition (task is certain — same path every day)")
    print("=" * 60)

    overnight_feed = """Overnight threat-intel digest (CISA + FS-ISAC, last 12h):
- IP 203.0.113.47 listed for command-and-control activity by CISA.
- File hash a1b2c3d4e5f6 linked to BackdoorX malware family.
- Domain mx-cdn.example listed for credential-phishing kits targeting banks.
- CVE-2027-1188: actively exploited remote code execution in Cisco ASA appliances.
- IP 198.51.100.221 listed for password-spray attacks on Microsoft 365 tenants."""

    asset_inventory = """NorthGate Capital — high-value asset inventory (excerpt):
- Cisco ASA 5500-X firewalls at perimeter (3 units, FW version 9.18)
- Microsoft 365 E5 tenant (4,200 mailboxes)
- CrowdStrike Falcon EDR on all endpoints
- Bloomberg, Reuters market-data feeds (whitelisted)
- Recent suspicious outbound traffic recorded to IP 203.0.113.47"""

    fixed_results = run_fixed_intel_digest(overnight_feed, asset_inventory)
    print("\n[FIXED RESULTS]")
    for key, value in fixed_results.items():
        print(f"  {key}: {str(value)[:80]}")

    # ── Demo 2: Adaptive — alert triage ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DEMO 2: Adaptive decomposition (task is uncertain — branch per alert)")
    print("=" * 60)

    alerts = [
        # The live test alert from the notebook header (data exfiltration)
        """Alert NG-2027-1142: EDR detected outbound transfer of 8.3 GB from
host 'research-analyst-laptop-04' to external IP 203.0.113.47 at 02:47 EST.
Host owner is Maya Iyer (Sr. Equity Research). No active VPN session.""",
        # Phishing
        """Alert NG-2027-1143: User reported via PhishMe button a message from
'security-alerts@northgate-it-support.com' asking them to 'verify their
SSO password' at a lookalike domain. 47 other users received the same email.""",
        # Brute force
        """Alert NG-2027-1144: Azure AD sign-in logs show 3,200 failed
authentication attempts against 'finance-ops@northgate.com' from 14
different IPs in the last 30 minutes. No success yet.""",
    ]
    for alert in alerts:
        result = run_adaptive_triage(alert)
        print(f"\n  -> branch={result['branch']} | {result['answer'][:90]}...")
