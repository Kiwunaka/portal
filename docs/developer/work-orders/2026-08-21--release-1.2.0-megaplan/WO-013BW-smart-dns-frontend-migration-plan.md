# WO-013BW — Smart DNS frontend migration and all-node PLAN

## Outcome

Close the missing shared-443 frontend migration source and remote-PLAN gap
without selecting a production target or changing any server.

Post-candidate platform source `99d0715e8792280a7eb34650e6aa37bc8a44638c`
adds `remote_migrate_owned_smart_dns_frontend.py`. Its default operation is a
read-only PLAN. Install and rollback are separate guarded operations; neither
was executed in this work order.

## Guarded operation

The migration keeps the existing HAProxy default route and transport routes,
then adds only canonical exact and child-SNI Smart DNS rules backed by the
loopback PROXY-v2 listener. The operation is fail-closed on:

- strict known-host verification with TOFU disabled;
- an explicit root effective UID;
- exact current/candidate config and systemd-unit digests;
- exact Smart DNS immutable-release, node and client-disabled confirmations;
- remote `haproxy -c` validation without returning raw config;
- a root-owned mode-`0700`, non-symlink receipt with exact backup digests;
- compare-and-swap checks before apply and before automatic rollback;
- an explicit applied receipt and exact live candidate before manual rollback;
- active frontend/backend state, loopback-only backend listener and post-reload
  local DoH response.

The updated HAProxy unit validates before sending `USR2`, retains master-worker
mode and adds `KillMode=mixed`. The exact previous unit is retained as the
rollback fixture rather than being reconstructed from assumptions.

## Correctness review

The first independent review found two non-security, release-blocking wiring
errors before any live use: install supplied the DoH hostname to the receipt
builder instead of APPLY, and explicit rollback passed through the remote
unfronted-base transformer. A second focused review caught three remaining
recovery gaps: local install fixtures were still loaded before rollback, a
failed automatic rollback did not return the recovery receipt ID, and explicit
rollback did not compare the live Smart DNS release with the receipt. Its
recheck found one final observability gap: stderr returned the receipt but not
the automatic rollback result when `--json-out` was omitted. All six findings
are corrected. Focused orchestration tests now exercise online APPLY wiring,
error-path receipt reporting and an already-fronted rollback that does not read
the current checkout's install fixtures or policy. APPLY rechecks `prepared`;
explicit rollback rechecks `applied` plus the backend release; automatic
rollback rejects any live config or unit whose digest is neither the receipt
base nor its candidate.

## Verification

```text
python -m ruff check scripts/remote_migrate_owned_smart_dns_frontend.py tests/test_remote_migrate_owned_smart_dns_frontend.py
# PASS
python -m py_compile scripts/remote_migrate_owned_smart_dns_frontend.py
# PASS
python -m pytest -q tests/test_remote_migrate_owned_smart_dns_frontend.py tests/test_remote_apply_transport_front.py tests/test_check_script_manifest.py
# 28 passed
git diff --check
# PASS
```

The prior complete security review reported zero security findings. Its
correctness blockers and the later focused recovery findings were converted
into the root, receipt, release, CAS and orchestration tests above. That earlier
report does not by itself prove the corrected bytes; the corrected final diff
received a separate focused source recheck before promotion.

## Seven-node read-only PLAN

The corrected script ran without `--apply` on all seven active owned nodes.
Every process exited zero, retained a sanitized report and returned
`mutation_performed=false`.

| Node class | Count | Result |
|---|---:|---|
| No owned HAProxy frontend/config | `5` | Not an applicable migration target |
| Active valid owned frontend with valid candidate render | `2` | Frontend source-ready; Smart DNS backend absent |

The second class is `ru` and `ru_spb`. On both, HAProxy is active, TCP/443 is
present and the candidate validates, but Smart DNS is inactive, not configured
for fronted mode and has no loopback backend listener. Install therefore remains
fail-closed. Neither node is selected by this PLAN. Brain is not a target, and
`ru_spb` must not be selected merely because it shares the same current shape.

## Release interpretation

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3` with stronger status
`POST_CANDIDATE_FRONTEND_MIGRATION_SOURCE_AND_ALL_NODE_PLAN_PROVED_BACKEND_MISSING`.
This closes the separate frontend PLAN/APPLY/ROLLBACK source gap from WO-013BV,
but it does not prove a fronted Smart DNS install, live DNS/SNI, application
access, leak/privacy, rollback, physical-device or origin behavior.

Candidate.6 remains byte-identical and unchanged. This source is post-candidate
and requires a successor candidate if included in 1.2.0. Gate F remains
`4 PASS / 15 non-PASS / 0 FAIL` and is not regenerated.

## Required next evidence

1. extend the guarded Smart DNS server installer with the already-reviewed
   loopback/PROXY-v2 fronted mode and root-only runtime material;
2. select one delivery frontend explicitly; keep Brain and SPB unselected by
   default;
3. rerun exact server and frontend PLANs, then separately authorize their
   receipt-bound APPLY order and immediate rollback drill;
4. prove local backend health, public DoH and SNI attribution, then real
   ChatGPT/Gemini/Xbox access rather than DNS-only success;
5. run leak/privacy/lifecycle plus physical Android, Windows and distinct
   current/Brain/RU-origin evidence;
6. assemble and sign a successor candidate, then regenerate Gate F.

The local Raspberry Pi 4 may provide a terminal-only ARM64/RU-origin probe once
its trusted SSH profile is supplied. It is a separate origin and portability
target; it does not replace Android or Windows client proof.

## Evidence boundary

Normalized evidence is under
`evidence/013BW-smart-dns-frontend-migration-plan/` with SHA-256
`94f5475eba155283222947a796bd17debee93896ea2f679b0aa2234da726550a`.
It contains node codes,
booleans, counts and cryptographic digests only. Raw addresses, hostnames,
known-host entries, credentials, keys, runtime configuration and provider
payloads are not retained. The complete per-node PLAN reports remain
machine-local operator artifacts outside the repository.
