# WO-013CV — candidate.10 bounded client security scan

## Outcome

Retain one source-exact, read-only security review for the Android/Windows
client revision in signed candidate.10 without converting partial coverage
into a release pass.

## Exact boundary

| Item | Value |
|---|---|
| Candidate | `pokrov-1.2.0-candidate.10` — unchanged |
| Platform source | `209b8f40c36d95f2bbc67caa52a41ecb09f46720` — not reviewed by this scan |
| Client source | `3459438f02bd774e722b1b858e7f7f16d57a9f5c` |
| Core source | `a45d69e40ed7d892619a2b5c4592a527f630665e` — not reviewed by this scan |
| Scan ID | `1ea1b1de-8f30-460a-9874-3e8bd8a47329` |
| Scan mode | standard, source-only, read-only, offline after launch |
| Tracked inventory | `735` files |
| Completed at | `2026-08-30T08:56:44.545684Z` |

No candidate byte, app runtime, server, DNS record, tag, public release, Store
object or stable pointer changes.

## Reviewed trust boundaries

Eight bounded surfaces cover secure session storage and legacy migration;
Android exported components, VpnService/TUN/DNS/egress and false-green state;
direct/store update download and install authority; Windows LocalSystem IPC,
profile storage, egress commit and recovery; loopback/managed transport and
direct-DoH policy; and diagnostic/export confidentiality.

The scan reports zero validated findings and no validated P0/P1 in those
reviewed surfaces. The main Android presentation does not treat an established
TUN alone as a verified connection: green state requires healthy DNS, uplink
and Core egress evidence. Required egress failure invalidates and tears down
the runtime. Windows enters `running` only after authenticated egress succeeds.

Android direct update metadata is constrained to canonical HTTPS GitHub
release paths, exact size and SHA-256, expected package/version/ABI, a newer
version code and signer continuity before opening a selected system installer.
The store flavor has no direct-install permission or provider. Windows IPC is
local-only, caller-authorized and bounded by a random session token, deadline,
correlation and nonce replay rejection.

## Honest limitations

Coverage is `partial`, not complete. The scan inventoried 735 tracked files but
performed risk-selected review rather than an exhaustive line-by-line audit.
It did not execute tests, the application, an emulator, a physical device, a
Windows VM, production services or packaged APK/EXE/DLL artifacts. It did not
query a dependency vulnerability database, inspect an SBOM or review Git
history. The independent delegated baseline was unavailable in this session.

Android's custom-scheme acquisition handoff remains deferred: the client
validates exact scheme/host/path/purpose and an opaque bounded handle, but
server-side single-use and ownership semantics are outside this repository, so
no P0/P1 attack path was established by this scan.

Therefore the broad Gate F `no-open-P0` attestation remains `MISSING`. This
source evidence cannot replace binary/runtime/device proof, cannot repair the
RU-origin `FAIL`, and does not regenerate Gate F.

## Concurrent Smart DNS state

At `2026-08-30T08:58:12Z`, all four delegated Timeweb authoritative servers
still return `NXDOMAIN` for `dns.pokrov.space`. TTL is not involved because no
authoritative A record exists. ACME and Smart DNS runtime APPLY remain
`NOT_RUN`.

Normalized retained metadata is in
`evidence/013CV-candidate10-client-security-scan/013CV-candidate10-client-security-scan.json`.

## Release decision

Candidate.10 and its signed manifest stay unchanged. Gate F remains
`NO_GO 6 PASS / 13 non-PASS / 1 FAIL`; all five source-plan gates remain
`BLOCKED`. No Gate G or public/stable promotion is authorized.
