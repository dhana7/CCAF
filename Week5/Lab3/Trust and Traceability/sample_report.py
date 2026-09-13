"""
sample_report.py — A small mock quarterly report (one statement per line).

Each line is intentionally short so we can show source line numbers as a
clean form of provenance. Some lines contain compliance issues seeded so
the reviewer has something to find.
"""

# Each item is one statement / one line of the report.
REPORT_LINES = [
    "AcmeCorp Quarterly Report — Q2 FY26.",
    "Total revenue for the quarter was $42.0M.",
    "Operating margin held steady at 18%.",
    "Revenue from the new APAC region rose 200% with no comparable explanation.",
    "The company repurchased 1.2M shares during the quarter.",
    "Cash and equivalents stood at $112M at quarter end.",
    "Forward-looking statements include uncertain outcomes.",
    "The board approved a 5% dividend increase, effective next quarter.",
    "Material related-party transactions not detailed.",
    "No going-concern issues were identified by management.",
]


def get_numbered_report() -> str:
    """Return the report with explicit line numbers, ready for the model."""
    return "\n".join(f"{i+1}: {line}" for i, line in enumerate(REPORT_LINES))


def get_quote(line_number: int) -> str:
    """Look up the original quote for a given line number (1-indexed)."""
    idx = line_number - 1
    if 0 <= idx < len(REPORT_LINES):
        return REPORT_LINES[idx]
    return ""