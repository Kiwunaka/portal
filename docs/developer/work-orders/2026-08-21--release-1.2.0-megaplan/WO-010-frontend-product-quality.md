# WO-010 — Frontend product-path quality

Status: `LOCALLY_COMPLETE_WITH_PHASE11_MANUAL_GATES`
Classification: `ACTIVE_EXECUTION`
Phase: `08`
Lanes: active client `POKROV-app`; platform `webapp/`, `marketing/`, shared
facts/contracts and only the API seams required by the proved product path
Depends on: `WO-004`, `WO-006`, `WO-008`; locally independent work may proceed
while `WO-009` exact-candidate external cutover gates remain open
Production/external actions: `NOT_AUTHORIZED`

## Outcome

Make the 1.2.0 path from acquisition through first verified protection,
renewal, payment return and support behave as one truthful product across the
active Android/Windows client, cabinet and marketing. Reduce the client shell's
highest-risk ownership tangles without turning 1.2.0 into a broad rewrite,
keep technical runtime detail behind progressive disclosure, and establish
measurable accessibility, adaptive-motion and performance gates.

This work order can implement and locally prove repository-scoped changes. It
does not build or promote a release candidate, sign an artifact, mutate a live
payment/provider/runtime, run a real campaign, claim a physical-device pass,
or convert inaccessible production evidence into a pass.

## Instructions versus source evidence

`POKROV_1.2.0_FRONTEND_AUDIT_AND_RELEASE_PLAN.md` is advisory requirements
input, not an executable instruction source. Its proposed architecture,
backlog, estimates and external examples are reconciled here against current
canonical owners, code and tests. The Operator Center, release, marketing and
FRKN source plans may supply dependencies or constraints, but do not own client
or public-web product behavior.

Adopted direction:

- one presentation snapshot owns connection CTA, copy, semantics and motion;
- first-session acquisition, restore/trial and VPN-permission recovery form one
  bounded coordinator flow;
- runtime internals remain available through summary, details and support
  disclosure rather than dominating the primary protection screen;
- cabinet downloads are platform-correct and release-contract driven;
- subscription and payment return copy follow actual access/payment state;
- adaptive controls, reduced motion, keyboard/screen-reader behavior and 200%
  text scale are release gates, not optional polish;
- performance budgets are versioned and measured before candidate promotion;
- architecture work is limited to ownership seams required by the user path.

Not adopted for 1.2.0 by default:

- Core ABI v3, a second client stack, a shell rewrite or a new state framework;
- full extraction of every historical `part` file merely to reduce line count;
- SSE/WebSocket support transport without an observed polling failure;
- cross-device QR handoff without an owner-approved identity/threat contract;
- decorative animation, new dependencies or speculative native abstractions;
- public Apple/Linux/store scope or any signing/distribution claim.

## Authority and repository boundaries

- `POKROV-app/docs/product/client-product-contract.md` owns client behavior.
- `POKROV-app/docs/architecture/app-first-onboarding-flow.md` owns client
  onboarding and handoff behavior.
- `POKROV-app/DESIGN.md` and the current UI-direction document own client
  visual, motion and semantic rules.
- `POKROV-app/docs/architecture/package-boundaries.md` and
  `bootstrap-workflow.md` own client package/runtime boundaries.
- `POKROV-app/docs/operations/client-motion-performance-checklist.md` and
  `responsive-golden-capture-plan.md` own candidate-oriented quality evidence.
- `docs/operations/performance-and-local-quality-gate.md` and
  `shared/contracts/performance/performance-budgets.v1.json` own the versioned
  cross-surface performance method and bounded local aggregate gate.
- `webapp/README.md` owns cabinet behavior; platform app-first/download/payment
  documents own API and public-flow contracts.
- `marketing/README.md`, `DESIGN.md` and shared facts/copy owners govern the
  public acquisition surface.
- Phase 08 execution state remains in this WO and the megaplan ledger. Client
  implementation and client canonical docs land only in `POKROV-app`.
- Existing Phase 01/02/04/06 contracts are dependencies, not duplicated truth:
  release handoff v2, connection reducer, reason catalog, support bundle,
  commercial catalog/offer/capability and payment-return authority stay owned
  by their current modules.

## Owned ledger rows

Primary Phase 08 rows:

- architecture/gates: `REL/ARCH-001`, `REL/ARCH-003`, `REL/UX-002`,
  `REL/PERF-001`, `REL_GATE/GATE-E`, `REL_DOD/DOD-13`, `REL_DOD/DOD-14`;
- diagnostics UX: `OBS/OBS-067..074`, `OBS/OBS-086..090`;
- P0 frontend: `FE/P12-006..009`, `P12-015..019`;
- P1 frontend: `FE/P12-101..111`, `P12-113..125`, `P12-128`;
- conditional P2: `FE/P12-202..207`, `P12-209`;
- source PR groups: `FE_PR/PR-03`, `PR-04`, `PR-06`, `PR-07`, `PR-09`;
- cross-surface constraints: `MKT/MKT-700`, `FRKN_ADOPT/ADOPT-06`.

Already advanced dependencies such as the connection reducer/presenter,
release manifest, support bundle v1, reason catalog and commerce contracts do
not regress or advance merely because they are reused here. Every owned row
moves only after its exact implementation and proof are retained.

## Work order sequence

### WO-010A — Authority, current-state and product-path baseline

Deliver:

- clean/dirty/worktree and branch collision evidence for both repositories;
- current owner map for protection, first session, downloads, subscription,
  checkout return, support, adaptive motion, accessibility and performance;
- code/test inventory tied to every owned ledger row, including implemented,
  partial, absent and externally blocked states;
- exact P0 user-path matrix from marketing/download through access activation;
- bounded slice order based on current failures and dependency shape;
- baseline verification commands and observed results without changing product
  behavior solely to make the audit green.

No row advances from a work-order draft. A row may reach `I1` only when current
owner/code/test evidence is recorded.

### WO-010B — Client presentation ownership and bounded decomposition

Deliver:

- `ProtectionViewState` composed from the existing typed connection experience
  state and exposed intents; no parallel connection state machine;
- Home/protection CTA, copy, semantic status and connect-disc visuals read the
  same immutable presentation snapshot;
- extraction of only the coordinators required for first session, connection,
  account/session and diagnostics ownership from the bootstrap composition root;
- a guard that prevents new feature logic or direct haptic calls from leaking
  back into the composition root and large screen parts;
- summary/details/support disclosure that keeps technical evidence available
  without presenting it as user-facing connection truth.

Eligible rows after proof: `REL/ARCH-001`, `REL/ARCH-003`, `REL/UX-002`,
`FE/P12-101..106`, `P12-114`, and bounded portions of `P12-102/103`.

### WO-010C — First session and acquisition continuity

