"""session_manager.py — Save, resume, fork, and summarize SOC investigation
sessions for NorthGate Capital's SOC team.

A session is just a dictionary:
    {
        "id":        "a1b2c3",     # short unique id
        "parent_id": None,         # set when this was forked from another
        "messages":  [ ... ],      # the running investigation history
        "summary":   "",           # structured digest of older messages
    }

Each session is stored as a JSON file under ./sessions/, so any analyst can
open the file and read exactly what the agent remembers.
"""

import anthropic
import json
import os
import uuid

client = anthropic.Anthropic()

SESSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")


# ─── Make and grow a session ───────────────────────────────────────────────────

def new_session():
    """Create a fresh, empty session (just a dictionary)."""
    session = {
        "id": uuid.uuid4().hex[:6],
        "parent_id": None,
        "messages": [],
        "summary": "",
    }
    print(f"\n[Session] created new session '{session['id']}'")
    return session


def add_user(session, text):
    """Add a user (analyst) message to the session's history."""
    session["messages"].append({"role": "user", "content": text})


def add_assistant(session, text):
    """Add an assistant (Sentinel) message to the session's history."""
    session["messages"].append({"role": "assistant", "content": text})


# ─── Save & resume (survive a shift change) ────────────────────────────────────

def save_session(session):
    """Write the session to a JSON file. Returns the file path."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, session["id"] + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2, ensure_ascii=False)
    print(f"  [Session] saved '{session['id']}' ({len(session['messages'])} msgs) -> {path}")
    return path


def resume_session(session_id):
    """Load a saved session back so a different shift can continue the work."""
    path = os.path.join(SESSIONS_DIR, session_id + ".json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"No saved session with id '{session_id}'")
    with open(path, encoding="utf-8") as f:
        session = json.load(f)
    print(f"\n[Session] resumed '{session_id}' ({len(session['messages'])} msgs restored)")
    return session


# ─── Fork (test two hypotheses in parallel) ────────────────────────────────────

def fork_session(session):
    """
    Copy a session at its current point into a new branch.

    Both branches share the history up to the fork, then evolve independently.
    Used when the SOC wants to explore two competing hypotheses (insider vs
    external) without losing the shared prior context.
    """
    child = new_session()
    child["parent_id"] = session["id"]
    child["messages"] = list(session["messages"])  # shallow copy of history
    child["summary"]  = session["summary"]
    print(f"[Session] forked '{session['id']}' -> new branch '{child['id']}'")
    return child


# ─── Summarize (keep a long session small) ─────────────────────────────────────

def summarize_session(session, keep_recent=2):
    """
    Squeeze old investigation turns into a short structured digest:

      - Keep the last `keep_recent` messages as-is (fresh context).
      - Ask Claude to compress everything older into DECISIONS / FACTS / OPEN.
      - Replace the old messages with that summary on the session object.

    Concrete values (hostnames, IP addresses, user names, timestamps) MUST be
    preserved — losing them in summarization is how investigations go wrong.
    """
    if len(session["messages"]) <= keep_recent:
        print("  [Session] nothing to summarize (history is short).")
        return session

    older  = session["messages"][:-keep_recent]
    recent = session["messages"][-keep_recent:]

    transcript = ""
    for m in older:
        transcript += m["role"] + ": " + m["content"] + "\n"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system="""You compress SOC investigation history into a SHORT structured digest.
Output exactly these three sections as short bullet points:

DECISIONS: <containment / escalation decisions made so far>
FACTS: <concrete values established — hostnames, IPs, usernames, timestamps, hashes>
OPEN: <unresolved questions or next investigation steps>

