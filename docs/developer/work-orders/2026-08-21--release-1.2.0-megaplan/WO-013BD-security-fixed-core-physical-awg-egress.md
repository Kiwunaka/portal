# WO-013BD — Security-fixed Core physical AWG transport and egress split

## Outcome

The exact production-signed Android pre-candidate built from client
`064fcd018d259210761406d224b00d20bebb5599` and security-fixed Core
`547f09670fad1eeffa94897fb36b12ec5e7818cd` was installed and read back
byte-identically on one physical Huawei/Android 12 device. The same phone and
Beeline path passed the ordinary Frankfurt profile, while both closed owner
labs completed fresh authenticated handshakes and exchanged bidirectional
inner payload.

Neither AWG lab reached the client-verified green state. Both terminated their
selected-endpoint URL test as `EGRESS-001` even though the tunnel stayed up for
bounded diagnostics. The honest result is therefore transport/cryptography
`PASS` and client egress verification `FAIL`, not end-to-end AWG readiness.

This closes the active-Core physical transport repeat requested after
WO-013BC. It does not create a replacement candidate, advance Gate F or prove
Windows parity, RU-origin readiness, leak safety, lifecycle endurance or a
production transport claim.

## Exact source and artifact

| Item | Exact identity | Result |
|---|---|---|
| Platform base | `25eda3c2b8445c3d0561bc156cdb0f465de82819` plus this bounded AWG operator/config patch | locally verified; Brain deploy recorded below |
| Client | `064fcd018d259210761406d224b00d20bebb5599` | clean and equal to `origin/main` before this evidence update |
| Core | `547f09670fad1eeffa94897fb36b12ec5e7818cd` | clean and equal to `origin/main` |
| Bound AAR | `7895b2f7d6e5fe00cc74d3ff85b961f4110b551eb2cf9860fba5e1337ef01a63` | exact client binding |
| ARM64 APK | `101364310` bytes, SHA-256 `7d1d409368fe8c14c0a5064e0104e10ab0d7c798ff96ca5a65e2b65af6958ee5` | `1.2.0+4046`, release, non-debuggable, production self-managed signer, exact device readback |

The APK's embedded ARM64 Core entry matches the bound AAR entry. The test did
not reuse the earlier `3c2b114...` physical result.

## Hosted source evidence

Core GitHub Actions run `33227157016` is exact for `547f096...` and completes
all five jobs successfully: the full test/vet/race/security/static/fuzz/SBOM
job, release contract, Apple source reproducibility, Android AAR
reproducibility and Windows DLL reproducibility plus the 100-cycle proxy test.

Client run `33227155356` is exact for `064fcd0...`, but its only job contains
zero executed steps. It remains `BLOCKED_BY_ACCESS` under the owner-solo/no-
purchase policy and is not counted as `PASS`.

## Physical Beeline result

The ordinary profile on the same APK, device and cellular origin reached the
verified green state with a live POKROV VPN transport. This controls for a
general APK/Core, account or Beeline outage.

### AWG2

- protected exact-device bind: `PASS`;
- fresh authenticated handshake: `PASS`;
- outer capture: `118` packets, `66` inbound, `51` outbound, handshake age
  `15s`;
- inner capture: `118` packets, `70` from client, `47` to client, `112` TCP,
  `5` UDP and `57` TCP payload packets, including payload in both directions;
- reset packets: `0`;
- exact `547f096...` operator Core interop against the same owned material:
  `PASS`, including authenticated TLS/HTTP egress;
- Android selected-endpoint probe: `FAIL_EGRESS_001`.

### AWG 3.1

- protected exact-device bind: `PASS`;
- fresh authenticated handshake with randomized trailers: `PASS`;
- outer capture: `125` packets, `75` inbound, `49` outbound, handshake age
  `21s`;
- inner capture: `117` packets, `69` from client, `47` to client, `108` TCP,
  `8` UDP and `50` TCP payload packets, split `25/25` across both directions;
- reset packets: `0`;
- exact `547f096...` operator Core interop against the same owned material:
  `PASS`, including authenticated TLS/HTTP egress;
- Android selected-endpoint probe: `FAIL_EGRESS_001`.

The shared failure is above AWG handshake/crypto and below the client's final
verified-protection state. Current evidence points at the Android/Core
selected-endpoint URL-test path or its runtime context. It does not support an
IP-ban, broken owned server, Beeline-wide UDP failure or a defect unique to
AWG 3.1.

## IPv4-only managed DNS correction

Both owned endpoints advertise only `0.0.0.0/0`. Their managed DNS policy now
sets `strategy=ipv4_only` so the profile cannot intentionally select an IPv6
destination outside its routed prefixes. Focused builder tests pass.

Before deployment, the Brain source probe matched all `197` selected files to
platform `25eda3...`. A controlled portal-api deployment retained backup
`/root/portal_bot.deploy-backups/20260829T022805Z-4868`, passed staging,
compile, restart and delayed health, and changed only the reviewed managed-
config builders from the deployed base. Both physical lab tests were repeated
after this change and still returned `EGRESS-001`.

After commit `d5fa133cb71694a99d799803ce5573674620fd2a` reached platform
`master`, a fresh read-only Brain probe matched all `197/197` deploy-selected
files semantically (`4` exact bytes, `193` CRLF-only differences, `0`
mismatches). Its retained report SHA-256 is
`79b4d3de33c27be38fe6217e5f2f4a473b4e0a297f378979eb20b6c87ba61182`.

The IPv4-only policy is retained as the correct route-family contract. It is
explicitly not classified as the root-cause fix for the remaining failure.

## Operator tooling

The exact-device binder now returns additional boolean/count/version/age
diagnostics only when ownership validation blocks. It still returns no raw
install, account or device identity. The packet counter now reports FIN, PSH,
TCP payload and payload-direction counts without addresses or payload bytes.
These additions distinguished a working bidirectional data plane from a final
URL-test failure without weakening privacy.

## Cleanup and release interpretation

The exact device was rebound to `default`; server readback confirms both AWG
materials absent, lab allowlist/cohort identity absent and the entitled account
unchanged. POKROV was force-stopped, no app VPN service remained and Wi-Fi was
restored. Deletion of temporary screenshots containing account UI was attempted
with exact paths, but the local execution policy rejected deletion outside the
workspace. They remain a local cleanup item and are not retained in Git or the
release evidence directory.

- Candidate.5 remains immutable and `REJECTED_FOR_REPLACEMENT`.
- No replacement candidate exists.
- Phase 10 remains `I3`; `W3-02`, `W3-03`, `W9-05` and `UNCERT-02` do not
  advance.
- Gate F remains blocked and is not regenerated.
- No tag, public asset, store object, stable switch or release promotion
  occurred.

The next bounded transport task is to reproduce and correct the exact
selected-endpoint URL-test failure inside Android/Core while preserving
fail-closed verified-state semantics. Only after that passes on these same
source-bound bytes should Windows live app/service/TUN/DNS/AWG parity and a
new digest-bound candidate proceed.

## Verification and retained evidence

Focused platform tests pass `41/41`; Ruff, Python compile and `git diff --check`
pass for the bounded implementation before this record. Machine-readable
evidence is retained at
`evidence/013BD-security-fixed-core-physical-awg/013BD-security-fixed-core-physical-awg.json`.
Address-free raw operator JSON remains outside candidate artifacts under
`E:/POKROV-tools/builds/client-064fcd0-core-547f096-physical-beeline-20260829/`
and is digest-bound from the aggregate evidence. No raw endpoint, key, address,
install ID, device serial or account identifier is retained here.