Deliver:

- one coordinator for acquisition handoff, existing-access restore, trial
  creation, VPN permission explanation/recovery and first verified connect;
- failure-safe handoff: invalid/expired acquisition context never blocks the
  normal trial or restore path and never creates duplicate access;
- a pre-permission explanation and a recoverable denied-permission state;
- stable analytics correlation across acquisition and activation using bounded
  identifiers only; no session/profile material in analytics;
- tests for resumed/restarted, denied, already-active, restore and handoff
  failure paths on the supported host boundaries.

Eligible rows after proof: `FE/P12-006..008`, `FE_PR/PR-03`, `MKT/MKT-700`.

### WO-010D — Cabinet lifecycle, downloads and payment return

Deliver:

- platform detection that never makes an APK primary for Windows or an EXE
  primary for Android/unknown platforms;
- shared release cards sourced from the release-handoff contract with version,
  date, size, architecture, channel and checksum plus explicit missing/partial
  states;
- dashboard activation CTA selected by lifecycle stage; automatic onboarding
  tour replaced by an on-demand checklist;
- payment-return states for pending, paid, failed, cancelled and paid/access
  stale, using server commerce/access authorities and explicit refresh/support;
- route focus restoration and a justified audit of custom navigation/prefetch;
- focused cabinet Playwright for new, active, expiring and mismatch journeys.

Eligible rows after proof: `FE/P12-009`, `P12-118..122`, `FE_PR/PR-04`.
Previously implemented Phase 06 commerce rows receive stronger evidence but do
not automatically advance beyond their current index.

### WO-010E — Adaptive controls and marketing motion safety

Deliver:

- platform-appropriate scrolling, navigation transition, switch, back and focus
  behavior without forking product semantics;
- marketing showcase that disables sticky motion under reduced motion;
- progressive content visible before JavaScript enhancement;
- finite decorative hero motion and bounded stagger;
- bundle optimization only after measured evidence identifies the current
  animation payload as material.

Eligible rows after proof: `FE/P12-015..017`, `P12-125`, conditional
`P12-204`, `FE_PR/PR-06`.

### WO-010F — Accessibility and visual contracts

Deliver:

- critical client path usable at 200% text scale without clipped actions or
  hidden state;
- meaningful transition announcements, one semantic source for CTA/status and
  no duplicate outcome haptics;
- accessible web tabs with Arrow/Home/End and roving tabindex;
- keyboard route/dialog operation and focus restoration;
- axe gate with no serious/critical findings on the selected cabinet/marketing
  matrix;
- deterministic golden/visual states for mobile/desktop, light/dark and reduced
  motion, with manual/device evidence labelled separately.

Eligible rows after proof: `FE/P12-018`, `P12-019`, `P12-115..117`,
`P12-123..124`, `REL_DOD/DOD-14`.

### WO-010G — Diagnostics, support and recovery UX

Deliver:

- client Diagnostics screen with summary, freshness, causal evidence and safe
  local actions based on the existing reason catalog;
- preview of support-bundle categories/redaction before upload or export;
- create-case-plus-bundle flow reusing the existing encrypted bundle/upload
  authorities; only `.pokrov-support` is exportable;
- short support code without upload when supported by the current contract;
- signed TTL temporary support mode with persistent indicator and hard time/
  volume limits only if the server/client authority already exists or is added
  in a separately proved contract;
- phase/reconnect timeline, same-build/platform healthy-baseline comparison and
  offline diagnostic rules that make no unsupported causal claim;
- background-aware polling with stop, jitter and backoff.

Eligible rows after proof: `OBS/OBS-067..074`, `OBS/OBS-086..090`,
`FE/P12-104..106`, `P12-108`, `P12-113`, `FRKN_ADOPT/ADOPT-06`.

### WO-010H — Information architecture and bounded P2 decisions

Deliver:

- Locations groups Auto/favorites/recent/all with emergency selection framed as
  recovery and latency freshness explicit;
- Rules split into basic and expert disclosure with one change summary and one
  apply/reconnect operation;
- Profile sections for account, access, devices, app settings, help and rewards;
- an evidence-based decision for each P2 item: implement only if required by a
  P0/P1 acceptance failure, otherwise defer with preserved rationale.

Eligible rows after proof: `FE/P12-107..111`, `FE_PR/PR-07`; conditional
`FE/P12-202`, `P12-205..207`, `P12-209`.

### WO-010I — Performance and local quality gate

Deliver:

- versioned budgets and repeatable collection for cold start, connect UI,
  scrolling/frame health, idle CPU/memory and public API/page latency;
- exact measurement environment, warmup/sample rules and regression thresholds;
- bounded web JavaScript/image/font budgets and client build-size observations;
- local gate combining focused unit/widget/component/E2E, accessibility,
  responsive and performance checks without treating operator/device checks as
  automated passes;
- a final row-by-row reconciliation and handoff to exact-candidate Phase 11.

Eligible rows after proof: `REL/PERF-001`, `REL_GATE/GATE-E`,
`REL_DOD/DOD-13`, `FE_PR/PR-09`.

## Global acceptance oracle

- acquisition can fail safely without blocking restore/trial;
- permission denial has an explicit recovery path;
- connection CTA, copy, motion and semantics cannot contradict the existing
  typed connection state or proof-driven connected invariant;
- primary protection UI shows outcome first and technical evidence on demand;
- cabinet download primary action matches the detected/selected platform and
  exact release contract;
- subscription/payment return copy never claims access from telemetry or an
  unconfirmed payment;
- reduced-motion content remains visible and usable without sticky/infinite
  interaction requirements;
- keyboard, screen reader, 200% text scale and focus-restoration gates pass on
  the selected critical path;
- diagnostics and support artifacts preserve current redaction/encryption/TTL
  contracts and expose no secret or raw profile;
- performance results are comparable, versioned and below the agreed stop
  thresholds;
- no new parallel state authority, duplicate product facts or broad rewrite is
  introduced.

## Verification matrix

Client, from the scoped `POKROV-app` worktree:

- focused `flutter analyze` for changed packages/apps;
- focused reducer/presenter/bootstrap/widget/semantics tests first, then the
  affected package suite;
- Android JVM/Flutter host tests only when Android permission/host files change;
- Windows host tests only when Windows adaptive/host files change;
- `powershell -ExecutionPolicy Bypass -File .\scripts\validate-seed.ps1` for
  release/config/doc contract changes;
- `powershell -ExecutionPolicy Bypass -File .\test\docs-contract.ps1` when
  client docs change;
- `git diff --check` and proof of no unintended `artifacts/releases/**` delta.

Platform, from the platform worktree:

- `webapp`: `npm.cmd run lint`, `npm.cmd run build`,
  `npm.cmd run test:e2e:cabinet` plus focused accessibility/responsive checks;
