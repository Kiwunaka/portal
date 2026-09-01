# WO-013DV — Candidate 18 Windows replacement, signing and exact replay

Status: `PASS_SIGNED_CANDIDATE_WINDOWS_FOUNDATION_PHYSICAL_NETWORK_GATES_OPEN`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `01/03/10/11`
Candidate: `pokrov-1.2.0-candidate.18`
Production mutation: `NOT_RUN`
Promotion: `NOT_AUTHORIZED`

## Outcome

Candidate 17 is retained as rejected evidence. Its Windows setup contains only
eight manifest-bound runtime files. It omits `msvcp140.dll`,
`vcruntime140.dll` and `vcruntime140_1.dll`. On the isolated Windows 11 VM the
service cannot start, while that installer can return exit code `0`. Candidate
17 must not be published or relabeled as a passing Windows candidate.

Client PR 53 fixes that exact boundary. The package now resolves the Microsoft-
signed x64 VC143 app-local runtime through Visual Studio installation metadata,
requires the Microsoft signer, includes the three DLLs in the release manifest
and makes service installation transactional. A failed service start returns a
non-zero installer result and removes the partial installation. The same change
adds a guarded migration from the public per-user 1.1.6 install to the
machine-wide service.

Candidate 18 binds these exact sources:

| Lane | Revision |
|---|---|
| Platform | `d6898e63c5c9ab7dd267b9d5150b54196f99d967` |
| Client | `820ca1016bdfef0f44a1d217e3804adb9b365ca5` |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `5dc25bdde2ce146c65c37c08bf96afebe722f759` |
| Receipt merge | `d8fb1cbcc420a933e9ffc8cd7a430cff56903467` |

The six build `1.2.0+4049` artifacts pass offline supply validation. Five
Android artifacts use the production certificate. Windows remains
`SKIPPED_BY_OWNER` under the exact direct-beta exception and still requires the
SmartScreen/unknown-publisher warning. The 352-component CycloneDX SBOM,
six-subject provenance, strict-v2 handoff and 11-file Windows runtime manifest
are bound to the candidate.

## Windows evidence

The exact setup SHA-256 is
`21dca69a4cffe9648bf9788c1279606896c798b32617dd88fa0d9c1e9c1bf2d3`.
An isolated Windows 11 VM starts from clean POKROV application state and proves:

- setup exit `0` and exact `11/11` installed-file identity;
- automatic `LocalSystem` service identity and authenticated UI/service IPC;
- SCM stop and restart;
- clean uninstall with no service, install-owner or adapter residual;
- unchanged idle route and DNS fingerprints;
- public per-user 1.1.6 to machine-service migration and final cleanup.

The evidence ceiling is clean application state, not a clean operating-system
image. Live TUN, connected DNS and leak checks, authenticated VPN egress,
sleep/reboot/crash recovery, connected uninstall and interactive SmartScreen
remain `MANUAL_OWNER_TEST`.

## Signing and hosted replay

Release-index input PR 37 and receipt PR 38 pass real hosted source-contract
jobs and merge under `OWNER_SOLO_EXCEPTION`. Main-only signer run `33475398520`
creates a private Actions artifact with `promotion_authorized=false`.

| Signed object | SHA-256 |
|---|---|
| Manifest | `d686238265e19b7a63759b735e18a49d8910f1885098dc923c5f1c51130f9a56` |
| Detached signature | `a5584da629e4562b2ec6d79824f5d121e691f8b7e3ce0a83475f6a00464b6324` |
| Receipt | `42a4c7381dc8dab6cdb226476f0ab316222bd96f16994d75e10f22f0436fe83d` |

Exact-source replay run `33475733478` checks out the candidate 18
platform/client/Core tuple and passes handoff v2 validation, client unit and
Android flavor tests, and the conditional Linux foundation. Client PR 53 run
`33471290095` also passes all real cross-repository steps before merge.

## Android evidence boundary

The exact x86_64 APK installs and launches on LDPlayer, and the installed
`base.apk` is byte-identical. No network result is credited because the host
Windows route is already controlled by another tunnel. Nested emulation inside
the Windows VM is rejected as release evidence because it adds another NAT and
tunnel boundary.

Candidate 18 physical ARM64 Wi-Fi and Beeline tests remain open. AWG 3.1,
AWG2, default/fallback, Smart DNS, Private DNS, IPv4/IPv6 leak, Doze/OEM and
endurance results from older candidates do not transfer to these APK bytes.

## Release decision

Candidate 18 is the current signed private candidate. Candidate 17 is rejected,
and candidate 16 remains immutable historical Gate F evidence. Gate F has not
been regenerated for candidate 18. No tag, GitHub Release, public asset, Store
submission, stable-pointer change or production promotion occurred.

This work order changes no completion level. Distribution remains `I4=5`,
`I3=319`, `I2=20`, `I1=34`, `I0=0` across `378` rows. It replaces current
candidate identity only and preserves every unrun physical, connected Windows,
origin, provider, Operator, legal, rollback, performance and aggregate P0 gate.
