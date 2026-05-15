# Public Beta Release Handoff

Generated: 2026-05-15

Status: `GO`

GO for public beta publication.

## Scope

- Platform: POKROV public beta for Android APK and Windows EXE outside app stores.
- Distribution: GitHub Releases for Android APK and Windows EXE, install guide at `https://pokrov.space/install/`.
- Version: `0.2.0-beta.1+20260508`.
- Store publishing, Apple release, appcast, MSIX, ZIP first-layer distribution, and trusted Windows signing are outside this release.
- Telegram channel launch copy may be prepared, but it must not be posted by automation.

## Evidence

- Current-origin quick gate: `docs/audit-artifacts/release-gate-local-quick-2026-05-15.md` -> PASS.
- Current-origin full gate equivalent: `docs/audit-artifacts/release-gate-full-local-2026-05-15.md` -> PASS.
- Brain-origin gate: `docs/audit-artifacts/release-gate-brain-2026-05-15.md` -> PASS.
- Static deploy/public HTTPS smoke: `docs/audit-artifacts/brain-static-public-smoke-2026-05-15.md` -> PASS.
- Runtime app-download smoke: `docs/audit-artifacts/brain-runtime-app-download-smoke-2026-05-15.json` -> PASS.
- APK/EXE/docs reachability: `docs/audit-artifacts/staged-client-apps-reachability-2026-05-15.md` -> PASS.
- Email and Lava.top post-deploy probe: `docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json` -> PASS.
- Paid checkout aggregate evidence: `docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json` -> PASS.
- Live email runtime status: `docs/audit-artifacts/live-email-auth-status-brain-2026-05-15.json` -> PASS.
- Live payment provider status: `docs/audit-artifacts/live-payment-provider-status-brain-2026-05-15.json` -> PASS.
- Android physical audit: operator-attested complete and OK for this beta pass.
- Windows unsigned installer risk: accepted for this outside-store beta pass.
- RU-origin: skipped by operator; do not claim RU-origin verification.

## Safe Public Claims

- POKROV is open in public beta for Android and Windows outside app stores.
- Android APK and Windows EXE are available from GitHub Releases through the POKROV install page and cabinet download surface.
- Windows may show an unsigned-app or SmartScreen warning in this beta.
- Email sign-in, recovery, and paid access-key delivery are enabled.
- Paid checkout uses Lava.top only.
- Telegram Stars and legacy payment providers are not public checkout routes for this beta.

## Unsafe Claims

- Do not claim app-store publication.
- Do not claim trusted Windows signing.
- Do not claim Apple release availability.
- Do not claim RU-origin verification.
- Do not publish raw payment ids, callback payloads, Telegram initData, subscription URLs, private email addresses, or secrets.

## Operator Handoff

- Public surfaces to verify after deploy: `https://pokrov.space/`, `https://pokrov.space/install/`, `https://app.pokrov.space/`, `https://api.pokrov.space/api/health`.
- Telegram announcement remains prepared-only unless the owner explicitly posts it.
- If a launch-critical post-deploy check regresses, roll back static assets or runtime release claims and keep the public claims above narrowed to the last green evidence.
