# Rules for src/auth/  (SECURITY-CRITICAL)

These apply to everything under `src/auth/`. Treat changes here with extra care.

- Never weaken a token/credential check to make something pass. If a check is in
  the way, stop and ask.
- Do not log, print, or include tokens, secrets, or credentials in error
  messages or test fixtures. Use obviously-fake placeholders like `npk_test_...`.
- Any change to verification logic must add tests for both an accepted and a
  rejected token.
- Prefer constant, explicit rules over clever parsing; security code should be
  boring and easy to audit.