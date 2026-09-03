# POKROV 1.2.0 Megaplan — Wave Index

Last updated: 2026-09-03
Classification: `ACTIVE_EXECUTION`
Wave status: `PHASE_11_CANDIDATE31_SIGNED_SUPPLY_PASS_GATE_F_NO_GO_BRAIN_SOURCE_DRIFT`
Release candidate: `POKROV_1_2_0_CANDIDATE31_PRIVATE_SIGNED_GATE_F_NO_GO`

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

## Current candidate reconciliation

Candidates.20–23 remain immutable `NO_GO` history. WO-013FA rejects
candidate.22 after exact connected uninstall leaves the UI and 13 loaded files.
WO-013FB is the candidate.23 rejection authority: with its exact Windows
service still `Running`, a headless 32-client pipe-contention probe accepts `9`
requests and rejects `23`. Narrow predecessor PASS slices are retained as
history and are not transferred by label.

WO-013FB remains the signed-supply and correction authority for candidate.24.
WO-013FG then closes the retained development-only webapp lock finding in
successor platform source and passes fresh zero-finding audits plus local
quality `15/15` without rewriting candidate.24.

At that historical point, WO-013FH was the authority. Private
`pokrov-1.2.0-candidate.25`, app
`1.2.0+4053`, binds merged platform `883cd103...`, client `54259b0...`, Core
`cd8f0f4...` and signed release-index `18d9cb4...`. Because the only source
change is the platform development lock, its strict-v2 supply deliberately
reuses the same six exact build-4053 client artifacts while binding them to a
new handoff `b65b9e7e...`, SBOM `f6d8ec5...`, provenance `4f106a2e...` and
manifest/signature/receipt `7161bae7...` / `f83cf5ac...` / `2c18b318...`.
Release-index signer run `33709201344` passes; output remains private and
`promotion_authorized=false`.

Candidate.25's exact installer file identity passes inside the headless
Windows 11 guest and all `11/11` required runtime files bind to its manifest.
WO-013FJ adds another full headless CLI rebuild plus exact candidate.25 proof
on an ephemeral hosted Windows machine: machine install, `11/11` installed
files, LocalSystem service, ordinary-UI authenticated IPC, SCM restart, clean
uninstall and idle route/DNS/adapter restoration pass. The rebuild setup is
rehearsal-only and is never substituted for immutable candidate bytes. The
main desktop and input are not used. Connected TUN/DNS/egress, connected
uninstall, reboot/sleep/crash and interactive SmartScreen remain unrun.

Candidate.25 refreshes current-public and Brain read-only origin evidence.
Brain exact-source/readiness/subscription/delivery passes `197/197`, `23/23`,
`5/5` and `7/7 x3`; current health/catalog p95 is `48.8176/51.3052 ms`.
WO-013FE remains the candidate.24 source replay history: Gate B passes
`70/70 + 111/111`, Gate D passes `196/196 + 12` and `25/25`, and local quality
passes `15/15`, including client `413/413`, cabinet `69/69` and static
performance `9/9`. Its disposable `1.1.6 -> candidate.24 -> 1.1.6` rollback
restores portal/client pointers byte-identically and focused tests pass
`16/16`; guarded runtime rollback is still open.

WO-013FH is the current Gate F authority. Signed identity, all `19/19`
evidence pointers and attached hosted checks validate. Current-origin and
Brain-origin advance to PASS, producing exact `BLOCKED 5 PASS / 14 non-PASS /
0 FAIL` with zero validation errors. Installed Windows and Android, packaged
AWG/Smart DNS, authenticated sessions, general RU origin, runtime rollback,
provider/Operator/legal, comparable performance and final aggregate evidence
remain open. No tag, public asset, Store object, stable pointer or promotion
exists.

WO-013FI adds a fresh candidate.25 exact-Core AWG3.1-then-AWG2 PASS from the
owned Raspberry Pi 4 over its direct RU fixed-network path. It is supplemental
source-level Core evidence only: packaged Android/Windows, mobile and
multi-ASN rows remain open, and Gate F stays `BLOCKED 5/14/0`.

WO-013FJ is the bounded exact Windows clean-host authority. It closes basic
hosted install/service/IPC/restart/uninstall and idle restoration only. The
connected `windows_live_network` row remains non-PASS, so WO-013FH remains the
current Gate F authority at `BLOCKED 5/14/0`.

WO-013FK corrects the CMake registration issue exposed by WO-013FJ's CLI
rehearsal. Fresh Debug `8/8` and Release `7/7` native CTest pass; the Debug-only
service integration is no longer scheduled in Release. This is successor
test-harness source only and gives candidate.25 no new runtime credit. GitHub
run `33719302139` executes zero steps and is `BLOCKED_BY_ACCESS` by the account
Billing/spending limit, not represented as a hosted PASS.

WO-013FL takes the merged WO-013FK successor client source through another
full headless CLI build and an isolated Windows 11 upgrade/reboot. The new
Windows-only `candidate.26-precursor` passes the complete client tests, Debug
`8/8`, Release `7/7`, `11/11` staged and installed file identity, ordinary-UI
authenticated service IPC and post-reboot automatic LocalSystem service. It is
not a created or signed multi-platform candidate. Connected TUN/DNS/egress is
`NOT_RUN` because no managed profile or connect action is supplied. Its failed
`portal.pokrov.space` sentinel is non-canonical and receives no blocker credit.

WO-013FM corrects that sentinel to `api.pokrov.space` and exercises exact
candidate.25 through a secret-free direct-only profile in the isolated Windows
11 VM. Authenticated IPC, Core, TUN, route/DNS ownership, health, disconnect
rollback and connected guest-reboot restoration pass. The ordinary UI remains
at first-run onboarding and no trial/account is created, so managed DE/AWG/
Smart-DNS and connected-uninstall gates remain open. Gate F stays `5/14/0`.

WO-013FN rejects the next Windows CLI build as `candidate.27-precursor`: its
first direct upgrade from the retained candidate.23 VM reproducibly aborts
before replacement when the installer cannot re-resolve the installation
owner. The second attempt receives no credit. Client PR 72 merges the bounded
correction: only an existing machine installation may reuse its protected,
exactly validated owner SID; clean install remains fail-closed. The resulting
`candidate.28-precursor` passes the full CLI build, native `7/7 + 8/8`, bounded
static scan, first-pass `11/11` upgrade, direct TUN/DNS lifecycle and connected
guest reboot. It is not a created candidate. Candidate.25 remains immutable
and Gate F remains `5/14/0`, but promotion now requires a new exact successor.

WO-013FO creates that exact successor. Private signed candidate.29 rebuilds
all six `1.2.0+4053` artifacts from platform `efb05e0...`, merged client
`7e3e771...` and pinned Core `cd8f0f4...`; offline supply and main-only Ed25519
signing pass. Its exact Windows setup passes first-attempt upgrade from the
candidate.28 precursor, `11/11` installed-file identity, ordinary-user UI,
automatic LocalSystem service, direct-only TUN/DNS lifecycle and connected
guest-reboot restoration. Candidate.29 becomes the active signed supply at
that point, then receives a later exact Gate F snapshot. WO-013FP first binds all `19/19` pointers at
`BLOCKED 2/17/0`, and WO-013FQ refreshes current/Brain origin to `NO_GO
2/17/1` after enabled DE times out in three Brain samples.

WO-013FR then completes fresh first launch and real managed Windows attempts.
AWG3.1 and AWG2 stage and fail the authenticated egress probe with clean
rollback. Exact-Core AWG3.1 and AWG2 independently return
`failed_no_outer_response` from the owned direct-RU Pi. A later fresh ordinary
control never stages Core: six successful panel copies are present, but the
slow `ru_spb` peer causes the aggregate timeout before any `UserNode`
confirmation is retained. The earlier ordinary Core-egress claim is withdrawn.
The frozen Gate F snapshot remains `NO_GO 2/17/1`; its AWG-backed Windows
live-network and authenticated-egress rows are explicit FAIL, equivalent to
`2/17/3` if regenerated. The isolated P0 platform defect requires a successor,
so candidate.29 is immutable rejected history. Physical Android, Smart DNS,
provider/Operator/legal, rollback and final aggregate rows stay non-PASS. No
public tag, asset, Store object, stable pointer or promotion exists.

WO-013FS is the immutable candidate.30 authority. Private signed
`pokrov-1.2.0-candidate.30`, app `1.2.0+4053`, binds platform `7c413334...`,
client `7e3e771f...`, Core `cd8f0f41...` and signed release-index
`b06fe143...`. Its six application artifacts build through CLI, and the exact
Windows setup passes `11/11` installed identity, service, direct TUN/DNS and
connected-reboot checks without host input control. Two fresh Core builds with
the CI-pinned Go 1.25.13 and MinGW GCC 13.2.0 reproduce the candidate DLL
byte-for-byte; `100/100` proxy lifecycle repetitions pass.

Candidate.30 is nevertheless `NO_GO`: strict replay proves that its CycloneDX
root still identifies candidate.29 and carries a different artifact-set
digest. SLSA provenance also carries the prior artifact-set digest and stale
candidate references. The detached signature and artifact bytes validate, but
SBOM and provenance are mandatory signed-release contracts. Platform PRs 198
and 199 add the missing fail-closed bindings; exact replay now stops first at
`sbom_root_bom_ref_mismatch`. Gate F is `NO_GO 1 PASS / 18 non-PASS / 2 FAIL`
with zero validation errors. The
candidate remains unmodified rejected history; the successor must regenerate
SBOM/provenance/handoff metadata and obtain a new hosted signature. Physical
Android and LDPlayer are `NOT_RUN`. No deploy, public release, Store object or
stable-pointer mutation occurs.

WO-013FT supersedes the active candidate boundary with private signed
`pokrov-1.2.0-candidate.31`. The six application files are exact same-byte
reuses of the retained CLI build, while SBOM, provenance and handoff are newly
generated for candidate.31. Strict supply validation passes `6/6` artifacts
and `11/11` Windows runtime files, and hosted signer run `33781982978` produces
a valid manifest/signature/receipt. Candidate.30's provisional expected
artifact-set digest is corrected append-only to the canonical `dce1c4e4...`;
its stale metadata findings and immutable `NO_GO` are unchanged. Candidate.31
Gate F is `BLOCKED 2 PASS / 17 non-PASS / 0 FAIL` with zero validation errors.
ADB sees no device, so exact Android/LDPlayer runtime remains `NOT_RUN`.
Managed Windows transports, origins, rollback, provider/Operator/legal and
final attestations remain open. No Gate G, deploy, public asset, Store object
or stable-pointer mutation is authorized.

WO-013FU adds exact same-byte installed Windows identity and corrected local
IPC contention evidence for candidate.31 without taking host input or changing
host networking. All `11/11` files and the automatic LocalSystem service pass;
the corrected command-line harness passes `32/32`. A noninteractive installer
rerun is explicitly `NOT_CREDITED`, managed network checks remain `NOT_RUN`,
and Gate F stays `BLOCKED 2/17/0`.

WO-013FV supersedes that initial decision with exact current/Brain-origin
evidence. Brain readiness passes `23/23`, subscription stability passes `5/5`
and final enabled delivery passes `7/7` three times, but the deployed Brain
payload matches only `196/197` candidate.31 platform files. Current-origin is
blocked by the untouched owner tunnel. Gate F is therefore exact `NO_GO
2/17/1`; no production reconciliation or promotion is performed.

WO-013FW adds fresh direct-RU Raspberry Pi exact-Core evidence. AWG3.1 and AWG2
pass in that order, and the existing default-off Smart DNS live policy plus
ChatGPT/Gemini/Xbox TLS paths pass from the same origin. This is source-level
Core and live-lab proof, not packaged candidate runtime or authenticated client
egress; Gate F remains `NO_GO 2/17/1`.

WO-013FX corrects WO-013FV's file-history diagnosis without changing its Gate F
decision. After identical CRLF normalization, the sole Brain mismatch exactly
matches known predecessor `1207b63…`; the other `196/197` deployed files match
candidate.31. Brain is therefore one known file behind, not running unknown
manual source. No deploy occurs and Gate F remains `NO_GO 2/17/1`.

## Execution order

