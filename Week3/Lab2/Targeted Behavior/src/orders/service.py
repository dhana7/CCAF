"""Order placement for NorthPeak."""

from __future__ import annotations

from decimal import Decimal

from auth.tokens import verify_token  # migrated from verify_token_v1 (Ex 2)

CENTS = Decimal("0.01")


def place_order(token: str, items: list[dict]) -> dict:
    """Place an order if the caller's token is valid."""
    if not verify_token(token):
        raise PermissionError("invalid token")
    subtotal = sum((Decimal(str(i["price"])) for i in items), Decimal("0")).quantize(CENTS)
    return {"placed": True, "item_count": len(items), "subtotal": subtotal}


def count_items(items: list[dict]) -> int:
    """Return the number of items in an order (Exercise 1)."""
    return len(items)
