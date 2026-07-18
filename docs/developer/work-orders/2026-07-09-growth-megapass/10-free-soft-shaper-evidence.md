# Free Soft Inbound Shaper Evidence

Status: `LOCAL_CODE_PASS`; node execution remains `MANUAL_OWNER_TEST`.

Backend companion status: local contract and migration tests pass; no live
panel, node, or throughput claim is made by this evidence.

## Scope

This slice adds a local-only nftables command planner for the dedicated
free-soft TCP/UDP inbound. It does not create the inbound, assign credentials,
change backend entitlement state, connect over SSH, or modify a live node.

The backend companion uses explicit `free_standard` and `free_soft` node roles
and persists `standard`, `soft_transition_pending`, `soft_active`,
`reset_pending`, and `error`. Its durable worker confirms the target before
disabling the source; reset also clears standard-profile traffic before it
disables soft. Additive SQLite and PostgreSQL migrations preserve legacy job
payloads while backfilling roles and queue indexes.

Consumer node selection is role-bound end to end: API locations/subscriptions,
legacy panel helpers, and Telegram/admin resync use the persisted confirmed
role. Transition/error states refuse legacy resync. Bot and worker expiry paths
queue durable re-entry instead of issuing independent panel mutations.

Late payment is rechecked after each destructive panel action and again during
database finalization. A superseded transition disables its free target and
restores a paid source, or the last confirmed standard source if no paid source
was part of that job. Any failed compensation is retained as `manual_review`.
A confirmed monthly reset starts a new full 30-day cycle at confirmation time.

Owned runtime objects are stable and isolated:

- family/table: `inet pokrov_free_soft`
- chains: `pkr_soft_input`, `pkr_soft_output`
- bounded dynamic sets: one IPv4 and one IPv6 set per direction
- rules: four total, covering IPv4/IPv6 and input/output
- default dedicated port: `8443`
- default target: `2mbit`, emitted as `250 kbytes/second`
- default burst: `64 kbytes`
- default maximum entries per set: `65535`, with `10m` timeout

`setup` validates the complete batch with `nft --check -f -` before applying
the same batch. The batch destroys only its owned table and recreates it in one
nft transaction, so rerunning it converges to the same ruleset without duplicate
rules. `rollback` idempotently destroys only that table. `audit` only lists that
table and contains no mutating command.

## Safety Contract

- JSON dry-run is the default for every action.
- Local execution requires explicit `--apply` and is refused off Linux.
- The executor uses argv plus stdin directly; there is no shell and no SSH.
- Interface, port, rate, timeout, burst, and set size are bounded and validated.
- Reports omit executor stdout/stderr, environment, hostname, username, and
  exception text.
- No command flushes the full nftables ruleset or changes an existing qdisc.

## Enforcement Truth

This is packet policing, not queue-based traffic shaping. Packets over the
token-bucket rate are dropped. The configured target is symmetric: up to the
configured rate in each direction, not one combined full-duplex bucket.

The key is the client IP observed on the encrypted transport connection:

- multiple accounts behind one NAT address share the same cap;
- one account using multiple public IPs receives one cap per observed IP;
- this is not per-account or per-device proof;
- the dedicated inbound must contain only free-soft credentials, otherwise the
  port rule will also police any premium credential placed there.

## Local Evidence

RED was captured before implementation with 23 expected failures because the
script did not exist. A second RED was captured for direct dataclass validation,
and a third for bounded dynamic-set syntax.

Current focused command:

```powershell
python -m pytest tests/test_free_soft_inbound_shaper.py -q
```

Current result: `24 passed`.

Backend-focused regression after role/race/resync fixes:

```powershell
python -m pytest tests/test_free_soft_profile_contract.py tests/test_free_soft_profile_migrations.py tests/test_node_provisioning_service.py tests/test_panel_client_free_profiles.py tests/test_free_soft_inbound_shaper.py tests/test_free_cycle_service.py tests/test_key_pressure_scoring.py tests/test_admin_ops_api.py tests/test_plan_policies.py tests/test_bot_paywall.py tests/test_api_auth_and_tickets.py -q
```

Result: `233 passed`, `12 subtests passed`, `0 failed`. After independent
review fixes, the final combined free-profile/API/bot focused regression passed
`176` tests with `0` failures and no warnings.

The repository release pytest matrix from `scripts/release_gate_check.py` ran in
the pinned integration virtual environment and passed `454` tests plus `23`
subtests with `0` failures in `624.83s`. Its `16` warnings are existing
`datetime.utcnow()` and httpx raw-content deprecations in
`tests/test_api_payments_callbacks.py`; no warning originated in this slice.

Static evidence on the same code candidate:

- Python byte-compilation: `29` changed/untracked Python files, `PASS`;
- JSON parse: `shared/access-matrix.json` and
  `infra/free-soft-inbound.json`, `PASS`;
- `python scripts/check-links.py`: `PASS`;
- `git diff --check`: `PASS`.

The local WSL distribution does not contain `nft`, and Docker Desktop is not
running, so no Linux nft parser or kernel/netlink proof is claimed here.

## Manual Node Gate

Use the exact candidate on an isolated canary only after the dedicated inbound
exists and its interface/port are confirmed.

1. Run `python scripts/free_soft_inbound_shaper.py setup --iface <iface> --port <port>` and review the dry-run JSON.
2. Run `sudo python scripts/free_soft_inbound_shaper.py audit --iface <iface> --port <port> --apply`; retain the redacted JSON result.
3. Confirm the installed nft version supports `destroy table`, dynamic sets,
   per-element limits, `inet` IPv4/IPv6 matching, and `th` port expressions.
4. Run setup with `--apply`, then list only `inet pokrov_free_soft` and confirm
   four rules, four bounded sets, the selected interface/port, and counters.
5. Repeat setup and confirm there are still exactly four rules and no duplicate
   chains or sets.
6. Exercise TCP and UDP over IPv4 and IPv6 in both directions. Retain sustained
   throughput, loss/retransmit, reconnect, DNS, and leak evidence.
7. Test two clients behind one NAT and two clients on distinct public IPs to
   confirm the documented sharing model.
8. Confirm premium and pre-quota free profiles never use the soft inbound and
   remain unaffected.
9. Dry-run rollback, apply rollback, confirm only `pokrov_free_soft` is absent,
   and verify ordinary POKROV connectivity still works.

Production readiness remains blocked until these exact-node canary checks and
the backend credential-routing checks are retained together.

## Migration Rollback

The migration is additive. It does not delete users, credentials, jobs, or
legacy payloads. Before replacing an invalid pre-existing node role, it stores
that value in `nodes.access_role_legacy`.

Rollback requires the previous application revision and an operator window:

1. Stop the node-provisioning worker and retain queued/running/manual-review job evidence.
2. Reconcile any already-mutated panel profiles from the recorded target/source job payload before reverting application code.
3. For rows with a retained value, restore it with `UPDATE nodes SET access_role = access_role_legacy WHERE access_role_legacy IS NOT NULL`.
4. On PostgreSQL, the previous revision may also require `ALTER TABLE nodes ALTER COLUMN access_role DROP NOT NULL` and `DROP DEFAULT`; SQLite can leave the additive columns in place.
5. Keep all additive columns and indexes unless a separately reviewed down migration proves they are unused. Do not erase job or audit rows.
6. Start the previous revision only after a dry-run subscription/panel comparison shows no consumer route points at `operator_lab` or the wrong free inbound.

No database or panel rollback was executed in this local evidence run.