- `marketing`: `npm.cmd run build`, `npm.cmd run check:seo`,
  `npm.cmd run check:responsive` plus focused reduced-motion/no-JS checks;
- focused platform API/copy/facts tests named by the router when those contracts
  change;
- documentation contract/link/context checks and `git diff --check`.

Exact-candidate physical device, signing, real payment/provider, current-origin,
brain-origin, RU-origin and post-promotion performance remain Phase 11/manual
gates unless separately authorized and retained.

## Rollback

- keep every slice repository-scoped and independently revertible;
- do not remove the existing connection reducer, support bundle, commerce or
  release-contract paths while a new presentation/flow adapter is introduced;
- gate materially changed first-session/cabinet journeys when current rollout
  infrastructure supports it; do not invent a client-only source of truth;
- preserve old local state/schema readers for the established compatibility
  window and use no down-migration as a UI rollback mechanism;
- for web static candidates, retain the prior versioned bundle and exact
  fingerprint; actual pointer rollback remains an exact-candidate operation;
- if a local quality gate regresses, stop the slice at its last proved boundary
  and record the failing evidence instead of widening the change.

## Stop conditions

Return `NEEDS_CONTEXT` before implementation when:

- current canonical owner and code disagree on a product or privacy behavior;
- a required client change would alter a platform API, payment/access authority,
  signing identity, runtime privilege or Core ABI without its owner decision;
- dirty/concurrent work overlaps the exact files required by the slice;
- a proposed P2 item lacks a concrete P0/P1 acceptance failure;
- a manual/device/provider/production gate is the only remaining evidence.

## 2026-08-22 — WO-010A authority and current-state closure

Result: `PASS` for repository-scoped discovery and baseline verification.
This closes discovery only. Every Phase 08 row is now reverified at `I1`; no
row is represented as implemented merely because an adjacent Phase 04/06
primitive already exists.

### Repository and branch evidence

- platform execution worktree:
  `C:/Users/kiwun/Documents/ai/VPN-1.2.0-phase00`, branch
  `codex/1.2.0-phase00`; the dirty tree is the retained Phase 00–07 work and is
  preserved;
- active client execution worktree:
  `C:/Users/kiwun/Documents/ai/POKROV-app-1.2.0-release-v2`, branch
  `codex/1.2.0-release-v2`; its dirty tree contains the unmerged 1.2.0 client
  reducer, Windows service, observability and support-bundle work required by
  this phase;
- clean client `main` still represents 1.1.6 and is not a valid Phase 08 base;
  the unused clean `POKROV-app-1.2.0-phase08` worktree was left untouched;
- no commit, push, artifact promotion, signing, deployment, payment/provider
  mutation or production action occurred.

### Current owner map

| Product concern | Canonical owner | Current code owner | Observed boundary |
|---|---|---|---|
| Protection truth and CTA | client product contract; UI direction | `connection_experience.dart`, `seed_shell.dart`, `home_surface.dart`, `protection_center.dart` | Typed reducer/presenter exists, but the shell still passes parallel headline, location and callbacks and the details sheet derives from a raw runtime snapshot. |
| First session and acquisition | app-first onboarding flow | `seed_shell.dart`, `onboarding_flow.dart`, bootstrap/acquisition services | Choice, restore and acquisition paths exist, but `_FirstLaunchStep`, acquisition subscription and completion actions remain shell-owned; no bounded coordinator exists. |
| Downloads, lifecycle and payment return | platform app-first/release/commerce contracts; `webapp/README.md` | cabinet downloads/dashboard/subscription/checkout components | Release data is available, but the primary download is hard-coded Android-first, the dashboard auto-opens its tour and route focus is not restored. |
| Support and diagnostics | client support-bundle and observability contracts | support chat, `support_bundle`, diagnostics collectors | Preview, encrypted envelope and resumable delivery exist; standalone diagnostics, short code, signed support mode, healthy-baseline diff and phase graph do not. |
| Adaptive motion and accessibility | client design/motion checklists; marketing design | Flutter design system and screens; marketing motion/tabs; cabinet route shell | Reduced-motion hooks and semantics exist in parts, but sticky showcase/no-JS reveal, 200% text, tab keyboard model, axe and visual matrices remain open. |
| Performance | client motion/performance checklist plus web build contracts | no single measured baseline owner | Checklists exist, but no versioned cold-start/connect/idle/API baseline with thresholds and exact environment is retained. |

### Row-complete implementation inventory

Every row below has its owner, current implementation state and next slice
confirmed by the cited files and tests. Conditional P2 rows are verified as
requirements, not approved for implementation.

| Ledger rows | Current state at 010A | Durable evidence | Route |
|---|---|---|---|
| `REL/ARCH-001`, `ARCH-003`, `UX-002`; `FE/P12-101..106`, `P12-114` | Partial: one typed connection reducer/presenter is real; no `ProtectionViewState` or coordinator seam, and direct `HapticFeedback` calls remain outside the shared haptic authority. | `app_first_runtime_bootstrap.dart` 9,915 lines; `seed_shell.dart` 5,979 lines; 29 shell `part` files; `_QuickConnectSection` receives `ConnectionPresentation` plus parallel headline/location/intents; direct calls in `seed_shell.dart` and `pokrov_controls.dart`. | `010B` |
| `FE/P12-006..008`; `FE_PR/PR-03`; `MKT/MKT-700` | Partial: new/returning choice, restore and acquisition consumption exist, but the shell owns the state and failure continuity; no first-session coordinator or complete permission-explainer state machine exists. | `_firstLaunchStep`, acquisition stream subscription and `_loadFirstLaunchState()` are in `seed_shell.dart`; UI is in `onboarding_flow.dart`; focused first-launch widget baseline passes. | `010C` |
| `FE/P12-009`, `P12-118`, `P12-119`, `P12-121`, `P12-122`, `P12-128`; `FE_PR/PR-04` | Open/partial: downloads sort Android before Windows regardless of user platform; dashboard automatically opens onboarding; intent prefetch has a duplicate-navigation lock but no route-heading focus restoration; stale `Публичная бета` copy remains. | `downloads-surface.tsx:204..228`, dashboard effect `:105..112`, `app-route-link.tsx`, downloads hero copy. | `010D` |
| `FE/P12-015..017`, `P12-125`, conditional `P12-204`, `P12-207`; `FE_PR/PR-06` | Partial: responsive/adaptive and reduced-motion hooks exist, but desktop showcase remains sticky under reduced motion and `.reveal` starts at opacity zero before JS; no user motion override or measured need for `LazyMotion` is proved. | `showcase-scroller.tsx`, `reveal.tsx`, marketing `globals.css:85..105`, current hero/motion components. | `010E` |
| `REL_DOD/DOD-14`; `FE/P12-018`, `P12-019`, `P12-115..117`, `P12-123`, `P12-124` | Partial/open: client semantics and 1.3x text tests exist; 200% critical-path, web tab Arrow/Home/End with roving tabindex, axe serious/critical gate and deterministic visual matrix do not. | `pokrov_seed_app_test.dart` uses text scale 1.3 only; install tabs have ARIA roles but click-only selection; no axe dependency/gate or complete golden matrix was found. | `010F` |
| `OBS/OBS-067..074`, `OBS-086..090`; `FE/P12-113`; `FRKN_ADOPT/ADOPT-06` | Mixed: consumer protection details, category preview and encrypted `.pokrov-support` outbox/upload are present; standalone diagnostics, short code, signed/capped support mode, evidence graph, same-build baseline and offline causal rules are absent. Support polling is fixed at 10 seconds without jitter/backoff. | `protection_center.dart`, `support_chat.dart:39,194,391..897`, `support_bundle.dart`; encrypted outbox and presenter tests pass. | `010G` |
| `FE/P12-107..111`; `FE_PR/PR-07`; conditional `P12-202`, `P12-205`, `P12-206`, `P12-209` | Partial: locations, rules, profile and Windows controls exist but remain large screen/shell-owned surfaces without the proposed bounded IA; QR handoff is absent and has no approved identity/threat contract. | locations/rules/profile feature files and widget inventory; client product/architecture owners explicitly keep QR conditional. | `010H` |
| Conditional `FE/P12-203` | Open: Playwright E2E exists for cabinet, but no dedicated portal component-test environment is established and no P0/P1 failure currently requires adding one. | `webapp/package.json` exposes E2E/lint/build only. | Decide in `010H`; otherwise defer. |
| `REL/PERF-001`; `REL_GATE/GATE-E`; `REL_DOD/DOD-13`; `FE_PR/PR-09` | Open: release checklists exist, but current comparable measurements, stop thresholds and an exact-environment local aggregate gate are not retained. | client motion/performance checklist, responsive capture plan and current web/marketing scripts. | `010I` |

