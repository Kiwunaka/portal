# WO-013EH — candidate.21 private assembly and Windows runtime reconciliation

Status: `PRIVATE_CANDIDATE21_WINDOWS11_UPGRADE_DEFAULT_RUNTIME_PASS_SIGNED_INDEX_ANDROID_AND_AGGREGATE_GATES_OPEN`

Observed: `2026-09-02`

Production/public mutation: `NONE`

## Outcome

Candidate.20 is immutable `NO_GO`. Its default Windows 11 connect/disconnect,
public-1.1.6 migration and connected reboot remain valid bounded evidence, but
a forced service termination left the durable recovery journal at `committed`
after SCM restarted the service. Route, DNS and egress happened to return to
the baseline because the process-owned tunnel disappeared; the restarted
runtime did not resume the required rollback sequence and the ordinary UI
reported the runtime unavailable.

Client PRs 61 and 62 merge the startup-recovery correction and build-4050
release projection into `POKROV-app/main` `1e164586d741484b5ae8fb2ee267ef5dd813cadb`.
The service now checks pending recovery before serving its first IPC client;
clean startup remains lazy, and a failed recovery remains fail-closed and
retryable. Platform PR 160 merges the matching release projection as
`e2608130e85d9a0f8fa4b920f46cf3d7679332c3`. Core stays
`cd8f0f4169d570d693992a959d81d17c2c44884d`.

Those exact clean sources are built into local private
`pokrov-1.2.0-candidate.21`, app `1.2.0+4050`. The candidate contains six
immutable distribution files. All five Android outputs retain the one
production certificate lineage; Windows trusted signing remains
`SKIPPED_BY_OWNER` under the approved direct-beta exception. The candidate is
not published or promoted.

Candidate.21 is the current private runtime candidate, but it does not yet
have a strict-v2 handoff, SBOM/provenance refresh or signed public release-index
manifest. Candidate.20 remains the latest signed-index snapshot and is
rejected. Neither fact authorizes publication.

