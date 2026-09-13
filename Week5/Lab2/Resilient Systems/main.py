"""
main.py - Lab 5.2: Resilient Claims Processing Pipeline.

The coordinator walks each claim through three subagents:

    intake  ->  validation  ->  adjudication

What this demonstrates:
  * Errors propagate cleanly - every stage returns a StageResult and the
    coordinator decides how to react. No silent drops.
  * A scratchpad records every finding for audit + crash recovery.
  * Re-running skips claims already in `done` or `failed` state.

Run with:
    python main.py

To see crash recovery: press Ctrl+C mid-run, then run again.
To reset: delete `scratchpad.json` and run again.
"""

from dotenv import load_dotenv

from agents import run_intake, run_validation, run_adjudication
from sample_claims import CLAIMS
from scratchpad import Scratchpad

load_dotenv()


def process_claim(claim: dict, pad: Scratchpad) -> str:
    """
    Walk one claim through all three stages.

    Returns the final status string: 'done' or 'failed'.
    The coordinator is the only place that knows how to react to a
    StageResult.ok == False - subagents themselves never raise.
    """
    claim_id = claim["claim_id"]
    stages = [
        ("intake", run_intake),
        ("validation", run_validation),
        ("adjudication", run_adjudication),
    ]

    print(f"[CLAIM {claim_id}] ", end="", flush=True)

    for stage_name, fn in stages:
        result = fn(claim)
        pad.log(claim_id, stage_name, result.to_dict())

        if result.ok:
            print(f"{stage_name}...ok  ", end="", flush=True)
        else:
            # Error PROPAGATES here - the coordinator logs the exact reason,
            # marks the claim failed, and stops processing further stages.
            print(f"{stage_name}...FAIL ({result.error})")
            pad.mark_failed(claim_id, f"{stage_name}: {result.error}")
            return "failed"

    print()  # newline after all stages succeed
    pad.mark_done(claim_id)
    return "done"


def main():
    pad = Scratchpad("scratchpad.json")
    print("Pipeline starting. State file: scratchpad.json\n")

    done_count = 0
    failed_count = 0
    skipped_count = 0

    for claim in CLAIMS:
        status = pad.status(claim["claim_id"])

        # ----- Crash recovery: skip claims already finished. -----
        if status in ("done", "failed"):
            print(f"[CLAIM {claim['claim_id']}] (already {status}, skipping)")
            skipped_count += 1
            continue

        final = process_claim(claim, pad)
        if final == "done":
            done_count += 1
        else:
            failed_count += 1

    # ----- Summary -----
    print("\n" + "-" * 60)
    print(f"SUMMARY  done: {done_count}   failed: {failed_count}   "
          f"skipped: {skipped_count}")
    print("Open scratchpad.json to inspect every finding.")
    print("-" * 60)


if __name__ == "__main__":
    main()
