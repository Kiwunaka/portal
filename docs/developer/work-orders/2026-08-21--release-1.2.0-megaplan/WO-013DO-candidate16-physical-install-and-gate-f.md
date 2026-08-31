# WO-013DO — candidate.16 physical install binding and Gate F NO_GO

Status: `EXACT_CANDIDATE16_ARM64_INSTALL_PASS_GATE_F_NO_GO`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.16`
Production/external mutation: `NONE`

## Outcome

Bind the immutable candidate.16 production-signed ARM64 APK to one owner
physical Android device without launching the application or taking screen
control. Exact installed-package readback matches the signed artifact at
`1.2.0+4049`, closing the prerequisite that previously prevented Gate F from
running.

Generate the first candidate.16 Gate F decision from that binding and the
retained exact-candidate release truth. The verifier validates the signed
manifest, detached signature, receipt, manifest-bound public keyring, exact
four-source tuple, all `19/19` evidence pointers and the upstream binding
digest. The decision is `NO_GO`: `2 PASS / 17 non-PASS`, including exactly
`2 FAIL`, with zero validation errors. Gate G remains unauthorized.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.16` |
| Operational ID | `d9081b8e77bc82512079affc952ce7c7aa82af5eccc843f6a3636b3269094b4f` |
| Platform source | `719e23dc49407beb9ae30d98d17d4b73d18ae37c` |
| Client source | `75ba7e721cfee486f7189edd51de97aba2746722` |
| Core source | `cd8f0f4169d570d693992a959d81d17c2c44884d` |
| Signed release-index source | `54cfa03502ffafa5e4fb230a2cbdb0c0572c429f` |
| Manifest SHA-256 | `ae1906e68df755b1e0ce6a77d6ede8256f923e72fe11da57f1cae89a82c4ffe6` |
| Signature SHA-256 | `f5df63578d56db84a48eac1c68f1192e81462e8b407b1b6ff877c2b415507a9a` |
| Receipt SHA-256 | `1231ab6988746ca0e9725296826de2a9696a9a78600aa5e7f0b0c1b8c5782de4` |

Candidate.16 remains immutable, private and artifact-only with
`promotion_authorized=false`. The later client documentation merge records
evidence only and does not alter the candidate source tuple or application
bytes.

## Physical ARM64 install binding

The owner physical device is retained only as the bounded class
`owner_physical_android_12_arm64`; no serial or other raw identifier is kept.
Before the install, the POKROV process and `tun0` were absent. The standard ADB
package update completes, and exact post-install readback reports:

| Check | Result |
|---|---|
| Package version | `PASS`, `1.2.0+4049` |
| Installed base size | `PASS`, `101366678` bytes |
| Installed base SHA-256 | `PASS`, `9bcdbe00fe8f8ed029894a65d531614f4fb912dda27e5fb1bb088c5b7516cc74` |
| Signed ARM64 artifact match | `PASS`, byte-identical |
| Application launched | `false` |
| Post-install POKROV process | absent |
| Post-install `tun0` | absent |
| Screen control | not used |

This is install identity only. Default-profile TUN/DNS/egress and cleanup,
AWG2/AWG3.1, WARP, per-app, Private DNS, external IPv6/leak, UDP53/MTU,
handoff, Doze, OEM and endurance checks remain `MANUAL_OWNER_TEST`.

Client PR `#50` merges the sanitized evidence and candidate.16 documentation
to `POKROV-app/main` as `1125d276...`. Its hosted job ends before repository
code with `steps=[]`; it is recorded as `HOSTED_CHECK_BLOCKED_BY_BILLING`,
not PASS. Local docs-contract and complete seed validation pass.

## Gate F result

```text
NO_GO
required=19
pass=2
non_pass=17
fail=2
validation_errors=0
gate_g_authorized=false
```

The two PASS rows are signed supply/SBOM/provenance and release-document to
manifest binding. The two FAIL rows are the exact candidate.16 LDPlayer AWG
rehearsal and authenticated client egress: both AWG 3.1 and AWG2 activate the
selected profile and form TUN, managed DNS and routes, then fail authenticated
egress without false green and clean up.

The remaining rows stay honest: eleven are `MANUAL_OWNER_TEST`, broad
no-open-P0/false-green/secret-leak attestation is `MISSING`, the exact current
origin aggregate is `NOT_RUN`, Windows trusted signing is
`SKIPPED_BY_OWNER`, and hosted platform/client execution is
`BLOCKED_BY_ACCESS_GITHUB_BILLING`. Ordinary default LDPlayer traffic, bounded
Brain source/readiness, isolated rollback, Windows idle-host checks and the RU
bundle/PLAN do not replace their broader Gate F rows.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013DO-candidate16-signed-binding.json` | `2c87c2cf67446a57beb591ad544b2fb28b266fd6e4fd33eac40d5909a69b85be` |
| `013DO-candidate16-gate-f-evidence.json` | `e350e942b4dcec0e0734128b0692f6992322b6a8e4ab5276f06f43d4e0213cee` |
| `013DO-candidate16-gate-f-input.json` | `8370396845582df370af1fc65e2027b20aa6853a1f6f8d1f98b844aa19f09329` |
| `013DO-candidate16-gate-f-decision.json` | `2c586078d18b8ec3272be3fbceddf8661f12ee977a02eab5860ead467560a54a` |

The evidence directory is pinned to LF so these digests remain portable.

## Verification

```text
physical ARM64 installed-package readback -> PASS exact 1.2.0+4049 bytes
client docs contract -> PASS
client full seed validation -> PASS
Gate F -> expected exit 2, NO_GO 2/17/2, validation_errors=0
JSON parse -> PASS for all four retained records
git diff --check -> PASS
```

## Completion-index and mutation boundary

`REL_GATE/GATE-F` remains `I3` but advances from not run to the exact
candidate.16 `NO_GO 2/17/2` decision. The 378-row distribution stays
`I4=5`, `I3=319`, `I2=20`, `I1=34`, `I0=0`. The physical-device gate remains
manual because install identity is not runtime proof.

No candidate artifact, VPN runtime, server, provider, DNS, database, Operator,
tag, GitHub Release, public asset, Store object or stable pointer is changed.
Resolve the owned DE identity and service boundary, repeat exact-Core and
client AWG egress, then complete physical default runtime, connected Windows,
current/Brain/RU, payment/Operator/legal, performance and no-open-P0 rows
before another Gate F. Gate G requires separate owner authorization even after
a future Gate F GO.
