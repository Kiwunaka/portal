# WO-013CU — candidate.10 bounded platform security scan

## Outcome

Retain one source-exact, read-only security review for the platform revision in
signed candidate.10 without converting partial coverage into a release pass.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` — unchanged |
| Platform source | `209b8f40c36d95f2bbc67caa52a41ecb09f46720` |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` — not reviewed by this scan |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` — not reviewed by this scan |
| Scan ID | `c31fb013-2058-417d-b929-ea98ecd39f87` |
| Scan mode | standard, source-only, read-only, offline after launch |
| Tracked inventory | `2744` files |
| Completed at | `2026-08-30T08:33:59.291807Z` |

No candidate byte, runtime, server, DNS record, tag, public release, Store
object or stable pointer changes.

## Reviewed trust boundaries

Nine bounded surfaces cover public authentication and sessions, Operator v2
authentication/RBAC/CSRF/step-up, payment callbacks and entitlement mutation,
private support attachments and encrypted bundles, HMAC-authenticated internal
ingest, outbound HTTP/SSRF boundaries, SSH/release operations, frontend script
injection and sensitive browser storage, and tracked high-signal credential
patterns.

The scan reports zero validated findings and no validated P0/P1 in those
reviewed surfaces. Existing controls include signed and expiring sessions,
operator HMAC-stored opaque sessions plus CSRF/origin/step-up checks,
signature-before-fulfilment payment callbacks with durable idempotency,
owner-bound private attachments with magic-byte and quota checks, body-bound
internal HMAC with durable nonce replay protection, fixed provider boundaries,
and reject-unknown SSH host-key behavior by default.

Credential-pattern matches are synthetic redaction fixtures/tests. This was
not an entropy-based or Git-history secret scan.

## Honest limitations

Coverage is `partial`, not complete. The scan did not execute application code,
tests or a production runtime; did not validate deployed CORS, cookies, trusted
proxy values, panel exposure, UFW or known-hosts state; did not query a
dependency vulnerability database; and did not review all 2744 files line by
line. The independent delegated baseline was unavailable in this session and
TAC status could not be verified because its connector was unauthenticated.

`SECURITY.md` still permits browser bearer/localStorage only during the current
transition window. Its residual XSS token-theft exposure remains a deferred
cookie-only migration, not a new P0/P1 finding from this bounded scan.

Therefore the broad Gate F `no-open-P0` attestation remains `MISSING`. The scan
adds useful source evidence but cannot turn that row into `PASS`, cannot repair
the RU-origin `FAIL`, and does not regenerate Gate F.

## Concurrent Smart DNS state

At `2026-08-30T08:36:46Z`, all four delegated Timeweb authoritative servers
still return `NXDOMAIN` for `dns.pokrov.space`. The two common mis-entry forms
`dns.pokrov.space.pokrov.space` and `dns.dns.pokrov.space` also return
`NXDOMAIN`. TTL is not involved because no authoritative record exists.
Trusted-certificate issuance and Smart DNS server/runtime APPLY remain
`NOT_RUN`.

Normalized retained metadata is in
`evidence/013CU-candidate10-bounded-security-scan/013CU-candidate10-bounded-security-scan.json`.

## Release decision

Candidate.10 and its signed manifest stay unchanged. Gate F remains
`NO_GO 6 PASS / 13 non-PASS / 1 FAIL`; all five source-plan gates remain
`BLOCKED`. No Gate G or public/stable promotion is authorized.
