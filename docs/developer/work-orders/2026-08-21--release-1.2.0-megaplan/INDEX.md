# POKROV 1.2.0 Megaplan — Wave Index

Last updated: 2026-08-28
Classification: `ACTIVE_EXECUTION`
Wave status: `PHASE_11_CANDIDATE3_NO_GO_REPLACEMENT_PRE_CANDIDATE_LOCALLY_PROVED`
Release candidate: `POKROV_1_2_0_CANDIDATE3_PRIVATE_PRERELEASE_PUBLIC_RELEASE_NOT_CREATED`

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
| 03 | Windows/Android runtime boundaries; conditional Linux beta foundation | Windows service/recovery/journal and Android runtime/private producers are locally proved. WO-013AL evaluates exact candidate.3 and leaves Gate C `BLOCKED` at `I2`: Windows live TUN/DNS/recovery and authenticated physical Android/OEM/store matrices remain open. WO-005G's later fail-closed Linux source foundation is not shipped in candidate.3 or the public 1.2.0 pair | `WO-005`, `WO-005C4`, `WO-005D4`, `WO-005G`, `WO-013AL` |
| 04 | Observability, error catalog, redacted bundle and support pipeline | Locally complete (`I3`) for shipped Android/Windows scope, including four-class safe transport failures, active operational producers, Android count-only routing, no-upload short code, signed temporary support mode, encrypted-only manual export and a current 7/7 MSVC native proof for the bounded Windows service journal; 013S proves the active public pin and hosted source-control custody, while deployed runtime/RBAC/audit and exact-candidate device evidence remain open; Linux remains explicitly not shipped | `WO-006`, `WO-006I`, `WO-006J`, `WO-006K`, `WO-006L`, `WO-013S` |
| 05 | Portal bounded contexts, payments, HTTP/DB/outbox reliability | Locally complete (`GATE-D` and `ARCH-002` at `I3`); 007G–007I split admin, public/client and Action Intent domain/runtime owners. WO-013AM passes the frozen candidate source matrix but leaves Gate D `BLOCKED` below I4 until production provider/PostgreSQL/outbox/reconciliation/rollback proof exists | `WO-007`, `WO-007G`, `WO-007H`, `WO-007I`, `WO-013AM` |
| 06 | Product facts, subscriptions, checkout, offers and attribution | Local source packages: 008A–008G commercial package at `I2`; 008H–008M close active-client generation, copy/public truth, whole-client product facts, subscription state presentation, no-waterfall loading and the complete local subscription/checkout aggregate at `I3`; deployed provider, broad commercial-consistency and exact-candidate gates stay open | `WO-008`, `WO-008H`, `WO-008I`, `WO-008J`, `WO-008K`, `WO-008L`, `WO-008M` |
| 07 | Canonical Operator Center v2 and legacy admin cutover | Local package complete, including the deterministic 75-operation OpenAPI/TypeScript contract, purpose-bound Telegram OIDC Authorization Code plus PKCE login and same-identity step-up for preprovisioned operators, exact retained-bridge permissions and query-suppressed field redaction; live IdP, authenticated exact-candidate readback and cutover/rollback gates remain open | `WO-009`, `WO-009H`, `WO-009I`, `WO-009J` |
| 08 | App, cabinet and marketing UX/accessibility/performance reconciliation | Locally complete at `I3`; WO-013AN passes exact-candidate local UI/accessibility/responsive/static/API slices but leaves Gate E `BLOCKED` below I4 on authenticated, physical screen-reader/device, comparable-artifact, browser-lab, RU-origin and post-promotion evidence | `WO-010`, `WO-013AN` |
| 09 | Legal-gated, capacity-aware marketing pilot and evidence-based decision | Locally complete (`I3` package); external pilot `NOT_AUTHORIZED` | `WO-011` |
| 10 | FRKN-derived rules and isolated AWG2/AWG3.1/HY2/Smart-DNS owner labs | AWG2/AWG3.1 and bounded base HY2 source labs are locally proved and default-off; HY2 has a byte-identical immutable server bundle and guarded remote installer, and its read-only owned-node plan proves a conflict-free `443/udp` target while blocking APPLY on absent Brain kill-switch/runtime material. WO-013AS advances the selective, non-recursive Smart DNS and opaque SNI relay lab to `I3`: exact pushed source, byte-reproducible server bundle, guarded installer source/tests, full client regression, production-signed build-4046 packages and LDPlayer/Huawei default-off/state-machine proof pass. Its dedicated-node PLAN/deploy and live DNS/SNI/access/leak/rollback evidence remain pending. Deploy/handshake and all exact device/RU gates remain open; Gecko, Mimic and port hopping remain monitor-only | `WO-012`, `WO-013AO`, `WO-013AR`, `WO-013AS` |
| 11 | Exact-candidate RC matrix, immutable promotion, rollback and go/no-go | 013AE makes signed `pokrov-1.2.0-candidate.3` the current exact-candidate basis. Its Gate F remains `NO_GO`: 5 of 19 checks pass, 14 remain non-PASS and Gate B has one explicit candidate failure. 013AO separately binds the replacement pre-candidate baseline; 013AR adds the default-off managed HY2 source, client/server artifacts and production-signed Android install/launch proof at `I3`; 013AS now adds an `I3` selective Smart-DNS source/artifact/device-state checkpoint without a server deploy or live access claim. None creates a new candidate or live transport/access claim. No public `v1.2.0`, stable switch or promotion occurred; exact-candidate physical Android, Windows live network/recovery, HY2/Smart-DNS server deploy and runtime matrices, RU-origin, authenticated egress, provider/PostgreSQL/outbox runtime, Operator, legal and device/browser performance gates remain open | `WO-013`, `WO-013C`, `WO-013D`, `WO-013E`, `WO-013H`, `WO-013I`, `WO-013J`, `WO-013K`, `WO-013L`, `WO-013M`, `WO-013N`, `WO-013O`, `WO-013P`, `WO-013Q`, `WO-013R`, `WO-013S`, `WO-013T`, `WO-013U`, `WO-013V`, `WO-013W`, `WO-013X`, `WO-013Y`, `WO-013Z`, `WO-013AA`, `WO-013AB`, `WO-013AC`, `WO-013AD`, `WO-013AE`, `WO-013AF`, `WO-013AG`, `WO-013AH`, `WO-013AI`, `WO-013AJ`, `WO-013AK`, `WO-013AL`, `WO-013AM`, `WO-013AN`, `WO-013AO`, `WO-013AQ`, `WO-013AR`, `WO-013AS`, `WO-010K` |

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
| `WO-005G` | Reopen one fail-closed Linux daemon/non-root UI source foundation without adding it to candidate.3 | Active client conditional Linux lane | Source locally proved (`LNX-001 I3`); live connect, network transactions, signed package and clean VM matrix remain open | `WO-005E`, `WO-013C`, `WO-013` |
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
| `WO-010K` | Reconcile the conditional support streaming row and complete the source-plan adaptive polling contract without adding a second transport | Active client support/release evidence | `P12-208` is a verified conditional deferral at `I1`; client PR 29 locally proves 8-10s active, 15-30s quiet, immediate-resume and bounded failure behavior, but is unmerged because its required hosted job is billing-blocked. Candidate.3 remains unchanged | `WO-010G2`, canonical client product contract, frontend source plan, client PR 29, LDPlayer-only owner instruction |
| `WO-011` | Prepare and, only after separate authorization, run the legally qualified capacity-bounded pilot | Platform/client | Local package complete; external execution `NOT_AUTHORIZED` | `WO-008`, `WO-009`, `WO-010` |
| `WO-011H` | Align the homepage story contract with the governed trust-led surface | Marketing tests/docs | Regression closed locally; no ledger advancement | `WO-011F` |
| `WO-012` | Evaluate transport diversity without a second client stack | Core/client/platform lab contract | Local package complete; manual/external gates retained | `WO-004`, `WO-006` |
| `WO-013` | Prove and promote the exact RC | Cross-repo/release | Signed candidate.3 exists; Gate F is exact-evidence `NO_GO`; Gate G/public/stable promotion remains unauthorized | All release-bound WOs |
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
| `WO-013AD` | Correct the SPB dual-role/type-3 diagnosis, disable only the stale advertised identity and retain client/device recovery evidence | Platform/client runtime and release evidence | Direct SPB is untouched; stale `ru_spb` type 3 is disabled with rollback snapshot; client PR 23 resets removed saved variants and passes PR/post-merge CI; candidate.2 direct/type 1 plus non-candidate type 2/recovery smoke pass on Beeline; no row advances and a new candidate remains required | `WO-013E`, `WO-013AC`, deployed self-hop guard, client PR 23, owned Brain/SPB/device access |
| `WO-013AE` | Replace candidate.2 as current truth with signed/private-carrier candidate.3 and reconcile exact Windows plus LDPlayer preflight evidence | Cross-repository candidate/release evidence | Candidate.3 binds current platform/client/Core/release-index source; signature, private carrier, hosted source gates and Windows clean-host pass; exact LDPlayer upgrade/launch/settings persistence passes while catalog/TUN/DNS/egress is access-blocked; physical device, live Windows network, origins, public assets and stable promotion remain open; no row advances | `WO-013AD`, platform PR 44, client PRs 25/26, release-index PRs 7/8, exact signed candidate.3 bytes |
| `WO-013AF` | Run one exact candidate.3 portal and client-channel rollback rehearsal without touching production or tracked stable state | Platform release operation/evidence | Signed manifest, exact generated handoff, real client pointer and real portal projection pass isolated 1.1.6→1.2.0→1.1.6 rollback; `REL_DOD/DOD-18` reaches `I3`; authorized runtime/origin proof remains open | `WO-013D`, `WO-013AE`, exact platform/client/Core/release-index checkouts |
| `WO-013AG` | Prove whether live Brain backend source is stale without deploying or restarting production | Platform operations/release evidence | Exact candidate.3 platform payload matches 193/193 after CRLF-only normalization; Brain readiness 23/23 and live enabled delivery 7/7 pass; 013AH later supplies the separate current-origin local aggregate, while RU-origin and authenticated client egress remain open; no row advances | `WO-013AE`, `WO-013Z`, owned trusted Brain access |
| `WO-013AH` | Correct the reproducibility harness and retain an exact candidate.3 current-origin local aggregate without changing candidate bytes | Platform release/performance evidence | Fail-first old harness retained; corrected quick 12/12 and default 13/13 gates pass against exact platform/client/Core, health p95 42.5337 ms and catalog p95 43.3626 ms pass source-bound; GitHub jobs are billing-blocked and PR 48 stays unmerged; RU-origin and authenticated client egress remain open; no row advances | `WO-013AE`, `WO-013AG`, exact source checkouts, harness PR 48 |
| `WO-013AI` | Emit one cryptographically and digest-bound exact candidate.3 Gate F decision without authorizing promotion | Platform release decision/evidence | Fixed 19-check verifier, upstream digest binding and exact LDPlayer byte/launch pass locally; after Gates B–E replay, Gate F returns `NO_GO` with 5 PASS, 14 non-PASS, 1 FAIL and 0 validation errors; `DOD-20` and `PR-10` remain `I3`, while Gate F and candidate remain below I4 | `WO-013AE`–`WO-013AN`, `WO-010K`, exact signed candidate bytes, platform PR 49 and client PR 29 readback |
| `WO-013AJ` | Baseline source-plan Gate A against exact candidate.3 without turning manual or skipped slices into PASS | Platform release decision/evidence | Exact source tuple, payment/release suite `103 + 21 subtests`, cross-repo contract, STOP-SHIP regressions `7/7` and solo PR controls `3/3` pass; Gate A remains `BLOCKED` by Windows live network/recovery and unsigned public/stable Windows signing, so `GATE-A` reaches only `I1` | source-plan Gate A, `WO-013M`–`WO-013P`, `WO-013AA`, `WO-013AE`, exact source worktrees |
| `WO-013AK` | Evaluate source-plan Gate B against exact candidate.3 and retain the replacement fix without transferring lab evidence | Platform/client/Core release decision/evidence | Exact state, ABI and false-green matrices pass; one Windows CRLF support-reference freshness test fails in frozen source, so Gate B stays `I3` as `NO_GO`; the post-candidate normalization fix passes `70/70`; physical lab4031 DNS/AWG readiness is retained separately and live AWG remains unconfigured | source-plan Gate B, `WO-004`, `WO-006I`, `WO-013AE`, exact source worktrees, returned owner phone, read-only Brain access |
| `WO-013AL` | Evaluate source-plan Gate C against exact candidate.3 without transferring post-candidate Linux or phone-lab evidence | Platform/client/Core release decision/evidence | Exact Windows service/IPC clean-host and Android exact-byte LDPlayer launch plus Core ABI pass bounded slices; Windows live network/recovery, authenticated physical Android/OEM/store matrices remain open, so Gate C stays `I2` as `BLOCKED`; Linux remains outside candidate.3 | source-plan Gate C, `WO-005`, `WO-005G`, `WO-013AE`, `WO-013AK`, exact source and artifact evidence, LDPlayer |
| `WO-013AM` | Evaluate source-plan Gate D against exact candidate.3 without running a real provider payment | Platform release decision/evidence | Frozen candidate payment/HTTP/DB/outbox/module matrix passes `196 + 12 subtests` and Action Intent/router ownership passes `25/25`; deployed source identity passes, but provider/PostgreSQL/outbox/reconciliation/rollback runtime proof is absent, so Gate D stays `I3` as `BLOCKED` with no replacement-code defect | source-plan Gate D, `WO-007`, `WO-007G`–`WO-007I`, `WO-013AG`, exact platform source, retained Brain source identity |
| `WO-013AN` | Evaluate source-plan Gate E against exact candidate.3 without converting automated UI checks into physical-device proof | Platform/client release decision/evidence | Exact quick/default aggregate, Playwright `88/88`, controlled API p95 and fresh desktop/mobile render smoke pass local slices; authenticated journeys, physical screen readers/scaling, device/browser performance, comparable artifacts, support recovery, RU-origin and post-promotion evidence remain open, so Gate E stays `I3` as `BLOCKED` with no replacement-code defect | source-plan Gate E, `WO-010`, `WO-013AH`, `WO-013AL`, exact platform/client/Core sources and private render screenshots |
| `WO-013AO` | Reconcile the current replacement source tuple, same-byte Android Core provenance, owned AWG/DNS physical slice and exact local aggregate without creating a candidate | Cross-repository pre-candidate/release evidence | Platform/client/Core base tuple `e5ef03a...` / `c196dff...` / `f44dbe8...` is clean and pushed; exact Node 22.14 local gate passes `15/15`; owned default-off lab closure advances `FRKN_PLAN/W3-01` to `I3`; later client `5e78dd9...` adds locally verified external Smart DNS routing and a production-signed build-4046 physical state-machine PASS without resolver/access proof; platform PR 58 and client PR 33 remain zero-step billing-blocked, while Core PR 6 passes four product jobs and awaits the client-main binding | `WO-013AK`, `WO-013AN`, owned physical pre-candidate evidence, current PR heads |
| `WO-013AP` | Add closed Linux NetworkManager/resolved/nft checkpoint/apply/rollback events without enabling or claiming live Linux traffic | Client conditional-Linux source and platform execution evidence | Client PR 28 head `583e04a...` adds typed transaction events plus honest unavailable preflight wiring; portable Go, Linux cross-vet/build/test compile, Flutter `4/4`, docs and branch-basis seed checks pass; `OBS-045` advances only to `I2` because Linux execution, real network transactions, journald readback and clean-host restoration are absent | `WO-005G`, Linux PR 28, `OBS-043`–`OBS-046`, branch-basis platform/Core authority |
| `WO-013AQ` | Add an authenticated same-build release-health comparison without exposing operator aggregates or exact cohort values | Platform/client pre-candidate source and observability evidence | Platform `3e52b73...` adds a weekly k-anonymous, contribution-capped, band-only projection; client `44c9cca...` adds a strict existing-session-only consumer on explicit diagnostics refresh plus the build-4046 `PSD2` support-code correction; platform/client/Core tests and final seed parity pass; `OBS-087` advances only to `I2` because no deploy, runtime cohort, exact candidate or physical comparison exists | `WO-010G3`, observability contracts and inventory, exact platform/client/Core source |
| `WO-013AR` | Add a managed default-off Hysteria2 owner lab through the existing Core engine without a production claim | Cross-repository transport source/artifact and preflight evidence | Core/platform/client exact contract, encrypted device-bound material, L3 guard, reproducible Android AAR, production-signed build-4046 default-off phone proof, byte-identical immutable Linux server bundle and a no-mutation owned-node PLAN pass; the guarded installer blocks APPLY because deployed Brain has no HY2 kill-switch readback and runtime material is absent; `FRKN_HY2/HY2-01` remains `I3`; server deploy, managed handshake/traffic, performance, origins and candidate remain open | `WO-012G` owner amendment, `WO-013AO`, exact Core/platform/client source and returned physical phone |
| `WO-013AS` | Add a default-off owned selective Smart DNS and opaque TLS relay lab without a second VPN core or access claim | Platform/client network-lab source and pre-candidate evidence | Exact pushed platform/client source, canonical policy, bounded Go DoH/SNI server, byte-reproducible immutable bundle, guarded remote installer source/tests, `412/412` client regression, production-signed build-4046 APKs and exact-byte LDPlayer/Huawei default-off/state-machine proof advance `SMARTDNS-01` to `I3`; dedicated-node PLAN/deploy, live DNS/SNI/access/leak/lifecycle/rollback/origin evidence and candidate remain open | `WO-013AO`, `WO-013AR`, platform `2d18fd7`, client `75e82b0`, retained local artifacts, returned physical phone and LDPlayer |
| `WO-013AT` | Retain the owner-free GitHub policy and exact current PR-head local gate without creating a candidate or changing visibility | Cross-repository release policy and pre-candidate evidence | The owner declines paid GitHub and waives private branch protection only under `OWNER_SOLO_EXCEPTION`; exact platform/client/Core product sources pass the local aggregate `15/15`; private platform/client hosted checks remain zero-step `BLOCKED_BY_ACCESS`, Core passes four product jobs and awaits the client-main binding; no visibility, merge, deploy, candidate or ledger change occurs | `WO-013AO`, current PRs 58/33/6, exact local aggregate, future open-source safety audit |

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
- `evidence/013AD-spb-dual-role-runtime-correction/013AD-spb-dual-role-runtime-correction.json`
  binds the sanitized same-host/separate-identity diagnosis, exact bounded
  rollout disable, physical Beeline route results, client PR 23 recovery and
  explicit no-new-candidate/no-ledger-advance boundary.