| Phase | Architectural outcome | State | Primary WO |
|---|---|---|---|
| 00 | Baseline, authority map, complete execution ledger | Locally proved (`I3`) | `WO-001` |
| 01 | Release manifest, version/provenance contract, CI and stop-ship controls | Candidate.31 is the current private signed supply. Strict replay passes its candidate-bound CycloneDX root/property, SLSA invocation/internal references, six artifacts and eleven Windows runtime files. Exact Gate F is now `NO_GO 2/17/1` because live Brain matches only `196/197` bound platform files; the sole mismatch is exactly known predecessor `1207b63…`. Candidate.30 remains immutable `NO_GO` history. `OWNER_SOLO_EXCEPTION` and the direct-beta Windows signing exception remain explicit. Three zero-step hosted jobs are `BLOCKED_BY_ACCESS_GITHUB_BILLING`; final live aggregate and public promotion remain non-PASS. `DEP-001` retains `I4`; no public asset or promotion exists | `WO-002`, `WO-003`, `WO-003B`–`WO-003J`, `WO-013J`–`WO-013P`, `WO-013CX`, `WO-013DC`–`WO-013DE`, `WO-013EA`, `WO-013EB`, `WO-013EH`, `WO-013EI`, `WO-013EV`–`WO-013FX` |
| 02 | Typed connection state, proof-driven green state, core ABI and migrations | Aggregate Gate B remains `BLOCKED/I3`. Candidate.31 supply, exact same-byte installed identity and corrected local IPC contention pass, but exact managed network runtime has not been rerun. Candidate.30 direct TUN/DNS/reboot evidence is retained only as same-byte predecessor evidence; candidate.29 AWG failures remain immutable history and are not transferred. Physical Android false-green/device matrices remain open. ABI v3 stays deferred until after 1.2.0 | `WO-004`, `WO-004A2`, `WO-004B2`, `WO-004D`, `WO-006I`, `WO-013CX`, `WO-013DD`–`WO-013DF`, `WO-013EN`, `WO-013EV`, `WO-013EW`, `WO-013FB`–`WO-013FU` |
| 03 | Windows/Android runtime boundaries; conditional Linux beta foundation | Gate C stays `BLOCKED/I3`. Candidate.31 exact same-byte installed identity passes `11/11`; the automatic LocalSystem service and corrected local IPC contention pass `32/32`. Its noninteractive setup rerun is `NOT_CREDITED`, while managed AWG/Smart-DNS, connected uninstall, Windows 10, interactive SmartScreen, sleep/crash and IPv6 remain unrun or environment-blocked. ADB saw no device, so exact Android runtime is `NOT_RUN`; host-tunneled emulator output stays excluded. Linux native runtime/packaging remains open and deliberately unshipped | `WO-005`, `WO-005C4`, `WO-005D4`, `WO-005G`, `WO-013CC`–`WO-013CO`, `WO-013CX`, `WO-013DD`–`WO-013DF`, `WO-013DJ`, `WO-013DL`, `WO-013DO`, `WO-013EA`, `WO-013EF`, `WO-013EG`, `WO-013EV`–`WO-013FU` |
| 04 | Observability, error catalog, redacted bundle and support pipeline | Locally complete (`I3`) for shipped Android/Windows scope. Candidate.31's regenerated SBOM/provenance and strict supply validation pass without raw egress or connection material. Candidate.30's stale metadata is immutable rejected history. Deployed runtime/RBAC/audit, connected managed-device evidence and final live privacy attestation remain open | `WO-006`, `WO-006I`, `WO-006J`, `WO-006K`, `WO-006L`, `WO-013S`, `WO-013DJ`, `WO-013DQ`, `WO-013DR`, `WO-013EP`, `WO-013EQ`, `WO-013FB`, `WO-013FH`, `WO-013FJ`, `WO-013FN`, `WO-013FO`, `WO-013FS`, `WO-013FT` |
| 05 | Portal bounded contexts, payments, HTTP/DB/outbox reliability | Locally complete (`GATE-D` and `ARCH-002` at `I3`); 007G–007I split admin, public/client and Action Intent domain/runtime owners. Candidate.31 exact Brain readiness/subscription/delivery passes `23/23`, `5/5` and `7/7 x3`, but deployed source matches only `196/197` bound platform files. The one mismatch is an exact known predecessor blob, not unknown source. Gate D stays `BLOCKED` below I4 until source reconciliation and production provider/PostgreSQL/outbox/reconciliation/operator/runtime-rollback proof exist | `WO-007`, `WO-007G`, `WO-007H`, `WO-007I`, `WO-013CI`, `WO-013CO`, `WO-013EL`, `WO-013EN`, `WO-013FD`, `WO-013FE`, `WO-013FH`, `WO-013FV`, `WO-013FX` |
| 06 | Product facts, subscriptions, checkout, offers and attribution | Local source packages: 008A–008G commercial package at `I2`; 008H–008M close active-client generation, copy/public truth, whole-client product facts, subscription state presentation, no-waterfall loading and the complete local subscription/checkout aggregate at `I3`. WO-013DK completes the generated copy-authority map and active-client drift gate at `I3`. WO-013DU adds current-runtime proof that one logical DE node renders two public address choices in sing-box, Happ, Clash and raw VLESS without duplicating provisioning. Deployed provider, broad commercial-consistency and successor exact-candidate gates stay open | `WO-008`, `WO-008H`, `WO-008I`, `WO-008J`, `WO-008K`, `WO-008L`, `WO-008M`, `WO-013DK`, `WO-013DU` |
| 07 | Canonical Operator Center v2 and legacy admin cutover | Local package complete, including the deterministic 75-operation OpenAPI/TypeScript contract, purpose-bound Telegram OIDC Authorization Code plus PKCE login and same-identity step-up for preprovisioned operators, exact retained-bridge permissions and query-suppressed field redaction; live IdP, authenticated exact-candidate readback and cutover/rollback gates remain open | `WO-009`, `WO-009H`, `WO-009I`, `WO-009J` |
| 08 | App, cabinet and marketing UX/accessibility/performance reconciliation | Locally complete at `I3`. Candidate.25's retained source audits and `15/15` local quality remain history. Exact candidate.31 current-origin measurement is `BLOCKED_BY_ACCESS` because the owner's active tunnel is left untouched, and Brain has one exact-source mismatch now identified as predecessor `1207b63…`. Gate E stays `BLOCKED` below I4 on source reconciliation, authenticated journeys, physical accessibility/OEM/scaling, comparable artifact/device/browser performance, support, general RU-origin and post-promotion evidence | `WO-010`, `WO-013AN`, `WO-013CI`, `WO-013CO`, `WO-013DA`, `WO-013DD`, `WO-013DE`, `WO-013DQ`, `WO-013DS`, `WO-013EL`, `WO-013EN`, `WO-013EO`, `WO-013FD`–`WO-013FH`, `WO-013FV`, `WO-013FX` |
| 09 | Legal-gated, capacity-aware marketing pilot and evidence-based decision | Locally complete (`I3` package); external pilot `NOT_AUTHORIZED` | `WO-011` |
| 10 | FRKN-derived rules and isolated AWG2/AWG3.1/HY2/Smart-DNS owner labs | Candidate.31 exact Core now passes AWG3.1 then AWG2 from the direct-RU Raspberry Pi, and the existing default-off Smart DNS policy/TLS contour passes from the same origin. Candidate.29 failures remain immutable predecessor evidence. Phase 10 remains `I3`, not `I4`: packaged candidate.31 Android/Windows, multi-ASN, UDP/IPv6/MTU, leak/privacy/load/lifecycle and authenticated-session evidence remain open. HY2 remains undeployed; Gecko, Mimic and port hopping remain monitor-only | `WO-012`, `WO-013AO`, `WO-013AR`, `WO-013AS`, `WO-013AU`, `WO-013AX`–`WO-013BL`, `WO-013BP`, `WO-013BQ`, `WO-013BV`–`WO-013BX`, `WO-013CE`, `WO-013CG`, `WO-013CK`, `WO-013DG`, `WO-013DP`, `WO-013DU`, `WO-013EJ`, `WO-013EY`, `WO-013EZ`, `WO-013FB`–`WO-013FW` |
| 11 | Exact-candidate RC matrix, immutable promotion, rollback and go/no-go | Candidate.31 is the current private signed candidate. Its exact supply, signature, same-byte installed Windows identity, local IPC and direct-RU exact-Core AWG pass, but live Brain exact-source identity fails `196/197`; the sole mismatch exactly matches known predecessor `1207b63…`. Gate F is `NO_GO 2/17/1` with zero validation errors. The Pi evidence is not packaged-client or general-RU Gate F proof. Candidate.30 and candidate.29 remain immutable rejected history. Physical Android, managed Windows AWG/Smart DNS, general-RU origin, provider/Operator/legal, runtime rollback, comparable performance and final rows remain open. No public `v1.2.0`, Store object, stable switch or promotion occurred | `WO-013`, `WO-013BK`–`WO-013FX` |

Active Phase 10/11 supersession: WO-013FT is the current signed-candidate
authority, WO-013FV is the current Gate F authority, and WO-013FX is its
append-only source-diagnosis correction. Candidate.31's signature and regenerated
supply metadata pass, but exact Brain source identity fails `196/197`; the one
mismatch is exact predecessor `1207b63…`, and the decision remains `NO_GO
2/17/1`. Its remaining runtime, origin, approval, rollback and final-attestation
rows are explicit non-PASS. WO-013FS
retains candidate.30 as immutable `NO_GO 1/18/2` history; its corrected
canonical expected artifact-set digest does not change the stale retained
metadata findings or decision.
WO-013FU is supplemental candidate.31 Windows evidence only: exact same-byte
installed identity and corrected local IPC contention pass, while its installer
rerun is not credited and no managed connection row advances.
WO-013FV adds current/Brain-origin truth: current-origin is access-blocked by
the untouched owner tunnel; Brain readiness and delivery pass, but live source
drift is one explicit FAIL. Production reconciliation needs separate approval.
WO-013FW is supplemental candidate.31 source-level and live-lab evidence:
direct-RU Pi AWG3.1/AWG2 and Smart DNS policy/TLS pass, while packaged-client,
authenticated-session and general-RU Gate F rows remain open.
WO-013FX corrects the historical no-known-Git-match conclusion in WO-013FV:
the sole mismatched file exactly matches predecessor `1207b63…` after identical
CRLF normalization. The historical work order stays immutable, production stays
untouched and the Gate F decision does not change.
WO-013FO is the earlier private signed-supply and bounded direct-Windows
authority for candidate.29. WO-013FP/013FQ are its exact Gate F authorities,
ending at `NO_GO 2/17/1`. WO-013FR is the later managed
Windows and direct-RU Pi authority: Windows live network and authenticated
egress are explicit FAIL for AWG3.1/AWG2, and both AWG variants receive no
outer response on the Pi. Its corrected fresh ordinary control stops earlier
at first-run provisioning because the slow peer prevents healthy-node mapping
persistence; candidate.29 therefore requires replacement. A regenerated
aggregate would be `2/17/3`, while the ordinary P0 remains a separate source
defect. WO-013FN remains the earlier source-fix and precursor authority:
candidate.27 is rejected and candidate.28 proves the first-upgrade correction
before the same merged client source is packaged in candidate.29. WO-013FH
remains predecessor Gate F history at candidate.25 `BLOCKED 5/14/0`; that
decision is not transferred. WO-013FB remains the rejection authority for
candidate.23 and predecessor signed-supply authority for candidate.24.
Candidate.23's exact installed Windows service remains `Running` but rejects
`23/32` simultaneous status clients, so those bytes are immutable `NO_GO`.
Candidate.24 contains the bounded retry correction and source/native regression
proof and remains immutable signed history.

WO-013FG is the source authority for the webapp development-lock refresh.
WO-013FH binds it into historical candidate.25 and records exact `BLOCKED
5/14/0`. Candidate.29 remains rejected history. Candidate.31 now binds the
later merged platform/client tuple and all `19/19` Gate F pointers. Gate G and
publication remain unauthorized.

WO-013FI remains candidate.25 exact-Core RU fixed-network AWG history. It
records AWG3.1 and AWG2 PASS without changing candidate.29 packaged-client,
multi-ASN, Gate F or promotion state.

WO-013EW/013EY/013EZ retain candidate.22 signed supply, Windows lifecycle,
Smart DNS and packaged AWG history; WO-013FA records its later connected-
uninstall failure. WO-013EJ/013EK retain candidate.21 Smart DNS and exact-Core
RU fixed-network AWG history. WO-013EL–WO-013EU retain candidate.21 origin,
rollback, Gates A–E, privacy, RU planning and `BLOCKED 5/14/0` Gate F history.
Candidate.29 now exists but still needs its own installed Windows/Android AWG,
Smart DNS, authenticated and general RU-origin, runtime rollback and aggregate
evidence before promotion.

WO-013EA remains the rejected signed-index predecessor authority; WO-013EB is
its exact offline source-gate authority; WO-013EC is its
exact static artifact privacy authority; WO-013ED is its exact offline Gates
A-E authority; and WO-013EE retains its PB-14 physical-boundary evidence.
Candidates 13–19 remain immutable history.
Candidate 17 is rejected for incomplete Windows runtime packaging, candidate
18 for the non-elevated UI/service authentication failure, and candidate 19
for the exact local rule-set service-boundary `CORE-005` failure. Their earlier
supply, rollback, origin and emulator results remain history and cannot
authorize candidate 20 publication.

Candidate 20 contains the merged service-owned rule-set correction and retains
signed supply plus bounded Windows 11 default, migration and connected-reboot
evidence. It is nevertheless immutable `NO_GO`: an exact forced service
termination left its durable recovery journal committed after SCM restart.

Candidate 21 contains the startup-recovery correction and six exact build-4050
artifacts. Its isolated Windows 11 upgrade from that retained failure state,
ordinary non-elevated UI/LocalSystem service and default
TUN/DNS/authenticated-egress/disconnect-restoration slices pass. Strict-v2
handoff `07e0009c...`, refreshed SBOM/provenance and signed manifest
`ce0b8586...` now validate through WO-013EI. WO-013EJ additionally binds the
live default-off Smart DNS runtime entries to this exact source and passes the
direct isolated-Windows DoH/TLS contract. WO-013EK passes AWG2 and AWG3.1
through exact candidate.21 Core on one owned direct-RU fixed-network Pi. It
remains private only: Android runtime, fresh in-place candidate.21
service-restart recovery, Windows 10/non-default paths, packaged Android/
  Windows AWG selection, in-app Smart DNS selection, named origins and
  runtime rollback remain open. WO-013ET first binds the aggregate as Gate F
  `BLOCKED 4/15/0`; WO-013EU adds exact-SHA hosted-check evidence and refreshes
  the current decision to `BLOCKED 5/14/0`. Host-tunneled LDPlayer
network output remains excluded and no nested emulator is used.

WO-013EL additionally binds this exact candidate to the deployed Brain payload
at `197/197`, readiness `23/23`, subscription stability `5/5`, enabled delivery
`7/7` three times and current-origin public API p95 `35.6952/41.3740 ms`.
  Authenticated client egress and general RU-origin remain open; the aggregate
  STOP-SHIP result stays `BLOCKED` and both rows remain non-PASS in WO-013EU.

WO-013EM replaces candidate.18's local pointer evidence with the exact signed
candidate.21 tuple. Manifest, detached signature, receipt and all four source
revisions validate before the disposable portal/client sequence
`1.1.6 -> candidate.21 -> 1.1.6` passes. Stable bytes restore exactly,
receipts validate and unrelated fixture state survives. `DOD-18` and
`P12-130` stay `I3`; real runtime pointer/kill rollback with guarded backup,
current/Brain readback and post-rollback health remains open.

