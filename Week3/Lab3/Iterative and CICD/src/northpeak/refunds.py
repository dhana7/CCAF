"""Refund eligibility and amounts for NorthPeak Outfitters."""

from __future__ import annotations

# A return is eligible within this many days of delivery.
RETURN_WINDOW_DAYS = 30

# Exercise 1 (TDD loop): opened items incur a 15% restocking fee.
RESTOCKING_FEE_RATE = 0.15


def within_return_window(days_since_delivery: int) -> bool:
    """Return True if a return is still inside the 30-day window."""
    if days_since_delivery < 0:
        raise ValueError("days_since_delivery must not be negative")
    return days_since_delivery <= RETURN_WINDOW_DAYS


def refund_amount(price: float, days_since_delivery: int, opened: bool = False) -> float:
    """Return the refund amount for a returned item.

    Full price within the window; 0.0 outside it. Opened items within the
    window incur a 15% restocking fee. `opened` defaults to False so every
    pre-existing call/test is unaffected (Exercise 1 -- see CLAUDE.md's
    "Backward compatibility" rule).
    """
    if price < 0:
        raise ValueError("price must not be negative")
    if not within_return_window(days_since_delivery):
        return 0.0
    if opened:
        return round(price * (1 - RESTOCKING_FEE_RATE), 2)
    return round(price, 2)
