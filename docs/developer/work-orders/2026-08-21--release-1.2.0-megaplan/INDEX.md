# POKROV 1.2.0 Megaplan — Wave Index

Last updated: 2026-08-30
Classification: `ACTIVE_EXECUTION`
Wave status: `PHASE_11_CANDIDATE13_SIGNED_LDPLAYER_I4_GATE_F_NOT_RUN_PHYSICAL_WINDOWS_ORIGINS_MANUAL`
Release candidate: `POKROV_1_2_0_CANDIDATE13_SIGNED_PRIVATE_ACTIONS_ARTIFACT_ONLY_PROMOTION_NOT_AUTHORIZED`

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
| 01 | Release manifest, version/provenance contract, CI and stop-ship controls | Release-v2, client adoption, release-bound CI, reproducible dependencies, shared catalog and cross-repository truth are proved; the public-index source/trust root is on public main, PR-00 is merged, and `OWNER_SOLO_EXCEPTION` explicitly replaces the unavailable second reviewer without claiming independent review. WO-013CX adds exact candidate.13's validated six-artifact supply chain and genuinely passing public-index signer while private platform/client zero-step jobs remain non-PASS. This bounded supply slice reaches `I4`; the aggregate release controls remain below promotion readiness | `WO-002`, `WO-003`, `WO-003B`, `WO-003C`, `WO-003D`, `WO-003E`, `WO-003F`, `WO-003G`, `WO-003H`, `WO-003I`, `WO-003J`, `WO-013J`, `WO-013K`, `WO-013L`, `WO-013M`, `WO-013N`, `WO-013O`, `WO-013P`, `WO-013CX` |
| 02 | Typed connection state, proof-driven green state, core ABI and migrations | Aggregate Gate B remains `BLOCKED/I3`. Candidate.10's exact source replay remains retained history. WO-013CX binds the successor lifecycle correction to signed candidate.13: the full exact client gate passes, and LDPlayer accepts AWG 3.1 -> AWG2 -> default/Auto across successive Core runs in one application process. Windows connected recovery and exact physical-device boundaries remain open; ABI v3 stays deferred until after 1.2.0 | `WO-004`, `WO-004A2`, `WO-004B2`, `WO-004D`, `WO-006I`, `WO-013CI`, `WO-013CO`, `WO-013CX` |
| 03 | Windows/Android runtime boundaries; conditional Linux beta foundation | Gate C stays `BLOCKED/I3`. Older physical evidence remains immutable history and is not transferred. Exact candidate.13 x86_64 bytes pass the bounded LDPlayer AWG 3.1/AWG2/default lifecycle, but the physical phone was not touched. Connected clean-VM Windows, exact candidate.13 ARM64 physical Android, external leak/UDP53/MTU/OEM/endurance/accessibility and Store delivery remain open. Linux is deliberately not shipped | `WO-005`, `WO-005C4`, `WO-005D4`, `WO-005G`, `WO-013CC`–`WO-013CO`, `WO-013CX` |
| 04 | Observability, error catalog, redacted bundle and support pipeline | Locally complete (`I3`) for shipped Android/Windows scope, including four-class safe transport failures, active operational producers, Android count-only routing, no-upload short code, signed temporary support mode, encrypted-only manual export and a current 7/7 MSVC native proof for the bounded Windows service journal; 013S proves the active public pin and hosted source-control custody, while deployed runtime/RBAC/audit and exact-candidate device evidence remain open; Linux remains explicitly not shipped | `WO-006`, `WO-006I`, `WO-006J`, `WO-006K`, `WO-006L`, `WO-013S` |
| 05 | Portal bounded contexts, payments, HTTP/DB/outbox reliability | Locally complete (`GATE-D` and `ARCH-002` at `I3`); 007G–007I split admin, public/client and Action Intent domain/runtime owners. WO-013CO replays exact candidate.10 source at `196/196 + 12` and `25/25`, plus Brain `197/197`, `23/23`, `7/7`; Gate D remains `BLOCKED` below I4 until production provider/PostgreSQL/outbox/reconciliation/operator/rollback proof exists | `WO-007`, `WO-007G`, `WO-007H`, `WO-007I`, `WO-013CI`, `WO-013CO` |
| 06 | Product facts, subscriptions, checkout, offers and attribution | Local source packages: 008A–008G commercial package at `I2`; 008H–008M close active-client generation, copy/public truth, whole-client product facts, subscription state presentation, no-waterfall loading and the complete local subscription/checkout aggregate at `I3`; deployed provider, broad commercial-consistency and exact-candidate gates stay open | `WO-008`, `WO-008H`, `WO-008I`, `WO-008J`, `WO-008K`, `WO-008L`, `WO-008M` |
| 07 | Canonical Operator Center v2 and legacy admin cutover | Local package complete, including the deterministic 75-operation OpenAPI/TypeScript contract, purpose-bound Telegram OIDC Authorization Code plus PKCE login and same-identity step-up for preprovisioned operators, exact retained-bridge permissions and query-suppressed field redaction; live IdP, authenticated exact-candidate readback and cutover/rollback gates remain open | `WO-009`, `WO-009H`, `WO-009I`, `WO-009J` |
| 08 | App, cabinet and marketing UX/accessibility/performance reconciliation | Locally complete at `I3`; WO-013CO binds exact candidate.10 quality `15/15`, static performance `9/9` and direct current-origin health/catalog p95 `36.8219/46.127 ms` PASS. The fail-first missing-dependency run and Node `24.15.0` versus requested `22.14.x` mismatch remain visible. Gate E stays `BLOCKED` below I4 on authenticated journeys, physical accessibility/OEM/scaling, comparable artifact/device and browser-lab performance, support, RU-origin and post-promotion evidence | `WO-010`, `WO-013AN`, `WO-013CI`, `WO-013CO` |
| 09 | Legal-gated, capacity-aware marketing pilot and evidence-based decision | Locally complete (`I3` package); external pilot `NOT_AUTHORIZED` | `WO-011` |
| 10 | FRKN-derived rules and isolated AWG2/AWG3.1/HY2/Smart-DNS owner labs | AWG2/AWG3.1 and bounded base HY2 source labs are locally proved and default-off. Candidate.5's exact physical AWG failures remain immutable history. WO-013AY/013AZ add bounded diagnostics and the Core bind correction; WO-013BA proves direct pinned-peer local interoperability. WO-013BB fixes the owned-node reply route without changing cryptography, WO-013BC binds byte-reproducible Android/Windows artifacts, and WO-013BD separates working transport from the common Android endpoint DNS failure. WO-013BE corrects the AWG endpoint's default-resolver boundary in Core `a45d69e...`; exact production-signed build 4046 passes AWG2 and AWG3.1 selected-endpoint green state on LDPlayer and physical Beeline. WO-013BF packages the same exact Windows DLL into setup `81268d7e...` with an `8/8` manifest readback. WO-013BG records an LDPlayer WARP/control pair blocked by the shared emulator egress boundary and a partial physical host-lifecycle pass without promoting WARP proof. WO-013BH proves a portable immutable Smart-DNS bundle and all-seven active-node no-mutation PLAN matrix. WO-013BI rejects an intermediate false spare-address lead and proves with strict report-v3 parsing that `de` has exact binds on both globally routable addresses while the other six nodes use wildcard/dual-stack binds; no safe zero-purchase deploy target exists without a separate guarded migration. WO-013BJ binds the canonical ChatGPT/OpenAI, Gemini and Xbox policy to server exact/child DoH behavior and the client routing copy as source-only proof. WO-013BK binds those source changes and the corrected AWG Core into signed candidate.6. WO-013BV adds the post-candidate zero-purchase shared-443 source path: strict loopback PROXY v2 plus validated HAProxy exact/child-SNI rendering, while leaving the current installer dedicated-only and every live frontend unchanged. WO-013BW closes the separate frontend-operation source gap with exact receipt/CAS-bound PLAN/APPLY/ROLLBACK and a corrected all-seven no-mutation PLAN; RU and RU-SPB render valid candidates but both lack the required fronted Smart-DNS backend, so neither is selected. WO-013BX closes the matching guarded fronted-server installer source gap and proves no-mutation install PLAN readiness on RU and RU-SPB; runtime material remains absent and no node is selected. WO-013CE proves the exact fronted bundle's DoH and application TLS passthrough in an isolated `x86_64` owner-terminal fixture, then rejects RU direct egress for DNS-only geo/access bypass and selects no production target. WO-013CG adds the missing receipt/CAS first-frontend bootstrap and proves an exact no-mutation PLAN on the foreign `it` canary while leaving live transport unchanged. WO-013CK corrects two fail-closed operation defects, then proves guarded `it` frontend APPLY, current/Brain reachability, receipt-bound rollback and re-APPLY; Smart DNS itself remains uninstalled without runtime material, DNS name or certificate. WO-013BL's post-signing LDPlayer AWG2/AWG3.1/default comparison reaches the same egress boundary for all three and is classified as an emulator-origin block, not a protocol PASS or FAIL. WO-013BP adds exact-candidate selected/excluded-app config, force-stop cleanup and WARP endpoint/TUN materialization on LDPlayer, with the same origin block and clean restore. WO-013BQ proves the IPv4-only Android TUN structurally blocks unconfigured IPv6 on the exact candidate.6 LDPlayer path without claiming an external leak PASS. Phase 10 remains `I3`, not `I4`, because Windows live parity plus required origins and service-access matrices are open. HY2 remains undeployed. Smart-DNS runtime material/deploy, live service access, attribution, leak/runtime-rollback/origin proof remain open. Gecko, Mimic and port hopping remain monitor-only | `WO-012`, `WO-013AO`, `WO-013AR`, `WO-013AS`, `WO-013AU`, `WO-013AX`, `WO-013AY`, `WO-013AZ`, `WO-013BA`, `WO-013BB`, `WO-013BC`, `WO-013BD`, `WO-013BE`, `WO-013BF`, `WO-013BG`, `WO-013BH`, `WO-013BI`, `WO-013BJ`, `WO-013BK`, `WO-013BL`, `WO-013BP`, `WO-013BQ`, `WO-013BV`, `WO-013BW`, `WO-013BX`, `WO-013CE`, `WO-013CG`, `WO-013CK` |
| 11 | Exact-candidate RC matrix, immutable promotion, rollback and go/no-go | Candidates 5–12 remain immutable history. WO-013CX binds exact platform `7d983c0...`, client `ce2581d...` and Core `cd8f0f4...` to signed private candidate.13: supply-chain validation passes, the hosted public-index signer passes, and exact LDPlayer x86_64 AWG 3.1 -> AWG2 -> default/Auto passes in one application process with clean lab/VPN teardown. This advances only the bounded candidate supply/runtime slice to `I4`. Gate F is not generated because its required exact ARM64 physical-install binding is absent; the phone was not touched. Clean Windows, current/Brain/RU origins, provider/Operator/legal, rollback and broader performance remain non-PASS. Hosted private platform/client zero-step checks remain non-PASS under the no-purchase solo policy. No tag, public `v1.2.0`, Store object, stable switch or promotion occurred | `WO-013`, `WO-013BK`–`WO-013CX` |

