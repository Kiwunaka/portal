# Windows managed switching — 2026-09-08

PASS_BOUNDED: ordinary UI reconnect AWG3.1 → AWG2 → AWG3.1 on the installed
Win11 v3 package, client `6fc1e84` / Core `8dc57a8`. Three steady observations
confirmed running/Core/DNS/egress readiness, staged/effective equality, one
TUN and health 200. Protected service-file hashes changed to AWG2 and returned
exactly to the first AWG31 hash. Persisted revisions followed the server choice.
Every disconnect removed TUN and restored route/DNS hashes; 305 installed
package hashes remained exact. [Source-bound evidence](evidence/windows-switching-2026-09-08.json).

Independent route proof is still BLOCKED_BY_ACCESS: the external IP hash was
identical before and during VPN; DE SSH failed host-key verification. Brain's
trusted connection did not supply a matching stored target key. No host-key
check was bypassed or trust record replaced. The owner was asked for an
independently verified fingerprint; server peer counters were not collected.
The UI retained its saved Milan location and unresolved access label while the
fixed lab transport was DE; full effective-location presentation remains open.

The owner's expanded test authorization is retained in
[OWNER-DECISIONS-2026-09-08.md](OWNER-DECISIONS-2026-09-08.md). Three temporary
cohort switches affected only the exact test installation. The full original
rollout configuration was restored; entitlement and endpoint material unchanged.
Sampler stopped, temporary task removed, clone shut down with NIC none. Host
route/DNS hashes match the retained baseline. No product code changed, no new
candidate was created, and no push, merge, deployment or publication occurred.

Client commands and original/normalized evidence hashes are retained at
`E:/r12client/docs/operations/evidence/2026-09-08-r12-managed-switching/`.
N01/W01 advance for this bounded installed slice; parent statuses remain active.
N03, sleep/crash, WFP, Win10, remaining protocols and exact final candidate gates
are not closed by the three successful service observations.

Client evidence commit: `809363b`. Handoff validation: 33 docs tests PASS;
platform-context audit PASS; package validator PASS (83 R12 IDs, 378 legacy IDs,
295 links); explicit-root client seed/docs PASS; 23 retained Git blob hashes
verified. `git diff --check` PASS. Concurrent generated files remain untouched.
