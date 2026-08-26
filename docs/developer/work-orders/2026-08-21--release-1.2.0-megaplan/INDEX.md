# POKROV 1.2.0 Megaplan — Wave Index

Last updated: 2026-08-27
Classification: `ACTIVE_EXECUTION`
Wave status: `PHASE_11_CANDIDATE2_SIGNED_PRIVATE_CARRIER_AND_BOUNDED_WINDOWS_CLEAN_HOST_PROVED`
Release candidate: `POKROV_1_2_0_CANDIDATE2_PRIVATE_PRERELEASE_PUBLIC_RELEASE_NOT_CREATED`

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
| 01 | Release manifest, version/provenance contract, CI and stop-ship controls | Release-v2, client adoption, release-bound CI, reproducible dependencies, shared catalog and cross-repository truth are proved; the public-index source/trust root is on public main, PR-00 is merged, and `OWNER_SOLO_EXCEPTION` explicitly replaces the unavailable second reviewer without claiming independent review; exact platform/client/Core PR heads, app-bound checks, signed merges and post-merge promotion runs are retained at `I3` | `WO-002`, `WO-003`, `WO-003B`, `WO-003C`, `WO-003D`, `WO-003E`, `WO-003F`, `WO-003G`, `WO-003H`, `WO-003I`, `WO-003J`, `WO-013J`, `WO-013K`, `WO-013L`, `WO-013M`, `WO-013N`, `WO-013O`, `WO-013P` |
| 02 | Typed connection state, proof-driven green state, core ABI and migrations | 004A/004A2, 004B/004B2, 004C and aggregate Gate B are `I3`; direct cutover and deterministic visual baselines are explicit; ABI v3 is deferred until after 1.2.0; final Core main passes all five hosted jobs and is the same source revision used for the locally reproducible Android/Windows bytes embedded by final client main; candidate signing and device proof remain open | `WO-004`, `WO-004A2`, `WO-004B2`, `WO-004D`, `WO-006I`, `WO-013N`, `WO-013P` |
| 03 | Windows/Android runtime boundaries; conditional Linux beta foundation | Locally complete: Windows service/recovery/journal and stack-only crash profile plus Android runtime/private operational producers are proved; Linux explicitly not shipped in 1.2.0 | `WO-005`, `WO-005C4`, `WO-005D4` |
| 04 | Observability, error catalog, redacted bundle and support pipeline | Locally complete (`I3`) for shipped Android/Windows scope, including four-class safe transport failures, active operational producers, Android count-only routing, no-upload short code, signed temporary support mode, encrypted-only manual export and a current 7/7 MSVC native proof for the bounded Windows service journal; 013S proves the active public pin and hosted source-control custody, while deployed runtime/RBAC/audit and exact-candidate device evidence remain open; Linux remains explicitly not shipped | `WO-006`, `WO-006I`, `WO-006J`, `WO-006K`, `WO-006L`, `WO-013S` |
| 05 | Portal bounded contexts, payments, HTTP/DB/outbox reliability | Locally complete (`GATE-D` and `ARCH-002` at `I3`); 007G–007I split admin, public/client and Action Intent domain/runtime owners | `WO-007`, `WO-007G`, `WO-007H`, `WO-007I` |
| 06 | Product facts, subscriptions, checkout, offers and attribution | Local source packages: 008A–008G commercial package at `I2`; 008H–008M close active-client generation, copy/public truth, whole-client product facts, subscription state presentation, no-waterfall loading and the complete local subscription/checkout aggregate at `I3`; deployed provider, broad commercial-consistency and exact-candidate gates stay open | `WO-008`, `WO-008H`, `WO-008I`, `WO-008J`, `WO-008K`, `WO-008L`, `WO-008M` |
| 07 | Canonical Operator Center v2 and legacy admin cutover | Local package complete, including the deterministic 75-operation OpenAPI/TypeScript contract, purpose-bound Telegram OIDC Authorization Code plus PKCE login and same-identity step-up for preprovisioned operators, exact retained-bridge permissions and query-suppressed field redaction; live IdP, authenticated exact-candidate readback and cutover/rollback gates remain open | `WO-009`, `WO-009H`, `WO-009I`, `WO-009J` |
| 08 | App, cabinet and marketing UX/accessibility/performance reconciliation | Locally complete; exact-candidate performance/manual gates retained | `WO-010` |
| 09 | Legal-gated, capacity-aware marketing pilot and evidence-based decision | Locally complete (`I3` package); external pilot `NOT_AUTHORIZED` | `WO-011` |
| 10 | FRKN-derived rules; isolated AWG2 PoC, later HY2 decision | Local package complete; exact artifact/device/RU gates open | `WO-012` |
| 11 | Exact-candidate RC matrix, immutable promotion, rollback and go/no-go | 013AC makes signed `pokrov-1.2.0-candidate.2` the current exact basis: six hashes/source tuple validate, a private prerelease retains the Windows installer and signed outputs, exact hosted platform/client release gates pass, the bounded Windows clean-host service/IPC/install/uninstall slice passes, and PB-14 is replayed on candidate.2. Android is production-signed; Windows retains the owner-approved unsigned direct-beta exception. No public `v1.2.0`, six public assets or stable pointer exists, and exact physical Beeline/OEM, live Windows TUN/DNS/rollback, aggregate origins, provider, Operator, legal and promotion gates remain open | `WO-013`, `WO-013C`, `WO-013D`, `WO-013E`, `WO-013H`, `WO-013I`, `WO-013J`, `WO-013K`, `WO-013L`, `WO-013M`, `WO-013N`, `WO-013O`, `WO-013P`, `WO-013Q`, `WO-013R`, `WO-013S`, `WO-013T`, `WO-013U`, `WO-013V`, `WO-013W`, `WO-013X`, `WO-013Y`, `WO-013Z`, `WO-013AA`, `WO-013AB`, `WO-013AC` |

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
| `WO-004B2` | Complete the Core platform-build/security/reproducibility CI contract without overstating hosted execution | Core release CI/evidence | `CORE-001 I3`; 013P binds final Core main `bdbd97f...` to five successful hosted jobs and to the locally reproducible Android/Windows bytes embedded by final client main; exact-candidate signing/device evidence remains open | `WO-004B`, `WO-006C`, `WO-013I`, `WO-013N`, `WO-013P` |
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
| `WO-013` | Prove and promote the exact RC | Cross-repo/release | Final source promotion complete; candidate construction, signing and external promotion not authorized or run | All release-bound WOs |
| `WO-013A2` | Replace circular phase/plan preflight logic with an exact fail-safe row-stage policy | Platform release preflight | Complete locally; no ledger advancement | `WO-001`, `WO-013A` |
| `WO-013A3` | Move PB-14 out of the circular local-freeze lane because its signed-manifest health-stop proof requires an exact candidate | Platform release preflight | Complete locally; no ledger advancement, PB-14 remains unproved | `WO-013A2`, `WO-006J` |
| `WO-013C` | Make Linux non-shipment and Android OEM background/permission/surface limitations explicit and machine-bound | Platform/client release limitations | Complete locally (`REL_DOD/DOD-17 I3`); exact-candidate release notes and physical OEM proof remain open | `WO-005`, `WO-006`, `WO-013` |
| `WO-013D` | Make the client stable pointer reversible through an exact rollback catalog, atomic switch contract and retained evidence | Client/platform release rollback | Complete locally (`FE/P12-130 I3`); exact-candidate portal/runtime drill remains `NOT_RUN` | `WO-003`, `WO-013C` |
| `WO-013E` | Retain the physical Android/Beeline and LDPlayer runtime slice and reconcile mobile failures with deployed type-2/type-3 server evidence | Client/platform/Core runtime evidence | Partial pre-candidate evidence recorded; no ledger advancement, complete OEM/origin matrix and RC remain open | `WO-013`, `WO-012`, `WO-013U`, current deployed/source tuple |
| `WO-013H` | Freeze clean platform/client/Core source identities and retain honest preflight blockers | Cross-repo release source freeze | Complete local evidence; no ledger advancement, candidate remains uncreated | `WO-013B`, `WO-013C`, `WO-013D` |
| `WO-013I` | Build Core 1.1.0 Android/Windows artifacts twice, bind exact bytes to the active client and verify them in preflight | Core/client/platform artifact boundary | Closed into final source tuple by 013P: final Core source, locally reproducible bytes and final client embedding are bound; candidate signing/device proof remains open | `WO-013H`, `WO-004B2`, `WO-013P` |
| `WO-013J` | Audit the real public baseline and implement a fail-closed signed/same-byte release-index source contract | Public release-index/platform preflight | Source/trust-root publication closed by 013N (`REL/REPO-001 I3`); 013O resolves the sole-owner review precondition (`FE/P12-023 I3`); exact signed candidate assets remain `I4` | `WO-003I`, `WO-003J`, `WO-013I`, `WO-013N`, `WO-013O` |
| `WO-013K` | Prove PR-00 as one isolated local evidence-only commit with no visible UI delta | Platform release review boundary | Hosted isolation and merge closed by 013N (`PR-00 I3`); PR 18 and scoped follow-up PR 19 are merged; normal non-author review was explicitly replaced for 1.2.0 by 013O and final exact controls are retained by 013P | `WO-003J`, `WO-013H`, `WO-013J`, `WO-013N`, `WO-013O`, `WO-013P` |
| `WO-013L` | Isolate an exact hosted Ubuntu client-gate control over the frozen three-repository tuple | Platform CI control/client gate | Exact hosted proof closed by 013N (`TEST-001 I3`): PR 17/run 32621490357 passes the full standard gate; control PR remains open and candidate evidence remains separate | `WO-003B`, `WO-013H`, `WO-013I`, `WO-013K`, `WO-013N` |
| `WO-013M` | Make the branch-policy STOP-SHIP gate verify the complete review, provenance and anti-bypass contract | Cross-repository promotion policy | Superseded by 013O for the sole-owner 1.2.0 lane; normal team-review policy remains the baseline | `WO-013B`, `WO-013H`, `WO-013L` |
| `WO-013N` | Publish and read back the release-index trust root, merge hosted PR-00, and prove the exact hosted client standard gate | Public index/platform/client/Core pre-freeze evidence | Complete (`REL/REPO-001`, `FE_PR/PR-00`, `REL/TEST-001 I3`); candidate remains uncreated | `WO-013J`, `WO-013K`, `WO-013L`, owner GitHub authorization |
| `WO-013O` | Replace the unavailable second reviewer/private-plan enforcement with an explicit fail-closed owner-solo PR/check control | Cross-repository promotion policy | Complete policy decision; exact final PR/check execution and row closure are retained by 013P | `WO-013M`, `WO-013N`, explicit sole-owner authorization |
| `WO-013P` | Promote and retain the final source tuple under exact owner-solo PR/check controls | Platform/client/Core source promotion | Complete (`REL/REL-001`, `REL_DOD/DOD-09 I3`); candidate remains uncreated | `WO-013O`, exact hosted PR checks, owner GitHub authorization |
| `WO-013Q` | Assemble and retain the exact local pre-candidate app artifacts, SBOM/provenance, checksums and strict handoff | Client/platform release evidence | Partial implementation (`REL_DOD/DOD-15 I2`): Android production signing passes; Windows trusted signing/support key and all candidate/manual/promotion proof remain open | `WO-013P`, frozen source tuple, explicit candidate-preparation authorization |
| `WO-013R` | Merge fail-closed Windows Authenticode and deterministic secret-only public-index signing controls without manufacturing a candidate | Client/public-index/platform release evidence | Controls merged and hosted source gates pass; no row advances because the trusted Windows certificate, support key, rebuilt artifacts and signed candidate index remain absent | `WO-013Q`, owner-solo PR authorization, explicit release continuation |
| `WO-013S` | Bind the support-mode public pin to active client source and prove hosted private-key custody without exposing secrets or mutating production | Client/platform support-signing boundary | Source/build input and hosted custody proved; `REL_DOD/DOD-15` remains `I2` and `OBS/OBS-072` remains `I3` because trusted Windows signing, rebuilt candidate artifacts and deployed runtime/device proof remain absent | `WO-013R`, owner-solo PR authorization, hosted repository secrets/variables |
| `WO-013T` | Prove a non-mutating trusted-Windows-signing readiness path and audit the exact local/hosted custody gap | Client/platform Windows signing boundary | Readiness control and exact self-signed/`UntrustedRoot` blocker proved; `REL_DOD/DOD-15` remains `I2`, candidate remains uncreated | `WO-013S`, client PR 13 hosted gate, local certificate-store and GitHub configuration readback |
| `WO-013U` | Apply the exact owner-approved unsigned Windows 1.2.0 direct-beta exception and rebuild the current artifact/supply-chain set | Client/platform release evidence | Current six-file set, production Android signing, Windows `SKIPPED_BY_OWNER`, embedded support pin, SBOM/provenance, strict handoff and 23/23 checksums proved; `REL_DOD/DOD-15` remains `I2`, candidate/publication remain uncreated | `WO-013T`, client PR 14 and post-merge hosted gates, exact local build tuple |
| `WO-013V` | Rebuild the exact local pre-candidate set and retain byte-identical LDPlayer/runtime evidence | Client/platform release evidence | Six current artifacts, production Android signing, owner-approved unsigned Windows, strict supply/checksum bundle and exact LDPlayer proof recorded; no ledger advancement, physical/manual/origin gates and candidate remain open | `WO-013E`, `WO-013U`, current clean source tuple |
| `WO-013W` | Correct and retain the direct current-origin API performance method without manufacturing a deploy or aggregate gate pass | Platform performance/release evidence | Clean source-bound health/catalog p95 pass with real persistent warmups; backend deploy is not required, aggregate current-origin/candidate/device gates remain open and no row advances | `WO-010I`, `WO-013V`, platform PRs 34/35, owned direct-origin evidence |
| `WO-013X` | Retain exact LDPlayer 4030 DNS/AI/Games state and bounded content reachability without manufacturing service or physical-device proof | Client/platform release evidence | Saint Petersburg direct VPN path, persisted controls, owned/Google/Gemini/Xbox reachability and final disconnect recorded; ChatGPT returns 403 and remains `NOT_PASS`, no deploy or ledger advancement | `WO-013V`, `WO-013W`, exact installed x86_64 bytes |
| `WO-013Y` | Sign and independently read back the exact tracked candidate manifest without publishing assets or promoting stable | Public release-index/platform release evidence | PR/post-merge gates and secret-backed signer pass on public main; manifest/signature/receipt are retained and verified, `OBS_DOD/DOD-29` reaches `I4`; public asset, runtime and promotion gates remain open | `WO-013V`, public release-index PR 4, owner solo authorization, exact tracked template |
| `WO-013Z` | Preserve the redacted Brain-origin pre-candidate readiness/delivery slice under a non-colliding work-order identity | Platform operations/release evidence | Clean Brain readiness 23/23, live delivery 7/7 and runtime app/provider 8/8 pass; exact-candidate Brain gate remains open, separate former-free MTProto diagnostic fails and no row advances | `WO-013W`, platform PR 37, owned Brain access, superseded conflicting PR 38 branch evidence |
| `WO-013AA` | Reconcile the red exact Core aggregate with exact-source product jobs and the corrected product-identical CI control | Core/client/platform release evidence | Exact Core 344b317 product/security/platform jobs pass; old aggregate stays red for missing client LFS checkout; workflow-only control 9b94e0b passes all five jobs and `REL_DOD/DOD-10` reaches `I3` | `WO-013I`, `WO-013Y`, Core PR 4 and runs 32944235783/32946337754/32947422554 |
| `WO-013AB` | Bind the retained signed candidate to a real local release-health breach and guarded rollout rollback request | Platform observability/release control | Exact manifest signature passes against the c1d6170 keyring; isolated 4030 UPD-004 blocks observation close and drives candidate policy to zero, so `OBS_PB/PB-14` reaches `I3`; external switch and production cohort remain unproved | `WO-006J`, `WO-013Y`, exact signed candidate bytes |
| `WO-013AC` | Replace candidate.1 as current truth with signed/private-carrier candidate.2 and reconcile hosted source, Windows clean-host and PB-14 evidence | Cross-repository candidate/release evidence | Candidate.2 signature/source/supply/private-carrier digests pass; exact hosted platform/client gates and bounded Windows service/IPC clean-host slice reach candidate proof; PB-14 is replayed; public v1.2.0, live TUN/DNS, physical Android, origins and stable promotion remain open | `WO-013AB`, platform PR 42, client PRs 21/22, release-index PRs 5/6, exact signed candidate.2 bytes |

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
- `evidence/013P-final-source-promotion/013P-final-source-promotion.json`
  binds the final signed source tuple, exact PR heads and required checks,
  post-merge promotion runs, final Core artifact hashes, complete 3/3 solo
  readback and the honest no-candidate ceiling.