Active Phase 10/11 supersession: WO-013CX is the current signed-candidate
authority. Candidate.11 was rejected because ordinary Smart Connect quarantine
could block an explicitly selected lab profile; candidate.12 corrected that
path but was rejected after the warm AWG 3.1 -> AWG2 lifecycle exposed a
cross-run Android event-fence defect. Candidate.13 contains both corrections.
Its exact x86_64 APK passes control-plane selection, runtime-profile identity,
tunnel, managed DNS and authenticated egress for AWG 3.1, warm AWG2 and warm
ordinary Auto without a process restart, then restores default/no-lab/no-VPN
state. The physical phone remains `MANUAL_OWNER_TEST` and untouched.

Candidate.13's release-index signer output is
`ACTIONS_ARTIFACT_ONLY`, `promotion_authorized=false`. The source seed remains
`PRE_CANDIDATE_LOCAL`; the strict-v2 handoff and signed receipt are the
candidate authority. Gate F is
`NOT_RUN_MISSING_EXACT_ARM64_INSTALL_BINDING`, not an inherited candidate.10
result. Gate G is `NOT_AUTHORIZED`. XHTTP and HY2 remain post-1.2.0 bounded
lanes; neither is required to promote the base protocol line.

Active Phase 10/11 supersession: WO-013CP supersedes the older Phase 10 wording
about an undecided DNS name. `dns.pokrov.space` is now the authorized hostname,
but its A record is
still absent on all four delegated authoritative servers. Runtime material,
certificate and Smart DNS service remain absent.

WO-013CQ adds an exact candidate.10 LDPlayer client replay without changing
that server boundary. The installed APK matches the signed candidate bytes;
custom DoH, direct DoH, external Smart DNS and the AI/Gaming purposes persist
across force-stop/relaunch and restore cleanly. No DoH request or service access
ran while authoritative DNS remained `0/4`, so `SMARTDNS-01` stays `I3`.

WO-013CR removes obsolete pull-request state without changing candidate.10.
Thirteen already-promoted, old-tuple or explicitly superseded PRs are closed
with their branches and commits preserved. HAPP iOS, the current Linux beta
foundation and the source-only AWG lifecycle test remain open with explicit
boundaries. A fresh direct check still returns `NXDOMAIN` on all four delegated
servers, so Smart DNS APPLY remains `NOT_RUN`.

WO-013CS resolves that retained Linux beta branch against current client
`main`, proves the exact merge-result source with the full client gate and a
real owned Linux compile host, then merges PR 28 under the solo exception.
Linux remains source-only and outside candidate.10: live connect, network
mutation/rollback, signed packaging and the exact Ubuntu 24.04 VM matrix stay
open. Authoritative Smart DNS is still `0/4 NXDOMAIN`.

WO-013CT adds a separate source-exact AWG RU-origin slice without the physical
phone. One digest-verified ARM64 binary from candidate.10 Core runs AWG2 and
randomized-trailer AWG3.1 on an owned Raspberry Pi 4 direct fixed-network path;
both reach verified authenticated egress and clean all temporary state. This
advances only `AWG-10` to partial `I2`. It does not replace candidate.10
Android/Windows, multi-ASN or the still-failing general RU manifest.

WO-013CU retains a completed exact-platform security scan. Nine critical
source surfaces return zero validated findings, but coverage is explicitly
partial and source-only, with no independent baseline or runtime posture
validation. The broad Gate F no-open-P0 attestation therefore remains
`MISSING`; Gate F is not regenerated. A concurrent authoritative DNS recheck
still returns `NXDOMAIN 4/4`, so ACME and Smart DNS APPLY remain `NOT_RUN`.

WO-013CV retains the matching exact-client source scan. Eight Android/Windows
trust surfaces return zero validated findings and no validated P0/P1, including
proof-driven connection presentation, direct/store update authority, Windows
privileged IPC/runtime and encrypted support export. Coverage remains partial:
no binary/runtime/device, dependency-database, Git-history or independent
baseline proof occurred. Gate F therefore remains unchanged. A fresh
authoritative DNS recheck still returns `NXDOMAIN 4/4`.

The candidate.7 history below remains retained context: WO-013BY creates signed
private candidate.7
from platform `af259f3...` with the same exact client/Core build `4046` bytes,
corrected SBOM/provenance and a passing fail-closed supply-chain validator.
WO-013BZ then binds fresh current- and Brain-origin PASS, exact candidate.7
LDPlayer AWG2/AWG3.1 formation with a common emulator-origin block and clean
restore, plus a direct terminal-only Pi RU baseline. The first candidate.7
Gate F is `BLOCKED` at `4 PASS / 15 non-PASS / 0 FAIL`; Pi baseline is not
promoted into exact-candidate RU-origin PASS. WO-013CA then runs the exact
ARM64 package on physical Beeline: the ordinary profile passes, while AWG2 and
AWG3.1 form validated VPN/TUN/DNS state but fail selected-exit proof. The
physical differential rejects candidate.7 for replacement without rewriting
the earlier Gate F snapshot. WO-013CB then corrects the live reply-policy,
mobile MTU and AWG3.1 content-padding boundaries without changing official
cryptography. Both exact candidate.7 Android profiles reach green tunnel, DNS
and authenticated egress on physical Beeline and restore cleanly. The changed
platform provisioning and Android notification source still require
candidate.8 and a new Gate F. Candidate.6 remains immutable history. No phase
or ledger item advances to `I4`.

WO-013CC now binds the required successor candidate.8 from exact platform
`241a83b...`, client `3459438...` and Core `a45d69e...`. All `15/15` local
source steps, the six-artifact/8-file supply-chain verifier and public
release-index signature pass. The exact ARM64 package physically proves the
notification false-green correction plus AWG2 and mobile-safe AWG3.1 tunnel,
DNS and authenticated egress over Beeline, then restores default/no-lab/no-VPN
state. Fresh current-origin health/catalog budgets pass. Candidate.8 Gate F is
`BLOCKED` at `4 PASS / 15 non-PASS / 0 FAIL` with zero validation errors:
exact Brain/RU, isolated Windows, remaining Android active-WARP/external-IPv6/
UDP53/MTU/excluded-app/multi-OEM/endurance, live Smart DNS and external manual
rows remain open.
Candidate.7 remains immutable rejected history. No phase or ledger item
advances to `I4`, and no public or stable promotion occurred.

WO-013CD continues the same immutable candidate.8 ARM64 package on the unlocked
physical device. The defined WARP fallback/revoke path, selected-app TUN traffic
plus excluded-control bypass, mobile/Wi-Fi handoff, screen-off, tile and
notification lifecycle, forced deep Doze, forced app standby and strict Private
DNS interaction pass with a clean final restore. Active WARP carriage is not
proven, and IPv6 is `BLOCKED_NO_UNDERLYING_IPV6` because both VPN-on and
VPN-off controls lack it. The incomplete Android row stays
`MANUAL_OWNER_TEST`; Gate F remains `4/15/0` and no completion-index level or
promotion state changes.

WO-013CE resolves the Smart DNS egress ambiguity without touching candidate.8
or production. The exact fronted bundle passes an isolated `x86_64` terminal
fixture for strict PROXY v2, DoH synthesis and verified AI/gaming TLS
passthrough, with complete process/listener/temp cleanup. Source inspection
proves that application TCP/443 leaves directly from the service host. An RU
frontend/backend would therefore retain RU egress and is `NO_GO` for DNS-only
geo/access bypass. No target is selected; the preferred next topology is a
colocated foreign owned frontend and loopback backend. `SMARTDNS-01` stays
`I3`, Gate F stays `4/15/0`, and no public or stable state changes.

WO-013CF binds fresh read-only exact Brain proof and bounded owner-host checks
to the same immutable candidate.8. Brain source/readiness/enabled delivery
passes `197/197`, `23/23` and `7/7`. Four direct RU-terminal samples prove
all owned public surfaces and stable RU-SPB reachability, but the canonical
probe contour remains absent and NL is intermittent. The exact Windows setup
passes clean application-state install, `8/8` files, LocalSystem service,
authenticated IPC, restart, uninstall and idle network restoration; connected
TUN/DNS/egress/recovery and clean-VM proof remain open. Gate F advances only
Brain and returns `BLOCKED` at `5/14/0`; no `I4`, public or stable advance is
claimed.

WO-013CG closes WO-013CE's missing foreign first-frontend source/PLAN boundary.
Platform `c2ffc48...` adds a one-backend HAProxy default route plus guarded
PLAN/APPLY/ROLLBACK with root-only receipts, x-ui SQLite CAS, inbound-invariant
binding and explicit automatic-rollback outcomes. A sanitized read-only `it`
PLAN proves one exact Xray-owned VLESS/Reality public-443 inbound, free loopback
10443/18443 and an available but absent HAProxy package. It returns
`bootstrap_applicable=true`, `mutation_performed=false`. `it` is a PLAN canary,
not a deployed target; `SMARTDNS-01` stays `I3`, candidate.8/Gate F stay
unchanged and live APPLY/material/access/origin proof remain open.

WO-013CH binds the exact candidate.8 x86_64 APK to a new LDPlayer rehearsal.
Installed bytes match `ec07ba17...2627`; all seven locations render. Ordinary
Frankfurt fails closed without false green, while guarded AWG2 and AWG3.1 each
confirm tunnel, DNS and selected egress. Default restore removes both lab
materials and membership and leaves no TUN. Only
`android_ldplayer_rehearsal` advances to PASS; Gate F remains `BLOCKED` at
`6/13/0`. Client PR `37` reconciles active readiness owners, and LF attributes
make the successor evidence digest-stable on Windows checkouts. No `I4`, public
or stable advance is claimed.

WO-013CI replaces the stale candidate.3 Gate A–E decision layer with a replay
bound to the signed candidate.8 tuple. Exact Core hosted CI passes `5/5`; Gate
B source matrices pass `70/70` and `111/111`; Gate D passes `196/196 + 12` and
`25/25`; Gate E retains `15/15`, `9/9` and current-origin p95 PASS. All five
gates remain `BLOCKED` because their live/manual boundaries are still open,
with zero explicit failures; Gate C advances `I2 -> I3`. Gate F revalidates all
`19/19` pointers and stays `BLOCKED` at `6/13/0`. No Gate G or promotion is
authorized.

