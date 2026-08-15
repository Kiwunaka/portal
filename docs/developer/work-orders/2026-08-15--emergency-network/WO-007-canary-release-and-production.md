# WO-007 — Canary, Release And Production

## Metadata

| Field | Value |
| --- | --- |
| WO id | `WO-007-canary-release-and-production` |
| Title | Exact emergency-network candidate is promoted, monitored and reversible |
| Ceremony | `release_wo` |
| WO status | `closed_stable_direct_with_manual_gates` |
| Orchestrator | `/root` |
| Repository lane | `mixed` |
| Working branch or worktree | exact reviewed platform/client promotion commits |
| Intended promotion state | platform `master`, client `main`, stable direct release and production deploy |
| Created / updated | `2026-08-15` |

## Goal

Promote the exact green platform/client candidate, deploy backend/admin safely,
publish Android/Windows artifacts when client binary changes, and roll out the
feature to entitled RU cohorts behind reversible 5%→25%→100% gates.

## Non-Goals

- Converting synthetic evidence into a real-БС claim.
- 100% rollout while the owner manual gate is absent.
- Store/iOS/macOS release or trusted Windows signing procurement.

## Write Scope

- release metadata and exact candidate evidence
- rollout configuration and operator runbook
- platform/client canonical docs affected by final behavior
- this wave status/closure

## No-Touch Scope

- production promotion before WO-001..WO-006 exact gates pass
- destructive database reset or release-history rewrite
- raw emergency credentials in public release notes

## Authority Anchors

Publishing/signing guide, deployment runbook, release handoff owners, WO-003
rollback control, WO-006 exact evidence and owner manual gate.

## Acceptance Oracle

- Authoritative boundary: deployed current-origin runtime plus exact public client candidate.
- Success observation: 5% operator/RU cohort sees the signed catalog and can
  connect; health/error/staleness thresholds remain green; rollback removes the
  feature without client reinstall. The same gates repeat at 25%.
- 100% condition: exact real Russian LTE/БС owner evidence is PASS and no canary
  rollback threshold is breached. Otherwise rollout remains capped and status
  is `partial`, not falsely complete.
- Negative cases: catalog probe collapse, signature/auth error, crash/reconnect
  regression, DNS leak, wrong exit or support incident rate above threshold
  automatically halt promotion and retain the last good state.
- Proof mechanism: release gates, deployment dry-run/verify, current-origin smoke,
  rollout metrics and rollback drill.
- Triggered proof blocks: all release WO blocks including manual and promotion evidence.

## Docs Impact

Platform product/API/system/monitoring/deployment owners; client product,
bootstrap and release-readiness owners; exact handoff metadata and this wave.

## Validation And Evidence

Focused/full platform and client gates, exact Android/Windows builds when
required, GitHub digest/signing checks, deploy verify, signed catalog smoke,
5%/25% metrics and rollback record. Real LTE remains owner evidence.

## Status And Handoff

- Current WO status: `closed_stable_direct_with_manual_gates`
- Dependencies: WO-003, WO-006
- Platform emergency source is pushed through `c567787`; client runtime source
  is pushed through `43af4a6`, with release metadata on `6f52ad6`.
- Public stable direct release `v1.0.10` is published, non-draft and
  non-prerelease. Eight public assets match local staging by exact size and
  SHA-256. Android has four production-signed ABI variants; Windows setup and
  portable artifacts retain the explicit unsigned SmartScreen warning.
- Production release handoff, backend restart and static-site deploy passed.
  Caddy plus portal API, bot, helpbot, feedbackbot and worker are active;
  five repeated subscription reads passed; both SRS rule sets are valid.
- Brain-signed authenticated and anonymous client catalogs expose Android and
  Windows `1.0.10` on the stable channel; the retained runtime smoke is PASS.
  Public update readback returns `recommended` with the exact `v1.0.10` URL for
  Android `1.0.9`, and `none` for an already-current `1.0.10` client.
- Owner directed a stable direct release instead of a beta/canary channel.
  Percentage canary staging is `SKIPPED_BY_OWNER`; catalog rollback and the
  previous `1.0.9` public release remain available. This does not convert the
  absent Russian LTE proof into PASS or authorize a real-BS badge.
- Exact Huawei/RU-LTE, Windows clean TUN/DNS without Hiddify and the controlled
  synthetic firewall lab remain explicit post-release manual gates.