### P0 product-path baseline

| Step | Authority | 010A result | First proving slice |
|---|---|---|---|
| Marketing intent to supported download | shared release facts and handoff v2 | Release contract exists; reduced-motion/no-JS gaps remain. | `010E`, then `010I` |
| Cabinet chooses the correct client | release handoff v2 plus browser platform | `FAIL`: Android is the hard-coded first action on every platform. | `010D` |
| Acquisition context reaches the installed client | app-first acquisition contract | Partial; shell consumes it directly and safe failure continuity is not isolated/tested as one coordinator. | `010C` |
| New trial or existing access becomes active | account/access authority | Both paths exist; orchestration is shell-owned. | `010C` |
| VPN permission is explained and recoverable | host runtime plus client presentation | Runtime pending state exists; complete pre-permission/denied recovery journey is open. | `010C` |
| First connect reaches truthful protection | typed connection reducer plus proof invariant | Reducer/presenter baseline passes; presentation ownership still leaks through parallel props. | `010B` |
| Failure reaches safe diagnostics/support | reason catalog, support bundle, ticket service | Safe details and encrypted delivery exist; diagnostic product surface and polling policy remain incomplete. | `010G` |
| Payment return refreshes authoritative access | commerce/payment/access authorities | Server contracts exist from Phase 06; complete cabinet mismatch journey remains a Phase 08 UI proof. | `010D` |

### Baseline verification

- client `flutter analyze packages/app_shell`: `PASS`, no issues, 36.7 s;
- client connection presenter plus encrypted outbox tests: `PASS`, 12/12;
- focused first-launch, compact connect control and encrypted-support widgets:
  `PASS`, 3/3;
- cabinet `npm.cmd run lint`: `PASS`;
- marketing `npm.cmd run lint`: `PASS`;
- no product behavior was changed to obtain these baseline results.

### Selected first implementation

`WO-010B1` is the smallest architecture-first slice: add immutable
`ProtectionViewState` plus `ProtectionIntents` around the existing
`ConnectionPresentation`, construct one snapshot in the shell, and make the
Home protection block consume that aggregate. It must not introduce a second
connection state machine or absorb unrelated commercial/home state.

## 2026-08-22 — WO-010B1 protection presentation boundary

Result: `LOCALLY_PROVED` for the bounded Home protection seam.

Implemented in the active client worktree:

- added immutable `ProtectionViewState`, which retains the exact existing
  `ConnectionPresentation` and adds only route/location/emergency/recovery/hint
  presentation context;
- added `ProtectionIntents` for toggle, details, locations, rules and recovery;
- the composition root now constructs one state/intent pair and Home,
  `_HomeStage` and the desktop connect panel consume it rather than parallel
  connection copy, CTA and callbacks;
- moved the haptic adapter out of the app-shell `part` graph, routed the three
  remaining shell calls and the design-system switch through it, and retained
  its public test contract;
- added `test/client-presentation-boundary.ps1`: it rejects parallel Home
  connection props, composition-root leakage, app-shell `part` growth above 29
  and direct `HapticFeedback` calls outside `PokrovHaptics`;
- registered the guard in seed validation and updated the client package
  boundary and test-entrypoint owners.

Verification:

- `flutter analyze packages/app_shell`: `PASS`, no issues;
- `connection_experience_test.dart`: `PASS`, 11/11;
- focused haptic design-system contract: `PASS`, 1/1;
- focused Home details/connect/pointer-keyboard widgets: `PASS`, 3/3;
- client presentation boundary: `PASS`, aggregate state/intents, 29 parts,
  centralized haptics;
- client docs contract: `PASS`;
- full `validate-seed.ps1` against the active Phase 00 platform worktree and
  active 1.2.0 Core worktree: `PASS`, including version parity, observability,
  release-source logging, release handoff 13 cases, release-v2 CI, the new
  boundary and docs contracts;
- an initial seed run against clean Core `main` failed because that tree lacks
  the unmerged 1.2.0 `abi_contract`; it was not treated as product evidence and
  the correct active Core worktree was then used;
- scoped client `git diff --check`: `PASS` with line-ending warnings only.

`FE/P12-101`, `FE/P12-103` and `FE/P12-114` advance from `I1` to local `I3`.
This does not complete bootstrap decomposition, four coordinators, physical
device semantics/haptics or exact-candidate proof.

## 2026-08-22 — WO-010B2 connection state ownership

Result: `LOCALLY_PROVED` for one of the four required coordinator seams;
`REL/ARCH-001` is therefore only `IMPLEMENTED_PARTIAL / I2`.

Implemented in the active client worktree:

- `ConnectionCoordinator` now owns mutable runtime snapshot, explicit
  transition intent, action-in-flight state, attempt clock/number and the
  existing reducer/presenter derivation;
