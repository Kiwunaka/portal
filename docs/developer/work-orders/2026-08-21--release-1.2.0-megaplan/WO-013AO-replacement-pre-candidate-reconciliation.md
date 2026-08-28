# WO-013AO — Replacement pre-candidate reconciliation

Date: `2026-08-28`

Status: `READY_LOCAL_FREEZE / HOSTED_CHECKS_BLOCKED`

## Objective

Reconcile the current post-candidate source line after the Gate B correction,
owned AWG/DNS lab work and Android Core rebinding without transferring any of
that evidence into signed `candidate.3` or creating a replacement candidate.

## Exact implementation and evidence tuple

| Lane | Revision | Branch / PR | State |
| --- | --- | --- | --- |
| Platform runtime | `e5ef03ac7ab013d8810cc9c6ea9ccc40cebd11db` | `codex/awg-owned-lab-deploy`, PR `#58` to `master` | locally gated runtime source |
| Platform AWG operations/evidence | `39af0f1d3a01209bd46dcd0661cabef5de679efe` | same branch / PR | focused checks passed; pushed after the aggregate gate |
| Platform AWG managed issuance | `32e444695432531d7a1a517cb0386bb690c73969` | same branch / PR | local source correction; `53/53` focused and `154 + 8 subtests` backend pass; not deployed |
| Client runtime | `c196dff6bf72c325d5bba675fe19342cd3821f61` | `codex/release-1.2.0-candidate-8-source`, PR `#33` to `main` | locally gated runtime source |
| Client AWG evidence docs | `2eeee5fa0c09096426e09aeb0eeb865a6aede981` | same branch / PR | docs/seed contracts passed; pushed after the aggregate gate |
| Client external Smart DNS lab | `5e78dd9aef93726d40f44ae6a075c952ba951a6a` | same branch / PR | source, unit/widget, full app-shell and physical state-machine proof passed; no resolver/access proof |
| Core | `f44dbe89d6b89954032a1a798c2209d8c0aff90d` | `codex/fix-egress-event-subsystem`, PR `#6` to `main` | clean and pushed |

This tuple is `PRE_CANDIDATE_LOCAL`. It is not signed, promoted, public or
stable. Signed private `candidate.3` remains the exact-candidate authority and
remains `NO_GO`.

## Android Core provenance reconciliation

Core Android was built twice from `f44dbe89d6b89954032a1a798c2209d8c0aff90d`.
Both AARs were byte-identical with SHA-256
`ca391059b6676de5a2cfbf582395fd7ab0b0b5979c8a0c40faaa7208b79178e5` and
size `107394593` bytes. The bytes also match the client AAR previously built
from `54e76bbb...` because the intervening Core commit changes tests only.

The client seed, validation fixtures and canonical client release documents
now bind Android source provenance to `f44dbe89...`; no runtime binary changed.
Windows remains bound to its separately declared Core revision and artifact.

## Current local quality evidence

The aggregate local gate ran with exact Node `22.14.0` against platform runtime
`e5ef03ac...`, client runtime `c196dff...` and Core `f44dbe89...`. All `15/15`
steps passed:

- performance contract and `30/30` contract tests;
- Flutter analysis and `400/400` app-shell tests;
- client seed, release-v2, documentation and repository-hygiene contracts;
- WebApp lint/build and `69/69` cabinet Playwright tests;
- marketing build, SEO, responsive, accessibility and reduced-motion checks;
- AdminApp production build;
- local static performance collection and required gate `9/9 PASS`.

The private local report `010I-local-quality-gate.json` has SHA-256
`facc6b09b7ad94768c59f946d7164adbc7c229a6de605fa958bdc20bb5599e6e`.
It explicitly records `candidate_proven=false`, `local_status=PASS` and
`promotion_status=MANUAL_OWNER_TEST`. Exact candidate/device performance,
artifact comparison, selected browser lab, authenticated controlled-origin
API work and signing/device/origin proof remain non-PASS manual lanes.

The later AWG operations/evidence commits do not change platform or client
runtime behavior. They pass `47/47` focused AWG/smart-connect tests, `32/32`
platform documentation tests, platform-context audit, client seed validation,
client docs contract and both diff/secret checks. The full aggregate gate was
not relabeled or rerun against those documentation/operations heads.

## Owned AWG and DNS physical slice

The retained
[physical pre-candidate record](../../../audit-artifacts/2026-08-28-owned-awg-dns-physical-pre-candidate.md)
binds production-signed working Android package `1.2.0+4044` without treating
it as a candidate.

- AWG2 and randomized-trailer AWG3.1 live server/client alignment pass.
- On physical Beeline, both guarded UDP controls reached the server and were
  echoed `3/3`, while the phone received `0/3`. Both handshakes therefore stay
  `BLOCKED_BY_NETWORK_CURRENT_ORIGIN`; this is not a cryptographic failure or
  universal transport verdict.
