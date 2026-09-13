"""
main.py — Lab 5.3: Trust & Traceability for a financial report reviewer.

Run with:
    python main.py

The script:
  1. Loads a small mock financial report.
  2. Runs TWO independent review passes with different prompts.
  3. Buckets the findings into auto_clear / human_review / contested.
  4. Prints every finding with its source line and quote (provenance).
"""

import sys

from dotenv import load_dotenv

from sample_report import get_numbered_report
from reviewer import review
from confidence import bucket, CONFIDENCE_THRESHOLD

# Windows consoles default to cp1252; force UTF-8 so the report's em-dashes
# and ellipses render instead of showing as "?" boxes.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def print_bucket(title: str, items: list[dict], show_disagreement: bool = False):
    print("\n" + title)
    print("-" * len(title))
    if not items:
        print("(none)")
        return
    for item in items:
        if show_disagreement:
            print(
                f"  line {item['line']:>2} : \"{item['quote']}\"\n"
                f"          pass A flag: {item['flag_pass_a']}\n"
                f"          pass B flag: {item['flag_pass_b']}"
            )
        else:
            print(
                f"  line {item['line']:>2} : \"{item['quote']}\"\n"
                f"          flag={item['flag']}  "
                f"confidence={item['confidence']}"
            )


def main():
    report_text = get_numbered_report()
    print("=" * 70)
    print("REPORT UNDER REVIEW")
    print("=" * 70)
    print(report_text)

    print("\nRunning pass A (strict reviewer)…")
    pass_a = review(report_text, mode="strict")
    print(f"  -> {len(pass_a)} finding(s)")

    print("Running pass B (general reviewer)…")
    pass_b = review(report_text, mode="general")
    print(f"  -> {len(pass_b)} finding(s)")

    buckets = bucket(pass_a, pass_b)

    print("\n" + "=" * 70)
    print(f"RESULTS  (confidence threshold = {CONFIDENCE_THRESHOLD})")
    print("=" * 70)
    print_bucket("AUTO-CLEAR (confirmed, high confidence)", buckets["auto_clear"])
    print_bucket("HUMAN REVIEW (low confidence)", buckets["human_review"])
    print_bucket("CONTESTED (the two passes disagreed)",
                 buckets["contested"], show_disagreement=True)

    print("\nDone. Every finding above includes its source line — that's the")
    print("provenance a human reviewer needs to verify in one click.")


if __name__ == "__main__":
    main()