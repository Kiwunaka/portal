# WO-013CJ — candidate.8 isolated rollback rehearsal

Status: `PASS_LOCAL_EXACT_CANDIDATE8_PORTAL_CLIENT_ROLLBACK`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.8`
Production/external mutation: `NONE`

## Outcome

Repeat the real portal projection and client stable-pointer mechanisms against
the signed candidate.8 tuple inside an isolated local fixture. The exact
platform/client/Core revisions pass this sequence:

```text
1.1.6+20260819 -> pokrov-1.2.0 -> 1.1.6+20260819
```

The harness independently verifies the signed manifest and source tuple,
generates candidate handoff SHA-256
`53c9f8529fb92231f2f8ee312252de1170369ea6ab5464b15fe67d9defbe9c01`
and binds artifact-set SHA-256
`f3f64e4eeb137969b4bce23e6d980192c71243b4505a571062ad3d2e4e3c5164`.
Client validation, dry-run, forward atomic switch, reverse atomic switch and
final stable validation all pass. The final pointer returns byte-identically
to retained stable handoff
`563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f`.
The portal projection also returns byte-identically and preserves an unrelated
setting.

## Evidence ceiling

- `REL_DOD/DOD-18` and `FE/P12-130` remain `I3` with stronger exact
  candidate.8 local evidence.
- `REL_GATE/GATE-F` remains `I3` and `BLOCKED` at `6 PASS / 13 non-PASS / 0
  FAIL`. Local rehearsal does not replace a separately authorized runtime
  pointer/kill rollback, external backup/receipt, current/Brain readback or
  post-rollback health proof.
- Tracked client pointer/catalog, portal runtime, production, public release
  and stable pointer are unchanged.
- The owner's active Hiddify TUN, physical Android and LDPlayer were untouched.

No public release, deploy, payment/provider action, runtime pointer or stable
promotion occurred.

## Evidence

The full external report is retained outside Git at:

```text
E:\POKROV-tools\release-candidates\pokrov-1.2.0-candidate.8\rollback\candidate8-rollback-rehearsal.json
```

Its SHA-256 is
`d1fa472aa1a0f2425c0281b42b9fb9011d452509814810d956b8dc579b6fecea`.
The generated handoff is retained beside it with SHA-256
`53c9f8529fb92231f2f8ee312252de1170369ea6ab5464b15fe67d9defbe9c01`.

Normalized evidence is
`evidence/013CJ-candidate8-local-rollback/013CJ-candidate8-local-rollback.json`.
Its canonical LF SHA-256 is
`cc42f91908fdf52f37211577900b2b2d5eeb5e45fa927d5a09c3ff8a4198be3a`.
It contains no address, hostname, credential, key, customer data, remote
payload or provider response.

## Verification

```text
tests/test_release_1_2_candidate_rollback_rehearsal.py -> 5/5 PASS
candidate.8 signature/source/handoff binding -> PASS
portal forward/reverse/byte identity/unrelated setting -> PASS
client initial/dry-run/forward/reverse/final stable readback -> PASS
exact platform/client/Core/release-index worktrees -> CLEAN
production/public/stable mutation -> NONE
```

## Next action

Keep the Gate F row manual until the owner separately authorizes the real
runtime pointer/kill rollback and current/Brain post-rollback readback. Continue
other candidate.8 live-device and release gates without treating this local
fixture as production proof.
