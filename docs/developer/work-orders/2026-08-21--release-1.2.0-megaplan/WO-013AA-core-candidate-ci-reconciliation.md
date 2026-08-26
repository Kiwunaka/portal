# WO-013AA — Candidate Core CI reconciliation

Status: `CANDIDATE_CORE_PLATFORM_ABI_SECURITY_PROVED_CROSS_REPO_CONTROL_RECONCILED`
Phase: `11`
Rows: `REL_DOD/DOD-10`
Candidate: `pokrov-1.2.0-candidate.1`
Deployment: `NOT_REQUIRED_NOT_RUN`
Recorded: `2026-08-26`

## Goal

Reconcile the red aggregate CI status on the exact Core source bound by the
signed candidate manifest without calling the red run green, changing product
bytes, rebuilding the candidate or weakening the cross-repository contract.

## Exact candidate binding

The independently verified signed manifest SHA-256
`84695f6e318814bc2d1e9de1c9adc3aa4277015d551c5462b197664e574c28d6`
binds:

- Core `344b317a7a09eca7943a93866b193553538bd8f6`;
- client `a74d2aea5aed62f5c31d3a0bbc258e408cebe3bd`;
- platform `8bed966e64e23527da982f3fcfb1b9e48ce6f408`;
- public release index `c1d617093692b05d2a12ae8ad8394e5570b0df8a`.

The client promotion line remains exactly `a74d2aea...` and its installed
LDPlayer x86_64 APK SHA-256
`7d7a22b23a33811326c452fdd23d19bbb02aae0b3f6bd74a6753e38f222675ed`
matches the candidate manifest. No candidate source or artifact identity is
replaced by this work order.

## Exact red run

Core push run `32944235783` remains `failure` after attempt 3. It must not be
reported as a successful aggregate run. Its product jobs on exact source
`344b317a...` are independently green:

- `test`: tests, vet, race, reachable `govulncheck`, staticcheck, parser fuzz,
  dependency/license SBOM generation — `SUCCESS`;
- `android-artifact-reproducibility`: two builds and byte comparison —
  `SUCCESS`;
- `windows-artifact-reproducibility`: two builds, 15-export contract and
  100-cycle proxy backtest — `SUCCESS`;
- `apple-source-build`: two source builds and deterministic comparison —
  `SUCCESS`.

Only `release-contract` failed. Attempt-3 job `98265239259` checked out the
private client without Git LFS, so the runner saw the LFS pointer instead of
the pinned 107,388,169-byte AAR and correctly stopped with
`Pinned Android Core artifact size does not match runtime-artifacts.seed.json`.
The local client file size/SHA-256 remain exactly
`107388169` / `da3ea37834b688abac5c276f4ca9c2cdcc8e32b97edf5062913fc4f3fea6aba9`.
This is a real CI-control defect, not an infrastructure skip and not evidence
that the product job failed.

## Product-identical CI control

Core PR 4 added LFS checkout plus an explicit bound-source materialization
step. PR head `ec503cb0738aeba336ac6a0d3438b9d32326ac28` passed all five jobs in
run `32946337754`, including `Materialize bound Core source authority` and the
full cross-repository parity check. It merged as
`9b94e0bda7e454536e8fa9b4519f2281211798e0`.

The exact diff from candidate Core `344b317a...` to control merge
`9b94e0bd...` changes only `.github/workflows/ci.yml` (`29` insertions, `1`
deletion). No Go source, module, license, ABI, build script or artifact input
changes. Post-merge CI runs `32947194845` and `32947422554` are `SUCCESS`;
the latter repeats all five jobs and the release-contract job materializes the
client-bound Core authority before validation.

The evidence therefore remains split honestly:

- exact candidate-source product/platform/security jobs: `SUCCESS` in the
  red aggregate run;
- old exact-source aggregate status: `FAIL_CI_CONTROL_MISSING_LFS`;
- product-identical corrected cross-repository control: `SUCCESS`;
- candidate device/origin/public promotion: still open.

## Ledger decision

`REL_DOD/DOD-10` advances `I2 -> I3`. The row requires Core platform builds,
ABI and security checks; exact-source product jobs and the product-identical
corrected hosted control now prove that scope. It does not advance to `I4`
because the physical Android/Windows runtime, exact origin and public
same-byte promotion gates remain open.

The current distribution becomes `I4=1`, `I3=309`, `I2=16`, `I1=37`,
`I0=14`; 310 rows are at or above `I3`, 67 remain below `I3`, and the pending
stage split becomes `0/32/14/21`.

## Next action

Keep run `32944235783` retained as the red historical control. Do not rerun it
again: its workflow revision can never fetch the LFS AAR. Use current Core CI
for future controls, but keep candidate product source and artifact hashes
bound to `344b317a...`. Execute the physical Beeline and clean-Windows exact
candidate gates before any `I4` claim.
