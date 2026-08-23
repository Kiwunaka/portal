# WO-004B2 — Core Release CI Matrix

Status: `COMPLETE_I3`
Classification: `ACTIVE_EXECUTION`
Phase: `02`
Lane: Core source/build/reproducibility evidence
Depends on: `WO-004B`, `WO-006C`
Production/external actions: `NOT_AUTHORIZED`

## Bounded outcome

Close `REL/CORE-001` as a locally proved release-CI source contract. The Core
repository must describe and fail closed over the supported release platforms,
ABI, race/security gates, parser fuzzing, source SBOM, two-build comparison and
bounded provenance without treating an unrun hosted job as artifact proof.

POKROV 1.2.0 ships Android and Windows Core artifacts. Apple is a source-build
lane pending hosted/device proof. Linux runs tests and analysis only and has no
shipped 1.2.0 Core artifact.

## Implemented matrix

- Linux/quality: complete root `go test ./...`, embedded AWG/daemon/libbox/TLS
  suites, focused vet/race/reachable `govulncheck v1.7.0`, pinned Staticcheck
  `v0.7.0` families `SA2*`, `SA5*`, `SA6*`, and a 30-second config/profile
  no-panic fuzz target.
- Supply chain: pinned CycloneDX Go module `v1.10.0` emits timestamp/serial-free
  root and sing-box SBOMs with dependency and detected-license inventory.
- Android: Ubuntu builds the AAR twice, validates `armeabi-v7a`, `arm64-v8a`,
  `x86`, `x86_64`, compares complete file trees and retains bounded evidence.
- Windows: pinned MinGW-w64 builds the DLL twice with the client-pinned Cronet,
  validates the exact export contract, runs the active client's 100-cycle
  current-source proxy backtest, compares trees and retains bounded evidence.
- Apple: macOS 15 builds the XCFramework twice to isolated output roots,
  compares trees and retains source-build evidence.

`scripts/new-release-artifact-evidence.ps1` requires a clean Git source,
byte-identical build roots and present SBOMs. It records deterministic tree,
source, Go/release/contract and SBOM hashes. Its fixed ceiling is
`PRE_CANDIDATE_LOCAL`, `candidate_proven=false`, `promotion_authorized=false`.
The workflow uploads evidence/SBOM JSON only; it has read-only repository
permissions and no signing, attestation, release or publication action.

## Defects found and corrected

The former workflow proved only Ubuntu tests and focused vet/race/vulnerability
checks. It had no Android, Windows or Apple build jobs, no two-build comparison,
SBOM, parser fuzz or retained provenance. `scripts/test.ps1` also covered a
narrow root package list; switching to the complete module exposed three real
compile/vet defects in the ray2sing command and two tunnel-service diagnostics.
Those defects were corrected and the affected Go files were formatted.

The Android builder now resolves `.exe` only on Windows, so its gomobile tools
work on Ubuntu. The Apple builder accepts an isolated output root. A broad
Staticcheck diagnostic exposed inherited style/deprecation/dead-code debt; the
release gate deliberately uses the security/correctness families above instead
of expanding 1.2.0 into a big-bang cleanup.

## Verification — 2026-08-22

- Canonical `pwsh scripts/test.ps1` with Go `1.25.13`: `PASS`, including brand,
  15-export ABI, observability, AWG2, release-CI contract, full root module and
  embedded AWG/daemon/libbox/TLS/uTLS suites.
- Exact CI Staticcheck package/family set: `PASS`.
- Config parser fuzz, local five-second probe: `66,088` executions, `151` new
  interesting inputs, no panic, `PASS`.
- CycloneDX root and sing-box SBOM generation: command exit `0`; repeated output
  SHA-256 is byte-identical. License/version detection warnings are retained and
  explicitly prevent a zero-warning legal-clearance claim.
- Evidence writer fixture: matching trees accepted; one-byte mismatch rejected.
- Release-CI contract, workflow YAML parse and Core `git diff --check`: `PASS`.
- A first full-gate attempt under Windows PowerShell 5 failed because that
  shell lacks the required `ConvertFrom-Json -Depth`; it is retained as
  `NOT_CREDITED_NONCANONICAL_SHELL`. The canonical `pwsh` rerun passed.
- Hosted GitHub Android/Windows/macOS execution, exact clean candidate artifacts,
  physical devices, signing, publication and RU-origin proof: `NOT_RUN`.

Machine evidence:
`evidence/004B2-core-release-ci-matrix/004B2-core-release-ci-matrix.json`.

## Ledger decision

- `REL/CORE-001`: `I2 -> I3`, `LOCALLY_PROVED`. The fail-closed source/workflow
  contract and local quality/SBOM/evidence primitives are implemented and pass.
- `REL_DOD/DOD-10`: remains `I2`, `IMPLEMENTED_PARTIAL`. Hosted Android,
  Windows and Apple jobs plus exact-candidate evidence have not run.

Current distribution: `I3=277`, `I2=35`, `I1=45`, `I0=20`; `100` rows remain
below `I3`. Stage split: `30/32/17/21`. The evidence ceiling is local `I3`; no
candidate, artifact promotion, signing, deployment or external mutation occurred.
