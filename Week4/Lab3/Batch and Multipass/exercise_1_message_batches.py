"""Exercise 1 (starter) - Classify a workload with the Message Batches API.

Run:            python exercise_1_message_batches.py
Fetch later:    python exercise_1_message_batches.py --fetch <batch_id>

Batches trade latency for cost and scale: submit many requests, let them process
asynchronously, then collect results by custom_id. Your job: complete two pieces
- build_requests() (one {custom_id, params} per headline) and the polling loop
inside main() (retrieve, print status, break on "ended", sleep, bail out past the
deadline). fetch_results() is provided.

NOTE: this exercise makes real API calls and submits a real batch. Complete BOTH
TODOs before running so you don't submit a batch you then can't poll.
"""

import os
import sys
import time

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def get_client():
    from anthropic import Anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first (see .env.example).")
    return Anthropic()


HEADLINES = [
    "Helix Robotics beats earnings expectations, shares jump 12%.",
    "Regulators open probe into Helix Robotics data practices.",
    "Helix Robotics names new chief financial officer.",
    "Analysts downgrade Helix Robotics on slowing growth.",
    "Helix Robotics unveils new warehouse automation line.",
    "Helix Robotics quarterly revenue comes in line with estimates.",
    "Lawsuit alleges safety defects in Helix Robotics products.",
    "Helix Robotics partners with major retailer for nationwide rollout.",
]

PROMPT = ("Classify the sentiment of this news headline toward the company as "
          "exactly one of: positive, neutral, negative. One word.\n\n"
          "Headline: {h}")


# =====================================================================
# TODO (Exercise 1, piece 1 of 2): build_requests().
#
# Return a list with one dict per headline. Each dict has:
#   "custom_id": a STABLE unique id, e.g. f"headline-{i}"   (join results by this)
#   "params":    a dict mirroring messages.create(): model, max_tokens, messages
#                where messages = [{"role": "user", "content": PROMPT.format(h=h)}]
# Use enumerate(headlines) so each headline gets its own custom_id.
# =====================================================================
def build_requests(headlines):
    return [
        {
            "custom_id": f"headline-{i}",
            "params": {
                "model": MODEL,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": PROMPT.format(h=h)}],
            },
        }
        for i, h in enumerate(headlines)
    ]


def fetch_results(client, batch_id):
    for entry in client.messages.batches.results(batch_id):
        if entry.result.type == "succeeded":
            text = "".join(b.text for b in entry.result.message.content
                           if b.type == "text").strip()
            print(f"{entry.custom_id}: {text}")
        else:
            print(f"{entry.custom_id}: ERROR ({entry.result.type})")


def main():
    client = get_client()
    print(f"Model: {MODEL}")

    batch = client.messages.batches.create(requests=build_requests(HEADLINES))
    print("submitted batch:", batch.id, "| status:", batch.processing_status)

    deadline = time.time() + 600  # wait up to 10 minutes in this demo
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        print("status:", batch.processing_status, "| counts:", batch.request_counts)
        if batch.processing_status == "ended":
            break
        if time.time() > deadline:
            print(f"\nStill processing after 10 minutes. Fetch results later with:\n"
                  f"  python exercise_1_message_batches.py --fetch {batch.id}")
            return
        time.sleep(10)

    print("\nResults:")
    fetch_results(client, batch.id)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--fetch":
        fetch_results(get_client(), sys.argv[2])
    else:
        main()