## Exact private candidate

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.21`, `1.2.0+4050` |
| Platform | `e2608130e85d9a0f8fa4b920f46cf3d7679332c3` |
| Client | `1e164586d741484b5ae8fb2ee267ef5dd813cadb` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Hosted client main CI | run `33576468801`, `SUCCESS` |
| Private creation manifest | `c79eb481c3ce0402edaf72c2a5083027481b5a8bc34511c1a694cb972f5331d6` |
| Precursor readiness receipt | `59a411809fe3d49958c086306d18d75b6a1604a3b24c80f05a0ae4eb43ba087b` |
| Windows setup | `87f90be11a927c271c84e8042f17e052ee1070a1ac4923fa3949d6e19c00dff3`, `29143633` bytes |
| Windows build manifest | `665f77f096a54b9fe5ec375149ebadae4e0871165dcba8f19c3fe6fbf6be2919`, `11/11` required files |
| Windows signing | `SKIPPED_BY_OWNER`, mandatory SmartScreen warning |
| Promotion/publication | `false / false` |

Android artifact identities:

- ARM64 APK `d5dd9905bafdc30809a1199dde5961129680a03513b60a6e46f323a6a583693c`,
  `101366678` bytes;
- ARMv7 APK `f39eaa0dabe4a6cd87113506e5ffc954623f6e82d3f684252639c035d898d2f5`,
  `90778788` bytes;
- universal APK `396e8aca2b3b77d727c66ce1287430bdbb550619cd36618c8be1daed07351578`,
  `295370161` bytes;
- x86_64 APK `fc6da2ca396d3e81c4bff1dc3bf7f40700fbf5fdc7bf0d76742e5d80984751e5`,
  `109951989` bytes;
- market AAB `fdd8e1df6a0e52ae1f48234f9c049c071d3fb2a946498c125a3d8c43f188cfcd`,
  `126263297` bytes.

All five signing receipts use certificate SHA-256
`0A0602A7DF5D96A0B427909D004F3DDF26DEF86587634BF16694DA8D654B2500`.
Bounded artifact, Windows staging and token-shape scans return zero definite
findings. They are precursor/private-candidate evidence, not a replacement for
the missing signed release-index supply chain.

## Exact Windows 11 result

The isolated Windows 11 VM begins with candidate.20's forced-termination
recovery journal intentionally retained at `committed`. Installing the exact
candidate.21 setup returns exit `0`, leaves the automatic LocalSystem service
running, validates all `11/11` required files and runs the startup rollback to
`clean`. The retained pending network state is removed and the safe service
events contain successful network restoration and rollback completion.

The exact non-elevated check then proves:

- ordinary caller token, not an elevated owner session;
- installed-file and service-binary identity;
- automatic LocalSystem service running before and after UI launch;
- ordinary-user ownership of the UI process and a live visible client;
- no retained identifier or connection material.

The visible default path reaches verified `Подключено`, selects Germany and
produces a distinct DE egress. `sing-tun` appears, while route and DNS
fingerprints differ from the RU baseline. Disconnect removes the tunnel and
returns egress country, egress hash, route fingerprint, DNS fingerprint,
default-route count, DNS-interface count and active-adapter count exactly to
the pre-connect baseline.

Evidence SHA-256 values:

- upgrade/startup recovery:
  `45a1349a3a09fe56537462978cbf8e686815f58a8c980ba5e3eab80186e5a960`;
- non-elevated UI/service:
  `453b1fa08d0b5571d167e81a429dbf6e4cee083e9d1b7f4f9faeb557d78b60dc`;
- pre-connect network baseline:
  `e7e7686ab7d6b5276cb0719747ddc69a4438fd6d995982b3b9a7bb9a826603d3`;
- connected network:
  `44da58ed9b43bc3673dcfc6d5c9cd3745c8d58814c33a64c50688a3e5fa99cf9`;
- restored network:
  `bf46957d4dd3478f38512a64fe75b3967f857a4314d4cffe0a20bb0828090049`.

This rebinds `REL/WIN-003` and `REL_DOD/DOD-04` to the exact current
candidate.21 default Windows 11 slice at `I4`. It also proves upgrade-time
startup recovery from the exact predecessor failure state. It does not yet
prove an in-place forced termination of candidate.21 followed by SCM restart,
sleep/resume, connected reboot, Windows 10, connected uninstall, AWG2/AWG3.1
live Windows traffic, IPv6/leak or interactive SmartScreen.

## AWG and Smart DNS boundary

The exact candidate.21 source tuple adds current replacement evidence without
claiming live protocol success:

- platform AWG2/AWG3.1 control-plane contract: `72/72 PASS`;
- client typed AWG2/AWG3.1 materialization: `2/2 PASS`;
- Smart DNS client routing contract: `18/18 PASS`;
- Smart DNS focused guarded UI contract: `2/2 PASS`;
- live Windows VM Smart-DNS endpoint/TLS policy probe:
  `PASS_EXACT_WINDOWS_VM_LIVE_SMART_DNS_CONTRACT`.

AWG transport egress is still not run on candidate.21 Android or Windows.
Smart DNS remains default-off and lacks exact in-app selection, authenticated
ChatGPT/Gemini/Xbox sessions, physical DoH, attribution, leak/privacy/load and
lifecycle proof. Hysteria2 remains undeployed.

## Ledger effect

No level distribution changes. `WIN-003` and `DOD-04` were already `I4` and
now receive current exact-candidate replacement evidence. Distribution stays
`I4=7`, `I3=320`, `I2=19`, `I1=32`, `I0=0` across `378` unique rows.

Active next actions are moved from rejected candidate.20 to candidate.21.
Candidate.20 signed supply, SBOM/provenance, offline Gates A–E and privacy
results remain retained predecessor evidence; they are not relabeled as
candidate.21 PASS.

## Open gates

- strict-v2 handoff, refreshed SBOM/provenance and signed release-index
  manifest for candidate.21;
- fresh in-place candidate.21 forced-service-restart recovery and reconnect;
- exact candidate.21 LDPlayer install/launch byte identity without host-tunnel
  network credit;
- physical ARM64 Wi-Fi and Beeline default/AWG/Smart-DNS/WARP matrices;
- remaining Windows, authenticated current/Brain/RU origins, provider/payment,
  PostgreSQL/outbox, Operator OIDC/RBAC, legal/commercial, accessibility,
  comparable performance and endurance;
- guarded candidate.21 rollback plus origin readback;
- final no-open-P0, false-green and privacy attestation.

Gate F remains `NOT_RUN`; Gate G, tag, public GitHub Release, Store upload and
stable pointer remain unauthorized.

## Evidence

- normalized record:
  `evidence/013EH-candidate21-private-windows-runtime/013EH-candidate21-private-windows-runtime.json`;
  SHA-256
  `10802dc4bd94523a1704dfa85355b49e5be7819a60ab773966c97b6e118390bb`;
- local private candidate root:
  `E:/POKROV-tools/release-candidates/pokrov-1.2.0-candidate.21`;
- precursor evidence root:
  `E:/POKROV-tools/temp/candidate21-artifact-precursor`.

The normalized record retains only safe counts, states and hashes. It contains
no credential, raw profile, connection material, customer/provider payload,
device identifier, raw DNS server or open egress address.