- Explicit no-carrier readback selected AWG2 for the exact physical and
  LDPlayer identities, but build 4044 on Wi-Fi and build 4043 on LDPlayer
  emitted no AWG traffic. LDPlayer also rejected the selected Frankfurt
  location before tunnel start. This is `FAIL_WORKING_CLIENT_ACTIVATION` and
  blocks another AWG3.1 device loop until the common client path is fixed.
- Direct HTTPS DoH returned valid responses for the bounded AI/Games set.
  Product routes still require the VPN, so DNS-only ChatGPT/Gemini/Xbox access
  remains `NOT_IMPLEMENTED` and would be a separate Smart-DNS architecture.
- Normal WARP plus independent IP and DNS egress passed after exact lab unbind.

Post-observation source review located the first common activation blocker in
the platform managed-profile route: device-bound `awg2_lab` and `awg31_lab`
material was selected correctly, but issuance still passed through the
ordinary Smart Connect/node shortlist and could return `503 No eligible nodes`
before the typed endpoint reached the client. The route now bypasses that
unrelated catalog for both owned labs, ignores `selected_node_code` and returns
`smart_connect: null`; all device/material/rollout/server gates remain
fail-closed. Focused network regressions pass `53/53`, the router-mandated
backend suite passes `154` tests plus `8` subtests, and documentation contracts
pass `32/32` with platform-context and diff checks. This is
`PASS_LOCAL_SOURCE`, not deployed-device proof, and does not relabel the
retained 4044/4043 failures.

## Working build 4045 correction slice

Client runtime source `51f41c646796e506d9d329ce54e8cc15fb7dfa7b`
demotes an Android `running` snapshot when the app-owned TUN is absent. It
preserves the staged configuration for retry, clears stale Core egress truth
and records `service_destroyed`. Direct and Store Android unit matrices pass
`179/179` each, Flutter analysis is clean, app-shell tests pass `400/400`, the
client docs contract passes and cross-repository seed validation projects
`1.2.0+4045` consistently into platform head
`34d1551f9c732ed879629a768d8825cc694f435c`.

Production-signed working APKs from that exact client source were verified and
installed without declaring a candidate:

- arm64 `1.2.0+4045`, SHA-256
  `8e3c45df8db2582f1a29a1f49776f45da5a0420391f584b892f66e4a7947eddf`,
  installed on the physical Huawei;
- x86_64 `1.2.0+4045`, SHA-256
  `0d76ee15fb9b1519cb8f92940cce315fbe3a1b485aaa44625a8f75623f1cc786`,
  installed on LDPlayer.

Both hosts cold-started without the app-owned VPN service and reported
`Подключить` / `Не защищено`; the physical Wi-Fi state remained disabled.
This is `PASS_4045_DISCONNECTED_HOST_TRUTH`. It closes the stale-running
false-green regression only. It does not prove AWG2/AWG3.1 handshake, tunnel
egress, DNS/leak behavior, endurance or release readiness, and the paired
platform managed-profile correction is still not deployed.

A subsequent bounded physical connect control started the POKROV service but
produced no Android VPN transport after approximately `25` seconds. The UI
tree was unavailable before a post-connect label could be retained, so DNS and
HTTPS were not run. Exact cleanup stopped POKROV, confirmed no Android VPN
transport, foregrounded Hiddify and preserved disabled Wi-Fi. Record this as
`FAIL_4045_PREDEPLOY_ANDROID_ACTIVATION`; it still precedes deployment of the
managed-profile correction and is not an AWG cryptographic verdict.

An independent LDPlayer connect control reached canonical
`core_egress_probe_failed`: the selected outbound did not pass internet proof,
so POKROV stopped the system VPN fail-closed and exposed the safe retry state.
There was no VPN-permission prompt, residual POKROV service or VPN transport
after cleanup. No AWG policy was bound and no server policy was mutated, so
this is `FAIL_4045_LDPLAYER_SELECTED_OUTBOUND_EGRESS`, not AWG tunnel evidence.

A returned-phone state control then inspected build `4045` over Beeline without
starting a connection. With Hiddify stopped and no POKROV service or active VPN
network agent, AdGuard was selected, direct DoH was off, and AI/Games remained
VPN-route presets. The direct-DoH laboratory switch persisted after app
force-stop/cold relaunch and was restored to its original off state. This is
`PASS_4045_PHYSICAL_DIRECT_DOH_SETTING_PERSISTENCE`; it proves persisted
settings only, not a DNS transaction, VPN-free service access or an AWG path.

## Working build 4046 external Smart DNS slice

Client source `5e78dd9aef93726d40f44ae6a075c952ba951a6a` adds a persisted,
default-off external Smart DNS lab on the existing direct outbound. It can be
enabled only for a custom HTTPS DoH endpoint, direct DoH transport and at least
one selected AI or Games purpose route. Selected AI/Games domains then use the
direct outbound; Video and other purpose groups remain VPN-routed, and exact
user overrides retain priority. Invalid persisted combinations normalize off,
while invalid directly constructed combinations fail before native staging.

Focused routing tests pass `16/16`, the focused widget flow passes `1/1`, full
Flutter analysis is clean and the complete app-shell matrix passes `404/404`.
The client documentation contract and cross-repository seed validation pass
with working target `1.2.0+4046`; the exact client worktree is clean and pushed.

