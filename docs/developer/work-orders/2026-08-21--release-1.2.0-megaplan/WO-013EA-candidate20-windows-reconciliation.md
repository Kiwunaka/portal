# WO-013EA — Bind signed candidate 20 and close the Windows 11 default-path gate

Status: `CANDIDATE20_SIGNED_WINDOWS11_DEFAULT_WIN003_PASS_ANDROID_GATES_OPEN`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Candidate 19 is immutable `NO_GO`. Its ordinary-user client wrote absolute
AppData paths for local binary rule sets into the managed profile while the
LocalSystem service relocated only the JSON. Core could not open the rule sets,
returned `CORE-005`, and the service rolled back without reporting connected.
This was a client/service materialization defect, not a DE, SPB, DNS or Core
binary result.

Client PR 55 adds a Windows-only bounded bundle over the existing authenticated
IPC channel. The ordinary UI reads its own local `.srs` inputs, replaces their
paths with service-relative slot markers and sends canonical sequential assets.
The service validates framing, names, base64, counts and byte limits, then
materializes exact bytes in a protected A/B generation before atomically
staging the profile. Pipe ACLs and server-side caller authorization remain
unchanged. Hosted PR run `33503907082` passes; merged client `main` and the
candidate source are
`8ab9815ab98f111140c0c8ce4e289555652d56e8`.

That exact source is rebuilt into signed private candidate 20. No tag, public
GitHub Release, Store upload, stable pointer or promotion is created.
`promotion_authorized=false` remains authoritative.