WO-013CJ repeats the signed candidate.8 portal projection and client stable
pointer mechanisms inside an isolated fixture. The exact sequence
`1.1.6+20260819 -> pokrov-1.2.0 -> 1.1.6+20260819` passes initial validation,
dry-run, forward/reverse atomic switches and final readback; client and portal
restore byte-identically and preserve unrelated configuration. DOD-18 and
P12-130 retain `I3` with stronger exact-candidate evidence. Gate F remains
`6/13/0` because the separately authorized real runtime pointer/kill drill and
current/Brain post-rollback readback were not run.

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
| `WO-013` | Prove and promote the exact RC | Cross-repo/release | Signed candidate.8 is current; successor digest-bound Gate F is `BLOCKED` at `6/19 PASS`, `13/19 non-PASS`, `0 FAIL`. Gate G/public/stable promotion remains unauthorized | All release-bound WOs |
| `WO-013A2` | Replace circular phase/plan preflight logic with an exact fail-safe row-stage policy | Platform release preflight | Complete locally; no ledger advancement | `WO-001`, `WO-013A` |
| `WO-013A3` | Move PB-14 out of the circular local-freeze lane because its signed-manifest health-stop proof requires an exact candidate | Platform release preflight | Complete locally; no ledger advancement, PB-14 remains unproved | `WO-013A2`, `WO-006J` |
| `WO-013C` | Make Linux non-shipment and Android OEM background/permission/surface limitations explicit and machine-bound | Platform/client release limitations | Complete locally (`REL_DOD/DOD-17 I3`); exact-candidate release notes and physical OEM proof remain open | `WO-005`, `WO-006`, `WO-013` |
| `WO-013D` | Make the client stable pointer reversible through an exact rollback catalog, atomic switch contract and retained evidence | Client/platform release rollback | Complete locally (`FE/P12-130 I3`); WO-013CJ repeats exact candidate.8 portal/client rollback locally, while the authorized runtime drill remains open | `WO-003`, `WO-013C`, `WO-013CJ` |
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
| `WO-013AU` | Sign candidate.5, deploy the reviewed Brain AWG route and retain bounded exact physical Android runtime evidence | Cross-repository candidate/runtime evidence | Six immutable artifacts, strict-v2 handoff, SBOM/provenance and hosted manifest signature are retained; the one-file Brain route deploy passes `193/193` with only `portal-api` restarted; exact physical ordinary Frankfurt tunnel and bounded Smart-DNS DNS/ICMP pass with clean restore; AWG device binding is `BLOCKED_BY_ACCESS` before the remote helper/Core; Gate F, Windows/provider/origin/manual gates, public assets and stable promotion remain open | `WO-013AT`, promoted platform/client/Core tuple, release-index signer, authorized Brain deploy, returned physical phone |
| `WO-013AV` | Correct the candidate.5 release harness, converge Brain to the full exact payload, close current/Brain origins and regenerate Gate F | Platform release decision/runtime evidence | Candidate runtime/artifacts remain immutable; the corrected full release matrix exits zero; Brain fail-first `179/197` becomes postdeploy `197/197`, readiness `23/23` and enabled delivery `7/7`; postdeploy current-origin health/catalog p95 pass; Gate F is `BLOCKED` with `6 PASS`, `13 non-PASS`, `0 FAIL`; no Gate G or public/stable mutation | `WO-013AU`, exact source worktrees, signed candidate.5, authorized Brain deploy |
| `WO-013AW` | Retain the no-purchase/no-protection solo policy and audit public-repository safety before visibility changes | Cross-repository publication policy/evidence | Core and release index are already public; direct platform/client visibility flips are blocked by unreviewed reachable history, binaries/oversized blobs and missing publication licenses. Publish sanitized source-only successors after rights/license and clean-clone CI proof; no billing, protection, visibility or repository mutation occurred | `WO-013AT`, owner public-source direction, all-reachable-history redacting preflight |
| `WO-013AX` | Run exact candidate.5 owned AWG2/AWG 3.1 physical interoperability and retain replacement corrections | Cross-repository candidate/protocol/runtime evidence | Protected binds succeed and exact candidate.5 starts Android VPN for both profiles, but outer packet exchange never becomes an authenticated handshake, inner traffic stays zero and DNS/egress are unproved; both slices are `FAIL`. Candidate.5 is immutable and rejected for replacement. Platform binder `f4927c6` and client stale-location fix `bbf1de8` pass focused local verification; privacy-safe Core rejection diagnostics and a new signed candidate are required | `WO-013AU`, `WO-013AV`, exact signed candidate.5, returned physical phone, owned AWG endpoints |
| `WO-013AY` | Bridge bounded AWG diagnostics into the Android diagnostics screen and isolate the replacement failure on LDPlayer | Cross-repository replacement source/artifact/runtime evidence | Core `b057ff3...`, client `7a633a8...` and platform operator `b0affe4` pass full/focused gates. Production-signed diagnostic build 4046 shows `handshake_retry #4` for both AWG2 and AWG 3.1 with failed DNS-name and HTTPS egress, then clean default restore. This is emulator pre-candidate failure evidence, not root-cause correction or physical/candidate proof | `WO-013AX`, replacement Core/client source, owned LDPlayer, default-off AWG endpoints |
| `WO-013AZ` | Correct the AWG bind allocated-port/partial-cleanup contract and recheck both replacement profiles | Core/client/platform replacement runtime evidence | Core `6b8ddca...` passes focused/full gates and exact signed replacement APKs build, but AWG2/AWG3.1 both repeat `handshake_retry #4` plus failed DNS/HTTPS on LDPlayer. Bind fix retained; handshake remains failed; default cleanup passes; no candidate or row advance | `WO-013AY`, exact replacement source, owned LDPlayer, default-off AWG endpoints |
| `WO-013BA` | Prove the corrected POKROV AWG bind path against a direct peer from the exact pinned official engine | Core local source interoperability evidence | Core `3c2b114...` passes deterministic AWG2 and AWG 3.1 real-loopback-UDP authenticated handshake plus exact inner TCP echo against the direct pinned peer; focused/full gates pass; no production material, physical proof, candidate or row advance | `WO-013AZ`, Core `6b8ddca...`, pinned official `amneziawg-go/v3 v3.1.20260814` |
| `WO-013BB` | Correct the multi-address owned-node AWG reply route and repeat both profiles on physical Beeline | Platform server operator plus cross-repository pre-candidate runtime evidence | Platform `f79974c...` applies exact source-port policy routes plus bounded SNAT with backup/readback/service-cycle proof. Production-signed Android `1.2.0+4046` completes fresh AWG2/AWG 3.1 handshakes and bidirectional inner traffic on physical Beeline; post-cycle Core interop passes both; clean `default` restore passes. Phase 10 stays `I3`; no candidate or Gate F advance | `WO-013BA`, exact replacement client/Core, owned default-off AWG endpoint, returned physical phone |
| `WO-013BC` | Converge exact Android/Windows Core artifacts and retain the unsigned Windows pre-candidate assembly | Cross-repository artifact/reproducibility and local release evidence | Core `3c2b114...` produces byte-identical AAR/DLL rebuilds; client `75aabd9...` binds both and `55e7d5c...` records the owner-approved unsigned setup. Exact DLL proxy cycles pass `100/100` and the clean aggregate passes `15/15`, but Windows app/service/TUN/DNS/AWG and all candidate-bound gates remain open; no candidate or Gate F advance | `WO-013BB`, exact clean Core/client/platform tuple, owner unsigned-Windows exception |
| `WO-013BD` | Repeat both owned AWG profiles on physical Beeline with the exact security-fixed Core and separate transport truth from client egress truth | Cross-repository pre-candidate runtime and hosted-CI evidence | Production-signed client `064fcd0...` with Core `547f096...` installs/readbacks exactly. Core hosted CI passes five jobs; ordinary Frankfurt passes on the same phone. AWG2/AWG3.1 each pass fresh handshake and bidirectional TCP/UDP payload, but Android selected-endpoint proof remains `EGRESS-001`. IPv4-only DNS is deployed and correct for the routed prefix but does not fix the failure. Clean default restore passes; no candidate, row or Gate F advance | `WO-013BC`, exact active client/Core bytes, owned default-off endpoints, returned physical phone, controlled Brain deploy |
| `WO-013BE` | Correct the Core AWG endpoint default-resolver boundary and repeat AWG2/AWG3.1 selected-endpoint proof | Cross-repository source, artifact, LDPlayer, physical Beeline and local aggregate evidence | Core `a45d69e...` preserves hostname authentication, official crypto and fail-close while using the configured default resolver for the inner FQDN. Reproducible AAR/DLL bindings pass; production-signed client `68779c4...` installs/readbacks exactly and both profiles retain green state on LDPlayer and physical Beeline without the prior DNS failure. Clean tuple `9281b40.../f500728.../a45d69e...` passes `15/15`; no candidate, index or Gate F advance | `WO-013BD`, exact active client/Core bytes, owned default-off endpoints, returned physical phone |
| `WO-013BF` | Package the resolver-corrected Core in the exact active Windows setup without mutating the non-isolated host | Cross-repository source, package and retained manifest evidence | Client/Core `f500728.../a45d69e...` produces setup `81268d7e...`; all `8/8` required files match and bundled DLL `53b5e82a...` is exact. Owner unsigned exception and SmartScreen warning remain; setup/install/TUN/DNS/AWG/recovery/candidate proof does not advance | `WO-013BE`, exact active client/Core bytes, owner unsigned-Windows exception, isolated Windows host still required |
| `WO-013BG` | Separate WARP behavior from the current LDPlayer egress boundary and retain a bounded physical Android host-lifecycle preflight | Cross-repository pre-candidate Android runtime evidence | Exact x86_64 WARP, automatic ordinary fallback and independent WARP-off control all terminate `EGRESS-001`, so LDPlayer is classified `BLOCKED_BY_LDPLAYER_NETWORK_CURRENT_ORIGIN`; cleanup restores WARP off and no service/TUN. Exact physical service/TUN survives Wi-Fi/LTE/Wi-Fi, Doze and standby, then restores system state and stops cleanly, but secure keyguard leaves WARP egress/UI and preference restore open. No row or candidate advance | `WO-013BE`, exact active Android bytes, returned physical phone, owner unlock required for continuation |
| `WO-013BH` | Make Smart DNS bundle/parity deterministic across Windows LF/CRLF checkouts and run the exact no-mutation PLAN across all active nodes | Platform source/artifact and owned-topology preflight evidence | Platform `64982d9.../8bdc21f...` passes `20/20` focused tests, Go test/vet, Ruff and policy parity; two exact-source bundles are byte-identical. All seven active-node PLANs report active UFW, occupied TCP/443, absent runtime material and zero mutation. Under the no-purchase policy there is no safe current deploy target; `SMARTDNS-01` remains `I3` | `WO-013AS`, exact current platform/client policy truth, owned read-only node access, separate migration/rollback required before any APPLY |
| `WO-013BI` | Replace a false intermediate Smart-DNS spare-address signal with a strict structured bind-scope audit before deployment | Platform source/artifact and owned-topology correction evidence | Platform `ff7e653...` advances reports to v3 and passes `23/23` focused tests plus Go/Ruff/manifest/parity gates. Two exact-source bundles match. Strict PLANs prove `de` has exact TCP/443 binds on both globally routable assigned addresses and the other six nodes use wildcard/dual-stack binds; zero active nodes have an unclaimed public address, runtime material or mutation. The v2 lead is invalid and never authorized APPLY; `SMARTDNS-01` remains `I3` | `WO-013BH`, independent structured `de` replay, exact v3 PLAN reports, frontend migration/rollback still required before any APPLY |
| `WO-013BJ` | Bind the canonical selected AI/gaming policy to owned resolver behavior and the active client routing copy | Platform/client source, contract tests and inactive bundle evidence | Platform `84f16dd...` proves representative OpenAI, Gemini and Xbox exact/child `A` synthesis, outside refusal and alternate-type NODATA. Go test/vet, `23/23` platform tests, `17/17` client routing tests and policy parity pass; two exact-source inactive bundles match. This is `PASS_SOURCE_CONTRACT_ONLY`; `SMARTDNS-01` remains `I3` | `WO-013BI`, exact canonical policy/client copy, live dedicated-address/access/leak/rollback/origin gates still open |
| `WO-013BK` | Assemble and sign resolver-corrected candidate.6 without promoting it or borrowing pre-candidate runtime proof | Cross-repository candidate/source/signing evidence | Exact current tuple passes `15/15`; six artifacts match, Windows runtime files match `8/8`, release-index PR `13` passes and main-only signer run `33239993242` returns `READY_SIGNED_MANIFEST`. Exact phone ARM64 install identity matches, but keyguard and unavailable isolated Windows leave runtime gates open. `promotion_authorized=false`; no public release/stable mutation | `WO-013BE`, `WO-013BF`, `WO-013BJ`, exact build/signing inputs, owner-unlocked phone and isolated Windows host still required |
| `WO-013BL` | Run digest-bound candidate.6 Gate F and retain an AWG2/AWG3.1/default LDPlayer differential | Cross-repository candidate decision/runtime evidence | Exact signed x86_64 bytes and owned lab binding pass. AWG2, AWG3.1 and ordinary default all form service/TUN/routes/DNS but fail at the same LDPlayer egress boundary; cleanup restores default. Gate F validates all inputs and returns `BLOCKED` with `2 PASS`, `17 non-PASS`, `0 FAIL`; physical phone remains keyguard-locked and Windows/origins/manual lanes are open | `WO-013BK`, exact signed candidate.6, owned LDPlayer, owner-unlocked phone and isolated Windows host still required |
| `WO-013BM` | Bind exact candidate.6 current-origin performance, classify Brain access and regenerate Gate F | Candidate decision/origin evidence | Exact clean platform health/catalog p95 pass. Both owned Brain inventory address candidates reject retained auth without mutation, so Brain is `BLOCKED_BY_ACCESS`; RU remains `NOT_RUN`. Successor Gate F is `BLOCKED` with `3 PASS`, `16 non-PASS`, `0 FAIL` and zero validation errors | `WO-013BL`, exact platform source, current workstation origin, restored Brain access still required |
| `WO-013BN` | Repeat exact candidate.6 portal and client-channel rollback without touching tracked or runtime state | Exact-candidate rollback evidence | Strict-v2 signed handoff, client dry-run/forward/reverse/final validation and portal byte-identical rollback pass in an isolated fixture. DOD-18 and P12-130 stay `I3`; runtime pointer/kill rollback and Brain/post-rollback readback remain open, so Gate F count is unchanged | `WO-013BM`, exact platform/client/Core, signed candidate.6, retained stable handoff |
| `WO-013BO` | Bind PB-14 incident identity to the exact candidate.6 Android build and reject historical hardcoding | Exact-candidate release-health control evidence | Historical build `4030` output is invalid and excluded. The fixed fail-closed harness derives hash-matched signed build `4046`; corrected isolated promotion stop and rollback request pass. PB-14 and DOD-23 stay `I3`; no candidate rebuild, external switch or Gate F advance | `WO-013BK`, signed physical-install binding, isolated Action Intent fixture |
| `WO-013BP` | Exercise exact candidate.6 per-app directions, WARP materialization and process-stop cleanup on LDPlayer | Exact-candidate Android emulator runtime evidence | Selected/excluded app configs, count-only journal, service/TUN force-stop cleanup and native WARP endpoint/TUN formation pass their bounded slices. All transport attempts retain the common LDPlayer origin egress block; final default/WARP-off/no-material restore passes. Four rows gain stronger `I3`; Gate C and Gate F do not advance | `WO-013BL`, exact signed x86_64 candidate.6, owned LDPlayer; physical phone and Windows host still required |
| `WO-013BQ` | Prove whether exact candidate.6's IPv4-only Android TUN releases or blocks unconfigured IPv6 on LDPlayer | Exact-candidate Android source/runtime evidence | IPv6-capable LDPlayer forms an IPv4-only WARP TUN with no IPv6 address/default route. Exact source has no `allowFamily` call and matches Android's default family-block contract. Structural fail-closed slice passes; external/physical leak tests and Gate C/F remain open | `WO-013BP`, exact signed x86_64 candidate.6, exact client source, official Android VpnService contract; physical phone still required |
| `WO-013BR` | Close candidate.6 Brain-origin through the owner's trusted SSH configuration and regenerate Gate F | Candidate decision/origin evidence | Exact Brain source `197/197`, readiness `23/23` and enabled delivery `7/7` pass without deploy or restart. Successor Gate F is `BLOCKED` with `4 PASS`, `15 non-PASS`, `0 FAIL` and zero validation errors; RU and physical/Windows/manual lanes remain open | `WO-013BM`, `WO-013BQ`, exact signed candidate.6, owner-trusted SSH configuration |
| `WO-013BS` | Determine whether the canonical RU-origin sandbox is ready for an exact candidate.6 run without changing it | Candidate origin/environment evidence | Trusted key access and NTP pass, but `9/9` source paths, `4/4` systemd units, `4/4` configuration records and the spool are absent. RU becomes `MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED`; Gate F remains `4 PASS`, `15 non-PASS`, `0 FAIL` | `WO-013BR`, exact platform source, canonical RU sandbox, separate owner authorization required before install/run/upload |
| `WO-013BT` | Replace the stale HY2 server artifact with an exact candidate.6 Core build and repeat the owned-node PLAN | Cross-repository exact-Core artifact and owned-node preflight evidence | Two complete Go builds produce the same verified `a45d69e...` bundle. Brain HY2 kill-switch, owned-node root/tools/UFW and free UDP port pass read-only; runtime material is absent and no mutation/handshake occurs. HY2 remains `I3`; Gate F stays `4/15/0` | `WO-013AR`, `WO-013BR`, exact candidate.6 Core, explicit authorization and owner-only runtime material still required before APPLY |
| `WO-013BU` | Build the exact candidate.6 RU-origin source/unit bundle and prove guarded install/rollback readiness without mutation | Candidate origin/artifact and owned RU-host PLAN evidence | Corrects the historical dependency map from nine to ten required members; two exact Git-object bundles are byte-identical. Trusted key plus `sudo -n`, tools, empty `0/14` targets and absent units/user/group/spool pass read-only. Runtime material and install/run/upload/readback remain absent; W9-02 stays `I1` and Gate F stays `4/15/0` | `WO-013BS`, exact candidate.6 platform, explicit authorization and owner-only four-file runtime material still required before APPLY |
| `WO-013BV` | Prove a no-purchase shared-443 Smart DNS source path without migrating a live frontend | Post-candidate Smart DNS source/artifact evidence | Strict loopback PROXY v2 restores original source addresses; validated HAProxy exact/child-SNI and `send-proxy-v2` rendering pass. Two inactive bundles are byte-identical. Current installer remains dedicated-only; no frontend/Brain target, remote PLAN, mutation, live access or candidate claim exists | `WO-013BI`, `WO-013BJ`, post-candidate platform source; guarded frontend migration/rollback and successor candidate still required |
| `WO-013BW` | Implement the guarded shared-443 frontend operation and run the corrected all-node PLAN | Post-candidate Smart DNS frontend source/PLAN evidence | Receipt/CAS-bound PLAN/APPLY/ROLLBACK source, exact previous unit and `28` focused tests pass. Read-only PLAN exits zero on all seven nodes with no mutation: five are not applicable; RU and RU-SPB render valid candidates but lack the active fronted backend. No target, deploy or access claim exists | `WO-013BV`, post-candidate platform source; fronted server install/runtime material, explicit target/APPLY and successor candidate still required |
| `WO-013BX` | Add guarded fronted server install mode and prove the exact immutable artifact with RU install PLANs | Post-candidate Smart DNS server source/artifact/PLAN evidence | Fronted mode is exact loopback TCP/18443 plus PROXY v2 and UFW-neutral receipt-bound rollback. `49` focused tests, Go/Ruff/parity, two byte-identical bundles and a zero-finding ten-surface security scan pass. Read-only PLAN on RU and RU-SPB reports free backend listener, absent runtime material and zero mutation; RU is proposed but not selected, SPB/Brain remain unselected. The then-assumed ARM64 terminal target is corrected by WO-013CE's observed `x86_64` runtime | `WO-013BW`, exact post-candidate platform source; runtime material, separately authorized server/frontend APPLY and successor candidate still required |
| `WO-013BY` | Correct the full-product supply-chain evidence and sign candidate.7 without rebuilding unchanged binaries | Cross-repository candidate/source/signing evidence | Exact tuple `af259f3.../b2497af.../a45d69e...` passes `15/15`; fail-closed validation passes `6/6` artifacts and `8/8` Windows runtime files with a corrected 349-component SBOM and six-subject provenance. Release-index PRs `15/16` and signer run `33256988566` pass; public-key readback returns `READY_SIGNED_MANIFEST`. Exact candidate.7 runtime and Gate F remain open; no public/stable mutation | `WO-013BX`, exact candidate.7 metadata and same-byte artifact set; returned physical phone, LDPlayer, isolated Windows host and trusted Pi SSH target still required |
| `WO-013BZ` | Bind candidate.7 current/Brain origins, exact LDPlayer AWG rehearsal, direct Pi RU baseline and first Gate F | Candidate runtime/origin/decision evidence | Exact current-origin health/catalog and Brain source/readiness/delivery pass. AWG2/AWG3.1 form service/TUN/DNS on the hash-matched x86_64 artifact but remain blocked by the common LDPlayer egress boundary; cleanup restores default/no TUN/no AWG. Pi proves direct RU DNS/DoH/HTTP baseline and a ChatGPT HTTP 403 above DNS, but no candidate or Smart DNS runtime. Gate F validates `19/19` pointers and returns `BLOCKED` at `4/15/0` | `WO-013BY`, exact candidate.7 signed outputs, owned LDPlayer and trusted Pi/Brain SSH; physical Android, Windows, exact RU client, Smart DNS runtime and manual external gates remain required |
| `WO-013CA` | Compare exact candidate.7 physical AWG2/AWG3.1 against the ordinary mobile control and restore default state | Exact-candidate physical Android runtime evidence | Exact ARM64 candidate.7 on Beeline passes ordinary `legacy_reality_fallback`. Both owned AWG profiles create Android-validated VPN/TUN, IPv4 route and managed DNS but fail selected-exit proof. Both slices are `FAIL_AUTHENTICATED_EGRESS_NOT_CONFIRMED`; candidate.7 is rejected for replacement. Final default/no-lab/no-VPN restore passes; remaining Android and Windows matrices stay open | `WO-013BZ`, exact candidate.7 ARM64 package, returned physical phone and guarded owner-only profile binding; server/transport diagnosis and replacement candidate required |
| `WO-013CB` | Correct owned AWG reply policy, physical mobile MTU and AWG3.1 packet growth, then repeat exact candidate.7 physical proof | Platform operations and exact-candidate physical Android evidence | Both live/material MTUs move `1408 -> 1280`; AWG3.1 keeps header protection/random trailers and disables data content padding. Alignment and Core interop pass. Exact ARM64 candidate.7 reaches green tunnel/DNS/authenticated egress for AWG2 and AWG3.1 on Beeline, then restores default/no-material/no-TUN. Platform/client source changes still require candidate.8; Windows and remaining matrices stay open | `WO-013CA`, guarded owned-node access, exact candidate.7 ARM64 package and returned physical phone |
| `WO-013CC` | Build/sign candidate.8, prove exact physical false-green/AWG2/AWG3.1 egress, refresh current-origin and rerun Gate F | Cross-repository candidate, Android runtime and release decision evidence | Exact tuple `241a83b.../3459438.../a45d69e...` passes `15/15`, six-artifact supply validation, public release-index signing and physical ARM64 ordinary/AWG2/AWG3.1 authenticated egress with clean restore. Fresh current-origin passes. Gate F validates `19/19` pointers and remains `BLOCKED` at `4/15/0`; Brain/RU, Windows, Smart DNS and remaining manual matrices stay open | `WO-013CB`, exact candidate.8 artifacts and signed release-index source; no public promotion |
| `WO-013CD` | Continue exact candidate.8 physical Android WARP/per-app/network/lifecycle/DNS proof and restore the owner device | Exact-candidate physical Android and release evidence | Exact ARM64 bytes pass the explicit WARP fallback/revoke path, selected-app TUN traffic/bypass, handoff, screen-off, tile/notification, Doze/standby and Private DNS interaction. IPv6 is blocked by the underlying path and active WARP, UDP53/MTU, excluded-app, multi-OEM and endurance remain open. Device privacy/restore pass; Gate F stays `4/15/0` | `WO-013CC`, returned unlocked physical phone, exact candidate.8 artifact; no rebuild or public promotion |
| `WO-013CE` | Prove current Smart DNS egress semantics and reject an RU direct-egress deploy for DNS-only access bypass | Post-candidate Smart DNS architecture and isolated runtime evidence | Exact Linux/amd64 bundle passes config, strict PROXY-v2, DoH and verified AI/gaming TLS passthrough on the trusted `x86_64` terminal fixture with zero production mutation and full cleanup. Source dials application origins directly, so RU deployment is `NO_GO`; no target is selected, `SMARTDNS-01` stays `I3`, Gate F stays `4/15/0` | `WO-013BX`, exact source/bundle, owner terminal access; guarded colocated foreign frontend/backend PLAN remains required |
| `WO-013CF` | Bind fresh exact Brain, direct RU-terminal and Windows current-host evidence, then regenerate candidate.8 Gate F | Candidate origin, Windows runtime and release decision evidence | Brain source/readiness/delivery pass `197/197`, `23/23`, `7/7`. Four RU-terminal samples prove owned public access and RU-SPB `4/4` but retain RU as manual because the canonical contour is absent. Exact Windows install/service/authenticated-IPC/restart/uninstall/idle-network restore passes on the owner host while connected and clean-VM checks remain manual. Gate F validates `19/19` pointers and returns `BLOCKED` at `5/14/0` | `WO-013CC`–`WO-013CE`, exact signed candidate.8, trusted Brain/Pi access and owner-current-host authorization; no public promotion |
| `WO-013CG` | Add the missing guarded first foreign transport-front bootstrap and prove the `it` canary PLAN without mutation | Post-candidate Smart DNS frontend source/PLAN evidence | Platform `c2ffc48...` adds one-backend HAProxy preservation, root-only receipts, exact inbound-invariant SQLite CAS, outcome-labelled automatic rollback and fronted-state recovery. `68/68` focused tests pass. Read-only `it` PLAN proves the exact VLESS/Reality/Xray/free-loopback shape and returns `mutation_performed=false`; `SMARTDNS-01` remains `I3` | `WO-013CE`, foreign owned read-only access; explicit maintenance APPLY, transport/rollback proof, runtime material, Smart DNS APPLY and successor candidate remain required |
| `WO-013CH` | Retain exact candidate.8 LDPlayer install/catalog and ordinary/AWG2/AWG3.1 differential, restore default state and refresh Gate F | Exact-candidate Android emulator and release-decision evidence | Exact x86_64 APK `ec07ba17...2627` installs/readbacks byte-identically, all seven locations render, ordinary egress fails closed, AWG2/AWG3.1 confirm tunnel/DNS/selected egress, and guarded cleanup removes lab material/membership with no TUN. Only the LDPlayer rehearsal row advances; Gate F validates `19/19` and remains `BLOCKED` at `6/13/0`. Client PR `37` merges current readiness reconciliation; no physical/public/stable claim | `WO-013CF`, exact signed candidate.8 x86_64 package and owned LDPlayer; thirteen Gate F rows and Gate G remain open |
| `WO-013CI` | Replay source-plan Gates A–E against signed candidate.8 and regenerate Gate F | Exact-candidate source, hosted-Core and release-decision evidence | Exact Core CI passes `5/5`; Gate B passes `70/70 + 111/111`; Gate D passes `196/196 + 12` and `25/25`; Gate E retains `15/15 + 9/9` plus current-origin p95. Gates A–E remain `BLOCKED` with zero explicit failures; Gate C advances `I2 -> I3`. Gate F validates `19/19` and remains `BLOCKED` at `6/13/0`; no Gate G/public/stable mutation | `WO-013CH`, exact signed candidate.8 sources and retained evidence; live Windows/Android/RU/Smart-DNS/provider/Operator/legal/performance gates remain open |
| `WO-013CJ` | Repeat exact candidate.8 portal/client rollback without touching tracked or runtime state | Exact-candidate rollback evidence | Signed candidate.8 handoff generation, client initial/dry-run/forward/reverse/final validation and portal byte-identical rollback pass in an isolated fixture. DOD-18 and P12-130 remain `I3` with stronger exact-candidate proof; runtime pointer/kill rollback and current/Brain post-rollback readback remain open, so Gate F stays `6/13/0` | `WO-013CI`, exact platform/client/Core, signed candidate.8 and retained stable handoff |
| `WO-013CK` | Prove the foreign `it` transport frontend through live APPLY, rollback and re-APPLY, then classify current Beeline whitelist reachability | Post-candidate Smart DNS transport/runtime evidence | Two fail-closed operation defects are corrected in platform `9dee549...`; `it` passes frontend APPLY, current/Brain TCP/443, receipt-bound rollback, post-rollback reachability and re-APPLY. Exact Smart DNS PLAN passes with zero mutation, but no runtime material/DNS name/certificate exists and the service is not installed. Beeline controls pass while POKROV control and `ru_spb` time out before VPN/TLS. Phase 10 stays `I3`; candidate.8 and Gate F `6/13/0` are unchanged | `WO-013CG`, exact fronted bundle/server PLAN, authorized `it` maintenance and physical Beeline differential; owner DNS-name authorization and runtime deployment remain required |
| `WO-013CL` | Close the exact candidate.8 physical inverse excluded-app traffic/bypass subcheck without overstating the Android aggregate | Exact-candidate Android physical evidence | The same redacted control app crosses TUN while included, leaves Android VPN UID ranges after exclusion and loads a benign public page with only bounded background TUN traffic. Exact APK/certificate readback and clean restore pass; a failed terminal marker is discarded. Client PR `38` merges; Gate C remains `I3/BLOCKED` and Gate F stays `6/13/0` | `WO-013CD`, exact signed candidate.8 ARM64 package and one owned physical Android device; active WARP, IPv6/leak, UDP53/MTU, broader OEM, endurance and delivery rows remain open |
| `WO-013CM` | Bind signed candidate.10 to exact Brain, canonical RU probe and exact LDPlayer AWG2/AWG3.1 evidence | Candidate origin, Android emulator and release-decision evidence | Brain passes `197/197`, `23/23`, `7/7`; the exact Pi rollback/install and full ingest/admin pipeline pass, but RU verdict is `FAIL 10/13` on independent Brain TLS, free REALITY target and NL TCP failures. Exact x86_64 AWG2/AWG3.1 tunnel/DNS/egress/routes pass and default restore removes lab/VPN state. Physical phone stays manual, Smart DNS DNS is absent `0/4`, and candidate.10 Gate F is not regenerated | Signed candidate.10, owner-authorized Brain/Pi operations and owned LDPlayer; three RU failures, authoritative DNS, physical Android, isolated Windows and exact Gate F remain required |
| `WO-013CN` | Generate a fail-closed Gate F decision for exact signed candidate.10 without inheriting stale candidate.8 results | Exact-candidate release-decision evidence | Signed manifest/keyring/source tuple and all `19/19` pointers validate. Gate F returns `NO_GO`: `5 PASS / 14 non-PASS`, including one explicit RU-origin FAIL, with zero validation errors. Eight checks remain manual, three not run, one missing and hosted private checks skipped by owner. Gate F stays `I3`; Gate G remains unauthorized | `WO-013CM`, exact signed candidate.10 outputs and public release-index keyring; fix/reject RU failures and complete exact/manual gates before any new Gate F |
| `WO-013CO` | Replay exact candidate.10 Gates A–E and direct current-origin, then regenerate Gate F | Exact-candidate source, origin, performance and release-decision evidence | Gate B passes `70/70 + 111/111`, Gate D passes `196/196 + 12` and `25/25`, local quality passes `15/15`, static performance `9/9`, and current-origin p95 health/catalog pass at `36.8219/46.127 ms`. All five gates remain `BLOCKED` on live/manual boundaries with zero new source defects. Gate F validates `19/19` and remains `NO_GO` at `6/13/1`; the physical phone is unavailable and untouched | `WO-013CN`, exact candidate.10 source worktrees and current-origin authorization; classify three RU failures, then complete physical Windows/Android and remaining manual gates |
| `WO-013CP` | Retire stale disabled Brain/Free delivery targets, repeat candidate.10 RU-origin and bound the remaining path failures | Post-signing candidate runtime/control-plane and origin evidence | Separate guarded backups plus compare-and-set operations clear two stale drain flags only after zero-route checks. Brain runtime is stopped; Free external shutdown remains `BLOCKED_BY_ACCESS`. Two fresh canonical Pi runs agree at `FAIL 9/11` on NL and RU-SPB timeouts. NL DNS/listener/firewall/ban checks pass locally while no Pi packet is observed at server ingress. Smart DNS remains blocked at authoritative DNS `0/4`; physical phone remains unavailable | `WO-013CM`–`WO-013CO`, owner-authorized control-plane retirement and direct-RU Pi; fix authoritative DNS, pursue new RU route/provider evidence and complete remaining manual gates before a new Gate F |
| `WO-013CQ` | Replay the exact candidate.10 Smart-DNS client configuration on LDPlayer and restore its prior state | Exact-candidate Android emulator and Smart-DNS evidence | The installed x86_64 APK matches candidate.10 bytes. Custom DoH, direct DoH, external Smart DNS and selected AI/Gaming purposes survive force-stop/relaunch; visible copy warns that application traffic is direct and the IP is not hidden. Cleanup returns to Automatic/VPN DNS, clears lab state and leaves no TUN/VPN. Live DoH/service access is `NOT_RUN` because authoritative DNS is still `0/4`; physical Android remains unavailable | `WO-013CP`, exact candidate.10 APK and owned LDPlayer; publish authoritative DNS, install the guarded resolver and run live access/attribution/leak/rollback plus physical-device matrices |
| `WO-013CR` | Close obsolete release PRs, preserve active work and recheck authoritative Smart-DNS DNS | Cross-repository release governance and DNS readiness evidence | Thirteen already-promoted, old-tuple or explicitly superseded PRs close with zero merges and zero branch deletions. Platform HAPP PR 57, client Linux PR 28 and Core AWG lifecycle PR 5 remain open with explicit release boundaries. All four delegated servers return `NXDOMAIN`, so authoritative DNS remains `0/4` and ACME/server/frontend APPLY remain `NOT_RUN` | `WO-013CQ`, current platform/client/Core promotion refs and GitHub PR metadata; publish the authorized A record in the delegated Timeweb zone, then execute the existing guarded Smart-DNS sequence. Adopt retained active PRs only on their declared release lines |
| `WO-013CS` | Refresh, natively prove and adopt the conditional Linux beta foundation on current client main without changing candidate.10 | Client conditional-Linux successor source and platform evidence | PR 28 head `646e944...` resolves cleanly on current main and merges as `30ccf4f...`. Full client/seed/docs gates, Linux Flutter `4/4`, runtime engine `70` plus one expected skip, and native Linux gofmt/test/vet/build pass. Hosted zero-step job is `SKIPPED_BY_OWNER`. `LNX-001` remains `I3`; actual live connect/network rollback/package/Ubuntu 24.04 proof stays open and Linux remains outside 1.2.0 | `WO-005G`, `WO-013AP`, `WO-013CR`, owner-approved solo exception; implement and retain live Core/network/recovery/package/VM evidence before I4 or a Linux claim |
| `WO-013CT` | Run candidate.10 Core AWG2/AWG3.1 interop from an owned Raspberry Pi 4 direct RU fixed-network path | Exact-Core protocol and bounded RU-origin evidence | Guarded platform `8dfaeab...` cross-builds exact Core `a45d69e...` to one digest-verified Linux ARM64 test binary. AWG2 and randomized-trailer AWG3.1 both pass tunneled TCP, verified TLS and authenticated-egress marker; remote temp/process cleanup is `0/0`, no raw material returns and no server/runtime mutates. `AWG-10` advances only `I1 -> I2`; candidate Android/Windows and multi-ASN coverage remain open | `WO-013CC`, `WO-013CM`, `WO-013CS`, owned Pi/Brain/AWG lab access; repeat on candidate.10 physical Android, isolated Windows and distinct mobile/fixed RU networks before I3/I4 |

