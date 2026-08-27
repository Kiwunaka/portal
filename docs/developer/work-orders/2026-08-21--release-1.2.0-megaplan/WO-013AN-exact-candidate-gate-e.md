# WO-013AN — Exact candidate.3 Gate E decision

Status: `LOCALLY_PROVED_EXACT_CANDIDATE_DEVICE_BLOCKED_I3`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `08`, decision replay in Phase `11`
Row: `REL_GATE/GATE-E`
Candidate: `pokrov-1.2.0-candidate.3`
Production/external mutation: `NONE`

## Outcome

Evaluate Gate E against the frozen candidate platform/client/Core tuple. The
exact current-origin aggregate passes the complete local release gate,
production frontend builds, Playwright `88/88`, automated accessibility,
responsive and static-budget checks. Controlled exact-source API performance
also passes: health p95 is `42.5337 ms <= 100 ms` and public catalog p95 is
`43.3626 ms <= 200 ms`.

A fresh exact-source browser smoke confirms the unauthenticated cabinet entry
at desktop `1440x1000` and mobile `390x844`: the page is non-blank, identity
and truth-first copy are correct, the primary Telegram button is visible and
enabled, no framework overlay or console warning/error appears, and the mobile
layout has no horizontal overflow. The local recovery route also renders its
distinct recovery state without an external submission.

This does not prove authenticated journeys, physical TalkBack/Narrator and OS
scaling, exact-device performance, comparable artifact-size regression,
20-sample browser-lab performance, live support upload/recovery, RU-origin or
post-promotion behavior. Gate E therefore returns `BLOCKED` with no new
candidate defect and remains at local `I3`.

## Exact candidate result

| Requirement | Result | Exact boundary |
|---|---|---|
| Truth-first UX and product path | `PASS_EXACT_CANDIDATE_SOURCE_LOCAL` | Exact aggregate and fresh unauthenticated render expose current login availability and do not manufacture a protected/authenticated state. |
| Responsive desktop/mobile | `PASS_EXACT_CANDIDATE_SOURCE_LOCAL` | Production builds, automated responsive checks and fresh 1440/390-pixel renders pass; mobile scroll width equals viewport width. |
| Diagnostics, support and recovery | `PASS_EXACT_CANDIDATE_SOURCE_LOCAL_RUNTIME_BLOCKED` | Candidate source contracts and recovery presentation pass; exact-device upload, transport recovery and operator readback remain unrun. |
| Accessibility and motion | `PASS_AUTOMATED_EXACT_CANDIDATE_SOURCE_MANUAL_DEVICE_BLOCKED` | Critical-route axe, keyboard/tab and reduced-motion automation pass; physical screen readers, OEM text scale and Windows OS scaling remain manual. |
| Performance budgets | `PARTIAL_EXACT_CANDIDATE_SOURCE` | Controlled API and local static stop budgets pass; candidate-device, comparable-artifact, browser-lab, authenticated and post-promotion budgets remain open. |

## Fresh rendered verification

On detached exact platform source
`eafaca3e64c0619dea7f58fc9c430682b4520559`:

- dependency install: `392` packages, success;
- production WebApp build: `40` static routes, success;
- in-app browser desktop `1440x1000`: correct title and meaningful entry
  screen, zero console warnings/errors;
- in-app browser mobile `390x844`: no horizontal overflow, zero console
  warnings/errors;
- primary login control: visible and enabled;
- recovery route: distinct `Восстановить доступ` state rendered without a
  form submission or production authentication.

The fresh render host used Node `24.15.0` while the package declares
`22.14.x`. It is therefore a visual/interaction smoke only, not comparable
performance evidence. The retained WO-013AH exact-candidate aggregate remains
the production-build/E2E authority.

Private screenshots remain outside the repository under
`E:\POKROV-tools\release-evidence\1.2.0-candidate3-gate-e-2026-08-27`:

- desktop SHA-256:
  `63c8316a7d836a2a353dbbba56a0172087000b912ae850285dd1c97b1a1990a9`;
- mobile SHA-256:
  `b82df6c526b8b37df5954ed514f5a8d720322662206e6b142ba4a22647ac34aa`.

## Decision boundary

Gate E is `BLOCKED`, not `FAIL`. No candidate source defect requires a Gate E
replacement change. Candidate.3 remains overall `NO_GO` because Gate B already
contains one deterministic frozen-source failure. Automated axe does not
replace physical TalkBack/Narrator, and a local build does not replace
candidate-device or post-promotion performance.

No login, external form/message, entitlement, payment, deploy, public asset,
stable pointer or Gate G mutation occurred.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013AN-gate-e-test-evidence.json` | `aea8d5d1949eb36777b2bb0a44cc02785ba345e7710cd8075954f66091a4a695` |
| `013AN-gate-e-decision.json` | `fd27c886e702dacab94410b86b0e86b70efb55ebd13ab4011a050a876f1a9d6f` |

## Ledger decision

`REL_GATE/GATE-E` remains `I3`; its status becomes
`LOCALLY_PROVED_EXACT_CANDIDATE_DEVICE_BLOCKED`. `REL/PERF-001` and
`FE_PR/PR-09` receive the same exact-candidate ceiling without advancing.
`FE_PR/PR-10` is corrected from stale `BLOCKED` wording to exact-candidate
`NO_GO` after Gate B. Distribution remains `I4=4`, `I3=312`, `I2=19`,
`I1=41`, `I0=1`.

## Next action

For a replacement candidate, retain authenticated cabinet and client journeys,
physical Android TalkBack/OEM/text-scale plus Windows Narrator/OS-scaling,
candidate-device and comparable-artifact budgets, 20-sample browser-lab
performance, support upload/recovery and authorized RU-origin. Repeat Gate E
after the Gate B fix and required hosted checks land; then rerun Gate F.
