# WO-013AF — Exact candidate.3 portal and client-channel rollback rehearsal

Status: `PASS_LOCAL_EXACT_CANDIDATE_PORTAL_CLIENT_ROLLBACK`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.3`
Recorded: `2026-08-27`
Production/runtime mutation: `NOT_PERFORMED`
Public/stable mutation: `NOT_PERFORMED`

## Outcome

The retained signed candidate.3 manifest is now bound to a generated strict-v2
runtime handoff and exercised through both real rollback mechanisms in one
isolated local sequence:

`1.1.6+20260819 -> pokrov-1.2.0 -> 1.1.6+20260819`.

The client-owned `set-release-stable-pointer.ps1` performs the dry-run,
same-filesystem atomic forward switch, backup/receipt readback and atomic
reverse switch. The platform-owned `remote_brain_apply_release_handoff.py`
projects the same two handoffs into a temporary portal env. The final client
pointer matches retained stable bytes and the final portal env matches its
pre-candidate bytes exactly. An unrelated env setting is preserved.

This closes the verified-local scope of `REL_DOD/DOD-18` at `I3`. It is not a
production rollback or candidate promotion. `I4/I5` still require separately
authorized stable-pointer/runtime mutation and current/Brain-origin readback.

## Exact source and signature binding

| Surface | Exact revision / identity |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.3`; operational id `51f54f889279c49354b822aea9d188af46346e4ed380c73c3a700bd5911f253b` |
| Platform generator input | `eafaca3e64c0619dea7f58fc9c430682b4520559` |
| Client generator and pointer | `ac22825e857a313c9e4eba61030eb548d6346ead` |
| Core runtime contract | `344b317a7a09eca7943a93866b193553538bd8f6` |
| Release-index signing source | `6a1afa95fe52da2d559ba7b1da88715cd0344bb2` |
| Signed manifest | `a2752b6a3b95faacf13a68edb708c560966a0f5eb8727e109d7f1603fdc81090` |
| Detached signature | `926f0b4667a58ba9cc5ace5c4e6c3c8129d1ec3d4d449b3f0831a8c527cd7121` |
| Signing key | Ed25519 `pokrov-release-2026-01`; public-key verification `PASS` |

The exact client generator produces handoff SHA-256
`565a43dd8e31444e6154872823bdbfd6a222acdef3c600efec18c23d68c5063b`.
It contains six candidate artifacts, ten still-blocking promotion gates and
handoff artifact-set SHA-256
`a2d650f4820e940028b53e90061a7247eaa54fc030cb6e14adb4ef8d339a55e7`.
The handoff product identity remains `pokrov-1.2.0`; the exact `.candidate.3`
identity is carried by the independently verified signed release-index
manifest.

## Client-channel result

- retained stable handoff SHA-256:
  `563dd47835e017363eac63b33d66bdfeb9b41881168d4a14808f1daf48d3569f`;
- dry-run leaves the pointer on retained stable bytes;
- forward apply reads back candidate handoff `565a43dd...` and keeps a
  byte-identical stable backup;
- reverse apply reads back stable `563dd478...` and keeps a byte-identical
  candidate backup;
- final validation reports stable `1.1.6+20260819`, two bound rollback targets
  and `rollback_byte_identical=true`;
- forward and rollback receipts are embedded in the retained evidence with
  randomized temporary paths normalized to `<isolated>`.

The tracked client catalog and tracked stable pointer were never written.

## Portal result

The actual strict-v2 runtime consumer projects the exact candidate artifact
hashes, including Android arm64
`e105dc28bcadba9c063f64fb05652f6d905df373700c3c9d531a10ed0bd5d4d3`
and Windows
`9962e3e80947dae374619ed388fc08b7322bffda38202a42e5812597c7818021`.

Portal env SHA-256 changes from `c4d3ea78...` to `a290236f...` on the forward
projection and returns to `c4d3ea78...` on rollback. The rollback is
byte-identical and preserves the unrelated setting. No SSH connection,
service restart, static rebuild or remote env write occurs.

## Ledger decision

`REL_DOD/DOD-18` advances `I0 -> I3`. The exact signed candidate, generated
runtime handoff, portal consumer and client pointer now pass one retained local
rollback rehearsal. `FE/P12-130` remains `I3` with stronger exact-candidate
evidence.

Distribution becomes `I4=4`, `I3=308`, `I2=15`, `I1=38`, `I0=12`. There are
312 rows at or above `I3` and 65 below `I3`; the pending stage split becomes
`0/30/14/21` for pre-freeze/candidate/external/deferred.

## Verification

- `python -m pytest -q tests/test_release_1_2_candidate_rollback_rehearsal.py`
  -> `5 passed`;
- exact rehearsal script ->
  `PASS_LOCAL_EXACT_CANDIDATE_PORTAL_CLIENT_ROLLBACK`;
- client stable-pointer validation, dry-run, forward apply, reverse apply and
  final validation -> `PASS` in the isolated artifact root;
- portal candidate projection and byte-identical rollback -> `PASS_LOCAL`;
- tracked client pointer/catalog, portal runtime, deployment, publication and
  stable promotion -> unchanged / not performed.

## Retained evidence

- `evidence/013AF-exact-candidate-rollback-rehearsal/013AF-candidate3-release-handoff.json`
  is the exact generated strict-v2 handoff; 12947 bytes, SHA-256
  `565a43dd8e31444e6154872823bdbfd6a222acdef3c600efec18c23d68c5063b`.
- `evidence/013AF-exact-candidate-rollback-rehearsal/013AF-candidate3-rollback-rehearsal.json`
  binds the signature, source tuple, exact handoff, embedded receipts, portal
  and pointer round trips, mutation boundary and evidence ceiling; 8101 bytes,
  SHA-256
  `7a9d3c97a01b59ad0b3fbc342216805b13a4166b19d3a1e112704695c1d8cadc`.

## Next action

Do not convert this local `I3` into production proof. Before `I4`, obtain
explicit authority for the actual portal/client runtime drill, retain the real
external backup and receipt, verify the same candidate identity from
current-origin and Brain-origin, and restore the retained stable pointer.
Public `v1.2.0` and stable promotion remain separately prohibited.