## Current evidence

- `BASELINE.json` records repository heads and observed gaps as of 2026-08-21.
- `EXECUTION-LEDGER.csv` is the machine-readable item register; `(plan,id)` is the primary key.
- `EXECUTION-INDEX.md` defines the completion index and aggregate reporting rules.
- `SOURCE-CROSSWALK.md` preserves plan coverage and conflict decisions.
- `WO-013AU-candidate5-signing-brain-awg-route-and-physical-runtime.md`
- `WO-013AV-candidate5-gate-f-current-and-brain-origin.md`
- `WO-013AW-free-publication-preflight.md`
- `WO-013AX-candidate5-owned-awg-physical-interoperability.md`
- `WO-013AY-replacement-awg-bounded-diagnostics.md`
- `WO-013AZ-awg-bind-contract-and-runtime-recheck.md`
- `WO-013BA-pinned-awg-peer-local-interop.md`
- `WO-013BB-owned-awg-reply-routing-and-physical-recheck.md`
- `WO-013BC-core-artifact-convergence-and-windows-assembly.md`
- `WO-013BD-security-fixed-core-physical-awg-egress.md`
- `WO-013BE-awg-default-resolver-physical-pass.md`
- `WO-013BF-windows-resolver-setup.md`
- `WO-013BG-android-warp-lifecycle-preflight.md`
- `WO-013BH-smart-dns-portability-and-zero-purchase-plan.md`
- `WO-013BI-smart-dns-strict-address-topology.md`
- `WO-013BJ-smart-dns-ai-gaming-contract.md`
- `WO-013BK-candidate6-signed-assembly.md`
- `WO-013BL-candidate6-gate-f-and-ldplayer-differential.md`
- `WO-013BM-candidate6-current-origin-and-gate-f.md`
- `WO-013BN-candidate6-local-rollback.md`
- `WO-013BO-candidate6-pb14-build-binding.md`
- `WO-013BP-candidate6-ldplayer-per-app-warp-lifecycle.md`
- `WO-013BQ-candidate6-ldplayer-ipv6-family-block.md`
- `WO-013BR-candidate6-brain-origin-and-gate-f.md`
- `WO-013CC-candidate8-signed-physical-awg-and-gate-f.md`
- `evidence/013CC-candidate8-signed-physical-awg/`
- `WO-013CD-candidate8-android-physical-matrix.md`
- `evidence/013CD-candidate8-android-physical-matrix/`
- `WO-013CE-smart-dns-egress-architecture-and-mini-fixture.md`
- `evidence/013CE-smart-dns-egress-architecture/`
- `WO-013CF-candidate8-brain-ru-windows-evidence.md`
- `evidence/013CF-candidate8-brain-ru-windows-evidence/`
- `WO-013CG-smart-dns-foreign-frontend-bootstrap-plan.md`
- `evidence/013CG-smart-dns-foreign-frontend-bootstrap/`
- `WO-013CH-candidate8-ldplayer-rehearsal-and-gate-f.md`
- `evidence/013CH-candidate8-ldplayer-rehearsal/`
- `WO-013CI-candidate8-gates-a-e-replay.md`
- `evidence/013CI-candidate8-gates-a-e/`
- `WO-013CJ-candidate8-local-rollback.md`
- `evidence/013CJ-candidate8-local-rollback/`
- `WO-013CK-smart-dns-it-live-frontend-canary.md`
- `WO-013CL-candidate8-android-excluded-app.md`
- `evidence/013CL-candidate8-android-excluded-app/`
- `WO-013CM-candidate10-brain-ru-ldplayer-evidence.md`
- `evidence/013CM-candidate10-brain-ru-ldplayer/`
- `WO-013CN-candidate10-gate-f-no-go.md`
- `evidence/013CN-candidate10-gate-f/`
- `WO-013CO-candidate10-gates-a-e-current-origin-and-gate-f.md`
- `evidence/013CO-candidate10-gates-a-e/`
- `WO-013CP-candidate10-ru-control-plane-retirement.md`
- `evidence/013CP-candidate10-ru-control-plane-retirement/`
- `WO-013CQ-candidate10-ldplayer-smart-dns.md`
- `evidence/013CQ-candidate10-ldplayer-smart-dns/`
- `WO-013CR-candidate10-pr-hygiene.md`
- `evidence/013CR-candidate10-pr-hygiene/`
- `WO-013CS-linux-current-main-native-proof.md`
- `evidence/013CS-linux-current-main-native-proof/`
- `WO-013CT-candidate10-core-ru-pi-awg-interop.md`
- `evidence/013CT-candidate10-core-ru-pi-awg/`
- `WO-013CU-candidate10-bounded-security-scan.md`
- `evidence/013CU-candidate10-bounded-security-scan/`
- `WO-013CV-candidate10-client-security-scan.md`
- `evidence/013CV-candidate10-client-security-scan/`
- `WO-013BS-candidate6-ru-origin-environment-preflight.md`
- `WO-013BT-candidate6-hy2-artifact-and-plan.md`
- `WO-013BU-candidate6-ru-origin-bundle-and-install-plan.md`
- `WO-013BV-smart-dns-shared-443-fronted-source-proof.md`
- `WO-013BW-smart-dns-frontend-migration-plan.md`
- `WO-013BX-smart-dns-fronted-server-install-plan.md`
- `WO-013BY-candidate7-corrected-supply-chain-and-signing.md`
- `WO-013BZ-candidate7-runtime-ru-pi-and-gate-f.md`
- `WO-013CA-candidate7-physical-awg-differential.md`
- `WO-013CB-candidate7-owned-awg-mobile-pmtu.md`

  Together these work orders bind the signed candidate.5 artifact set and
  hosted signature, exact
  one-file Brain deploy, bounded physical Android/Smart-DNS runtime proof,
  later exact AWG2/AWG 3.1 protocol failures, replacement corrections and
  clean device restore without authorizing public or stable promotion. WO-013AY
  retains the bounded replacement diagnostic bridge, exact diagnostic artifact
  hashes, LDPlayer failure categories and clean lab restore without transferring
  emulator evidence into a candidate or physical gate. WO-013AZ adds the
  reproduced bind-contract correction and proves with later signed bytes that
  the handshake/egress failure remains unchanged. WO-013BA proves the corrected
  client bind path against a direct pinned official peer. WO-013BB then binds
  the multi-address reply-route correction, persistent server readback and
  physical Beeline AWG2/AWG 3.1 replacement passes without converting those
  production-signed bytes into an immutable candidate. WO-013BC converges the
  corrected Core source into byte-reproducible Android/Windows artifacts,
  retains the unsigned Windows pre-candidate setup and clean local `15/15`
  aggregate, while keeping Windows live TUN/DNS/AWG and candidate gates open.
  WO-013BD then repeats both profiles with the exact security-fixed Core on
  physical Beeline, proving handshake and bidirectional payload but retaining
  the common Android selected-endpoint `EGRESS-001` failure and a clean restore.
  WO-013BE corrects that common resolver boundary and proves retained green
  AWG2/AWG3.1 state on exact LDPlayer and physical Beeline bytes, while keeping
  Phase 10 at `I3` and candidate creation false.
  WO-013BF packages the same resolver-corrected Core into the active unsigned
  Windows setup with exact manifest readback, but performs no install or live
  Windows network action on the non-isolated build host.
  WO-013BG then separates a shared LDPlayer `EGRESS-001` environment boundary
  from WARP behavior and retains only a partial physical Android host-lifecycle
  pass; protected WARP egress, per-app, leak, OEM and candidate proof stay open.
  WO-013BH makes the Smart-DNS bundle contract Windows-portable and records the
  exact all-active-node no-mutation PLAN result: every current TCP/443 endpoint
  is occupied, so deployment stays closed under the no-purchase policy unless
  an already owned address is deliberately freed through a guarded rollback.
  WO-013BI rejects an intermediate v2 spare-address false lead, replaces it
  with strict report-v3 parsing and proves no current active node has an
  unclaimed globally routable address outside its TCP/443 bind scope.
  WO-013BJ then binds the unchanged selected OpenAI/ChatGPT, Gemini and Xbox
  policy to representative owned-resolver and client-routing behavior as
  source-only proof without changing the topology conclusion.
  WO-013BK then creates and signs candidate.6 from the exact corrected source
  tuple and artifact set, while keeping every unrun device, Windows, origin and
  promotion gate explicitly open. WO-013BL adds candidate.6's own digest-bound
  `2 PASS / 17 non-PASS / 0 FAIL` Gate F and the exact AWG2/AWG3.1/default
  LDPlayer comparison without upgrading the shared emulator-origin block.
  WO-013BM adds exact current-origin PASS, retains Brain as access-blocked and
  RU as not run, and advances only the Gate F evidence count to `3/16/0`.
  WO-013BN repeats the real portal/client rollback mechanisms against exact
  candidate.6 in an isolated fixture without converting local proof to runtime
  Gate F PASS. WO-013BO then rejects the hardcoded-build false-exact PB-14
  output and repeats the local stop/request with candidate-bound build `4046`,
  without rebuilding the signed candidate or advancing Gate F. WO-013BP adds
  exact candidate.6 selected/excluded-app configs, count-only journaling,
  force-stop cleanup and WARP materialization on LDPlayer, then restores the
  default state without converting the emulator-origin block into device PASS.
  WO-013BQ then binds the observed IPv4-only TUN to Android's default
  family-block contract and records a structural IPv6 fail-closed PASS without
  converting it into an external or physical leak PASS. WO-013BR then closes
  the false Brain access block through the owner's trusted SSH configuration,
  retaining exact source `197/197`, readiness `23/23`, enabled delivery `7/7`
  and the successor `4/15/0` Gate F without any runtime mutation. WO-013BS
  then proves the canonical RU sandbox is accessible but the exact probe
  contour is not installed, preserving RU as non-PASS and Gate F at `4/15/0`.
  WO-013BT replaces the stale HY2 server artifact with an exact candidate.6
  Core build and proves the guarded remote PLAN is ready except for deliberate
  owner-only runtime material, without deployment or Gate F advancement.
  WO-013BU corrects the RU dependency set to ten, binds a byte-identical exact
  candidate.6 source/unit bundle and proves the canonical host is privilege/tool
  ready with `0/14` occupied targets, while keeping runtime material, install,
  execution, upload and readback explicitly absent.
