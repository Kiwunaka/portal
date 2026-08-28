# WO-013AK — Exact candidate.3 Gate B decision

Status: `LOCALLY_PROVED_EXACT_CANDIDATE_NO_GO_I3`
Classification: `ACTIVE_EXECUTION_EVIDENCE_AND_REPLACEMENT_FIX`
Phase: `02`, decision replay in Phase `11`
Row: `REL_GATE/GATE-B`
Candidate: `pokrov-1.2.0-candidate.3`
Production/external mutation: `READ_ONLY_INSPECTION_ONLY`

## Outcome

Evaluate Gate B against the frozen candidate instead of transferring local or
post-candidate proof. Typed state, runtime ABI and false-green handling pass,
but the exact platform source fails one deterministic observability support
reference contract on a normal Windows CRLF checkout. Connected recovery also
remains manual. Gate B therefore returns `NO_GO`; the aggregate stays at `I3`
and candidate.3 must be replaced.

## Exact candidate result

| Requirement | Result | Exact boundary |
|---|---|---|
| Connection state machine | `PASS` | Exact client state/diagnostics/migration tests pass `107/107`; Android state/lifecycle/error fencing passes `45/45`; candidate.3 LDPlayer transitions from connecting to an explicit unprotected failure without a VPN interface. |
| Typed runtime contract | `PASS` | Runtime engine passes `63/63` with the exact Windows Core, including 100 start/stop cycles; Core ABI and Windows native contracts pass. |
| Idempotent shutdown/recovery | `MANUAL_OWNER_TEST` | Source and bounded lifecycle tests pass, but exact authenticated Android recovery and live Windows connected TUN/DNS rollback remain unrun. |
| Diagnostics/error catalog | `FAIL` | Exact platform source passes 68 tests and fails `test_checked_in_reference_is_current`: the generator hashes raw CRLF checkout bytes while canonical validation and the signed manifest use LF identity. |
| False-green tests | `PASS` | The exact source matrix passes and the observed candidate.3 negative runtime never reports protection without VPN/tun. |

The minimal correction normalizes CRLF and lone CR to LF in both generator and
validator hashing. The corrected focused suite passes `70/70`. It is not in
candidate.3 and does not rewrite the frozen candidate result.

## Physical lab boundary

The returned Huawei phone runs post-candidate owner-lab build `1.2.0+4031`, not
candidate.3 `1.2.0+30`. Its APK SHA-256 is `1ba37463...`; extracted ARM64 Core
SHA-256 is `efad5822...` and contains separate AWG2 and AWG 3.1 contract
markers. On Beeline LTE the catalog includes Санкт-Петербург, but the one
ordinary connection attempt fails closed before a verified tunnel; Wi-Fi is
restored afterward.

DNS/route settings survive a cold restart: AdGuard DNS, ad blocking, local LAN
direct, AI services and Games remain enabled. The UI states that DNS presets
are DoH inside the VPN tunnel; no DNS-only-without-VPN reachability claim is
made.

Read-only Brain inspection proves the 193-file candidate.3 platform payload is
current and live PostgreSQL contains both AWG material tables. Neither AWG2 nor
AWG 3.1 has a rollout, server record, allowlist, material row or configured
material secret. The disabled `free` node is unhealthy and did not answer the
bounded SSH preflight; active paid nodes were not touched. Therefore no live
AWG connection can be claimed and no deploy is useful until an isolated owned
server exists.

## Evidence digests

| File | SHA-256 |
|---|---|
| `013AK-gate-b-test-evidence.json` | `c880dad8e7f01d0079426005695646f8842b78e07f10872313aee550a66a33a3` |
| `013AK-gate-b-decision.json` | `07d5bcbd5be6631b3648fb10926bb773ccbb4f41fb0d5ba7fbabddad9fe5f21b` |

## Verification

- exact candidate platform observability/release suite: `68 passed, 1 failed`;
- post-candidate corrected suite: `70/70 PASS`;
- exact client state/diagnostics/migrations: `107/107 PASS`;
- exact Android state/lifecycle/error fencing: `45/45 PASS`;
- exact runtime engine with real candidate Windows Core: `63/63 PASS`;
- exact Windows native contract: `7/7 PASS`;
- platform AWG2/AWG 3.1 focused current-source suite: `42/42 PASS`;
- current client AWG runtime suite: `62 PASS`, one declared exact-DLL skip;
- current client DNS/routing suite: `11/11 PASS`;
- physical lab DNS/settings persistence: `PASS`;
- live AWG server/profile/material: `NOT_CONFIGURED`;
- production mutation: none.

## Ledger decision

`REL_GATE/GATE-B` remains `I3`. Its status becomes
`LOCALLY_PROVED_EXACT_CANDIDATE_NO_GO`; there is no index advance because a
candidate-specific explicit failure cannot reach `I4`. Distribution remains
`I4=4`, `I3=312`, `I2=19`, `I1=41`, `I0=1`.

## Next action

Merge the normalization fix only after required hosted checks run, construct a
new signed candidate and replay Gate B. Keep AWG server work separate: acquire
or restore an isolated owned VPS, pin/build the official server, configure the
material secrets, provision only the owner install through the guarded action
path, then run Android/Windows and Beeline evidence with immediate kill/rollback.
