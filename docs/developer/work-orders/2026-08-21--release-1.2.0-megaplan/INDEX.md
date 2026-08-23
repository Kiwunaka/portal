# POKROV 1.2.0 Megaplan — Wave Index

Last updated: 2026-08-23
Classification: `ACTIVE_EXECUTION`
Wave status: `PHASE_11_OWNER_SOLO_AUTHORIZED_CANDIDATE_ASSEMBLY_ACTIVE`
Release candidate: `NOT_CREATED`

## Outcome

Deliver POKROV 1.2.0 as an evidence-bound release across the platform, active Android/Windows client, core and public release index. The release must close the audited stop-ship defects, establish one signed machine-readable release contract, make connection truth and diagnostics authoritative, ship the canonical Operator Center, reconcile frontend and commercial behavior, and only promote immutable artifacts after exact-candidate gates pass.

Linux and protocol experiments are conditional lanes: Linux may be a beta only after its own daemon/package matrix is proved; FRKN-derived AWG2/Hysteria2 work cannot be advertised as production or RU-ready without exact-candidate RU-origin evidence.

## Authority and lane boundaries

- Platform source and canonical root documentation: `Kiwunaka/portal`, promotion branch `master`.
- Active Android/Windows client: `Kiwunaka/POKROV-app`, promotion branch `main`.
- Core: `Kiwunaka/pokrov-core`, promotion branch `main`.
- Public release index: `Kiwunaka/pokrov`; immutable assets remain GitHub Release evidence.
- This wave is execution state, not product or release authority. Canonical owners must be updated in the WO that changes behavior.
- Current runtime, signing, device, RU-origin and provider proofs remain distinct. A document or local pass is not production proof.

## Execution order