The production build script recovered the already trusted public emergency pin
from build `4045` only after a unique SHA-256 match to retained signing
evidence; it did not regenerate or rotate a key. All four `4046` APK variants
then passed version, ABI, release/non-debuggable and production-signature
verification. The physical arm64 package is `1.2.0+4046`, `101348662` bytes,
SHA-256 `dd750a9ff6482dc3a953dc6d00c68ca7648ffeb3cd29efde46a22c1977eafed1`.
It is a working pre-candidate artifact, not an immutable release candidate.

On the returned physical phone the valid state machine was exercised without
starting a connection. With AdGuard and AI/Games initially selected, choosing
a custom HTTPS DoH address exposed the new switch but kept it disabled until
direct DoH was enabled. Once prerequisites were satisfied, the switch enabled
and the AI/Games explanations changed to direct external Smart DNS with the
explicit warning that the public IP remains visible. Custom DoH, direct DoH and
the lab flag persisted across force-stop/cold relaunch. The original AdGuard,
DoH-through-VPN and AI/Games state was then restored and re-read; final cleanup
left no POKROV service and no raised TUN interface. Record this as
`PASS_4046_PHYSICAL_EXTERNAL_SMART_DNS_STATE_MACHINE`.

No DNS query, compatible Smart-DNS resolver, ChatGPT/Gemini/Xbox access,
POKROV connection, AWG profile or tunnel was exercised. This proves the
client-side configuration, persistence, fail-closed prerequisites and truthful
routing labels only. An owned or contracted compatible resolver plus exact
live service-access, leak, privacy and rollback evidence remains absent.

The full bounded local quality gate was then repeated on exact clean platform
`9383117794f9ee17b5976204c3b8601732464c17`, client
`f3d3310f520156cbb07a8993fbe485cf599a174f` and unchanged Core
`f44dbe89d6b89954032a1a798c2209d8c0aff90d` under declared Node `22.14.0`.
All `15/15` steps pass, including Flutter `400/400`, cabinet E2E `69/69` and
local static performance `9/9`. Private report SHA-256 is
`57ca935298957ec88f86f118441acc8611fe1a044af879c0038b3074964f02ed`.
It explicitly records `candidate_proven=false`, `local_status=PASS` and
`promotion_status=MANUAL_OWNER_TEST`; it does not convert the predeploy device
failure or any external/manual lane to PASS.

Read-only Brain source probes now bind the exact change window. Current live
runtime `e5ef03ac...` matches `193/193` deploy-payload files; report SHA-256 is
`2be21f11...26c6c`. Corrected runtime source `716186a...` matches `192/193` and
differs only at `portal_bot/api_client_routes.py`; report SHA-256 is
`410d7cff...556a` with `runtime_mutated=false`. Deploy/source-probe/release-op
tests pass `57` tests plus `25` subtests. The authorized plan restarts only
`portal-api`, requires staging/backup/preflight, delayed active+zero-restart
health, automatic rollback on deploy failure and a postdeploy `193/193` source
readback before any AWG device binding. No deploy or runtime mutation occurred.

A fresh read-only recheck keeps exact AWG branch head `83502f1...` at
`192/193`, with only `portal_bot/api_client_routes.py` different and report
SHA-256 `fb396cd9...ceb5`. Current aggregate head `50c9d12...` is explicitly
rejected for this deploy window: it is only `179/197` and carries 18 later
HY2/observability/Smart-DNS runtime deltas. Its report SHA-256 is
`b92f345c...f897`; both reports retain `runtime_mutated=false`.

The dedicated guarded deploy entrypoint then passed a fresh read-only PLAN
against Brain at `193/193`. It pins live source `e5ef03ac...`, reviewed AWG
source `83502f1...`, the sole target `portal_bot/api_client_routes.py`, restart
unit `portal-api`, postdeploy full-source readback and automatic baseline
restore/readback. PLAN report SHA-256 is `73dcc150...b835f` and records
`runtime_mutated=false`; apply was neither authorized nor run.

Aggregate merge head `9bbb7c9...` combines those AWG operations with later
OBS-087, HY2 and Smart-DNS work without widening the deploy window. The
deployer now digest-pins the exact 193-path mapping owned by both frozen
revisions; four aggregate-only runtime entries absent from both are ignored,
while one-sided shape or remote-target drift fails closed. The combined
contract suite passes `166` tests plus `6` subtests; release/docs/manifest
checks pass `76` tests plus `21` subtests. A post-commit read-only Brain PLAN
again returns `193/193`, `runtime_mutated=false`; report SHA-256 is
`ff48d40f...34e4b6`. No deploy, restart or policy mutation occurred.

