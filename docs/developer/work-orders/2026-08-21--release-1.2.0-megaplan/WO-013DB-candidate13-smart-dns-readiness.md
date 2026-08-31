# WO-013DB — candidate.13 Smart DNS `it` readiness refresh

Status: `PASS_READ_ONLY_PLAN; BLOCKED_BY_AUTHORITATIVE_DNS`

Observed: `2026-08-31T00:38:21Z`

## Scope

Refresh the owned Smart DNS `it` canary against current platform `master`
without changing DNS, the node, HAProxy, Xray, the Smart DNS service, client
state, candidate artifacts or release pointers.

This slice does not transfer candidate.8/10 runtime credit into candidate.13.
It proves only the current immutable bundle and read-only server plans.

## Exact inputs

- signed candidate: `pokrov-1.2.0-candidate.13`;
- candidate platform source: `7d983c0ab52e9c01f94da8916a6bca6a0039be8d`;
- current platform verification source:
  `a895033279b175ea885d2df5996ca6f90b5f7cc2`;
- Smart DNS bundle source:
  `650dc3fab8053736cfb976d4a34ea1f2f0b40349`;
- bundle SHA-256:
  `cda97da16a892c1a8563bd20434cd749a2174c192ba722147091a3e1c14a0225`;
- bundle size: `2916305` bytes;
- selected owned node: `it`;
- authorized DoH hostname: `dns.pokrov.space`;
- listener contract: HAProxy public TCP/443 to Smart DNS loopback
  TCP/18443 with PROXY protocol v2.

## Verification

The focused bundle/runtime/frontend/policy suite passes `53/53`. The exact
retained bundle passes the immutable bundle verifier. A local Go executable is
not installed, so this slice does not claim a fresh Go test or rebuild; the
previous two byte-identical builds remain retained evidence and are not
silently reclassified as this run.

The current runtime-material PLAN reaches the owned `it` node using pinned SSH
host identity and reports:

- root and all required tools present;
- TCP/80 free;
- UFW active with no temporary TCP/80 rule yet;
- upstream DoT reachable;
- no certificate, private key, runtime directory or Smart DNS service present;
- no returned host, address, credential, private key or runtime material;
- `mutation_performed=false`.

The current frontend PLAN reports active HAProxy on public TCP/443, valid
current configuration, no Smart DNS route, no loopback listener, inactive
Smart DNS and a valid generated candidate route for TCP/18443. The plan binds
the actual runtime digests rather than assuming that the repository fixture is
the live base. No frontend or service mutation occurred.

Direct DNS queries to all four delegated Timeweb nameservers return no A record
for `dns.pokrov.space`. Both common mistaken names also return no A record. All
four nameservers expose the unchanged SOA serial `2026082102`; this is an
unpublished-zone state, not a TTL propagation delay.

## Decision

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3`. Runtime/certificate APPLY, service
install, frontend APPLY, live DoH, external access and client access checks are
`NOT_RUN`. The guarded runtime script correctly fails closed until one unique
public A record matches the owned `it` node.

Candidate.13, Gate F, Gate G, public release, Store and stable pointers are
unchanged. The next Smart DNS action is owner publication of the DNS-only A
record followed by a fresh `4/4` authoritative readback. Only then may the
already authorized receipt-bound ACME/runtime, service and frontend sequence
run.

## Evidence

- `evidence/013DB-candidate13-smart-dns-readiness/013DB-candidate13-smart-dns-readiness.json`
- external sanitized runtime PLAN SHA-256:
  `b9785f1c4d579e663f70bca6b75ab9c03cbf7edbc8923190f26906a36ecd1f37`;
- external sanitized frontend PLAN SHA-256:
  `afb102b24321e9c1460f37b26303ab56494195032bdcef3bd91a6f65fc337594`.

## Rollback

No rollback ran because no mutation occurred. The existing receipt-bound
automatic frontend rollback and explicit rollback procedure remain unchanged.