- `evidence/013Q-local-pre-candidate-assembly/013Q-local-pre-candidate-assembly.json`
  binds the six exact local app artifacts, Android production signer, unsigned
  Windows result, SBOM/provenance, strict-v2 handoff, corrected preflight and
  the remaining 12 promotion gates without claiming an RC or public release.
- `evidence/013R-signing-controls/013R-signing-controls.json` binds merged
  Windows and public-index signing controls, exact PR/check revisions, the
  retained invalid-workflow correction, missing trusted certificate/support
  key and the superseded pre-candidate boundary without claiming signatures.
- `evidence/013S-support-signing-custody/013S-support-signing-custody.json`
  binds client public-pin source control, exact PR/merge/check revisions and the
  hosted public custody receipt while retaining the missing Windows signer,
  uncreated candidate and untouched production-runtime boundary.
- `evidence/013T-windows-signing-readiness/013T-windows-signing-readiness.json`
  binds the readiness-only control, exact client PR/merge/check revisions, two
  retained self-signed private-key identities, SignTool and GitHub-config
  readbacks, and the honest no-trusted-signer/no-candidate ceiling.
- `evidence/013U-owner-approved-direct-beta-assembly/013U-owner-approved-direct-beta-assembly.json`
  binds the exact owner exception, client PR/merge/check revisions, current
  retained six-file artifact set, production Android signer, unsigned Windows manifest,
  embedded support pin, SBOM/provenance, strict handoff, checksums and the ten
  remaining gates without claiming a public release or production mutation.