The bounded local quality gate was then run on the exact unified clean tuple:
platform `01f9a1356d19e247eb8ae136c6ec1685b1a9ea56`, client
`48c31dfcde48d263bf6a656b1efeef35ef67baaa` and Core
`e8eb7721fc6eaac6813d3a888ac90d0da1f541a1`. The first invocation honestly
returned `FAIL` because the new platform worktree had no frontend
`node_modules`; its retained report SHA-256 is
`2a238406e68b860d8457034152d0946f8c4f47dee7ea3406c557be11dda44efa`.
This was an environment-precondition failure, not a product pass and not
discarded evidence.

After lockfile-only `npm ci` for webapp, marketing and adminapp, the same gate
was repeated under the package-pinned Node `22.14.0`. All `15/15` steps pass,
including Flutter `412/412`, cabinet Playwright `69/69`, all three production
frontend builds and local static performance `9/9`. The 4,608-byte quality
report SHA-256 is
`df4b84b5586513556ffadaa068d4dff1e7085da89bb5cc973854e489e831ad46`;
the performance evidence and gate SHA-256 values are respectively
`102195f1e9dd9a07ff2aedd3842a7f3f1360b54b177d4f6f6048e63ebfe107b0`
and `9238f7e2c468a036820ad8e9b75e71a85690a636973a8250438607bf223f829e`.
The report still records `candidate_proven=false`,
`promotion_status=MANUAL_OWNER_TEST` and `scope=local_worktree_only`; it does
not authorize deployment, signing or promotion.

Fresh source/host checks bind platform `50c9d12...`, client `75e82b0...` and
Core `e8eb772...`: AWG2/AWG3.1 contract sync passes, ten focused Flutter tests,
thirteen Android direct-release JVM tests and thirty-one Core AWG tests pass.
The separate live Core interop from the current Windows origin fails after the
outer write for both profiles. For AWG2, a concurrent address-free server
capture counts `34` inbound and `8` outbound packets, including `8` initiation
and `8` response-sized packets, with no handshake. That exact slice is
`BLOCKED_BY_NETWORK_CURRENT_WINDOWS_ORIGIN_REVERSE_UDP`; AWG3.1 remains the
narrower `FAIL_NO_OUTER_RESPONSE_CURRENT_WINDOWS_ORIGIN` because its packet
capture was not repeated. No server setting, rollout or device binding changed.

## Single-source Core and local-freeze checkpoint

The active pre-candidate tuple now binds platform
`8c7496a70fbc1c918ff8e89a4a458e98aef6a01f`, client
`3564023c8d0e66977043332f2772cfd512489676` and Core
`e8eb7721fc6eaac6813d3a888ac90d0da1f541a1`. Android and Windows artifacts
were rebuilt twice from that one Core revision and are byte-identical:

- Android AAR: `107390782` bytes, SHA-256
  `7c392883ee8a09c15e414a0e9d70a4d4d3cb259032e51c5481cd14a571950745`;
  evidence-tree SHA-256
  `aafd5f0eb2a83f7c438affb32c946af17b77593e9e0f5105b7f7b1d293e2f8f3`;
- Windows DLL: `55403008` bytes, SHA-256
  `73aacd2ccbb3414573284c0c2a253f29c6ed4a56ddf2ff8bb6cc9ae7ca371488`;
  evidence-tree SHA-256
  `25405fd108405f56c08c5a24f88a2b45a6936ff14eae4f113b2e7e71f08eb78c`;
- deterministic source SBOM SHA-256 values:
  `d40547fa3ba28c84bf377e6cb8d174546ea75f41287028ca2e97931cd7ebfb9b`
  and `83bc11b4b90e267346647670f6ce4003d9586ed4519b7bca076e84c3127ce542`.

The replacement DLL passed the exact ABI check and `100/100` proxy-only
start/stop cycles without route mutation. The complete client gate then passed:
Flutter app shell `412/412`, runtime engine `67` passes with its standard
real-DLL case skipped as designed and proved separately, Android shell Flutter
`8/8`, Windows shell Flutter `24/24`, and both Android direct/store Gradle unit
matrices (`162` successful tasks overall). Seed validation, cross-repository
parity, observability, release-v2, docs and repository-hygiene contracts also
pass.

The strict read-only replacement preflight reports `READY_LOCAL_FREEZE` with
`0` blockers, `0` pre-freeze rows below `I3`, `27` candidate rows below `I3`,
`13` external rows, `18` deferred rows and `58` total ledger rows below `I3`.
Its 38,467-byte report
`2026-08-28-replacement-preflight-8c7496a-3564023.json` has SHA-256
`6a8d84d5eb51375340de0a377a2448c33622ee28c27de2c671f717dae8a35b00`.
It explicitly records `candidate_created=false`; this closes the local freeze
prerequisites only and does not claim signing, hosted CI, physical-device,
clean-host, origin, deployment or promotion proof.

## Direct-beta 4046 replacement packet checkpoint

The current local direct-beta packet binds platform release tooling
`e6ae46e33b74029ec30626a216cd947c8c131ba3`, client
`3564023c8d0e66977043332f2772cfd512489676`, Core
`e8eb7721fc6eaac6813d3a888ac90d0da1f541a1` and release index
`863968ec7ea28df08692b354d622de97c9cc5990`. The platform revision fixes a
false-green in the GitHub release-plan helper: strict-v2 handoff input must now
match the complete planned artifact set, roles, architectures, sizes, hashes,
canonical filenames and prerelease URLs. The focused helper suite passes
`9/9`; release/orchestrator/manifest and documentation regressions also pass.

