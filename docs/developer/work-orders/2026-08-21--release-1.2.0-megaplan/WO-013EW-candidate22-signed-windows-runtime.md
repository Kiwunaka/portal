# WO-013EW — candidate.22 signed supply and Windows recovery runtime

Status: `PRIVATE_CANDIDATE22_SIGNED_SUPPLY_WINDOWS11_SERVICE_AND_REBOOT_PASS_AGGREGATE_GATES_OPEN`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Candidate.21 remains immutable `NO_GO`. Exact clean platform
`d16087d5da509e17163bdd7293bec5711aa7eedc`, client
`0aad6bbb3a8baf9bd9e2436ed9e57f7c6fbbafed` and Core
`cd8f0f4169d570d693992a959d81d17c2c44884d` are rebuilt as private
`pokrov-1.2.0-candidate.22`, app `1.2.0+4051`. The candidate contains the five
production-signed Android outputs and the owner-approved unsigned Windows
direct-beta installer. No candidate byte is public or promoted.

The six artifacts are bound to strict-v2 handoff, refreshed CycloneDX SBOM,
provenance, offline supply validation and a trusted Ed25519 release-index
manifest. Release-index input PR 45 merges as exact signing source
`d45b5035e135130cbdec3968e712201e5bc78230`; signer run `33656388958`
completes successfully. Receipt PR 46 merges later as
`5728034df053b7d2397af6bf49a524b3f6e86726` and is not substituted into the
signed manifest.

The exact Windows setup is installed in the isolated Windows 11 VM. A rejected
pre-hello pipe session and a successor session both leave the same automatic
LocalSystem process available. The ordinary non-elevated UI launches against
the installed service. Connected service termination then changes the service
PID, completes startup network recovery, permits ordinary-UI profile restage
and reconnect, and ends with disconnect plus exact RU route/DNS/egress
restoration.

After signing, the same installed bytes are tested across a full connected VM
reboot. The restarted service reaches clean lazy `artifact_ready` state,
retains successful recovery events, permits ordinary-UI restage and reconnect,
and again restores the exact baseline after disconnect. This closes the exact
candidate.22 Windows 11 rejected-session, in-place service-restart and
connected-reboot slices. It does not close Windows 10, sleep/resume, connected
uninstall, packaged AWG2/AWG3.1, IPv6/leak or interactive SmartScreen.

## Exact signed candidate