| Phase | Architectural outcome | State | Primary WO |
|---|---|---|---|
| 00 | Baseline, authority map, complete execution ledger | Locally proved (`I3`) | `WO-001` |
| 01 | Release manifest, version/provenance contract, CI and stop-ship controls | Release-v2, client adoption, release-bound CI, reproducible dependencies, shared catalog and cross-repository truth are locally proved; the public-index source/trust root is on public main, PR-00 is merged and the exact hosted client gate passes; `OWNER_SOLO_EXCEPTION` explicitly replaces the unavailable second reviewer without claiming independent review, Core main has the full solo-safe live policy, and final exact PR/check bindings remain open for private platform/client promotion | `WO-002`, `WO-003`, `WO-003B`, `WO-003C`, `WO-003D`, `WO-003E`, `WO-003F`, `WO-003G`, `WO-003H`, `WO-003I`, `WO-003J`, `WO-013J`, `WO-013K`, `WO-013L`, `WO-013M`, `WO-013N`, `WO-013O` |
| 02 | Typed connection state, proof-driven green state, core ABI and migrations | 004A/004A2, 004B/004B2, 004C and aggregate Gate B are `I3`; direct cutover and deterministic visual baselines are explicit; ABI v3 is deferred until after 1.2.0; current Core source passes all five hosted jobs, while one exact candidate revision combining hosted CI with the already-bound artifact bytes remains open | `WO-004`, `WO-004A2`, `WO-004B2`, `WO-004D`, `WO-006I`, `WO-013N` |
| 03 | Windows/Android runtime boundaries; conditional Linux beta foundation | Locally complete: Windows service/recovery/journal and stack-only crash profile plus Android runtime/private operational producers are proved; Linux explicitly not shipped in 1.2.0 | `WO-005`, `WO-005C4`, `WO-005D4` |
| 04 | Observability, error catalog, redacted bundle and support pipeline | Locally complete (`I3`) for shipped Android/Windows scope, including four-class safe transport failures, active operational producers, Android count-only routing, no-upload short code, signed temporary support mode, encrypted-only manual export and a current 7/7 MSVC native proof for the bounded Windows service journal; Linux remains explicitly not shipped and external custody, runtime and exact-candidate evidence remain open | `WO-006`, `WO-006I`, `WO-006J`, `WO-006K`, `WO-006L` |
| 05 | Portal bounded contexts, payments, HTTP/DB/outbox reliability | Locally complete (`GATE-D` and `ARCH-002` at `I3`); 007G–007I split admin, public/client and Action Intent domain/runtime owners | `WO-007`, `WO-007G`, `WO-007H`, `WO-007I` |
| 06 | Product facts, subscriptions, checkout, offers and attribution | Local source packages: 008A–008G commercial package at `I2`; 008H–008M close active-client generation, copy/public truth, whole-client product facts, subscription state presentation, no-waterfall loading and the complete local subscription/checkout aggregate at `I3`; deployed provider, broad commercial-consistency and exact-candidate gates stay open | `WO-008`, `WO-008H`, `WO-008I`, `WO-008J`, `WO-008K`, `WO-008L`, `WO-008M` |
| 07 | Canonical Operator Center v2 and legacy admin cutover | Local package complete, including the deterministic 75-operation OpenAPI/TypeScript contract, purpose-bound Telegram OIDC Authorization Code plus PKCE login and same-identity step-up for preprovisioned operators, exact retained-bridge permissions and query-suppressed field redaction; live IdP, authenticated exact-candidate readback and cutover/rollback gates remain open | `WO-009`, `WO-009H`, `WO-009I`, `WO-009J` |
| 08 | App, cabinet and marketing UX/accessibility/performance reconciliation | Locally complete; exact-candidate performance/manual gates retained | `WO-010` |
| 09 | Legal-gated, capacity-aware marketing pilot and evidence-based decision | Locally complete (`I3` package); external pilot `NOT_AUTHORIZED` | `WO-011` |
| 10 | FRKN-derived rules; isolated AWG2 PoC, later HY2 decision | Local package complete; exact artifact/device/RU gates open | `WO-012` |
| 11 | Exact-candidate RC matrix, immutable promotion, rollback and go/no-go | Core 1.1.0 artifacts remain reproducible/bound; 013N proves public release-index source/trust-root publication, merged PR-00 isolation and the exact hosted client gate; 013O authorizes the sole-owner control, protects public Core main and advances the public trust surface to `I3`; exact final source PR/check bindings, one artifact-bound current Core revision, candidate construction and device/origin gates remain open; candidate not created | `WO-013`, `WO-013C`, `WO-013D`, `WO-013H`, `WO-013I`, `WO-013J`, `WO-013K`, `WO-013L`, `WO-013M`, `WO-013N`, `WO-013O` |

The row order is a dependency order, not permission for one giant merge. Each implementation WO must stay repository-scoped and independently reviewable.

## Queue

