# WO-013CZ — candidate.13 isolated rollback rehearsal

Status: `PASS_LOCAL_EXACT_CANDIDATE13_PORTAL_CLIENT_ROLLBACK`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.13`
Production/external mutation: `NONE`

## Outcome

The signed candidate.13 tuple passes the real portal projection and client
stable-pointer mechanisms inside an isolated local fixture:

```text
1.1.6+20260819 -> pokrov-1.2.0 -> 1.1.6+20260819
```

The harness verifies the detached Ed25519 signature, receipt, manifest-bound
public keyring, exact source tuple and all six signed artifacts. It generates
the post-sign operational handoff SHA-256
`6d65772d00cca27610a95e2eea285b489f54b08a34ce6f88d711cc2f3d8fa6e9`
and artifact-set SHA-256
`d9bba178d184958f9577ac39e3e736ef081677297cc67dc5bcffcb327edb4f69`.
The generated handoff differs from the retained assembly handoff only by the
release-index source revision: it replaces assembly revision `8581a46...`
with exact signed revision `440f3be...`; artifact bytes are unchanged.

Client validation, dry-run, forward switch, reverse switch and final stable
validation all pass. The final pointer returns byte-identically to stable
handoff SHA-256
`563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f`.
The portal projection also restores byte-identically and preserves an unrelated
setting.

## Fail-closed harness correction

The first attempt stopped before mutation because the shared candidate
validator required an exact physical-phone install binding. That binding is a
valid PB-14/Gate F requirement but is unrelated to an isolated pointer
rollback. The validator now remains strict by default; only the rollback
harness opts out and instead validates the internally consistent signed
manifest package/build identity. PB-14 and Gate F still require physical-phone
binding, and no physical evidence is fabricated or inherited.

## Evidence ceiling

- `REL_DOD/DOD-18` and `FE/P12-130` remain `I3` with stronger exact
  candidate.13 local evidence.
- Gate F remains `NOT_RUN_MISSING_EXACT_ARM64_INSTALL_BINDING`; this local
  rehearsal does not replace the separately authorized runtime pointer/kill
  rollback, external backup/receipt, current/Brain readback or post-rollback
  health proof.
- Tracked client pointer/catalog, portal runtime, production, public release,
  stable pointer, physical Android and LDPlayer are unchanged.

No public release, deploy, tag, payment/provider action, runtime pointer or
stable promotion occurred.

## Evidence

External outputs are retained at:

```text
E:\POKROV-tools\release-candidates\pokrov-1.2.0-candidate.13\rollback\candidate13-rollback-handoff.json
E:\POKROV-tools\release-candidates\pokrov-1.2.0-candidate.13\rollback\candidate13-rollback-rehearsal.json
```

Their SHA-256 values are respectively
`6d65772d00cca27610a95e2eea285b489f54b08a34ce6f88d711cc2f3d8fa6e9`
and `d068d061159f4ab98726782806be983d9ba888e41a8175ace9b0301e4a2e038f`.
Normalized evidence is in
`evidence/013CZ-candidate13-local-rollback/`; the normalized rollback record
SHA-256 is
`25a511c8218eb867d8082311853c50a195165ff52f234a734ed1ce3d7289343b`.

## Verification

```text
PB-14 plus rollback focused tests -> 13/13 PASS
candidate.13 signature/source/handoff binding -> PASS
portal forward/reverse/byte identity/unrelated setting -> PASS
client initial/dry-run/forward/reverse/final stable readback -> PASS
exact platform/client/Core/release-index worktrees -> CLEAN
production/public/stable mutation -> NONE
```

## Next action

Keep Gate F manual until exact candidate.13 ARM64 is installed and bound on a
physical device. Continue clean Windows and origin gates; a real runtime
pointer/kill rollback still requires separate authorization and retained
external readback.
