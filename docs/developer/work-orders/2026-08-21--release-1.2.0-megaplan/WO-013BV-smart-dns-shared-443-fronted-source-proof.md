# WO-013BV — Smart DNS shared-443 fronted source proof

## Outcome

Remove the source-level requirement to buy or free another public IPv4 without
pretending that an existing frontend has already been migrated.

Platform source `06e4a4abfb2b105eaaff4f819203f1b43e74788d` adds a second,
default-off Smart DNS listener mode. The original guarded installer remains
limited to a dedicated public TCP/443 listener. The new mode binds only to an
explicit loopback unprivileged port and requires HAProxy PROXY protocol v2
before any TLS ClientHello is parsed.

The server accepts only the PROXY command with TCP/IPv4 or TCP/IPv6 address
blocks of the exact base length. Missing headers, LOCAL commands, unsupported
families, malformed lengths and TLVs fail closed. The restored source address
is exposed through `net.Conn.RemoteAddr`, so both the connection limiter and
the DoH request limiter continue to operate per original client instead of
collapsing every user into the loopback frontend address.

The transport-front renderer now supports validated exact SNI names, safe
exact-or-child suffix matches and an explicit `send_proxy_v2` backend flag.
Names, suffixes, route identifiers, backend addresses and ports are validated
before rendering. The existing default routes remain unchanged.

## Why this is not a deployment

This closes only the server/frontend source-contract gap discovered after the
strict all-node topology PLAN:

- no runtime frontend was selected;
- Brain is explicitly not an automatic target;
- no HAProxy file, service, firewall, DNS record or certificate changed;
- the current Smart DNS installer rejects fronted runtime material and still
  supports only the dedicated-address mode;
- no rollback-capable frontend migration tool or remote PLAN exists yet;
- no DNS answer, application SNI relay, ChatGPT/Gemini/Xbox access, leak,
  lifecycle or origin check ran.

The no-purchase path is therefore technically viable but not operationally
ready. A delivery-node frontend is preferred over the control-plane host unless
a later bounded topology review proves otherwise. Any chosen frontend must keep
its current default backend and all POKROV transport routes byte-for-byte
recoverable under a receipt-bound rollback.

## Immutable local artifact

Two clean builds from exact platform source produced byte-identical inactive
Linux/amd64 bundles:

| Field | Result |
|---|---:|
| Bundle members | `11` |
| Bundle size | `2916119` bytes |
| Bundle SHA-256 | `2f713b638bbbd70a3ea1a7c40bee3c25011668a04ea19c7404b6b30e86e5a5eb` |
| Embedded ELF SHA-256 | `05a4b6635be25c471b16ae1782d6d393d4b14ea49f3ba9b0f3706e251b38bb5e` |
| Independent repeat | `PASS_BYTE_IDENTICAL` |
| Canonical policy SHA-256 | `b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa` |
| Runtime material included | `false` |
| Deployment performed | `false` |

The bundle contains both the unchanged dedicated config template and the new
fronted template. The bundle contract labels the fronted mode source-only and
`deploy_supported_by_current_installer=false`.

## Verification

```text
go test ./...
# PASS
go vet ./...
# PASS
python -B -m pytest -p no:cacheprovider tests/test_build_owned_smart_dns_server_bundle.py tests/test_remote_install_owned_smart_dns_lab.py tests/test_remote_apply_transport_front.py tests/test_check_smart_dns_policy_parity.py -q
# 30 passed
python -B -m pytest -p no:cacheprovider tests/test_check_script_manifest.py -q
# 4 passed
python -m ruff check <focused Smart-DNS/transport-front files>
# PASS
python -m py_compile <changed Python scripts>
# PASS
scripts/build_owned_smart_dns_server_bundle.py build <external-a>
scripts/build_owned_smart_dns_server_bundle.py build <external-b>
# PASS_LOCAL_IMMUTABLE_BUNDLE twice; byte-identical
```

## Release interpretation

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3` with status
`POST_CANDIDATE_FRONTED_SOURCE_AND_IMMUTABLE_BUNDLE_PROVED_NO_MIGRATION_PLAN`.
This is stronger than the prior “no safe zero-purchase target” source state,
but it does not advance the row to live proof.

Candidate.6 remains byte-identical and unchanged. The new platform source and
bundle are post-candidate and require a successor candidate before they can be
used as exact-candidate release evidence. Gate F remains `4 PASS / 15 non-PASS /
0 FAIL` and is not regenerated.

## Required next evidence

1. implement a separate guarded frontend PLAN/APPLY/ROLLBACK operation that
   inventories the exact current HAProxy config and backend health without
   exposing endpoints or runtime material;
2. choose one owned delivery frontend under an explicit risk/rollback decision,
   keeping Brain unselected by default;
3. generate canonical exact/child SNI routes from the policy and prove the
   rendered HAProxy config with `haproxy -c` plus a local PROXY-v2/TLS fixture;
4. stage receipt-bound root-only certificate/config material and rerun a fresh
   no-mutation PLAN;
5. only after separate owner authorization, APPLY the exact bundle/migration,
   then retain rollback, DoH/SNI attribution, real service access, leak,
   lifecycle, physical-device and current/Brain/RU-origin evidence;
6. assemble and sign a successor candidate if this lane is included in 1.2.0.

## Evidence boundary

Normalized evidence is under
`evidence/013BV-smart-dns-shared-443-fronted-source-proof/` with SHA-256
`ad8f4571069f0696e5e312d3cd2b4fcd0553f4fd9d3f2e47b7d67d6154ce0019`.
It retains no address, hostname, device identifier, credential, key,
certificate, runtime configuration or provider payload. External bundle paths
are machine-local and are not release assets.