- `evidence/013BH-smart-dns-zero-purchase-plan/013BH-smart-dns-zero-purchase-plan.json`
  binds the exact source/bundle/policy identities, seven sanitized PLAN report
  digests, zero-mutation result and no-safe-current-target decision without
  retaining addresses, credentials, keys or runtime material.
- `evidence/013BI-smart-dns-strict-address-topology/013BI-smart-dns-strict-address-topology.json`
  binds the v2 rejection, current v3 source/bundle, seven strict PLAN report
  digests, independent `de` count-only replay and zero-mutation decision.
- `evidence/013BJ-smart-dns-ai-gaming-contract/013BJ-smart-dns-ai-gaming-contract.json`
  binds the unchanged canonical policy, server/client contract tests,
  byte-identical inactive bundle and source-only evidence ceiling.
- `evidence/013BK-candidate6-signed-assembly/013BK-candidate6-signed-assembly.json`
  binds the exact source/artifact tuple, local gate, hosted signature, exact
  phone install identity and remaining runtime/promotion evidence ceiling.
- `evidence/013BY-candidate7-corrected-supply-chain-and-signing/013BY-candidate7-corrected-supply-chain-and-signing.json`
  binds the final candidate.7 source tuple, same-byte six-artifact set,
  corrected offline supply-chain PASS, hosted signature/receipt and explicit
  device/origin/promotion evidence ceiling.
