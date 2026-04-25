# Public Launch Runbook

Status: draft

## D-14 to D-10: Discovery

- Create wave.
- Capture dirty baseline.
- Run R01-R10.
- Terminate research contexts.
- Synthesize only written evidence.
- Create public beta scope, risk register, debt register, and release gate plan.

## D-10 to D-7: Implementation Foundation

- W01 design foundation.
- W05 backend foundation.
- W09 security baseline.
- Payment provider decision.
- Public beta scope freeze.

## D-7 to D-4: Surface Implementation

- W02 marketing/checkout/install/legal.
- W03 cabinet.
- W04 admin.
- W06 payments/support.
- W07 client.
- W08 infra.

## D-4 to D-2: Release Candidate

- Run focused tests.
- Produce artifacts and checksums.
- Run Android audit when physical device is available.
- Verify Windows artifact metadata.
- Verify emergency controls.
- Verify payment webhook behavior.
- Verify support ticket flow.
- Verify admin real modules.

## D-2 to D-1: Final Gate

- Run full release gate.
- Run visual smoke.
- Run live read-only checks.
- Run low-value payment test only when authorized.
- Update canonical docs.
- Prepare Telegram/public communications.
- Prepare rollback.
- Record go/no-go.

## D-Day

- Deploy only after public beta signoff.
- Verify API, marketing, checkout, cabinet, downloads, payment webhook, managed profile, support ticket, admin, and bot surfaces.
- Publish Telegram announcement only after evidence supports the public claim.
- Monitor first hour every 10 minutes.

## Rollback Triggers

- payment double grants
- failed entitlements
- API outage
- managed profile outage
- payment webhook storm
- unsafe Android local control issue
- admin auth issue
- leaked secrets/configs
- severe node outage
- support overload with broken access

