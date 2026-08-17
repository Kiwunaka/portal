# Emergency Source Audit

Audit timestamp: `2026-08-15`
Audit target: current-origin, read-only
Secrets retained: none

## Authority And Attribution

- Approved data source: [`igareck/vpn-configs-for-russia`](https://github.com/igareck/vpn-configs-for-russia)
- Audited `main`: `fc00600ec218264bc6904cc30b8a4a2dc5a4a704`
- Repository license: `GPL-3.0`
- Owner agreement to use the emergency data input: `OPERATOR_ATTESTED`
- POKROV does not execute upstream code and does not ship the upstream feed
  directly to a client. It parses, verifies, signs and promotes a bounded
  server-owned projection.

The upstream README says its subscriptions are public, automatically refreshed
and tested from Russia. That is useful source context, not POKROV proof of a
working tunnel, a foreign exit or real restricted-network availability.

## Exact Inputs

| Input | Bytes | SHA-256 | Candidate lines |
| --- | ---: | --- | ---: |
| `Vless-Reality-White-Lists-Rus-Mobile.txt` | 39,735 | `3546f5fd2801d5c00f6447bd38aa52be36db376a6da373f8f542d43cea391b1f` | 135 |
| `WHITE-SNI-RU-all.txt` | 3,336 | `515e272be33940ebcf50688480aacdf5a406d3c55f16ae50842e67940aad6ebd` | 11 |

Seven documented mirrors returned byte-identical mobile-feed content during the
audit: GitHub, GitLab, Codeberg, Gitea, SourceHut, Bitbucket and GitHack. Mirror
agreement reduces bootstrap fragility; it is not an authenticity decision.
Only a pinned digest followed by POKROV parsing, verification and signing can
enter staging.

## Current Shape

The strict `pokrov-emergency-vless-reality-v1` parser accepts only:

- VLESS with a canonical non-zero UUID;
- REALITY with required SNI, 32-byte base64url public key and even-length short
  ID;
- TCP/raw or gRPC (`mode=gun` is normalized as legacy gRPC metadata);
- a deterministic uTLS fingerprint allowlist;
- known endpoint ports `443`, `4443`, `6443`, `7443`, `8443`;
- no insecure TLS, arbitrary route/DNS/inbound fields, XHTTP `extra`, unknown
  fields or duplicate query keys.

Live safe-aggregate result for the exact inputs:

| Input | Syntactically accepted | TCP | gRPC |
| --- | ---: | ---: | ---: |
| mobile | 35 | 12 | 23 |
| SNI | 3 | 0 | 3 |

The parser result is not the active catalog. Source names, fragments, ordering
and geography are ignored. A separate fresh trusted verification must prove a
non-RU exit before selection.

The later release preflight intentionally used the production ingestion quorum,
not the wider discovery list above. All three controlled mirrors agreed for
both feeds; 157 candidate lines produced 23 normalized unique records and one
safe aggregate source digest
`54f71c23fa8a9e0afd47b0e010814fb19a4278748a5deaa507f59dfb658d2dea`.
This supersedes the six-row advisory discovery count for worker capacity only;
it still does not prove handshake, exit country or restricted-network behavior.

## Foreign-Candidate Reality Check

Current-origin DNS plus third-party geolocation was used only as an advisory
discovery signal. It found six syntactically accepted non-RU candidates across
the two inputs: three TCP/raw and three gRPC. One additional NL gRPC row uses an
unsupported `qq` fingerprint and remains rejected. Actual country, credential
validity, deterministic payload transfer and restricted-network behavior are
still unproved.

Therefore the product contract is **4–20 active reserves**, not a promise that
the current source always contains 20. Promotion fails closed below four fresh
verified candidates. No result in this audit may receive the label
`Проверено при реальном БС`.

The upper bound was raised from 12 to 20 after exact Huawei/Beeline evidence
showed that server-reachable candidates can diverge sharply by carrier and
region. The client still tests every retained path locally and never treats the
larger signed pool as proof that a route works in the current device network.

## Redacted Regression Fixture

`tests/fixtures/emergency_catalog/source-v1.txt` is synthetic-only. It covers
valid TCP/gRPC, normalization, duplicate identity, insecure TLS, unsupported
transport/scheme/fingerprint and malformed identity without retaining any
upstream URI or credential material.

Exact focused proof:

```text
python -B -m pytest -p no:cacheprovider tests/test_emergency_catalog_source.py -q
12 passed
```

Limitations carried into the next work order:

- geolocation is advisory until the controlled verifier records a trusted exit;
- parser success does not prove handshake, payload, БС, latency or capacity;
- source freshness and mirror agreement do not replace endpoint freshness;
- probe DNS must reject private/rebound answers before any connection attempt.
