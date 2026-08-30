# WO-013CP — candidate.10 RU control-plane retirement and path classification

## Outcome

Remove two false mandatory delivery targets without hiding live users, then
repeat the canonical direct-RU probe. Brain and the former Free node were both
disabled but still marked `draining`, which intentionally kept them in the
release manifest. Guarded readback proves that neither is a current consumer
route. Separate production backups and compare-and-set updates clear only the
two stale drain flags.

The exact signed candidate artifacts and source tuple do not change. Fresh Pi
runs now evaluate `11` required targets instead of `13` and remain honest
`FAIL 9/11`: NL and RU-SPB time out on the current RU path. Brain and Free are
retired targets, not converted failures or synthetic passes.

## Exact candidate boundary

| Component | Revision or digest |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` |
| Platform source | `209b8f40c36d95f2bbc67caa52a41ecb09f46720` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` |
| Signed release-index source | `fc00b26d402b167260e495eb33397115bef1c317` |
| Manifest SHA-256 | `0711546b0da4b811fba42e1ad543797494e4104bd95251c9e8e8011ac04dff83` |

This is post-signing runtime/control-plane evidence. It does not rebuild,
relabel or promote candidate.10 and does not transfer candidate.8 device proof.

## Brain retirement

Brain had zero user mappings, keys, provisioning jobs, profile references and
enabled pool memberships. Its only apparent consumer count was a stale
`active_clients=14` collector value from 14 February, more than 196 days old.
Current readback proves `x-ui` and Xray inactive, no Xray process and no Xray
listener. The HAProxy-to-empty-backend shape explains the earlier Pi TLS
failure, but there is no consumer dataplane to restore.

A `125041679`-byte production Postgres backup was retained before mutation;
restore was `NOT_RUN`. The guarded serializable operation locked the exact
node row, rechecked all zero-reference preconditions, changed one row from
`disabled + draining` to `disabled + not-draining`, cleared stale current
client counters and passed postcondition readback.

## Former Free-node retirement

Free had zero user mappings, zero non-revoked keys, zero nonterminal jobs and
zero enabled pool memberships. Three revoked keys remain historical. Three
user rows retain the stale `free_profile_standard_node_code=free` marker, but
they have no active Free key and their actual mappings are on paid nodes. The
field is not rewritten in this slice.

A separate `125047166`-byte production Postgres backup was retained; restore
was `NOT_RUN`. The guarded compare-and-set cleared exactly one stale drain flag
and retained the node as disabled. Node-side Xray shutdown remains
`BLOCKED_BY_ACCESS`; removing a dead control-plane delivery target does not
claim that inaccessible external runtime has been inspected or stopped.

## Fresh RU-origin result

The canonical Pi runner and uploader both exit successfully after each
control-plane change. The dynamic manifest revisions remove Brain first and
then Free. Two final `11`-target runs agree:

| Slice | Result |
|---|---|
| Canonical public and environment controls | `4/4 PASS` |
| Delivery nodes other than NL/RU-SPB | `5/5 PASS` |
| Delivery NL | `FAIL tcp_connect_timeout` |
| Delivery RU-SPB | `FAIL tcp_connect_timeout` |
| Overall RU-origin | `FAIL — 9 PASS / 2 FAIL` |

RU-SPB passed the earlier candidate.10 run and fails the two fresh runs. This
is retained as changed origin evidence, not rewritten history. The physical
phone is unavailable and untouched; the result comes from the owned direct-RU
Pi only.

## Bounded NL classification

NL remains enabled with live users and cannot be excluded. Brain-origin NL
passes, Pi DNS resolves to the owned NL address and Xray owns TCP/443. The Pi
source is not in either Fail2ban jail. Local firewall inventory has no
TCP/443-specific drop, reject, rate or connection-limit rule.

One bounded packet capture ran only during a canonical Pi probe and observed
no matching packet at NL. The capture contained no retained addresses and was
deleted after count extraction. Together with repeated Pi timeouts, the
bounded classification is `RU_TO_NL_PATH_FAILURE_BEFORE_OBSERVED_SERVER_INGRESS`.
It is not an Xray, certificate, DNS or local firewall defect. No further NL or
SPB loop is justified without new route/provider evidence.

## Smart DNS boundary

The owner-reported Timeweb edit is not visible on the delegated zone. Fresh
direct checks against all four authoritative servers still return no A record
for `dns.pokrov.space` (`0/4`). TTL does not explain an answer absent directly
from authoritative servers. Certificate issuance, root-only runtime material,
Smart DNS server APPLY and the separate frontend route APPLY remain `NOT_RUN`.

The already-proved foreign `it` frontend and exact bundle stay ready. The next
safe step is to make the A record authoritative `4/4`, then execute the
existing ACME/runtime PLAN/APPLY and server/frontend rollback sequence before
real ChatGPT, Gemini and Xbox access, attribution and leak checks.

## Release interpretation

- `FRKN_PLAN/W9-02` remains `I1`: current and Brain origins pass, but RU is
  still `FAIL`, now `9/11` on two path failures.
- `FRKN_SMART_DNS/SMARTDNS-01` remains `I3`: frontend and bundle readiness do
  not substitute for authoritative DNS, certificate, service or access proof.
- Candidate.10 Gate F is not regenerated because its required RU check still
  fails. The exact retained decision remains `NO_GO 6 PASS / 13 non-PASS / 1
  FAIL` with Gate G unauthorized.

No candidate artifact, source commit, node runtime, payment/provider state,
physical device, public tag/release, Store object or stable pointer changed.

## Evidence

The tracked normalized record is
`evidence/013CP-candidate10-ru-control-plane-retirement/013CP-candidate10-ru-control-plane-retirement.json`.
It binds the redacted external plans, backups, applies, Pi artifacts, NL
classification and authoritative-DNS check by SHA-256. No raw address, endpoint,
credential, key, runtime material, customer identifier or provider payload is
tracked.
