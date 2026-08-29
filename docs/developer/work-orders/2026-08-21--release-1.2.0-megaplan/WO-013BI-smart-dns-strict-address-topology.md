# WO-013BI — Strict Smart DNS bind-scope correction

## Outcome

Replace an intermediate, non-authoritative shell address counter with a strict
structured audit before it could be used to justify a Smart DNS deployment.

The short-lived v2 PLAN parser could overcount private/global-scope interface
rows and failed to match every exact TCP/443 bind. It therefore produced a
false lead that the multi-address `de` node might contain unclaimed public
addresses. No APPLY, DNS, certificate, firewall, service, frontend or routing
mutation followed that result. The v2 reports are rejected as
`INVALID_INTERMEDIATE_NOT_RELEASE_EVIDENCE`.

Platform `ff7e653bf8266488be2db04aadd5f28eb90cf0aa` replaces that logic with a
bounded Python helper. It parses structured `ip -j -4` data, accepts only
globally routable IPv4 values, parses IPv4 and dual-stack `ss` listener rows,
and emits only booleans plus a `none`/`one`/`multiple` unclaimed-address bucket.
It never returns an address, process name, listener owner or runtime material.
The report schema advances to `pokrov-owned-smart-dns-remote-operation-v3` so
the rejected v2 result cannot be mistaken for current evidence.

## Exact current artifact and verification

- exact platform source:
  `ff7e653bf8266488be2db04aadd5f28eb90cf0aa`;
- current inactive bundle: `2912449` bytes, SHA-256
  `79cf040a6725cfb35f232242fefc8dfc61fd472448bb3d14b443a7472db0de8c`;
- two independent builds are byte-identical and pass bundle verification;
- canonical/client policy SHA-256 remains
  `b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa`;
- focused builder/parity/installer tests: `23/23 PASS`;
- focused Ruff, Python compile, script manifest and policy parity: `PASS`;
- Go `1.25.13` test/vet: `PASS`.

## Strict all-active-node PLAN

The exact v3 installer and bundle ran in read-only PLAN mode against `de`,
`us`, `ru`, `ru_spb`, `pl`, `it` and `nl`:

| Result | Count |
|---|---:|
| active nodes checked | `7/7` |
| TCP/443 busy | `7/7` |
| expected-address exact bind | `1/7` (`de`) |
| wildcard/dual-stack bind | `6/7` |
| any unclaimed globally routable IPv4 outside the bind scope | `0/7` |
| runtime material ready | `0/7` |
| mutation performed | `0/7` |

On `de`, the strict helper found two globally routable assigned IPv4 values and
two exact TCP/443 binds. A separate in-memory structured replay produced the
same `2 assigned / 2 bound / 0 unclaimed` result. It also compared active AWG
endpoint material without returning it; this did not reveal or create a spare
address. The other six nodes have a wildcard or dual-stack TCP/443 listener,
so every assigned address is covered.

## Release interpretation

- `FRKN_SMART_DNS/SMARTDNS-01` remains `I3`.
- The no-purchase policy remains intact, but the current owned topology has no
  safe address-specific deployment target.
- The only zero-purchase route is a separately reviewed migration that
  deliberately frees an existing address with exact frontend rollback, or
  leaving the Smart DNS lab undeployed.
- No candidate, service, DNS/SNI relay, access, leak, rollback, origin or
  promotion proof is created.

Machine evidence:
`evidence/013BI-smart-dns-strict-address-topology/013BI-smart-dns-strict-address-topology.json`.
Its SHA-256 is
`c845a20e9b0ebd8ddc7273d7eca5f0905efaab8a886a9dc092fb3207d77f268e`.
It retains no address, hostname, credential, key, runtime configuration,
customer data or raw provider response.