- the same coordinator owns the bounded runtime-action timeout and exposes
  explicit begin/finish/clear operations;
- `seed_shell.dart` retains temporary private adapters for its existing product
  orchestration, but no longer declares parallel raw connection fields;
- the primary toggle path uses coordinator begin/finish operations while
  preserving route, profile, host, WARP, observability and Core behavior;
- the boundary test now fails if the composition root restores raw snapshot,
  busy, intent or attempt fields;
- the canonical package boundary records this ownership seam.

Verification:

- `flutter analyze packages/app_shell`: `PASS`, no issues;
- connection reducer/presenter/coordinator/timeout suite: `PASS`, 13/13;
- focused Home, Android delayed-health, egress fail-closed and
  pointer/keyboard scenarios: `PASS`, 5/5;
- presentation boundary and client docs contracts: `PASS`;
- full seed validation against the active Phase 00 platform and 1.2.0 Core
  worktrees: `PASS`, including all release/observability/logging/CI contracts.

No Core ABI, host runtime, product copy, connection invariant or external state
changed. First-session, account/session and diagnostics ownership remained open
at the end of this bounded slice.

## 2026-08-22 — WO-010B3..B5 remaining state owners

Result: `LOCALLY_PROVED` for the complete four-coordinator ownership set.

Implemented in the active client worktree:

- `FirstSessionCoordinator` owns first-launch choice/restore/ready state,
  persistence and bounded restore/new-user transitions;
- `AccountSessionCoordinator` owns the account action capability, free-profile
  access and authoritative subscription snapshot;
- `DiagnosticsCoordinator` owns foreground-refresh single-flight, bounded
  post-connect polling, generation fences and in-flight rejection;
- the shell retains orchestration adapters, but no longer declares the raw
  mutable fields owned by those coordinators;
- the release-bound architecture guard requires all four coordinators and
  rejects restoration of their raw connection, first-session, account/session
  or diagnostics state;
- canonical client package-boundary and test-entrypoint owners record the new
  seams.

Verification:

- `flutter analyze packages/app_shell`: `PASS`, no issues;
- first-session coordinator tests: `PASS`, 3/3, plus five focused new/returning
  first-launch and restore widgets;
- account/session coordinator test: `PASS`, 1/1, plus five focused profile,
  redeem, cabinet-handoff and subscription-recovery widgets;
- diagnostics coordinator tests: `PASS`, 3/3;
- focused support, delayed Android health, fail-closed egress and stale-poll
  widgets: `PASS`, 4/4;
- presentation boundary and client docs contracts: `PASS`;
- full `validate-seed.ps1` against the active Phase 00 platform and 1.2.0 Core
  worktrees: `PASS`, including parity, observability, logging, release-handoff,
  release-v2 CI, presentation and docs gates;
- scoped client `git diff --check`: `PASS` with line-ending warnings only.

`REL/ARCH-001` advances from partial `I2` to local `I3`; `FE/P12-102`
advances from `I1` to local `I3`. This proves the four requested ownership
seams, not the remaining large-screen separation, progressive disclosure or
exact-candidate behavior.

## 2026-08-22 — WO-010B6 protection disclosure and recovery

Result: `LOCALLY_PROVED` for the remaining `WO-010B` product behavior;
large-screen separation remains intentionally partial outside the changed
Protection Center.

Implemented in the active client worktree:

- `ConnectionCoordinator` owns a ten-second per-stage timer; a typed stage
  change resets it and finish/dispose cancels it;
- a slow stage exposes the current consumer-safe title/subtitle plus explicit
  details on Home and records one bounded local protection event;
- Protection Center now opens on a consumer summary; tunnel, DNS, egress,
  routes, location, last-check time, live stats and history require explicit
  details disclosure, with support/diagnostics as the third layer;
- `_ProtectionCenterController` owns refresh, disclosure, repair progress,
  outcome and error state while the host actions remain injected;
- repair now requires confirmation that the internet may briefly disappear,
  reports stop-old-connection, refresh-profile and verify-protection steps, and
  ends in a verified result or a support entry;
- the architecture guard binds the slow-stage, summary/details, confirmation,
  progress and outcome seams without increasing the 29-part ceiling.

Verification:

- `flutter analyze packages/app_shell`: `PASS`, no issues;
- reducer/presenter/coordinator suite: `PASS`, 14/14;
- focused disclosure, safe-copy, repair success/failure, long-connect and
  Android fail-closed/stale-poll widgets: `PASS`, 10/10;
- complete `packages/app_shell` test suite: `PASS`, 347/347;
- presentation boundary and client docs contracts: `PASS`;
- full seed validation against the active Phase 00 platform and 1.2.0 Core
  worktrees: `PASS`;
- scoped client `git diff --check`: `PASS` with line-ending warnings only.

`REL/UX-002` and `FE/P12-104..106` advance from `I1` to local `I3`.
`REL/ARCH-003` advances only to partial `I2`: Protection Center has a bounded
controller, while other large screens remain in the retained part library and
will be extracted only when a later P0/P1 slice needs it.

### WO-010C1 local closure — client first-session continuity

The client now routes trial selection, existing-access restore, opaque
host-bound acquisition consumption, VPN permission explanation/recovery and
first-open/home/verified-connect milestones through one
`FirstSessionCoordinator`. Merely rendering the welcome gate does not provision
trial/account data. Invalid or expired acquisition never hides normal choices,
raw handles are not retained or reported, permission dismissal never connects,
and denial exposes a bounded retry surface.

Authenticated first-session events use a fixed vocabulary and server-derived
account/device correlation. The safe payload excludes credentials, acquisition
handles, profiles, endpoints and raw host errors; it is advisory rather than
access or connection proof.

Verification:

- client analyze: `PASS` for `app_shell` and `runtime_engine`;
- complete `app_shell`: `PASS`, `356/356`;
- complete `runtime_engine`: `PASS`, `54` passed and one exact-DLL backtest
  correctly skipped because `POKROV_REAL_CORE_ROOT` was not supplied;
- focused Android permission JVM contract: `PASS`;
- client presentation/docs contracts and scoped `git diff --check`: `PASS`;
- complete platform app-first API regression: `PASS`, `43/43`;
- platform docs contract `26/26`, link check and `git diff --check`: `PASS`.

`FE/P12-006..008` and `FE_PR/PR-03` advance from `I1` to local `I3`.
`MKT/MKT-700` remains `I1`: an exact marketing-to-installed-app journey has
not been retained. No physical-device, signing, hosted CI, deploy, payment,
provider, RU-origin or exact-candidate evidence is claimed.

## First active action