| WO | Outcome | Lane | Status | Dependency |
|---|---|---|---|---|
| `WO-001` | Freeze baseline and make every source-plan item trackable | Platform docs | Complete | None |
| `WO-002` | Define strict v2 on the existing release-handoff contract | Platform release contract | Complete (`I3`) | `WO-001` |
| `WO-003` | Generate v2 in the client and prove app/core/version parity | Active client | Complete (`I3`) | `WO-002` |
| `WO-003B` | Enforce v2 in release-bound cross-repository CI | Cross-repo release gates | Complete (`I3`) | `WO-003` |
| `WO-003C` | Pin reproducible Python/Node/frontend dependencies and reject drift | Platform release gates | Complete locally (`I3`) | `WO-003B` |
| `WO-003D` | Project strict v2 into runtime download and manifest identity | Platform runtime/release handoff | Implemented partially (`I2`) | `WO-003B` |
| `WO-003E` | Reconcile the shared release catalog and prove every cabinet release-card fact | Platform/web release consumers | Complete locally (`I3`) | `WO-003D`, `WO-010D1` |
| `WO-003F` | Bind release notes and visible UI version to strict v2 | Cross-repo release identity consumers | Complete locally (`I3`) | `WO-003`, `WO-003D`, `WO-003E` |
| `WO-003G` | Separate current readiness owners from retained candidate history | Cross-repo documentation/release authority | Complete locally (`I3`) | `WO-003F` |
| `WO-003H` | Reconcile package, API/UI and active documentation version truth | Cross-repo release version authority | Complete locally (`I3`) | `WO-003F`, `WO-003G` |
| `WO-003I` | Remove tracked temp helpers and enforce source/history/staging/public-index separation | Client source/release boundary | Closed by 013N (`REL/REPO-001 I3`): clean source boundary plus public v2 main, trust root, hosted source-contract run and exact readback are retained | `WO-003H`, `WO-013J`, `WO-013N` |
| `WO-003J` | Reconcile the public trust-surface and freeze/contracts aggregate without overstating unavailable evidence | Cross-repo release authority | 013N closes `REL/REPO-001`, `PR-00` and `TEST-001`; 013O closes `FE/P12-023` at `I3` under the explicit sole-owner exception without inventing independent review | `WO-003I`, `WO-006I`, `WO-008A`, `WO-010E`, `WO-013J`, `WO-013K`, `WO-013L`, `WO-013N`, `WO-013O` |
| `WO-004` | Establish state/core truth | Client/core | Complete (`I3`) | `WO-003B` |
| `WO-004A2` | Accept the one-truth direct cutover and close deterministic critical-state visual baselines | Client presentation/evidence | Complete locally (`PR-01/PR-02 I3`) | `WO-004A`, `WO-010E1` |
| `WO-004B2` | Complete the Core platform-build/security/reproducibility CI contract without overstating hosted execution | Core release CI/evidence | `CORE-001 I3`; current head `0e6b020...` passes all five hosted jobs, but is not the artifact-bound Core source and therefore does not prove the exact candidate | `WO-004B`, `WO-006C`, `WO-013I`, `WO-013N` |
| `WO-004D` | Keep ABI v3 `ConnectionStatus` out of the 1.2.0 blocker path per source authority | Core/client contract decision | Deferred post-1.2.0 (`I1`, no implementation claim) | `WO-004B`, `WO-006I` |
| `WO-005` | Correct privilege/runtime platform architecture | Client/core | Complete locally; Linux not shipped | `WO-004` |
| `WO-005C4` | Add one bounded stack-only Windows crash profile without full dumps | Active Windows client | Complete locally (`OBS-035 I3`) | `WO-005B2`, `WO-005C3`, `WO-006A` |
| `WO-005D4` | Close the bounded app-private Android lifecycle/network/power/watchdog/updater journal | Active Android client | Complete locally (`5 rows I3`) | `WO-005D1..D3`, `WO-006A`, `WO-006I` |
| `WO-006` | Build safe observability and support evidence | Cross-repo | Complete locally (`I3`) | `WO-004` |
| `WO-006I` | Split Core start failures into four safe transport classes and close Gate B | Cross-repo observability/state boundary | Complete locally (`I3`) | `WO-004`, `WO-006C` |
| `WO-006J` | Wire remaining active operational producers and permit only an Android selected-app count remotely | Cross-repo observability/support boundary | Complete locally with mixed index at execution time (`6 rows I3`, `DOD-08 I1`); `DOD-08` later closes in `WO-006L`, while PB-14 exact health-stop path remains open | `WO-006H`, `WO-010` |
| `WO-006K` | Add the no-upload short code, case-bound signed support mode, persistent indicator, cumulative caps and encrypted-only Android/Windows export | Cross-repo support/privacy boundary | Complete locally (`OBS-070..074 I3`); exact-candidate custody and physical-host proof remain open | `WO-006J`, `WO-010G3` |
| `WO-006L` | Rebuild and test the bounded sanitized Windows service journal with the current native MSVC target while keeping Linux outside the 1.2.0 matrix | Active Windows client observability boundary | Complete locally (`OBS_DOD/DOD-08 I3`); installed-service and exact-candidate Windows proof remain open | `WO-006J`, current client platform authority |
| `WO-007` | Close payment stop-ships and decompose portal seams | Platform | Complete locally (`GATE-D I3`, `ARCH-002 I2`) | `WO-003` |
| `WO-007G` | Split base admin, guarded-action and guarded-network routes without another backend or raised ceiling | Platform modular monolith | Complete partial architecture proof; `ARCH-002` remains `I2` | `WO-007F`, current Operator Center routes |
| `WO-007H` | Split public bootstrap and managed-client routes and make restored-owner slice reload ownership deterministic | Platform modular monolith | Complete partial architecture proof; `ARCH-002` remains `I2` | `WO-007G`, current public/client routes |
| `WO-007I` | Separate the single Action Intent domain-policy owner from generic persistence/execution mechanics | Platform modular monolith | Complete locally (`REL/ARCH-002 I3`) | `WO-007H`, current Operator Center policies |
| `WO-008` | Unify commercial authority and revenue attribution | Platform/client | Complete locally (`I2`); external/legal/exact-candidate gates retained | `WO-007` |
| `WO-008H` | Generate, pin and consume platform product facts in the active client without moving commercial authority | Platform/client shared contract | Complete locally (`REL/CONTRACT-001 I3`) | `WO-008A`, `WO-003H` |
| `WO-008I` | Remove live product-fact duplication and consume canonical referral/privacy/release truth | Platform/client public truth | Complete locally (`P12-129`, `ADOPT-07` I3) | `WO-008H`, `WO-008F` |
| `WO-008J` | Enforce active-client trial/reward/server-price/device-scope parity and reject local production price literals | Platform/client product-facts gate | Complete locally (`P12-024 I3`); exact-candidate device and deployed readback remain open | `WO-008H`, `WO-008I` |
| `WO-008K` | Map the server access-state matrix to the cabinet subscription title and primary action | Platform WebApp subscription policy | Complete locally (`P12-011 I3`); exact-candidate authenticated/provider/public readback remains open | `WO-008F`, `WO-008J` |
| `WO-008L` | Prove independent checkout requests start concurrently before any response on cabinet and public checkout | Platform WebApp/marketing browser gates | Complete locally (`P12-120 I3`); deployed-origin exact-candidate timing remains open | `WO-008F`, `WO-008K` |
| `WO-008M` | Close the source-plan subscription/checkout aggregate across client, cabinet, marketing and backend authorities | Cross-surface subscription/payment UX | Complete locally (`FE_PR/PR-05 I3`); exact-candidate device/provider/payment/readback remains open | `WO-008J`, `WO-008K`, `WO-008L`, `WO-010` |
| `WO-009` | Replace competing admin surfaces with Operator Center v2 | Platform/client/core | Local package complete; external exact-candidate gates open | `WO-006`, `WO-007`, `WO-008` |
| `WO-009H` | Generate the live Admin API v2 contract, consume it in AdminApp and fail closed on route/envelope drift | Platform/AdminApp API boundary | Complete locally (`OC-120 I3`); hosted clean generation and exact-candidate schema publication/readback remain open | `WO-009F4`, current v2 router and permission matrix |
| `WO-009I` | Close retained-bridge role usability, field-level redaction and real high-risk route integration | Platform/AdminApp RBAC boundary | Complete locally (`OC-110 I3`); exact-candidate IdP/step-up and real assignment/readback remain open | `WO-009H`, current role-governance authority |
| `WO-009J` | Replace compatibility-first operator entry with purpose-bound Telegram OIDC Authorization Code plus PKCE login and same-identity step-up | Platform/AdminApp identity boundary | Complete locally (`OC-100 I3`); live BotFather registration, real operator migration, legacy disablement and exact-candidate readback remain open | `WO-009I`, current operator-session authority |
| `WO-010` | Complete frontend/product path quality | Platform/client | Locally complete; Phase 11 manual gates retained | `WO-004`, `WO-008` |
| `WO-010J` | Move the release-critical update state/presentation out of the client shell and close bounded screen ownership | Active client architecture | Complete locally (`REL/ARCH-003 I3`) | `WO-010B6`, `WO-010D1` |
| `WO-011` | Prepare and, only after separate authorization, run the legally qualified capacity-bounded pilot | Platform/client | Local package complete; external execution `NOT_AUTHORIZED` | `WO-008`, `WO-009`, `WO-010` |
| `WO-011H` | Align the homepage story contract with the governed trust-led surface | Marketing tests/docs | Regression closed locally; no ledger advancement | `WO-011F` |
| `WO-012` | Evaluate transport diversity without a second client stack | Core/client/platform lab contract | Local package complete; manual/external gates retained | `WO-004`, `WO-006` |
| `WO-013` | Prove and promote the exact RC | Cross-repo/release | Active local preparation; external promotion not authorized | All release-bound WOs |
| `WO-013A2` | Replace circular phase/plan preflight logic with an exact fail-safe row-stage policy | Platform release preflight | Complete locally; no ledger advancement | `WO-001`, `WO-013A` |
| `WO-013A3` | Move PB-14 out of the circular local-freeze lane because its signed-manifest health-stop proof requires an exact candidate | Platform release preflight | Complete locally; no ledger advancement, PB-14 remains unproved | `WO-013A2`, `WO-006J` |
| `WO-013C` | Make Linux non-shipment and Android OEM background/permission/surface limitations explicit and machine-bound | Platform/client release limitations | Complete locally (`REL_DOD/DOD-17 I3`); exact-candidate release notes and physical OEM proof remain open | `WO-005`, `WO-006`, `WO-013` |
| `WO-013D` | Make the client stable pointer reversible through an exact rollback catalog, atomic switch contract and retained evidence | Client/platform release rollback | Complete locally (`FE/P12-130 I3`); exact-candidate portal/runtime drill remains `NOT_RUN` | `WO-003`, `WO-013C` |
| `WO-013H` | Freeze clean platform/client/Core source identities and retain honest preflight blockers | Cross-repo release source freeze | Complete local evidence; no ledger advancement, candidate remains uncreated | `WO-013B`, `WO-013C`, `WO-013D` |
| `WO-013I` | Build Core 1.1.0 Android/Windows artifacts twice, bind exact bytes to the active client and verify them in preflight | Core/client/platform artifact boundary | Complete local pre-candidate evidence; no ledger advancement, three real preflight blockers remain | `WO-013H`, `WO-004B2` |
| `WO-013J` | Audit the real public baseline and implement a fail-closed signed/same-byte release-index source contract | Public release-index/platform preflight | Source/trust-root publication closed by 013N (`REL/REPO-001 I3`); 013O resolves the sole-owner review precondition (`FE/P12-023 I3`); exact signed candidate assets remain `I4` | `WO-003I`, `WO-003J`, `WO-013I`, `WO-013N`, `WO-013O` |
| `WO-013K` | Prove PR-00 as one isolated local evidence-only commit with no visible UI delta | Platform release review boundary | Hosted isolation and merge closed by 013N (`PR-00 I3`); PR 18 and scoped follow-up PR 19 are merged, while non-author review remains a separate policy blocker | `WO-003J`, `WO-013H`, `WO-013J`, `WO-013N` |
| `WO-013L` | Isolate an exact hosted Ubuntu client-gate control over the frozen three-repository tuple | Platform CI control/client gate | Exact hosted proof closed by 013N (`TEST-001 I3`): PR 17/run 32621490357 passes the full standard gate; control PR remains open and candidate evidence remains separate | `WO-003B`, `WO-013H`, `WO-013I`, `WO-013K`, `WO-013N` |
| `WO-013M` | Make the branch-policy STOP-SHIP gate verify the complete review, provenance and anti-bypass contract | Cross-repository promotion policy | Superseded by 013O for the sole-owner 1.2.0 lane; normal team-review policy remains the baseline | `WO-013B`, `WO-013H`, `WO-013L` |
| `WO-013N` | Publish and read back the release-index trust root, merge hosted PR-00, and prove the exact hosted client standard gate | Public index/platform/client/Core pre-freeze evidence | Complete (`REL/REPO-001`, `FE_PR/PR-00`, `REL/TEST-001 I3`); candidate remains uncreated | `WO-013J`, `WO-013K`, `WO-013L`, owner GitHub authorization |
| `WO-013O` | Replace the unavailable second reviewer/private-plan enforcement with an explicit fail-closed owner-solo PR/check control | Cross-repository promotion policy | Exception authorized; public Core main protection passes; `FE/P12-023 I3`; exact final platform/client/Core PR bindings remain pending for `REL-001`/`DOD-09` | `WO-013M`, `WO-013N`, explicit sole-owner authorization |

