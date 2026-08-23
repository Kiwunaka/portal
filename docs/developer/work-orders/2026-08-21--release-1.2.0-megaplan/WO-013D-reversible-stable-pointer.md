# WO-013D — Reversible stable pointer and rollback catalog

Status: `COMPLETE_LOCAL_I3`
Phase: `11`
Row advanced: `FE/P12-130`
Promotion: `NOT_REQUESTED`

## Outcome

Turn the retained client release pointer into a reversible, fail-closed source
contract without creating a 1.2.0 candidate, mutating retained release bytes,
syncing runtime config or claiming a deployed rollback drill.

## Implemented boundary

- `config/release-rollback-catalog.seed.json` binds the root stable pointer and
  exact immutable rollback targets. The current entry is retained public
  `1.1.6+20260819`; the exact pointer and versioned handoff have the same
  SHA-256 and cover Android plus Windows.
- `scripts/set-release-stable-pointer.ps1` validates every catalog identity,
  version, schema and digest. It rejects paths escaping the artifact root and
  targets absent from the catalog.
- The switcher defaults to validation/dry-run. `-Apply` requires optimistic
  locking on the current release, a same-filesystem backup outside
  `artifacts/releases`, a new receipt path, atomic replacement and exact
  readback. It never rewrites a versioned handoff.
- The isolated contract proves dry-run, stale-lock rejection, exact forward
  backup/switch, exact reverse backup/rollback and tamper rejection. No test
  writes the retained release tree.
- The standard client seed gate invokes the rollback contract on Linux/Windows
  PowerShell paths. Canonical client and platform release/rollback docs state
  the same authority and evidence ceiling.
- The standard gate also found 30 `part` files in `app_shell.dart`. The pure
  `ruDays` helper is now a normal imported/exported library, restoring the
  guarded ceiling of 29 without weakening the boundary.

## Index decision

`FE/P12-130` advances `I0 -> I3`: the rollback catalog and reversible stable
pointer are locally implemented and regression-tested. `REL_DOD/DOD-18`
remains `I0` because portal plus client-channel rollback for one exact
candidate has not run.

Distribution becomes `I3=301`, `I2=21`, `I1=40`, `I0=15`; `76` rows remain
below `I3`. Stage split becomes `5/33/17/21`.

## Local proof

- Retained pointer plus isolated rollback contract: PASS, five synthetic cases.
- Client release-v2 CI contract and repository hygiene: PASS.
- Focused client presentation boundary: PASS, 29 parts.
- Focused Russian plural tests: `4/4` PASS.
- Full cross-repository client seed gate: PASS, including v2 generation,
  observability parity, source logging, rollback, CI, hygiene, presentation,
  performance and docs contracts.
- Platform docs contracts: `32/32` PASS; platform context audit: PASS.
- Client `artifacts/releases/**` diff: empty.

Machine evidence:
`evidence/013D-reversible-stable-pointer/013D-reversible-stable-pointer.json`.

## Evidence ceiling

The 1.2.0 candidate is not created and therefore is not a catalog target. The
public release index remains `BLOCKED_BY_ACCESS`. No actual stable pointer,
runtime config, portal deploy, static site, device, origin, public asset,
announcement or promotion was changed. The exact-candidate rollback drill
remains `NOT_RUN` and mutation authority remains `NOT_AUTHORIZED`.
