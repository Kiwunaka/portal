# Owner decisions — 2026-09-07

Authority: owner's direct response in this task on 2026-09-07. This changes
the pending choices in NEXT_ACCEPTANCE; old readbacks remain historical.

## Cached profile and rollback — N02/N07

An unreachable API must not prevent connection with the last downloaded VPN
profile. A user on a restricted/allowlisted access network may reach a VPN
server while the control-plane API is blocked. Refresh is opportunistic (on
connection or about every six hours); successful refresh checks the server
revision. API failure is not an entitlement revocation. The owner accepts
up to one day of delayed access expiry while offline.

Implementation uses a bounded offline window, preserves account/profile
binding and the original verification timestamp, and does not extend the
window through retries, restaging or clock rollback. Explicit server denial,
known revocation and logout remain separate from API unavailability. A failed
dataplane probe alone must not destroy the last usable profile. An old profile
never proves a healthy tunnel: route/egress proof remains required.

## Automatic network diagnostics — O03/V02

Keep existing automatic diagnostics; do not require a manually submitted
support bundle for the basic operator view. Add the source access network's
public IP (not the VPN exit), carrier and approximate region for troubleshooting.
This is operational diagnostics, not advertising or sale of data. Reuse
existing ingestion, access controls and retention where applicable; expose
unknown when origin cannot be established. Do not silently label a VPN-exit
observation as the underlying mobile connection. No GPS or exact physical
location was requested.

## Seller/provider — M01

Owner identifies LavaTop as the payment provider and explicitly skips seller
details/receipt confirmation for now: `SKIPPED_BY_OWNER`. No fabricated seller
identity is inserted into public legal text. This skip is not payment/provider
E2E proof and does not authorize real charges, refunds or publication.

## Android

Owner connected the Huawei phone for ADB testing. Fresh readback identifies
manufacturer HUAWEI, model ADA-AL00U, Android 12, SDK 31, arm64-v8a (owner's
spoken Android 13 is superseded by this observed OS version). Device-specific
checks must bind installed bytes and preserve the owner's data. Access is now
available; previous `0 devices` observations are historical.

## GitHub costs — G04/G06

No paid GitHub features at this stage. Paid private-branch protection and
hosted checks that require spending are `SKIPPED_BY_OWNER`. Do not purchase a
plan, increase spending limits, change repository visibility or configure a
paid runner. Existing free/local verification remains applicable. A skipped
hosted job is never CI PASS, and a local suite is not branch enforcement.

Future macOS build spending is mentioned as a later possibility, not an
authorization for a purchase or a macOS build job now. Current production,
signing, candidate-publication and rollout boundaries are unchanged.
