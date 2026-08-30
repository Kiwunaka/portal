# WO-013CN — exact candidate.10 Gate F NO_GO

## Outcome

Generate the first fail-closed Gate F decision for signed immutable
`pokrov-1.2.0-candidate.10` from candidate-scoped evidence. Do not inherit
candidate.8 source-plan, current-origin or physical-device results merely
because the client/Core artifact bytes are unchanged.

The retained verifier validates the signed manifest, detached Ed25519
signature, signing receipt, public keyring, exact four-repository source tuple,
all `19/19` evidence pointers and both upstream evidence digests. It returns
`NO_GO`: `5 PASS / 14 non-PASS`, including exactly `1 FAIL`, with zero
validation errors. Gate G remains unauthorized.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` |
| Operational ID | `1de7182d9c82759acc36eb7a336d1fef2362e8f69505f3b4880e595f79020454` |
| Platform source | `209b8f40c36d95f2bbc67caa52a41ecb09f46720` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `fc00b26d402b167260e495eb33397115bef1c317` |
| Manifest SHA-256 | `0711546b0da4b811fba42e1ad543797494e4104bd95251c9e8e8011ac04dff83` |
| Signature SHA-256 | `6f96f8932e388f221cf7d5e10dc1680fbcbb62f87efe00410439eb9f62e42799` |
| Receipt SHA-256 | `094a42f3c0d9be3957b3065344e5bfce4880c2899833fed3b4d211d8d453a89c` |

The Android build number is derived through the established retained-candidate
validator. Candidate.10 binds the same ARM64 and x86_64 artifact bytes already
identified for build `4046`. The same-byte physical install identity is enough
for build-number validation only; it does not transfer candidate.8 physical
runtime credit. The candidate.10 physical Android row remains
`MANUAL_OWNER_TEST` because the phone is unavailable.

## Exact checks

| Status | Count | Checks |
|---|---:|---|
| `PASS` | 5 | supply/signature/SBOM/provenance; release-doc manifest binding; Brain-origin; LDPlayer rehearsal; authenticated client egress |
| `FAIL` | 1 | RU-origin |
| `MANUAL_OWNER_TEST` | 8 | mandatory stop-ship/DoD; target-channel/manual signing; rollback/kill; Windows live network; physical Android; provider E2E; Operator auth/RBAC/action intent; legal/commercial approval |
| `NOT_RUN` | 3 | exact Gates A–E replay; current-origin; performance/release health |
| `MISSING` | 1 | broad no-open-P0/false-green/secret-leak attestation |
| `SKIPPED_BY_OWNER` | 1 | private hosted required checks under the no-purchase solo policy |

The single explicit FAIL is the canonical RU run retained by WO-013CM:
`10/13` targets pass, while Brain TLS, free REALITY target and NL TCP fail as
three independent conditions. `ru_spb` passes. A required FAIL produces
`NO_GO`; it is not diluted by the thirteen other non-PASS checks or the five
passes.

## Evidence binding

The decision references one candidate.10 evidence object for all required
status pointers. That object in turn binds:

- the secret-free WO-013CM Brain/Pi/LDPlayer summary;
- the exact signed runtime binding with three signer outputs, public keyring
  validation and same-byte APK identities.

| Evidence | SHA-256 |
|---|---|
| Signed runtime binding | `3c2ea5fc08690149db9b11d1c9596ac7751d122bed1be2a3abdba461e20b86bb` |
| Gate F evidence | `77535b0b2f556d628cdc217fb7f1b6c44509afbd8c67a689cb4e765b1b8af56b` |
| Gate F input | `d5ec25f630ff7dbc256ade8bf0c8a8c7fb6017a37180318133df328ee8cef549` |
| Gate F decision | `40daab1330ed4ac6beee9c1e98bc97dadef94633e2e206bf800438ae1f8d36f1` |

No raw endpoint, IP, runtime secret or secret hash, physical-device/emulator
identifier, private key, credential or customer data is tracked.

## Completion-index effect

- `REL_GATE/GATE-F` remains `I3` and changes from the historical candidate.8
  `BLOCKED` snapshot to exact candidate.10 `NO_GO 5/14/1`.
- `FRKN_PLAN/W9-05` records the same exact-candidate no-go decision and remains
  `I1`.
- No row advances to `I4`; Gate G remains prohibited.

## Mutation boundary

Gate F generation is read-only with respect to every runtime and repository
outside this branch. It creates only retained decision evidence. The earlier
authorized Brain/Pi/emulator mutations are bound by WO-013CM and are not
repeated.

No artifact rebuild, candidate relabel, payment action, production deploy,
repository visibility change, tag, public release, Store submission, stable
pointer or Gate G authorization occurred.

## Verification

```text
python -B scripts/release_1_2_gate_f.py <candidate.10 exact inputs>
# expected exit 2: NO_GO, 5 PASS / 14 non-PASS / 1 FAIL / 0 validation errors

python -B -m pytest -p no:cacheprovider tests/test_release_1_2_gate_f.py -q
```

## Remaining boundary

Resolve or deliberately reject the three RU target failures, replay exact
candidate.10 Gates A–E and current-origin, complete the physical Android and
isolated Windows matrices, establish the no-open-P0 attestation and finish the
provider, Operator, legal, performance and other manual gates. A future Gate F
must use new exact evidence; candidate.10 remains signed but not releasable.
