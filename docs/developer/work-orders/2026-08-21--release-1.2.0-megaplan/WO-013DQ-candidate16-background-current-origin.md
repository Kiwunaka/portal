# WO-013DQ — candidate.16 background current-origin and STOP-SHIP slice

Status: `CURRENT_ORIGIN_API_PERFORMANCE_PASS; STOP_SHIP_LOCAL_7_OF_7_PASS; AGGREGATE_GATES_OPEN`
Classification: `ACTIVE_EXECUTION_EVIDENCE`
Phase: `11`
Candidate: `pokrov-1.2.0-candidate.16`
Production/external mutation: `NONE`

## Outcome

Use only background terminal, ADB and trusted Pi commands while the owner keeps
control of the PC. No screen input, application launch, VPN start, device
setting, route, DNS, server, provider or release pointer is changed.

The exact candidate.16 platform/client/Core source tuple is clean. The
permanent STOP-SHIP registry passes all `7/7` exact-source regression anchors,
and GitHub reports zero open organization issues with either a `P0` label or
`P0` in the title. This is not the aggregate no-open-P0/false-green/secret-leak
attestation: one manual gate, hosted execution and complete live-device
coverage remain open.

Fresh current-origin health and public-catalog measurements pass from a bound
physical Ethernet source while the workstation's ambient default route is a
tunnel. Proxy discovery is disabled by the collector, and no literal source
address is retained in tracked evidence.

## Exact source and performance result

| Item | Result |
|---|---|
| Platform | `719e23dc49407beb9ae30d98d17d4b73d18ae37c`, clean |
| Client | `75ba7e721cfee486f7189edd51de97aba2746722`, clean |
| Core | `cd8f0f4169d570d693992a959d81d17c2c44884d`, clean |
| Health | `PASS`, 50 samples, p95 `37.8716 ms <= 100 ms` |
| Public catalog | `PASS`, 50 samples, p95 `48.2119 ms <= 200 ms` |

The first collector invocation used the marketing host and correctly stopped
on HTTP `308`. It produced no gate artifact. The repeated run uses the
canonical API host and passes both budgets. Authenticated client egress is not
part of these public API measurements, so the full Gate F `current_origin` row
remains non-PASS.

## STOP-SHIP and P0 boundary

The exact-source report records:

- permanent regressions: `7 PASS / 0 FAIL`;
- hosted branch controls: two `BLOCKED_BY_ACCESS`, one
  `FAIL_UNPROTECTED`;
- reviewer controls: three explicit `OWNER_SOLO_EXCEPTION`, with no
  independent review claimed;
- one manual live gate still open;
- aggregate result: `NO_GO`.

The unprotected branch and unavailable paid protection are accepted owner
policy, but they are not converted into a technical PASS. Candidate.16's lab
failure remains fail-closed under WO-013DF. Exact-source privacy regressions
also pass: platform release-health/bundle ingest/upload `53/53`, client
release-source logging across `145` production files plus four negative
fixtures, observability runtime `29/29`, and support bundle `15/15`. These
source tests do not replace a complete live-device/runtime owner attestation,
so Gate F's `no_open_p0_false_green_or_secret_leak` remains `MISSING`.

## Background device and DNS boundary

Both authorized Android targets still contain exact `1.2.0+4049` and have no
`tun0`. The physical Android app is absent from the process table; LDPlayer's
existing process remains present from prior state. Both resolve and reach the
public Smart-DNS hostname. LDPlayer and the trusted Pi receive expected HTTP
`400` from an empty DoH request over trusted TLS.

Windows resolves a general control hostname and completes general HTTPS, but
its current system resolver does not resolve the Smart-DNS hostname. LDPlayer
and Pi succeed at the same time, so this is classified as a current Windows
resolver-context issue, not a global Smart-DNS outage. No cache flush or DNS
adapter change is made. WO-013DP's bounded four-query LDPlayer policy matrix
remains the stronger Smart-DNS policy evidence.

## Provider identity boundary

Datalix documents a background noVNC WebSocket path, but it requires an API-
or session-token plus the service ID. No provider token is available to this
background slice.
Both DE SSH ports currently fail to provide a complete banner from this
origin, no suitable pinned match is established, and trusted state remains
unchanged. WO-013DM therefore stays authoritative:
`BLOCKED_BY_HOST_IDENTITY` until the provider console returns an out-of-band
fingerprint for exact comparison.

## Evidence

- normalized record:
  `evidence/013DQ-candidate16-background-current-origin/013DQ-candidate16-background-current-origin.json`;
- normalized record SHA-256:
  `600f6dfdff2ca5a9ea920fbb554b22b2b189bbdb39d9a10d6eea52d670cca906`;
- health gate SHA-256:
  `3ab90b74d01cb516a61a0f829d3a6fcefa4ba4b37a6aa1b385a34eb868ba1b30`;
- catalog gate SHA-256:
  `8f26285730b717ba2679d1cfe1c848886fd4e909267462a88f273f600d8bd825`;
- private STOP-SHIP report SHA-256:
  `ed45235e9457139bd01fb50bd3a984b6137517678f756e404dfb293383e2f385`.

Private collector records remain outside Git because they contain the local
source address. Tracked gates retain only the environment fingerprint,
candidate source, sample counts, thresholds and results.

## Decision

`REL/PERF-001`, `REL_DOD/DOD-01/DOD-12/DOD-13`, `REL_GATE/GATE-E` and the
exact-source OBS privacy rows gain stronger candidate evidence without index
promotion. Device performance, authenticated client egress, connected Windows,
provider identity and the aggregate attestation remain open. Gate F stays
`NO_GO 2/17/2` and is not regenerated from an unchanged decision boundary.
Gate G, public assets, Store submission and stable promotion remain
unauthorized.
