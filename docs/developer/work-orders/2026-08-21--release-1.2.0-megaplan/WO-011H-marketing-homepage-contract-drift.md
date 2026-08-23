# WO-011H — Marketing homepage contract drift closure

Status: `REGRESSION_CLOSED_LOCAL`
Phase: `09`
Ledger rows: none advanced
Promotion: `NOT_REQUESTED`

## Intent

Close the stale story-test contract found by the wider `WO-003E` regression
without restoring retired service-led claims or changing the governed homepage.

## Resolution

- The homepage story contract follows the actual trust-led sequence in
  `marketing/src/app/page.tsx`.
- `ServicesGrid` is explicitly absent. The old six-card claim surface is not
  silently remounted.
- The expected hero is `Проверьте подключение до оплаты`; the retired
  YouTube/TikTok/ChatGPT one-button claim is explicitly rejected.
- `marketing/README.md` names the real route owner and current section sequence
  instead of a nonexistent `homepage.tsx`.

## Proof

- Marketing story contracts: `PASS`, `6/6`.
- Full adjacent API/marketing/copy regression: `PASS`, 48 tests plus 4
  subtests. Existing `datetime.utcnow()` deprecation warnings remain outside
  this slice.
- No application source, public copy registry, external surface or release
  state changed.

Evidence:
`evidence/011H-marketing-homepage-contract/011H-marketing-homepage-contract.json`.