Five exact `1.2.0+4046` local artifacts were assembled without creating a
GitHub release or immutable candidate:

- Android arm64, `101346230` bytes, SHA-256
  `a046408731fc6a9306b1d500a1187d6d16cc92cdff66c8acccfa1df68f17761f`;
- Android armeabi-v7a, `90760708` bytes, SHA-256
  `2a28a15479570fd8b948b5d757787d5475d76bfe78e4743214bd6352bdbeceef`;
- Android x86_64, `109930165` bytes, SHA-256
  `9807a0e84d1b4a64f63629152c76cbaba9e23b52ce3bc2d6482e0a45778f5623`;
- Android universal, `295299185` bytes, SHA-256
  `f4f930c589d08cd440ee25806d9f02b3531026bd744efa20e406af9e723de5e2`;
- Windows x64 installer, `28919231` bytes, SHA-256
  `6cbb4e95c780b79c2bcc744cac421a1a12884acd923c1de86dd5090562902e80`.

All four APKs are non-debuggable and pass production self-managed signature
verification with certificate SHA-256
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.
The Windows installer is intentionally `NotSigned` under the owner's direct
beta exception: its signature gate is `SKIPPED_BY_OWNER`, SmartScreen warning
is expected and no trusted-signing or Store claim is made.

The five-artifact set SHA-256 is
`e85009d7af7951e96db0c4de3b5aef6162d131d92e921b28f82221b52603dd1e`.
Its CycloneDX SBOM and provenance SHA-256 values are respectively
`1f0d52ac29603b775b882084318461c2f4fe262075785747cb190595b7b9e7f1`
and `f96793cad98e06da8565d84ed8d2d6682f1e864475446ef2ddc721f40605acbf`.
The strict-v2 handoff is `valid_v2`, lists five artifacts and retains ten
blocking candidate gates; its SHA-256 is
`7eb411f8363d849af669825e9a2365f2ba0ec3e685ea99b92c3aae5efdcd6bb2`.
The complete `20/20` checksum inventory verifies with checksum-file SHA-256
`1e13433e98e31f19cc8be838cd016a9484e2853cdf579e26bfdbd2010744f7ca`.

The corrected publishing helper accepted that exact strict-v2 handoff and
produced a `plan_only` prerelease plan for `v1.2.0-beta.4046`, five artifacts
and canonical public filenames. The 6,515-byte plan has SHA-256
`1804dfc056a1cc382ecb46d2a4a80ac50074aa4d11751270209ee1b6d5afe369`.
It created no staging directory and ran no `gh release create` command.

LDPlayer installed the exact x86_64 APK; installed `base.apk` matches the
staged SHA-256 byte-for-byte, and package readback reports version `1.2.0`,
code `4046`. The retained disconnected state shows no POKROV VPN service, VPN
transport, TUN link or always-on VPN. This is
`PASS_EXACT_PRE_CANDIDATE_INSTALL_AND_DISCONNECTED_HOST_TRUTH` only; AWG2,
AWG3.1, DNS, HTTPS egress, leak behavior and rollback were not exercised.
The returned Huawei remained absent from Windows PnP and ADB, including as
Huawei, Android, MTP or ADB hardware, so physical-device candidate testing is
`BLOCKED_BY_DEVICE_ENUMERATION`, not a client failure or pass.

The exact read-only replacement preflight now reports `READY_LOCAL_FREEZE`
with `0` blockers and `0` pre-freeze rows below `I3` across `378` ledger rows.
There remain `27` candidate, `18` deferred and `13` external rows below `I3`.
The 38,467-byte report
`2026-08-28-replacement-preflight-e6ae46e-3564023.json` has SHA-256
`7057c195a956c250d8656df739984b2057d254a00a31f73b296a624f4ab94fa1`.
It records `candidate_created=false`, `candidate_proven=false` and
`promotion_authorized=false`. This checkpoint authorizes no deploy, server
policy mutation, release creation, publication or promotion.

### Post-packet LDPlayer DNS and deploy-plan follow-up

The exact staged x86_64 build `4046` exposed all seven current catalog
locations on LDPlayer: Frankfurt, Amsterdam, Warsaw, Milan, Moscow,
Saint Petersburg and New York. This is catalog/UI readback only; the displayed
availability and synthetic host latency do not prove a successful tunnel or
the mobile-origin reachability of any location.