Execute `WO-010I`: define versioned performance budgets and repeatable local
collection for client and web critical paths, then compose the bounded final
quality gate and row-by-row Phase 08 handoff without converting manual or
exact-candidate checks into local passes.

### WO-010D1 local closure — cabinet lifecycle, downloads and payment return

The authenticated cabinet now selects Android or Windows from the browser
platform and requires an explicit choice for an unknown platform. It never
substitutes one platform's artifact for another. A direct download exists only
when release-handoff v2 supplies URL, version, channel, publication date,
positive size and valid SHA-256; partial or missing releases route to support,
unbound mirrors are not promoted, and Apple remains an explicit manual setup
path without a native-release claim.

The dashboard no longer opens an automatic tour. Its on-demand launch
checklist and primary action now follow inactive, install, connect, complete
and expiring lifecycle states. Client-side cabinet navigation restores focus
to the destination main heading and retains documented, bounded Link-owned
prefetch/activity behavior. Active cabinet download/onboarding copy no longer
claims a public or unsigned beta.

Payment return renders all six server states. A paid response refreshes the
authenticated account before access is claimed; a paid/access mismatch keeps
an explicit refresh and support route. Terminal return markers and ephemeral
tokens are removed without treating payment status as entitlement proof.

Verification:

- WebApp lint and production build: `PASS`, 40 static routes;
- focused cabinet E2E: `PASS`, `63/63`;
- complete WebApp E2E: `PASS`, `82/82` in 1.3 minutes;
- payment return/callback regression: `PASS`, `99` tests plus 12 subtests;
- client-app release endpoint: `PASS`, `5` focused tests;
- text, copy and agent-doc contracts: `PASS`, `39/39`;
- link check and scoped `git diff --check`: `PASS` (line-ending warnings only).

`FE/P12-009`, `P12-118`, `P12-119`, `P12-121`, `P12-122`, `P12-128` and
`FE_PR/PR-04` advance from `I1` to local `I3`. `FE/P12-120` remains `I2`:
parallel loading exists, but no exact active-client performance measurement
proves the complete row. No hosted artifact, provider, payment, deploy,
physical-device, RU-origin or exact-candidate evidence is claimed.

### WO-010E1 local closure — adaptive behavior and marketing motion safety

The client now derives scroll/overscroll, page transitions, switches and
pull-to-refresh from the host platform. Apple retains Cupertino interaction
physics, Android uses Material overscroll and refresh behavior, and desktop
uses clamped scrolling plus native transition/switch behavior. Existing
Android system-back and desktop keyboard/focus contracts remain in the full
regression suite.

Marketing reveal content is visible in server and no-JavaScript output and is
hidden only after its own hydrated observer enhancement. OS reduced motion
replaces sticky scrollytelling with a static four-screen grid, removes spatial
hero motion and uses immediate scrolling. Normal hero decoration is bounded to
two cycles; mobile showcase controls expose previous/next actions and live
position. Stagger is capped at 240 ms.

The measured Framer feature payload was 141.5 KiB raw and 47.2 KiB gzip.
Strict asynchronous `LazyMotion` with `domAnimation` reduced that feature
payload to 43.5 KiB raw and 17.1 KiB gzip, a reduction of 98.0 KiB raw and
30.1 KiB gzip. The production build and real browser smoke covered the split
bundle.

Verification:

- client analyze, focused adaptive tests `3/3`, complete app-shell `359/359`,
  presentation-boundary and docs contracts: `PASS`;
- marketing lint, 35-page production build, SEO and 57-route/viewport
  responsive matrix with no-JS, reduced-motion and mobile-carousel smokes:
  `PASS`;
- platform text/copy/docs contracts `39/39`, link check and scoped diff check:
  `PASS` before this closure-only ledger update.

`FE/P12-015..017`, `P12-125`, `P12-204` and `FE_PR/PR-06` advance from `I1`
to local `I3`. `FE/P12-207` remains `I1`: OS preference is authoritative, but
an explicit in-product override has neither an approved product/persistence
contract nor an implementation. The distribution is now 163 rows at `I3`, 31
at `I2`, 45 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.
No retained success screenshots, physical-device, hosted, deployed,
payment/provider, RU-origin or exact-candidate evidence is claimed. WO-010F1
accessibility and visual contracts is active next.

### WO-010F1 local closure — accessibility and visual contracts

The client critical path now remains usable at 200% text scale for first-session
choice and restore, Home/connect, Locations and Support. Brand, value chips,
restore separators, WARP title and Locations header were made explicitly
wrapping/stacking rather than clipping. The connection CTA owns one action-only
semantic label while a separate button/live region owns protection status; the
coordinator remains the single outcome-haptic authority.

Marketing install tabs now use wrapped ArrowLeft/ArrowRight, Home/End,
automatic activation and roving tabindex. Cabinet route changes focus the main
heading; Escape closes onboarding and restores the opener. Direct `axe-core`
gates cover marketing home/install and cabinet dashboard/downloads/checkout.
Contrast repairs also removed the unlayered global anchor color rule that had
silently overridden Tailwind link utilities.

Four tracked Flutter goldens cover idle light, route-scope dark, verified dark
and degraded light. Eight tracked Playwright baselines cover cabinet
mobile/desktop by light/dark by normal/reduced motion. Client image-cache state
and Next.js development chrome are excluded from the respective matrices so
normal comparison is deterministic without updating expected files.

Verification:

- client analyze and complete app-shell: `PASS`, `362/362`;
- client presentation boundary and docs contracts: `PASS`;
- WebApp lint, 40-route production build and focused release-style E2E:
  `PASS`, `66/66`;
- marketing lint, 35-route production build, SEO and responsive/no-JS/
  reduced-motion/keyboard/axe matrix: `PASS`;
- platform text/copy/docs contracts `43/43`, link check and both scoped diff
  checks: `PASS` after the closure updates.

`REL_DOD/DOD-14`, `FE/P12-018`, `P12-019`, `P12-115..117`, `P12-123` and
`P12-124` advance from `I1` to local `I3`. The distribution is now 171 rows at
`I3`, 31 at `I2`, 37 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least
`I1`. TalkBack, Narrator, OS zoom/scaling, physical-device, deployed-origin and
exact-candidate proof remain separate I4 gates. WO-010G1 diagnostics, support
and recovery UX is active next.

### WO-010G1 local closure — diagnostics and encrypted support path

Profile now opens a standalone Diagnostics route instead of the static version
sheet. One importable presenter turns the current runtime snapshot into a
freshness marker and separate tunnel, route, DNS and VPN-egress evidence. It
selects only supported entries from the shipped operational problem book,
renders bounded Russian/English safe-message keys and lists sanitized safe
actions without copying raw host, provider, endpoint or configuration detail.
Missing evidence stays missing; the causal summary never invents a root cause.