- `evidence/013V-exact-local-pre-candidate-and-ldplayer/013V-exact-local-pre-candidate-and-ldplayer.json`
  binds the rebuilt six-file set, exact assembly/deployed-runtime boundary,
  production Android signer, unsigned-Windows exception, complete 36-entry
  staging manifest and byte-identical LDPlayer install/runtime evidence while
  retaining the physical/manual/origin and no-candidate ceilings.
- `evidence/013W-current-origin-api-method/013W-current-origin-api-method.json`
  binds the source-address isolation, corrected persistent warmup method,
  signed platform merges, clean health/catalog p95 passes, diagnostic manifest
  and no-deploy decision while retaining the aggregate current-origin,
  candidate, physical-device, Brain/RU and promotion ceilings.
- `evidence/013X-exact-ldplayer-content-reachability/013X-exact-ldplayer-content-reachability.json`
  binds the byte-identical 4030 emulator target, Saint Petersburg direct VPN
  path, persisted DNS/AI/Games controls, bounded owned/Google/ChatGPT/Gemini/Xbox
  results and final disconnected state. The paired screenshots are retained by
  size and SHA-256; ChatGPT functionality and all physical/origin gates remain
  explicitly unproved.
- `evidence/013Y-signed-candidate-manifest/013Y-signed-candidate-manifest.json`
  binds public release-index PR/main checks, the exact secret-backed signer run,
  downloaded Actions artifact, independent public-key validation and retained
  manifest/signature/receipt bytes. It advances only the signed observability
  contract-hash oracle and preserves the no-public-assets/no-promotion ceiling.
