import pytest

from northpeak.refunds import within_return_window, refund_amount


# --- Official baseline suite (6 tests, all green before Exercise 1) -------


def test_within_window_boundary():
    assert within_return_window(0) is True
    assert within_return_window(30) is True
    assert within_return_window(31) is False


def test_full_refund_within_window():
    assert refund_amount(100.0, 10) == 100.0


def test_full_refund_at_window_edge():
    # Day 30 is the last day inside the 30-day window: still a full refund.
    assert refund_amount(100.0, 30) == 100.0


def test_no_refund_after_window():
    assert refund_amount(100.0, 45) == 0.0


def test_no_refund_just_outside_window():
    # Day 31 is the first day outside the window: refund is 0.
    assert refund_amount(100.0, 31) == 0.0


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        refund_amount(-1.0, 5)
    with pytest.raises(ValueError):
        within_return_window(-1)


# --- Exercise 1: restocking-fee rule, written FIRST (red), then green -----


def test_opened_item_restocking_fee():
    # 15% restocking fee on an opened item still within the window.
    assert refund_amount(100.0, 10, opened=True) == 85.0


def test_opened_item_outside_window_still_zero():
    assert refund_amount(100.0, 45, opened=True) == 0.0