- `evidence/013AE-candidate3-reconciliation/013AE-candidate3-reconciliation.json`
  replaces candidate.2 as current truth with the signed candidate.3 source,
  artifact and supply-chain tuple; exact hosted gates, private carrier,
  Windows clean-host, LDPlayer preflight and PB-14 boundaries; and explicit
  access-blocked/manual/public-promotion ceilings without advancing a row.
- `evidence/013AE-candidate3-reconciliation/013AE-candidate3-signed-manifest.json`
  retains the exact signer run, downloaded outputs, independent public-key
  validation and private carrier digest readback.
- `evidence/013AE-candidate3-reconciliation/013AE-pb14-candidate3-health-stop.json`
  replays the real local health-stop/action-intent control from candidate.3
  bytes without a deployed cohort or external artifact switch.
- `evidence/013AF-exact-candidate-rollback-rehearsal/013AF-candidate3-release-handoff.json`
  is the exact generated strict-v2 candidate.3 runtime handoff bound to the
  signed source/artifact tuple.
- `evidence/013AF-exact-candidate-rollback-rehearsal/013AF-candidate3-rollback-rehearsal.json`
  retains the embedded pointer receipts, exact stable readback, portal
  byte-identical restoration, signature binding and no-production-mutation
  ceiling.
- `evidence/013AG-exact-candidate-brain-origin/013AG-exact-candidate-brain-origin.json`
  binds exact candidate.3 platform source to all 193 live Brain deploy files,
  fresh readiness 23/23 and enabled delivery 7/7 while preserving the
  no-deploy, no-client-egress and separate current/RU-origin ceilings.