WO-013EN replaces candidate.20's offline source/local-quality authority with
the exact candidate.21 tuple. Gate B passes `70/70 + 111/111`, Gate D passes
`196/196 + 12` and `25/25`, and declared-toolchain local quality passes
`15/15`, including client `413/413`, cabinet `69/69` and static performance
`9/9`. Its separate dependency audit retains one high finding each for
adminapp and marketing from the same transitive development-only
`browserslist` `4.28.4` path. No application/static-export/SBOM/distributed
  client exposure is observed; both active locks required a separate patch.
  Gates A–E remain blocked and their Gate F aggregate row remains non-PASS.

WO-013EO closes that active-line patch: adminapp and marketing now resolve
`browserslist` `4.28.8`, and fresh Node `22.14.0` install, audit, lint and build
pass with zero findings. Package manifests and production dependencies are
unchanged. Candidate.21's recorded source warning remains historical truth; a
successor candidate must be built and signed to consume the patched locks.

WO-013EP replaces candidate.20's static privacy authority with candidate.21.
All six signed artifact hashes bind; five Android archives, the raw Windows
installer and the manifest-bound `11/11` required-file / 302-file staging tree
return zero definite findings. Fingerprint-only triage retains 12
ABI-duplicated occurrences, one value hash and zero strict provider-shape
matches without storing the matched value. Installed Android/Windows,
deployed ingest and final live privacy remain open.

WO-013EQ replaces candidate.20's source-privacy authority with candidate.21.
Platform privacy passes `75/75`, release-source logging `145 + 4`,
observability runtime `29/29` and support bundle `15/15`. The fresh STOP-SHIP
replay retains `7/7`, owner-solo controls `3/3` and open-P0 queries `0/0`, but
  the aggregate remains `BLOCKED` on branch-policy and manual-live controls.
  Installed-device journals/bundles, deployed ingest and final live privacy stay
  open; the final-live Gate F row is `MISSING` in WO-013ET.

WO-013DG supersedes the Phase 10 row's earlier uninstalled Smart DNS boundary.
The owner-authorized `dns.pokrov.space` record is authoritative `4/4`; the exact
`650dc3f...` bundle is live default-off on the foreign `it` canary behind the
owned HAProxy frontend. Certificate/runtime, backend and route APPLY pass. A
real receipt-bound frontend/backend rollback, retained-release re-verification
and re-APPLY pass, followed by matching current-, Brain- and owned-RU-origin
DoH/TLS probes. Ordinary `it` health remains green. `SMARTDNS-01` stays `I3`,
because the bundle and operator corrections postdate immutable candidate.16
and client selection remains disabled; no Gate F/G or public-release credit is
transferred. WO-013EJ supersedes only that old candidate-binding gap: exact
candidate.21 source reproduces the live runtime entries and a fresh direct
Windows VM policy probe passes. `SMARTDNS-01` still stays `I3` because in-app
and physical authenticated/leak/lifecycle evidence remains open.

WO-013DH classifies the shared candidate.16 AWG egress boundary without
changing protocol parameters. Exact candidate.16 Core runners for AWG2 and
AWG3.1 on the owned RU Pi both receive no outer response while using the same
material fingerprints as older passing Core runs. The owner attests the
Datalix account was unpaid; a later current/RU recovery check finds partial TCP
acceptance but no SSH banner or ordinary service readback on either DE address.
This is `PROVIDER_RECOVERY_INCOMPLETE`, not a protocol FAIL or PASS. AWG-10
stays `I2`, W3-02/W3-03 stay `I3`, and exact-Core retry waits for real node
health.

WO-013DU supersedes only that current-runtime provider boundary. Owner-restored
access proves one DE VM with two provider addresses; both pass authenticated
Reality egress, subscription delivery and repeated Brain reachability. AWG2 and
AWG3.1 server listeners are active again. The platform change and runtime
repair postdate candidate.16, so the old client failure is not rewritten and a
successor signed candidate must repeat the client/AWG matrix.

WO-013EK closes the exact-Core portion of that successor retry. Both AWG2 and
AWG3.1 pass outer exchange, tunneled TCP, verified TLS and authenticated egress
from the owned Raspberry Pi 4 over its direct RU fixed-network route using
candidate.21 Core `cd8f0f4...`. Temporary state is removed and no server or
client setting changes. `AWG-10` remains `I2`: packaged Android/Windows,
physical Beeline/Wi-Fi and additional fixed/mobile ASN canaries remain open.

WO-013DV closes that successor-candidate creation boundary. Candidate 18 binds
the restored platform plus the Windows packaging correction, passes the real
hosted signer and exact-source replay, and proves the 11-file Windows install
and public-1.1.6 migration on the isolated VM. It does not inherit candidate.16
Gate F or network evidence. A new Gate F remains prohibited until candidate.18
physical Android, connected Windows and named-origin rows are actually run.

WO-013DW closes the candidate.18 local pointer-replay gap. The signed tuple
passes the disposable portal and client sequence
`1.1.6 -> candidate.18 -> 1.1.6`; portal state and the retained stable handoff
restore byte-identically, receipts validate and unrelated fixture state
survives. Real runtime/stable/public state and devices remain untouched.
`DOD-18` and `P12-130` stay `I3` until the separately guarded runtime
pointer/kill rollback, current/Brain readback and post-rollback health pass.

WO-013DX closes the candidate.18 Brain-origin source/readiness/delivery slice
without mutation. Exact platform source passes `197/197`, the isolated
readiness retry passes `23/23` with five stable subscription samples, and all
seven enabled delivery nodes are open in three redacted samples. The first
readiness attempt's single management-SSH timeout remains retained as non-PASS
history. Current-origin authenticated client and RU-origin remain separate and
open, so W9-02 stays `I2` and Gate F is not regenerated.

WO-013DY closes the candidate.18 source-bound current-origin public API and
local STOP-SHIP slice. Health and catalog pass 50-sample p95 budgets at
`43.5854/43.7925 ms`; all seven permanent regression anchors and all three
owner-solo PR controls pass; queried open P0 counts are zero. Aggregate
STOP-SHIP remains `BLOCKED` on the accepted unprotected-branch state and one
manual live gate. Authenticated client egress and the final live
no-open-P0/false-green/privacy attestation remain open.

WO-013DZ rejects candidate.18 after exact ordinary-user reproduction of its
Windows UI/service authentication failure and supersedes it with signed private
candidate.19. The new candidate binds client `10f5516...`, passes hosted exact
source replay, non-elevated Windows IPC/journal/uninstall/migration and isolated
rollback. Brain exact source/readiness pass; the first six delivery samples
retain two `remote_exec_error` non-PASS records followed by three consecutive
`7/7` results. Source-bound current health/catalog pass at
`38.1649/42.2156 ms`, while aggregate STOP-SHIP remains blocked. Exact LDPlayer
install/launch passes but network credit is excluded by the host tunnel. The
physical Wi-Fi/Beeline and connected Windows matrices remain open; Gate F is
not regenerated and public/stable promotion remains unauthorized.

WO-013EA rejects candidate.19 after the exact service-relocated profile reaches
Core with unresolved ordinary-user rule-set paths and returns `CORE-005`. Client
PR 55 materializes a bounded canonical bundle under the protected service A/B
slot and merges as `8ab9815...`. Signed private candidate.20 binds those bytes;
six-artifact supply, SBOM/provenance, release-index PRs 41/42 and main-only
signer run `33509003189` pass. The first signer dispatch fails closed on a
template-byte mismatch and produces no artifact.

The exact candidate.20 Windows setup then passes isolated Windows 11 default
connect, four service-owned rule sets, TUN, managed DNS, authenticated DE
egress, disconnect rollback, clean uninstall and public-1.1.6 migration.
`WIN-003` and `DOD-04` advance `I1 -> I4`; the distribution becomes `I4=7`,
`I3=319`, `I2=20`, `I1=32`, `I0=0`. Exact post-build source replay run
`33511744299` passes. Candidate.20 Android runtime, remaining Windows matrix,
named origins, candidate rollback and aggregate attestations stay non-PASS.
Gate F is not regenerated and Gate G,
public assets, Store state and stable promotion remain unauthorized.

WO-013EB then repeats source controls on the same exact candidate.20 tuple
without host-network or device runtime actions. Permanent STOP-SHIP regressions
pass `7/7`, owner-solo PR bindings `3/3`, open P0 queries `0/0`, platform
privacy `75/75`, release logging `145 + 4`, observability `29/29` and support
bundle `15/15`. `DOD-01` advances `I2 -> I3`; the current distribution becomes
`I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0`. Branch-policy and final live
aggregate status remain non-PASS, so Gate F is still not regenerated.

WO-013DI supersedes candidate.13-only local rollback evidence. The exact
candidate.16 signed tuple passes the disposable portal and client sequence
`1.1.6 -> candidate.16 -> 1.1.6`; portal state and the stable pointer restore
byte-identically, receipts validate and unrelated fixture state survives.
Tracked/runtime/public/stable state and devices remain untouched. `DOD-18` and
`P12-130` stay `I3` because the separately authorized runtime pointer/kill
rollback plus current/Brain readback and post-rollback health remain open.

WO-013DJ separately closes the Linux native-journal `I3` gap on current
successor client source. PR 47 adds native Unix-datagram and real
missing-socket fallback tests without changing the production envelope, then
an exact ARM64 test binary passes on the owner's Raspberry Pi 4 and one safe
event is read back from the real journal. Signed candidate.16 still contains
no Linux artifact; Ubuntu 24.04 signed-package, service lifecycle,
retention/rotation and network-transaction proof remain open.

WO-013DK closes `FE/P12-210` at local `I3` on current successor source. The
platform synchronizer now pins the copy catalog and marketing-governance
contracts in the active-client seed and generates one authority map covering
all seven catalog namespaces plus the `app.*` review baseline. Client PR 48
merges as `9b52d6a...`; exact-Core seed/docs drift checks and the platform
copy-contract matrix pass. Candidate.16, runtime UI, legal/campaign state,
deploy and publication remain unchanged.

WO-013DL binds the exact candidate.16 Windows setup to a guarded current-host
run. Install, all `8/8` file digests, automatic LocalSystem service and owner
binding, authenticated IPC, SCM restart, uninstall and idle route/DNS
restoration pass. This is a clean app-state result, not a clean OS/VM result.
The account is not ready for connection, so no TUN/DNS/egress claim is made;
the aborted connected attempt restores service, files, registry, adapter,
routes and DNS cleanly. Windows live-network and recovery rows remain open.

WO-013DM records the owner's Datalix payment restoration. Strict SSH still
stops on a changed host identity and leaves `known_hosts` unchanged. Payment
does not prove the answering host, so DE alignment and candidate.16 AWG2/AWG3.1
retries wait for exact provider-console fingerprint confirmation and ordinary
service readback. No protocol result or completion index changes.

WO-013DN adds the signed candidate.16 platform revision to the fail-closed RU
bundle allowlist. Its exact ten-member package reproduces byte-for-byte and
passes verify plus local/remote install PLAN. The selected owned Pi is reachable
and ready at the user/group/tool/spool boundary, but has four source mismatches,
no private runtime material or archive, inactive timers and a retained failed
runner state. Nothing is installed or started; RU-origin remains
`MANUAL_OWNER_TEST` and waits for separately authorized receipt-bound APPLY,
run, upload, heartbeat and admin readback.

WO-013DO closes the exact physical ARM64 install prerequisite without claiming
runtime proof. The candidate.16 production-signed APK reads back
byte-identically as `1.2.0+4049`; the app is not launched, no POKROV process or
`tun0` remains and no screen control is used. Gate F then validates the signed
candidate, exact source tuple, all `19/19` pointers and upstream digest with
zero validation errors. It returns `NO_GO 2/17/2`; the two FAIL rows are the
exact AWG LDPlayer rehearsal and authenticated egress. Gate F stays `I3` and
the 378-row distribution is unchanged.

WO-013DP uses the returned phone and LDPlayer only through background ADB
shell. Both resolve `dns.pokrov.space`; the phone has no POKROV process or TUN
and exposes no non-UI DoH tool. LDPlayer direct DoH/TLS returns the expected
bounded policy shape: outside-policy `REFUSED/0`, ChatGPT/Gemini/Xbox
`NOERROR/1` each, and malformed DoH HTTP 400. No app or VPN is launched and no
screen control is used. `SMARTDNS-01` remains `I3`; client integration and
Gate F are unchanged.

Candidate.16's release-index signer output is `ACTIONS_ARTIFACT_ONLY`,
`promotion_authorized=false`. The strict-v2 handoff and signed receipt are the
candidate authority. Gate F is exact candidate.16 `NO_GO 2/17/2`, not an
inherited older-candidate result. Gate G is `NOT_AUTHORIZED`. XHTTP and HY2 remain post-1.2.0 bounded
lanes; neither is required to promote the base protocol line.