- `evidence/013Z-brain-origin-pre-candidate-runtime/013Z-brain-origin-pre-candidate-runtime.json`
  preserves the clean redacted Brain readiness, seven-node live delivery,
  runtime app/provider readback and separate closed MTProto diagnostic captured
  before the signed manifest artifact existed. It does not claim candidate
  runtime and advances no row.
- `evidence/013AA-core-candidate-ci-reconciliation/013AA-core-candidate-ci-reconciliation.json`
  binds the red exact-source aggregate, its four successful product jobs, the
  missing-LFS release-contract failure and the product-identical workflow-only
  correction whose PR and post-merge runs pass all five jobs. It advances only
  `REL_DOD/DOD-10` to `I3`.
- `evidence/013AB-pb14-exact-candidate-health-stop/013AB-pb14-exact-candidate-health-stop.json`
  revalidates the retained manifest/signature/receipt against the exact public
  keyring, binds the signed candidate to one identity-free 4030 health breach
  and proves local observation stop plus guarded zero-distribution rollback
  request. It does not claim an external artifact switch or production cohort.
- `evidence/013AC-candidate2-reconciliation/013AC-candidate2-signed-manifest.json`
  replaces candidate.1 as current truth with the independently verified
  candidate.2 manifest/signature/receipt, exact source tuple, signer run and
  private prerelease carrier digest readback.
