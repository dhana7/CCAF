"""Token verification for NorthPeak services."""

from __future__ import annotations


def verify_token(token: str) -> bool:
    """Return True if the API token is structurally valid.

    Valid tokens start with 'npk_' and are at least 12 characters long.

    NOTE: lab stub — this checks token *shape* only. Real authentication would
    verify a cryptographic signature, expiry, and issuer (e.g. a signed JWT)
    using a constant-time comparison.
    """
    return isinstance(token, str) and token.startswith("npk_") and len(token) >= 12


# verify_token_v1 (DEPRECATED: accepted any 6+ character token) has been
# fully migrated away from and removed here -- see Lab 3.2 Exercise 2,
# which used Plan mode to locate and update every caller (src/orders/service.py,
# src/payments/charges.py) before deleting it. Its last form was:
#
#   def verify_token_v1(token: str) -> bool:
#       return isinstance(token, str) and len(token) >= 6
