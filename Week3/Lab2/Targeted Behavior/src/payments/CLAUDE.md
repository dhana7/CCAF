# Rules for src/payments/  (MONEY-CRITICAL)

These apply to everything under `src/payments/`. Mistakes here cost real money.

- Always verify the caller token before charging.
- Represent money as `decimal.Decimal`, never `float`.
- Reject non-positive amounts with a clear `ValueError`.
- Never store raw card numbers or secrets in code, tests, or logs.
- Any change to charge logic needs a test covering a successful charge AND a
  rejected one (bad token or bad amount).