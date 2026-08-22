# Rules for src/orders/

- Order functions take a caller `token` first and verify it before doing work.
- Money is `decimal.Decimal` USD (never `float`), quantized to 2 decimals at the boundary.
- Return plain dicts that are easy to serialize; no hidden global state.
- Add a test in `src/tests/` for any new order behaviour.