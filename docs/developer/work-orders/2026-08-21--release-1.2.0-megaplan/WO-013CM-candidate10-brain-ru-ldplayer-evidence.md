# WO-013CM — candidate.10 Brain, canonical RU probe and LDPlayer AWG evidence

## Outcome

Bind the signed immutable `pokrov-1.2.0-candidate.10` to the exact Brain
runtime, the canonical probe on the owned direct-RU Pi 4 and an exact-byte
LDPlayer AWG2/AWG3.1 rehearsal. Preserve different verdicts for each origin
and do not convert a partial RU result into release readiness.

Brain-origin is `PASS`. The complete runner/uploader/ingest/archive/heartbeat
and admin readback path works from RU, but the release verdict is honestly
`FAIL`: `10/13` required targets pass and three retain distinct failures.
The exact LDPlayer package passes both default-off owned AWG profiles and is
restored to default with no lab material or active VPN. The physical phone is
unavailable and remains `MANUAL_OWNER_TEST`.

Candidate.10 Gate F is not regenerated in this slice. The latest retained
digest-bound Gate F decision is still candidate.8 `BLOCKED` at `6 PASS / 13
non-PASS / 0 FAIL`; it does not absorb candidate.10 evidence implicitly.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` |
| Product build | `1.2.0+4046` |
| Platform source | `209b8f40c36d95f2bbc67caa52a41ecb09f46720` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `fc00b26d402b167260e495eb33397115bef1c317` |
| Manifest SHA-256 | `0711546b0da4b811fba42e1ad543797494e4104bd95251c9e8e8011ac04dff83` |
| Signature SHA-256 | `6f96f8932e388f221cf7d5e10dc1680fbcbb62f87efe00410439eb9f62e42799` |
| Receipt SHA-256 | `094a42f3c0d9be3957b3065344e5bfce4880c2899833fed3b4d211d8d453a89c` |
| Android x86_64 APK SHA-256 | `ec07ba17e9a5c697fcf46ccd193970fa3666eeeb3b9e345876aa8ee1d45a2627` |

The offline supply validator passes all `6` candidate artifacts and `8`
Windows runtime files. Public release-index source/receipt changes and signer
run `33292070137` pass. The output remains
`ACTIONS_ARTIFACT_ONLY`, `promotion_authorized=false`; no tag, Store object,
stable pointer or public release is created.

## Brain-origin

The fail-first read-only source probe found `194/197` semantic matches. The
owner-authorized guarded backend operation retained rollback state, deployed
the exact platform source, restarted the bounded service set and required
delayed health before accepting the change. Automatic rollback remained armed
and was not triggered.

Postdeploy evidence passes:

- exact selected runtime source `197/197`;
- readiness `23/23`;
- enabled delivery network `7/7`.

This is exact candidate.10 Brain-origin `PASS`. It is not RU-origin or
post-public-promotion proof.

## Canonical RU-origin on Pi 4

The exact receipt-bound candidate.9 rollback passes PLAN/APPLY and preserves
the spool. Candidate.10 bundle install then passes PLAN/APPLY with receipt
`20260830T042736Z-240736-0108ccc4595f`. The deterministic bundle contains
`10` members, is `47930` bytes and has SHA-256
`0108ccc4595ff2f424b4e5169d19fc539e21cc1eaed79cb92ccbacf04ce85e22`.

The manual runner and uploader services both exit successfully. Signed
manifest fetch, ingest, archive, fresh heartbeat and all three admin read
endpoints pass. The latest run is current and eligible, the environment is
available, uploader queues are zero and archive writes are healthy.

The exact result is:

| Slice | Result |
|---|---|
| Canonical API, cabinet and marketing | `3/3 PASS` |
| Environment control | `PASS` |
| Delivery `de`, `it`, `pl`, `ru`, `ru_spb`, `us` | `6/6 PASS` |
| Delivery `brain` | `FAIL tls_handshake_failed` |
| Delivery `free` | `FAIL reality_target_mismatch` |
| Delivery `nl` | `FAIL tcp_connect_timeout` |
| Overall RU-origin | `FAIL — 10 PASS / 3 FAIL` |

The candidate.9 false failures from the fixed body threshold and forbidden
address-family classification are absent. The three remaining failures are
not collapsed into one SPB investigation and do not trigger an in-place
candidate mutation. `ru_spb` itself passes in the canonical run.

The timers remain installed and enabled but were left inactive after the
deterministic manual run. Root-only runtime material remains on the host; the
temporary local runtime-material copies were removed. No secret, secret hash,
raw endpoint or raw connected address is retained here.

## Exact LDPlayer AWG rehearsal

The Android emulator QA procedure targeted only the explicit owned LDPlayer
instance: Android 9/API 28, `x86_64`. The installed `base.apk` is byte-identical
to candidate.10, reports `1.2.0+4046`, `minSdk=24` and `targetSdk=36`.

The first ordinary connect refreshed an expired entitlement and failed closed:
no tunnel started and the UI showed that access was unavailable. This is not a
protocol failure. A guarded owner operation then granted exactly one test day
to the exact emulator install and selected each default-off lab in turn.

| Profile | Exact emulator result |
|---|---|
| `awg2_lab` | `PASS`: tunnel active, DNS ready, authenticated egress confirmed and routes assigned; crash buffer `0` |
| `awg31_lab` | `PASS`: tunnel active, DNS ready, authenticated egress confirmed and routes assigned; crash buffer `0` |

AWG3.1 keeps the official pinned cryptography; it is protocol obfuscation, not
a custom POKROV cryptographic primitive. UI coordinates came from the Android
UI hierarchy, visual state came from retained screenshots, and logs are
bounded/redacted.

Guarded default PLAN/APPLY then reads back `selected_profile=default`,
`resolved_profile=legacy_reality_fallback`, no AWG2/AWG3.1 material, no cohort
or lab membership, WARP off and no active Android VPN. The one-day test access
is a bounded exact-install entitlement and is not transferred to another user
or device.

The physical phone was not used. Physical candidate.10 Android proof remains
`MANUAL_OWNER_TEST_DEVICE_UNAVAILABLE`; LDPlayer does not replace it.

## Smart DNS boundary

A fresh authoritative check for `dns.pokrov.space` returns no A record on all
four Timeweb authoritative servers (`0/4`). Therefore TTL is not the blocker:
the record is absent from the delegated zone. Certificate issuance and Smart
DNS server/route APPLY remain unperformed until authoritative DNS is `4/4`.

## Completion-index effect

- `FRKN_PLAN/W9-02` now records exact candidate.10 Brain `PASS` and canonical
  RU-origin `FAIL`, while current-origin stays a separate unrun row for this
  exact source.
- `FRKN_PLAN/W3-02` gains exact candidate.10 LDPlayer AWG2/AWG3.1 proof but
  remains `I3`: physical candidate.10 and isolated Windows parity are open.
- `FRKN_PLAN/W9-05` records candidate.10 RU `FAIL` with Gate F regeneration
  pending; no go/no-go row advances to `I4`.

## Evidence

The secret-free normalized summary is under
`evidence/013CM-candidate10-brain-ru-ldplayer/`. It binds the external Brain,
Pi, admin, exact APK, guarded profile and redacted UI/log evidence by SHA-256.
External evidence remains under `E:/POKROV-tools/evidence`; signed candidate
outputs remain under `E:/POKROV-tools/release-candidates`.

Normalized summary SHA-256:
`15d435bb15475495b43e44e3537738f9a3bc6937b4859e4d5a6c0318fede7b59`.

No raw endpoint, IP, runtime secret or hash of a runtime secret, device/install
identifier, private key, credential or customer data is tracked.

## Mutation boundary

This slice includes the authorized exact Brain backend deploy, receipt-bound
candidate.9 Pi rollback, candidate.10 Pi install and one-day exact-emulator
test entitlement. Each mutable operation had explicit PLAN/APPLY or guarded
rollback controls and retained readback. Candidate artifacts were not rebuilt
or relabelled.

No payment action, repository visibility change, tag, public release, Store
submission, stable pointer or Gate G authorization occurred.

## Remaining boundary

Investigate the three RU target failures as independent endpoint/runtime
conditions, correct the authoritative Smart DNS record before ACME/server
deployment, run the physical candidate.10 Android matrix when the phone is
available, complete isolated Windows AWG/network parity and regenerate exact
candidate.10 Gate F. Until then candidate.10 is signed but not releasable.
