"""
reviewer.py — Run a compliance review pass with Claude.

The reviewer asks the model to emit a JSON list of findings, each of:

    {
      "line": 4,
      "flag": "unusual_change_without_disclosure",
      "confidence": 0.92
    }

We attach the QUOTE ourselves from the line number, so provenance can't
be hallucinated by the model — it always points at a real line of the
real report.
"""

import json
import os
from anthropic import Anthropic

from sample_report import get_quote

MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5")
_client = Anthropic()  # picks up ANTHROPIC_API_KEY from env

# Two slightly different prompts so the two passes are NOT identical.
# Agreement across these two passes = high confidence.
PROMPT_STRICT = (
    "You are a strict compliance reviewer for quarterly financial reports. "
    "Identify lines that may have a compliance issue (missing disclosure, "
    "vague risk language, unusual changes without explanation, undetailed "
    "related-party transactions). "
    "Respond ONLY with a JSON array of objects: "
    '[{"line": int, "flag": str, "confidence": float}]. '
    "confidence is your 0..1 belief that this is a real issue."
)

PROMPT_GENERAL = (
    "You are reviewing a quarterly financial report for anything a regulator "
    "would want to ask about. Focus on disclosure gaps and ambiguous "
    "language. "
    "Respond ONLY with a JSON array of objects: "
    '[{"line": int, "flag": str, "confidence": float}]. '
    "confidence is your 0..1 belief that this is a real issue."
)


def _parse_json_array(text: str) -> list:
    """Tolerant JSON parser — strips ``` fences if present."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Treat parse failure as zero findings rather than crashing the lab.
        return []


def review(report_text: str, mode: str = "strict") -> list[dict]:
    """
    Run one review pass. Returns a list of findings, each with the quote
    attached locally so provenance can't be hallucinated.

    Parameters
    ----------
    report_text : str
        Numbered report (use sample_report.get_numbered_report()).
    mode : "strict" or "general"
        Which prompt to use. Two different prompts → two independent passes.
    """
    system_prompt = PROMPT_STRICT if mode == "strict" else PROMPT_GENERAL

    response = _client.messages.create(
        model=MODEL_NAME,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": report_text}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    findings = _parse_json_array(text)

    # Attach the quote from our own data — NEVER trust the model to copy it.
    cleaned = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        line = f.get("line")
        if not isinstance(line, int):
            continue
        quote = get_quote(line)
        if not quote:
            continue  # line number out of range
        cleaned.append({
            "line": line,
            "quote": quote,
            "flag": str(f.get("flag", "unspecified")),
            "confidence": float(f.get("confidence", 0.0)),
        })
    return cleaned