| Item | SHA-256 / value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.22`, `1.2.0+4051` |
| Platform / client / Core | `d16087d...` / `0aad6bbb...` / `cd8f0f4...` |
| Artifact set | `692e007b776977e8c295f559ef8633d7b63336a1f9451306910cd6c05cc87e27` |
| Creation manifest | `852172b64c5f733e285472ced24150ff842a0bf29979fee2fb187f9f891d81bc` |
| CycloneDX 1.5 SBOM | `be462e77e4d5ea03b85dfc1bdcd3b9681c1d3023414c8781c56c9e7f3d53f19e` |
| Provenance | `13bf87993cdcd7dc7cb80791ccbc15ef6b886d390d1ef563c5cd3718229b5ee7` |
| Handoff input / strict-v2 handoff | `8ffc9b58...` / `6fd9cb56...` |
| Offline supply validation | `b899e136df829852a4f303eb3f0b8237fdfa5afea5cc24d1e09299dd48c996d1` |
| Signed manifest | `81c56e9fcf7478c50d5881538d26fd72459f05a04d9cce403ec99d8ecdcc7d59` |
| Detached signature | `b230a4423064f5b45813fec6eb88a956b820cb6603ad2986b641f2bdd4a8a387` |
| Signing receipt | `6512351934514fd63347ddd7f40e83c5ab56148a8e5e1eb899ac22ed12812124` |
| Signing key | `pokrov-release-2026-01` |
| Release-index source | `d45b5035e135130cbdec3968e712201e5bc78230` |
| Signer artifact | ID `9856878942`, digest `sha256:c41c82689af24facab3e4f753c5eed7c72ab2ea358ac66df4aff905dae2db6ed` |
| Manifest validation | `READY_SIGNED_MANIFEST`, `6` artifacts, `1` owner unsigned-Windows exception |
| Promotion | `promotion_authorized=false` |

Artifact identities:

- Android ARM64 `77bfcaa298d7b9ef4ccf36f179daa715eb619aade8247299dc65075a9b9a6bf4`;
- Android ARMv7 `3f3505f9535a306cf30855bb5e6f3a67826139c3c2298fc1f96e5d701e26036c`;
- Android universal `f6dd81ec42c5eabf9c56ce1c11663518a14e904735cb1b045a352137eb1720f7`;
- Android x86_64 `31962adcc276eb517c1807b7c2ceb8be28d8d4c86755f69924d3ded8a9cfc181`;
- Android market AAB `fe075bb328133a0da762248ae5364c101853fc72200644d6d21597aad0c875bf`;
- Windows setup `effc6a8ed7ccfa943986aca93f4d1d846d66c8d42730ea0b77854b48f77bf409`.

All five Android signing receipts retain certificate SHA-256
`0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`.
Windows trusted signing remains `SKIPPED_BY_OWNER`; the mandatory
SmartScreen/unknown-publisher warning remains a release limitation.

## Exact Windows 11 result

| Slice | Result | Evidence SHA-256 |
|---|---|---|
| install, rejected/successor IPC and non-elevated UI | `PASS_EXACT_CANDIDATE22_INSTALL_PIPE_AND_NON_ELEVATED_UI` | `f5ec0e77b97c09534821ecdec875c4d66ab112cae74d1193123f077b25591864` |
| in-place connected service restart | `PASS_EXACT_CANDIDATE22_INPLACE_SERVICE_RESTART_RECOVERY` | `2b8c7d251d69a9447521fac13737878108de894f963300eaaec544c25f9e9dbd` |
| connected Windows reboot | `PASS_EXACT_SIGNED_CANDIDATE22_CONNECTED_REBOOT_RECOVERY` | `f88efbcf727067dec03c7e921aa2a67d7cffb3188428cfa2c9a2f6450f9facb5` |
| Windows build manifest | `11/11` required files | `fbf08cf5437c64826bc66f1950292547e6b1b31a26af788074d6063db684c527` |
| installed service binary | exact installed identity | `18191f195309460b9d72a4a91a3fc817f3b3610d32891858a0ddddedaae11fb6` |
| temporary test controller | exact diagnostic identity | `7449e24860fe1c6d5ba83741b14a8780f4516c80443f4460067a8e4bbd6ba596` |

The reboot verifier's first post-boot assertion expected `initialized`, while
the actual clean lazy state was `artifact_ready` with `running=0` and
`can_connect=0`. The safe error receipt is retained at SHA-256
`d272ae8fbb3e851b3047c35dc748cd8ac7c79c90e835358d48065424e8e1ae3e`.
The predicate was corrected to accept both documented clean startup states;
the already captured boot was then verified without changing product code or
rerunning the reboot. This is a harness correction, not a product failure.

## AWG and Smart DNS boundary

Candidate.22 precursor readiness also binds source/runtime contracts without
claiming unrun packaged protocol traffic:

- platform AWG2/AWG3.1 control-plane contract: `72/72 PASS`;
- client typed AWG2/AWG3.1 materialization: `2/2 PASS`;
- Smart DNS client routing contract: `18/18 PASS`;
- Smart DNS focused guarded UI contract: `2/2 PASS`;
- direct isolated-Windows Smart DNS endpoint/TLS contract:
  `PASS_EXACT_WINDOWS_VM_LIVE_SMART_DNS_CONTRACT`.

Packaged candidate.22 AWG2/AWG3.1 traffic is still unrun on Android and
Windows. Smart DNS remains default-off and lacks exact in-app selection,
authenticated ChatGPT/Gemini/Xbox sessions, physical DoH,
attribution/leak/privacy/load/lifecycle proof. Hysteria2 remains undeployed.

## Completion index and next boundary

`REL/REL-001` and `REL/DEP-001` are rebound to the exact signed candidate.22
supply without changing their level. `REL/WIN-003` and `REL_DOD/DOD-04`
retain `I4` and are rebound to exact candidate.22 Windows 11 install/default,
service-restart and connected-reboot evidence. `FRKN_PLAN/W3-02` remains `I3`
because typed source is not packaged live protocol traffic. `REL_GATE/GATE-F`
remains `I3` and returns to candidate.22 `NOT_RUN` pending a fresh 19-row
snapshot. Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0`
across `378` unique rows.

Next priority is exact Android install plus packaged AWG3.1/AWG2 and in-app
Smart DNS on an isolated emulator or physical Wi-Fi/Beeline device. Remaining
Windows platform matrix, named origins, guarded rollback, provider/database,
Operator, legal/commercial, accessibility, comparable performance/endurance
and final live attestations remain open. Gate G, tag, public GitHub Release,
Store upload and stable-pointer mutation remain unauthorized.

## Evidence

- normalized record:
  `evidence/013EW-candidate22-signed-windows-runtime/013EW-candidate22-signed-windows-runtime.json`;
  SHA-256
  `6c8e9da5aaefe9377c5d654ac5764cf8e594afcb497417ac20c582c250538cfa`;
- immutable local candidate root:
  `E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.22`;
- precursor evidence root:
  `E:/POKROV-tools/temp/candidate22-artifact-precursor`;
- post-sign Windows reboot evidence root:
  `E:/POKROV-tools/temp/candidate22-postsign-windows-connected-reboot`.

The normalized record retains only public repository identities, hashes,
counts and safe result states. It contains no credential, private key, raw
profile, connection material, raw route, raw DNS server, public egress address,
device identifier, customer data or provider payload.