- `evidence/013BZ-candidate7-runtime-ru-pi-gate-f/013BZ-candidate7-runtime-evidence.json`
- `evidence/013BZ-candidate7-runtime-ru-pi-gate-f/013BZ-candidate7-gate-f-evidence.json`
- `evidence/013BZ-candidate7-runtime-ru-pi-gate-f/013BZ-candidate7-gate-f-input.json`
- `evidence/013BZ-candidate7-runtime-ru-pi-gate-f/013BZ-candidate7-gate-f-decision.json`
- `evidence/013BZ-candidate7-runtime-ru-pi-gate-f/013BZ-candidate7-signed-runtime-binding.json`
  bind candidate.7 current/Brain PASS, exact LDPlayer origin-block/restore,
  direct Pi RU baseline and the validated `4/15/0` Gate F decision without
  retaining device, host, network or credential identifiers.
- `evidence/013BL-candidate6-gate-f/013BL-candidate6-gate-f-decision.json`
  binds the exact signed candidate identity, all 19 evidence pointers and the
  current `BLOCKED` decision; the adjacent evidence files retain the sanitized
  LDPlayer differential and non-PASS manual/runtime rows.
- `evidence/013BM-candidate6-current-origin-and-gate-f/013BM-candidate6-gate-f-decision.json`
  binds exact current-origin PASS, Brain access failure, separate RU status and
  the successor `3 PASS / 16 non-PASS / 0 FAIL` candidate.6 decision.
