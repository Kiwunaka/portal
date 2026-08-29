# WO-013CH — candidate.8 LDPlayer rehearsal and Gate F refresh

## Outcome

Retain the exact `pokrov-1.2.0-candidate.8` x86_64 Android rehearsal on the
owned LDPlayer emulator, preserve different outcomes for ordinary, AWG2 and
AWG3.1 profiles, prove the final default/no-lab state, and regenerate the
digest-bound Gate F decision without touching the physical phone or
authorizing promotion.

The `android_ldplayer_rehearsal` row advances from `NOT_RUN` to `PASS`.
Successor Gate F remains `BLOCKED`, now at `6 PASS / 13 non-PASS / 0 FAIL`
with zero validation errors. Gate G, public release, Store upload and stable
pointer mutation remain unauthorized.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.8` |
| Operational ID | `eeedbaf8540a83649a7143d6c7097336429e466118ed4f9ca2b732b7e6e2195a` |
| Platform source | `241a83b4dca00799b39696a4ae0c3c97e087ec39` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `b242e0a3060b04f9b71641a0524bf251a75ce2a8` |
| Manifest SHA-256 | `f0006cec90c84e401e9920d9098102c7f50ab5ace5242e0d7683c3df709a6fbc` |
| Signature SHA-256 | `5fcae0675ea45e79baf495859fd170661f5d6dd3a8535275acd4d62680d324f6` |
| Receipt SHA-256 | `4109bb3417b32a780604300055f5308acf7dc810e7ea9c547075e1da41cc21fc` |

No candidate artifact was rebuilt, relabelled or mutated.

## Exact emulator and package boundary

The test used the explicit LDPlayer emulator target only. The physical phone
was visible to neither command routing nor UI automation in this slice and no
physical-device identifier is retained. The environment is Android 9/API 28
`x86_64`.

The exact candidate APK has SHA-256
`ec07ba17e9a5c697fcf46ccd193970fa3666eeeb3b9e345876aa8ee1d45a2627`
and size `109952213`. The installed `base.apk` is byte-identical. Package
readback is release/non-debuggable `space.pokrov.pokrov_android_shell`
`1.2.0+4046`. APK Signature Scheme v2 verifies and the certificate SHA-256 is
`0a0602a7df5d96a0b427909d004f3ddf26def86587634bf16694da8d654b2500`.

UI interaction used the Android emulator QA contract: exact emulator target,
ADB UI hierarchy, bounds-derived coordinates and retained UI-tree/screenshot
digests. It did not use image-coordinate guessing or route commands to an
unspecified device.

## Catalog and profile differential

After refresh, all seven active locations were visible: Frankfurt, Milan,
Amsterdam, Warsaw, Moscow, Saint Petersburg and New York. This proves the SPB
catalog entry renders on LDPlayer; it is not a claim that every origin can
reach every SPB transport.

| Profile | Exact result | Boundary |
|---|---|---|
| Ordinary `legacy_reality_fallback` control | `PASS_FAIL_CLOSED_CURRENT_ORIGIN_EGRESS_NOT_CONFIRMED` | TUN formed, selected egress was not confirmed, POKROV stopped system VPN and showed explicit failure/retry without false green. This is not an ordinary egress or protocol PASS. |
| `awg2_lab` | `PASS_TUN_DNS_SELECTED_EGRESS` | Guarded PLAN/APPLY passed without entitlement extension; app details confirmed tunnel, DNS and selected exit; server alignment passed `11/11`; count-only outer traffic was retained without addresses. |
| `awg31_lab` | `PASS_TUN_DNS_SELECTED_EGRESS` | Guarded PLAN/APPLY passed without entitlement extension; app details confirmed tunnel, DNS and selected exit; server alignment passed `11/11`; `randomized_trailers_mobile_safe_v2` retains official pinned cryptography and no custom cryptography. |

AWG2 TUN counters observed `3247` RX / `2602` TX bytes. Its 12-second
count-only outer capture observed `10` packets and a one-second handshake age.
The idle inner capture did not prove an independent inner payload and receives
no such credit. AWG3.1 TUN counters observed `690` RX / `546` TX bytes; its
count-only outer capture correctly treats fixed-size classification as not
applicable to randomized trailers.

The ordinary control does not downgrade the two lab results, and the two lab
results do not turn ordinary emulator egress into a pass. Each profile keeps
the outcome actually observed.

## Restore

Guarded default PLAN/APPLY passed and read back:

- `selected_profile=default`;
- `resolved_profile=legacy_reality_fallback`;
- no AWG2 or AWG3.1 material;
- no cohort or lab-allowlist membership;
- no entitlement extension;
- WARP off;
- no `tun0` or Android VPN agent;
- UI `Не защищено` / `Подключить`.

The exact candidate APK remains installed and its app process may remain
alive; neither fact is a connected/VPN claim.

## Gate F interpretation

The established `android_ldplayer_rehearsal` criterion is an exact-byte
emulator install/launch rehearsal and has previously passed without replacing
authenticated egress or physical Android. Candidate.8 now proves that boundary
and more: exact installed bytes, launch/catalog, two authenticated lab-profile
paths, truthful ordinary failure and clean restore.

Only this row changes in the successor aggregate:

| Check | Previous | Current |
|---|---|---|
| `android_ldplayer_rehearsal` | `NOT_RUN` | `PASS` |

The fail-closed verifier validates all `19/19` pointers and returns
`BLOCKED`: `6 PASS`, `13 non-PASS`, `0 FAIL`, zero validation errors.
`REL_GATE/GATE-F` remains `I3`; no row advances to `I4` and no promotion
authority is created.

## Evidence

Tracked, sanitized evidence is under
`evidence/013CH-candidate8-ldplayer-rehearsal/`:

| Evidence | SHA-256 |
|---|---|
| LDPlayer summary and 22 external artifact digests | `622f5c88b284e3ede569b5195e21bf9d8c1e9a9fd328c648645e0a4b5ac93693` |
| Successor Gate F evidence | `f50daf50089954997cb6b44544afb652bf6f6272f3fcb5d8c61cbc109862b253` |
| Gate F input | `122692743909673bf040430a14e63fb02806d4b5cadfc8859efead4479bfa257` |
| Gate F decision | `389793c48fd5da17eac79f90f12e1c5f04f6069048a7c9ddb02b57ee2c49e599` |

External APK, screenshots, UI summaries, guarded PLAN/APPLY reports and
count-only packet reports remain under `E:/POKROV-tools/evidence` and are
bound by file name, size and SHA-256. No raw device/account identifier,
endpoint, address, key, credential, customer data or packet payload is tracked.

Gate F evidence uses raw file digests. `.gitattributes` now pins the existing
013CF and new 013CH JSON evidence to LF so Windows `core.autocrlf=true` cannot
manufacture a hash mismatch on a fresh checkout. The decision was generated
and revalidated from a temporary LF checkout; that temporary worktree was
removed after the result was retained.

Client release/readiness owners were reconciled by PR `37`: source commit
`0aa9b1e7915aa8bbc3179aeedc26e1091b184b63`, merge commit
`e3ae08bc16a90472d26e7b52ec5db6be3574e9c7`. Hosted run `33277235236`, job
`99165987170`, executed zero steps and remains `SKIPPED_BY_OWNER` under the
no-purchase solo policy, not PASS.

## Mutation boundary

The owned lab binding was temporary, applied through guarded exact-install
PLAN/APPLY and fully restored. No entitlement was extended. No production
deploy, service restart, payment action, candidate mutation, physical-device
action, repository visibility change, tag, public release, Store upload,
stable pointer or Gate G authorization occurred.

## Verification

```text
apksigner verify --verbose --print-certs <exact candidate.8 x86_64 APK>
# PASS: v2, expected certificate SHA-256

python -B scripts/release_1_2_gate_f.py <exact candidate.8 inputs> --expect-blocked
# BLOCKED: 6 PASS / 13 non-PASS / 0 FAIL / 0 validation errors

python -B -m pytest -p no:cacheprovider tests/test_release_1_2_gate_f.py -q
# PASS

client test/docs-contract.ps1
client scripts/validate-seed.ps1 -PlatformRoot <clean platform> -CoreRoot <clean Core>
# PASS
```

## Remaining boundary

Gate F still requires the thirteen non-PASS rows, including current exact
Gates A-E/mandatory DoD/no-open-P0 attestations, Windows connected clean-VM
network matrix, canonical RU-origin proof, provider payment E2E, Operator
OIDC/RBAC/action-intent, legal/commercial approval, comparable performance and
release health, rollback/kill controls and the explicitly skipped hosted row.
Physical Android remains a separate matrix and LDPlayer cannot replace it.
