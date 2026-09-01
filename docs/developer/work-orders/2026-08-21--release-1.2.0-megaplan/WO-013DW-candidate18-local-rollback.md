# WO-013DW — Candidate 18 isolated portal/client rollback rehearsal

Status: `PASS_LOCAL_EXACT_CANDIDATE18_PORTAL_CLIENT_ROLLBACK`

Observed: `2026-09-01T06:37:03Z`

## Scope

Verify the signed candidate.18 manifest, receipt, detached signature and exact
source tuple, generate its post-sign operational handoff, and execute the real
portal projection plus client stable-pointer mechanisms inside one disposable
local fixture:

```text
1.1.6+20260819 -> pokrov-1.2.0 candidate.18 -> 1.1.6+20260819
```

No tracked client catalog or pointer, portal runtime, production service,
public release, stable pointer, physical phone, LDPlayer or Windows VM state is
changed.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.18`, `1.2.0+4049` |
| Platform source | `d6898e63c5c9ab7dd267b9d5150b54196f99d967` |
| Client source | `820ca1016bdfef0f44a1d217e3804adb9b365ca5` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `5dc25bdde2ce146c65c37c08bf96afebe722f759` |
| Signed manifest SHA-256 | `d686238265e19b7a63759b735e18a49d8910f1885098dc923c5f1c51130f9a56` |
| Detached signature SHA-256 | `a5584da629e4562b2ec6d79824f5d121e691f8b7e3ce0a83475f6a00464b6324` |
| Signing receipt SHA-256 | `42a4c7381dc8dab6cdb226476f0ab316222bd96f16994d75e10f22f0436fe83d` |
| Candidate handoff SHA-256 | `bb98ad813c110c1390dbaa62746a2dd70470accb17ae9a72e1f526c28d40f48d` |
| Candidate artifact-set SHA-256 | `0bab180ee351cea74933ac80a5207fc8bd378940953799b423d8ff7838f68e04` |
| Retained stable handoff SHA-256 | `563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f` |

The harness materializes exact committed source snapshots from all four
repositories, verifies the Ed25519 signature against the manifest-bound public
keyring and confirms all six artifact bindings. It deliberately does not
require physical-device state because this rehearsal changes only disposable
portal and pointer fixtures.

## Results

The portal consumer applies the candidate.18 projection, observes Android
artifact SHA-256 `4983209204ba4a1090483ffb3c6f6741261d80215ff1a2703e951093c5166297`
and Windows artifact SHA-256
`21dca69a4cffe9648bf9788c1279606896c798b32617dd88fa0d9c1e9c1bf2d3`,
then restores the initial fixture bytes exactly. Its before and rollback
SHA-256 values are both
`c4d3ea78d382d6ca6ab7d1d4d5367edc4478a9d96d91527ec2000df80e38ecd7`.
An unrelated setting survives both transitions.

The client channel passes initial validation, no-apply dry-run, forward switch
to candidate.18, reverse switch to `1.1.6+20260819` and final stable
validation. Stable bytes restore exactly. Forward receipt SHA-256 is
`82e87de46ec54b7297e6668d98e09d9e437d985c5e3d363e275d164dbefbfbac`;
rollback receipt SHA-256 is
`36f9a38d4e30e3458766b640ef2b03906366e3247935a8099c9824e991ac294e`.

## Verification and evidence ceiling

The focused rollback/PB-14 suite passes `16/16`. Exact platform, client, Core
and release-index worktrees remain clean, and the disposable fixture is
removed by the harness.

`REL_DOD/DOD-18` and `FE/P12-130` remain `I3`, now with exact candidate.18
local evidence. This is not a production, public or origin proof. A real
runtime pointer/kill rollback still requires a guarded backup and receipt,
current/Brain-origin readback and post-rollback health. Gate F remains
`NOT_RUN` for candidate.18 and Gate G remains unauthorized.

The 378-row distribution remains `I4=5`, `I3=319`, `I2=20`, `I1=34`,
`I0=0`.

## Evidence

- normalized record:
  `evidence/013DW-candidate18-local-rollback/013DW-candidate18-local-rollback.json`;
- normalized record SHA-256:
  `ef27b48eba1a1eb93c5d07b24f7df0cebe34f4a62d81edf6b8335cb441dbff2d`;
- external signed-binding SHA-256:
  `873347af177d31114e1ef9e81a50ea3437509ad709dfbaccb8fd423e9b557ddd`;
- external generated handoff SHA-256:
  `bb98ad813c110c1390dbaa62746a2dd70470accb17ae9a72e1f526c28d40f48d`;
- external rollback report SHA-256:
  `35578c6a6c5b86362e20cbf622e929970639035911bd720d488456d01be920de`.

The external outputs remain under the private candidate.18 rollback evidence
directory. They contain no signing private key, credential, customer data or
device identifier.

## Next action

Keep public and stable pointers unchanged. Complete the candidate.18 physical
Android and connected-Windows matrices before regenerating Gate F. Execute a
real runtime pointer/kill rollback only under its separate production guard.
