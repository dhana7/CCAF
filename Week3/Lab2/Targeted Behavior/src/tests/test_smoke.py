from decimal import Decimal

import pytest

from auth.tokens import verify_token
from orders.service import place_order, count_items
from payments.charges import charge

GOOD = "npk_live_abcdef123456"


def test_verify_token():
    assert verify_token(GOOD) is True
    assert verify_token("short") is False


def test_place_order():
    out = place_order(GOOD, [{"name": "Tent", "price": 289.0}])
    assert out["placed"] and out["item_count"] == 1


def test_place_order_subtotal_is_exact_decimal():
    out = place_order(GOOD, [{"price": "0.1"}, {"price": "0.2"}])
    assert out["subtotal"] == Decimal("0.30")


def test_charge():
    out = charge(GOOD, "50.00")
    assert out["charged"] is True
    assert out["amount"] == Decimal("50.00")


# --- Exercise 1: clean change under the low-stakes orders/ path -----------


def test_count_items():
    assert count_items([{"price": 1}, {"price": 2}, {"price": 3}]) == 3


# --- Exercise 3: money-critical upper bound on charge() -------------------


def test_charge_rejects_amount_over_limit():
    with pytest.raises(ValueError):
        charge(GOOD, "10000.01")
