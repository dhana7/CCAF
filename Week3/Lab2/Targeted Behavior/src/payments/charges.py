"""Payment charges for NorthPeak."""

from __future__ import annotations

from decimal import Decimal

from auth.tokens import verify_token  # migrated from verify_token_v1 (Ex 2)

CENTS = Decimal("0.01")
MAX_CHARGE_AMOUNT = Decimal("10000")  # Exercise 3: money-critical upper bound


def charge(token: str, amount: Decimal | float | str) -> dict:
    """Charge an amount if the caller's token is valid.

    Raises:
        PermissionError: if the token does not verify.
        ValueError: if the amount is not positive, or exceeds MAX_CHARGE_AMOUNT.
    """
    if not verify_token(token):
        raise PermissionError("invalid token")
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("amount must be positive")
    if amount > MAX_CHARGE_AMOUNT:
        raise ValueError(f"amount exceeds the ${MAX_CHARGE_AMOUNT:,} limit")
    return {"charged": True, "amount": amount.quantize(CENTS)}