- `evidence/013AH-exact-candidate-current-origin/013AH-exact-candidate-current-origin.json`
  binds the immutable candidate platform/client/Core tuple to corrected quick
  and default local release gates plus source-bound health/catalog latency,
  while retaining fail-first harness and GitHub billing-block evidence.
- `evidence/013AI-exact-candidate-gate-f/` retains the exact installed
  LDPlayer APK byte match, one 19-check candidate-bound evidence bundle, the
  digest-bound Gate F input and the final `NO_GO` decision.
- `evidence/013AJ-exact-candidate-gate-a/` retains the exact-source STOP-SHIP
  replay, owner-solo PR input and six-requirement Gate A `BLOCKED` decision.
- `evidence/013AK-exact-candidate-gate-b/` retains the exact-source Gate B
  replay, one deterministic candidate failure, the post-candidate correction,
  physical lab4031 DNS/AWG boundary and final Gate B `NO_GO` decision.
- `evidence/013AN-exact-candidate-gate-e/` retains the exact local
  UI/accessibility/responsive/static/API performance ceiling, private
  desktop/mobile screenshot digests and Gate E `BLOCKED` decision without
  converting missing physical/device/browser evidence into a pass.
- `evidence/010K-support-transport-reconciliation/010K-support-transport-reconciliation.json`
  binds the conditional no-streaming decision, unmerged adaptive-polling client
  source, complete local gate, zero-step GitHub billing blocker, LDPlayer
  render-only boundary and unchanged candidate.3 identity.
