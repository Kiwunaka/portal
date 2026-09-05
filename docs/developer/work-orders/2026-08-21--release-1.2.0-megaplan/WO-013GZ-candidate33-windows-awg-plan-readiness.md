# WO-013GZ — candidate.33 Windows AWG plan readiness

Status: `READY_READ_ONLY_PLAN; TEMPORARY_CONTROL_PLANE_APPLY_NOT_AUTHORIZED; GATE_F_BLOCKED`

Superseded for current VM identity/authorization by WO-013HL (2026-09-05).
The owner authorized bounded temporary switching; fresh VM digest differs
from this historical target. HL retains real APPLY/default-restore results,
with client connection still NOT_RUN.

Observed: `2026-09-04`

Production/public mutation: `NONE`

Local preparation update, 2026-09-04: the binder now rejects shared AWG
scope before any guarded write and creates only install-based selectors.
Legacy account selectors, other devices/cohorts and AWG defaults/carrier rules
require separate operator review. PLAN below remains historical target
readiness, not proof that the new APPLY precondition passes. Config drift
before the rollout write also stops the bind; this is not an atomic rollback
of any earlier material write. See the canonical binder procedure in
`docs/operations/deployment-and-access.md`. Local binder/selector and release
script checks pass `65 tests + 21 subtests`; link and diff checks pass.
No remote command or APPLY was run for this preparation, and packaged
AWG/DNS/egress proof remains open pending explicit temporary-switch authority.

## Outcome

After exact candidate.33 connected-uninstall cleanup and clean `11/11`
reinstall, fresh guarded read-only PLAN runs resolve the same one entitled
Windows target for both `awg31_lab` and `awg2_lab`. Both plans confirm exact
app version `1.2.0+4053`, confirmed install identity, available source material
and no entitlement extension. Neither plan returns a raw user/device identifier
or connection material.

This proves control-plane readiness only. No APPLY, profile fetch, packaged
Core activation, TUN, DNS, egress, recovery or cleanup runtime credit is
assigned. A temporary guarded owner-lab control-plane APPLY remains a separate
production mutation and is not authorized by the current candidate/docs merge
authority.

## Exact boundary

| Fact | Exact value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.33` |
| Platform / client / Core | `f530005...5bc1` / `6ab1bca...735e` / `cd8f0f4...884d` |
| Windows setup | `250622f7...3580` |
| Installed state | `11/11`, Automatic LocalSystem service, no UI/TUN/diagnostic CLI |
| Confirmed app-first install digest | `fe746f13...75d0` |
| Target selection | `confirmed_install_hash`, one matched Windows target |
| Entitlement | active; extension not needed and not applied |
| Raw identifiers/material returned | `false` |

## Plans

| Profile | Result | Source material | APPLY | SHA-256 |
|---|---|---|---|---|
| `awg31_lab` | `PLAN ok=true` | available | `false` | `9543f467...1fc5` |
| `awg2_lab` | `PLAN ok=true` | available | `false` | `53209f60...abe5` |

The external readiness index is:

```text
E:/POKROV-tools/release-evidence/1.2.0-candidate33-windows-awg-plans-post-reinstall-2026-09-04/candidate33-windows-awg-plan-index.json
SHA-256 df387c1f6474509c932a934507f1515fcbca57c67b43eece5a734355fc98af19
```

The platform-retained summary is
`evidence/013GZ-candidate33-windows-awg-plan-readiness/013GZ-candidate33-windows-awg-plan-readiness.json`,
SHA-256 `2222185fe51ef6075e4abf288d3c61e98b365b287eb90a3dd5b41592008c70b7`.

## Required authorized sequence

When separate temporary APPLY authority exists, run:

1. guarded fresh PLAN and APPLY of `awg31_lab`;
2. exact candidate.33 profile refresh and packaged Windows
   service/Core/TUN/DNS/egress/recovery proof;
3. guarded default restore plus client disconnect and zero-TUN readback;
4. guarded fresh PLAN and APPLY of `awg2_lab`;
5. the same exact packaged runtime proof;
6. guarded default restore plus zero-material/zero-TUN cleanup readback.

Any failed APPLY, profile revision mismatch, false green state, missing cleanup,
route/DNS residue or target-identity drift is a non-PASS result. The two
profiles must not receive credit from one cached runtime profile.

## Release impact

No ledger level changes. `FRKN_PLAN/W3-02` and `FRKN_AWG/AWG-03` remain below
exact packaged runtime completion. Gate F remains `BLOCKED 2/17/0`; no Gate G,
candidate byte, deploy, public asset, Store object, stable pointer or production
runtime changed.