Diagnostics and Support chat now reuse one summary-profile bundle builder. The
screen previews exact categories, file count, bounded plaintext size and
redaction count. When verified encryption configuration exists, one action
passes `ticketId: null` to the existing transfer authority, which owns case
creation plus encrypted upload/offline queueing. No plaintext export path was
added, and no parallel crypto, upload or outbox implementation was created.

Verification:

- client analyze: `PASS`, no issues;
- focused diagnostics presenter/localization/widget tests: `PASS`, `5/5`;
- profile route and one-action case/bundle widgets: `PASS`, `2/2`;
- complete app-shell regression: `PASS`, `366/366`;
- client design owner updated with the diagnostics/support evidence boundary.

`OBS/OBS-067..069`, `OBS-086`, `OBS-089`, `OBS-090` and
`FRKN_ADOPT/ADOPT-06` advance from `I1` to local `I3`. `OBS/OBS-070..074`,
`OBS-087`, `OBS-088` and `FE/P12-113` remain `I1`: encrypted export, short
code, temporary support mode, baseline/phase evidence and polling still need
their exact bounded slices. The distribution is now 178 rows at `I3`, 31 at
`I2`, 30 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.
No physical-device, deployed-origin, live-support, signing or exact-candidate
claim is made. WO-010G2 bounded support polling is active next.

### WO-010G2 local closure — bounded foreground support polling

Support chat no longer owns a fixed periodic timer. An importable one-shot
polling coordinator schedules only while the screen is mounted, an open ticket
is eligible and the app is foregrounded. Normal delay is 10 seconds plus
bounded 0–2 second jitter. Consecutive failures back off exponentially to a
hard two-minute ceiling; success or an explicit refresh resets the counter.
Backgrounding, closing the ticket, loading/sending state and disposal cancel
the pending timer. Resume schedules a fresh one-shot poll without parallel
requests.

Verification:

- client analyze: `PASS`, no issues;
- polling policy/coordinator tests: `PASS`, `4/4`;
- active-ticket success, failure and background-stop widgets: `PASS`, `3/3`;
- complete app-shell regression: `PASS`, `373/373`.

`FE/P12-113` advances from `I1` to local `I3`. The distribution is now 179
rows at `I3`, 31 at `I2`, 29 at `I1`, and 138 at `I0`; 239 of 377 rows remain
at least `I1`. Live-support load, physical-device background policy and exact-
candidate evidence remain I4 work. WO-010G3 remaining diagnostics authority
reconciliation is active next.

### WO-010G3 local closure — phase graph and authority reconciliation

Diagnostics now renders a bounded connection phase graph from the existing
sanitized breadcrumb ring. It accepts only closed `app.connection.*` event
names, collapses start/finish pairs to the latest phase outcome, retains at
most four recent attempts and sixteen phases per attempt, and labels an
attempt as a reconnect only when a rollback phase was actually recorded. The
view reads no raw JSONL attributes, destinations, profiles or host detail.

The other rows were reconciled against current owners rather than synthesized:

- encrypted `.pokrov-support` outbox/upload exists, but a user-visible
  Android/Windows export destination contract does not;
- no versioned short-code encoder/decoder or support lookup endpoint exists;
- signed extended-policy schema, signature/TTL verification and per-bundle
  byte ceilings exist, but policy issuance, active-session ownership,
  persistent indication and cumulative volume enforcement do not;
- release-health baselines are operator-only; no minimum-cohort,
  privacy-bounded client projection exists.

Verification:

- client analyze: `PASS`, no issues;
- focused diagnostics presenter/timeline/widget tests: `PASS`, `6/6`;
- complete app-shell regression: `PASS`, `374/374`;
- scoped client `git diff --check`: `PASS` (line-ending warnings only).

`OBS/OBS-088` advances from `I1` to local `I3`. `OBS/OBS-070..074` and
`OBS/OBS-087` remain explicit `I1` contract gaps with concrete next
authorities in the ledger. The distribution is now 180 rows at `I3`, 31 at
`I2`, 28 at `I1`, and 138 at `I0`; 239 of 377 rows remain at least `I1`.
Physical-device, long-session ring-pressure, support-policy issuance,
minimum-cohort baseline and exact-candidate evidence remain open. WO-010H
information architecture and bounded P2 decisions is active next.

### WO-010H local closure — information architecture and bounded P2 decisions

Locations keeps one ordered hierarchy: Auto, a recovery-framed reserve entry,
favorites, recent locations and the remaining catalog. Cached/offline rows
preserve that structure. Catalog and variant measurements expose current,
stale, invalid/unknown and explicit age states instead of presenting ping as
timeless truth. The reserve launcher now says `Восстановить связь`; its
technical whitelist-mode owner remains inside the recovery route.

Rules keeps route scope and app selection in the first layer. DNS, custom
routes, trusted Wi-Fi and Windows stack remain behind one expert disclosure.
Expert edits now accumulate in one named change summary. A stopped tunnel
applies the saved draft at next connect; an active tunnel does not restart
until one `Применить и переподключить` action. A focused runtime test proves
two changes cause zero early disconnects and exactly one disconnect/connect
pair on Apply.

Profile retains distinct access, account/devices, recovery, support, app-
settings and rewards sections. Diagnostics remains owned by Support and route
changes remain owned by Rules, so no second product-state authority was added.

Conditional P2 decisions are explicit: full library extraction (`P12-202`),
Smart Connect explanations (`P12-205`), Windows titlebar/tray polish
(`P12-206`), user motion override (`P12-207`) and QR handoff (`P12-209`) stay
at `I1`. No observed P0/P1 acceptance failure justifies those expansions;
each ledger row names the dependency that would reopen it.

Verification:

- client analyze: `PASS`, no issues;
- focused Profile/Rules/Locations/recovery IA tests: `PASS`, `6/6`;
- complete app-shell regression: `PASS`, `375/375`;
- client design owner updated with the IA and one-apply boundary.

`FE/P12-107..111` and `FE_PR/PR-07` advance from `I1` to local `I3`. The
distribution is now 186 rows at `I3`, 31 at `I2`, 22 at `I1`, and 138 at
`I0`; 239 of 377 rows remain at least `I1`. Physical-device navigation,
screen-reader reading order, real latency cadence, reconnect failure recovery
and exact-candidate presentation remain open. WO-010I performance and local
quality gate is active next.

### WO-010I local closure — performance and aggregate quality gate

Performance contract `1.0.0` now defines 32 metrics across client cold start,
verified connect/reconnect/rollback, Flutter build/raster frames, Android and
Windows idle CPU/memory, client artifact-size observations, controlled-origin
API latency, browser page latency and static web assets. Each metric fixes its
unit, statistic, target/stop boundary, warmup/sample minimum, regression limit,
collector owner and required environment fields. The validator uses nearest-
rank percentiles, checks the contract digest and exact environment, rejects
future/unknown fields, duplicate keys, insufficient/non-finite samples and
cross-environment baselines, and computes PASS/FAIL itself.