Be brief. NEVER drop a concrete value (IP, hostname, username, hash, alert ID).""",
        messages=[{"role": "user", "content": "Summarize this investigation history:\n\n" + transcript}],
    )
    digest = response.content[0].text.strip()

    session["summary"]  = digest
    session["messages"] = recent
    print(f"  [Session] summarized {len(older)} old msgs -> structured digest "
          f"({len(recent)} recent msgs kept).")
    return session


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── Demo 1: Save & resume across a shift change ────────────────────────────
    print("=" * 60)
    print("DEMO 1: Save & resume - investigation survives a shift change")
    print("=" * 60)

    # Day 1, 02:47 EST — Sarah Chen (Tier-1, night shift) opens the alert.
    s = new_session()
    add_user(s, "Opening alert NG-2027-1142: 8.3 GB outbound transfer from "
                "research-analyst-laptop-04 to 203.0.113.47 at 02:47 EST. "
                "Asset owner Maya Iyer. Where do we start?")
    add_assistant(s, "Suggested first actions: (1) query SIEM for any other "
                     "traffic to 203.0.113.47 in the last 7 days, (2) check "
                     "Maya Iyer's badge swipes and VPN logs, (3) confirm with "
                     "the EDR that the process tree shows the source of the "
                     "transfer. Quarantine of the laptop is reasonable once "
                     "the SIEM query returns.")
    add_user(s, "SIEM shows no prior traffic to 203.0.113.47 from any "
                "NorthGate asset. Maya's badge shows she left at 18:22 EST "
                "and has not returned. No active VPN session.")
    add_assistant(s, "Two leading hypotheses: (A) insider — Maya logged in "
                     "remotely without VPN, unlikely given no VPN session; "
                     "(B) external — credentials or device compromise. "
                     "Recommend quarantining the laptop now and preserving "
                     "memory image before reboot. Shift change at 08:00.")
    save_session(s)

    saved_id = s["id"]
    del s  # pretend the shift ended and Sarah went home

    # Day 2, 08:00 EST — Mike Torres (Tier-2 lead, day shift) resumes the case.
    s2 = resume_session(saved_id)
    print("  Restored investigation history:")
    for m in s2["messages"]:
        print(f"    {m['role']}: {m['content'][:70]}...")

    # ── Demo 2: Fork - explore two hypotheses in parallel ──────────────────────
    print("\n" + "=" * 60)
    print("DEMO 2: Fork - test 'insider' vs 'external APT' hypotheses in parallel")
    print("=" * 60)

    # Branch A: insider-threat hypothesis
    branch_insider = fork_session(s2)
    add_user(branch_insider, "Pursuing the insider hypothesis. Pull Maya's "
                             "HR file: any recent PIP, departure notice, or "
                             "salary discussion in the last 60 days?")
    add_assistant(branch_insider, "HR shows Maya gave verbal notice on Day -3 "
                                  "and her last day is Day +14. No PIP. "
                                  "Recommend interviewing HR business partner "
                                  "and reviewing what data she had legitimate "
                                  "access to.")
    save_session(branch_insider)

    # Branch B: external-APT hypothesis
    branch_apt = fork_session(s2)
    add_user(branch_apt, "Pursuing the external-APT hypothesis. Pull EDR "
                         "memory image and process tree for the upload "
                         "process. Any persistence mechanisms or lateral-"
                         "movement signs?")
    add_assistant(branch_apt, "EDR shows the upload was launched by powershell.exe "
                              "with an encoded command parent, spawned from a "
                              "scheduled task created at 02:42. Persistence "
                              "confirmed. No lateral movement to other hosts yet.")
    save_session(branch_apt)

    print(f"\n  Both branches share parent '{s2['id']}' but diverge after the fork:")
    print(f"    insider ({branch_insider['id']}): {branch_insider['messages'][-1]['content'][:65]}...")
    print(f"    apt     ({branch_apt['id']}): {branch_apt['messages'][-1]['content'][:65]}...")

    # ── Demo 3: Structured summary - keep a long investigation small ───────────
    print("\n" + "=" * 60)
    print("DEMO 3: Structured summary - compress a long investigation")
    print("=" * 60)

    long_s = new_session()
    add_user(long_s,      "Alert NG-2027-1142 opened. 8.3 GB exfil to 203.0.113.47.")
    add_assistant(long_s, "Logged. Source host research-analyst-laptop-04, owner Maya Iyer.")
    add_user(long_s,      "EDR memory image collected. Hash: a1b2c3d4e5f6.")
    add_assistant(long_s, "Memory image preserved at evidence-share/incident-1142/image.raw.")
    add_user(long_s,      "Decision: quarantine the laptop, do NOT disable Maya's account yet.")
    add_assistant(long_s, "Quarantine applied via EDR. Maya's account remains active pending interview.")
    add_user(long_s,      "Legal notified. Counsel says preserve all logs for 7 years.")
    add_assistant(long_s, "Logs from SIEM, EDR, and AD pinned for 7-year retention under hold ID L-2027-44.")

    print(f"\n  Before: {len(long_s['messages'])} messages in history.")
    summarize_session(long_s, keep_recent=2)
    print(f"  After:  {len(long_s['messages'])} messages + 1 structured summary.")
    print("\n  Structured summary:\n")
    for line in long_s["summary"].splitlines():
        print(f"    {line}")
    save_session(long_s)
