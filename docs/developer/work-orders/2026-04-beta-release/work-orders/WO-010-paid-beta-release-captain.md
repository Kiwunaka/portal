# WO-010 Paid Beta Release Captain

Status: draft
Lane: mixed

## Scope

Own final paid beta gate report, onboarding, user communications, go/no-go, deploy checklist, rollback checklist, and support checklist.

This WO runs last after W01-W09 evidence exists.

## Required Outputs

- final release gate report
- paid beta onboarding text
- tester instructions
- Telegram announcement set
- artifact/download status
- go/no-go decision
- deploy checklist
- rollback checklist
- support checklist
- beta signoff

## Signoff Artifact

Create or update a final signoff with:

- status: beta-ready, beta-ready with accepted limitations, or blocked
- Android and Windows artifact status, signing, runtime verification, public approval, and notes
- core flow evidence: trial start, redeem key, payment/checkout, Telegram bonus, Android connect, Windows connect, cabinet ticket, admin user management, node metrics
- gate evidence: backend, marketing, webapp, admin, client, Android audit, UI visual smoke, copy guardrails, link checks
- accepted limitations
- blockers
- rollback plan
- tester instructions
- support instructions
- final decision

## Required User Communications

- Telegram paid beta announcement
- payment opened announcement
- payment paused/maintenance message
- Android internal APK warning
- Windows unsigned warning
- support instruction message
- known limitations message
- beta full/closed waitlist message
- post-beta thanks/update message

## Paid Beta User Onboarding

Beta users must receive:

- what POKROV beta is
- what platforms are available
- Android internal APK status unless audit/signing pass
- Windows unsigned status if signing is missing
- how to pay
- how to activate key/access
- where to download
- how to contact support
- what data to include in bug reports
- known limitations
- refund/manual support policy

Do not onboard more than 25 active paid beta users without explicit orchestrator approval.

## Paid Beta Support Policy

Primary support:

- cabinet ticket

Fallback:

- Telegram support

Response target:

- best-effort within 24h

Admin visibility required:

- user identity
- payment status
- subscription/access state
- device list
- platform
- app version
- route mode
- last connection attempt
- latest safe diagnostics
- ticket history

Support must not require users to paste raw configs or secrets.

## Go / No-Go

Beta-ready:

- all P0 gates green
- payment flow verified
- support flow verified
- admin can manage users/payments/access
- downloads gated
- emergency switches available
- docs and copy reflect beta limitations

Beta-ready with accepted limitations:

- core flows green
- noncore gates classified
- Android public/store cutover blocked but internal APK acceptable
- Windows unsigned warning accepted
- no fake modules or fake claims

Blocked:

- payment creates wrong access
- duplicate payment extends twice
- users cannot activate access
- managed profile delivery broken
- both Android and Windows beta connect paths blocked
- admin auth broken
- support ticket flow broken
- production deploy failed
- rollback unknown
- public UI contains unsafe claims or fake availability

## Validation

```powershell
python scripts/release_gate_check.py --output docs/audit-artifacts/release_gate_report.md
```

With client platform gates only when prerequisites are intentionally present:

```powershell
set ANDROID_AUDIT_SERIAL=<physical-device-serial>
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab --output docs/audit-artifacts/release_gate_report.md
```

## Handoff Format

- What I checked
- What I found
- What I changed
- How I verified
- What remains / risk
- Final decision