Historical Phase 10 state: WO-013CP superseded the older wording about an
undecided DNS name. At that candidate.10 checkpoint, `dns.pokrov.space` was the
authorized hostname but its A record was absent on all four delegated
authoritative servers, and runtime material, certificate and service were
absent. WO-013DG is the current supersession and closes those server-side
boundaries without transferring candidate credit.

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
| `WO-013` | Prove and promote the exact RC | Cross-repo/release | Signed candidate.16 is current. Signed supply and exact dependency locks have bounded `I4`; full local quality, ordinary LDPlayer traffic and exact physical ARM64 install identity pass. Both current AWG profiles activate but fail authenticated egress, so `W3-02/W3-03` remain `I3`. Gate F validates `19/19` and returns `NO_GO 2/17/2`; Gate G/public/stable promotion remains unauthorized | All release-bound WOs |
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
| `WO-013CU` | Retain a bounded source-exact candidate.10 platform security scan | Platform security evidence | Nine high-risk source surfaces return zero validated findings, but coverage is partial/source-only and does not supply runtime or no-open-P0 release proof | Exact candidate.10 platform source; later candidates require their own bounded reconciliation |
| `WO-013CV` | Retain a bounded source-exact candidate.10 client security scan | Client security evidence | Eight Android/Windows trust surfaces return zero validated P0/P1 findings, but coverage is partial/source-only and not transferred into candidate.13 runtime proof | Exact candidate.10 client source; later candidates require their own bounded reconciliation |
| `WO-013CW` | Prove candidate.11 AWG runtime, expose Smart Connect quarantine and land its successor correction | Candidate Android/runtime defect evidence | Exact candidate.11 AWG3.1/AWG2/ordinary slices are retained, but a repeatable pre-Core quarantine defect rejects the candidate. The client correction is later bound into candidate.13 | Candidate.11 remains immutable rejected history; successor candidate required |
| `WO-013CX` | Sign candidate.13 and prove AWG3.1 -> AWG2 -> default lifecycle on LDPlayer | Exact candidate supply and Android emulator evidence | Six artifacts, signature, SBOM/provenance and exact x86_64 lifecycle proof pass. `W3-02` and bounded `W3-03` reach `I4`; exact ARM64, Windows, origins and remaining manual gates stay open | Exact candidate.13 artifacts and LDPlayer; no public promotion |
| `WO-013CY` | Revalidate candidate.13 against current promotion heads and reconcile the final ledger | Final release audit and decision evidence | Signed supply revalidates, platform/client deltas are docs-only, Core tree is unchanged, and stale candidate references are corrected. Decision is `PROMOTION_BLOCKED_GATE_F_NOT_RUN`; no publication mutation occurs | `WO-013CX`, current platform/client/Core/release-index heads and exact retained artifacts |
| `WO-013CZ` | Repeat exact candidate.13 portal/client rollback without touching tracked or runtime state | Exact-candidate rollback evidence | Signed candidate.13 post-sign handoff generation, client initial/dry-run/forward/reverse/final validation and portal byte-identical rollback pass in an isolated fixture. DOD-18 and P12-130 remain `I3`; runtime pointer/kill rollback and current/Brain post-rollback readback remain open. Gate F is still not run because the exact ARM64 physical binding is absent | `WO-013CY`, exact platform/client/Core, signed candidate.13 and retained stable handoff |
| `WO-013DA` | Refresh exact candidate.13 current/Brain/RU origins and inspect Windows isolation without mutation | Candidate origin and environment evidence | Source-bound current health/catalog p95 and exact Brain source/readiness pass. RU exact source/units are present but runtime material/archive are absent, so RU stays `MANUAL_OWNER_TEST`. No isolated Windows target exists and the owner tunnel is preserved. W9-02 advances only `I1 -> I2`; Gate F remains not run | `WO-013CZ`, exact candidate.13 source, owned current/Brain/Pi read-only access; separate authorization is required for RU APPLY and a separate Windows target is required |
| `WO-013DB` | Refresh candidate.13 Smart DNS `it` readiness without mutation | Current source, immutable bundle, authoritative DNS and owned-node PLAN evidence | Focused tests pass `53/53`; the exact bundle verifies; runtime and frontend PLANs reach the owned node and remain mutation-free. Authoritative DNS is absent `0/4` with unchanged SOA, so ACME/service/frontend/live access remain `NOT_RUN` and `SMARTDNS-01` stays `I3` | `WO-013CK`, exact Smart DNS bundle, current platform master, owned `it` read-only access; owner must publish the DNS-only A record before APPLY |
| `WO-013DC` | Refresh affected candidate.13 Python locks and prove the successor dependency set | Current platform dependency and release-gate evidence | Six direct pins and both universal hash locks refresh. Fresh audits return zero known findings across 27 production and 60 test dependencies; no-op lock recompilation is stable; the complete 3632-test collection is covered with 3622 passed, 10 skipped and zero unresolved failures; two Paramiko 5 read-only owned-node PLANs pass. Candidate.13 stays immutable but becomes explicitly non-promotable; `DEP-001` remains `I3` until a successor is frozen and hosted-proved | `WO-003C`, `WO-013CX`–`WO-013DB`, current platform master; merge the refresh, assemble/sign the successor and rerun exact-candidate gates before promotion |
| `WO-013DD` | Sign dependency-refresh candidate.14, run the complete local quality gate and retain exact LDPlayer truth | Exact candidate supply, quality and Android emulator evidence | Six-artifact signed supply, refreshed dependency locks and local quality `15/15` pass. Exact x86_64 install/default tunnel/DNS/egress pass, but AWG3.1/AWG2 requested profiles remain cached default; current-candidate lab activation is non-PASS and candidate.13 success is not transferred. Cleanup passes. `DEP-001` reaches `I4`; `W3-02/W3-03` return to `I3`; Gate F remains not run | `WO-013DC`, exact platform/client/Core/release-index sources, signed candidate.14 artifacts and LDPlayer; correct managed-profile staging before repeating lab and device gates |
| `WO-013DE` | Sign candidate.16 after correcting managed-profile readiness, prove the bounded Brain deploy, exact local quality and ordinary LDPlayer path | Exact candidate supply, platform runtime, quality and Android emulator evidence | The confirmed-node/key fallback rejects false ready state; Brain `portal-api` source readback passes `197/197`; signed six-artifact supply and local quality `15/15` pass; exact x86_64 default tunnel/DNS/egress passes. Candidate.16 AWG3.1/AWG2 labs are `NOT_RUN`; `DEP-001` retains `I4`, `W3-02/W3-03` stay `I3`, and Gate F remains not run | `WO-013DD`, platform PR 129, exact platform/client/Core/release-index sources, signed candidate.16 artifacts and LDPlayer; run current-candidate labs, exact physical Android and isolated Windows before Gate F |
| `WO-013DF` | Repeat candidate.16 AWG 3.1 and AWG2 on LDPlayer and retain exact fail-closed truth | Exact candidate Android emulator and transport evidence | Both guarded binds and exact runtime profile activations pass; each creates VPN/tun0, managed DNS and IPv4 routes, then fails authenticated egress without false green. Each removes the VPN. Final default cleanup/reconnect/disconnect passes. `W3-02/W3-03` stay `I3`; Gate F remains not run | `WO-013DE`, exact candidate.16 x86_64 artifact and owned LDPlayer; isolate the shared egress boundary, then complete physical Android and Windows without transferring older proof |
| `WO-013DG` | Deploy the exact Smart DNS bundle on `it`, prove bounded live behavior and execute receipt-bound rollback/re-apply | Current platform runtime, owned-node and three-origin evidence | DNS is authoritative `4/4`; trusted runtime, backend and HAProxy route APPLY pass; real frontend/backend rollback, exact-release verification and re-APPLY pass; current/Brain/RU DoH and TLS/SNI probes agree; ordinary `it` health remains green. The service stays client-disabled/default-off and postdates candidate.16, so `SMARTDNS-01` remains `I3` and release gates do not advance | `WO-013CK`, `WO-013DB`, exact `650dc3f...` bundle and owner-authorized `it` runtime; bind to a successor candidate only if shipping Smart DNS in 1.2.0 |
| `WO-013DH` | Classify the candidate.16 AWG no-response result against DE provider state and guard the retry boundary | Exact candidate Core, RU Pi and owned-node availability evidence | Exact AWG2/AWG3.1 Core runners cleanly return no outer response; material fingerprints match older passing inputs, but no PASS transfers. Owner attests Datalix was unpaid; current/RU recovery checks find partial TCP acceptance with no SSH banner or service readback. Result is provider recovery incomplete, protocol not run. `AWG-10` stays `I2`, `W3-02/W3-03` stay `I3`, Gate F unchanged | `WO-013DF`, exact candidate.16 Core and owned RU Pi; wait for DE SSH plus ordinary service readback, then alignment, exact-Core retry and only then LDPlayer |
| `WO-013DI` | Rehearse signed candidate.16 portal/client rollback in a disposable local fixture | Exact signed tuple, portal projection and client stable-pointer evidence | Manifest/signature/receipt and exact four-repository tuple validate; `1.1.6 -> candidate.16 -> 1.1.6` passes; portal and pointer restore byte-identically; backups/receipts and unrelated-state preservation pass; focused suite `16/16`. Tracked/runtime/public/stable state and devices remain unchanged. `DOD-18/P12-130` stay `I3` | `WO-013DE`, exact signed candidate.16 and retained stable handoff; real runtime pointer/kill rollback with backup, current/Brain readback and health remains required before I4 |
| `WO-013DJ` | Prove the conditional Linux native journald socket, closed fallback and owned-host readback | Current successor client source and owned Raspberry Pi evidence | Client PR 47 merge `6470d76...` adds native socket/fallback tests and an opt-in live probe without changing production behavior. Go/full-client gates pass; exact Linux/ARM64 tests plus sanitized real journal readback pass; temporary state is removed. `OBS-043` advances `I2 -> I3`; candidate.16 and Linux release scope remain unchanged | `WO-005G`, `WO-013AP`, `WO-013CS`, client base `75ba7e7...`; exact signed Ubuntu 24.04 package/lifecycle/retention/rotation proof remains required before I4 |
| `WO-013DK` | Generate the cross-surface copy-authority map and bind it to the active client | Current platform/client successor source and deterministic local contract evidence | Platform `f8a3b33...` extends the existing synchronizer; client PR 48 merge `9b52d6a...` pins copy/governance digests and carries the generated seven-namespace map plus `app.*` baseline. Exact-Core seed/docs and platform `41/41` copy-contract checks pass. `P12-210` advances `I2 -> I3`; candidate, runtime, deploy, legal and publication state do not change | `WO-008A/008F/008H/008I/008J`, current platform owners and active client `main`; keep the read-only generator check in the next exact-candidate preflight |
| `WO-013DL` | Bind candidate.16 Windows setup to a guarded current-host install and idle lifecycle | Exact signed Windows artifact and owner-host evidence | Setup identity, all `8/8` files, LocalSystem service/owner binding, authenticated IPC, SCM restart, uninstall and idle route/DNS restoration pass. Connected network, recovery, SmartScreen interaction and clean Windows 10/11 remain manual | `WO-013DE`, exact candidate.16 setup and runtime manifest; complete connected clean-VM proof |
| `WO-013DM` | Retain Datalix payment restoration without accepting an untrusted host-identity change | Owned-provider identity boundary evidence | Owner payment attestation is retained, but strict SSH stops on a changed host key and leaves trusted state unchanged. DE alignment and exact candidate AWG retries remain not run | `WO-013DH`, trusted provider console; compare the server Ed25519 fingerprint out of band before any service action |
| `WO-013DN` | Build and verify the candidate.16 RU probe bundle and run an owned-Pi no-mutation install PLAN | Exact candidate platform and owned-Pi environment evidence | The ten-member bundle reproduces and PLAN passes. The Pi has four source mismatches, no runtime material/archive, inactive timers and a failed retained runner state; no install, run, upload, heartbeat or admin readback occurs | `WO-013DE`, RU probe handoff and separately authorized APPLY/runtime material |
| `WO-013DO` | Bind exact candidate.16 ARM64 install identity and generate Gate F | Exact signed Android install and release-decision evidence | Physical installed bytes match signed `1.2.0+4049` without app launch or screen control. Gate F validates signature/keyring/source tuple plus `19/19` pointers and returns `NO_GO 2/17/2` with zero validation errors. Physical runtime and remaining external/manual rows stay non-PASS; Gate G remains unauthorized | `WO-013DE`–`WO-013DN`, candidate.16 signed outputs and POKROV-app PR 50; resolve AWG egress and complete physical/Windows/origin/provider/Operator/legal/performance/no-open-P0 rows before another Gate F |
| `WO-013DP` | Verify Smart-DNS reachability from Android devices without launching POKROV or taking UI control | Background Android OS and LDPlayer direct-DoH evidence | Both devices resolve the public hostname. LDPlayer trusted DoH returns bounded `REFUSED` outside policy and `NOERROR` for ChatGPT/Gemini/Xbox; the phone lacks a non-UI DoH tool. No app/VPN/device setting changes. `SMARTDNS-01` stays `I3`; candidate/client/session/Gate F credit does not transfer | `WO-013DG`, returned physical phone and LDPlayer; run client-integrated and physical DoH/session/leak/lifecycle proof only with a non-UI-safe harness |
| `WO-013DQ` | Add candidate.16 current-origin API performance and exact STOP-SHIP/P0 background evidence without taking UI control | Exact source, current-origin, Android/Pi and provider-boundary evidence | Source-bound health/catalog pass 50-sample p95 budgets; exact STOP-SHIP regressions pass `7/7`, with zero queried open P0 issues. Hosted/manual controls and aggregate attestation remain non-PASS. Android/Pi Smart-DNS reachability stays bounded; Windows has a resolver-context failure only. Datalix identity remains blocked without accepting a key. No index or Gate F change | `WO-013DM`, `WO-013DO`, `WO-013DP`, exact candidate.16 source tuple; confirm DE identity out of band, then complete authenticated origins and device gates |
| `WO-013DR` | Bind candidate.16 distribution bytes and run a bounded static payload privacy scan without taking UI control | Exact signed Android/Windows artifact evidence | All `6/6` artifact sizes/hashes pass. Five Android archives and the manifest-declared Windows payload tree have zero definite private-material, populated-credential or high-confidence connection-URI findings. Scheme/parser broad matches are source-accounted false positives. The current extractor cannot independently unpack the Windows loader, so the exact installer raw scan plus `8/8` hashed required files remain the explicit evidence ceiling. No index or Gate F count changes | `WO-013DO`, `WO-013DQ`, exact candidate.16 artifacts and manifests; retain physical/connected runtime and aggregate attestation before I4 |
| `WO-013DS` | Bind the installed candidate.16 x86_64 bytes and retain a background LDPlayer idle/API baseline | Exact Android emulator and performance evidence | Installed APK hash matches the signed artifact. A stable 56.35-second no-VPN idle sample records RSS/PSS/threads/CPU; separate persistent HTTP/1.1 health/catalog runs pass 50-sample p95 budgets at 73.985/97.756 ms. No Android resource threshold exists, the app was not launched, and no client session is claimed. No index or Gate F count changes | `WO-013DQ`, `WO-013DR`, exact candidate.16 x86_64 install; retain cold-start/connect and comparable physical Android/Windows evidence before I4 |
| `WO-013DT` | Refresh candidate.16 Brain-origin source, readiness and enabled delivery without mutation | Exact Brain source/runtime and delivery evidence | Exact selected source passes `197/197`, readiness passes `23/23` with `5/5` stable subscription samples, and enabled delivery repeats `6/7` across three samples. Only `de` is non-open; the other six, including `ru_spb`, pass throughout. Brain-origin remains non-PASS and Gate F is not regenerated | `WO-013DM`, `WO-013DO`, exact candidate.16 platform source and owner-trusted Brain access; confirm Datalix identity out of band, restore `de`, then repeat `7/7` |
| `WO-013DU` | Restore one DE VM on both provider addresses and expose them as two VPN choices without duplicating node truth | Owner-authorized current-runtime deployment, authenticated transport and subscription evidence | PR 149 hosted CI passes and merged platform `a68280f...` deploys with `197/197` readback. Both DNS names pass TCP and authenticated Reality egress; four live subscription formats expose two labeled choices with one DE user mapping. AWG2/AWG3.1 server listeners are active. This is post-candidate.16 and requires a successor signed candidate | `WO-013DT`, owner-restored provider access and DNS; build and bind a successor candidate, then repeat exact Android/Windows/AWG/origin and Gate F evidence |
| `WO-013DV` | Reject candidate.17, bind the corrected Windows package into signed candidate.18 and retain exact hosted replay | Cross-repository signed candidate, isolated Windows VM and hosted evidence | Candidate.18 binds platform `d6898e6...`, client `820ca10...`, Core `cd8f0f4...`, six artifacts, a 352-component SBOM, provenance and an 11-file Windows manifest. Signer/receipt and exact source replay pass. Windows clean-app-state install/service/IPC/restart/uninstall plus public-1.1.6 migration pass. LDPlayer network evidence is excluded; physical Android, connected Windows, origins and Gate F remain open. No index changes | `WO-013DU`, client PR 53, release-index PRs 37/38 and exact candidate.18 bytes; run candidate.18 physical and connected-network gates before Gate F |
| `WO-013DW` | Rehearse signed candidate.18 portal/client rollback in a disposable local fixture | Exact signed tuple, portal projection and client stable-pointer evidence | Manifest/signature/receipt and exact four-repository tuple validate; `1.1.6 -> candidate.18 -> 1.1.6` passes; portal and pointer restore byte-identically; backups/receipts and unrelated-state preservation pass; focused suite `16/16`. Tracked/runtime/public/stable state, devices and the Windows VM remain unchanged. `DOD-18/P12-130` stay `I3` | `WO-013DV`, exact signed candidate.18 and retained stable handoff; real runtime pointer/kill rollback with backup, current/Brain readback and health remains required before I4 |
| `WO-013DX` | Refresh exact candidate.18 Brain-origin source, readiness and enabled delivery without mutation | Exact platform source and redacted Brain runtime evidence | Exact selected source passes `197/197`; readiness retry passes `23/23` with `5/5` stable subscription samples; all seven enabled nodes are open in three delivery samples. The initial one-check management timeout is retained. Brain-origin passes, while current authenticated client and RU-origin remain open. No index changes | `WO-013DV`, trusted read-only Brain access and exact platform source; complete current authenticated and RU-origin plus device/runtime gates before Gate F |
| `WO-013DY` | Refresh candidate.18 current-origin API budgets and exact STOP-SHIP/P0 controls without mutation | Exact source, source-bound current-origin and hosted-control evidence | Health/catalog pass 50-sample p95 budgets at `43.5854/43.7925 ms`; permanent regressions pass `7/7`; owner-solo PR controls pass `3/3`; queried open P0 counts are zero. Aggregate remains `BLOCKED` on two access-blocked controls, one accepted unprotected branch and one manual live gate. No index changes | `WO-013DV`, exact candidate.18 source tuple and controlled physical-Ethernet method; complete authenticated client, live privacy/false-green and manual gates before Gate F |
| `WO-013DZ` | Reject candidate.18 and bind the corrected Windows client into signed private candidate.19 | Exact signed supply, hosted replay, isolated Windows/rollback, named-origin and LDPlayer install evidence | Candidate.18 is immutable `NO_GO`. Candidate.19 binds platform `d6898e6...`, client `10f5516...`, Core `cd8f0f4...` and signed release-index `43fc20f...`; six artifacts, signer/receipt, hosted replay, Windows foundation, local rollback and bounded named-origin slices pass. Two transient Brain management samples remain non-PASS before three final `7/7` samples. LDPlayer network is excluded. Physical Android, connected Windows, authenticated current/RU origins and aggregate manual gates remain open; Gate F/G and publication remain unauthorized | `WO-013DV`–`WO-013DY`, client PR 54, release-index PRs 39/40 and exact candidate.19 bytes; complete physical Wi-Fi/Beeline and connected Windows before another Gate F |
| `WO-013EA` | Reject candidate.19, bind the service-owned rule-set correction into signed private candidate.20 and close the Windows 11 default path | Exact signed supply, isolated Windows 11 TUN/DNS/egress/rollback and migration evidence | Candidate.19 is immutable `NO_GO`. Candidate.20 binds platform `d6898e6...`, client `8ab9815...`, Core `cd8f0f4...` and signed release-index `61ad0b0...`; six artifacts, signer/receipt, exact replay and Windows default path pass. `WIN-003/DOD-04` reach `I4`. Candidate20 LDPlayer/physical Android, Windows 10/non-default/recovery, named origins, candidate rollback and aggregate manual gates remain open; Gate F/G and publication remain unauthorized | `WO-013DZ`, client PR 55, release-index PRs 41/42, hosted replay 33511744299 and exact candidate.20 bytes; complete Android, remaining Windows, origin/rollback and aggregate gates before another Gate F |
| `WO-013EB` | Repeat candidate.20 permanent STOP-SHIP, P0 and source privacy controls without touching host networking or device runtime | Exact platform/client/Core source and hosted-policy evidence | Permanent regressions pass `7/7`, owner-solo PR controls `3/3`, GitHub open P0 label/title `0/0`, platform privacy `75/75`, release logging `145 + 4`, observability `29/29` and support bundle `15/15`. The verifier remains `BLOCKED` on two inaccessible branch policies, one accepted unprotected branch and its generic manual input; final live aggregate remains missing. `DOD-01` reaches `I3`; no Gate F/G or promotion is generated | `WO-013EA`, exact candidate.20 source tuple and read-only GitHub access; complete physical Android, remaining Windows and final live aggregate before I4/Gate F |
| `WO-013EC` | Bind candidate.20 distribution bytes and run bounded static artifact privacy without touching host networking or device runtime | Exact signed Android/Windows bytes plus manifest-bound Windows staging evidence | All `6/6` artifact sizes/hashes pass. Five streamed Android archives expose `1895` entries with zero definite findings. Twelve loose matches collapse to one ABI-duplicated Flutter runtime/symbol fingerprint and zero strict provider-token shapes. Raw installer plus `11/11` required files and all `302` staged files also return zero definite findings. No row advances and Gate F remains not run | `WO-013EA`, `WO-013EB`, exact candidate.20 artifacts and preserved clean client build tree; complete device/runtime, deployed ingest and final aggregate evidence before I4/Gate F |
| `WO-013ED` | Replay candidate.20 source-owned Gates A–E without touching host networking or device runtime | Exact platform/client/Core source plus declared Node 22 local-quality evidence | Gate B passes `70/70 + 111/111`; Gate D passes `196/196 + 12` and `25/25`; full local quality passes `15/15`, including client `413/413`, cabinet `69/69` and static performance `9/9`. Fail-first dependency/browser reports and noncanonical Node 24 PASS remain retained. All five gates stay `BLOCKED` with zero source failures; no level advances and Gate F remains not run | `WO-013EA`–`WO-013EC`, exact candidate.20 source worktrees and local fixture/browser execution; complete physical Android, remaining Windows, live provider/Operator/origin/performance/rollback before Gate F |
| `WO-013EE` | Reconcile active low-level ledger instructions and preflight candidate.20 PB-14 without using host networking or device runtime | Exact candidate.20 signed supply plus WO-013EA–ED evidence | Thirty rows receive current evidence/instructions, stale pre-20 next-actions fall `23 -> 0`, no level changes. PB-14 reaches the physical boundary and fails closed because exact installed Android identity is absent; focused PB-14/rollback tests pass `16/16`. No incident, rollback or Gate F is staged | Install and hash-bind the exact candidate.20 ARM64 artifact on physical Android, then run guarded PB-14/candidate rollback and remaining live/manual gates |
| `WO-013EF` | Add bounded Linux peer-credential/polkit-D-Bus authorization observability without using host networking or device runtime | Client main source, local tests and hosted Ubuntu build/test evidence | PR 57 merges as client main `eceb130...`; every mutation emits one validated closed authorization event and request/auth/write deadlines are separated. PR Ubuntu Linux step passes. `DOD-06` and `OBS-044` stay `I2`; no desktop-session readback, signed package, runtime promotion or candidate.20 change is claimed | Retain clean Ubuntu desktop allow/deny/dismiss/missing-agent/timeout D-Bus and journald readback, then package and repeat before I3/I4 |
| `WO-013EG` | Implement the dormant typed Linux NetworkManager/resolved/nft transaction and reverse fault recovery without enabling product traffic | Client main source, focused fault tests, full local client gate and hosted Ubuntu build/test evidence | PR 58 source `9fa8c76...` merges as `7ae2427...`; fixed system-D-Bus checkpoint, per-link resolved settings, one atomic owned nft table and reverse rollback/retry are source-proven. `connect` remains unavailable, candidate.20 is unchanged and `OBS-045` stays `I2` | Bind the exact Core/TUN plan and durable recovery, then retain clean Ubuntu native D-Bus/journald, route/DNS/nft partial-fault and exact restoration proof before I3/I4 |
| `WO-013EH` | Reject candidate.20 after its exact service-restart recovery failure, assemble private candidate.21 and replace the current Windows 11 default runtime proof | Six exact build-4050 artifacts, private creation receipt and isolated Windows 11 upgrade/default runtime evidence | Candidate.20 is immutable `NO_GO`. Candidate.21 binds platform `e2608130...`, client `1e164586...` and Core `cd8f0f4...`; upgrade-time startup recovery, `11/11` files, ordinary UI/LocalSystem service, default Germany TUN/route/DNS/DE egress and exact RU baseline restoration pass. No level changes; Gate F remains not run | Superseded for signed supply by WO-013EI; retain this exact Windows boundary and complete fresh in-place recovery plus remaining device/runtime gates |
| `WO-013EI` | Bind the exact candidate.21 bytes to strict-v2 handoff, refreshed SBOM/provenance and a trusted private release-index manifest | Exact four-repository tuple, offline supply validation, GitHub input/signer/receipt chain and retained Actions-only signed output | Handoff `07e0009c...`, SBOM `c01234bf...`, provenance `b6e63ae0...`, manifest/signature/receipt `ce0b8586...` / `ef474e6e...` / `aaa027cc...` validate. Signer run `33586752995`, input PR 43 and receipt PR 44 pass. `promotion_authorized=false`; no public asset, tag, Store object or stable pointer exists. No level changes; Gate F remains not run | Complete exact Android/AWG/Smart-DNS, fresh Windows lifecycle, named-origin, rollback, provider/Operator/legal/performance and aggregate gates before Gate F |
| `WO-013EJ` | Bind the live default-off Smart DNS contract to exact signed candidate.21 source and repeat the direct Windows 11 policy path | Deterministic candidate-source bundle, live backend/frontend read-only PLANs, authoritative DNS and isolated Windows VM DoH/TLS evidence | Two exact-source builds match; nine runtime entries match the live bundle, while only source-bound manifest/README differ. Live service/route/receipt readback passes with zero mutation, and the signed-candidate Windows VM direct contract returns expected `NOERROR`/`NODATA`/`REFUSED` plus trusted ChatGPT/Gemini/Xbox TLS/HTTP. `SMARTDNS-01` stays `I3`; Gate F stays not run | Run exact candidate.21 in-app/physical authenticated-session, attribution, leak/privacy/load/lifecycle and fresh named-origin aggregate matrices |
| `WO-013EK` | Run exact candidate.21 Core AWG2/AWG3.1 from the owned direct-RU fixed-network Raspberry Pi | Signed candidate tuple, clean exact-Core snapshot, digest-bound Linux ARM64 binaries and secret-safe RU-Pi runtime evidence | AWG2 and AWG3.1 both pass outer exchange, tunneled TCP, verified TLS and authenticated egress; temporary roots/executables return to zero and no server or client setting changes. `AWG-10` stays `I2` because packaged Android/Windows and distinct mobile/fixed multi-ASN evidence remain open; Gate F stays not run | Run exact candidate.21 packaged Android and isolated-Windows AWG selection, then physical Wi-Fi/Beeline and additional named RU-origin ASN canaries |
| `WO-013EL` | Refresh exact candidate.21 current-public and Brain read-only origin evidence | Exact clean source tuple, Brain source/readiness/delivery reports, controlled current-origin API budgets and current STOP-SHIP/P0 queries | Brain `197/197`, readiness `23/23`, subscriptions `5/5` and delivery `7/7 x3` pass; current health/catalog p95 `35.6952/41.3740 ms` pass. Permanent regressions and solo controls pass, but aggregate STOP-SHIP remains blocked and authenticated-client/general-RU evidence remains open. No level changes; Gate F stays not run | Complete authenticated current-client, general RU-origin, physical multi-ASN, provider/Operator/legal/rollback/performance and final live aggregate gates |
| `WO-013EM` | Rehearse signed candidate.21 portal/client rollback in a disposable local fixture | Exact signed tuple, portal projection and client stable-pointer evidence | Manifest/signature/receipt and exact four-repository tuple validate; `1.1.6 -> candidate.21 -> 1.1.6` passes; portal and pointer restore byte-identically; backups/receipts and unrelated-state preservation pass; focused suite `16/16`. Tracked/runtime/public/stable state, devices and the Windows VM remain unchanged. `DOD-18/P12-130` stay `I3` | Run the separately guarded runtime pointer/kill rollback with backup, current/Brain readback and post-rollback health before I4 |
| `WO-013EN` | Replay candidate.21 source-owned Gates A–E and audit the materialized frontend dependency trees without runtime mutation | Exact signed platform/client/Core/release-index tuple plus declared Node 22 local-quality and dependency-audit evidence | Gate B passes `70/70 + 111/111`; Gate D passes `196/196 + 12` and `25/25`; full local quality passes `15/15`, including client `413/413`, cabinet `69/69` and static performance `9/9`. Webapp audit is zero; adminapp/marketing each retain one high finding from the same transitive development-only `browserslist` `4.28.4` path. No distributed-runtime exposure is observed, but both active locks require a patch. All five gates stay blocked; no level changes and Gate F remains not run | `WO-013EI`–`WO-013EM`, exact candidate.21 clean source worktrees and local fixture/browser execution; patch active locks, then complete physical Android, remaining Windows, live provider/Operator/origin/performance/rollback before Gate F |
| `WO-013EO` | Refresh the two active frontend development locks after the candidate.21 audit without rewriting the candidate | Adminapp/marketing package locks plus declared Node 22 install/audit/lint/build evidence | Both locks resolve `browserslist` `4.28.8`; package manifests and production dependencies stay unchanged. Fresh audits report zero findings, both lint/builds pass, admin API/SDK stays `75/75`, marketing export repair produces 30 copies, and focused platform tests pass `28/28`. Candidate.21 remains immutable and a successor candidate is required for release credit. No levels change | `WO-013EN`, exact active-line locks and local Node `22.14.0`; complete candidate.21 runtime gates or build/sign a successor only when another source/runtime change requires replacement |
| `WO-013EP` | Repeat bounded static artifact privacy against all six signed candidate.21 distribution bytes | Exact signed artifacts, streamed Android archives, raw Windows installer and manifest-bound exact-client staging tree | `6/6` size/SHA bindings pass; five Android archives expose `1895` entries with zero definite findings; 12 loose occurrences collapse to one ABI-duplicated fingerprint and zero strict provider-shape matches. Windows installer plus `11/11` required and all 302 staged files return zero definite findings. No matched values or raw paths are retained. Rows keep their levels and Gate F remains not run | `WO-013EI`, exact candidate.21 artifacts and clean client staging tree; complete installed Android/Windows, deployed ingest and final live privacy proof before I4/Gate F |
| `WO-013EQ` | Replace candidate.20 source-privacy evidence with exact candidate.21 without runtime or network mutation | Exact clean platform/client/Core source plus read-only hosted-control evidence | Platform privacy passes `75/75`, release logging `145 + 4`, observability runtime `29/29` and support bundle `15/15`. STOP-SHIP retains `7/7`, solo controls `3/3` and P0 queries `0/0`; aggregate stays `BLOCKED` on branch-policy/manual-live controls. Rows keep their levels and Gate F remains not run | `WO-013EL`, `WO-013EP` and exact candidate.21 source worktrees; complete installed-device journals/bundles, deployed ingest and final live privacy proof before I4/Gate F |
| `WO-013ER` | Authorize the exact signed candidate.21 platform source in the fail-closed RU bundle builder and prove a no-mutation owned-Pi install PLAN | Signed candidate.21 source, clean exact-source worktree, deterministic bundle and direct-RU Raspberry Pi 4 preflight | Builder focused suite passes `11/11`; two 10-member bundles are byte-identical at SHA-256 `56218e1...`; verify, local PLAN and remote PLAN pass with no runtime material and `mutation_performed=false`. Environment remains incomplete and general RU-origin stays `MANUAL_OWNER_TEST`; rows keep their levels and Gate F remains not run | `WO-013EI`, exact candidate.21 platform source and owned-Pi preflight; prepare receipt-bound runtime material, run separately confirmed APPLY, then runner/uploader/ingest/archive/heartbeat/admin readback |
| `WO-013ES` | Prove that the existing Brain RU-auth registry and managed drop-in exactly match the candidate.21 RU probe contract without exposing the credential | Tightened read-only preflight plus current Brain runtime | Focused tests pass `10/10`; registry, drop-in, active `portal-api` environment and exact one-key metadata all match. No secret or hash is returned and `mutation_performed=false`. Key rotation is not required by current evidence; transfer, Pi APPLY and live readback remain not run. Rows keep their levels and Gate F remains not run | `WO-013ER` and current Brain auth state; separately authorize guarded existing-key transfer, then validate private runtime material and execute the Pi/manual RU sequence |
| `WO-013ET` | Generate the exact candidate.21 Gate F decision without making physical install a prerequisite for signed-candidate validation | Immutable manifest/signature/receipt/keyring, exact four-source tuple and 12 digest-bound upstream records | Signed identity and all `19/19` evidence pointers validate. Gate F is `BLOCKED 4 PASS / 15 non-PASS / 0 FAIL` with zero validation errors; `REL_GATE/GATE-F` stays `I3`, distribution is unchanged and Gate G remains unauthorized | Close the 15 non-PASS exact-candidate rows, then regenerate Gate F; public/Store/stable promotion still requires separate authorization |
| `WO-013EU` | Bind exact candidate.21 source revisions to completed hosted checks and refresh Gate F without rerunning workflows | Ten exact-SHA GitHub Actions job conclusions plus 13 digest-bound upstream records | All `10/10` required hosted jobs are `success`; signed identity and all `19/19` Gate F evidence pointers validate. Gate F is `BLOCKED 5 PASS / 14 non-PASS / 0 FAIL` with zero validation errors. Branch protection and independent review remain separate non-PASS controls; Gate G remains unauthorized | Close the 14 non-PASS exact-candidate rows, then regenerate Gate F; public/Store/stable promotion still requires separate authorization |
| `WO-013EV` | Reject candidate.21 for the exact Windows rejected-session service-availability defect and project build 4051 | Exact candidate.21 source, corrected native regression and hosted client CI | Candidate.21 becomes immutable `NO_GO`; corrected client source merges and passes hosted CI. Candidate.22 is still pre-candidate at this checkpoint | Build and bind candidate.22 without rewriting candidate.21 history |
| `WO-013EW` | Assemble and sign private candidate.22, then prove exact Windows 11 service and reboot recovery | Six exact build-4051 artifacts, strict-v2 supply, signed release-index chain and isolated Windows 11 evidence | Candidate.22 signed supply validates. Rejected/successor IPC, ordinary UI/service, default TUN/DNS/egress restoration, connected service restart and connected reboot pass on exact bytes. Gate F is `NOT_RUN`; no public/stable promotion exists | Prioritize exact Android packaged AWG3.1/AWG2 and in-app Smart DNS, then close remaining candidate.22 Gate F rows |
| `WO-013EX` | Generate candidate.22's first exact Gate F decision | Immutable manifest/signature/receipt/keyring, exact four-source tuple, WO-013EW and 10 attached hosted checks | Signed identity, all `19/19` pointers and all upstream hashes validate. Gate F is `BLOCKED 3 PASS / 16 non-PASS / 0 FAIL` with zero validation errors. Gate G remains unauthorized | Close the 16 non-PASS candidate.22 rows, prioritizing Android/AWG/Smart DNS, then regenerate Gate F |
| `WO-013EY` | Prove candidate.22's Windows in-app Smart-DNS split path | Exact installed Windows hashes, headless UI selection/relaunch, connected system DNS/HTTPS controls and clean restore | Custom direct DoH, external Smart DNS and AI/Games persist; allowlisted DNS/TLS uses the owned proxy while the outside control does not, and general traffic uses the selected Germany exit. Authenticated sessions and physical Android stay open; one post-wake Home refresh observation remains manual. Gate F is unchanged | Windows packaged AWG is superseded by WO-013EZ; run physical Wi-Fi/Beeline Smart DNS and reproduce the Home refresh with normal physical input before final false-green attestation |
| `WO-013EZ` | Prove candidate.22 packaged Windows AWG3.1 and AWG2, then restore the default cohort | Exact installed Windows hashes, guarded owner-lab binds, profile revisions, Core/TUN/DNS/egress controls and cleanup readback | Both profiles separately reach connected through the packaged Windows service/Core and the DE exit; guarded cleanup resolves the ordinary fallback and final disconnect restores DHCP DNS with no TUN or crash dump. Strict DE server packet capture is blocked by missing local host trust and is not claimed. Gate F is unchanged | Run exact packaged Android AWG3.1/AWG2 over physical Wi-Fi/Beeline, reconcile DE host trust, then complete UDP/IPv6/MTU/lifecycle/endurance matrices |
| `WO-013FA` | Reject candidate.22 after connected uninstall and prove the bounded build-4052 correction before candidate creation | Exact candidate.22 install/uninstall state, residual-file inventory, successor packaging contracts and isolated Windows 11 pre-candidate VM replay | Candidate.22 removes service/TUN and restores RU egress but leaves the UI and 13 loaded files, so it is immutable `NO_GO`. Exact local build-4052 setup `9aa6b0fd...` closes the process/service/file/directory/registry cleanup in the VM; this is pre-candidate proof only. Gate F is retained at `3/16/0` and not regenerated | Superseded by WO-013FB candidate.23 rejection and candidate.24 signed supply; retain as immutable predecessor evidence |
| `WO-013FB` | Reject candidate.23 for Windows pipe contention and bind corrected candidate.24 signed supply | Fresh exact candidate.23 headless 32-client probe plus candidate.24 artifacts, strict-v2 supply, hosted client CI and release-index signer/receipt | Candidate.23 remains `Running` but accepts `9/32` simultaneous clients and is immutable `NO_GO`. Candidate.24 build `4053` adds bounded retries; six artifacts, `11/11` Windows runtime files, SBOM/provenance/handoff, manifest/signature/receipt and native CTest `8/8` pass. Headless VM file identity passes; exact install is `NOT_RUN` because the guest token is non-elevated. No level changes or public promotion | Install and hash-bind exact candidate.24 through a non-interactive elevated VM path, then run Windows contention/lifecycle/uninstall plus Android AWG/Smart-DNS matrices |
| `WO-013FC` | Generate candidate.24's first exact Gate F decision | Immutable manifest/signature/receipt/keyring, exact four-source tuple, WO-013FB and 10 attached hosted checks | Signed identity, all `19/19` pointers and upstream hashes validate. Gate F is `BLOCKED 3 PASS / 16 non-PASS / 0 FAIL` with zero validation errors. Gate G remains unauthorized | Close the 16 non-PASS candidate.24 rows, prioritizing installed Windows/Android AWG/Smart DNS and origins, then regenerate Gate F |
| `WO-013FD` | Refresh candidate.24 current-public and Brain read-only origin evidence | Exact signed source tuple, Brain semantic/readiness/subscription/delivery probes, current-public health/catalog budgets and current STOP-SHIP/P0 queries | Brain `197/197`, readiness `23/23`, subscriptions `5/5` and delivery `7/7 x3` pass; current health/catalog p95 `36.2096/49.9565 ms` pass. Permanent regressions and solo controls pass, but authenticated-client/general-RU/device evidence and final live aggregate remain open. No level changes | Complete authenticated client egress, general RU-origin, physical multi-ASN and remaining live gates without merging the bounded origin contours |
| `WO-013FE` | Replay candidate.24 source-owned Gates A-E and isolated local rollback | Exact signed platform/client/Core/release-index tuple, declared Node 22 local quality, dependency audit and disposable portal/client pointer fixture | Gate B passes `70/70 + 111/111`; Gate D passes `196/196 + 12` and `25/25`; quality passes `15/15`, client `413/413`, cabinet `69/69` and performance `9/9`. The `1.1.6 -> candidate.24 -> 1.1.6` fixture restores byte-identically and focused rollback tests pass `16/16`. One moderate dev-only webapp lock finding remains; runtime rollback and live/device boundaries stay open | Patch the active development lock, then complete installed Windows/Android, provider/Operator/origin/performance and guarded runtime rollback evidence |
| `WO-013FF` | Regenerate candidate.24 Gate F with current/Brain origin evidence | Immutable signed identity, exact four-source tuple, all `19/19` pointers, WO-013FD/013FE and portable LF-bound JSON evidence | Current-origin and Brain-origin advance to PASS. Gate F is `BLOCKED 5 PASS / 14 non-PASS / 0 FAIL` with zero validation errors; Gate G remains unauthorized | Close the 14 explicit non-PASS candidate.24 rows, then regenerate Gate F; no public/Store/stable promotion before exact GO |
| `WO-013FG` | Patch the successor webapp development lock without rewriting candidate.24 | Lock-only `@humanfs/node 0.16.8` refresh, exact Node 22/npm 10 audits and complete local-quality replay | Webapp/adminapp/marketing audits are zero; webapp lint/build, cabinet `69/69`, client `413/413`, full quality `15/15` and static performance `9/9` pass. Status is `PASS_PRE_CANDIDATE_LOCAL`; candidate.24 stays immutable at Gate F `BLOCKED 5/14/0` and no levels change | Merge through hosted checks, then build/sign a successor candidate before assigning release credit or repeating exact installed-device gates |
| `WO-013FH` | Bind the merged development-lock correction into signed private candidate.25 and regenerate Gate F | Exact four-source tuple, six-artifact strict-v2 supply, signer receipt, ten hosted jobs, headless CLI rehearsal, exact guest file identity and fresh current/Brain read-only origins | Signed identity and all `19/19` pointers validate. Candidate.25 Gate F is `BLOCKED 5 PASS / 14 non-PASS / 0 FAIL`; the exact installer hash matches in the VM but installation is `NOT_RUN`. No public/stable promotion or level change | Complete candidate.25 installed Windows/Android, authenticated/general-RU, provider/Operator/legal, runtime rollback, comparable performance and final live rows before regenerating Gate F |
| `WO-013FI` | Refresh candidate.25 exact-Core AWG3.1 and AWG2 evidence from the owned direct-RU Pi | Candidate.25 manifest/Core identity, candidate-matching guarded runner, ARM64 binary hashes and secret-free cleaned execution records | AWG3.1 and AWG2 both pass authenticated egress from one direct RU fixed-network path; runtime/server/client settings remain unchanged and temporary state is removed. `AWG-10` and Phase 10 keep their levels; Gate F remains `BLOCKED 5/14/0` | Run exact packaged Android and Windows AWG3.1/AWG2, physical Wi-Fi/Beeline and additional named fixed/mobile ASN canaries before advancing AWG-10 or regenerating Gate F |
| `WO-013FJ` | Rebuild the Windows release path headlessly and exercise immutable candidate.25 on a clean hosted Windows machine | Exact private setup/signature/source tuple, private prerelease carrier, ephemeral Windows Server 2025 run and sanitized CLI/hosted evidence | Fresh CLI build passes without candidate credit. Exact install, `11/11` files, LocalSystem service, authenticated IPC, SCM restart, clean uninstall and idle network restoration pass. Connected traffic/DNS/egress/recovery/connected-uninstall/SmartScreen remain manual; Gate F stays `BLOCKED 5/14/0` | Run exact connected Windows default/AWG3.1/AWG2/Smart-DNS, DNS/leak/egress, reboot and connected-uninstall matrices on a suitable isolated device without using the owner's active desktop |
| `WO-013FK` | Correct the Debug-only Windows service integration registration exposed by the fresh CLI rehearsal | CMake command authority, successor client source, fresh Debug/Release generations and executable CTest matrices | Debug enumerates and passes `8/8`; Release excludes the Debug-only SCM integration and passes `7/7`. Runtime/package source and candidate.25 bytes do not change. Hosted run executes zero steps and is `BLOCKED_BY_ACCESS` by GitHub Billing/spending limit; Gate F remains `5/14/0` | Keep candidate.25 immutable; restore an approved hosted runner path separately, and continue the exact connected Windows/Android matrices without assigning this test-only correction candidate credit |
| `WO-013FL` | Build the merged CTest successor source entirely by CLI and exercise its exact setup in the isolated Windows 11 VM | Exact client/Core/platform tuple, full client tests, Windows setup/manifest, static scan, Debug/Release JUnit and sanitized upgrade/IPC/reboot evidence | Windows-only candidate.26 precursor passes full build, Debug `8/8`, Release `7/7`, staged and installed `11/11`, ordinary-UI IPC and automatic service recovery after guest reboot. It is not a signed multi-platform candidate; connected runtime is `NOT_RUN`; Gate F remains `5/14/0` | Assemble a new signed all-platform candidate only after deciding to replace candidate.25, then repeat connected Windows and exact Android device matrices on those exact bytes |
| `WO-013FM` | Exercise exact installed candidate.25 TUN/DNS and connected reboot entirely inside the isolated Windows 11 VM | Candidate.25 installed snapshot, authenticated production IPC, secret-free direct-only profile, route/DNS fingerprints and real guest reboot | Exact candidate.25 service/Core passes direct-only TUN, DNS, health, disconnect restoration and connected-reboot restoration. Managed-node/AWG/Smart-DNS/connected-uninstall remain unrun; the initial too-strict post-check is retained and corrected; Gate F stays `5/14/0` | Complete first-run with an owner-approved existing activation code, then run managed default/AWG3.1/AWG2/Smart-DNS and connected-uninstall without creating an unapproved trial |
| `WO-013FN` | Reject the candidate.27 Windows precursor, correct in-place upgrade owner resolution and prove the candidate.28 precursor | Two exact CLI builds, retained candidate.23 VM ancestor, first-pass direct installer logs, manifest identity, native tests, static scan and direct TUN/DNS/reboot evidence | Candidate.27 is `NO_GO_PRECURSOR` after reproducible first-upgrade abort and `8/11` hashes. Client PR 72 merges exact validated existing-owner reuse. Candidate.28 precursor passes full build, native `7/7 + 8/8`, static scan, first-pass `11/11` upgrade, direct TUN/DNS and connected reboot. It is not a candidate; candidate.25 Gate F stays historical at `5/14/0` | Superseded by WO-013FO candidate.29; retain as immutable source-fix and precursor evidence |
| `WO-013FO` | Build and sign exact candidate.29 through CLI, then exercise its bounded Windows path without host input | Six rebuilt artifacts, strict-v2 supply, hosted signer/receipt, exact candidate.28-to-29 VM upgrade, `11/11` identity, ordinary UI, direct TUN/DNS and connected reboot evidence | Candidate.29 is the active private signed supply. Exact CLI, supply and bounded Windows direct checks pass. Gate F is `NOT_RUN`; managed Windows/AWG/Smart-DNS, physical Android, origins, provider/Operator/legal, rollback and final aggregate remain non-PASS. No public promotion exists | Assemble candidate.29's `19/19` Gate F pointers while prioritizing packaged AWG3.1/AWG2 and Smart DNS on exact Windows and physical Wi-Fi/Beeline |
| `WO-013FP` | Assemble candidate.29's first exact Gate F snapshot | Exact signed identity, four-source tuple and all `19/19` evidence pointers | Gate F is `BLOCKED 2 PASS / 17 non-PASS / 0 FAIL` with zero validation errors. No Gate G or public promotion is authorized | Superseded by WO-013FQ current/Brain origin refresh |
| `WO-013FQ` | Refresh candidate.29 current/Brain origin and regenerate Gate F | Source-bound current measurements, exact Brain source/readiness and three enabled-delivery samples | Current origin is blocked by the untouched owner tunnel; Brain origin FAILS because DE times out `3/3`. Gate F is exact `NO_GO 2/17/1` | Restore DE and obtain tunnel-free current-origin evidence, then repeat the remaining exact candidate rows |
| `WO-013FR` | Exercise exact candidate.29 managed Windows egress and independent exact-Core AWG from the direct-RU Pi | Fresh Windows first launch, AWG3.1/AWG2 managed attempts, corrected ordinary provisioning control, safe service probe, exact Core ARM64 runners and cleanup readback | AWG3.1/AWG2 fail `core_egress_probe_failed`; both Pi AWG variants fail `failed_no_outer_response`. The ordinary control is corrected to `pending_sync` before Core: six panel copies exist but zero confirmations survive the slow-peer aggregate timeout. The frozen Gate F stays `NO_GO 2/17/1`, with two AWG-backed FAIL rows equivalent to `2/17/3`; the separate P0 platform defect rejects candidate.29 for replacement | Land the per-node confirmation fix, build a successor, prove fresh ordinary provisioning headlessly, then repeat AWG/Smart DNS and physical Android matrices |
| `WO-013FS` | Build and test signed candidate.30 headlessly, then enforce exact SBOM/provenance candidate binding | Six exact application artifacts, hosted signature/receipt, CI-pinned Core reproducibility, bounded Windows 11 install/TUN/DNS/reboot evidence and strict supply replay | CLI and bounded Windows pass, but SBOM and provenance retain stale candidate/artifact-set bindings. Candidate.30 is immutable `NO_GO`; Gate F is exact `1 PASS / 18 non-PASS / 2 FAIL`. Platform PRs 198 and 199 add the missing fail-closed checks. Physical Android and LDPlayer are `NOT_RUN`; no deploy or public promotion occurs | Regenerate SBOM/provenance/handoff for a newly numbered candidate, validate before signing, obtain a new hosted signature, then repeat exact managed AWG/Smart-DNS and physical Android matrices |
| `WO-013FT` | Create and sign candidate.31 with corrected candidate-bound supply metadata, then regenerate Gate F | Six same-byte application artifacts, fresh SBOM/provenance/handoff, strict supply PASS, hosted Ed25519 signature/receipt, candidate.30 append-only digest correction and all `19/19` Gate F pointers | Candidate.31 is current private signed supply. Strict validation passes `6/6` artifacts and `11/11` Windows files; Gate F is `BLOCKED 2 PASS / 17 non-PASS / 0 FAIL`. ADB sees no device; managed Windows/Android/origin/approval rows remain open. Three zero-step hosted jobs remain `BLOCKED_BY_ACCESS_GITHUB_BILLING`; no deploy or promotion occurs | Run exact candidate.31 managed Windows default/AWG3.1/AWG2/Smart-DNS and Android physical/emulator matrices without host UI takeover, then refresh origins, rollback and remaining Gate F rows |
| `WO-013FU` | Verify candidate.31 same-byte installed Windows identity and corrected local IPC contention in the headless VM | Exact setup/manifest hashes, `11/11` installed files, automatic LocalSystem service, two retained invalid harness attempts and corrected 32-client CLI result | Installed identity and service pass; corrected local IPC passes `32/32`. The noninteractive installer rerun is `NOT_CREDITED`; no managed connection is exercised and Gate F remains `BLOCKED 2/17/0`. Host input and host networking remain untouched; VM ends powered off | Resume exact candidate.31 managed default/AWG3.1/AWG2/Smart-DNS and connected-uninstall checks inside an isolated device, then physical Android when available |
| `WO-013FV` | Refresh exact candidate.31 current/Brain origins and regenerate Gate F | Exact source hash replay, three retained readiness attempts, six delivery samples, read-only owner-route inventory and all `19/19` Gate F pointers | Brain final readiness is `23/23`, subscription is `5/5` and final delivery is `7/7 x3`, but deployed source is `196/197`. Its original no-known-Git-match diagnosis is superseded by WO-013FX; current-origin remains blocked by the untouched owner tunnel. Gate F is exact `NO_GO 2/17/1`; no server or host mutation occurs | Under separate production authorization, reconcile Brain to exact committed source; then rerun exact source/readiness/delivery and use a tunnel-free independent current-origin |
| `WO-013FW` | Repeat exact candidate.31 Core AWG3.1/AWG2 and live Smart DNS from the owned direct-RU Raspberry Pi | Exact Core snapshot/tool identities, bounded owned lab material, ARM64 runners, strict SSH, direct route, temp cleanup and Smart DNS DoH/TLS probe | AWG3.1 and AWG2 pass in order; default-off Smart DNS policy and ChatGPT/Gemini/Xbox TLS pass. No raw material returns and all temp state is removed. This is source-level/live-lab evidence, not packaged client or authenticated-session proof; Gate F remains `NO_GO 2/17/1` | Reconcile Brain source separately, then run packaged candidate.31 AWG/Smart DNS on Android and isolated Windows plus authenticated sessions and multi-ASN coverage |
| `WO-013FX` | Correct candidate.31 Brain file-history diagnosis without rewriting WO-013FV | Two whole-payload hash probes, a 21-version normalized Git scan, exact file hashes/sizes/line counts and Git ancestry | The sole candidate.31 mismatch exactly matches predecessor `1207b63…`; the other `196/197` files match candidate.31. The full predecessor matches only `193/197`, proving a single-file lag rather than a full old or unknown deploy. Gate F stays `NO_GO 2/17/1`; no mutation occurs | Under separate production authorization, deploy exact candidate.31 platform source; then rerun source/readiness/delivery before regenerating Gate F |