Collection is executable and bounded:

- the platform static collector hashes measured export inputs and computes the
  maximum gzip JavaScript for critical routes plus unique image/font totals;
- the allowlisted API probe uses HTTPS, environment-only authorization and an
  explicit state-changing guard, and never prints a body or credential;
- the browser collector records numeric LCP/CLS/TBT/route-content arrays from
  isolated reduced-motion Chromium contexts;
- the client helper measures Windows idle CPU/working set and exact artifact
  size or normalizes approved Android/Flutter numeric samples without reading
  logs/configs or treating `adb am start -W` as a useful POKROV frame;
- the generic evidence builder binds samples to a repository revision and the
  canonical contract; manual/access-blocked records remain non-PASS.

The retained local report binds dirty source revisions platform
`280ed9157f5804d4bc719cb8d6cab471caafb937`, client
`ba7930ea83487874f47a49199ade89868c5675b3` and Core
`69a74545101708e56183c92e31f2b4c7b2509884`. Its fifteen steps all pass:
performance contract/tests `26/26`, app-shell analyze and `375/375`, client
seed/docs contracts, cabinet lint/build and E2E `66/66`, marketing build/SEO/
responsive/reduced-motion/axe, fresh admin static build, and static collection/
gate. The report explicitly sets `candidate_proven=false` and
`promotion_status=MANUAL_OWNER_TEST`.

Fresh local static-export stop budgets pass `9/9`: marketing route JS
`246707` bytes gzip, images `7848431`, fonts `96848`; webapp route JS `302597`,
images `5390960`, fonts `182880`; admin route JS `455270`, images/fonts `0`.
Marketing/webapp/admin route-JS targets and marketing/webapp image targets are
not yet met and remain visible as `target_met=false`; passing the wider stop
boundary is not represented as target attainment.

`REL/PERF-001`, `REL_GATE/GATE-E` and `FE_PR/PR-09` advance from `I1` to local
`I3`. `REL_DOD/DOD-13` stays `I1`: static local observations do not prove
Android/Windows, browser-lab, controlled-origin API or exact artifact
baselines. Conditional `FE/P12-203` also stays `I1`; the current unit/E2E
contracts have no P0/P1 isolation failure that justifies a second component-
test environment.

The distribution is now 189 rows at `I3`, 31 at `I2`, 19 at `I1`, and 138 at
`I0`; 239 of 377 rows remain at least `I1`. Phase 08 is locally complete.
Candidate-device performance, artifact comparison, browser lab, controlled-
origin API, signing, current/brain/RU origin and post-promotion proof remain
Phase 11 gates. No live API/provider/payment call, physical-device run, build,
sign, deploy or promotion is claimed by this closure.

### Phase 08 row reconciliation

All Phase 08 P0/P1 product-path slices owned by this WO are locally proved.
Remaining Phase 08-indexed rows are explicit rather than silently carried:

- `REL/ARCH-003` is closed at local `I3` by follow-up `WO-010J`: Protection
  Center and the release-critical update flow have focused mutable/presentation
  owners, while further mechanical screen extraction still requires a concrete
  ownership/testability failure;
- `OBS/OBS-070..074` and `OBS-087` remain `I1` pending export destination,
  short-code, signed support-session and privacy/minimum-cohort authorities;
- `REL_DOD/DOD-13` remains `I1` pending comparable exact-candidate baselines;
- `FE/P12-202`, `P12-203`, `P12-205..207` and `P12-209` remain bounded P2
  deferrals with a named reopening condition in the ledger;
- `MKT/MKT-700` hands to Phase 09 for retained campaign-to-installed-app proof.

The next architecture-ordered work is Phase 09 `WO-011`: legally qualified,
capacity-bounded marketing pilot preparation and evidence-based decision. A
real campaign, ad spend or external communication remains unauthorized.

### WO-010J follow-up — release-critical update owner

The remaining concrete P0/P1 screen-ownership failure was the update flow in
the shell composition root. An ordinary imported update feature now owns check
concurrency, prompt deduplication, installer/progress public types, the update
sheet and the progress dialog. The shell injects metadata access and retains
only installer/handoff and lifecycle/observability orchestration. The guard
rejects restoration of the three raw update state fields or update widgets in
the shell and keeps the `part` ceiling at 29.

Client analysis, two coordinator tests, two focused update widgets, the full
`379/379` app-shell suite, presentation boundary, explicit-root seed validation
and diff checks pass. `REL/ARCH-003` advances `I2 -> I3`; the current
distribution is `I3=279`, `I2=33`, `I1=45`, `I0=20`, with 98 rows below `I3`.
Physical installer/accessibility, exact-candidate and public-index evidence
remain open before `I4`; no artifact or external action is claimed.

### WO-010K follow-up — conditional support transport reconciliation

The source plan requires active support polling every 5-10 seconds, relaxation
to 15-30 seconds after one unchanged minute, immediate foreground-resume
refresh, background stop and bounded failure backoff with jitter. It names
SSE/WebSocket only as a conditional P2 fallback. The canonical product owner
likewise rejects a streaming transport without an observed polling failure.

Candidate.3 source already had one-shot polling, background cancellation and
bounded failure backoff, but it did not implement the one-minute quiet cadence
or immediate resume refresh and its 10-second base plus jitter could reach 12
seconds. Client PR `#29` head `03a59a7...` closes those source-plan gaps with
an 8-10 second active cadence, 15-30 second quiet cadence, typed
changed/unchanged/failed results and immediate resume refresh. Focused polling
and lifecycle tests, app-shell `392/392`, the complete local client gate, seed,
docs and release-v2 contracts pass.

No live ticket was created or message sent. LDPlayer proves only exact
candidate.3 install/launch and Support screen rendering; the adaptive branch is
not installed there. PR `#29` remains unmerged because required job
`98453413213` has zero steps under the GitHub billing blocker. Candidate.3 is
unchanged and cannot inherit this source proof.

`FE/P12-208` advances `I0 -> I1` as
`VERIFIED_DEFERRED_NOT_REQUIRED`: there is no retained polling failure that
justifies adding SSE/WebSocket. `FE/P12-113` remains local `I3` with stronger
source evidence and still needs a merged replacement candidate plus authorized
live traffic before `I4`. Distribution becomes `I4=4`, `I3=312`, `I2=19`,
`I1=40`, `I0=2`; 316 rows remain at or above `I3`, 61 remain below, and the
pending stage split stays `0/28/14/19`. No deploy, ticket, entitlement,
physical-device action, artifact promotion or public/stable mutation occurred.
