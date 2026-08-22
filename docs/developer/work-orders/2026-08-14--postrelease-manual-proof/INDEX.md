# POKROV Post-release Manual Proof

Document class: `EVIDENCE`

Retained status for `v1.0.4-beta.1`: `READY`

This queue is preserved for the named old bytes. Current 1.2.0 manual gates are
owned by the 1.2.0 megaplan and require fresh exact-candidate evidence.

This follow-up preserves the owner-deferred proof that was intentionally moved
out of the completed `v1.0.4-beta.1` release goal on 2026-08-14. It does not
reopen that goal and does not downgrade the published prerelease.

## Queue

| Work order | Scope | Status |
| --- | --- | --- |
| [WO-001](WO-001-exact-runtime-and-owner-paths.md) | Huawei endurance/uplink, Windows isolated runtime, Telegram journey, RU-origin and offline keystore copy | `READY` |

## Resume Rule

Resume from `WO-001`. Keep every unexecuted owner-controlled check as
`MANUAL_OWNER_TEST`; a skip, prior candidate result or code-level test is not a
runtime `PASS` for the exact target.

## Relationship To The Closed Release Goal

The owner accepted the direct Android+Windows release goal as complete after
publication and production cutover of `v1.0.4-beta.1`. The six checks in this
wave are deliberate next-task hardening and stronger-claim evidence. They are
not retroactive blockers for availability of that prerelease.