- `evidence/013E-android-mobile-runtime-matrix/013E-android-mobile-runtime-matrix.json`
  binds the newer Android artifact identity, single physical Beeline matrix,
  LDPlayer evidence ceiling, deployed server-chain reconciliation and explicit
  no-candidate/no-ledger-advancement decision for the observed runtime tuple.
- `WO-013AO-replacement-pre-candidate-reconciliation.md` binds the current
  clean replacement tuple, same-byte Android Core provenance, private local
  aggregate report digest, owned AWG/DNS physical boundary and zero-step
  GitHub billing blocker without treating the tuple as a candidate.
- `WO-013AQ-client-release-health-baseline.md` binds the platform/client source
  implementation of an exact-build weekly privacy-bounded comparison, the
  strict band-only client consumer and the `OBS-087` `I1 -> I2` ceiling without
  claiming a deploy, runtime cohort, physical comparison or candidate.
- `WO-013AR-hysteria2-owned-lab.md` binds the exact managed HY2 source tuple,
  reproducible Android Core AAR, byte-identical immutable Linux server bundle,
  production-signed build-4046 artifacts and physical install/launch/default-off
  proof while keeping server deploy/material, handshake, traffic, origins and
  candidate explicit.
- `WO-013AS-owned-smart-dns-lab.md` binds the selective non-recursive DNS and
  opaque allowlisted-SNI architecture, platform/client policy parity, bounded
  server source and current `I2` evidence ceiling. It does not claim an
  immutable bundle, APK/device proof, dedicated node, deploy or service access.
