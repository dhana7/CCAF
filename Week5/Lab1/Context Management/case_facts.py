"""Persistent case facts that survive every turn of a long session."""


class CaseFacts:
    """A tiny key-value store of facts that must survive every turn."""

    def __init__(self):
        self._facts: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        """Pin a fact. Overwrites any earlier value for the same key."""
        self._facts[key] = value

    def get(self, key: str) -> str | None:
        """Read a pinned fact back (handy when experimenting in the REPL)."""
        return self._facts.get(key)

    def as_system_block(self) -> str:
        """
        Render the facts as a chunk of text appended to the system prompt
        every turn. Keep it short - every token here is paid for on every
        API call.
        """
        if not self._facts:
            return ""
        lines = ["[CASE FACTS - these are confirmed and must be preserved]"]
        for k, v in self._facts.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)