## Current evidence

- `BASELINE.json` records repository heads and observed gaps as of 2026-08-21.
- `EXECUTION-LEDGER.csv` is the machine-readable item register; `(plan,id)` is the primary key.
- `EXECUTION-INDEX.md` defines the completion index and aggregate reporting rules.
- `SOURCE-CROSSWALK.md` preserves plan coverage and conflict decisions.
- `WO-013EQ-candidate21-source-privacy.md`
- `evidence/013EQ-candidate21-source-privacy/`
- `WO-013ER-candidate21-ru-bundle-plan.md`
- `evidence/013ER-candidate21-ru-bundle-plan/`
- `WO-013ES-candidate21-ru-auth-contract-plan.md`
- `evidence/013ES-candidate21-ru-auth-contract-plan/`
- `WO-013EU-candidate21-hosted-checks-gate-f.md`
- `evidence/013EU-candidate21-hosted-checks-gate-f/`
- `WO-013EW-candidate22-signed-windows-runtime.md`
- `evidence/013EW-candidate22-signed-windows-runtime/`
- `WO-013EX-candidate22-gate-f-snapshot.md`
- `evidence/013EX-candidate22-gate-f/`
- `WO-013EY-candidate22-windows-smart-dns.md`
- `evidence/013EY-candidate22-windows-smart-dns/`
- `WO-013EZ-candidate22-windows-awg.md`
- `evidence/013EZ-candidate22-windows-awg/`
- `WO-013FA-candidate22-connected-uninstall-no-go.md`
- `evidence/013FA-candidate22-connected-uninstall-no-go/`
- `WO-013FB-candidate23-no-go-candidate24-signed-supply.md`
- `evidence/013FB-candidate23-no-go-candidate24-supply/`
- `WO-013FC-candidate24-gate-f-snapshot.md`
- `evidence/013FC-candidate24-gate-f/`
- `WO-013FD-candidate24-current-brain-origin.md`
- `evidence/013FD-candidate24-current-brain-origin/`
- `WO-013FE-candidate24-source-gates-and-local-rollback.md`
- `evidence/013FE-candidate24-source-gates-and-local-rollback/`
- `WO-013FF-candidate24-gate-f-origin-refresh.md`
- `evidence/013FF-candidate24-gate-f-refresh/`
- `WO-013FG-successor-webapp-development-lock.md`
- `evidence/013FG-successor-webapp-development-lock/`
- `WO-013FH-candidate25-signed-supply-and-gate-f.md`
- `evidence/013FH-candidate25-signed-gate-f/`
- `WO-013FI-candidate25-core-ru-pi-awg-interop.md`
- `evidence/013FI-candidate25-core-ru-pi-awg/`
- `WO-013FJ-candidate25-windows-hosted-clean-host-pass.md`
- `evidence/013FJ-candidate25-windows-hosted-clean-host-pass/`
- `WO-013FK-windows-ctest-configuration-correction.md`
- `evidence/013FK-windows-ctest-configuration-correction/`
- `WO-013FL-candidate26-cli-vm-upgrade.md`
- `evidence/013FL-candidate26-cli-vm/`
- `WO-013FM-candidate25-windows-direct-tun-reboot.md`
- `evidence/013FM-candidate25-windows-direct-tun-reboot/`
- `WO-013FN-windows-upgrade-owner-fix.md`
- `evidence/013FN-windows-upgrade-owner-fix/`
- `WO-013FO-candidate29-cli-vm-signed.md`
- `evidence/013FO-candidate29-cli-vm-signed/`
- `WO-013FP-candidate29-gate-f.md`
- `evidence/013FP-candidate29-gate-f/`
- `WO-013FQ-candidate29-current-brain-origin-no-go.md`
- `evidence/013FQ-candidate29-origin-gate-f/`
- `WO-013FR-candidate29-managed-egress-no-go.md`
- `evidence/013FR-candidate29-managed-egress/`
- `WO-013FS-candidate30-provenance-no-go.md`
- `evidence/013FS-candidate30-provenance-no-go/`
- `WO-013FT-candidate31-corrected-supply-gate-f.md`
- `evidence/013FT-candidate31-corrected-supply-gate-f/`
- `WO-013FU-candidate31-headless-windows-cli.md`
- `evidence/013FU-candidate31-headless-windows-cli/`
- `WO-013FV-candidate31-origin-no-go.md`
- `evidence/013FV-candidate31-origin-no-go/`
- `WO-013FW-candidate31-ru-pi-awg-dns.md`
- `evidence/013FW-candidate31-ru-pi-awg-dns/`
- `WO-013FX-candidate31-brain-predecessor-diagnosis.md`
- `evidence/013FX-candidate31-brain-predecessor-diagnosis/`
- `WO-013EP-candidate21-static-artifact-privacy.md`
- `evidence/013EP-candidate21-static-artifact-privacy/`
- `WO-013EO-frontend-build-lock-refresh.md`
- `evidence/013EO-frontend-build-lock-refresh/`
- `WO-013EN-candidate21-gates-a-e-offline-replay.md`
- `evidence/013EN-candidate21-gates-a-e/`
- `WO-013EM-candidate21-local-rollback.md`
- `evidence/013EM-candidate21-local-rollback/`
- `WO-013EL-candidate21-current-brain-origin.md`
- `evidence/013EL-candidate21-current-brain-origin/`
- `WO-013EK-candidate21-core-ru-pi-awg-interop.md`
- `evidence/013EK-candidate21-core-ru-pi-awg/`
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
- `WO-013CW-candidate11-ldplayer-awg-runtime-and-quarantine-fix.md`
- `evidence/013CW-candidate11-ldplayer-awg-runtime/`
- `WO-013CX-candidate13-signing-and-ldplayer-lifecycle.md`
- `evidence/013CX-candidate13-signing-and-ldplayer-lifecycle/`
- `WO-013CY-candidate13-final-promotion-audit.md`
- `evidence/013CY-candidate13-final-promotion-audit/`
- `WO-013CZ-candidate13-local-rollback.md`
- `evidence/013CZ-candidate13-local-rollback/`
- `WO-013DA-candidate13-origin-and-windows-preflight.md`
- `evidence/013DA-candidate13-origin-windows-preflight/`
- `WO-013DB-candidate13-smart-dns-readiness.md`
- `evidence/013DB-candidate13-smart-dns-readiness/`
- `WO-013DC-release-dependency-refresh.md`
- `evidence/013DC-release-dependency-refresh/`
- `WO-013DD-candidate14-signed-local-quality-and-ldplayer.md`
- `evidence/013DD-candidate14-signed-local-quality-and-ldplayer/`
- `WO-013DE-candidate16-managed-profile-readiness-signing-local-quality.md`
- `evidence/013DE-candidate16-managed-profile-readiness-signing-local-quality/`
- `WO-013DF-candidate16-awg-ldplayer.md`
- `evidence/013DF-candidate16-awg-ldplayer/`
- `WO-013DG-smart-dns-it-live-and-rollback.md`
- `evidence/013DG-smart-dns-it-live-and-rollback/`
- `WO-013DH-candidate16-de-provider-outage.md`
- `evidence/013DH-candidate16-de-provider-outage/`
- `WO-013DI-candidate16-local-rollback.md`
- `evidence/013DI-candidate16-local-rollback/`
- `WO-013DJ-linux-journald-native-proof.md`
- `evidence/013DJ-linux-journald-native-proof/`
- `WO-013DK-generated-copy-contract-documentation.md`
- `evidence/013DK-generated-copy-contract/`
- `WO-013DL-candidate16-windows-current-host.md`
- `evidence/013DL-candidate16-windows-current-host/`
- `WO-013DM-candidate16-de-host-identity.md`
- `evidence/013DM-candidate16-de-host-identity/`
- `WO-013DN-candidate16-ru-probe-plan.md`
- `evidence/013DN-candidate16-ru-probe-plan/`
- `WO-013DO-candidate16-physical-install-and-gate-f.md`
- `evidence/013DO-candidate16-physical-gate-f/`
- `WO-013DP-candidate16-background-android-dns.md`
- `evidence/013DP-candidate16-background-android-dns/`
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
the current exact candidate reaches Gate F `GO` and the owner separately authorizes
Gate G. The build-4046 external Smart DNS client path remains a default-off lab
until a compatible resolver and live access/leak/rollback evidence exist.
Windows SmartScreen remains the owner-approved unsigned direct-beta
limitation.