- `WO-013AT-owner-free-github-exact-pr-head-gate.md` retains the owner's
  no-purchase/solo-protection policy and the exact `15/15` current product-source
  local aggregate while keeping private hosted checks, publication, candidate
  and promotion explicitly open.

## Collision and promotion gates

- Before each WO: inspect branch/status/diff in every repository in its write scope.
- Never overwrite dirty or concurrent work; use a scoped branch/worktree and stage only authorized files.
- No deployment, production mutation, payment action, campaign launch, external message, branch-protection change or artifact promotion is authorized by this index alone.
- Exact runtime/manual gates use the repository labels: `PASS`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS`, `NOT_REQUESTED`.
- Stable promotion is prohibited while a STOP-SHIP row is below `I4` or any required exact-candidate gate lacks retained evidence.

## Next action

013AE is the current signed candidate identity authority; 013AF is the current
verified-local rollback authority; 013AG is the current exact-candidate
Brain-source/control-plane authority; 013AH is the exact-candidate
current-origin local gate/performance authority; 013AJ/013AK are the exact
Gate A/Gate B authorities and 013AI is the rehashed current exact Gate F
`NO_GO` authority; 013AD remains the current SPB
runtime-correction authority and 013AC is retained as superseded
candidate.2 history. Signed `pokrov-1.2.0-candidate.3` binds platform/client/
Core/release-index `eafaca3...` / `ac22825...` / `344b317...` / `6a1afa95...`,
five production-signed Android artifacts and owner-approved unsigned Windows
installer `9962e3e8...`. Manifest/signature/receipt `a2752b6a...` /
`926f0b46...` / `fb4d0d5d...` validate independently. The private client
prerelease retains the installer and three signed outputs with matching
GitHub digests; it is not public or stable.

Exact candidate.3 Windows run `33033294889` proves machine-wide install,
eight installed-file hashes, LocalSystem service identity, authenticated
UI/service IPC, SCM restart, clean uninstall and unchanged idle route/DNS. It
does not prove live TUN, connected DNS/leak behavior, authenticated egress,
crash/reboot, uninstall while connected or interactive SmartScreen.

Exact universal Android APK `f41c76eb...` passes LDPlayer upgrade install,
package/version readback, launch/relaunch, Support screen rendering and
persistence of AI-services and Games routing controls. The retained emulator
account is expired, so catalog,
TUN, DNS, owned egress and content reachability are `BLOCKED_BY_ACCESS`. The
owner returned the physical phone, which now runs post-candidate lab build
`1.2.0+4046`; its earlier Beeline/DNS/AWG observations and later HY2
install/launch/default-off proof are not transferred to candidate.3. Exact candidate.3 physical
Beeline/OEM/handover remains unrun.

Candidate.3 PB-14 local replay passes: an identity-free `UPD-004` blocks
observation close and drives the guarded rollback request/public policy to
zero. This is isolated control evidence at `I3`, not a deployed cohort or an
external artifact switch.

Candidate.3 portal/client rollback rehearsal also passes at `I3`: the signed
manifest is bound to generated handoff `565a43dd...`; the real client pointer
and portal consumer complete isolated `1.1.6 -> 1.2.0 -> 1.1.6` restoration
with embedded receipts and byte-identical final state. Tracked stable/runtime
state is unchanged, so authorized production rollback and origin readback
remain open.

Fresh Brain-origin evidence proves the live backend is not stale: all `193`
deploy payload files match candidate platform source `eafaca3...` after only
CRLF-to-LF normalization, Brain readiness passes `23/23`, and the seven live
enabled delivery rows are open from Brain. No deploy or restart is needed.
This Brain-origin result does not prove LDPlayer/authenticated egress or
RU-origin behavior. A separate corrected harness binds
the immutable candidate tuple and passes current-origin quick `12/12`, default
`13/13`, health p95 `42.5337 ms` and catalog p95 `43.3626 ms`. GitHub did not
start platform PR 49 or client polling PR 29 jobs because account billing
blocked Actions, so both PRs remain unmerged and the hosted checks are
`BLOCKED_BY_ACCESS`, not `PASS`.

Gate F now returns exactly `NO_GO`: 5 of 19 checks are PASS and 14 remain
non-PASS, with one explicit Gate B candidate failure and zero
signature/evidence binding errors. This is the required evidence-based
decision behavior, not release readiness. Gate G remains unauthorized even
after a future GO.

WO-013AO is the current replacement pre-candidate source authority. Its clean
platform/client/Core tuple `e5ef03a...` / `c196dff...` / `f44dbe8...` passes
the exact Node 22.14 local aggregate `15/15`, and Android Core provenance is
rebound without a binary delta. It does not replace signed candidate.3 as the
current exact-candidate authority and does not repair candidate.3's `NO_GO`.
Later exact pushed platform server `2d18fd7...`, guarded operations
`ca9eb41...` and client `75e82b0...` source add the build-4046 external Smart
DNS lab. The byte-reproducible server bundle, guarded installer tests, full
client regression, production-signed working APKs and LDPlayer/Huawei
default-off state checks pass, but there is no installed resolver or live
service-access proof and no candidate is created.

WO-013AR adds the exact default-off HY2 source tuple
`8d60736...` + operations `8a97b53...` and guarded remote installer
`4c65912...` / client `850d9e3...` / Core `e8eb772...`, two
byte-identical Android Core AAR builds, a byte-identical immutable Linux server
bundle and production-signed build-4046 install/launch/default-off proof.
It advances only `FRKN_HY2/HY2-01` to `I3`; the immutable server bundle now
exists locally and a no-mutation owned-node PLAN proves UDP `443` and target
paths conflict-free. The deployed Brain lacks HY2 kill-switch readback and the
node lacks runtime material, so APPLY remains blocked; there is no server
deploy, managed handshake, traffic, performance, origin or candidate proof.
The original source-plan ledger distribution is `I4=4`, `I3=315`, `I2=21`,
`I1=37` across 377 rows. The derived `FRKN_SMART_DNS/SMARTDNS-01` row is
separate and now sits at `I3`.

The owner declined paid GitHub. Private platform/client branch protection is
waived only under `OWNER_SOLO_EXCEPTION`; named hosted checks are not waived
and remain `BLOCKED_BY_ACCESS`. Do not change visibility in this slice. Audit
source and history for public-release hazards before a separately authorized
public conversion. Preserve the promotion order: client binding, Core PR 6
`release-contract` replay, then Core/platform. Only after the exact promoted
tuple is green may a replacement candidate be frozen and subjected to the
candidate-bound device, Windows network, origin, provider, Operator, legal and
performance matrices.

The owned AWG and HY2 labs are still default-off. Beeline reverse UDP is
`BLOCKED_BY_NETWORK_CURRENT_ORIGIN`; another origin can be tested without
touching active paid nodes, but it cannot substitute for the eventual exact
candidate matrix. HY2's node preflight is green, but live testing still
requires the exact HY2-aware control-plane deployed with its kill-switch
engaged, root-only runtime material, separately authorized exact-bundle install
and encrypted device material. Direct DoH is not VPN-free Smart DNS. Public `v1.2.0`, six
same-byte public assets and the stable pointer remain prohibited until Gate F
is `GO` and the owner separately authorizes Gate G. The build-4046 external
Smart DNS client path remains a default-off lab until a compatible resolver and
live access/leak/rollback evidence exist. Windows SmartScreen remains the
owner-approved unsigned direct-beta limitation.