## Exact signed candidate

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.20`, `1.2.0+4049` |
| Platform | `d6898e63c5c9ab7dd267b9d5150b54196f99d967` |
| Client | `8ab9815ab98f111140c0c8ce4e289555652d56e8` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `61ad0b0e0780775b8f95f1a567e94d75d198a483` |
| Receipt merge | `493c4b936bbe1002c1b6ea573860e7306ed46703` |
| Manifest SHA-256 | `046d331274da76ba524f824debb17c4abc080657456c41099246589cc3c1770a` |
| Signature SHA-256 | `f5e81d310fa18b464421afe4c0da010e3b9c112c9affba64e7d1631b4f6890ea` |
| Signing receipt SHA-256 | `47429c2cb3b77520257bb63e7a41652d3744e0a4f710589bf4c20eec289b9479` |
| Release handoff SHA-256 | `a8720ce0dd52dba2377c25e9d698ca74a45a277d73a5d7461ef8fad98dfc081d` |
| Artifact-set SHA-256 | `77eeeafe793433b17f78db294f915e132446b4fc1028d1f5512f8e47ed9a8d7b` |

All five Android artifacts are production-signed. Windows setup SHA-256 is
`330b87cb074a04f43cb7004e4c03cdd0c692b54397acbc223f25dd6e0be8587f`;
it remains `SKIPPED_BY_OWNER` for trusted signing under the approved direct
beta exception and therefore requires the explicit SmartScreen warning. The
11-file Windows manifest, 352-component SBOM, six-subject provenance and all
six supply bindings pass.

Signer run `33509003189` passes and produces retained artifact `9800807994`.
The earlier run `33508836174` fails closed on a working-tree versus tracked-blob
template SHA mismatch and produces no artifact; it is preserved rather than
relabeled. Release-index PRs 41 and 42 pass their hosted source contract and
merge. A separate post-build exact-candidate cross-repository replay is
`PASS`: workflow run `33511744299`, job `99868854293`, validates the exact
platform `d6898e6...`, client `8ab9815...` and Core `cd8f0f4...` tuple, then
passes the strict handoff-v2 contract, client unit and Android-flavor suites and
the conditional Linux daemon foundation. The workflow head is the later
docs-only client `main` revision `9f8de86...`; its guarded input checkout binds
the tested implementation to the exact candidate source above.

## Exact Windows 11 result

The isolated Windows 11 VM first removes candidate 19 machine state. The exact
candidate 20 setup then proves:

- machine installation and all `11/11` manifest files;
- automatic LocalSystem service plus ordinary non-elevated UI and authenticated
  IPC;
- four exact rule sets staged only under the protected service-owned A/B slot,
  with no AppData path or unresolved marker in the staged profile;
- default Germany connect, `sing-tun`, managed DNS `172.19.0.2` and
  service-authenticated DE egress;
- disconnect with Core stop and removal of tunnel route, DNS and adapter while
  restoring the original Ethernet route and DNS;
- clean uninstall;
- exact public `1.1.6` per-user to candidate 20 machine/service migration and
  final clean uninstall.

The aggregate contains `24/24` true checks and is SHA-256
`525987f45ceb88197745b0e738fc2ccb4b5aaf969ad5253c22ad2a2091678d04`.
The service-owned rule-set evidence is
`9873b108afc1bc2e19e7d41d39a903140f3f02349fd749eab43c3d1cd350df6a`;
the migration summary is
`7506a74494772ec556f53222d289cf3d4b0d54a7296edfcb338b442946f91ebc`.
The retained reports contain no raw profile, connection material, device
identifier or open egress IP.

The VM retained an authorized user-level app state, so this is not claimed as
a fresh user profile. Candidate 19 installation root, service and owner
registry were absent before the candidate 20 install, making the machine
installation/service boundary clean.

This exact result closes `REL/WIN-003` and `REL_DOD/DOD-04` at candidate level
for the Windows 11 default TUN/DNS/authenticated-egress/rollback slice. It does
not transfer to Windows 10, AWG 3.1/AWG2 on Windows, sleep/reboot/crash,
connected uninstall, IPv6/leak, interactive SmartScreen or trusted
Authenticode. Those remain separate non-PASS checks.

## Android and emulator boundary

Candidate 20 Android artifacts are production-signed, but candidate 20
LDPlayer install/launch and physical runtime are not yet run. The host Windows
route uses Hiddify/TUN, so future LDPlayer credit is restricted to exact APK
install, launch, process survival and crash-buffer checks. Its network result
will not be release evidence, and no emulator is nested inside the Windows VM.

Exact physical ARM64 Wi-Fi and Beeline runtime remain `MANUAL_OWNER_TEST`.
They must cover default/fallback, AWG 3.1, AWG2, Smart DNS/WARP as selected,
restore, leak/family and endurance boundaries using candidate 20 bytes.

## Decision and open gates

Candidate 20 is the only current signed private candidate. The handoff now has
`WIN_003=PASS` and nine remaining promotion-blocking manual gates. Gate F is
not regenerated and Gate G remains unauthorized. Candidate 19 Brain/current
origin and isolated rollback results remain history and are not transferred.

Before another Gate F decision, complete:

- candidate 20 LDPlayer install/launch/byte identity without network credit;
- physical ARM64 Wi-Fi and Beeline runtime;
- remaining Windows 10/non-default/recovery checks;
- authenticated current, Brain and RU candidate-bound origins;
- provider/payment, PostgreSQL/outbox, Operator OIDC/RBAC and legal/commercial;
- comparable device performance, accessibility/OEM/endurance;
- candidate 20 guarded runtime rollback with origin readback;
- final no-open-P0, false-green and privacy attestation.

No tag, GitHub Release, public asset, Store object or stable pointer exists for
candidate 20.

## Evidence

- normalized record:
  `evidence/013EA-candidate20-windows-reconciliation/013EA-candidate20-windows-reconciliation.json`;
- normalized record SHA-256:
  `1a667984023d28533f583568704cb373eeb16943c139022fd28f57c276e1513f`;
- private candidate root:
  `E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.20`;
- external Windows evidence remains under
  `E:/POKROV-tools/temp/candidate20-winvm-evidence/` and contains no retained
  credential, customer payload or raw connection material in the tracked
  record.