## Current next action — assemble a successor after the Windows upgrade fix

WO-013FH is the exact private signed-supply and Gate F authority for
candidate.25. It incorporates the WO-013FG development-lock correction, binds
the exact four-source tuple and validates all `19/19` pointers at
`BLOCKED 5/14/0`; signed supply, release docs, hosted checks, current-origin
and Brain-origin pass while the other 14 rows remain non-PASS. Candidate.24
and earlier decisions remain immutable predecessor history.

WO-013FI freshly proves the same candidate.25 Core's AWG3.1 and AWG2
interoperability from one direct RU fixed-network Pi path. This narrows the
transport uncertainty but does not close packaged-client, mobile/multi-ASN or
general RU-origin rows.

WO-013FJ now proves the exact candidate.25 setup on an ephemeral hosted Windows
machine through machine install, `11/11` files, LocalSystem service,
authenticated IPC, SCM restart, clean uninstall and idle network restoration.
Its separate CLI rebuild is rehearsal-only. Gate F is unchanged because the
connected `windows_live_network` matrix remains open.

WO-013FK corrects the resulting Debug-only CTest registration issue in
successor client source and passes fresh local Debug `8/8` plus Release `7/7`.
It changes no runtime/package source and grants candidate.25 no credit. Its
hosted job is `BLOCKED_BY_ACCESS` by the GitHub account limit with zero steps.

