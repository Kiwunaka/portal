# WO-013Z — Brain-origin pre-candidate runtime evidence

Status: `BRAIN_ORIGIN_PRE_CANDIDATE_RUNTIME_PASS_EXACT_CANDIDATE_OPEN`
Phase: `11`
Rows: `FE/P12-012`, `FRKN_PLAN/W9-02`
Capture candidate state: `NOT_CREATED`
Current candidate state: `SIGNED_MANIFEST_ARTIFACT_ONLY_PUBLIC_RELEASE_NOT_CREATED`
Deployment: `NOT_REQUIRED_NOT_RUN`
Recorded: `2026-08-26`

## Goal

Prove the current owned control-plane and enabled delivery contour from the
Brain origin without deploying, changing routes, reading connection material
or converting a pre-candidate runtime slice into exact-candidate proof.

This work was originally retained on pre-merge branch
`codex/brain-origin-evidence-record` as a conflicting `WO-013X`. The current
ledger already owns `WO-013X` for the exact LDPlayer content slice, so this
integration preserves the same evidence under the non-colliding `WO-013Z`
identity. No observation or result is upgraded by the rename.

## Probe correction

The legacy `remote_brain_network_probe.py` read the retained operator
inventory and checked the same requested ports on every historical host. Its
first diagnostic therefore reported a closed legacy `us:443` even though the
live enabled pool had already changed. That result is
`INVALID_FOR_CURRENT_DELIVERY_VERDICT`.

Platform PR 37 adds a fail-closed `--live-enabled-nodes` mode. It reads only
enabled `code`, `host` and configured `vless_port` values from the live
control-plane database, probes those endpoints from Brain and retains only
node code, port, bounded TCP status and allowlisted error kind. Host, IP, SNI,
raw exception, password and token material never enter the report. The
retained-inventory mode remains diagnostic-only and requires `--redact` before
it may write JSON.

The same PR adds a bounded `--json-out` envelope to
`verify_brain_ready.py`. It records service/listener/endpoint/subscription
status and counts, not response bodies, process details or secret values.

PR head `34f6b2b34f78b0a6b9833d3239faa381c3fd4364` passed
cross-repository run `32982213812` and Guardrails run `32982213900`. Signed
merge `d310ceffea683f50ebe369ac9a0abee3a9a204c4` passed post-merge Release v2
Contract run `32983333728` and Guardrails run `32983333723`.

## Clean signed-source result

All credited probes ran from a clean worktree at signed platform merge
`d310ceffea683f50ebe369ac9a0abee3a9a204c4`:

| Slice | Result | Exact observation | Evidence SHA-256 |
|---|---|---|---|
| Brain readiness | `PASS` | `23/23`, including six required services, `443/8444`, public/static endpoints and `5/5` stable subscription samples | `cd902e9381368fb717e426b11152e10de8512e77b9483f57e9c48ae1078f120b` |
| Live enabled delivery TCP | `PASS` | `7/7` configured endpoints open: `de`, `it`, `nl`, `pl`, `ru`, `ru_spb`, `us` | `0a8781d622383566e1012536fd882535e6304dccc795d36f304c8820c4742988` |
| Runtime app/provider policy | `PASS` | `8/8` checks; authenticated and anonymous app catalogs plus provider policy | `b37c980d614a1c77bb057e33f52b6b38b2bb773723c80b7839496eafaecf8501` |
| Former-free MTProto diagnostic | `FAIL_DIAGNOSTIC_SEPARATE` | retained target `9443/tcp` closed | `888e64924839247555ca31bebad3ca02507d7d8797416b71d4529d7957b4f4f4` |

The runtime app catalogs exposed stable `1.1.6` and no release manifest at
capture time. That was the expected rollback-safe state before the signed
candidate-manifest artifact existed. It is not evidence of a stale backend and
does not authorize a deploy or pointer change. The later 013Y signer result
does not retroactively convert this capture into exact-candidate runtime proof.

The expanded external diagnostic manifest validates `25/25` with SHA-256
`26018ffb88e3bbcf16a78e941268a92721b6a0c724118f8e0d61ffe132758aef`.
Its four Brain artifacts pass the sensitive-pattern scan. This supersedes the
physical `SHA256SUMS.txt` state referenced by 013W while preserving all 21
earlier current-origin files and their individual hashes.

## Deployment and gate decision

The deployed backend runtime remains
`243dcbe4727041d62cc0a36e7d2fd5a8530c7c25`. Changes after it are probe
tooling, tests and documentation, not backend runtime modules. No deploy,
restart, route change, payment action, stable-pointer change, GitHub Release or
public asset publication occurred.

`BRAIN_ORIGIN_PRE_CANDIDATE_RUNTIME` is `PASS`. The exact-candidate
`BRAIN_ORIGIN` promotion gate is still `NOT_RUN`; the stable `1.1.6` capture
cannot prove future 1.2.0 bytes. The closed former-free MTProto port is a
separate operational diagnostic and prohibits a current Telegram-proxy
readiness claim, but it does not rewrite the `7/7` VPN delivery result or prove
a VPN outage.

No execution-ledger row advances. `FE/P12-012` remains `I2` because provider
policy readback is not payment-provider E2E for an exact candidate.
`FRKN_PLAN/W9-02` remains `I1`: current-origin and Brain-origin pre-candidate
slices now exist separately, while exact-candidate and RU-origin evidence do
not. The capture-time distribution remains retained inside the evidence JSON;
the current aggregate is owned by `EXECUTION-INDEX.md`.

## Next action

Run the exact APK on the physical Beeline device once Windows exposes it to
ADB. Then execute the Windows clean-host and remaining exact-candidate gates.
Repeat the full/current quick and Brain-origin slices against the exact
candidate. Keep MTProto disabled/unclaimed until its separate owned service
configuration and reachability are intentionally restored and proved.