The external Smart DNS state machine was then exercised with the public
token-free `https://cloudflare-dns.com/dns-query` endpoint. The external lab
toggle stayed disabled while direct DoH was off, became available only after
direct DoH was enabled, showed the required compatible-server/public-IP
warning when enabled, and preserved the valid state across a force-stop/cold
launch. One bounded Frankfurt connect then ended with the canonical
`core_egress_probe_failed`; POKROV removed its system VPN fail-closed and left
no app service, VPN transport or TUN link. Site-address, VPN-egress and route
checks remained unrun because connection proof never passed. This is
`PASS_4046_LDPLAYER_SMART_DNS_STATE_AND_CLEANUP` plus
`FAIL_4046_LDPLAYER_SELECTED_OUTBOUND_EGRESS`, not DNS service-access or AWG
evidence. The original `Автоматически` DNS state was restored, both lab
toggles were disabled, and the clean state persisted across another cold
launch.

The exact build also exposes the bounded purpose groups in the Android Rules
surface: AI names ChatGPT and Gemini, while Games names Xbox; Video, Social and
RU-direct remain separate groups. No toggle was changed during this readback.
The 9,238-byte accessibility-tree evidence
`2026-08-28-ldplayer-ai-games-purpose-groups.xml` has SHA-256
`c33191fcc408cbed172bffcd52c005d155a23cefefe7bebe824946a0814052b2`.
This proves exact-build UI availability only. It does not prove that DNS alone
unblocks those services, a compatible Smart-DNS server, live name resolution,
traffic routing or service access.

The live Amsterdam variant sheet currently returns only `Обычный`, `Белые
списки` and `Белые списки тип 2`; neither owned AWG lab is exposed by the live
managed-profile policy. The 8,181-byte accessibility-tree evidence
`2026-08-28-ldplayer-amsterdam-live-variants.xml` has SHA-256
`486a5c9c7766d02283a7e1c5e53cc7ef6bd4d487d1daae67ece499a44da6126f`.
This is the expected pre-APPLY boundary, not an AWG client failure: AWG2 and
AWG3.1 are authenticated, device-bound managed profiles rather than raw
consumer location variants.

A bounded `OBS-079` airplane-mode attempt on the same LDPlayer installation
could not reach the app action: LDPlayer kept its ADB transport enumerated but
stopped returning every Android guest-shell command immediately after the
mutation. The instance and ADB daemon were restarted, after which airplane
mode was off, Wi-Fi and internet were restored, build `1.2.0+4046` remained
installed and no POKROV service, VPN transport or TUN link existed. A cold
launch then showed that the owned entitlement had expired, so no replacement
connect attempt was made. The 1,861-byte sanitized report
`2026-08-28-ldplayer-network-mutation-blocker.json` has SHA-256
`6676ac587a5a82c0befb7ecc63311a4b257ae808b7045f50b2492554850b6b3a`.
This is `BLOCKED_BY_EMULATOR_CONTROL_PLANE_AND_ENTITLEMENT` plus clean recovery
readback; it is neither an app PASS nor an app failure and does not advance
`OBS-079` or the AWG device matrix.

A fresh guarded Brain `PLAN` against the owned managed-profile route reports
`193/193` predeploy baseline matches, zero mismatches and the sole target
`portal_bot/api_client_routes.py`; only `portal-api` would restart. The plan
retains `runtime_mutated=false`, uses key authentication and did not stage,
upload, restart or alter policy. Its 932-byte report
`2026-08-28-brain-awg-route-plan-post4046.json` has SHA-256
`05199f7ccb3814ac231880eaf06fe6acd8b378c47e4c3f8883126ea5c2653360`.
AWG2/AWG3.1 device proof still requires separately authorized APPLY followed
by managed-profile readback and a bounded handshake, egress, DNS/leak and
cleanup matrix. The physical Huawei was still absent from both Windows USB
PnP and ADB during this follow-up.

## Hosted PR evidence

The existing PR branches were fast-forwarded without force or merge. Platform
runtime/release source is frozen at `e6ae46e3...`; platform changes after that
revision are confined to this retained work order. Client PR `#33` is at
`3564023c...`, and Core PR `#6` is at `4fa9accf...`. The Core PR head differs
from frozen product Core `e8eb7721...` only in `.github/workflows/ci.yml`; no
runtime, build input, release contract or product documentation changed after
the exact Core artifact freeze.

Platform runs `33174372410` and `33174372409` and client run `33174374801`
again received zero execution steps and failed within two or three seconds.
GitHub reports failed account payments or a spending-limit block. They remain
`BLOCKED_BY_ACCESS_GITHUB_BILLING`, not product failures and not passes.
`OWNER_SOLO_EXCEPTION` does not waive required checks.
Later evidence-only platform carriers repeat the same zero-step condition; the
current PR check rollup is the exact authority for the newest carrier rather
than a self-referential commit SHA inside this document.

At current platform carrier `2c08d542...`, `Guardrails` run `33181469536`, job
`98883458057`, and `Release v2 Contract` run `33181469508`, job `98883449576`,
each failed in two to three seconds with zero steps and no downloadable job
log. Authenticated GitHub UI readback of the current Guardrails job exposes one
pre-runner annotation: GitHub did not start the job because recent account
payments failed or the account spending limit must be increased. Repository
Actions are enabled, all actions are allowed and both jobs use the standard
`ubuntu-latest` label. Client run `33174374801`, attempt `2`, has the same
zero-step/no-log shape. This directly supports
`BLOCKED_BY_ACCESS_GITHUB_BILLING`; changing workflow code or treating a local
run as hosted proof would be a false green. No billing, visibility, runner or
repository setting was changed during this readback.