WO-013FL now proves that the merged successor client source builds fully by CLI
and that its exact Windows-only precursor upgrades the isolated Windows 11
guest, matches `11/11`, completes ordinary-UI authenticated service IPC and
restores the automatic LocalSystem service after a real guest reboot. This
removes the local CTest/build uncertainty but does not create candidate.26,
does not replace candidate.25 and does not satisfy connected
`windows_live_network`. Its `portal.pokrov.space` DNS sentinel was not the
canonical client endpoint and is superseded by WO-013FM's endpoint check.

WO-013FM now proves exact candidate.25's direct-only Windows dataplane through
authenticated production IPC: Core initializes, a secret-free profile stages,
TUN and DNS/routes form, the fixed API egress proof and health pass, disconnect
restores the baseline, and a real connected guest reboot returns to the same
route/DNS hashes with the automatic LocalSystem service safely lazy at
`artifact_ready`. The first verifier incorrectly required `initialized`; its
false harness FAIL and corrected PASS are both retained. This slice does not
use or retain raw IPs or connection material and never touches the host tunnel.

WO-013FN then proves that the next current-source candidate.27 precursor cannot
replace candidate.25: its first in-place upgrade reproducibly aborts before
file replacement because installation-owner resolution fails. The second-pass
success is diagnostic only. The constrained correction is now merged in client
`main` `7e3e771…`; candidate.28 precursor passes the first upgrade with
`11/11`, the full CLI build, native matrices, bounded static scan, direct
TUN/DNS lifecycle and connected reboot. Hosted PR run `33734564011` executes
zero steps and remains `BLOCKED_BY_ACCESS`; local and VM evidence is explicit.