- `evidence/013BR-candidate6-brain-origin-and-gate-f/013BR-candidate6-gate-f-decision.json`
  binds exact candidate.6 Brain source/readiness/delivery PASS, retains RU as
  separate `NOT_RUN` evidence and records the current
  `4 PASS / 15 non-PASS / 0 FAIL` decision.
- `evidence/013BS-candidate6-ru-origin-environment-preflight/013BS-candidate6-ru-origin-environment-preflight.json`
  binds exact candidate.6/platform and post-candidate harness identities,
  key-reachable/NTP-synchronized read-only preflight, the fully absent RU
  runner contour and the unchanged `4 PASS / 15 non-PASS / 0 FAIL` boundary.
- `evidence/013BT-candidate6-hy2-artifact-and-plan/013BT-candidate6-hy2-artifact-and-plan.json`
  binds exact candidate.6 Core, byte-identical lab.2 server bundles, verified
  Brain kill-switch/owned-node preconditions, missing runtime material and the
  explicit no-deploy/no-handshake/no-Gate-F-advance ceiling.
- `evidence/013BU-candidate6-ru-origin-bundle-and-install-plan/013BU-candidate6-ru-origin-bundle-and-install-plan.json`
  corrects the RU dependency map to ten exact members, binds the byte-identical
  candidate.6 bundle and sanitized key-plus-`sudo -n` PLAN, and preserves the
  no-runtime-material/no-install/no-run/no-Gate-F-advance ceiling.
- `evidence/013BV-smart-dns-shared-443-fronted-source-proof/013BV-smart-dns-shared-443-fronted-source-proof.json`
  binds strict loopback PROXY-v2 source restoration, validated HAProxy
  exact/child-SNI rendering, the byte-identical inactive bundle and the
  no-frontend/no-deploy/no-candidate ceiling.
- `evidence/013BN-candidate6-local-rollback/013BN-candidate6-local-rollback.json`
  binds the exact strict-v2 handoff, byte-identical client/portal rollback,
  fail-closed invalid invocation and unchanged runtime/public boundaries.
- `evidence/013BO-candidate6-pb14-build-binding/013BO-candidate6-pb14-build-binding.json`
  binds the rejected historical-build output, corrected candidate.6 build
  identity, local promotion stop/rollback request and unchanged mutation/Gate F
  boundaries.
- `evidence/013BP-candidate6-ldplayer-per-app-warp-lifecycle/013BP-candidate6-ldplayer-per-app-warp-lifecycle.json`
  binds the exact per-app/WARP managed-profile shapes, bounded journal outcomes,
  force-stop recovery, privacy assertions and clean default restore without
  retaining raw configs, package identifiers or device identity.
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
  server source, immutable bundle and APK/device-state evidence at `I3`.
  `WO-013BH-smart-dns-portability-and-zero-purchase-plan.md` binds the portable
  bundle plus seven-node PLAN matrix. `WO-013BI-smart-dns-strict-address-topology.md`
  is the current bind-scope authority and rejects the intermediate v2 false
  lead. None claims a free endpoint, deploy, live DNS/SNI relay, service access,
  leak/rollback/origin or candidate.
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

## Retained candidate.3 and pre-candidate history

013AE is the retained candidate.3 identity authority; 013AF is its
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

WO-013AO was the replacement pre-candidate source authority. Its clean
platform/client/Core tuple `e5ef03a...` / `c196dff...` / `f44dbe8...` passes
the exact Node 22.14 local aggregate `15/15`, and Android Core provenance is
rebound without a binary delta. At capture time it did not replace signed
candidate.3 or repair candidate.3's `NO_GO`; WO-013AU now supersedes that
current-candidate boundary without rewriting this retained history.
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

The owner declined paid GitHub and branch protection. Hosted jobs are now
`SKIPPED_BY_OWNER` under `OWNER_SOLO_EXCEPTION`, never PASS. WO-013AW audited
all fetched reachable history with redacted outputs: Core and the release index
are already public, while direct visibility flips for the existing platform
and client repositories remain unsafe because retained history, binaries,
oversized blobs, rights review and publication licenses are unresolved. The
approved public-source direction therefore uses sanitized source-only
successors plus clean-clone public CI; it is not a release prerequisite and no
visibility mutation occurred here.

The owned AWG and HY2 labs are still default-off. WO-013AX removes the earlier
Beeline reverse-UDP blocker: exact candidate.5 AWG2 and AWG 3.1 start the
Android VPN and exchange outer traffic, but neither establishes an
authenticated handshake or inner traffic. They are protocol `FAIL`, not
network-blocked. HY2's node preflight is green, but live testing still requires
the exact HY2-aware control-plane deployed with its kill-switch engaged,
root-only runtime material, separately authorized exact-bundle install and
encrypted device material. Direct DoH is not VPN-free Smart DNS. Public
`v1.2.0`, candidate assets and the stable pointer remain prohibited until
candidate.7 reaches Gate F `GO` and the owner separately authorizes
Gate G. The build-4046 external Smart DNS client path remains a default-off lab
until a compatible resolver and live access/leak/rollback evidence exist.
Windows SmartScreen remains the owner-approved unsigned direct-beta
limitation.

