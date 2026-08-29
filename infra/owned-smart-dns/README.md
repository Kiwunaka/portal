# POKROV owned Smart DNS laboratory

This directory contains source for a default-off, source-only Smart DNS
laboratory. It is not deployed and contains no runtime host, certificate,
private key, token, or retained DNS/SNI data.

The guarded bundle installer supports two explicit, default-off listener
modes. `dedicated` owns one public TCP/443 listener and its UFW rule. `fronted`
shares an already owned HAProxy TCP/443 frontend without buying another address
and binds only to `127.0.0.1:18443`; it never changes the public firewall. The
fronted mode requires one strict PROXY protocol v2 TCP IPv4/IPv6 header without
TLVs and restores the original source address before applying per-source
limits. Missing, direct, malformed, non-TCP, TLV-bearing, or non-loopback
listener combinations fail closed. Server install and frontend migration
remain separate guarded operations with separate receipts and rollback.

In both modes, TLS for the exact DoH hostname is terminated locally at
`/dns-query`; other ClientHello records are accepted only when the normalized
SNI matches the canonical AI or gaming-service suffix policy. Application TLS
is passed through without certificate replacement or decryption. Missing,
malformed, ambiguous, ECH-concealed, or non-allowlisted SNI is closed before
any origin connection.

The DoH endpoint is deliberately not recursive. An allowlisted `A` question
receives the owned proxy IPv4, `AAAA`, `HTTPS`, `SVCB`, and other allowed types
receive `NOERROR/NODATA`, and every question outside the allowlist receives
`REFUSED`. This prevents the service from becoming an open recursive resolver
without placing a bearer token in the client's persisted URL or profile.

The proxy resolves the real origin through one fixed authenticated DNS-over-TLS
upstream, never through its synthetic DoH path. It connects only to TCP/443 and
rejects non-public answers. Global, per-source, request, parser, handshake,
connect, idle, and lifetime limits are mandatory. Runtime logs contain startup
state and the policy digest only; request names, SNI, source addresses, and raw
payloads are not logged.

Application origin connections leave directly from the machine running this
service. There is no outbound proxy, WARP, VPN, or foreign-hop option in the
current contract. The deploy target is therefore also the application egress:
an RU-hosted instance is not a valid geo/access bypass merely because its DoH
answer and TLS relay work. The preferred access topology is a colocated foreign
owned frontend and loopback backend; any alternate egress chain needs a
separate source, trust-boundary, lifecycle, rollback, and live-access proof.

Local verification from this directory uses the pinned Go module:

```powershell
E:\path\to\go.exe test ./...
E:\path\to\go.exe build ./cmd/pokrov-smart-dns
```

The bundle builder canonicalizes every packaged text member as UTF-8 with LF
line endings. Windows CRLF checkouts therefore produce the same policy digest
and archive bytes as Linux checkouts. UTF-8 BOMs, undecodable bytes and lone
carriage returns fail closed instead of entering the signed supply chain. The
cross-repository policy-parity checker applies the same canonicalization before
byte comparison and reports that same canonical digest.

`config.template.json` and `config.fronted.template.json` are not runtime files.
Render one template's placeholders outside Git into
`/etc/pokrov-smart-dns/config.json`, retain it with owner/group-only
permissions, and validate it with `-check` before any separately authorized
install. The TLS private key stays outside the release bundle. Select the
matching installer mode explicitly. A fronted install requires
`FRONTED_LOOPBACK_PROXY_V2`, proves the loopback listener and a local
PROXY-v2/TLS/DoH probe, and leaves public TCP/443 and UFW untouched. It does not
authorize the separate HAProxy frontend migration. Both modes still require
one unique owned public IPv4 for the synthetic `A` answer.

No active POKROV delivery node currently has an unclaimed TCP/443 listener.
Deployment therefore requires either a deliberately freed owned public IPv4
or a reviewed SNI-mux migration on an existing owned frontend, plus an exact
candidate bundle, guarded PLAN/APPLY/ROLLBACK tooling, runtime material and
owner authorization. Brain is not an automatic target: control-plane and
data-plane risk must be reviewed before choosing a frontend. DNS reachability
and a verified TLS handshake are not proof that ChatGPT, Gemini, Xbox, or a
game works end to end.

The guarded PLAN reports only sanitized bind-scope facts: whether TCP/443 is
free, wildcard-bound, bound to the expected owned IPv4, or bound only to
another address; whether the expected IPv4 is assigned; and whether the node
has multiple global IPv4 addresses. A strict Python helper parses structured
`ip` data and `ss` listener rows, then reports only a `none`/`one`/`multiple`
bucket for assigned global IPv4 addresses not covered by the current TCP/443
bind scope. A result of `other_address_only` or an unclaimed-address bucket is
only a lead for a separate address-specific design and rollback review. It
never authorizes APPLY, changes the conservative existing-port rejection, or
returns an address, listener owner or process name.
