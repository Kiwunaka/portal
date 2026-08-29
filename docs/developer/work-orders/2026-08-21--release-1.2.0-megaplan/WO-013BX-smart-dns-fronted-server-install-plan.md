# WO-013BX — Smart DNS fronted server install source and RU PLAN

## Outcome

Close the server-side half of the shared-TCP/443 Smart DNS source gap without
creating runtime secrets, selecting a production target or changing a server.

Post-candidate platform source
`650dc3fab8053736cfb976d4a34ea1f2f0b40349` extends the guarded Smart DNS
installer with a closed `fronted` mode. The existing `dedicated` mode remains
the default-compatible public-TCP/443 path. `fronted` binds exactly to
`127.0.0.1:18443`, requires PROXY protocol v2 and does not add or remove UFW
rules. PLAN remains the default operation.

## Guarded operation

Fronted APPLY requires the separate exact confirmation
`FRONTED_LOOPBACK_PROXY_V2`. It verifies the immutable bundle and root-owned
runtime staging, retains a bundle/node/mode-bound root-only receipt, installs an
immutable release, and proves the exact listener with a valid PROXY-v2 header,
TLS SNI and a bounded DoH request before success.

Rollback is mode-aware. Explicit rollback requires an `applied` receipt and the
exact current release. Armed automatic rollback accepts only `prepared` or
`applied`. Fronted receipts record the firewall as `not_managed`, and both
install and rollback omit UFW mutation.

Server installation and the WO-013BW public HAProxy migration remain separate
operations with separate confirmations, receipts and rollback. Authorization
for one does not authorize the other.

## Correctness and security review

Focused execution uncovered and fixed a dormant generated-runtime validator
bug: an f-string had interpreted a regex quantifier before the validator was
sent to the node. The final tests execute both dedicated and fronted validators
rather than checking them as inert strings.

The exact committed diff received a completed security diff scan covering ten
surfaces: privileged inputs and SSH, listener and firewall ownership, runtime
material, PROXY-v2 parsing, receipt/rollback state, reporting, tests,
documentation and the shared systemd capability. It reported zero findings.
Two hypotheses were rejected as non-vulnerabilities: PROXY-v2 spoofing requires
an already host-local process, and the shared low-port capability is optional
post-compromise hardening rather than a new pre-compromise path.

The security report is machine-local, scan
`c4b8e173-6dda-4d51-913e-5afcdebd50e2`, SHA-256
`3b79fab2161c488e40ca5706e208aa262ee9a0c665e99e787b80ed4281013bd0`.
TAC advisory access was unavailable, so the protected report UI is not claimed.

## Verification

```text
python -m py_compile scripts/remote_install_owned_smart_dns_lab.py
# PASS
python -m ruff check scripts/remote_install_owned_smart_dns_lab.py tests/test_remote_install_owned_smart_dns_lab.py
# PASS
python -m pytest -q tests/test_remote_install_owned_smart_dns_lab.py tests/test_build_owned_smart_dns_server_bundle.py tests/test_remote_migrate_owned_smart_dns_frontend.py tests/test_check_script_manifest.py tests/test_check_smart_dns_policy_parity.py
# 49 passed
go test ./...
# PASS
go vet ./...
# PASS
python scripts/check_smart_dns_policy_parity.py --platform-root . --client-root <active-client-worktree>
# PASS; b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa
git diff --check
# PASS
```

Two exact-source builds are byte-identical: `2916305` bytes, SHA-256
`cda97da16a892c1a8563bd20434cd749a2174c192ba722147091a3e1c14a0225`.
The artifact is Linux/amd64, contains no runtime material and is not externally
signed.

## RU read-only server PLAN

The exact immutable artifact ran without `--apply` against `ru` and `ru_spb`.
Both processes exited zero with `mutation_performed=false`.

| Check | `ru` | `ru_spb` |
|---|---|---|
| Root and required tools | PASS | PASS |
| Existing public TCP/443 | Busy | Busy |
| Exact loopback TCP/18443 | Free | Free |
| Current Smart DNS service | Inactive/absent | Inactive/absent |
| Runtime material | Missing | Missing |
| Occupied install targets | `0` | `0` |

Both nodes are technically suitable for the server-first fronted install, but
this is not a target decision or deploy authorization. `ru` is the proposed
first canary for a later separately authorized operation. `ru_spb` remains
unselected by default, and Brain remains excluded.

## Raspberry Pi 4 boundary

The owner's local Pi 4 is added as a terminal-only ARM64/RU-origin probe for
DNS/DoH, routing, service/API reachability and leak observation once a trusted
SSH profile is supplied. It cannot run this exact Linux/amd64 server bundle.
An ARM64 build is a separate portability task, and Pi evidence cannot replace
Android or Windows client proof.

## Release interpretation

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3` with stronger status
`POST_CANDIDATE_FRONTED_SERVER_INSTALL_SOURCE_AND_RU_PLAN_READY_RUNTIME_MATERIAL_MISSING`.
This closes the guarded fronted-server source and RU PLAN gaps from WO-013BW.
It does not create runtime material or prove APPLY, frontend migration, live
DNS/SNI, ChatGPT/Gemini/Xbox access, attribution, leak/privacy, rollback,
physical-device, Windows or origin behavior.

Candidate.6 remains byte-identical and unchanged. This source is post-candidate
and requires a successor candidate if included in 1.2.0. Gate F remains
`4 PASS / 15 non-PASS / 0 FAIL` and is not regenerated.

## Required next evidence

1. supply the trusted Pi SSH target and run a secret-free terminal RU-origin
   probe; add Linux/ARM64 build support only if Pi server execution is desired;
2. create the owner-only Smart DNS runtime material without adding it to the
   repository or evidence;
3. explicitly authorize the `ru` server APPLY and immediate receipt-bound
   rollback drill, keeping Brain and SPB unselected;
4. only after local backend health, separately authorize the WO-013BW frontend
   migration and its rollback;
5. prove public DoH/SNI attribution and actual ChatGPT/Gemini/Xbox access, then
   leak/privacy/lifecycle, physical Android, Windows and distinct-origin lanes;
6. assemble and sign a successor candidate and regenerate Gate F.

The component owner was updated in `infra/owned-smart-dns/README.md`. Canonical
operations documentation was not edited because the owner's root worktree has
concurrent changes in both relevant files; that owner-document sync remains a
tracked handoff rather than overwriting unrelated work.

## Evidence boundary

Normalized evidence is under
`evidence/013BX-smart-dns-fronted-server-install-plan/` with SHA-256
`75574878cac773e3bee97c185da340aaa1dcb3e3eae2c27eb513ce2127f7f929`.
It contains node codes, booleans, counts and cryptographic digests only. Raw
addresses, hostnames, known-host entries, credentials, keys, runtime
configuration and provider payloads are not retained. Complete PLAN reports
and the security report remain machine-local operator artifacts.