The newest platform carrier narrows that statement. `Guardrails` run
`33178564672` still received zero steps, and client `Release v2 Contract` run
`33174374801` remains the same access/billing blocker. Platform `Release v2
Contract` run `33178564639`, however, executed thirteen steps, checked out the
cross-repository inputs and failed closed at seed validation. Client `main`
`95afa078...` still supplies `1.2.0+30`, while the platform owners correctly
describe the replacement `1.2.0+4046` line. This is
`FAIL_RELEASE_CONTRACT_CLIENT_MAIN_STALE_VERSION_TRUTH`, not a missing checkout
key and not a reason to rewrite the replacement owners back to `+30`; the
client replacement binding must be promoted first under its own green checks.

GitHub secret-slot metadata confirms the remembered release credentials are
present: the platform-to-client and client-to-platform deploy-key slots, both
Core deploy-key slots, the release-index manifest-signing slot and the two
support-mode slots all exist. No secret value was requested or read. The only
referenced missing slot is `NODE_PASS_BRAIN`, scoped to the manual remote
release-orchestrator step. It is not needed for the workflow's dry-run, but a
future hosted `verify-only` or `full` remote run would fail closed without it
after Actions access is restored. No secret or repository setting was changed.
The 3,751-byte sanitized readback
`2026-08-28-github-actions-secret-wiring-readback.json` has SHA-256
`3ad49b2b7a4f6843983705782873478e4f713d471819677618d2d8e9d6965ef2`.

The client workflow was also reproduced locally against the exact replacement
tuple instead of the stale promotion lines. Client `3564023c...` validated
against platform PR carrier `be3a969b...` (unchanged product source
`e6ae46e3...`) and a temporary detached Core product-source checkout at
`e8eb7721...`. Cross-repository version, product-fact, observability,
release-handoff, rollback, source-logging and repository-hygiene contracts all
passed for `1.2.0+4046`. The standard client gate then passed foundation
analysis, `563` Flutter tests, both Android Gradle flavors and the signing
source contracts. Its single declared skip was the client-local real-Core DLL
backtest; exact hosted Core Windows evidence separately retains the passing
100-cycle run. The temporary Core worktree was removed, and neither tracked
client files nor `artifacts/releases/**` changed.

The 2,912-byte sanitized report
`2026-08-28-local-client-release-v2-gate-3564023.json` has SHA-256
`ee9f3b9def349d0d22521705770d33aea9faf58032715e7fc2985b7034486b6e`.
This is `PASS_LOCAL_CLIENT_RELEASE_V2_GATE`; it does not replace the required
hosted client check, does not prove a physical-device tunnel and does not
authorize merge, candidate creation or deployment.

Client hosted run `33174374801` was retried once at the same exact head. Attempt
`2` again received zero steps and failed in two seconds, so the current client
PR check remains `BLOCKED_BY_ACCESS_GITHUB_BILLING`; the local pass is not used
as a waiver.

Platform Guardrails were then decomposed in a temporary clean detached checkout
at PR head `c2af23e5...`. Dependency, script-manifest and generated-artifact/
public-copy guards passed before any build output existed. The shared release,
orchestrator and client-smoke group passed `36/36`, support-signing custody
passed `11/11`, and eleven of twelve quick-gate constituents passed, including
worker retention, portal Flutter, API lifecycle, all three production builds,
WebApp Playwright and visual smoke. The quick wrapper's sole non-pass was its
local autodiscovery of stale `POKROV-app/main` and `POKROV-core/main`; the same
contract then passed separately with explicit client `3564023c...` and Core
product source `e8eb7721...`. The wrapper itself is therefore not relabeled as
a zero-exit pass.

The canonical adminapp block additionally passed the `75`-operation SDK hash,
lint, production build, `28`-route/`7`-workspace cutover readback and `78/78`
Playwright tests. This local host used Node `24.15.0`, not the hosted pin
`22.14.0`, so exact runner parity still belongs to GitHub. Both temporary Core
and platform worktrees, their `403` npm packages and generated build output
were removed. The 3,309-byte sanitized report
`2026-08-28-local-platform-guardrail-constituents-c2af23e.json` has SHA-256
`61269a7bc5f456aefe779d4210f083511185e7123594824842db52cc267c0146`.
This is `PASS_LOCAL_PLATFORM_CONSTITUENT_GATES`, not the required hosted
`repo-guardrails` check and not candidate or deployment evidence.

