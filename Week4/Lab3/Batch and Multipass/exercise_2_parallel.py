"""Exercise 2 (starter) - Parallel processing for throughput.

Run:  python exercise_2_parallel.py

The work is I/O-bound (waiting on the API), so a thread pool overlaps the waits
and finishes a burst of headlines far faster than one at a time. Your job:
implement run_parallel() with a ThreadPoolExecutor, preserving input order, then
compare sequential vs parallel wall-clock.

NOTE: this makes real API calls. The sequential pass runs immediately (verifying
your key and SDK); the parallel comparison runs once you implement run_parallel().
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client():
    from anthropic import Anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


HEADLINES = [
    "Helix Robotics beats earnings expectations, shares jump.",
    "Regulators open probe into Helix Robotics data practices.",
    "Helix Robotics names new chief financial officer.",
    "Analysts downgrade Helix Robotics on slowing growth.",
    "Helix Robotics unveils new warehouse automation line.",
    "Helix Robotics quarterly revenue in line with estimates.",
    "Lawsuit alleges safety defects in Helix Robotics products.",
    "Helix Robotics partners with major retailer for rollout.",
]

PROMPT = ("Classify sentiment toward the company as one of: positive, neutral, "
          "negative. One word.\n\nHeadline: {h}")


def classify(client, headline):
    msg = client.messages.create(
        model=MODEL, max_tokens=20,
        messages=[{"role": "user", "content": PROMPT.format(h=headline)}],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def run_sequential(client, headlines):
    t0 = time.time()
    out = [classify(client, h) for h in headlines]
    return out, time.time() - t0


# =====================================================================
# TODO (Exercise 2): implement run_parallel().
#
# Use ThreadPoolExecutor(max_workers=workers) in a `with` block and call
# pool.map(...) so results come back in INPUT ORDER (no manual id-tagging):
#     with ThreadPoolExecutor(max_workers=workers) as pool:
#         out = list(pool.map(lambda h: classify(client, h), headlines))
# Time the whole block and return (out, elapsed_seconds) - same shape as
# run_sequential() above, so main() can compute the speedup.
# =====================================================================
def run_parallel(client, headlines, workers=5):
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        out = list(pool.map(lambda h: classify(client, h), headlines))
    return out, time.time() - t0


def main():
    client = get_client()
    print(f"Model: {MODEL}")

    seq, seq_t = run_sequential(client, HEADLINES)
    print(f"\nSequential: {seq_t:.1f}s -> {seq}")

    par, par_t = run_parallel(client, HEADLINES, workers=5)
    print(f"Parallel  : {par_t:.1f}s -> {par}")

    if par_t > 0:
        print(f"\nSpeedup: {seq_t / par_t:.1f}x")
    print("\nTip: tune `workers` to your rate limits — too many will hit 429s.")


if __name__ == "__main__":
    main()