Candidate.28 is not a created candidate and does not inherit candidate.25's
signed supply. WO-013FO supersedes that missing-successor state with private
signed candidate.29. WO-013FQ/013FR then reject it on exact Brain delivery,
managed AWG evidence and the first-run partial-success persistence defect.
WO-013FS supersedes only the latest-attempt boundary with signed candidate.30
from client `7e3e771…`, platform `7c41333…` and exact Core `cd8f0f4…`.
Candidate.30's CLI and bounded Windows checks pass, but its stale SBOM and
provenance candidate/artifact-set bindings make Gate F exact `NO_GO 1/18/2`.
WO-013FT then creates private signed candidate.31 from platform `84837ce…`,
the same client/Core source and exact same application bytes. Fresh SBOM,
provenance and handoff pass strict validation before hosted signing. Its Gate F
is exact `BLOCKED 2/17/0`; candidate.31 is the current release boundary.
WO-013FU adds exact same-byte Windows installed identity `11/11` and a corrected
headless CLI contention PASS `32/32`. It credits neither the failed
noninteractive installer rerun nor any managed connection, so Gate F is
unchanged.
WO-013FV then refreshes current/Brain origins. Final Brain readiness and three
delivery samples pass, but live source matches only `196/197` candidate.31
files, while current-origin is blocked by the untouched owner tunnel. The
current Gate F result is therefore exact `NO_GO 2/17/1`.
WO-013FW adds fresh direct-RU Pi proof: exact-Core AWG3.1/AWG2 and current live
Smart DNS policy/TLS pass. Packaged client, authenticated sessions and the
general-RU Gate F row remain open, so the aggregate is unchanged.
WO-013FX then corrects the earlier file-history diagnosis: after identical CRLF
normalization, Brain's sole mismatched file is an exact Git predecessor
(`1207b63…`), while the other `196/197` deployed files are candidate.31. This
does not change the exact-source FAIL or Gate F `NO_GO 2/17/1`.

The exact UI still opens at first-run onboarding. No trial/account or
entitlement is created without action-time owner confirmation. A managed
profile through an existing activation code is therefore still required for
candidate.31's default/AWG/Smart-DNS/connected-uninstall matrix.

First reconcile Brain to exact committed source under separate production
authorization and rerun the exact source/readiness/delivery contour. Then, on
exact candidate.31 and a suitable isolated Windows device, run managed default
connection, connected DNS/leak/egress,
service restart, connected uninstall, AWG3.1/AWG2, Smart DNS and clean
restoration matrices. Candidate.30's direct-only connect/disconnect and
connected-reboot results are retained history but do not transfer by label.
Do not use interactive UAC or host input while the owner is using the
workstation.

In parallel, prioritize candidate.31's exact Android install and packaged
AWG3.1 then AWG2.
Use an isolated emulator only when its network path is not inherited from the
host tunnel; otherwise wait for the physical phone and retain separate Wi-Fi
and Beeline results. Continue Smart DNS on physical Wi-Fi/Beeline with
authenticated ChatGPT/Gemini/Xbox behavior, attribution and clean restore.
The predecessor Windows selection/TLS path does not replace that
physical authenticated-session matrix.

Then retain Windows 10, interactive SmartScreen and the remaining leak slices.
Record sleep/resume as `BLOCKED_BY_ENVIRONMENT` until a capable device exists,
and IPv6 as `BLOCKED_NO_IPV6_PATH` until a real IPv6 path exists. Continue
separate current/Brain/RU-origin evidence, guarded runtime pointer/kill
rollback, provider/PostgreSQL/outbox, Operator, legal/commercial,
accessibility, comparable performance/endurance and final no-open-P0,
false-green and privacy attestations. Regenerate the 19-row Gate F snapshot
after each material evidence slice. Only Gate F `GO` may allow a
separately authorized Gate G. No public tag, release, Store upload or stable
pointer exists.

### Historical candidate.5–10 context

WO-013BY is the historical candidate.7 signing authority. It signs the same six build
`1.2.0+4046` bytes against final platform `af259f3...` and corrected
SBOM/provenance. WO-013BZ is the historical candidate.7 runtime/decision authority: fresh
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

WO-013DE supersedes that active state with candidate.16. Its signed supply,
refreshed dependency locks, complete local quality gate, managed-profile
readiness correction and fresh LDPlayer default traffic pass. WO-013DF closes
the cached-default defect for both AWG profiles, but each exact current-candidate
runtime fails authenticated egress after tunnel/DNS/routes form. Candidate.13's
AWG lifecycle remains history and is not transferred. WO-013DO closes the exact
ARM64 install identity and generates Gate F `NO_GO 2/17/2`; physical runtime
and the remaining external/manual rows stay non-PASS.

For Smart DNS, WO-013CE proves the exact fronted Linux/amd64 bundle's strict
PROXY-v2, DoH and application TLS passthrough on the observed `x86_64` trusted
terminal host, then records `NO_GO` for RU direct egress as a DNS-only access
bypass. WO-013CG closes the no-mutation inventory and guarded first-frontend
source/PLAN for the foreign `it` canary. WO-013CK then corrects two fail-closed
operator defects and proves guarded frontend APPLY, current/Brain transport,
receipt-bound rollback and guarded re-APPLY. WO-013DG then makes the public DoH
name authoritative `4/4`, installs trusted root-only runtime material and the
exact backend, applies the SNI route, executes a full receipt-bound
frontend/backend rollback and re-apply, and proves bounded DoH plus TLS/SNI
behavior from current, Brain and owned-RU origins. Client selection remains
disabled, and authenticated application sessions, broad leak/privacy/load and
exact candidate device matrices remain open. The earlier Beeline work still
classifies control/API and `ru_spb` as filtered before VPN/TLS; direct `it` is
not an emergency bootstrap for that condition. Android system Private DNS
stays open because the current server is DoH-only.
Windows live network/recovery, candidate.16 origin proof, provider/PostgreSQL/outbox,
Operator, legal/commercial, accessibility, comparable-device performance and
post-public-promotion health also remain open before Gate F can become `GO`.
Public/stable Gate G remains separately authorized and prohibited until then.
