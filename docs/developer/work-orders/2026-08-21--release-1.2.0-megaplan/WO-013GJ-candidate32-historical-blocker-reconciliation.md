# WO-013GJ — candidate.32 historical-blocker reconciliation

Status: `PASS_FOURTEEN_HISTORICAL_ROWS_TARGET_CANDIDATE32; LEVELS_AND_GATE_F_UNCHANGED`

Observed: `2026-09-04T01:44:13Z`

Production/public mutation: `NONE`

## Outcome

Complete the bounded follow-up from WO-013GI by reconciling fourteen ledger
rows whose strongest proof remains candidate.20/21 or candidate.16 history,
but whose future action still named the predecessor candidate or did not make
the candidate.32 boundary explicit.

The historical evidence remains attached to the candidate that produced it.
Only the current blocker and next action move to exact private signed
candidate.32. This work order adds no runtime, device, origin, deploy or
promotion proof.

## Reconciled rows

| Row | Retained history | Current candidate.32 boundary | Level |
|---|---|---|---|
| `REL/WIN-005` | Candidate.20/21 Windows UI, service and default-runtime history | Login-startup, service-readiness and network-availability timing | `I3` unchanged |
| `REL/SEC-001` | Candidate.20 Windows 11 owner-session history | Full identity and privilege-boundary matrix | `I3` unchanged |
| `REL_DOD/DOD-12` | Candidate.21 bundle and bounded static-privacy history | Physical bundle, privacy replay, encrypted upload and live ingest | `I3` unchanged |
| `REL_DOD/DOD-17` | Candidate.21 limitations history | Physical Android OEM, network, Private DNS, leak and endurance matrix | `I3` unchanged |
| `OBS/OBS-005` | Candidate.21 logging/static-privacy history | Physical Android/Windows journals, bundle and privacy replay | `I3` unchanged |
| `OBS/OBS-006` | Candidate.21 rejection/static-privacy history | Deployed ingest, physical runtime and privacy replay | `I3` unchanged |
| `OBS/OBS-010` | Candidate.21 planted-secret/static corpus history | Physical and deployed-ingest corpus replay | `I3` unchanged |
| `OBS/OBS-075` | Candidate.21 property-suite history | Physical runtime-output property replay | `I3` unchanged |
| `OBS/OBS-076` | Candidate.21 golden-manifest history | Physical bundle plus encrypted upload and ingest | `I3` unchanged |
| `FRKN_AWG/AWG-01` | Candidate.21 synthetic/static history | Candidate-bound privacy and physical runtime replay | `I3` unchanged |
| `FRKN_AWG/AWG-08` | Predecessor manual-stage wording | Physical Windows/Android lab activation and clean restore | `I1` unchanged |
| `FRKN_PLAN/W6-03` | Candidate.20/21 Windows lifecycle history | Candidate.32 clean install, forced-kill, sleep/resume, reboot and recovery | `I1` unchanged |
| `FRKN_PLAN/W6-04` | Candidate.16 emulator and candidate.21 open-device history | Candidate.32 network, Doze, Private DNS and IPv6 leak matrix | `I1` unchanged |
| `FRKN_PLAN/W6-05` | Predecessor manual-stage wording | Physical Android/Windows lab exit, telemetry and restore | `I1` unchanged |

Every `next_action` in the full ledger now avoids candidate.21 as the future
target. Candidate.21 can still appear in `status` and `evidence` where it is
the truthful provenance of predecessor results.

## Evidence boundaries

WO-013GF remains the private signed candidate.32 supply authority, WO-013GG
remains the exact-source Gates A–E and Gate F authority, WO-013GH remains the
Android static authority, and WO-013GI remains the seven-row current-authority
reconciliation. This work order only closes the residual historical/current
wording split.

Gate F remains `BLOCKED 2/17/0`. The unsigned-Windows direct-beta owner
exception remains explicit. No candidate.32 install, managed AWG3.1/AWG2,
Smart DNS, physical Android, exact origin, provider, Operator, legal,
runtime-rollback, public asset, Store object, tag, stable pointer or promotion
is claimed here.

## Verification

```text
ledger rows -> 378
unique (plan,id) keys -> 378
duplicate keys -> 0
changed historical/current-boundary rows -> 14
next_action values targeting candidate.21 -> 0
index changes -> 0
distribution -> I4=7 / I3=320 / I2=19 / I1=32 / I0=0
Gate F -> BLOCKED 2/17/0; not regenerated
```

## Evidence

- normalized record:
  `evidence/013GJ-candidate32-historical-blocker-reconciliation/013GJ-candidate32-historical-blocker-reconciliation.json`;
- normalized record SHA-256:
  `4ad30edc62c63f28d236577dc6bc93c450c75019acaeadcfcdb872b543644cf9`.

The normalized record contains no credentials, private key, provider payload,
customer data or connection material.

## Follow-up

Stop further wording-only reconciliation. Execute the exact candidate.32
runtime matrices when an isolated target is available: managed Windows first,
then physical Android Wi-Fi/Beeline, packaged AWG3.1/AWG2, Smart DNS,
network/lifecycle/leak/restore, named origins and final approval rows. Do not
transfer predecessor runtime credit by label.
