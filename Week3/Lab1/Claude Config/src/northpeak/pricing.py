"""Pricing rules for NorthPeak Outfitters."""

from __future__ import annotations

# Free standard shipping at or above this order subtotal (USD).
FREE_SHIPPING_THRESHOLD = 75.0
STANDARD_SHIPPING = 7.95


def apply_member_discount(subtotal: float, is_member: bool) -> float:
    """Return the subtotal after the 10% member discount, if applicable."""
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    if is_member:
        return round(subtotal * 0.90, 2)
    return round(subtotal, 2)


def shipping_cost(subtotal: float) -> float:
    """Return shipping cost: free at/above the threshold, otherwise flat rate."""
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    return 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING


def order_total(subtotal: float, is_member: bool = False) -> float:
    """Compute the final order total: member discount, then shipping."""
    discounted = apply_member_discount(subtotal, is_member)
    return round(discounted + shipping_cost(discounted), 2)