- `evidence/013AC-candidate2-reconciliation/013AC-windows-clean-host.json`
  retains the exact hosted Windows install/service/authenticated-IPC/restart/
  uninstall/idle-network evidence and its explicit live-network/manual ceiling.
- `evidence/013AC-candidate2-reconciliation/013AC-pb14-candidate2-health-stop.json`
  replays PB-14 against candidate.2 and proves only the isolated local
  health-stop/rollback-request control.
- `evidence/013AC-candidate2-reconciliation/013AC-candidate2-reconciliation.json`
  binds the complete candidate.2 hashes, hosted runs, supply chain, publication
  boundary, scoped ledger advances and remaining exact-candidate gates.
- `evidence/013E-android-mobile-runtime-matrix/013E-android-mobile-runtime-matrix.json`
  binds the newer Android artifact identity, single physical Beeline matrix,
  LDPlayer evidence ceiling, deployed server-chain reconciliation and explicit
  no-candidate/no-ledger-advancement decision for the observed runtime tuple.

## Collision and promotion gates

- Before each WO: inspect branch/status/diff in every repository in its write scope.
- Never overwrite dirty or concurrent work; use a scoped branch/worktree and stage only authorized files.
- No deployment, production mutation, payment action, campaign launch, external message, branch-protection change or artifact promotion is authorized by this index alone.
- Exact runtime/manual gates use the repository labels: `PASS`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS`, `NOT_REQUESTED`.
- Stable promotion is prohibited while a STOP-SHIP row is below `I4` or any required exact-candidate gate lacks retained evidence.

## Next action

013AC is the current release truth. Signed
`pokrov-1.2.0-candidate.2` binds platform/client/Core/release-index
`c5f3fca...` / `e6c29d1...` / `344b317...` / `4c6d46c...`, five
production-signed Android artifacts and the owner-approved unsigned Windows
installer `4226daa4...`. Its detached signature validates independently. The
private client prerelease retains the installer and three signed outputs with
matching GitHub digests; it is not a public or stable release.

The exact candidate.2 Windows clean-host run proves machine-wide install,
eight installed-file hashes, LocalSystem service identity, authenticated
UI/service IPC, SCM restart, clean uninstall and unchanged idle route/DNS. It
does not prove live TUN, connected DNS/leak behavior, authenticated egress,
crash/reboot, uninstall while connected or interactive SmartScreen. PB-14 has
also been replayed on candidate.2 and remains a local isolated control at
`I3`, not deployed-cohort evidence.

The platform self-hop guard is deployed at candidate-bound `c5f3fca...`.
SPB remains a dual-role delivery/bridge node, but its own bridge is excluded
when SPB is the selected destination. The earlier Beeline failure of both SPB
direct and type 3 is therefore tracked as a shared SPB entry-path/carrier
failure; it is not exact candidate.2 physical-device proof.

Next execute the exact candidate.2 Android physical Beeline/OEM matrix and the
Windows live TUN/DNS/egress/connected-rollback matrix. Then retain aggregate
current-origin, exact-candidate Brain-origin, RU-origin, provider, Operator and
legal evidence. Public `v1.2.0`, six public assets, same-byte promotion and a
stable pointer remain prohibited until required STOP-SHIP rows reach `I4` and
the owner explicitly authorizes publication. The Windows SmartScreen warning
remains mandatory; AWG 3.1 remains default-off and `BLOCKED_BY_ACCESS` until an
isolated owned target exists.
