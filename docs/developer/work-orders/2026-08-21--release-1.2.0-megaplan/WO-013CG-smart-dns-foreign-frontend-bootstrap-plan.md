# WO-013CG — Smart DNS foreign transport-front bootstrap PLAN

## Outcome

Close WO-013CE's missing source/PLAN boundary for the preferred no-purchase
Smart DNS topology: one colocated foreign owned HAProxy TCP/443 frontend, the
existing Xray/Reality transport on loopback and a later loopback Smart DNS
backend.

Post-candidate platform source `c2ffc48285088129be507ac5bc3d9b8555225326`
adds a guarded bootstrap for the first frontend. A fresh read-only PLAN proves
that `it` has the exact direct-Xray shape required by that operation. No APPLY,
service restart, package install, x-ui write, runtime material, DNS publication
or production mutation occurred.

`it` is the bounded PLAN canary, not a deployed Smart DNS target.

## Foreign inventory

Read-only frontend migration inventory covered `de`, `it`, `nl`, `pl` and `us`.
Every node has public TCP/443 occupied, and none has the owned HAProxy frontend,
loopback TCP/18443 Smart DNS backend or applicable existing-frontend migration
shape. The prior shared-frontend migration operation therefore cannot be used
as a bootstrap.

`it` is the lowest-complexity canary shape observed for the missing source:

- `x-ui.service` is active and enabled;
- exactly one enabled x-ui inbound owns public TCP/443;
- the exact inbound is VLESS with Reality security and wildcard listen;
- Xray owns the live listener;
- loopback TCP/10443 and TCP/18443 are free;
- HAProxy is absent, while apt exposes an install candidate;
- the custom frontend config and service unit are absent.

The sanitized PLAN report has SHA-256
`72d768dd20633b8caab80173d8b985359b012c90b0f9aa72b98e9b319b63fb83`
and returns `bootstrap_applicable=true`, `mutation_performed=false`. It returns
no address, host, raw x-ui configuration, credential, key or runtime material.

## Source contract

`infra/portal-transport-front.legacy-one-backend.cfg` preserves current
transport behavior while changing listener ownership:

```text
client -> HAProxy :443 -> Xray/Reality 127.0.0.1:10443
```

The default backend receives all unmatched SNI, so the bootstrap does not
depend on a new public hostname and does not add Smart DNS routes. The later
guarded Smart DNS frontend migration can add exact/child SNI routes plus a
PROXY-v2 loopback backend without changing the legacy default route.

`scripts/remote_bootstrap_owned_transport_front.py` supplies separate
PLAN/APPLY/ROLLBACK modes:

1. PLAN opens the x-ui SQLite database read-only and returns bounded booleans,
   classifications and digests only.
2. APPLY requires exact node, inbound, config, unit and invariant digests plus
   `OWNED_TRANSPORT_FRONT_BOOTSTRAP_AUTHORIZED`.
3. A root-only receipt is created before mutation.
4. The exact x-ui row moves from wildcard `443` to `127.0.0.1:10443` through a
   one-row SQLite compare-and-swap bound to an invariant digest of the inbound
   protocol/security payload.
5. HAProxy package ownership, config validation, listener ownership and
   systemd state are verified before success.
6. Any APPLY guard failure records `automatic_rollback_pass` or
   `automatic_rollback_fail`; a failed postflight also invokes the explicit
   receipt-bound rollback.
7. Explicit rollback performs its CAS while the frontend is still serving. If
   the direct cutover then fails, it restores the fronted state. It removes the
   HAProxy package only when the receipt proves this operation installed it.

This is official Xray/Reality transport placement. It changes no cryptography
and is unrelated to a custom POKROV AWG cipher.

## Verification

```text
python -m pytest <transport-front and Smart-DNS focused set> -q
# 68 passed

python -m ruff check scripts/remote_bootstrap_owned_transport_front.py \
  tests/test_remote_bootstrap_owned_transport_front.py
# PASS

python -m py_compile scripts/remote_bootstrap_owned_transport_front.py
python scripts/check_script_manifest.py
git diff --check
# PASS
```

The focused set includes the new bootstrap, existing frontend renderer/smoke,
Smart DNS frontend migration, fronted installer, bundle/parity and manifest
contracts.

## Release interpretation

`FRKN_SMART_DNS/SMARTDNS-01` remains `I3` with status
`POST_CANDIDATE_FOREIGN_FRONTEND_BOOTSTRAP_SOURCE_AND_IT_PLAN_READY_APPLY_NOT_AUTHORIZED`.
This closes source and no-mutation PLAN uncertainty only.

Signed `pokrov-1.2.0-candidate.8` is unchanged. Gate F remains `BLOCKED` at
`5 PASS / 14 non-PASS / 0 FAIL`. No candidate was rebuilt, no completion row
advanced to `I4`, and no tag, public release, store object, stable pointer or
Gate G authorization was created.

## Required next evidence

1. decide whether the bounded `it` maintenance cutover is authorized;
2. if authorized, run exact confirmed frontend APPLY and immediate transport
   reachability plus receipt/rollback rehearsal before adding Smart DNS;
3. create root-only Smart DNS runtime material and run exact server/frontend
   PLANs against the now-fronted state;
4. authorize server and Smart DNS route APPLY separately;
5. prove real ChatGPT/Gemini/Xbox sessions, DNS/SNI attribution, privacy/leak,
   lifecycle and rollback from current, Brain and RU origins;
6. bind any shipped change to a successor candidate rather than relabelling
   immutable candidate.8.

Evidence is retained under
`evidence/013CG-smart-dns-foreign-frontend-bootstrap/` and contains only safe
digests, node codes, booleans and decision labels.
