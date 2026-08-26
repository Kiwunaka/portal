# WO-013W — Current-origin API method and runtime classification

Status: `CURRENT_ORIGIN_API_PERFORMANCE_PASS_AGGREGATE_GATE_OPEN`
Phase: `11`
Rows: `REL/PERF-001`, `REL_GATE/GATE-E`, `REL_DOD/DOD-13`
Candidate: `NOT_CREATED`
Deployment: `NOT_REQUIRED_NOT_RUN`
Recorded: `2026-08-26`

## Goal

Measure the owned public API from the direct operator origin without stopping
the ambient VPN, correct the collector when live evidence disproves its warmup
method, and retain the result without turning one API-performance slice into a
full current-origin or exact-candidate pass.

## Scope and no-touch boundary

The authorized write scope is the API latency collector, its strict evidence
validator/tests, the canonical performance guide and this release record. The
probe uses only public read-only health/catalog endpoints. It does not deploy,
restart services, mutate routes, stop Hiddify, create a candidate, publish an
asset, run a payment or change production configuration.

## Direct-origin isolation

The workstation had an active Hiddify `tun0` default route. Ambient requests
therefore did not represent the direct operator origin and remain
`INVALID_FOR_RELEASE_DIRECT_ORIGIN`. The collector now accepts a locally
assigned literal source address, validates a local socket bind, disables proxy
discovery for that mode and binds every request socket without changing the
route table. The retained profile used physical `Ethernet 2`; the RFC1918
address itself is intentionally not copied into tracked evidence.

PR 34 head `622909e16958e347685a7f6bd83f47fcba21cef8` passed
cross-repository and Guardrails runs `32973602112` and `32973602140`. It merged
as signed platform `master` `583e14a1dea9d5bd97fd964f3aff5115a6bab02a`;
post-merge runs `32974597716` and `32974597784` passed.

## Warmup defect and correction

The source-bound collector v1.1 exposed a separate method defect. `urllib`
sent `Connection: close`, so every discarded warmup and every retained sample
opened a fresh TCP/TLS connection. Direct cold health p95 was `126.2867 ms`
against the `100 ms` stop, while catalog p95 was `125.8498 ms`. A single curl
connection measured the first request at about `124 ms` and the next nine at
`34.6..43.8 ms`, proving that backend execution was not the observed stop and
that the declared warmup never warmed the measured transport.

Collector v1.2 uses one HTTP/1.1 client for all warmups and samples, measures
request-to-first-response-byte, drains response bodies without logging them and
fails the run on any failed sample. Evidence records
`persistent_http1_keep_alive`; the validator fingerprints this optional field,
so older cold-TLS evidence remains readable but cannot compare as the same
environment. A real loopback test proves 55 requests over one accepted
connection rather than relying only on mocks.

PR 35 head `c77331881c5be98c70f61f1d8f9e03c41a531a88` passed
cross-repository and Guardrails runs `32975671786` and `32975671804`. It merged
as signed platform `master` `899e5f01f8317ace7886602c73cd7d7a60f4cd9b`.
Post-merge Release v2 Contract run `32976807912` and Guardrails run
`32976807970` both passed.

## Clean retained result

Both credited records bind clean platform source `899e5f0`, collector `1.2.0`,
the persistent HTTP/1.1 connection policy, 5 discarded warmups, 50 retained
samples, direct source binding and disabled proxy discovery:

| Budget | p95 | Stop | Result | Evidence SHA-256 | Gate SHA-256 |
|---|---:|---:|---|---|---|
| `api.health.current_origin_ms` | `39.0546 ms` | `100 ms` | `PASS` | `b95602996f40515763a90d43e16c4de6d0a0c6939dbabdd793c3c1c7bec22610` | `616d302abdb17b0a9a13372f8f4451198dbb662692268f8c26c7dfe284940683` |
| `api.public_catalog.current_origin_ms` | `40.5479 ms` | `200 ms` | `PASS` | `9e32062dca2fd7ab424b28880df39f17171e27cc066a2d9fda8dec338bc32837` | `94d84a14fa261defd35fc07c9cd48b3f8bdeedacb95df4fdee731253c167daeb` |

The external 21-file diagnostic manifest validates `21/21` and has SHA-256
`3d7499cf3213c86981705b08a62b9d326c47c33d0bce906f2ffa88dbeacd06dd`.
It deliberately retains the ambient, cold-method, dirty-smoke and clean v1.2
records under distinct names rather than rewriting failed evidence into a pass.

## Deployment decision

The owned backend runtime code remains
`243dcbe4727041d62cc0a36e7d2fd5a8530c7c25`. Platform commits after that
runtime modify release documentation, probe tooling and tests, not deployed
backend modules. Public health and catalog return HTTP 200, and the corrected
warm result is well inside both stops. A backend redeploy would therefore
change no relevant runtime byte and is `NOT_REQUIRED_NOT_RUN`.

## Acceptance and ledger decision

The controlled current-origin API-performance slice is `PASS`. The aggregate
`CURRENT_ORIGIN` promotion gate remains open because the default/quick release
gate set, exact candidate binding and post-promotion observation are not proved
by these two endpoints. `BRAIN_ORIGIN` and conditional `RU_ORIGIN` remain
separate and receive no credit from this workstation result.

No execution-ledger row advances. `REL/PERF-001` and `REL_GATE/GATE-E` remain
`I3`; `REL_DOD/DOD-13` remains `I1` because exact Android/Windows, browser-lab,
artifact-comparison and comparable candidate baselines remain incomplete.
Distribution remains `I3=309`, `I2=17`, `I1=37`, `I0=14`; 68 rows remain below
`I3`, split `0/33/14/21` across pre-freeze, candidate, external and deferred
stages.

## Next action

Run the exact 4030 APK on the physical Beeline device once it is visible in
ADB, then retain the Android physical/OEM matrix. Separately run the full
current-origin and Brain-origin candidate-bound release gates. Do not deploy
the backend unless a later source/runtime diff or failed runtime evidence gives
a concrete reason.