## Current evidence

- `BASELINE.json` records repository heads and observed gaps as of 2026-08-21.
- `EXECUTION-LEDGER.csv` is the machine-readable item register; `(plan,id)` is the primary key.
- `EXECUTION-INDEX.md` defines the completion index and aggregate reporting rules.
- `SOURCE-CROSSWALK.md` preserves plan coverage and conflict decisions.
- `evidence/013H-clean-source-freeze/013H-clean-source-freeze.json` binds the
  clean source commits, local gates and five remaining preflight blockers.
- `evidence/013I-core-artifact-binding/013I-core-artifact-binding.json` binds
  the reproducible Core 1.1.0 bytes, clean client adoption and the reduced
  three-blocker preflight without claiming a candidate.
- `evidence/013J-public-release-index/013J-public-release-index.json` binds the
  audited legacy public baseline, local v2 contract revision, expected
  owner-key failure and unpublished four-blocker preflight.
- `evidence/013K-pr00-isolated-result/013K-pr00-isolated-result.json` binds the
  exact release-base-isolated PR-00 commit, its nine allowlisted paths, four
  exact snapshots, withdrawn local-parent proof and honest hosted-check ceiling.
- `evidence/013L-hosted-client-gate-control/013L-hosted-client-gate-control.json`
  binds the release-base-isolated five-path CI control, immutable source tuple,
  owner-only credential boundary and honest `NOT_RUN` hosted ceiling.