## Current next action — close candidate.13 physical, Windows and origin gates

WO-013CX is the active signed-candidate and runtime authority. The exact
candidate.13 x86_64 package passes the bounded LDPlayer AWG 3.1 -> AWG2 ->
default/Auto lifecycle without an application-process restart and ends in a
clean default/no-lab/no-VPN state. The current next release work is the exact
ARM64 physical install binding required by Gate F, connected clean-VM Windows
TUN/DNS/recovery/uninstall, current/Brain/RU origin refresh, and the remaining
provider, Operator, legal, rollback and performance rows. Public/stable Gate G
remains separately authorized and has not run.

### Retained candidate.5–10 context

WO-013BY is the active signed-candidate authority. It signs the same six build
`1.2.0+4046` bytes against final platform `af259f3...` and corrected
SBOM/provenance. WO-013BZ is the active runtime/decision authority: fresh
current- and Brain-origin checks pass, exact candidate.7 AWG2/AWG3.1 formation
on LDPlayer remains blocked by the common emulator egress boundary and restores
cleanly, and the Pi establishes a direct RU terminal baseline without executing
the candidate. Candidate.7 Gate F is `BLOCKED` at `4 PASS`, `15 non-PASS`,
`0 FAIL`. Candidate.6 remains signed immutable history; none of its runtime or
origin results is silently transferred.

WO-013AU remains the signed candidate.5 authority, WO-013AV remains its frozen
digest-bound Gate F authority, and WO-013AX remains its later mandatory AWG
runtime authority. Candidate.5 history is unchanged. The corrected
release harness, full Brain source `197/197`, readiness `23/23`, enabled
delivery `7/7` and current-origin API budgets still pass their exact slices.
The frozen Gate F result remains `BLOCKED` with `6 PASS`, `13 non-PASS`,
`0 FAIL`, but later AWG2 and AWG 3.1 physical results are explicit protocol
`FAIL`. Candidate.5 is therefore `REJECTED_FOR_REPLACEMENT`. Output remains
`ACTIONS_ARTIFACT_ONLY`; no public release or stable pointer exists. WO-013BK
supersedes only the active candidate boundary with signed candidate.6, and
WO-013BL supplies candidate.6's first digest-bound Gate F result. WO-013BM adds
exact current-origin PASS and its historical access-blocked Brain result.
WO-013BR closes that harness blind spot and supplies the current `BLOCKED`
result with `4 PASS`, `15 non-PASS`, `0 FAIL` and zero validation errors.
WO-013BS then narrows RU-origin from `NOT_RUN` to
`MANUAL_OWNER_TEST_ENVIRONMENT_NOT_INSTALLED`: access and NTP pass, but the
runner/uploader contour is wholly absent and no run/upload/readback occurred.
  WO-013BT separately refreshes the HY2 server bundle to exact candidate.6 Core
  and proves the no-mutation install PLAN is ready except for owner-only runtime
  material; HY2 remains undeployed and no live transport claim is made.
  WO-013BU separately corrects the RU source map, proves a deterministic exact
  source/unit bundle and a guarded no-mutation install PLAN, but leaves RU-origin
  non-PASS until an authorized install, run, upload, heartbeat and admin readback.
None of these
work orders rewrites candidate.5 evidence or inherits candidate.5's result.
WO-013BN adds exact local portal/client rollback proof, and WO-013BO adds the
corrected candidate-bound build-4046 PB-14 stop/request proof; both remain at
`I3` and leave the Gate F count unchanged. WO-013BP then proves the bounded
candidate.6 LDPlayer per-app/WARP/force-stop slice. WO-013BQ proves the
structural Android IPv6 family block for the observed IPv4-only TUN. WO-013BR
  then advances only the Brain-origin Gate F row. WO-013BS and WO-013BU do not
  advance RU-origin; external/physical DNS/IPv6 leak, the uninstalled RU contour and the
other 15 Gate F rows remain non-PASS.

Bounded privacy-safe Core diagnostics, the exact binder and the stale-location
correction remain retained. Core `6b8ddca...` fixes the bind contract and Core
`3c2b114...` proves direct pinned-peer interoperability. WO-013BB closes the
remaining owned-endpoint/mobile-path defect: the multi-address node selected
the wrong reply route, while late SNAT could not repair the already selected
path. Platform `f79974c...` adds source-port policy routing plus bounded SNAT;
service-cycle readback, physical Beeline AWG2/AWG 3.1 handshakes and
bidirectional inner traffic, and post-cycle Core interop all pass.

WO-013BC now binds byte-reproducible AAR/DLL outputs from Core `3c2b114...` to
clean client `75aabd9...`, retains an owner-approved unsigned Windows setup and
passes the exact DLL host-safe proxy lifecycle `100/100`. The clean converged
platform/client/Core local aggregate also passes `15/15`, but explicitly says
`candidate_proven=false`.

WO-013BD moves the active security-fixed Core repeat from open to measured:
client `064fcd0...` plus Core `547f096...` installs exactly on physical Beeline,
ordinary Frankfurt passes, and both owned AWG profiles complete fresh
handshakes plus bidirectional TCP/UDP payload. Both still fail the Android
selected-endpoint URL test as `EGRESS-001`. IPv4-only managed DNS matches the
IPv4-only endpoint route but did not remove the failure. Core hosted CI passes
all five jobs; the client hosted run remains a zero-step access stop.

WO-013BE closes that diagnosed source-bound failure: Core `a45d69e...` routes
the AWG inner-FQDN lookup through the configured default resolver, and exact
production-signed client `68779c4...` retains green AWG2/AWG3.1 state on
LDPlayer and physical Beeline. The clean current tuple
`9281b40.../f500728.../a45d69e...` passes the refreshed local aggregate `15/15`
with `candidate_proven=false`.

WO-013BF closes the active-source Windows setup packaging gap. WO-013BK binds
the corrected tuple and six rebuilt artifacts into the trusted signed
candidate.6 manifest. WO-013BL confirms that exact candidate.6 AWG2, AWG3.1
and ordinary-default LDPlayer runs all reach TUN/routes/DNS but share the same
emulator-origin egress block, then restore cleanly. WO-013BP adds exact
selected/excluded-app shapes, count-only privacy, process-stop cleanup and WARP
endpoint/TUN formation on that same emulator, again ending at the common
origin block and restoring default/WARP-off/no-material state. WO-013BQ then
confirms that the exact IPv4-only TUN has no IPv6 lane and, without an
`allowFamily` call, follows Android's fail-closed family contract. The exact
candidate.6 ARM64 package identity remains retained as historical phone
evidence. Candidate.7 binds the same exact installed ARM64/x86_64 bytes, and
WO-013BZ supplies its bounded LDPlayer runtime record plus first Gate F.
WO-013CA supplies the exact candidate.7 physical differential: ordinary
Beeline control passes while AWG2/AWG3.1 fail selected-exit proof, so
candidate.7 is rejected for replacement. WO-013CB closes that server/transport
diagnosis: persisted reply-source policy, MTU `1280` and the mobile-safe AWG3.1
randomized-trailer variant make both exact candidate.7 ARM64 profiles pass the
app's tunnel/DNS/authenticated-egress state over Beeline. WO-013CC then binds
that corrected source into signed candidate.8, and WO-013CD closes the bounded
physical Android WARP-fallback/per-app/handoff/lifecycle/Private-DNS slice with
a clean restore. WO-013CF then closes exact Brain source/readiness/delivery and
the Windows current-host install/service/IPC/restart/uninstall slice while
retaining RU and Windows live-network rows as manual. WO-013CH then closes the
exact candidate.8 LDPlayer rehearsal with separate ordinary fail-closed and
AWG2/AWG3.1 PASS outcomes plus a clean default restore, advancing Gate F to
`6/13/0`. WO-013CI then replays Gates A–E on the same signed tuple, removes the
stale candidate.3 Gate B defect, records zero explicit candidate.8 failures and
advances Gate C to `I3` without changing Gate F. The next release action is
connected Windows TUN/DNS/AWG/recovery proof plus the prioritized AWG/DNS lane
and remaining manual Gate F evidence; canonical RU automation is separate.
WO-013CL then closes the named candidate.8 physical inverse excluded-app
traffic/bypass subcheck without changing that historical Gate F count.
WO-013CM/013CN/013CO/013CP supersede the active candidate state with signed
candidate.10: exact Brain and LDPlayer AWG2/AWG3.1 pass; guarded control-plane
retirement removes disabled Brain/Free from the dynamic mandatory manifest;
canonical RU still fails `9/11` on NL and RU-SPB path timeouts. Exact source
Gates A–E retain zero new source defects and direct current-origin
health/catalog pass. All five gates remain `BLOCKED`, the physical phone
remains manual and untouched, and the latest exact Gate F remains `NO_GO
6/13/1` without regeneration while RU is still failing.
Active
WARP, external IPv6/leak, UDP53/MTU, multi-OEM and endurance remain open. No
candidate.8 physical runtime result is transferred into candidate.10 `I4`.
Do not spend the lane on SPB beyond bounded evidence; `ru_spb` passes the
canonical candidate.10 run. HY2 remains default-off and follows the existing
kill-switch/material/install guards.

For Smart DNS, WO-013CE proves the exact fronted Linux/amd64 bundle's strict
PROXY-v2, DoH and application TLS passthrough on the observed `x86_64` trusted
terminal host, then records `NO_GO` for RU direct egress as a DNS-only access
bypass. WO-013CG closes the no-mutation inventory and guarded first-frontend
source/PLAN for the foreign `it` canary. WO-013CK then corrects two fail-closed
operator defects and proves guarded frontend APPLY, current/Brain transport,
receipt-bound rollback and guarded re-APPLY. Smart DNS is still not installed:
the public DoH name is authorized, but its A record is absent on all four
delegated authoritative servers. The next honest slice requires authoritative
DNS `4/4`, a trusted certificate and root-only runtime material before separate
server/route APPLY and actual ChatGPT/Gemini/Xbox session access, resolver/DNS-SNI attribution,
leak/privacy, lifecycle and origin evidence. The same work order classifies the
bounded Beeline whitelist path: control/API and `ru_spb` are filtered before
VPN/TLS, so direct `it` is not the emergency bootstrap for that condition.
Android system Private DNS stays open because the current server is DoH-only.
Windows live network/recovery, candidate.10 RU failure remediation, provider/PostgreSQL/outbox,
Operator, legal/commercial, accessibility, comparable-device performance and
post-public-promotion health also remain open before Gate F can become `GO`.
Public/stable Gate G remains separately authorized and prohibited until then.
