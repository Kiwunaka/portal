# WO-013EE — candidate.20 active-ledger and PB-14 reconciliation

Status: `PASS_CURRENT_CANDIDATE_TRUTH; PB14_FAIL_CLOSED_PHYSICAL_IDENTITY_ABSENT`

Observed: `2026-09-01`

Production/public mutation: `NONE`

## Outcome

Audit every ledger row below `I3` after WO-013ED and reconcile the active
instructions with the current exact candidate 20. The ledger contains `378`
unique rows: `51` remain below `I3`. Nearly all require a physical device,
remaining Windows lifecycle, a named origin, a real provider/Operator/legal
decision, comparable performance or post-promotion evidence.

The audit finds `23` active next-action references that still direct future
work to candidate 6 or candidate 18. Thirty rows also contain current status or
evidence text that can now be replaced by candidate 20 proof from WO-013EA–ED.
The stale active actions are corrected to candidate 20. Historical candidate
6/16/18 observations remain identified as history and transfer no runtime
credit.

No index changes. Distribution remains `I4=7`, `I3=320`, `I2=19`, `I1=32`,
`I0=0` across `378` rows.

## Current evidence replacements

Candidate 20 evidence replaces older current-truth text only where the new
candidate has direct proof:

- signed supply, locks, manifest, receipt, SBOM/provenance and exact hosted
  replay use WO-013EA;
- Windows 11 ordinary UI/LocalSystem service, authenticated IPC, default
  TUN/DNS/egress, disconnect rollback and migration use WO-013EA;
- source privacy/property/golden coverage uses WO-013EB;
- six-artifact and Windows staging static binding uses WO-013EC;
- Gate B, Gate D, Smart-DNS source behavior, complete local quality and static
  performance use WO-013ED.

Candidate 16/18 AWG, origin, LDPlayer, rollback and performance observations
remain historical. Their active next actions now require candidate 20 rather
than silently requesting an obsolete build.

## PB-14 current preflight

The exact candidate 20 signer artifact is read back again:

- manifest `046d3312...770a`, `6884` bytes;
- detached signature `f5e81d31...90ea`, `64` bytes;
- signing receipt `47429c2c...9479`, `589` bytes;
- release-index keyring source `61ad0b0...`.

A bounded signed-supply input intentionally records
`physical_phone_install_binding=NOT_RUN`. The current PB-14 gate verifies the
candidate inputs through the physical boundary and returns exit `1` with:

`PB-14 candidate gate: FAIL: exact installed Android build identity is absent`

This is expected fail-closed behavior, not a candidate defect and not a PB-14
PASS. The gate does not reuse candidate 6 build `4046`, does not stage an
incident and does not request rollback. The focused PB-14 and rollback harness
tests pass `16/16`.

PB-14, DOD-23 and Gate F therefore remain non-PASS until the exact candidate
20 ARM64 artifact is installed on a physical Android device and its installed
base bytes/version are hash-bound to the signed artifact.

## Ledger effect

Updated rows:

- release/supply/Windows/performance: `DEP-001`, `WIN-004`, `WIN-005`,
  `REPO-001`, `PERF-001`, `SEC-001`, `DOD-15`, `DOD-17`, `DOD-20`;
- observability: `OBS-075`, `OBS-076`, `DOD-23`, `PB-14`;
- frontend/release: `P12-022`, `P12-023`, `PR-09`, `PR-10`;
- FRKN/AWG/Smart-DNS: `ADOPT-05`, `AWG-03`, `AWG-08`, `AWG-10`,
  `SMARTDNS-01`, `W1-03`, `W3-02`, `W3-03`, `W6-03`, `W6-04`, `W6-05`,
  `W9-02`, `W9-05`.

After reconciliation, active next-action references to pre-candidate-20 builds
are `0`. Historical evidence remains retained in the evidence column and work
orders.

## Verification

- exact candidate 20 PB-14 preflight:
  `FAIL_CLOSED_EXPECTED`, exit `1`, missing exact installed Android identity;
- PB-14 plus rollback harness tests: `16/16 PASS`;
- ledger parse: `378` rows, `378` unique `(plan,id)` keys, eight columns;
- pre-20 active next-action scan: `23 -> 0`;
- level changes: `0`;
- host VPN/routes/DNS, VM, LDPlayer and phone: `NOT_USED`.

## Evidence

- normalized reconciliation:
  `evidence/013EE-candidate20-active-ledger/013EE-candidate20-active-ledger-reconciliation.json`;
- normalized reconciliation SHA-256:
  `45fa8ef2b8919499b6a79c21337a37a7a7124c873267defde333b0b5711e19ef`;
- current signed-supply/no-physical-binding input:
  `evidence/013EE-candidate20-active-ledger/013EE-candidate20-signed-supply-no-physical-binding.json`;
- signed-supply input SHA-256:
  `462abce6f2c5a760b15cafd036a5d367681fd939df57942da8763a67bcacc330`.

The records contain no credential, raw connection material, customer/provider
payload or device identifier.