- `evidence/013M-branch-policy-stop-ship/013M-branch-policy-stop-ship.json`
  binds the clean full-policy verifier, exact required-check sets, current live
  branch results, zero eligible non-author reviewers and honest `NO_GO` state.
- `evidence/013N-authorized-prefreeze-closure/013N-authorized-prefreeze-closure.json`
  binds public release-index main and key readback, merged PR-00 checks, the
  exact hosted client `SUCCESS` tuple, secret names without private material,
  supporting Core CI and the honest no-candidate ceiling.
- `evidence/013O-owner-solo-promotion-control/013O-owner-solo-promotion-control.json`
  binds the explicit sole-owner decision, false-independent-review marker,
  public Core protection readback, clean source tuple and pending exact PR
  controls without claiming a candidate.

## Collision and promotion gates

- Before each WO: inspect branch/status/diff in every repository in its write scope.
- Never overwrite dirty or concurrent work; use a scoped branch/worktree and stage only authorized files.
- No deployment, production mutation, payment action, campaign launch, external message, branch-protection change or artifact promotion is authorized by this index alone.
- Exact runtime/manual gates use the repository labels: `PASS`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS`, `NOT_REQUESTED`.
- Stable promotion is prohibited while a STOP-SHIP row is below `I4` or any required exact-candidate gate lacks retained evidence.

## Next action

All explicit local `pre_freeze` rows and the public trust surface are now
`I3`. Assemble one current platform/client/artifact-bound-Core tuple and open
the three exact promotion PRs. Bind every PR number, base and 40-hex head in
one `owner-solo-pr-evidence.v1` file; the live gate must observe every named
GitHub App check successful before `REL/REL-001` or `REL_DOD/DOD-09` advances.
No manual click is needed merely to manufacture self-approval.

Then enter the 33-row candidate lane with that frozen tuple and retain signing, SBOM/provenance,
physical Android/Windows, current/brain/RU-origin, rollback and Gate F evidence.
The remaining 16 external and 21 deferred rows keep their existing authority
boundaries. Do not deploy, mutate production, execute a payment, enroll a
campaign cohort or claim RU/stable readiness without the separate authority
and exact evidence required by the owning gate.