The owner solo exception is now enforced without weakening checks on the two
public repositories. Core `main` requires the strict five-job source/artifact
matrix, and release-index repository `Kiwunaka/pokrov` `main` now requires the
GitHub Actions `source-contract` check. Both protect admins, require linear
history and resolved conversations, require zero independent approvals, and
forbid force-push and branch deletion. The release-index branch policy was the
only external setting changed in this slice; repository visibility and code
were unchanged. Private platform and client branch-protection APIs return the
exact GitHub `403` requirement to upgrade to Pro or make the repository
public, so equivalent enforcement remains `BLOCKED_BY_GITHUB_PLAN_403`. The
3,015-byte sanitized readback
`2026-08-28-github-solo-branch-protection-readback.json` has SHA-256
`d37f0fdc40143141c9024250cb0295813b224ab513142211bd27746a73fda696`.
This is partial Gate A progress; it does not waive the two private-repository
checks and no repository was made public.

Core run `33176149420` at exact CI head `4fa9accf...` passes the complete
`test` job plus Android artifact reproducibility, Windows artifact
reproducibility with the 100-cycle client backtest, and Apple source build.
All five first-party Core checkouts passed an explicit source-authority guard,
and the three retained artifact reports now record clean source
`4fa9accf01a7bed717f739d3f57eb27a65593e3c` rather than GitHub's temporary PR
merge commit. Their evidence SHA-256 values are:

- Android: `533a14315aafdff378feae7c7b81bce1a54741a2f52ab979b016bc5beb6f1040`;
- Windows: `5a6e7cc0e394b7034531c0b939170c41584eebe1cffa168b66be92abe9c93bbc`;
- Apple: `47c2fe57bd49f8b2958b9c523ef471aa99d9927161ab526ed62ec915ccd6a50b`.

The hosted source SBOM SHA-256 values remain
`b559d5b91c0c2f5ea054051a453b9890ba645dc6e298d741644db4589d5d3b8b`
and `cff200645059adab34f72aa66a097fa1cb1fb7c2f3017cfb4afc7a0530aae617`.
This is hosted pre-candidate reproducibility evidence only; hosted bytes are
not relabeled as the local packet or an immutable candidate.

The same run's `release-contract` job fails closed with the exact message that
client `main` still pins Core
`344b317a7a09eca7943a93866b193553538bd8f6`. Client PR `#33` contains the frozen
`e8eb7721...` product binding but is not merged. The overall run is therefore
honestly `FAIL_RELEASE_CONTRACT_CLIENT_MAIN_STALE` despite the four passing
Core jobs.

No PR is merged while these required checks are unresolved. No deploy,
candidate creation, public asset, stable pointer or production mutation occurs
in this work order.

## Ledger decision

`FRKN_PLAN/W3-01` advances `I1 -> I3`: the isolated POKROV-owned lab now has a
retained server record, exact alignment readback, default-off policy and
guarded kill/unbind path. This does not claim a successful tunnel or cohort.

The tuple also strengthens existing `I3` local evidence for `REL/PERF-001`,
`REL_GATE/GATE-E`, `FRKN_PLAN/W3-02`, `W3-03` and `W6-02`, and narrows the
`UNCERT-02` boundary without advancing it. Exact signed candidate,
device/origin matrix and promotion evidence required for `I4/I5` are absent.

WO-013AI already retains a complete fail-closed Gate F decision for the exact
signed prior candidate: `19` required checks, `5` passes, `14` non-passes, `1`
explicit failure and `0` validation errors. It binds the signed manifest,
source tuple and upstream evidence and returns `NO_GO`; Gate G and
public/stable mutation remain unauthorized. The retained decision SHA-256 is
`017c0369760029350f95eafa2b7944134f80c54ffdf1ce8265ce66f511a6d1dd`,
and the current focused Gate F/preflight/STOP-SHIP/docs suite passes `67/67`.
`REL_GATE/GATE-F` therefore advances from the stale `CAPTURED/I0` entry to
`VERIFIED_EXACT_CANDIDATE_NO_GO/I3`. This proves that the prior Gate F ran and
rejected its candidate; it is not candidate proof or a release pass.

Distribution becomes `I4=4`, `I3=314`, `I2=19`, `I1=40`, `I0=0`; `318/377`
rows are at or above `I3`, while `59/377` remain below.

## Next action

1. Retain the local-freeze tuple and obtain explicit authorization before
   creating or signing a replacement candidate; `READY_LOCAL_FREEZE` is not a
   candidate and not a release.
2. Deploy the locally verified managed-profile correction to an authorized
   controlled environment, then prove build `4046` creates an app-owned TUN and
   reaches Core over AWG2 before running AWG3.1 and the bounded DNS/egress/leak
   matrix.
3. Select an owned or explicitly approved compatible Smart-DNS resolver and
   run separate DNS, AI/Games access, IP-visibility, leak and rollback proof;
   the `4046` physical state-machine result is not that proof.
4. Restore private-repository Actions through Billing & plans, or obtain an
   explicit owner instruction before changing repository visibility.
5. Require successful platform/client app-bound checks on the exact PR heads.
6. Merge the client binding under the solo PR control, rerun Core
   `release-contract`, then promote Core and platform only with their required
   checks green.
7. Freeze and sign a replacement exact candidate from the promoted tuple.
8. Run the candidate-bound Android/Windows, current/Brain/RU-origin, provider,
   Operator, legal and performance matrices before any Gate F `GO` or Gate G.
