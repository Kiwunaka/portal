# WO-013BZ — candidate.7 runtime, RU Pi baseline and Gate F

## Outcome

Bind fresh candidate.7 current- and Brain-origin evidence, repeat the bounded
AWG2/AWG3.1 LDPlayer slice on the exact signed x86_64 bytes, accept the
owner's local Raspberry Pi 4 as a direct terminal-only RU probe, and generate
the first digest-bound candidate.7 Gate F without promoting any older proof.

Gate F validates all 19 pointers with zero validation errors and returns
`BLOCKED`: `4 PASS`, `15 non-PASS`, `0 FAIL`. Supply chain,
release-doc/manifest binding, current-origin and Brain-origin pass. The result
does not authorize Gate G, a tag, public assets, stores or the stable pointer.

## Exact candidate identity

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.7` |
| Operational ID | `81b5fc35a975384a84f62e20c3c1f31f2f3807ff77fb1daf334c97211fea8f03` |
| Platform source | `af259f377ec7a3cd757f0f43762154dd25e09f94` |
| Client source | `b2497af7704d0aa6901541e175ce154b0eab05d7` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Release-index source | `f6917c8264015aee72fe51126943b08191e85b07` |
| Signed manifest | `fb1d7049deaf3047456377e675c45a2177c76c51f8792703886ca2bcca5490ce` |
| Signature | `2b20ed7881c36f72b0777aa8c2a571e192895df15eb598165d5e93ae68418abf` |
| Receipt | `ff93d33bf0ef4b0e1b036ee1be5b83f769791295d0e1cfcde0a1f854b2799b04` |
| Android x86_64 | `3d95d82d8290150fadd13600b79eca26326792407532f571909d8df224df6fa4` |

Candidate.7 intentionally reuses candidate.6's six unchanged binary files.
The current device readback matches the candidate.7 x86_64 subject exactly;
no older runtime result is relabelled.

## Current- and Brain-origin

Current-origin ran from a clean detached checkout of the exact platform
source with five warmups and 50 retained samples per endpoint:

| Budget | p95 | Limit | Result |
|---|---:|---:|---|
| health | `65.5636 ms` | `100 ms` | `PASS` |
| public catalog | `67.4524 ms` | `200 ms` | `PASS` |

Brain used the owner's trusted SSH configuration in read-only mode. Exact
runtime source passes `197/197`, readiness passes `23/23`, and all seven live
enabled delivery ports are open. No remote content, alias, address or
credential is retained, and no deploy or restart occurred.

## Exact LDPlayer AWG rehearsal

The installed package is exact `1.2.0+4046` candidate.7 x86_64. Separate
owner-only bindings selected `awg2_lab` and `awg31_lab`. Both paths:

- materialized one managed `awg` endpoint and one peer;
- configured three managed DNS servers;
- created the app-owned Android VPN service and TUN;
- avoided fatal exceptions, ANRs, native fatal signals and security errors.

AWG2 ended with a failed Core egress probe. AWG3.1 reached the same service,
TUN and DNS shape and the probe stalled before bounded disconnect. Because
the byte-identical ordinary control already reproduces the emulator egress
boundary, the candidate.7 label is
`BLOCKED_BY_LDPLAYER_NETWORK_CURRENT_ORIGIN`. This is neither an AWG protocol
PASS nor an AWG protocol FAIL and does not replace physical Android proof.

Cleanup passes: the exact install resolves back to
`legacy_reality_fallback`, its lab cohort and allowlist membership are absent,
the managed profile contains no AWG endpoint, and both the service and TUN are
stopped. Encrypted server-side owner-lab material rows are not claimed deleted;
they are unreachable by this restored install unless a later guarded bind is
applied again.

## Raspberry Pi direct RU baseline

The existing trusted local SSH profile resolves to a Raspberry Pi 4 running
Debian 13 on `aarch64`. A read-only probe proves a direct, non-tunnel RU exit.
System DNS resolves ChatGPT, the OpenAI API, Gemini, Xbox and POKROV (`5/5`),
and public Cloudflare/Google DoH requests return `200` (`2/2`).

Observed HTTP results are intentionally interpreted by layer:

| Target | HTTP | Bounded interpretation |
|---|---:|---|
| `chatgpt.com` | `403` | DNS and TLS route exist; the edge refuses direct access |
| OpenAI API without credentials | `401` | transport reachable; authentication is expected |
| Gemini | `200` | direct web access available on this RU line |
| Google GenAI API without credentials | `403` | transport reachable; no authorized API request was made |
| Xbox | `307` | direct web redirect is reachable |
| POKROV | `200` | owned public site reachable |

This result proves that plain DNS is not the observed ChatGPT failure. A
normal resolver change alone cannot honestly be advertised as the fix for
this trace. The planned Smart Access path still needs an owned proxy/fronted
route, live resolver/SNI attribution, access, leak/lifecycle and rollback
evidence. No Smart DNS runtime was installed on the Pi or any server.

The Pi baseline is useful `RU-origin` environment evidence but remains below
the Gate F exact-candidate requirement: it did not run the Android/Windows
client, the canonical RU runner/uploader, or an owned Smart DNS service.
Therefore Gate F `ru_origin` stays `NOT_RUN`, not PASS.

## Gate F and remaining blockers

The first candidate.7 decision is `BLOCKED` at `4/19 PASS`, `15/19 non-PASS`,
`0 FAIL`. The major open rows are:

- exact Gates A-E/manual stop-ship aggregate and no-open-P0 attestation;
- physical Android AWG/WARP/per-app/network-change/OEM/leak/endurance matrix;
- isolated Windows install/service/IPC/TUN/DNS/AWG/recovery/uninstall matrix;
- exact-candidate RU client or canonical runner evidence;
- owned Smart DNS live access and rollback;
- provider, Operator, legal/commercial, comparable-device performance and
  post-public-promotion health.

Hosted platform jobs remain zero-step `SKIPPED_BY_OWNER` under the no-purchase
`OWNER_SOLO_EXCEPTION`. They are not PASS and do not require a paid GitHub
plan under the owner's chosen release policy.

`REL_GATE/GATE-F` remains `I3` with stronger status
`SIGNED_CANDIDATE7_GATE_F_BLOCKED_4_PASS_15_NONPASS`. `FRKN_PLAN/W9-02`
remains `I1`: current and Brain pass, while exact-candidate RU remains open.
`FRKN_PLAN/W9-05` remains `I1`. No completion-index level changes.

## Evidence and mutation boundary

Machine evidence is under
`evidence/013BZ-candidate7-runtime-ru-pi-gate-f/`:

| Evidence | SHA-256 |
|---|---|
| normalized runtime/origin evidence | `c6527e4d29e2076b662ffa8fbde381fe7080b1a2f8b917aa1e9a4471d9e23269` |
| Gate F evidence | `41199847011421f69fdd1b845b4bc251256da9a64ee0956fd2103110e823ea7e` |
| Gate F input | `eaea665dc36a64a91813fbfd289f07e6af432809efe3d35948a7d98610672262` |
| Gate F decision | `97b89b65b74b99ef19970ce1fcf19833493582bdd27d12915ae8f15fd7152caf` |
| signed/runtime binding | `46d531eff06f086cb0a3e833aab73fbc92abda4945a44a9ba4b376a6f60d8734` |

The owner-only AWG device policy was temporarily changed and restored. No
entitlement extension, payment action, production deploy, repository
visibility change, tag, public release, store object, stable pointer or Gate G
authorization occurred. No raw IP, hostname, SSH alias, device serial,
credential, private key, runtime profile, endpoint, customer data or provider
payload is retained.

## Verification

```text
python -B scripts/api_latency_probe.py <candidate.7 current-origin health and catalog inputs>
# PASS: 50/50 samples per endpoint, both p95 budgets met
python -B scripts/remote_brain_runtime_source_probe.py <trusted SSH config, exact af259f3 source>
# PASS: 197/197
python -B scripts/verify_brain_ready.py <trusted SSH config> --repeat 5
# PASS: 23/23
python -B scripts/remote_brain_network_probe.py <trusted SSH config> --live-enabled-nodes --redact
# PASS: 7/7
python -B scripts/release_1_2_gate_f.py <signed candidate.7 inputs> --expect-blocked
# BLOCKED: 4 PASS / 15 non-PASS / 0 FAIL / 0 validation errors
```
