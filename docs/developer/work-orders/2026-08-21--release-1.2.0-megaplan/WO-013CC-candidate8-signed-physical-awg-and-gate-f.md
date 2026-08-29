# WO-013CC — candidate.8 signed source, physical AWG and Gate F

## Outcome

Create and bind `pokrov-1.2.0-candidate.8` from the corrected platform and
client promotion lines, retain the exact six-artifact supply chain and public
release-index signature, prove the Android false-green correction plus AWG2
and AWG3.1 authenticated egress on the exact ARM64 package, refresh the
current-origin budgets, and produce a new fail-closed Gate F decision.

Gate F validates all 19 evidence pointers with zero validation errors and
returns `BLOCKED`: `4 PASS`, `15 non-PASS`, `0 FAIL`. Supply chain,
release-doc/manifest binding, current-origin and authenticated client egress
pass. This does not authorize Gate G, a tag, public assets, stores or the
stable pointer.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.8` |
| Operational ID | `eeedbaf8540a83649a7143d6c7097336429e466118ed4f9ca2b732b7e6e2195a` |
| Platform source | `241a83b4dca00799b39696a4ae0c3c97e087ec39` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `b242e0a3060b04f9b71641a0524bf251a75ce2a8` |
| Receipt-bearing release-index main | `b9945274bccdca48f32ef09e43b854c37a8dae66` |
| Signed manifest | `f0006cec90c84e401e9920d9098102c7f50ab5ace5242e0d7683c3df709a6fbc` |
| Detached signature | `5fcae0675ea45e79baf495859fd170661f5d6dd3a8535275acd4d62680d324f6` |
| Signing receipt | `4109bb3417b32a780604300055f5308acf7dc810e7ea9c547075e1da41cc21fc` |

The signed source is an exact published ancestor of current public
`origin/main`; the later main commit records the receipt and does not alter
the signed manifest bytes. The preflight now checks that ancestry instead of
incorrectly requiring the signed commit to remain the branch tip.

## Artifacts and supply chain

| Artifact | Bytes | SHA-256 | Signing state |
|---|---:|---|---|
| Android universal APK | `295370385` | `cd0f6edea8f362a0b3e1b4db5896bc862157b5ce84549284480f55737875a183` | `PASS` |
| Android ARM64 APK | `101366934` | `9278c09fd8fa5768d3260cf796b4230db5acb0a092187aae00c441d717cfc572` | `PASS` |
| Android ARMv7 APK | `90779172` | `0caa4fc7c46e560e7a6239a2bddf9d66e06547bbb65a08209728d16738fd3758` | `PASS` |
| Android x86_64 APK | `109952213` | `ec07ba17e9a5c697fcf46ccd193970fa3666eeeb3b9e345876aa8ee1d45a2627` | `PASS` |
| Android market AAB | `126269104` | `719f76d9cd9033e871c4422842a85f015c2428446301b097cb53b9250e1b40e2` | `PASS` |
| Windows setup EXE | `28929376` | `26ec26d8989d61415f07cbf9707f336ebba0b947fa4ba0ee93d3078fa3984668` | `OWNER_ACCEPTED_UNSIGNED_WINDOWS_DIRECT_BETA_ONLY` |

The offline verifier passes all six artifacts and all eight Windows runtime
files. The strict-v2 handoff, 349-component CycloneDX 1.5 SBOM, six-subject
SLSA provenance and Windows runtime manifest have SHA-256 values
`af98956b...ea24`, `72d76392...c7c3`, `9532fe29...a85c` and
`93814e56...17da`. Android uses the retained production certificate. Windows
Authenticode remains `NotSigned`; the owner exception permits only the
explicitly warned direct beta and is not trusted, Store or broad-stable proof.

Release-index source-contract run `33267112810`, main-only signer run
`33267152760` and receipt source run `33267250415` all execute real steps and
pass. Private platform PR `79` and client PR `34` hosted jobs remain zero-step
GitHub billing blocks. Under the no-purchase `OWNER_SOLO_EXCEPTION` they are
not required to become paid branch-protection checks, but they are still not
reported as PASS.

## Local source gate and preflight

The exact platform/client/Core tuple passes all `15/15` local source-gate
steps, including client analysis and `413` widget tests, `69` cabinet E2E
tests, frontend production builds, responsive/reduced-motion checks and static
performance budgets. The report keeps `candidate_proven=false` and
`promotion_status=MANUAL_OWNER_TEST`, as a local gate must.

The fail-closed preflight returns `READY_LOCAL_FREEZE` with zero blockers. It
uses exact detached platform `241a83b...`, client `3459438...`, Core
`a45d69e...` and signed release-index source `b242e0a...`; the newer clean
harness is recorded separately as `0d3c003...`. All web checks pass under the
declared Node `22.14.0` and npm `11.7.0` toolchain.

## Current-origin and physical Android

Fresh read-only current-origin measurements use a clean exact platform
checkout, five warmups and 50 retained samples per endpoint:

| Budget | p95 | Limit | Result |
|---|---:|---:|---|
| health | `66.9959 ms` | `100 ms` | `PASS` |
| public catalog | `68.7012 ms` | `200 ms` | `PASS` |

The exact candidate.8 ARM64 APK is installed on the owner's physical Android
device over Beeline mobile data with WARP off. Pulled installed bytes match
the retained APK SHA-256 exactly.

- Ordinary control shows `NONE -> connecting -> connected`; connected appears
  only after Android VPN and selected egress validation. The notification
  false-green regression is physically closed for this slice.
- `awg2_lab` reaches app-confirmed tunnel, managed DNS and selected egress;
  independent Core interop passes after the phone releases the same profile.
  The earlier concurrent same-profile failure is retained as a differential,
  not assigned a speculative cause.
- `awg31_lab` with `randomized_trailers_mobile_safe_v2` also reaches the same
  app-confirmed state and passes independent Core interop. It uses official
  pinned cryptography, randomized trailers and no custom cryptography.
- Final cleanup restores `default` / `legacy_reality_fallback`, removes AWG2
  and AWG3.1 material and lab membership, stops the VPN service and leaves
  WARP off.

This is an authenticated-egress PASS, not the whole Android release matrix.
WARP runtime, per-app traffic, Private DNS interaction, IPv6/leak behavior,
OEM/Doze lifecycle and endurance remain `MANUAL_OWNER_TEST`.

## Origin and platform boundaries

- `current-origin`: `PASS` for the exact platform source and named budgets.
- `brain-origin`: `NOT_RUN`; exact platform `241a83b...` is not deployed and
  candidate.7 Brain evidence is not relabelled.
- `RU-origin`: `NOT_RUN`; the same-day Raspberry Pi 4 result remains
  `PASS_BASELINE_ONLY`, not an exact candidate or Smart DNS runtime run.
- Windows live: `NOT_RUN`; local build/integrity pass does not replace an
  isolated Windows 10/11 install/service/IPC/TUN/DNS/AWG/recovery/uninstall
  matrix.
- Smart DNS live: `NOT_RUN`; no owned resolver/fronted access runtime is
  deployed, so access attribution, leak/lifecycle and rollback remain open.

## Gate F and remaining blockers

The exact candidate.8 Gate F result is `BLOCKED` at `4/19 PASS`, `15/19
non-PASS`, `0 FAIL`, with zero validation errors. The open rows include:

- aggregate Gates A-E/manual stop-ship and no-open-P0 attestation;
- the remaining physical Android matrix;
- isolated Windows live and cleanup proof;
- exact Brain and RU candidate execution/readback;
- live Smart DNS access and rollback;
- provider, Operator, legal/commercial, comparable performance and
  post-public-promotion health.

`REL_GATE/GATE-F` remains `I3`; `FRKN_PLAN/W9-05` remains `I1`. Candidate.7
remains immutable rejected history. No completion-index level changes are
claimed.

## Evidence and mutation boundary

Machine evidence is under
`evidence/013CC-candidate8-signed-physical-awg/`:

| Evidence | SHA-256 |
|---|---|
| signed/runtime binding | `83f4abc9193b6f137664a0c2fef7f5df93c38dab3625342f9edb7c0ff373d8e9` |
| normalized runtime summary | `83387ecfc028f2944bac9c618ee9042d98b374f698fc46df038ec4080c3be15a` |
| Gate F evidence | `6e2fb2e78f6a7c753b5c8fa3c9b7257524461f3869c75b4a15fe68602b575a32` |
| Gate F input | `ac6085e3f5f7f45a6d42dab26a798e9ca31b989558abac07d38954d469ec04bb` |
| Gate F decision | `3f15984b5006abe7fad751e47c0d90340e527150686398c6c1c1ae99d7b02a54` |

No raw device identifier, private key, credential, runtime profile, endpoint,
customer data or provider payload is retained. No production deploy, payment
action, repository visibility change, tag, public release, store submission,
stable pointer mutation or Gate G authorization occurred.

## Verification

```text
python -B scripts/release_1_2_local_quality_gate.py <exact candidate.8 roots> --keep-going
# PASS: 15/15; local-only, candidate_proven=false
python -B scripts/release_1_2_candidate_preflight.py <exact source and signed-index roots>
# READY_LOCAL_FREEZE; blockers=0
python -B scripts/validate_release_candidate_supply_chain.py <candidate.8 inputs>
# PASS: 6/6 artifacts; 8/8 Windows runtime files
python -B scripts/api_latency_probe.py <candidate.8 current-origin health and catalog inputs>
# PASS: 50/50 samples per endpoint, both p95 budgets met
python -B scripts/release_1_2_gate_f.py <signed candidate.8 inputs> --expect-blocked
# BLOCKED: 4 PASS / 15 non-PASS / 0 FAIL / 0 validation errors
```
