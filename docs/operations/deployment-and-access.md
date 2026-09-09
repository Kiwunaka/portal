# Deployment And Access

Last updated: 2026-08-31

## Document Status

This file is living source of truth for deployment entrypoints, runtime access, and sensitive material locations.

## Client Lane Distinction

Wave 0 now separates active client truth from retained client evidence:

- new client development truth belongs to `POKROV-app/main`, with live local checkout path `C:/Users/kiwun/Documents/ai/POKROV-app`
- retired bootstrap provenance is summarized in `docs/archive/client-lanes/app-next-bootstrap-summary.md`
- retained bridge bundle lineage is archived under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`
- commands in this guide now describe the active `POKROV-app` lane, with archive notes called out explicitly when retained bridge evidence matters

## Release Metadata Home

Release metadata now lives under the canonical client repo.

- active metadata root: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/`
- each candidate keeps `release-handoff.json`, checksums, manifests, and retained binaries in its versioned folder under that root
- `C:/Users/kiwun/Documents/ai/POKROV-app/config/release-handoff.seed.json` points operators to the latest repo-backed release truth
- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/` is retained rollback/archive evidence only
- a bridge-era `release-links.env` is compatibility evidence, not the active metadata authority
- keep the stable root-orchestrator pointer at `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json` only when it is intentionally synchronized from the active versioned metadata

## Control Plane

Canonical control-plane host:

- `brain`: `82.21.114.104`

Key services expected there:

- `portal-api`
- `portal-bot`
- `portal-helpbot`
- `portal-feedbackbot`
- `caddy`
- `x-ui`

RF auxiliary hosts:

- `mini`
  dedicated external RU probe origin, universal operator sandbox, and owner-approved emergency RU bridge endpoint for non-US delivery reachability
- `rf1`
  reserve RF ingress for operator and VIP/manual access

RF access rule:

- do not place control-plane services on `mini` or `rf1`
- do not add `rf1` to the normal runtime delivery pool in phase 1
- keep a hard kill switch for the `rf1` VIP/manual contour so it can be withdrawn without touching the standard consumer path
- `rf1` reserve work remains backlog-only
- owner-approved exception on `2026-06-01`: `mini` may run `ru_bridge_relay` on `tcp/443` through Xray Reality as the legacy primary emergency bridge to POKROV delivery nodes except US; additional RU bridge hosts may be added as separate `ru_bridge_relay.endpoints[]` ids without replacing `mini`. Do not add bridge hosts to the normal runtime delivery pool and do not move control-plane services onto them.
- historical owner-approved exception on `2026-04-24`: the former dedicated free node (`151.245.217.23`) may carry a Telegram-only MTProto proxy on `tcp/9443`; it is not a control-plane or subscription-delivery service, and its current runtime state is unattested while the host is inaccessible
- `mini` / `RFMINI` is the canonical RU-origin sandbox when SSH credentials are current; if access is blocked, label the release evidence as `RU-origin check: BLOCKED_BY_ACCESS`
- current `mini` SSH access, verified on `2026-06-01`: use `kiwunaka@176.123.166.119:22` with the retained local password bundle; `29374` opens TCP but resets before the SSH banner and should not be used as the primary SSH path
- RU probe readiness itself is a tracked operational dependency for release confidence and is scoped to `POKROV` public hosts, API health, and delivery-node reachability
- current topology decision as of `2026-07-05`: `mini` remains a bridge/sandbox, not a normal RU delivery node; the planned new RU server may become a full RU node plus a second bridge after provisioning, but no public RU-origin/readiness claim is allowed until that host has current probe evidence
- target bridge topology after the new RU host is live: each eligible foreign non-US node may have two bridge paths, the existing `mini` bridge and the new RU bridge; rollout must keep per-bridge health, downstream target reachability, and rollback controls separate

## Operator Shell Policy

Operator, release-health and support-bundle access is reviewed under
[`observability-access-review.md`](observability-access-review.md). That
playbook defines review cadence, independent ownership, fail-closed findings
and the evidence boundary; this deployment guide does not replace it.

- prefer `bash` when it is the simplest reliable operator path
- use `powershell` when quoting, Windows path handling, SSH invocation, or local tooling behavior is more reliable there
- pick the shell that reduces operator error for the exact command rather than forcing one shell everywhere

## SSH Host-Key Policy

Repo-owned Paramiko scripts must not silently trust unknown SSH host keys.

Runtime helpers:

- `scripts/ssh_host_keys.py`
- `portal_bot/ssh_host_keys.py`

Default behavior:

- load system known hosts
- load `POKROV_SSH_KNOWN_HOSTS` when set
- otherwise load `VPN NODE SSH KEYS/known_hosts`
- reject unknown host keys
- resolve DNS inventory hosts to their current IPv4 address before matching the pinned host key; DNS correctness remains a separate predeploy check
- accept the retained unencrypted PuTTY v2 RSA and Ed25519 private-key formats without falling back to password authentication
- when local routes differ by node, use `POKROV_SSH_BIND_SOURCE_<NODE_CODE>` for the exact node and keep `POKROV_SSH_BIND_SOURCE` as the optional global fallback

First-bootstrap exception:

- set `POKROV_SSH_TRUST_ON_FIRST_USE=1` only for a deliberate first contact or host-key rotation
- after the first successful connection, review and keep the saved key in the local known-hosts file
- turn `POKROV_SSH_TRUST_ON_FIRST_USE` back off before normal deploy, probe, sync, backup, or handoff commands

Do not paste host-key fingerprints, SSH passwords, private keys, or full known-hosts files into docs or reports. Record only redacted evidence that the target host key was reviewed.

## Sensitive Material Locations

These locations are intentionally preserved and must not be deleted during cleanup:

- `portal_bot/.env`
- `VPN NODE SSH KEYS/`
- `secrets for merchant/`
- `ops-local/`
- `external/client-fork/app/windows/sign.pfx` (retained rollback/archive signing material only)
- `external/client-fork/app/windows/sign.cer` (retained rollback/archive signing material only)

Rules:

- do not duplicate secret values into documentation
- do not print raw secrets into commit messages or reports
- document locations and usage only
- release gate and deploy handoffs may name secret locations, environment variable names, and redacted command shapes, but must not include raw token values, webhook payloads, subscription links, MTProto links, payment identifiers, Telegram IDs, or private keys
- if a command tail or remote log contains a bearer token, callback signature, provider payload, personal connection URL, or full user identifier, redact the value before moving it into `docs/`, work-order evidence, screenshots, or release-captain handoff

## Canonical Deploy Scripts

### Backend code deploy

- [remote_deploy_brain_portal_code.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_portal_code.py)
- [remote_deploy_brain_awg_route_fix.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_awg_route_fix.py)
- [remote_brain_runtime_source_probe.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_brain_runtime_source_probe.py)

Before restarting an apparently stale Brain runtime, compare the exact signed
platform commit with the live deploy payload in read-only mode:

```powershell
python scripts/remote_brain_runtime_source_probe.py --brain-ip <brain> --source-revision <full-40-character-platform-commit> --json-out <artifact>
```

The probe uses the same tracked payload selection as the backend deploy, reads
exact Git blobs rather than working-tree files, and only reads live files over
SFTP. It never uploads, restarts or changes runtime state and never retains
remote contents or credentials. The report distinguishes raw byte identity
from the sole accepted transport normalization, `CRLF_TO_LF_ONLY`; any other
difference, missing file or unreadable file fails closed. This establishes
Brain runtime source identity only. It does not prove current-origin,
RU-origin, authenticated client egress, a stable pointer or public promotion.

For the bounded owned-AWG activation repair, use the dedicated one-file entrypoint
instead of the bulk backend deployer:

```powershell
python scripts/remote_deploy_brain_awg_route_fix.py --json-out <plan-artifact>
```

Its default mode is read-only `PLAN`. It pins the current Brain baseline to
`e5ef03ac7ab013d8810cc9c6ea9ccc40cebd11db`, the reviewed AWG source to
`83502f1cb9a54ce7ae088a36ed2f9e696c90d841`, requires the full tracked runtime
to match `193/193`, and proves that the only semantic delta is
`portal_bot/api_client_routes.py`. It never reads deployment bytes from the
working tree. The exact 193-path live/candidate mapping is digest-pinned;
runtime entries added only by later aggregate work are excluded from this
frozen change window, while a path present in only one reviewed revision or a
mapping-target drift fails closed. An authorized apply additionally requires
`--apply --confirm AWG_ONE_FILE_83502F1_PORTAL_API`; it stages and backs up only
that file, restarts only `portal-api`, requires delayed health plus exact
candidate `193/193` readback, and automatically restores the baseline file and
rechecks the old `193/193` payload on failure. The confirmation argument is an
execution guard, not deploy authorization by itself.

Authorized runtime record, 2026-08-28: candidate.5 PLAN passed the frozen
baseline at `193/193`, then APPLY promoted only
`portal_bot/api_client_routes.py`, restarted only `portal-api`, passed delayed
health and read back the reviewed candidate payload at `193/193`. Rollback was
not required. The sanitized PLAN/APPLY report SHA-256 values are
`f9d04a3885504f7eaf0b855f66dffd326869bcaff3c6aebe41749192a4a35219` and
`5610826930cb5c84d243dfd019b750bff90d9c40b4f5222a213bd102bdb57038`.
This is exact Brain source and service-health evidence only. A later exact
Huawei bind attempt did not reach the remote helper because SSH failed at the
protocol-banner/timeout boundary; no device policy mutation or AWG Core start
occurred, so the candidate.5 device matrix remains `BLOCKED_BY_ACCESS`.

Typical use:

```powershell
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot,portal-worker
```

Repo-side deploy rule:

- the default restart set is `portal-api`, `portal-bot`, `portal-helpbot`, `portal-feedbackbot`, and `portal-worker`
- a normal git `push` runs repository guardrails only; production backend/static deploy still requires the manual release workflow in `full` mode or an explicit operator-run deploy command
- backend code deploy is staged and fail-closed: only tracked runtime files are selected, nested paths are preserved under `/root/portal_bot.deploy-staging/<release_id>/`, current live files are backed up under `/root/portal_bot.deploy-backups/<release_id>/`, and the script runs recursive Python bytecode compilation plus recursive JSON validation before promotion
- the tracked runtime payload includes production Python modules below `portal_bot/` except `portal_bot/tests/`, the pinned requirements file, the explicit node-probe helpers, all tracked JSON below `shared/`, and `copy/catalog.ru.json`; it does not copy `.env`, uploads, private support bundles, databases, tests, or untracked files
- promo media is durable runtime data under `PROMO_MEDIA_DIR` (default
  `/root/portal_bot/uploads/promos`), not a code-deploy payload. Staged backend
  promotion must leave that directory untouched. Server migration/backup must
  snapshot it together with the active `promo_slots_config_v1`; an asset is not
  removed while an active or rollback campaign references its content hash
- staged requirements are installed in a temporary staging venv first; the live venv is updated only after staged syntax/JSON/requirements preflight and the bounded `admin_v2`/observability import check pass
- if preflight or requirements installation fails, the script exits before live file promotion and before any `systemctl restart`
- each managed restart resets only the systemd failure/restart counter, then the deploy waits 12 seconds and requires every requested unit to remain `active` with `NRestarts=0` plus a successful public API health probe; command failure, crash-loop evidence, or failed health triggers file rollback and the same delayed verification on the previous file set
- after every successful deploy, only the five newest timestamped directories under `/root/portal_bot.deploy-backups/` are retained; `--backup-retain-count` may set a bounded value from 1 to 50, and pruning never selects nonconforming/manual evidence names
- `--restart` accepts only systemd-safe unit names; do not use shell fragments or chained commands in the unit list
- the deploy payload must include the full tracked JSON backend truth and contract tree under `/root/shared/`, including nested observability and support contracts rather than only the historical root JSON allowlist
- the deploy step should be treated as failed until delayed unit stability and public API health both pass
- support AI is a `portal-api` and `portal-helpbot` runtime feature and remains disabled by default. The exact route table is: `SUPPORT_AI_ENABLED=false` selects local fallback; `SUPPORT_AI_ENABLED=true` with `SUPPORT_AI_AGENT_ENABLED=false` selects the legacy one-call helper; both flags `true` select the code-owned harness. There is no shadow or double call. Immediate rollback from the harness is `SUPPORT_AI_AGENT_ENABLED=false`; disabling all provider use is `SUPPORT_AI_ENABLED=false`.
- both provider paths use exact OpenRouter `POST /v1/chat/completions`. The facade rejects any other provider URL, model, or reasoning profile before a provider call. The locked profile is canonical `deepseek-v4-flash-0731` (`deepseek/deepseek-v4-flash-0731` on the wire), medium provider-managed reasoning with the private trace excluded, a 45-second provider timeout inside a 50-second total deadline, at most one request per eligible message, and at most two concurrent provider runs. The 45/50-second windows are also the exact-route defaults when their environment values are omitted. The request intentionally omits `max_tokens` for this reasoning model and sends exactly one system message plus one user message with no `tools`, `tool_choice`, retry, or continuation payload.
- publish only the following secret-free harness configuration; keep the real key solely in the service environment through blank-at-rest `SUPPORT_AI_API_KEY`. `XCODY_API_KEY` remains a legacy compatibility alias only:

The support case alternative is `SUPPORT_AI_MODEL=deepseek/deepseek-v4-flash-vision-exp`
with the same medium reasoning and exact OpenRouter route. Its routing prefers
Fireworks and denies provider data collection. Ticket case reads and local OCR
follow [the support case boundary](../architecture/support-feedback-flow.md#read-only-ticket-case-context).
Install `poppler-utils`, `tesseract-ocr`, and `tesseract-ocr-rus` for PDF/image
text extraction; Pillow remains the existing pinned Python dependency.
Model selection does not authorize sending raw images or customer/provider
payloads. Keep per-service overrides in a secret-free EnvironmentFile loaded
after the common `.env`; do not overwrite the common environment during a
support-only rollout. Removing that override restores the common model settings.

```dotenv
SUPPORT_AI_ENABLED=false
SUPPORT_AI_AGENT_ENABLED=false
SUPPORT_AI_API_BASE_URL=https://openrouter.ai/api/v1
SUPPORT_AI_API_KEY=
SUPPORT_AI_MODEL=deepseek/deepseek-v4-flash-0731
SUPPORT_AI_REASONING_EFFORT=medium
SUPPORT_AI_TIMEOUT_SECONDS=45
SUPPORT_AI_RUN_DEADLINE_SECONDS=50
SUPPORT_AI_MAX_CONCURRENCY=2
SUPPORT_AI_CONCURRENCY_WAIT_MS=250
SUPPORT_AI_SESSION_TTL_SECONDS=3600
SUPPORT_AI_MAX_SESSIONS=256
SUPPORT_AI_OWNER_RATE_LIMIT_PER_MINUTE=6
SUPPORT_AI_MAX_RATE_BUCKETS=1024
SUPPORT_AI_PRE_RETRIEVAL_LIMIT=3
SUPPORT_AI_MAX_INPUT_CHARS=30000
SUPPORT_AI_MAX_OUTPUT_TOKENS=1200
```

- code pre-retrieves at most three topics from the validated deployed policy/KB snapshots. It has no model-visible tool and no DB, account, attachment, key/config, shell, arbitrary-file, or command-execution access; `safeDiagnostics` values never enter provider context. Provider/parse/safety failure can use a local KB answer only for fingerprint-bound confident routing; all other insufficient-evidence paths transfer to a human.
- knowledge refresh remains operator-side: first run `python scripts/pokrov_support_ai_kb_refresh.py run-xcody --dry-run`, then only with an owner-side runtime `XCODY_API_KEY` run `python scripts/pokrov_support_ai_kb_refresh.py run-xcody --apply`; review the KB diff before any separately authorized deploy.
- repository code cannot prove production feature flags, credential presence, enterprise route availability, or service state. This implementation did not deploy or restart production. Enablement requires retained live evidence for the exact committed route/model/reasoning/payload/policy/KB/retriever candidate, including zero payload-format HTTP 400 responses and honest latency/error/cache metrics.

Encrypted support bundles are also disabled until the owner provisions all
parts of the private runtime boundary. Keep the ticket HMAC secret and recipient
private-key file out of Git; the API receives only a signed public key-set JSON.
The quarantine and accepted directories must be private absolute paths on the
same owned filesystem, not public/static upload roots. `portal-api` may receive
and queue opaque ciphertext but must not have the recipient private-key file.
Only `portal-worker` receives that mounted file, and the worker is enabled only
after backup, retention, permission and rollback checks are retained.

```dotenv
POKROV_SUPPORT_UPLOAD_TICKET_SECRET=
POKROV_SUPPORT_SIGNED_KEY_SET_JSON=
POKROV_SUPPORT_BUNDLE_QUARANTINE_DIR=
POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR=
POKROV_SUPPORT_BUNDLE_WORKER_ENABLED=false
POKROV_SUPPORT_BUNDLE_WORKER_INTERVAL_SECONDS=5
POKROV_SUPPORT_BUNDLE_WORKER_BATCH_LIMIT=5
POKROV_SUPPORT_RECIPIENT_KEYS_FILE=
POKROV_SUPPORT_BUNDLE_L2_TG_IDS=
POKROV_SUPPORT_MODE_SIGNING_KEY_ID=
POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64=
POKROV_SUPPORT_MODE_CODE_SECRET=
RELEASE_HEALTH_RETENTION_DAYS=90
SUPPORT_BUNDLE_ACCEPTED_RETENTION_DAYS=30
SUPPORT_BUNDLE_QUARANTINE_RETENTION_DAYS=7
SUPPORT_BUNDLE_INCOMPLETE_GRACE_DAYS=1
SUPPORT_BUNDLE_ACCESS_AUDIT_RETENTION_DAYS=365
SUPPORT_BUNDLE_RETENTION_BATCH_LIMIT=100
```

The support-mode Ed25519 private key and code HMAC secret are server-only.
`POKROV_SUPPORT_MODE_CODE_SECRET` must contain at least 32 bytes of secret
material. The configured key ID/private key must match a public verification
key embedded in the exact Android/Windows candidate; a local test key or a
different candidate pin is a hard stop. Enabling issuance also requires current
operator RBAC/audit readback, rotation and rollback evidence. These variables
do not enable recipient decryption or support-bundle worker custody.

The master-only/manual `Support Signing Custody` workflow verifies the hosted
Actions private key and code-secret contract against the exact public pin on
`POKROV-app/main`. Secret values are scoped only to the validation step; the
retained artifact is a public revision/digest receipt. This source-control
custody check does not copy secrets to production, enable issuance, build a
candidate, or replace runtime/device/rollback evidence.

The payment-entitlement outbox worker is always supervised with the portal
worker; these values bound claim/retry work and do not enable a payment
provider:

```dotenv
PAYMENT_ENTITLEMENT_OUTBOX_BATCH_LIMIT=20
PAYMENT_ENTITLEMENT_OUTBOX_MAX_ATTEMPTS=5
PAYMENT_ENTITLEMENT_OUTBOX_STALE_AFTER_SECONDS=300
PAYMENT_ENTITLEMENT_OUTBOX_POLL_SECONDS=5
```

Commercial offer preview uses a dedicated HMAC key. It must not reuse the
checkout-ticket, web-session, provider or support-upload secret. All API
instances serving one commercial revision must receive the same candidate key;
missing or shorter-than-32-byte material prevents token issuance. The TTL is
clamped to 60–900 seconds and does not extend an existing reservation deadline.

```dotenv
COMMERCIAL_OFFER_HMAC_SECRET=
COMMERCIAL_OFFER_HOLD_TTL_SECONDS=600
```

Pause acquisition and wait at least the maximum outstanding hold TTL before a
key rotation or rollback that changes this secret; otherwise current holds fail
signature verification by design. Retain only presence/key-version and exact
candidate/process readback, never the key or a token. These variables do not
approve legal launch, create a campaign, enable a provider or prove deployed
preview/order behavior. Atomic order consumption is a separate release gate.

The API process also owns one bounded payment-provider HTTP registry. These
values configure its provider policies; code clamps every value. They do not
enable a provider or prove production connectivity:

```dotenv
PAYMENT_HTTP_CONNECT_TIMEOUT_SECONDS=5
PAYMENT_HTTP_SOCK_READ_TIMEOUT_SECONDS=15
PAYMENT_HTTP_POOL_LIMIT=20
PAYMENT_HTTP_MAX_RESPONSE_BYTES=65536
LAVATOP_REQUEST_TIMEOUT_SECONDS=30
CARDLINK_REQUEST_TIMEOUT_SECONDS=30
PALLY_REQUEST_TIMEOUT_SECONDS=30
PLATIMA_REQUEST_TIMEOUT_SECONDS=30
FK_API_REQUEST_TIMEOUT_SECONDS=25
```

Before deployment, retain an exact-candidate startup/shutdown check and a
sanitized telemetry sample containing only provider/operation/status/latency/
result code. Prove timeout, pool and oversized-response behavior in the deployed
environment without recording URL queries, headers, credentials or bodies.
Local registry tests are not live provider or pool evidence.

The same health endpoint includes a fixed integer-only `payment_db` projection.
Before candidate promotion, exercise concurrent payment DB and independent async
health requests on the deployed process, retain queue-wait/duration/failure
counts, and confirm rollback after an injected candidate-only DB failure. Do not
capture SQL, parameters or customer/order identifiers. Local threadpool tests
do not prove deployed database-pool capacity or event-loop latency.

Before a production rollout, apply the rerunnable outbox migration, verify the
new table/indexes, start the worker, and retain queue depth/oldest-age plus one
exact-candidate callback-to-provisioning readback. Local SQLite tests are not
PostgreSQL migration, process supervision or control-panel proof.

Local schema, API, crypto and worker tests do not prove production key custody,
rotation, private-directory permissions, process isolation, scheduling or a
successful real upload. Enablement and rollback are separate owner operations.
Keep the L2 allowlist empty until named production operators and least-
privilege directory access are approved. API workers may return accepted
ciphertext but still receive no recipient private key. Before enablement,
retain a dry retention run/backlog count, held-object proof, access-audit proof,
and alerts for worker failure/file errors; these local defaults are not a
PostgreSQL or object-store TTL.

Observer-lite canary install:

```powershell
python scripts/remote_install_node_observer.py --brain-ip 82.21.114.104 --node-code pl --run-now
```

### Antiabuse retention incident and rollback

`portal-worker` owns the frequent antiabuse privacy sweep. Its interval is
clamped to 60-900 seconds. Cleanup runs outside the shared asyncio event loop;
one chunk is capped by `ANTIABUSE_RETENTION_MAX_BATCHES_PER_RUN`, and remaining
backlog schedules another chunk after one second. Every database batch commits
separately.

Read-only backlog inspection:

```powershell
python scripts/cleanup_antiabuse_retention.py
```

Explicit one-shot drain:

```powershell
python scripts/cleanup_antiabuse_retention.py --apply
```

The command reads `DATABASE_URL` through normal backend configuration but never
prints it. Its JSON output contains counts only. Do not pass a database URL on
the command line, and do not treat a dry run as cleanup evidence.

Before a rollback to code without `antiabuse_retention_job`:

- retain a dry-run and applied count report with no secrets or row contents;
- verify `after` is all zero;
- install an equivalent scheduled cleanup in the rollback revision before
  stopping the new worker;
- keep antiabuse/security/user audit rows and null only the overdue sensitive
  fields;
- treat stopped worker or post-drain non-zero backlog as an incident, not a
  successful rollback.

The retention windows are an operational SLO, not a PostgreSQL TTL. Worker
outage or persistent backlog can exceed them and blocks a production readiness
claim until the backlog is drained and monitoring is restored.

### SQLite to PostgreSQL rehearsal

The guarded rehearsal entrypoint is:

```powershell
python scripts/migrate_sqlite_to_postgres.py inventory `
  --sqlite-path .tmp\migration\source.db `
  --output .tmp\migration\source-counts.json

# Review every table count before continuing.
python scripts/migrate_sqlite_to_postgres.py rehearse `
  --sqlite-path .tmp\migration\source.db `
  --snapshot-path .tmp\migration\source.snapshot.db `
  --source-manifest .tmp\migration\source-counts.json `
  --postgres-url-env REHEARSAL_POSTGRES_URL `
  --confirm-target portal_rehearsal `
  --reset-target `
  --rerun-check `
  --report .tmp\migration\rehearsal-report.json
```

Set `REHEARSAL_POSTGRES_URL` outside git and command-line arguments. The target
database name must exactly match `--confirm-target` and end in `_rehearsal`.
The command refuses to overwrite an existing snapshot. Both source and snapshot
may contain customer data and must stay outside git, docs, chat and ordinary
artifacts.

`inventory` is read-only and writes counts only. It is not automatic approval:
an operator must review the manifest against expected production totals. The
snapshot must contain required core tables and exactly match every manifest
table/count before any target reset begins.

The command:

- snapshots SQLite through `sqlite3.Connection.backup()` and runs
  `PRAGMA quick_check`;
- creates/migrates the disposable target under the canonical schema lock;
- resets, streams, backfills and validates target data in one transaction;
- synchronizes owned integer sequences after explicit copy and before backfill,
  then records final sequence state after the successful data commit;
- optionally repeats the replace and compares normalized report plus streamed
  target-content digests;
- writes an atomic JSON report containing names, hashes, counts and statuses,
  never URLs, passwords or row values.

Unexpected database/runtime failures expose only a generic error class in the
report and terminal. SQL `DETAIL` and bound parameters are never copied into
rehearsal evidence.

`backup_restore.status=AVAILABLE_NOT_RUN` is still not restore proof. If local
`pg_dump`/`pg_restore` are absent, the report says
`SKIPPED_TOOL_UNAVAILABLE`. A real redacted snapshot, source quiescence,
PostgreSQL credentials, backup/restore execution and cutover approval remain
manual owner gates.

The older no-subcommand copier remains compatibility-only for existing operator
automation. Do not use `--truncate-target` as rehearsal evidence. The remote
production cutover script is not hardened or executed by this slice.

### Production PostgreSQL encrypted clone and candidate gate

Use `remote_postgres_backup_restore_gate.py` when the live database is already
PostgreSQL and an encrypted production-to-rehearsal clone is required. The
source guard accepts only the exact confirmed `portal` database. The target
must be separately confirmed, end in `_rehearsal`, and differ from the source.
The script never prints a database URL or passphrase and does not retain a
plaintext dump:

```powershell
$env:POKROV_POSTGRES_BACKUP_PASSPHRASE = <read from the local protected secret store>
python scripts/remote_postgres_backup_restore_gate.py `
  --brain-ip <brain-ip> `
  --source-db portal `
  --confirm-source portal `
  --target-db portal_candidate_rehearsal `
  --confirm-target portal_candidate_rehearsal `
  --report C:\path\outside-git\postgres-backup-restore.json

# Review PLAN_ONLY before adding --apply. Use --reset-target only for an
# explicitly approved disposable target.
Remove-Item Env:POKROV_POSTGRES_BACKUP_PASSPHRASE
```

The apply path exports one repeatable-read snapshot, streams `pg_dump -Fc`
directly into AES-256-CBC/PBKDF2 encryption, and verifies the encrypted stream.
Its evidence connection begins with a repeatable-read `READ ONLY` transaction
as the first database statement, imports the exported snapshot, and emits one
aggregate JSON record per read-only query through psql `\gexec`. It must not use
temporary tables or any source DDL/DML.
It resolves the ordinary login role from the live `DATABASE_URL` entirely on
the control plane, checks that the URL still names the confirmed source, creates
the target owned by that role, removes database/schema access from `PUBLIC`,
grants the role explicit `USAGE, CREATE` on `public`, and restores with
`--no-owner --no-privileges --role=<resolved role>`. Neither the URL nor role is
included in reports.

After restore, the gate proves that the role owns the target, the `public`
schema, and every supported namespaced public object: all relations and indexes,
routines, types, extensions, collations, conversions, operators and
operator classes/families, text-search dictionaries/configurations, extended
statistics, and schema-scoped default ACLs. It proves the role can create in
`public` and that `PUBLIC` database/schema access remains revoked, then compares
exact aggregate table counts. The encrypted archive, report, and protected
passphrase material stay outside Git. A count match is restore proof for the
cloned target, not approval to mutate the source or deploy application code. If
target creation, ACL setup, restore, or ownership evidence fails, retain the
encrypted backup and treat the target as tainted; reset only the separately
confirmed `_rehearsal` database on the next approved run. Do not use
cluster-wide `REASSIGN OWNED` as repair.

After a complete verified restore and integrity match, the gate retains the
three newest matching encrypted archives by default and protects the archive
from the current run explicitly. `--backup-retain-count` accepts a bounded value
from 1 to 30. Retention runs only after restore proof; failures are reported as
`backup_retention.status=FAILED` without rewriting a completed backup/restore
result into a false failure. Manual files, plaintext legacy dumps, and other
backup families are outside this automatic selector.

The destructive inactive-user purge keeps only the two newest matching
`portal_pre_inactive_user_purge_<timestamp>.dump` safety snapshots after a
successful purge. These short-lived plaintext rollback files are root-only and
do not replace the encrypted restore-proven backup family. A separately named
encrypted historical anchor is evidence and is not selected by either rolling
retention rule.

Run the exact application candidate only after the clone is retained. Build the
archive from a clean `portal_bot` tree at `HEAD`; keep it outside Git:

```powershell
$commit = (git rev-parse HEAD).Trim()
git archive --format=tar --output C:\path\outside-git\portal-bot-candidate.tar $commit portal_bot shared
$sha256 = (Get-FileHash C:\path\outside-git\portal-bot-candidate.tar -Algorithm SHA256).Hash.ToLowerInvariant()

python scripts/remote_postgres_candidate_gate.py `
  --brain-ip <brain-ip> `
  --candidate-archive C:\path\outside-git\portal-bot-candidate.tar `
  --candidate-sha256 $sha256 `
  --candidate-commit $commit `
  --source-db portal `
  --confirm-source portal `
  --target-db portal_candidate_rehearsal `
  --confirm-target portal_candidate_rehearsal `
  --report C:\path\outside-git\postgres-candidate-plan.json
```

The archive contains the exact tracked backend plus its tracked `shared/`
runtime truth; dirty scoped files, untracked files, and secret-like filenames
are rejected. The exact tracked `.env.example` template is the only environment
filename exception; real `.env`, credential, password, private-key, and
keystore paths remain forbidden. Review
`PLAN_ONLY`, use a new no-clobber report path, then add `--apply`. The
candidate gate derives the target URL in remote process memory, imports only the
uploaded archive, and connects only to the rehearsal database. Before reading
application rows or running DDL it proves target/session identity, ordinary
login-role attributes, database ownership, schema privileges, `users` read
access, and ownership of every public application object. It then checks
additive DDL and index lock timeouts, the schema advisory lock, two idempotent
`db.init_db()` runs, `FOR UPDATE SKIP LOCKED`, concurrent attachment bind/retry,
and a real PostgreSQL protocol-level lost commit acknowledgement. Reports carry
only boolean/count access evidence, never a role or URL. Synthetic rows and
probe DDL must be confirmed absent before the report can say `PASS`.
The script does not create, drop, or reset a database and does not deploy or
restart a service.

Current R12 local compatibility (2026-09-08): the
[actual previous/current API rehearsal](../developer/work-orders/2026-09-05--consolidated-release-and-post12/EXECUTION-INTEGRATED-BACKEND-COMPAT-2026-09-08.md)
binds 197 read-only verified deployed source files to 200 Git-source files from
`16407b8`. The actual APIs pass 25 HTTP assertions and five SQL writes during
coexistence and code rollback in isolated PostgreSQL. Schema/bootstrap inputs
and observed columns/indexes/constraints match; no new expand/contract change
exists for this exact pair. This is local compatibility evidence, not a current
production snapshot, deployed-candidate or volume/lock/recovery pass.

The subsequent [2026-09-09 Brain rehearsal](../developer/work-orders/2026-09-05--consolidated-release-and-post12/EXECUTION-BRAIN-REHEARSAL-2026-09-09.md)
restored an encrypted production snapshot (121 tables, 2,466,128 rows) into
`portal_r12_20260909_rehearsal` and passed the exact `235e8a4` candidate database
gate on that clone. Three promo files also restored byte-identically from a
separate encrypted archive. Source services retained their PIDs and zero
restarts. Support attachments were empty; atomic cross-store consistency and
deployment of the current API/bot/worker are not claimed. Archives and the
rehearsal database remain retained outside Git on Brain.

### Static sites deploy

Observed 2026-09-09: backend `7d37005` and static inputs `0392052` are deployed
on Brain; static release `20260909045925` passed all 887 file hashes and
canonical public HTTP readbacks. Previous releases are preserved in a verified
server-side archive and the admin rollback pointer. Operator bootstrap/session
checks passed, but actual Telegram OIDC login is blocked at the admin callback;
Allowed URLs configuration is pending owner access. Do not disable bootstrap
or claim operator/release acceptance from these bounded checks. See the
[dated execution and retained evidence](../developer/work-orders/2026-09-05--consolidated-release-and-post12/EXECUTION-PLATFORM-DEPLOY-2026-09-09.md).

- [remote_deploy_brain_static_sites.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_static_sites.py)
- static deploy packages `marketing/out`, `webapp/out`, and `adminapp/out` as local `tar.gz` bundles, uploads one archive per surface, extracts them into a versioned release directory, validates required files, then atomically switches `/var/www/portal/{marketing,webapp,adminapp}` symlinks
- the `adminapp` prebuild deterministically emits `__build.json` and
  `__routes.json` from `operator-center.manifest.json` and
  `operator-center.cutover.json`; the pair binds exact
  app/domain/frontend commit/source state/build time/expected API schema to the
  route-manifest hash, cutover-matrix hash and seven-workspace migration oracle
- local and remote static validation requires both identity files, matching
  hashes and schemas, and rejects the obsolete `POKROV API superadmin v1`
  shell. Post-deploy smoke reads both files from `admin.pokrov.space`; HTML/file
  presence alone is insufficient Operator Center identity proof
- immediately before switching the canonical `adminapp` symlink, the deploy
  script atomically records the previous in-tree release target as
  `/var/www/portal/adminapp.rollback`. This is a rollback pointer contract, not
  proof that a production rollback drill has run
- `--rollback-adminapp` is an explicit destructive operator mode. It requires
  `--confirm-adminapp-rollback ROLLBACK_ADMINAPP` plus exact current/rollback
  route-manifest and cutover-matrix SHA-256 values. The command rejects targets
  outside `/var/www/portal/releases/*/adminapp`, validates both bundles before
  switching, atomically swaps `adminapp`/`adminapp.rollback`, then validates the
  served pointer again. Do not run it without an authorized exact candidate and
  retained pre/post evidence
- static deploy retains only the five newest versioned directories under `/var/www/portal/releases/`; the one-time `legacy_backups/` migration snapshot is not recreated after the public paths become symlinks
- `webapp/public/telegram-web-app.js` is the reviewed byte-identical mirror of the official Telegram Mini App SDK v63 (`telegram-web-app.js?63`, SHA-256 recorded beside its layout include); the cabinet loads it from its own origin so an unavailable `telegram.org` cannot block pre-hydration startup, and any SDK refresh must update the pinned integrity test in the same change
- `python scripts/remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --plan-only` validates and bundles local `marketing/out`, `webapp/out`, and `adminapp/out` without opening SSH; it proves the local Operator Center identity checks are satisfiable but is not public readback. Local and remote validation must reject legacy `marketing/out/fk-verify.html` and `marketing/out/fk-payment-theme.css` files because Lava.top/hosted checkout is the current public payment path
- before bundling, static deploy removes only the legacy `v=<release>` query field from exported `/_next/static/*` references while preserving unrelated query fields and fragments; Next chunk, CSS, font, and media filenames are content-hashed, HTML is revalidated, and inconsistent query-busted chunk identities can prevent soft navigation from committing
- `app.pokrov.space` and `admin.pokrov.space`/`www.admin.pokrov.space` should serve HTML with `Cache-Control: no-cache, must-revalidate`, while `/_next/static/*` assets should serve `Cache-Control: public, max-age=31536000, immutable`
- `admin.pokrov.space` serves the dedicated `adminapp/` static export and must
  route API calls to `https://api.pokrov.space`; the canonical v2 path uses a
  credentialed opaque `__Host-pokrov_admin_session` cookie and does not make
  `webapp/` the admin host. Production API configuration must provide a
  dedicated `ADMIN_OPERATOR_SESSION_SECRET` of at least 32 bytes, the exact
  `ADMIN_OPERATOR_ENVIRONMENT`, and the served admin origins in
  `ADMIN_OPERATOR_TRUSTED_ORIGINS`; do not reuse or print another signing key.
  `ADMIN_OPERATOR_OIDC_REDIRECT_URI` must be the exact registered HTTPS admin
  callback (normally `https://admin.pokrov.space/`). Keep
  `ADMIN_OPERATOR_LEGACY_BOOTSTRAP_ENABLED=true` only during measured identity
  enrollment/cutover; set it to `false` after an authorized exact-candidate
  OIDC login and step-up have been retained. OIDC does not auto-create an
  operator or role, so provision and review those records before disabling the
  compatibility path.
  Idle, absolute, step-up and active-session bounds use the documented
  `ADMIN_OPERATOR_*_SECONDS`/`ADMIN_OPERATOR_MAX_ACTIVE_SESSIONS` variables.
  A missing/short secret or invalid environment fails closed. CORS must keep
  the exact admin origin with credentials; wildcard credentialed origins are
  forbidden
- public Caddy on `brain` should keep HTTP/3 disabled with `servers { protocols h1 h2 }` and should serve `Alt-Svc: clear` on public HTTPS responses while browsers may still have the previous `h3=":8444"` alternative cached; this avoids user networks that fail QUIC or non-standard UDP paths while preserving standard HTTPS on `443`
- public HTTP redirects are explicit in `infra/Caddyfile.internal`; do not rely on Caddy's automatic HTTPS redirect on the internal `:8444` listener, because public users must see `https://host/path`, not `https://host:8444/path`
- `www.app.pokrov.space`, `www.api.pokrov.space`, `www.connect.pokrov.space`, and `www.pay.pokrov.space` are HTTPS redirect aliases to their canonical non-`www` hosts; `www.admin.pokrov.space` remains a served admin alias until `admin.pokrov.space` DNS is confirmed on authoritative and public resolvers
- security baseline for `brain`: expose only `80/tcp`, `443/tcp`, and the active SSH port publicly; Caddy `:8444`, API `:8080`, legacy `:2096`, and panel ports must be loopback-only or firewall allowlisted
- `infra/brain-haproxy-l4.cfg` and `infra/portal-transport-front.cfg` use HAProxy TCP stick-tables as a self-hosted burst guard; this is not a volumetric DDoS guarantee and hoster/network filtering remains a separate incident-control layer
- `infra/Caddyfile.internal` owns the public HTTP security headers (`nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors`, `Alt-Svc: clear`) while API path limits remain backend-owned
- [remote_deploy_brain_caddy_config.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_caddy_config.py) validates the repo Caddy config, uploads it to `brain`, backs up `/etc/caddy/Caddyfile`, validates the installed file, reloads Caddy, and retains only the five newest script-owned `Caddyfile.bak-<release_id>` rollback files; use it for Caddy-only changes instead of the older legacy proxy patch helper
- [remote_deploy_brain_haproxy_config.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_haproxy_config.py) applies the same validate/backup/install/reload/health/rollback contour to `/etc/haproxy/haproxy.cfg`; deploy the proxy-protocol-aware Caddy config first, then HAProxy `send-proxy-v2`, so a partial rollout never sends a PROXY preface to an unprepared listener
- fresh node/bootstrap paths must enable UFW default-deny and fail2ban `sshd` with escalating bans; root password access is retained only as break-glass until the owner approves a key-only cutover
- repo-managed systemd units should carry `NoNewPrivileges`, `PrivateTmp`, and read-mostly system protections unless a unit has a documented operational need for broader write access

### Emergency catalog deploy

The emergency catalog is deployed fail-closed. Source code, migrations, admin
UI and the pinned probe runtime may be installed while
`EMERGENCY_CATALOG_WORKER_ENABLED=false`; no source row is distributed merely
because the code exists on `brain`.

Required order:

1. take and retain the normal production database backup;
2. deploy portal code and static sites, leaving the emergency worker disabled;
3. run `remote_prepare_emergency_catalog_env.py --brain-ip 82.21.114.104`
   without `--enable-worker`. It creates signing and material-encryption keys on
   `brain`, writes a mode-`0600` environment file atomically and prints only the
   public signing key/key id;
4. install the exact hash-pinned Linux probe engine and GeoIP refresh units with
   `remote_install_emergency_runtime.py`;
5. deploy `infra/Caddyfile.internal`, verify Caddy, then deploy
   `infra/brain-haproxy-l4.cfg`; confirm the owned payload endpoint returns its
   deterministic digest and a country header derived from the real PROXY peer;
6. restart/verify API and worker with distribution still disabled, inspect the
   redacted admin status, then explicitly enable the worker and stage/probe one
   snapshot;
7. promote only a 4–20 member rolling pool of fresh exact-probed candidates
   with the bounded safe-delta preview. Current-revision successes lead; recent
   retained successes may fill empty slots for at most 24 hours, with stable
   material identity and unique-host checks. Start the client cohort only after
   signed readback and synthetic route proof.

Do not copy private signing or material keys into the repository, release
artifacts, logs or operator browser. Before destructive server recovery, retain
the mode-`0600` environment backup on an encrypted operator-controlled medium;
losing the signing key requires a client trust-key rotation, not silent key
replacement. The admin `disable` action stops new catalog/profile delivery and
prevents automatic worker promotion, but it cannot recall a valid offline cache
already stored on a device. Use short snapshot expiry plus entitlement checks,
then explicit rollback or promotion to reopen distribution.

### Bot token / username switch

- [remote_switch_bot_tokens.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_switch_bot_tokens.py)

### Release orchestration

- [release_orchestrator.py](C:/Users/kiwun/Documents/ai/VPN/scripts/release_orchestrator.py)
- staged shortcuts:
  - `python scripts/release_orchestrator.py --stage gates`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage backend`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage static`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage deploy`
  - `python scripts/release_orchestrator.py --brain-ip 82.21.114.104 --stage verify`
- wrapper steps stream child output, print heartbeat lines during quiet long-running steps, and enforce per-step timeouts unless the matching `--*-timeout-sec 0` option is used
- the GitHub Actions release orchestrator is manual-only; its default mode is `dry-run`, and `full` should be selected only after current gates and operator deploy intent are explicit
- dispatch inputs are passed through step environment variables and Bash argument arrays rather than interpolated into shell source; `NODE_PASS_BRAIN` is scoped to the orchestrator step, and secret-bearing remote runs are rejected unless `brain_ip` is the canonical `82.21.114.104` host with `pokrov.space` / `api.pokrov.space` domains

### Release handoff sync

- [remote_brain_apply_release_handoff.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_brain_apply_release_handoff.py)
- canonical client-owned metadata home: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/`
- standard operator input: versioned `release-handoff.json` under that metadata home
- bridge-era `release-links.env` is a compatibility fallback only
- canonical stable metadata pointer when maintained: `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/release-handoff.json`
- schema reference: [release_handoff_metadata.schema.json](C:/Users/kiwun/Documents/ai/VPN/scripts/release_handoff_metadata.schema.json)
- strict v2 input is validated again by the sync consumer, projected only from
  canonical Android APK and Windows setup-EXE artifact identities, and carries
  release channel, candidate, exact handoff/artifact-set SHA-256 and Core
  version/ABI/package into runtime env; legacy `downloads/runtime_env` parsing
  remains migration compatibility only

Exact-candidate evidence boundary:

- runtime download metadata sync and operations-evidence import are separate
  actions; neither one silently performs the other
- before import, compute the canonical candidate from `component`, `version`,
  `revision`, and `artifact_sha256`, and compare its derived `candidate_id`
  with the retained artifact bundle
- import only a redacted evidence envelope through the exact
  `POST /api/internal/releases/candidates` path using an approved
  HMAC-authenticated client and the dedicated `release:evidence` key scope
- keep `current`, `brain`, and `ru` evidence as separate rows with explicit
  labels; accepted labels include `PASS`, `FAIL`, `MANUAL_OWNER_TEST`,
  `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`,
  `BLOCKED_BY_ACCESS`, and `MISSING`
- an RU `PASS` is accepted only when it binds to the exact stored, eligible,
  current-manifest RU run; successful binding places that run on retention hold
- retention hold prevents normal 180-day cleanup of the evidence run, but does
  not prove a deploy, refresh an old run, or transfer evidence to another
  candidate
- do not include a secret value, raw log, provider payload, subscription URL,
  personal identifier, host credential, or arbitrary metadata in the import
- after import, read `/api/admin/releases/candidates` and
  `/api/admin/releases/{candidate_id}/readiness` and compare every origin with
  the retained source record

Local unit/contract tests, `adminapp` build/lint/E2E, and a clean diff are
candidate checks from the current workstation only. Even when all are green,
production deploy, `brain-origin`, RU-origin, live timer installation and live
secret/key state remain `NOT_REQUESTED`, `MANUAL_OWNER_TEST`, or
`BLOCKED_BY_ACCESS` until separately executed and retained.

### API-only lifecycle smoke

- [api_lifecycle_smoke.py](C:/Users/kiwun/Documents/ai/VPN/scripts/api_lifecycle_smoke.py)

### Observer-lite node install

- [remote_install_node_observer.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_node_observer.py)

### Publishing and signing guide

- [publishing-and-signing-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

### Monitoring and visibility guide

- [monitoring-and-visibility.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

### Authenticated egress adapter rollout

This rollout is fail-closed and must be staged. Collection can be deployed
before enforcement because `AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED` defaults
to `false`; while it is disabled, smart-connect retains the existing health and
capacity eligibility rules. Enabling it before every intended candidate has a
fresh authenticated PASS excludes nodes without that proof and can produce
`503` when no authenticated candidate remains.

Repository templates are deliberately non-runnable placeholders:

- `infra/portal-authenticated-egress-adapter.example.json` is the exact
  non-secret adapter schema;
- `infra/portal-authenticated-egress-canaries.example.json` is the separate
  credential-store schema and must never be copied into logs or evidence after
  real values are inserted;
- `infra/portal-node-metrics-authenticated-egress.conf` is the systemd drop-in
  wiring for the existing collector service; install it at
  `/etc/systemd/system/portal-node-metrics.service.d/authenticated-egress.conf`.

Owner-authorized deployment sequence:

1. Install a pinned sing-box binary and
   `scripts/singbox_authenticated_egress_adapter.py` as absolute root-owned,
   non-symlink regular files with mode `0755`; install `/etc/pokrov` and
   `/run/pokrov-authenticated-egress` with mode `0700`. The production
   adapter is Linux-only: each invocation creates its own `0700` subdirectory
   and a `0600` Unix socket, and rejects any core whose loopback SOCKS listener
   cannot be proved through `/proc` to belong to that live child.
2. Create the dedicated, revocable canary clients outside the repository.
   Install the runtime adapter config at the adapter's fixed
   `/etc/pokrov/authenticated-egress-adapter.json` path, then install the
   separate canary credential store and non-secret profile/expiry registry as
   root or collector-service owned mode `0600`. Replace every example
   placeholder; do not put values in argv,
   environment files, shell history, reports, or systemd unit text.
3. Before connecting the collector, invoke the adapter locally with one
   owner-controlled synthetic request and retain only its machine-code result.
   Confirm strict `not_run` for binding/material mismatch, then perform the
   owner-approved real canary test and require `authenticated_egress` PASS.
4. Install the systemd drop-in, set the existing
   `NODE_AUTHENTICATED_EGRESS_ADAPTER` and
   `NODE_AUTHENTICATED_EGRESS_PROFILES` paths, and daemon-reload. Before
   restarting the normal timer, run one explicitly scoped collector cycle as
   `python scripts/collect_node_metrics.py --only <node-code>`. The allowlist
   must contain exact enabled node codes; unknown or disabled codes fail before
   any probe or health write. The normal systemd timer omits `--only` and
   therefore retains full-pool collection. Do not start with the full registry.
5. Verify for that exact node that the DB timestamp is fresh,
   `authenticated_egress_ok=true`, admin output shows the same PASS, and basic
   `edge_reachability_ok` remains a separate diagnostic.
6. Record an owner-approved canary percentage and expand the registry by an
   explicit node allowlist to that percentage of enabled node inventory. The
   current control is per-node, not per-user traffic bucketing; do not label it
   as a user percentage. Observe at least one full freshness window before each
   expansion.
7. Expand to the full eligible inventory only after every included node has a
   fresh authenticated PASS and the projected smart-connect candidate set is
   non-empty. Then set `AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED=true`, restart
   the API, and verify the live shortlist before calling the rollout complete.

Rollback: first set `AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED=false` and restart
the API to restore the previous node-selection behavior. Then remove the
drop-in/runtime variables or restore the previous code candidate, daemon-reload,
and restart only the metrics timer/service as authorized. Removing only
credentials is an emergency revocation action; if enforcement remains enabled,
it intentionally returns to fail-closed exclusion and may cause `503`, so it is
not a healthy steady-state rollback.

### Paid rewards rollout boundary

The paid wheel/calendar implementation is repository-candidate truth until the
exact deployed candidate completes this rollout. Local tests do not prove a
production flag, worker, config, database backfill, or marketing deploy.

The guarded operator entrypoint is
[`scripts/reward_rollout.py`](C:/Users/kiwun/Documents/ai/VPN/scripts/reward_rollout.py).
It exposes only `preflight`, `backfill`, `configure`, and `verify`; it never
accepts credentials on the command line and never enables backend flags or the
marketing gate.

Before using it, collect a fresh secret-free runtime manifest on the owned
deployment host and expose its absolute local path only in the operator shell:

```json
{
  "instances": [
    {
      "instance_id": "api-1",
      "component": "api",
      "candidate": "<exact-git-sha>",
      "bonus_wheel_enabled": false,
      "bonus_calendar_enabled": false,
      "legacy_reward_mutator_accepting": false
    },
    {
      "instance_id": "bot-1",
      "component": "bot",
      "candidate": "<exact-git-sha>",
      "bonus_wheel_enabled": false,
      "bonus_calendar_enabled": false,
      "legacy_reward_mutator_accepting": false
    }
  ]
}
```

The manifest must contain every running API and bot instance and must come from
service-manager/container readback for that exact process set. Do not put a
token, credential, private connection URL, QR, provider response, environment
dump, or customer identifier in it. Missing API/bot reports, duplicate instance
IDs, malformed booleans, mixed candidates, enabled flags, a legacy mutator, an
unresolved account, or an open/invalid merge chain all fail closed. The script
does not discover an omitted instance, so the operator must reconcile the
manifest against the active service/container inventory before treating a pass
as fleet evidence.

From the exact deployed checkout, use a candidate-specific evidence directory:

```powershell
$candidate = '<exact-git-sha>'
$evidence = "docs/audit-artifacts/rewards/$candidate"
$env:REWARD_ROLLOUT_RUNTIME_MANIFEST = 'C:\absolute\owned-runtime\reward-runtime-manifest.json'

& python.exe -B scripts/reward_rollout.py preflight --candidate $candidate --evidence-dir $evidence
& python.exe -B scripts/reward_rollout.py backfill --candidate $candidate --confirm-apply reward-state-v1 --evidence-dir $evidence
& python.exe -B scripts/reward_rollout.py configure --candidate $candidate --confirm-apply paid_fortnightly_discounts_v3 --evidence-dir $evidence
& python.exe -B scripts/reward_rollout.py verify --candidate $candidate --evidence-dir $evidence
```

`preflight` and `verify` are read-only. `backfill` invokes the account-owned
reward-state backfill in one guarded database transaction and rolls it back if
the zero-unresolved invariant fails. `configure` locks `wheel_config`, hashes
the previous value, writes the exact code-owned
`paid_fortnightly_discounts_v3` preset, reads
it back in the same transaction, and rolls back on mismatch. Evidence contains
only candidate identity, timestamps, stable result codes, counts, and canonical
JSON hashes; it does not contain raw settings or runtime-manifest rows. A command
exit code of zero means its retained result is `PASS`; a blocked result exits
non-zero. Evidence filenames are exclusive-create: a repeated command must use a
new retained directory instead of overwriting an earlier observation.

Required order:

1. Stop/quiesce every legacy bot instance that can accept the old local wheel
   callback. The old adapter ignores `BONUS_WHEEL_ENABLED`; therefore a mixed
   fleet is unsafe even while the new flag is false.
2. Prove the exact candidate on every API, bot, and worker instance; prove both
   `BONUS_WHEEL_ENABLED=false` and `BONUS_CALENDAR_ENABLED=false`; prove account
   foundation has no unresolved identities, invalid merge chains, or open merge
   reviews relevant to the backfill.
3. Back up the production database, run additive migrations, and execute the
   account-owned reward-state backfill in one guarded transaction. Retain only
   counts, candidate identity, timestamps, and redacted stable codes.
4. Deploy the patched API, bot, and worker with both reward flags still false.
   Read both state endpoints and confirm `disabled_until_feature_flag`; mutation
   probes must return `bonus_feature_disabled` without creating grants/jobs.
5. Snapshot the previous `wheel_config`, write exact preset
   `paid_fortnightly_discounts_v3`,
   read it back, and retain canonical-JSON hashes plus outcome/count metadata.
   Do not copy secrets, raw user rows, private URLs, or provider payloads into
   evidence.
6. Enable wheel only, restart/read back every new API/bot instance, and run an
   exact active-paid smoke plus trial/free/expired/reward-tail denials. Verify
   grant, state, durable job, worker convergence, cooldown, and history before
   moving on.
7. Enable calendar only after the wheel slice is green. Verify first check-in,
   same-day idempotency, milestone grant, worker convergence, and ineligible
   denials.
8. Only after both backend features are verified may the static marketing build
   set `NEXT_PUBLIC_PAID_REWARDS_MARKETING_ENABLED=1`; rebuild and deploy the
   marketing surface, then verify the gated copy from the exact public artifact.

Safe rollback disables the marketing gate and both new backend flags on the
patched candidate first, verifies disabled readback, and leaves committed typed
grants/history intact. If a config rollback is needed, restore the snapshotted
canonical config and read it back. Never restart an unpatched legacy bot that
ignores the kill switch. Worker sync failures remain retry/manual-review
evidence; do not delete grants or reward state to make the dashboard look clean.

## Current Operator Procedures And Retained Evidence

Active execution checklists:

- [Android Production Signing Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Android Physical Device Audit Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- [RU Origin Probe Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)
- [Public Beta Release Runbook](C:/Users/kiwun/Documents/ai/VPN/docs/operations/public-beta-release-runbook.md)

Current operator playbooks:

- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)
- [Runtime App Download Smoke](C:/Users/kiwun/Documents/ai/VPN/docs/operations/runtime-app-download-smoke.md)
- [Lava.top Payment Operations](C:/Users/kiwun/Documents/ai/VPN/docs/operations/lavatop-payment-operations.md)

Retained dated evidence, not current procedure authority:

- [Email Delivery Webhook Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
- [Release Links And Final Handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)

### Commercial capacity automation and revision rollback

`portal-worker` owns the local commercial-capacity evaluator. Configure
`COMMERCIAL_CAPACITY_AUTOMATION_ENABLED=true` and a bounded
`COMMERCIAL_CAPACITY_AUTOMATION_INTERVAL_SECONDS` (default `300`, runtime clamp
`30..3600`). Readback is `GET /api/admin/campaigns.capacity_automation`; it is
not a production/provider/CDN proof. A live auto-managed campaign in a forbidden
band, missing evaluation freshness or a transition without its bounded
`AdminAudit` row is a stop condition.

Create and verify one complete repository revision bundle without deploying it:

```powershell
python scripts/commercial_revision_bundle.py snapshot --output C:\safe\commercial-2026-08-21.1.zip
python scripts/commercial_revision_bundle.py readback --bundle C:\safe\commercial-2026-08-21.1.zip
python scripts/commercial_revision_bundle.py restore --bundle C:\safe\commercial-2026-08-21.1.zip
```

`restore` is dry-run unless `--apply` is explicit. Local apply additionally
requires both `--expect-current-revision <current>` and
`--expect-bundle-sha256 <readback-sha>`; it stages same-directory files,
readbacks every byte and restores already-replaced preimages if any later write
fails. The bundle contains the exact product facts, tariff sources/adapters,
commercial JSON/schema/TypeScript adapter and generated reference. Repository
restore does not deploy backend/static assets, purge a CDN, alter a campaign,
or prove public/admin readback; those remain separately authorized steps.

### Lava.top Checkout Enablement

The backend supports `lavatop` as the active RUB provider for public beta; public provider env must stay Lava-only (`RUB_PAYMENT_PROVIDER_ENABLED=lavatop`, `RUB_PAYMENT_PROVIDER_ORDER=lavatop`). As of `2026-05-15`, the authenticated cabinet beta path has redacted live evidence for invoice creation, authenticated success callback handling, invalid-auth rejection, account extension, and fulfillment idempotency. Required env is documented in [Lava.top Payment Operations](C:/Users/kiwun/Documents/ai/VPN/docs/operations/lavatop-payment-operations.md): `LAVATOP_API_KEY`, `LAVATOP_OFFER_ID` or per-plan `LAVATOP_OFFER_ID_<PLAN_CODE>`, and either `LAVATOP_WEBHOOK_API_KEY` or Basic webhook credentials. Anonymous public checkout also requires configured email delivery (`EMAIL_DELIVERY_WEBHOOK_URL` plus relay secret/SMTP env) before it can safely issue paid access keys.

The 1.2.0 return projection additionally requires
`PAYMENT_RETURN_HMAC_SECRET` (or the documented checkout/session signing
fallback), bounded `PAYMENT_RETURN_TOKEN_TTL_SECONDS` and
`PAYMENT_RETURN_PENDING_TTL_SECONDS`. `LAVATOP_SBP_ENABLED` and
`LAVATOP_CARD_ENABLED` control the server-owned method capability rows;
disabling a row must leave it visible and unavailable with a closed reason.

Marketing `/success` and `/fail` are identity-free redirect adapters. They may
carry `provider` and `return_surface` only, then return to checkout where the
session token is read and the query is stripped. A deploy/readback check must
fail if a return token, order ID, buyer identity or offer token appears in the
provider redirect URL.

Retained evidence: [Paid Checkout Launch Evidence - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json), [Brain Post-Deploy Live Probe - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json), and [Live Payment And Email Confirmation - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md). Failed-payment no-fulfillment and paid access-key delivery have beta evidence; refund/chargeback reconciliation remains an operator runbook requirement before stronger production checkout claims.

### External RU probe runner

- [ru_probe_runner.py](C:/Users/kiwun/Documents/ai/VPN/scripts/ru_probe_runner.py)
- [build_ru_origin_probe_bundle.py](C:/Users/kiwun/Documents/ai/VPN/scripts/build_ru_origin_probe_bundle.py)
- [remote_install_ru_origin_probe.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_ru_origin_probe.py)

Typical use from the external RU host:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

Для candidate.6 сначала соберите и проверьте неизменяемый source/unit bundle из
точного platform commit `5713324c1c0c2566befadf527bc09ec0ecf84a4e`.
Канонический пакет имеет SHA-256
`e7eb8ec20693f9626d6e7697c7845fa165e77fc1daa7df580ef0618248be345b` и не
содержит runtime secrets. Доступ к RU-host берётся только из утверждённого
inventory/SSH config; адреса, пароли и ключи в документацию или отчёты не
копируются. Установка, ручной run, upload, heartbeat и admin readback остаются
отдельными авторизуемыми действиями и доказательствами.

`remote_install_ru_origin_probe.py` без `--apply` выполняет только secret-free
read-only PLAN. APPLY/ROLLBACK защищены точными confirmations и receipt, а rollback
никогда не удаляет probe spool. Наличие инструмента или успешный PLAN не является
доказательством установки либо RU-origin PASS.

### RF Reserve Note

- [remote_install_mini_canary_stack.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_mini_canary_stack.py)
- [remote_apply_ru_bridge_relay.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_apply_ru_bridge_relay.py)

Status:

- previous `remote_install_mini_canary_stack.py` xhttp/hysteria experiments remain historical/operator tooling only
- `remote_apply_ru_bridge_relay.py` is the current owner-approved emergency bridge path: it syncs active user UUIDs from `brain`, installs/preserves a bridge Xray Reality service, restricts bridge egress to POKROV target nodes, excludes `us`, and patches public bridge metadata into `network_rollout_config`
- the brain rollout patch keeps the old single-bridge top-level metadata compatible and merges `ru_bridge_relay.endpoints[]` by stable endpoint `id`; rerunning a type 2/type 3 RU bridge rollout must update that endpoint without deleting the existing `mini` endpoint
- when the new RU server is available, add it as a separate RU-node/bridge lane instead of replacing `mini`; prove both bridge paths independently before promoting a cohort
- rerun `remote_apply_ru_bridge_relay.py --apply --update-brain-rollout` after meaningful user growth or before relying on the bridge for a live incident, because `mini` authorizes the active UUID snapshot that was synced at apply time
- when bridge targets mix DNS hosts and raw IP hosts, keep Xray routing allow rules split by `domain` and `ip`; one rule containing both fields can fail to match the country-hop connection and make every `Белые списки` detour appear dead
- generated Hiddify/sing-box profiles must keep the bridge hop as a hidden technical outbound (`POKROV мост §hide§`) and expose only the country choices plus `Белые списки`; a standalone bridge delay failure is not a country-node outage
- while the bridge is globally enabled, `RU_BRIDGE_SELECTOR_DIRECT_CODES` controls which direct country entries remain visible to Hiddify balancers; the default keeps `de` direct and lets bridge-eligible non-DE countries surface through `Белые списки`
- rollback is `defaults.transport_profile=legacy_reality_fallback`; enable or keep `ru_bridge_relay` only through an explicit cohort/carrier/default decision after verification

### Telegram MTProto proxy on the former free node

- [remote_install_mtproto_proxy.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_mtproto_proxy.py)

Current canonical state:

- the node (`151.245.217.23`) is disabled for POKROV consumer delivery; its free-pool membership, active free keys, mappings, and queued/running free-provisioning jobs are zero
- the `2026-08-19` guarded retirement apply revoked the final residual free key and retired the remaining free-target rows; a post-apply plan and paid-node coverage readback both returned zero consumer drift. The retained database backups were created on Brain before mutation.
- `x-ui.service`/Xray shutdown on that host is `BLOCKED_BY_ACCESS` until fresh node-side evidence is available; the canonical application and database do not route users there
- `portal-mtproto.service` on `tcp/9443` is a separate Telegram-only compatibility service, not subscription delivery; its current runtime state also requires fresh node-side evidence
- the previous `mini:443` MTProto attempt is disabled; if this compatibility proxy is retained, it stays isolated on the former free node
- any MTProto secret and share links must live only in `/etc/portal-mtproto.env` on the former free node; do not copy them into docs, commits, or handoff reports
- enable `portal-mtproto-config-refresh.timer` only after fresh reachability and service-state evidence from that host
- the official Telegram MTProxy source currently needs a PID namespace workaround on this host, so the systemd unit starts it through `unshare --fork --pid --mount-proc`

Typical install or refresh from the repository root:

```powershell
python scripts/remote_install_mtproto_proxy.py --node-code free --node-host 151.245.217.23 --ssh-port 29374 --listen-port 9443 --enable-refresh-timer
```

If the endpoint is deliberately restored and freshly verified, register `151.245.217.23:9443` or an approved DNS name that resolves to `151.245.217.23` and still uses port `9443`.

### Scheduled release announcement

Use `scripts/remote_schedule_release_announcement.py` only after the matching platform code is deployed and Brain readiness is green. The script accepts an explicit timezone-aware timestamp between two minutes and 24 hours ahead, uploads a `0600` config under `/root/portal_bot/ops-schedules/`, and creates a persistent one-shot systemd timer. At execution time the Brain job prepares and confirms the same guarded admin intents used by the operator UI:

- `live_update.create` publishes the Russian in-app update card;
- `broadcast.send` freezes the active Telegram audience and records delivered, retryable and terminal outcomes per recipient;
- deterministic idempotency keys prevent a replay from duplicating either action;
- the config is removed only after both guarded actions complete. Partial Telegram delivery remains retained evidence and exits nonzero.

Never schedule before deploying `portal_bot/release_announcement_job.py`, and never place credentials, raw recipient identifiers or connection material in the config or systemd description.

### Feedback bot service install

- [remote_install_feedbackbot_service.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_feedbackbot_service.py)

## Transport Rollout And Node Shaping

The transport rollout stays additive: the current Reality path remains in place while app-first cohorts are moved to `grpc_443_primary` through rollout policy and per-node transport catalogs.

Transport policy rule:

- `nodes.transport_profiles_json` is the canonical per-node transport catalog for rollout and should carry the fixed profile set `legacy_reality_fallback`, `grpc_443_primary`, `reserve_xhttp_cdn`, and `operator_lab`; `ru_bridge_relay` lives in `network_rollout_config` because it is a cross-node RU bridge, not a node-local delivery inbound. `awg2_lab`, `awg31_lab` and `hy2_lab` are explicitly rejected from this catalog because their material is device-bound and encrypted separately.
- when one physical node/inbound is reachable through more than one public address, put the stable DNS names and consumer labels in that profile's `delivery_endpoints[]` (maximum eight). Keep `nodes.host` as the canonical primary address and `panel_base_url` as the management address. Do not create a second node row: that would duplicate provisioning, capacity, health, and panel ownership. Rollback is removal of `delivery_endpoints[]`, which restores the single canonical host without touching panel clients
- legacy node fields such as `inbound_id`, `vless_port`, and `reality_*` remain compatibility input and should synthesize `legacy_reality_fallback` when the transport catalog is empty
- `AppSetting.network_rollout_config` is the operator-controlled rollout source of truth for `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `network_rollout_config` is a JSON policy blob with `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `ru_bridge_relay`, `operator_lab`, `awg2_lab`, `awg31_lab`, `hy2_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- old node-inventory markdown moved to `docs/archive/flat-docs/08-node-inventory.md`; `scripts/node_inventory.py` keeps legacy bootstrap, DNS, and remote-maintenance helpers compatible with that retained IP snapshot, but live deployment decisions must still use Postgres/admin API state, rollout config, and current probe evidence
- `defaults` normally pin `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split`; live incident response may temporarily set `transport_profile=ru_bridge_relay`
- `carrier_overrides` and `cohort_overrides` may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `reserve_xhttp_cdn` stays opt-in, disabled by default, and is intended only as a reserve path on eligible nodes until a later rollout wave promotes it explicitly
- `ru_bridge_relay` stays opt-in unless an incident commander explicitly promotes it; app-managed sing-box manifests expose countries at the top level and nested `Обычный` / `Белые списки` endpoint choices under non-US nodes, while US remains a direct-only target and is never routed through the RU bridge
- app-managed sing-box configs load runtime rule sets from `https://connect.pokrov.space/rules/geoip-ru.srs` and `https://connect.pokrov.space/rules/adblock.srs`; the brain host mirrors those files under `/var/www/portal/rules/` and refreshes them with `pokrov-singbox-rules-refresh.timer`. Caddy serves only those two owned `/rules/` paths as `application/octet-stream` before the connect-host fallback redirect. `verify_brain_ready.py` must reject HTML/redirect regressions by requiring HTTP success, `SRS` binary magic and a nontrivial body for both files.
- BitTorrent routing is RU-only when the rendered paid profile contains `ru`/`ru_spb` delivery outbounds: the generated config adds a hidden RU torrent selector and points `protocol=bittorrent` at it before the `geoip-ru` direct rule. Profiles without RU outbounds keep the old direct fallback.
- `operator_lab` remains allowlist-only, carries `enabled`, `allowlist_install_ids`, `allowlist_tg_ids`, `allowlist_node_codes`, and `expires_at`, and must stay hidden from public UI and mass session/profile payloads
- `awg2_lab` is a separate owner-only sing-box endpoint lane. Source defaults are `enabled=false` and `kill_switch_engaged=true`. Selection additionally requires the exact `pokrov.awg2.endpoint.v1` ID/SHA, `awg2-v1` endpoint revision, current generation, Windows/Android platform, install/user and node allowlists, a ready POKROV-owned `server_record_id`, and a current encrypted row in `awg2_lab_materials` for that exact device.
- AWG2 endpoint material is provisioned only through the L3 guarded `PUT /api/admin/client/awg2-lab/material`; intent, preview, audit and result retain fingerprints and safe generation/server/node state, never the endpoint, keys or raw install ID. `AWG2_LAB_MATERIAL_SECRET` must come from the secret manager and must not be committed.
- AWG2/AWG3.1 material replacement rejects a client public key already bound to another device, including retained history; a revoked key cannot be reissued. Compare the derived X25519 public key, not raw private-key text or a whole endpoint hash. The existing PostgreSQL transaction boundary serializes competing insertions of the same key. This is a material-store guard; a live server peer still requires its corresponding guarded operator provisioning/removal.
- `scripts/remote_bind_owned_awg_lab_device.py` selects only the target device's already provisioned, current, exclusive AWG2/AWG3.1 material. It no longer copies another device's keys or reissues material during profile selection. Repeated binding preserves material age and generation. Missing, expired, incompatible or historically shared keys fail before rollout mutation; first-time provisioning and rotation remain separate L3 material operations after preparing the matching server peers. Existing shared-key lab records must be migrated individually, with retained rollback, before selective server revoke. The script requires a backend source containing the key-binding guard.
- `awg31_lab` is the parallel owner-only AWG 3.1 lane. It has the same fail-closed allowlist, device-bound encrypted-material and managed-profile boundaries as AWG2, plus the reviewed AWG 3.1 timing/header-protection contract. `AWG31_LAB_MATERIAL_SECRET` is runtime-only secret-manager input.
- `hy2_lab` is a separate owner-only Hysteria2 lane implemented by the existing embedded sing-box engine. Source defaults are `enabled=false` and `kill_switch_engaged=true`. Selection requires exact `pokrov.hy2.outbound.v1` ID/SHA, `hy2-v1` revision, active-device/platform and node allowlists, a ready POKROV-owned server record and a fresh encrypted row in `hy2_lab_materials`. The managed subset requires verified TLS/SNI with ALPN `h3`, exactly one port, bounded bandwidth and optional Salamander; raw URIs, port hopping, Gecko, Mimic and insecure TLS fail closed.
- HY2 material is provisioned only through the L3 guarded `PUT /api/admin/client/hy2-lab/material`; `HY2_LAB_MATERIAL_SECRET` is separate runtime-only secret-manager input. No owned HY2 server is deployed yet, so source/AAR/client/default-off evidence must not be reported as a live handshake.
- `scripts/build_owned_hy2_server_bundle.py` builds the reviewed `infra/owned-hy2/` source twice from clean candidate.6 Core `a45d69e...` with Go `1.25.13`, requires byte-identical Linux/amd64 binaries, runs a same-source synthetic `sing-box check`, retains the GPL notice and emits a deterministic ZIP with no runtime material. `verify` checks the complete member/digest contract; `plan --operation install|rollback` emits sanitized, non-mutating ordered actions. The current local artifact is `pokrov-hy2-server-a45d69e.zip`, size `15232131`, SHA-256 `fe9f082f3ad7e7e2a45db8257fc1fec202c63fe0ce43e0b25fc4620c827bd93e`; its embedded ELF SHA-256 is `e877237c919cb7c0b12df1ccd6a358eb206dbeefe3516e9a7d421e199d352901`. An independent repeat is byte-identical. The prior `e8eb772...` artifact remains historical pre-candidate evidence only.
- `scripts/remote_install_owned_hy2_lab.py` is the guarded server-side executor. Without `--apply` it performs only strict-host-key/Brain/node readback and returns sanitized booleans. Install requires the exact bundle/source/node confirmations, an engaged Brain HY2 kill-switch and receipt-bound root-only runtime material. It rejects any existing target, UDP `443` collision, inactive UFW, mismatched config shape or placeholder, creates a root-only pre-mutation receipt, starts before enabling, and automatically restores the receipt on failure. Explicit rollback additionally binds the exact current release and receipt. Runtime passwords, keys, config and raw host never enter its report or CLI.
- The 2026-08-28 read-only `PLAN` against owned node `de` returned `mutation_performed=false`: UFW was active, UDP `443` was free, the HY2 service/unit/config/current/release targets were absent, and no HY2 firewall rule existed. Runtime material was absent and the deployed Brain did not yet expose the branch-only HY2 kill-switch field, so `APPLY` remains fail-closed. This is node readiness evidence, not deployment or handshake proof.
- The server bundle is packaged inactive. Runtime config, certificate key, password, obfs password and device identity must be materialized outside Git directly into owner-only server state. Installation must retain the previous pointer/config/unit/firewall receipt before mutation. Rollback engages the platform HY2 kill first, stops the exact service, proves the UDP listener absent, restores only the receipt-bound previous state and retains the failed release. Neither the bundle nor either PLAN authorizes deployment.
- `infra/owned-smart-dns/` is the separate default-off selective Smart DNS source lane. Its HTTPS `/dns-query` endpoint is non-recursive: only allowlisted AI/gaming-service `A` questions receive the owned proxy IPv4, alternate types return `NOERROR/NODATA`, and outside names return `REFUSED`. Other TLS ClientHello records are forwarded only when one visible SNI matches the same policy; TLS remains opaque and ECH/no-SNI/malformed input fails closed.
- The Smart DNS source parser explicitly rejects an `encrypted_client_hello` extension (`0xfe0d`), including an allowlisted outer SNI and ECH GREASE, before origin dialing. The inner application name is not available to this selective relay. A locally generated TLS 1.3 ECH regression proves source rejection; existing runtime/bundle receipts below do not prove deployment of this later parser change. DNS answer or visible-SNI TLS success still cannot prove authenticated service access.
- `scripts/check_smart_dns_policy_parity.py` requires the canonical platform policy and active client copy to be byte-identical after explicit UTF-8 CRLF-to-LF canonicalization; BOM, invalid UTF-8 and lone CR fail closed. `scripts/build_owned_smart_dns_server_bundle.py` applies the same canonical form, requires clean exact platform source plus Go `1.25.13`, runs host tests/vet, builds Linux/amd64 CGO-free bytes twice and emits a deterministic inactive bundle outside the repository. Runtime address, hostname, certificate, private key and upstream resolver coordinates are excluded. The current exact-source `ff7e653...` bundle is `2912449` bytes with SHA-256 `79cf040a6725cfb35f232242fefc8dfc61fd472448bb3d14b443a7472db0de8c`; an independent repeat is byte-identical and both copies pass self-verification. Earlier `2d18fd7...` and `8bdc21f...` artifacts remain historical evidence only.
- `scripts/remote_install_owned_smart_dns_lab.py` owns guarded server PLAN/APPLY/ROLLBACK. PLAN performs strict-host-key Brain/node resolution and returns only sanitized booleans. APPLY additionally requires exact bundle/source/node confirmations, a unique public IPv4 matching the root-only runtime config, an explicit dedicated-node confirmation, an explicit client-selection-disabled attestation and receipt-bound runtime material. It rejects any existing target, TCP `443` or firewall collision, inactive UFW, non-exact config limits/paths or placeholders; it creates a root-only pre-mutation receipt, starts and probes local TLS/DoH before opening UFW, enables last and automatically restores the receipt on failure. A retry after automatic rollback may reuse only the retained release directory and only after an explicit reuse confirmation plus full member-count, type, owner, mode, size and SHA-256 verification; root-only receipt step markers preserve the last completed phase. Rollback binds the exact receipt/current release, requires client selection disabled, proves the listener absent, restores only receipt-owned state and retains the failed immutable release. Neither PLAN nor this source authorizes APPLY.
- The current 2026-08-29 report-v3 no-mutation PLAN checked all seven active nodes (`de`, `us`, `ru`, `ru_spb`, `pl`, `it`, `nl`) against the exact current bundle. Its bounded helper parses structured `ip -j -4` values, filters globally routable IPv4 and classifies exact, wildcard and dual-stack `ss` binds without returning addresses or process names. `de` has two globally routable assigned IPv4 values and two exact TCP/443 binds; the other six nodes have wildcard/dual-stack TCP/443 binds. No active node has an unclaimed globally routable IPv4 outside its current bind scope. Runtime material was absent and every report returned `mutation_performed=false`. An intermediate v2 shell counter that suggested otherwise is `INVALID_INTERMEDIATE_NOT_RELEASE_EVIDENCE` and caused no mutation. Smart DNS must not be overlaid onto these frontends. Under the no-purchase policy, an address is eligible only after a separate guarded frontend migration/rollback proves it was deliberately freed; otherwise the lab stays undeployed. Explicit owner authorization remains mandatory before APPLY. Source, bundle, PLAN, package/device-state or future DNS-answer evidence is not by itself a live service-access, leak, gameplay, RU-origin or release proof.
- Post-candidate platform `06e4a4a...` adds a source-only no-purchase alternative without weakening that historical PLAN: Smart DNS may bind to an explicit loopback unprivileged port behind a reviewed owned HAProxy TCP/443 SNI frontend. That listener requires strict PROXY protocol v2 TCP/IPv4 or TCP/IPv6 with no TLVs and restores the original source before connection and DoH limits. The transport-front renderer can express validated exact/child SNI routes and `send-proxy-v2`, but default routes are unchanged and the current guarded Smart DNS installer still rejects fronted APPLY. No frontend is selected; Brain is not an automatic target. A separate receipt-bound frontend PLAN/APPLY/ROLLBACK, `haproxy -c`, backend health, exact-candidate bundle, runtime material and explicit owner authorization remain mandatory before any live use.
- Post-candidate platform `99d0715...` supplies that separate guarded frontend operation through `scripts/remote_migrate_owned_smart_dns_frontend.py`. Default PLAN reads only sanitized tool/service/listener/digest state and validates the candidate with remote `haproxy -c` without returning runtime config. APPLY requires exact current/candidate config and service digests, Smart DNS release, node, client-disabled and mutation confirmations; it retains a root-owned mode-`0700` non-symlink receipt, uses compare-and-swap before replacement, validates then signals HAProxy `USR2`, probes the local DoH path and automatically restores only a known base/candidate state on failure. Explicit rollback loads no install fixture or policy from the current checkout, reads the exact applied receipt, verifies the live backend release and accepts only the live receipt candidate. Failed automatic rollback returns the sanitized receipt ID and rollback status in both JSON evidence and stderr for recovery. The corrected all-seven PLAN completed `7/7` with `mutation_performed=false`: five nodes have no applicable owned frontend, while `ru` and `ru_spb` have an active valid frontend and valid candidate render but no active/fronted/loopback Smart DNS backend. Neither is selected, Brain remains excluded and SPB is never an automatic choice.
- Post-candidate platform `c2ffc48...` supplies the missing first-frontend bootstrap through `scripts/remote_bootstrap_owned_transport_front.py` and `infra/portal-transport-front.legacy-one-backend.cfg`. It preserves the exact direct Xray/Reality behavior as the HAProxy default route while moving one digest-bound x-ui inbound from wildcard TCP/443 to loopback TCP/10443 through one-row SQLite compare-and-swap. PLAN is read-only. APPLY requires exact node/inbound/config/unit/invariant confirmations, a dedicated authorization token and a root-only receipt before mutation; package ownership, listener owners, config validity and postflight are checked. Post-candidate corrections `9284ca8...` and `9dee549...` fix Paramiko exclusive-write staging plus bounded listener readiness and operation-owned rollback cleanup. On 2026-08-30 the corrected guarded `it` sequence passed frontend APPLY, current- and Brain-origin TCP/443, explicit receipt-bound rollback with direct Xray restoration, post-rollback reachability and guarded re-APPLY. The current canary state is HAProxy on public TCP/443, the exact legacy Xray/Reality default backend on loopback TCP/10443 and free loopback TCP/18443. Smart DNS remains uninstalled: runtime material, public DoH hostname, trusted certificate, DNS publication and live service-access proof are absent. A same-device Beeline whitelist differential passed carrier and allowed-RU controls while POKROV control/API and `ru_spb` TCP/443 timed out before VPN/TLS; this classifies the bounded carrier path, not AWG or general whitelist readiness, and direct `it` is not an emergency bootstrap for that condition.
- Post-candidate platform `650dc3f...` extends the guarded server installer with exact loopback `127.0.0.1:18443`, mandatory PROXY v2 and UFW-neutral fronted PLAN/APPLY/ROLLBACK. Two exact-source Linux/amd64 bundles are byte-identical at `2916305` bytes and SHA-256 `cda97da16a892c1a8563bd20434cd749a2174c192ba722147091a3e1c14a0225`. Fresh RU and RU-SPB PLANs prove root/tools readiness, a free loopback listener, absent service/runtime material and zero mutation. This is install readiness only; neither node is selected.
- `scripts/remote_prepare_owned_smart_dns_runtime.py` owns the separate certificate/runtime-material PLAN/APPLY step for the fronted listener. Its public `A` comparison is resolved from the authenticated Brain session, not the operator workstation's ambient resolver, then checked for exactly one global IPv4 matching the selected owned node. APPLY still requires the exact bundle/source/node, DNS-match and ACME mutation confirmations; the DNS-origin change does not weaken any guard.
- The 2026-08-31 owner-authorized `it` canary supersedes the earlier uninstalled-state sentence above. `dns.pokrov.space` resolves on all four delegated Timeweb nameservers to the selected owned node. The guarded runtime step issued a server-side trusted certificate and installed root-only material plus renewal support; the exact `650dc3f...` bundle is active only on loopback TCP/18443 behind HAProxy TCP/443 with mandatory PROXY v2, no public-firewall mutation and client selection disabled. A receipt-bound live drill removed the frontend route, rolled back the backend to inactive/free-listener state, reverified the retained immutable release, re-applied both layers and ended with a fresh rollback PLAN that matches the live config, service and release digests. Post-drill DoH and TLS/SNI probes pass from current, Brain and owned-RU origins for the bounded ChatGPT, Gemini and Xbox policy; outside-policy DNS remains `REFUSED`, alternate address types remain `NOERROR/NODATA`, and malformed DoH remains HTTP 400. Ordinary `it` health, edge reachability and dataplane remain green. This is current-runtime/default-off lab proof for bundle `cda97da...0225`, not candidate.16 client binding, authenticated application-session proof, broad leak/load proof, Store readiness or release authorization. Exact receipts and sanitized evidence are retained in `WO-013DG`.
- WO-013DP adds a background-only Android-origin slice without changing that boundary. LDPlayer reaches the same DoH endpoint over trusted TLS: an outside-policy control returns `REFUSED/0`, ChatGPT/Gemini/Xbox return `NOERROR/1` each and malformed DoH returns HTTP 400. The owner phone resolves the public hostname but has no non-UI DoH tool. POKROV is not launched, no VPN or device setting changes, no screen control is used and no answer address is retained. This is direct Android-emulator transport/policy proof, not candidate client integration, physical DoH, authenticated application access or Gate F credit.
- The current server resolves allowed application SNI through fixed authenticated DoT and then opens the resolved public IPv4 on TCP/443 directly from the service host. It has no outbound proxy or tunnel setting, so an RU deployment would retain RU application egress and is `NO_GO` for the intended DNS-only geo/access bypass. An isolated `x86_64` owner-terminal fixture proves strict PROXY-v2 rejection, DoH synthesis and verified TLS passthrough for bounded AI/gaming representatives with complete cleanup and no production mutation, but not service-session access. The preferred next topology is a colocated foreign owned HAProxy frontend plus loopback Smart DNS backend. A remote-backend or process-WARP design creates new trust/routing/rollback boundaries and is not an implicit fallback. Android system Private DNS also remains separate because this service exposes DoH, not a proved DoT listener.
- Only authenticated `GET /api/client/profile/managed` may return decrypted typed owner-lab endpoints. Token subscriptions, previews, Happ/Clash/manual exports, location choices and public UI force `legacy_reality_fallback` and never contain owned lab material.
- Owned AWG node activation is incomplete until UFW admits both declared UDP listeners. The guarded live ports are `4500/udp` for AWG2 and `3478/udp` for AWG3.1. Run `scripts/remote_ensure_owned_awg_firewall.py` without `--apply` first, then use `--apply --confirm-node de`; it fails if UFW is inactive. `scripts/remote_rebind_owned_awg_lab_ports.py` owns the guarded old-to-new listener/material migration. Socket/service readback alone is not ingress proof.
- A multi-address owned node must select the endpoint address before emitting either lab's UDP reply. Run `scripts/remote_ensure_owned_awg_reply_source.py` without `--apply` first and pass its exact node/address-digest guards to APPLY. The operator requires an unambiguous main default route and kernel UDP source-port rule support, rejects occupied policy slots, creates a root-only backup, and installs one dedicated policy table/rule plus a narrow final SNAT for each owned lab source port. `--cycle-services` additionally proves the persisted `PostUp`/`PostDown` state. Late SNAT without the policy route is not a supported steady state because it cannot repair an already selected source route.
- Use `scripts/remote_audit_owned_awg_alignment.py` for v2 key, peer, address, S/H, header-protection, content-padding and randomized-trailer alignment; `scripts/remote_probe_owned_awg_udp_path.py` for fixed-size non-secret one-way probes; `scripts/remote_count_owned_awg_packets.py` for address-free direction and tunnel counts; and `scripts/remote_run_owned_awg_core_interop.py` for exact-Core handshakes. The interop script requires the expected Core commit in both local and RU modes, verifies the selected repository root and tracked module, and exports `engine/sing-box` from that commit into a private temporary snapshot. Mutable tracked, untracked and ignored worktree bytes are never consumed as build input; the exact-commit archive excludes them. Every Git invocation disables repository-local filesystem monitors and hooks while inherited and global/system Git configuration is excluded. The script rejects local replacements outside the snapshot, verifies the module cache, disables ambient Go workspace/toolchain/network selection, and builds the digest-bound test binary before decrypting AWG material. Only that already-built binary receives the material; Git and Go do not. A PASS additionally requires the exact test to be registered and verbose proof that `TestOwnedAWGLabAuthenticatedEgress` ran and passed; a zero exit with no matching test or a skipped test fails closed. Git and Go paths must be explicit and absolute, and their before/after SHA-256 identities are retained. The script can cross-build the same confirmed snapshot as Linux ARM64 and execute it on an explicitly confirmed owned Raspberry Pi SSH alias. That path additionally requires explicit absolute SSH/SCP executable paths and records their identities, binds SCP to the selected SSH program, uses strict host-key input, a caller-supplied non-system temp root, Pi 4/aarch64 plus direct-default-route preflight, digest-verified binary transfer, endpoint material over SSH stdin only, and exact `/tmp/pokrov-awg-ru-pi-<uuid>` cleanup. It returns Core/tool/binary/material digests, closed outcome fields and the bounded per-MTU measurements described below; no key, endpoint, raw host, test output or temporary path is retained. The counter and Core interop entrypoints accept optional `--json-out` paths so secret-free evidence can be retained without shell redirection. AWG3.1 randomized trailers make fixed-size handshake classification inapplicable, so direction counts and live handshake state are authoritative for that variant.

  The interop v4 receipt requires all three client-MTU subtests (1280/1400/1408) plus nonzero bidirectional packet observations. Each uses a TLS-authenticated request with 4096 bytes of inert header padding. A missing/skipped case or duplicate measurement fails the matrix even if the parent test exits zero. Only per-MTU packet counts, maximum UDP payload lengths and elapsed milliseconds are added to the safe receipt. Each case has a 45-second deadline; the three-case binary is bounded at 150 seconds. The server MTU and endpoint material are unchanged. Packet maxima from this short request do not prove sustained throughput, full MTU-path coverage, absence of leaks or preset quality; prior v3 smoke receipts remain historical single-configuration evidence.
- `scripts/remote_set_owned_awg_mtu.py` changes both owned lab server interfaces and both device-bound materials only between the allowlisted MTU values after PLAN, exact node/MTU confirmation, root-only backup, service restart and server/material readback. The current mobile-safe value is `1280`; a generated endpoint must use the same value.
- `scripts/remote_set_owned_awg31_variant.py` applies only the reviewed `randomized_trailers_mobile_safe_v2` server drop-in and matching encrypted material after backup and exact readback. It retains header protection and randomized handshake trailers but explicitly sets data-packet content padding to `0`: the physical Beeline path accepted the 1280-byte inner ceiling while the former `64-512` addition black-holed TLS records. It does not promote AWG3.1 outside the owner-only lab.
- `scripts/remote_probe_owned_awg_udp_roundtrip.py --apply` temporarily stops exactly one confirmed lab service, runs a bounded plain-UDP echo on its owned port and restores/readbacks the service in `finally`. It can compare normal route selection, ingress-address `IP_PKTINFO`, temporary narrow SNAT and temporary source-port policy routing; every temporary rule/table must be removed before `execution_safe=true`. A roundtrip is `PASS` only when the server received every probe, the selected source received a valid echo and the service was restored. Server receive plus missing reverse echo is a network-path failure, never `ok=true`.
- `scripts/remote_select_owned_awg_lab.py` selects or removes the exact rooted Android test install from the owner-only cohort after install-identity digest confirmation. PLAN is non-mutating; APPLY must be followed by the matching `default` cleanup. `--json-out` atomically retains the sanitized selection/readback and never writes the raw install ID.
- `scripts/remote_bind_owned_awg_lab_device.py` requires a confirmed device-label digest and normally ranks matching active devices by freshness. Run PLAN immediately before APPLY and compare only its sanitized `last_seen_age_seconds` plus OS/locale/time-zone digests; raw device identifiers are never returned. For a root-capable emulator, pass `--adb` and `--adb-serial` together with the locally computed `--confirm-target-install-sha256`: the binder reads the exact app-first install identity locally, verifies its digest, sends the raw value only through SSH stdin and selects that install even when Brain has no fresh `AccountDevice` card. Any supplied target-install confirmation is checked during PLAN; APPLY always requires it and Brain checks it before decrypting material or mutating state. Precondition failures return a nonzero status plus a structured blocker containing only counts, booleans and permitted digests. A stale legacy install-user may resolve to the runtime owner only when the selector is exact-local or exactly one device matches the confirmed label, the install-user is globally unique, `ADMIN_ID` resolves to exactly one active entitled user and the direct account component has zero entitled users; every ambiguous case fails closed. For an owned root-capable emulator whose exact install-user is inactive, `--extend-target-entitlement-days 1` is the only permitted entitlement mutation: it requires the exact local ADB selector, the confirmed install digest, a matching active device/account owner, a non-default AWG lab profile and guarded `user.extend` readback. It never transfers the runtime owner's entitlement and accepts no duration other than one day. Cleanup removes both the delivery-owner and stale legacy target identities. AWG3.1 readiness is checked against the current rollout policy and the existing exact-device material; the binder no longer reprovisions a key or rewrites its generation, endpoint revision, server record or age during selection. Set `--carrier-context none` for Wi-Fi/emulator policy readback or `beeline` for that cellular context. `--json-out` atomically retains the sanitized PLAN/APPLY readback without shell redirection. A successful binder readback proves control-plane selection, not client profile fetch, Core activation or tunnel traffic.

  The binder is an isolated-install tool, not a shared-rollout editor. Before
  any guarded entitlement/material/configuration write, APPLY rejects other
  allowed installs, all account-wide selectors, other AWG cohorts, and AWG
  defaults/carrier rules with `shared_awg_scope_requires_separate_review`.
  New cohort and lab allowlists contain only the confirmed install, never its
  whole account. Legacy account-based lab scopes need separate operator review;
  the binder must not silently convert or erase them. PLAN still proves target
  readiness only and does not inspect this APPLY precondition. The rollout
  configuration is reread before its write; drift stops the bind. A drift stop
  may follow already-completed material/entitlement writes and requires review,
  not a claim of atomic rollback. Serialize operator changes during a bind;
  this check is not a server-side compare-and-swap. No live APPLY is authorized
  by these local safeguards or by a successful test.
  Successful lab readback likewise requires exactly the confirmed install in
  both selectors and no account/platform-wide selector; it must not require
  the removed account allowlist. Server selection alone is not a client
  connection PASS. Recompute the installation digest from the actual test
  machine after reinstall instead of reusing a previous plan's target.
- After the client connects, run `scripts/inspect_android_runtime_profile.py` with the exact ADB serial and `--expected-profile`. It accepts only an Android application-ID package and rejects dot segments and unsafe device-path characters. A single root-side shell operation opens each preferences/config target once, validates the canonical path and regular-file type through that same file descriptor, and reads the bounded bytes from the same descriptor; the preferences target must be exact and the config must remain strictly below a non-symlinked `files/pokrov-runtime/` directory. Preferences, config and ADB stderr are byte-bounded before buffering; containment and overflow failures do not retry. The script returns only a normalized profile class, type counts and secret-presence booleans. A non-matching cached default/AWG profile exits nonzero. This readback is required before counting a lab connection as AWG2 or AWG3.1; it still does not replace TUN, egress and server-handshake evidence.
- On `2026-08-28`, live alignment v2 passed for AWG2 and randomized-trailer AWG3.1. Physical build `1.2.0+4044` reached both listeners from Beeline, but each guarded UDP roundtrip had server receive/echo `3/3` and phone receive `0/3`. Record this as `BLOCKED_BY_NETWORK_CURRENT_ORIGIN`: reverse UDP is dropped on that path. A later no-carrier readback selected AWG2 for the exact physical and LDPlayer devices, but build 4044 on Wi-Fi and build 4043 on LDPlayer emitted no AWG traffic; the emulator also rejected the selected Frankfurt location. Record this second boundary as `FAIL_WORKING_CLIENT_ACTIVATION`, before cryptography. Direct cellular DoH separately returned valid responses for all three bounded AI/Games queries, while normal WARP plus IP and DNS egress passed after exact lab unbind. The retained [physical pre-candidate evidence](../audit-artifacts/2026-08-28-owned-awg-dns-physical-pre-candidate.md) does not create a release candidate or clear the final Android matrix.
- On `2026-08-29`, bounded route/ingress/SNAT/policy probes isolated that reverse failure to source routing on the multi-address `de` node. The guarded policy correction and service-cycle readback passed. Production-signed replacement Android `1.2.0+4046` then completed fresh authenticated AWG2 and randomized-trailer AWG 3.1 handshakes plus bidirectional inner traffic on physical Beeline; exact Core interop passed both profiles again after the service cycle. Record this as `PASS_PHYSICAL_PRE_CANDIDATE`, not candidate proof: candidate.5 remains immutable/rejected, and a new digest-bound candidate, exact-candidate repeat, Windows parity and DNS/leak/origin gates remain open. The exact device was rebound to `default`, lab material read back absent, Wi-Fi was restored and no raw device/address/key material was retained.
- On `2026-08-29`, exact signed candidate.7 physical follow-up separated the remaining failure into path-MTU and AWG3.1 packet-growth causes. Both live interfaces and encrypted materials moved from `1408` to `1280` through guarded PLAN/APPLY. AWG2 then passed the app's tunnel, DNS and authenticated-egress checks. AWG3.1 retained official pinned cryptography, header protection and randomized trailers but moved from `64-512` content padding to `0`; exact Core interop, TCP, TLS, authenticated HTTP `204` marker and the app's own tunnel/DNS/egress checks then passed on Beeline. One fail-first variant APPLY rolled back because zero-valued UAPI output is omitted; the readback now treats absence as zero only when the persisted explicit reset and all other variant checks pass. Final alignment and reply-policy persistence passed, and guarded cleanup restored `default`, removed both lab materials and left no phone TUN. Candidate.7's original Gate F remains immutable and the changed platform/client source requires a successor candidate before promotion.
- On `2026-08-31`, exact signed candidate.14 x86_64 installs and launches on LDPlayer and the ordinary `default` profile passes Android VPN service, tunnel, managed DNS and authenticated egress. Guarded AWG3.1 and AWG2 control-plane selection/material provisioning also pass, but `inspect_android_runtime_profile.py` consistently reads cached `default`, including after normal reconnect and the user-facing repair flow. Record both lab outcomes as `FAIL_MANAGED_PROFILE_ACTIVATION_CACHED_DEFAULT`, above protocol execution; do not transfer candidate.13's successful emulator result or claim a candidate.14 protocol result. Guarded cleanup restores `default`, removes lab cohort/material, disconnects the app and leaves no VPN service/TUN. The one-day exact-install entitlement extension remains an explicit test mutation. Physical Android and isolated Windows remain `MANUAL_OWNER_TEST`.
- app-managed session and profile delivery should use the rollout-selected transport profile, while manual/export compatibility links stay on `legacy_reality_fallback` until the share-link parity wave lands
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint; `subscription_url` stays manual/import fallback only
- capacity-aware app routing uses `GET /api/client/nodes/candidates`, `POST /api/client/nodes/select`, and optional `selected_node_code` on `GET /api/client/profile/managed`; `POST /api/client/nodes/latency-samples` remains compatibility telemetry
- subscription rendering dynamically orders nodes while `SUBSCRIPTION_DYNAMIC_ORDERING=true`; `SUBSCRIPTION_EXCLUDE_HARD_REJECT=true` is the fail-closed default, so explicitly hard-rejected nodes are not rendered into paid/trial subscriptions. Low `health_score` alone remains a ranking penalty, not a hard rejection. `false` is an explicit rollback-only override and must not be used as a healthy production steady state
- observer-lite deployments whose Xray access log emits naive timestamps must set `PORTAL_OBSERVER_SOURCE_TIMEZONE` (or pass `--source-timezone`) to `UTC`, `Z`, or a strict fixed offset such as `+03:00` or `-04:00`; IANA names, absent settings, and invalid or out-of-bounds offsets make each affected line a counted parse error and no observation is sent for that line
- offset-aware observer timestamps are converted to canonical UTC `Z` before batching; the collector never interprets a naive timestamp as server-local time or UTC implicitly
- core rollout/rollback flags are `CAPACITY_AWARE_NODE_SELECTION`, `AUTHENTICATED_EGRESS_ENFORCEMENT_ENABLED`, `SUBSCRIPTION_DYNAMIC_ORDERING`, `SUBSCRIPTION_EXCLUDE_HARD_REJECT`, `KEY_PRESSURE_SCORING`, `KEY_PRESSURE_FAIR_USE_ROUTING`, `APP_NODES_SELECT_ENDPOINT`, `XRAY_METRICS_COLLECTOR`, `NODE_AGENT_METRICS`, and `USERNODE_MAPPING_AS_CANDIDATE_LIMIT`
- as of `2026-06-29`, rolling maintenance updated non-current delivery nodes `free`, `it`, `nl`, `pl`, and `us` to 3x-ui `3.4.1` with bundled Xray `26.6.22`; each node has a root-only backup under `/root/pokrov-xui-backups/*-v3.4.1`, while `de` was intentionally left untouched because it was the operator's active connection node during the rollout
- 3x-ui `3.x` requires CSRF for session-authenticated unsafe panel API requests; `PanelClient` must fetch `/csrf-token`, send `X-CSRF-Token` on panel POSTs, and keep an unsafe cookie jar for IP-based panel hosts such as `de`
- when backfilling many existing users into one 3x-ui inbound, create clients sequentially and verify the panel client count against `user_nodes`; concurrent `addClient` calls mutate the same inbound settings document and can leave database mappings ahead of actual panel clients

Rollout order:

1. Wave 0, code-first
   - migrate `nodes.transport_profiles_json`
   - backfill `legacy_reality_fallback` from the legacy node fields
   - seed `reserve_xhttp_cdn` metadata on eligible nodes without enabling it for public cohorts
   - ship backend changes for multi-inbound sync and `network_rollout_config`
   - expose rollout config and node transport health in admin/web surfaces
   - update the canonical docs in this task
2. Wave 1, deploy-first
   - run local tests and smokes
   - run `release_orchestrator.py --gates-only`
   - deploy the brain portal code
   - deploy static sites if the admin surface or public visibility changed
   - run `verify_brain_ready.py`
3. Wave 2, infra canary
   - choose one premium node as the canary
   - install the node-local transport front on public `:443` with `scripts/remote_apply_transport_front.py`
   - move the live `legacy_reality_fallback` listener behind the transport front on a loopback backend port
   - add the `grpc_443_primary` inbound on its loopback backend port behind the same transport front
   - prepare the reserve backend `reserve_xhttp_cdn` on its loopback port and SNI mapping, but keep the rollout flag disabled unless the explicit reserve test is requested
   - seed the node transport catalog with `legacy_reality_fallback`, `grpc_443_primary`, and reserve metadata
   - run `scripts/remote_transport_front_smoke.py` against the canary SNI names before cohort enablement
   - apply the qdisc profile and run the saturation smoke
   - enable `grpc_443_primary` only for a small RU-risk allowlist through `network_rollout_config`
4. Wave 3, fleet expansion
   - repeat inbound and qdisc rollout on the remaining premium nodes
   - move failover by `subnet`, then by `hoster_family`, then by country
   - after parity, switch `defaults.transport_profile` to `grpc_443_primary` for the RU-risk cohort
5. Wave 4, operator lab
   - add `operator_lab` on one controlled node only
   - open it through allowlist entries only
   - keep it out of public UI and non-operator payloads

Rollback shape:

- restore `defaults.transport_profile` to `legacy_reality_fallback`
- set `operator_lab.enabled=false`
- set `awg2_lab.kill_switch_engaged=true` (or `enabled=false`); policy then falls back before profile issuance while encrypted material remains retained for audit/rotation
- run `scripts/remote_apply_node_qdisc.py rollback`
- keep `nodes.transport_profiles_json` in place as dormant metadata instead of deleting it

Reserve-path rule:

- `reserve_xhttp_cdn` is prepared for operator-directed fallback only
- current reserve SNI is `cdn.connect.pokrov.space`
- the current transport-front template maps that reserve SNI to the loopback reserve backend
- when the reserve profile is selected, the client uses `transport_kind=xhttp` and `engine_hint=xray`; this does not change the default public `sing-box` path

Node shaping repo truth:

- `infra/node-qdisc-profiles.json` records `node_code`, `iface`, `uplink_mbps`, `target_rate_mbps`, and `preferred_qdisc`
- `target_rate_mbps` is fixed at `85%` of the confirmed sustainable uplink for each live node
- `scripts/remote_apply_node_qdisc.py` supports `install`, `apply`, `show`, `disable`, `rollback`, and `uninstall`
- `install` and `disable` control reboot persistence through `infra/portal-node-qdisc.service`; `rollback` removes the active qdisc without deleting the repo-truth profile
- node selection must come from explicit `NODE_CODE` provisioning or the built-in alias normalization such as `PLnode -> pl` and `FREENLnode -> free`
- if `sch_cake` is present, the script applies `CAKE nat triple-isolate`
- if `sch_cake` is unavailable, the script falls back to `fq_codel` and must report that fallback explicitly
- `scripts/remote_node_qdisc_smoke.py` runs one heavy egress flow plus parallel small HTTPS probes, records p95 latency / TTFB, and fails the gate if the heavy flow never materializes or starvation exceeds the configured thresholds
- `infra/portal-node-qdisc.service` restores the configured qdisc after reboot

### Owned AWG peer revocation worker

`portal_bot/awg_lab_peer_worker.py` runs inside the existing worker when
`AWG_LAB_PEER_TARGETS_FILE` names a JSON target file. Empty configuration leaves
this job disabled. Configure only the owned AWG2/AWG3.1 lab interfaces whose
current node/server-record and SSH host identities have been verified. This
does not enable public AWG or provision new client keys.

The root-owned target file contains a list with these fields for each interface:

```json
[
  {
    "profile": "awg2_lab",
    "node_code": "de",
    "server_record_id": "de-awg2-20260827-01",
    "host": "owned-awg.example.test",
    "port": 22,
    "username": "root",
    "key_file": "/run/secrets/owned-awg-ssh",
    "known_hosts": "/run/secrets/owned-awg-known-hosts",
    "interface": "pokrovawg2",
    "server_public_key_sha256": "REPLACE_WITH_VERIFIED_64_HEX_DIGEST"
  }
]
```

The digest is SHA-256 of the decoded server public-key bytes, not its Base64
text. SSH uses the supplied key and known-host file with TOFU disabled. The
server helper also verifies that digest against the current interface before
any change. Runtime configuration, key files and real peer material stay out
of Git and evidence. The remote interface configuration must be at
`/etc/amnezia/amneziawg/<interface>.conf`; `/usr/local/bin/awg` and Python 3
are required on that owned node.

Each pass commits device/account/entitlement or material-age revocation before
the SSH operation. It then removes the exact client public key from the saved
configuration and the live interface, and verifies both. The next pass starts
30 seconds after the previous pass. Failed server delivery remains pending in
retained revoked rows and is retried; it is not a successful server revoke.
Repeated successful removal is idempotent. Source code does not recreate peers.

The helper serializes configuration edits with an interface lock, keeps a
root-only preimage under `/etc/amnezia/amneziawg/.pokrov-revocations/`, and writes
the new configuration atomically before the live removal. After a failed live
operation, restoring the revoked key to the boot configuration is not automatic.
Unrelated peer sections remain byte-for-byte. A rotated key without an active
copy is sealed as revoked, retaining its encrypted material and earlier timestamp.
Historical keys shared by multiple device bindings are counted as blocked and
require explicit per-device migration before selective removal. The worker
reports only counts and stable error codes, never keys or raw device identity.

When the AWG job is configured, the worker entrypoint attaches an INFO stream
handler to `awg_lab_peer_worker` only. Systemd retains its aggregate activity
reports in the worker journal; unrelated logger levels stay unchanged. A
running process with a target file is not proof of periodic reconciliation:
retain the actual reports and the corresponding peer readback.

This is the source contract. Activation on a particular runtime requires its
deployment/readback evidence; an empty or missing target configuration cannot
be counted as effective revocation enforcement.

## Current POKROV-app Local Build Matrix

Canonical repo-local build and packaging commands for this wave:

- `python scripts/run_client_release_gate.py preflight`
- `python scripts/run_client_release_gate.py test --suite portal`
- `python scripts/run_client_release_gate.py test --suite full`
- `python scripts/run_client_release_gate.py build --target windows`
- `python scripts/run_client_release_gate.py build --target android-apk`
- `python scripts/run_client_release_gate.py build --target android-aab`
- `dart pub global run msix:create --build-windows false`

Current local-build notes:

- Android outside-store public beta is owner-attested for the `2026-05-15` launch decision; raw `python scripts/android_localhost_audit.py` evidence on a release-installed physical build remains required before stronger Android safety, store, or stable claims
- the platform-owned `run_client_release_gate.py` wrapper now targets `C:/Users/kiwun/Documents/ai/POKROV-app` by default; it validates the clean-room seed workspace, runs the `POKROV-app` test lane, and produces `POKROV-app` Android or Windows engineering artifacts
- raw Android wrapper artifacts are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/...`; their presence alone does not prove production signing or publication readiness
- local Android builds may fall back to the debug keystore when the production release keystore is unavailable; that is valid for local smoke only, not for publication
- production Android signing still requires the local `android/key.properties` path or equivalent secret injection outside git
- raw Windows wrapper outputs are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/windows/x64/runner/Release/...`
- the wrapper-driven Windows setup EXE, portable ZIP, and manifest are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/windows_shell/build/release_bundle/`
- after the final green rerun, store the active client-lane bundle under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`, write the matching `release-handoff.json` plus any compatibility `release-links.env` there, and clean raw `build/` and `dist/` outputs as disposable local artifacts
- Android validation evidence hygiene is stricter: retain formal evidence in `ops-local/android-localhost-audit*.json` and in any intentionally promoted records under `docs/audit-artifacts/`
- repo-local Android screenshots, UI XML dumps, logcat captures, and ad hoc runtime snapshots created during one validation pass are disposable scratch unless they are intentionally promoted into `docs/audit-artifacts/`
- machine-local Android tooling noise such as `C:\Windows\adb.exe`, `%TEMP%`, SDK install directories, and `~/.android` is outside repo cleanup scope and must not be treated as repo evidence or repo cleanup targets
- the repo-local MSIX smoke path is intentionally unsigned by default through `sign_msix: false`; signing still belongs to the release handoff
- public Windows and Android labels, Windows package identity, executable naming, installer names, and protocol activation must read as `POKROV` / `pokrov`
- explicit legacy compatibility handlers such as hidden Android import continuity may remain only where separately documented and not as the Windows packaged identity truth
- retained bridge bundle notes belong in the mirrored archive README under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`

Current brand-source rule for release assets:

- start raster regeneration from [external/logogo.png](C:/Users/kiwun/Documents/ai/VPN/external/logogo.png)
- start vector regeneration from [logo/logoclear.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logoclear.svg) and [logo/logowithtext.svg](C:/Users/kiwun/Documents/ai/VPN/logo/logowithtext.svg)
- do not ship stale derived launcher, splash, tray, favicon, or share-preview assets after those masters change

## Current Unclosed Release Blockers

As of `2026-05-15`, the outside-store Android + Windows public beta has a retained `GO` evidence pack. The documented green beta snapshot is not the same thing as a stable, store, trusted-signing, RU-origin, or raw-device release handoff.

Still required before a stronger public promotion, new exact release candidate, store/trusted release, or node enablement that depends on new node state:

- live deploy of the released backend and static surfaces
- live node enablement where the rollout depends on new node state
- separate `current-origin check`, `brain-origin check`, and `RU-origin check` evidence lines
- Android production signing instead of debug-keystore fallback
- confirmation that the final signed Android artifacts are actually production-ready
- raw physical-device `python scripts/android_localhost_audit.py` on the release-installed Android build if replacing the current beta owner attestation or making stronger Android claims
- live Windows and Android scenario evidence on real devices and in a real network after the current UI pass
- live transactional sender readiness for public email registration or recovery mail must stay green; as of `2026-05-15`, a real verify-email delivery and public email registration flow were confirmed for beta, but reset and paid-key delivery should still be checked before broad launch language
- final release handoff with published URLs, runtime sync, and redeployed static download surfaces for any new artifact or URL change

Current procedure links:

- Android signing: [android-production-signing-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- Android physical-device audit: [android-physical-device-audit-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- artifact creation and candidate verification: [publishing-and-signing-guide.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)
- runtime URL sync: `Active Client Release Path` in this document
- RU-origin evidence: [ru-origin-probe-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)

Retained email-delivery and prior release-link evidence remains available in
[email-delivery-webhook-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/email-delivery-webhook-handoff.md)
and
[release-links-and-final-handoff.md](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md),
but neither dated file is the current procedure authority.

## Release Rule

For release-oriented work, default completion includes:

- code or config change
- tests or smoke checks
- push
- deploy

If deploy is blocked, record:

- what changed
- what was verified
- what remains blocked
- rollback-safe state

## Paid Beta Deploy And Rollback Checklist

Before any paid beta deploy, capture:

- local platform branch, local HEAD, `origin/master` HEAD, and whether the branch is behind the promoted platform line
- if a client artifact or handoff is part of the deploy, local client branch, local HEAD, `origin/main` HEAD, and the exact `POKROV-app` release metadata path
- exact dirty patch state for any local dirty beta candidate, including generated report path and changed-file list
- selected gate scope: full or quick, client platform build gates included or not included, Android physical audit included or blocked, and payment callback suite status
- production database backup proof before migrations or data-shaping changes, plus the restore or rollback confidence level
- deployed version or commit before change, new version or commit after change, static artifact identifiers, and release-handoff file or env source if used
- emergency switch evidence for checkout disable, trial disable, download disable, Telegram bonus pause, payment webhook fulfillment pause, and manual access extension/revoke
- current deployed runtime state for `portal-api`, `portal-bot`, `portal-helpbot`, `portal-feedbackbot`, `caddy`, `x-ui`, metrics timers, and observer timers when they are in scope
- current `portal-daily-healthcheck.timer` state and the latest `/root/portal_bot/health_reports/panel_node_health_*.json` result when panel/node drift is in scope

Rollback is acceptable only when the handoff states:

- backend rollback command or previous deployed commit/package path
- static rollback source, including the preserved static backup directory when static surfaces changed
- release-handoff rollback source for `APP_*` download URLs when artifact links changed
- node rollout rollback path, including `remote_apply_node_qdisc.py disable` and `remote_apply_node_qdisc.py rollback` when qdisc was touched
- transport rollback path, including restoring `defaults.transport_profile=legacy_reality_fallback` and leaving dormant node catalog metadata intact
- database rollback position, restore source, or explicit no-migration/no-DB-change statement
- verification commands to rerun after rollback from `current-origin`, `brain-origin`, and RU-origin where access allows

If any live check is blocked by access, label it as `BLOCKED_BY_ACCESS` instead of implying a pass. If a check is intentionally skipped because it is outside the selected gate scope, label it as `NOT_REQUESTED` or `SKIPPED` and explain why it is still required before public or paid-beta signoff.

## Current Deploy Contour

The documented full release wrapper can currently chain:

- local gates
- optional `APP_*` runtime handoff sync
- backend deploy to `brain`
- static marketing and webapp deploy
- optional qdisc or observer rollout helpers
- brain-local readiness verification

Current contour rule:

- `scripts/release_orchestrator.py` does not publish Android or Windows binaries, does not create final signed artifacts, and does not by itself close the public release handoff
- `scripts/verify_brain_ready.py` is brain-local verification, not a replacement for separate `current-origin` or `RU-origin` evidence; use its optional `--json-out` path when a bounded secret-free release artifact is required
- `scripts/remote_brain_network_probe.py --live-enabled-nodes --json-out <artifact>` probes the configured port of each live enabled delivery row from Brain and returns only redacted node-code/status evidence. Its retained-inventory mode is diagnostic-only and cannot prove the current delivery pool.
- transport or node rollout helpers can support enablement, but they do not by themselves prove live node enablement unless the runtime pool and smoke evidence are also updated

Current product release scope:

- full public `v1`: `Android + Windows`
- `iOS` and `macOS`: readiness-only in this wave

## Post-Deploy Checks

At minimum, verify:

- backend health endpoint
- app-first `start-trial`
- support ticket creation
- canonical `connect.pokrov.space` subscription endpoint availability
- legacy `api.pokrov.space` subscription compatibility
- app node-candidate and node-select endpoints for an authenticated app session
- authenticated subscription preview endpoint for resolved format, node order, and excluded-node reasons without raw config leakage
- admin subscription preview endpoint for operator render-debug without raw token/config leakage
- admin node capacity and key pressure endpoints for operator visibility
- `GET /api/client/apps`
- `GET /api/payments/providers`
- checkout continuation from session or ticket
- Telegram linking / channel bonus path
- API-only lifecycle smoke for bonuses, checkout order creation, callback success, and post-payment dashboard state
- `portal-api`, `portal-bot`, and `portal-helpbot` service status
- `portal-feedbackbot` service status
- `portal-daily-healthcheck.timer` status and latest daily panel/node health report when checking control-plane/node drift
- `verify_brain_ready.py` should fail the repo-side handoff if any required control-plane unit is inactive, if required brain-local listeners on `443` or internal Caddy `8444` are missing, or if the built-in HTTP and subscription probes fail; this does not authorize public UFW exposure for `8444`
- public HTTPS checks for `pokrov.space`, `app.pokrov.space`, and `api.pokrov.space` should confirm that responses no longer advertise `Alt-Svc: h3=":8444"`; expected incident-recovery state is `Alt-Svc: clear` plus `200`/healthy status over standard HTTPS
- control-plane readback must separately require JSON from both
  `app.pokrov.space/api/health` and `api.pokrov.space/api/health`, plus an
  authenticated-path JSON error such as `401` from the app ingress. A `200`
  HTML webapp fallback on `/api/*` is a failed ingress check
- marketing and checkout probes should use route/function markers such as `Android + Windows`, `app.pokrov.space`, `checkout-shell`, `ключ доступа`, and canonical URLs, not old hero copy that can change without a deploy failure
- transport rollout verification on the canary node with `scripts/remote_apply_node_qdisc.py show`
- transport front verification with `scripts/remote_transport_front_smoke.py`
- `tc -s qdisc` on the shaped interface
- `scripts/remote_node_qdisc_smoke.py` results for heavy-flow saturation and small-probe latency
- when observer-lite is enabled on any node, `portal-node-observer.timer` freshness on that node plus `/api/admin/metrics/status` and `/api/admin/nodes/health` observer fields
- observer-lite promotion requires a manual exact-candidate proof that a retained Xray log timestamp and its configured source zone produce the expected UTC `Z` observation, trial activation at that UTC instant, and expiry exactly `5 days` later; also prove that a naive fixture with the setting removed is skipped and increments batch `parse_error_count`
- after any REALITY target rotation, verify the node inbound `dest/serverNames`, the `brain` `nodes.reality_sni` row, and `python scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104` in the same handoff
- predeploy DNS expectations come from the current `brain` node rows, with the retained archive inventory only as a fallback; a verified public `443` transport front may satisfy a different internal Xray listener port only when the service is active, its HAProxy config is valid, its exact loopback mapping is present, and HAProxy/Xray own the expected listeners

Release gate rule:

- full `release_gate_check.py` should stay green; by default that means the release `pytest` matrix, admin/auth regression, `client_security_smoke.py`, `python scripts/run_client_release_gate.py test --suite full`, `api_lifecycle_smoke.py`, link checks, marketing/webapp production builds, admin webapp smoke, browser E2E from `webapp/e2e/`, and `ui_visual_smoke.py`
- the release gate report must classify what the run actually proved: `current-origin check`, `brain-origin check`, `RU-origin check`, Android physical audit, runtime app-download smoke, and client platform builds must show `PASS`, `FAIL`, `BLOCKED_BY_ACCESS`, `SKIPPED`, or `NOT_REQUESTED` rather than relying on one global pass/fail line
- `python scripts/run_client_release_gate.py preflight` should be green before trusting any wrapper-driven client gate result; a missing or incomplete `POKROV-app` seed workspace is a release blocker even if other repo-local tests happen to pass
- marketing release readiness also requires `python scripts/check-links.py` and `python scripts/ui_visual_smoke.py` to stay green after every CTA, legal, SEO, or branding change
- `verify_brain_ready.py` should validate both the canonical connect host and the legacy API compatibility path before a release is considered healthy
- the default full backend deploy and verify contour should include `portal-feedbackbot`, not just `portal-api`, `portal-bot`, and `portal-helpbot`
- `client_security_smoke.py` is the static repo-level gate for default local-surface settings, routing preset groundwork, and known localhost control paths; it does not replace the Android release-build port and reachability audit
- set `ANDROID_AUDIT_SERIAL=<device-serial>` when running `release_gate_check.py` if you want the opt-in adb localhost audit folded into the same markdown report
- set `ANDROID_AUDIT_CONNECT_WAIT_SEC` and `ANDROID_AUDIT_DISCONNECT_WAIT_SEC` when the adb localhost audit needs non-default timing in the same report
- set `ANDROID_AUDIT_PACKAGE=space.pokrov.pokrov_android_shell` for the active Android shell unless a release candidate deliberately changes the package id
- when `TELEGRAM_INIT_DATA` is available, retain evidence through `python scripts/runtime_app_download_smoke.py --redact --check-providers --require-release-handoff`
- add `--client-platform-gates windows,android-apk,android-aab` or set `CLIENT_PLATFORM_GATES` when you want the same markdown report to include artifact-producing client builds
- the latest documented `release_orchestrator.py --gates-only` success is a local-only proof and does not replace live deploy, live node enablement, or three-origin network evidence
- Android outside-store beta currently relies on owner attestation; a trusted/stable/store Android release must also include a release-build localhost-listener audit covering proxy, DNS, command-server, and admin/control surfaces before connect, after connect, and after disconnect; green repo/static gates are necessary but not sufficient
- the Android release gate fails if an unauthenticated local SOCKS, HTTP proxy, Clash API, command, or similar admin surface remains reachable
- public client release validation must include routing preset smoke for `Full tunnel` and `All except RU`, plus DNS split and leak checks on Android and Windows
- `Blocked only` remains internal or compatibility-only until geo assets and DNS behavior are complete enough for honest public verification

Current local gate entrypoints:

```powershell
python scripts/release_gate_check.py
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab
python scripts/release_orchestrator.py --gates-only
```

Notes:

- `release_gate_check.py` is the canonical local report generator for the public-v1 gate set.
- `release_gate_check.py --quick` swaps the default full client Flutter suite for `python scripts/run_client_release_gate.py test --suite portal`.
- on Windows, `release_gate_check.py` injects a repo-local disposable `--basetemp` for its `python -m pytest ...` gates so a broken workstation-level `%TEMP%\\pytest-of-<user>\\pytest-current` symlink does not pollute the release handoff tail.
- `release_orchestrator.py --gates-only` is the one-command wrapper for the same gate pack, but it intentionally exits before release handoff sync, backend deploy, static deploy, and post-deploy verify.
- `release_orchestrator.py --stage backend|static|deploy|verify` is the preferred recovery path when a previous full run timed out after a known completed phase; `deploy` means backend plus static, with gates and verify skipped.
- `release_orchestrator.py` streams child output and emits quiet-step heartbeats; tune `--gate-timeout-sec`, `--backend-timeout-sec`, `--static-timeout-sec`, `--verify-timeout-sec`, or `--step-timeout-sec` when a release lane is expected to exceed the default timeout.
- latest verified local run: `python scripts/release_orchestrator.py --gates-only` exited `0` on `2026-04-13`; see `docs/audit-artifacts/release_gate_report.md` for the current local gate snapshot
- pass `--brain-ip 82.21.114.104` to either command when you also want `predeploy_node_readiness.py` folded into the same run.
- `--release-metadata-file` and `--release-env-file` cannot be combined with `--gates-only`; use the full `release_orchestrator.py` flow when you need runtime `APP_*` download URLs synced onto brain before deploy or verify.
- the full `release_orchestrator.py` flow uses the same default backend restart set as `remote_deploy_brain_portal_code.py`, including `portal-feedbackbot`
- `--brain-ip` is required for the full remote contour, including release handoff sync, backend deploy, post-deploy verify, observer-timer ensure, metrics-timer ensure, and qdisc rollout lanes
- without `ANDROID_AUDIT_SERIAL`, a green gate report does not replace the required on-device Android localhost audit
- emulator-backed adb audits are preflight only and do not clear public Android release
- when node reachability is part of a release handoff, report `current-origin`, `brain-origin`, and `RU-origin` results separately instead of collapsing them into one verdict

## Telegram OAuth / OIDC Runtime

`POKROV` now supports Telegram OAuth / OIDC for web login.

Runtime env on `brain` must include:

- `TELEGRAM_OAUTH_CLIENT_ID`
- `TELEGRAM_OAUTH_CLIENT_SECRET`
- `TELEGRAM_OAUTH_REDIRECT_URI`

Current canonical redirect URI:

- `https://app.pokrov.space/`

Current trusted origins in `BotFather` should include:

- `https://pokrov.space/`
- `https://app.pokrov.space/`
- `https://admin.pokrov.space/` when Operator Center OIDC is enabled; this is
  also the exact `ADMIN_OPERATOR_OIDC_REDIRECT_URI`.

Telegram bot profile and native `Similar bots` readiness live in [Telegram Bot Profile Growth](C:/Users/kiwun/Documents/ai/VPN/docs/operations/telegram-bot-profile-growth.md).

Current official public surfaces:

- marketing and public site: `https://pokrov.space/`
- user cabinet and web login: `https://app.pokrov.space/`
- public API host: `https://api.pokrov.space/`

Hostname role policy:

- `pokrov.space` is the canonical public hostname family
- `kiwunaka.space` remains compatibility-only for migration and older subscriptions
- support, onboarding, release notes, and new links must always prefer `pokrov.space`

Web runtime rule:

- `https://api.pokrov.space/` remains the canonical dedicated public API host
- `https://app.pokrov.space/api/*` is the owned same-origin client fallback and
  must proxy to the API before the webapp static fallback; an API path that
  returns HTML is a deployment failure, while non-API paths still serve the UI

Migration-only legacy note:

- `kiwunaka.space` hosts remain compatibility surfaces for older subscriptions during cutover
- do not use `kiwunaka.space` in new release copy, onboarding copy, or fresh distribution links

Monitoring note:

- the external RU probe runbook, hostname migration visibility, and device/session visibility rules live in [Monitoring And Visibility](C:/Users/kiwun/Documents/ai/VPN/docs/operations/monitoring-and-visibility.md)

Safe deploy note:

- use local env injection for the client secret
- do not write raw OAuth secrets into docs, commits, or terminal summaries

## Retained Bridge Bundle Archive

Retained archive home:

- `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`

Development-truth note:

- this section describes retained bridge evidence only
- new client development truth is `POKROV-app/main`
- retired bootstrap provenance now lives in `docs/archive/client-lanes/app-next-bootstrap-summary.md`

Important outputs:

- versioned bridge bundle mirrors and checksums under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`
- release metadata preserved with that same versioned bundle when rollback-safe evidence matters

Do not delete release artifacts if they are still being distributed or verified.

Related guide:

- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)

## Active Client Release Path

Default release slug in this repo:

- `pokrov`

Current release boundary:

- public distribution is the public GitHub stable-direct handoff through the
  current cabinet/runtime contract
- retained distributed release: `v1.1.6`; public client package/build line
  `1.1.6+29`
- private candidates.20 through .22 remain immutable `NO_GO` history. The
  candidate.20 and .21 package lines are `1.2.0+4049` and `1.2.0+4050`; their
  bounded evidence is not current release authority
- working source target: `1.2.0+4053`, `PRE_CANDIDATE_LOCAL`,
  `candidate_created=false`; the seed is not deployable release metadata
- exact platform `5ba4dba...`, client `df9ed85...` and Core `cd8f0f4...`
  define local private `pokrov-1.2.0-candidate.23` at `1.2.0+4052`. Six
  artifacts, strict-v2 handoff, refreshed SBOM/provenance and signed
  release-index manifest/signature/receipt validate. The exact Windows package
  installs and initially connects, but valid requests can fail under
  serial-pipe contention while the service remains running. Candidate.23 is
  immutable `NO_GO`; the current build-4053 working branch contains the bounded
  retry, but no successor candidate exists yet
- no runtime sync, tag, public asset, Store object or stable pointer exists;
  `promotion_authorized=false`
- stable-direct publication does not prove store availability, trusted Windows
  signing, exact-final Huawei/RU-LTE evidence or Apple readiness
- artifact creation, signing, and candidate publication are owned by [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md); this guide owns runtime application and deploy access
- retained public/development version truth is owned by the client
  `config/release-handoff.seed.json`; runtime receives only a validated handoff

Default artifact names:

- `pokrov-android-arm64-v8a.apk` = default Android APK
- `pokrov-android-armeabi-v7a.apk` = legacy ARMv7 APK
- `pokrov-android-market.aab` = market handoff only; no store availability claim
- `pokrov-windows-setup-x64.exe`
- `pokrov-windows-setup-x64.msix`
- `pokrov-windows-portable-x64.zip`

Current public download surfaces expose only:

- Android default ARM64 APK plus the explicitly labeled legacy ARMv7 variant
- Windows `EXE`
- install/docs fallback via `APP_DOCS_URL`

Treat `AAB`, `MSIX`, and portable `ZIP` as market/operator artifacts unless a later runtime payload and public surface explicitly expose them. Their existence does not prove store availability.

Canonical local client verification commands:

```powershell
python scripts/run_client_release_gate.py preflight
python scripts/run_client_release_gate.py test --suite portal
python scripts/run_client_release_gate.py test --suite full
python scripts/run_client_release_gate.py build --target windows
python scripts/run_client_release_gate.py build --target android-apk
python scripts/run_client_release_gate.py build --target android-aab
```

Client verification notes:

- `run_client_release_gate.py` is the canonical root-level wrapper for the platform-owned client gate lane and targets `C:/Users/kiwun/Documents/ai/POKROV-app` automatically.
- `python scripts/run_client_release_gate.py preflight` is the fastest repo-local proof that the `POKROV-app` seed workspace, host shells, and wrapper scripts are present before client gates run.
- `python scripts/run_client_release_gate.py test --suite full` delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/run-tests.ps1`, while `--suite portal` runs the narrower Flutter lane in `packages/app_shell`, `apps/android_shell`, and `apps/windows_shell`.
- `python scripts/run_client_release_gate.py build --target windows` delegates to `C:/Users/kiwun/Documents/ai/POKROV-app/scripts/build-windows-release.ps1 -SyncRuntime -SkipTests -SkipAnalyze` and expects the unsigned setup EXE, portable ZIP, and manifest under `apps/windows_shell/build/release_bundle/`.
- `python scripts/run_client_release_gate.py build --target android-apk` and `--target android-aab` now build the `POKROV-app` Android shell and verify the raw outputs under `apps/android_shell/build/app/outputs/...`; they no longer refresh any retired bridge working-set paths.
- after those commands succeed, write the active client-lane bundle into `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`, keep the client-owned `release-handoff.json` beside it, and only then hand alpha/beta builds to testers.
- if `preflight` fails, inspect the `POKROV-app` seed workspace first; that fix belongs in the canonical client repo instead of as an ad hoc root-repo override.
- any direct commands against retired bridge material are archive or rollback exceptions only; the wrapper commands above are the release-workflow truth documented for operators and CI.

Signed release path:

- Android signing requires `ANDROID_SIGNING_KEY`, `ANDROID_SIGNING_STORE_PASSWORD`, `ANDROID_SIGNING_KEY_PASSWORD`, `ANDROID_SIGNING_KEY_ALIAS`
- Windows signing requires `WINDOWS_SIGNING_KEY`, `WINDOWS_SIGNING_PASSWORD`
- without those secrets, local builds are valid only as unsigned smoke artifacts
- current `POKROV-app` Android shell package and namespace are `space.pokrov.pokrov_android_shell`; set `ANDROID_AUDIT_PACKAGE` to that value unless a release candidate intentionally changes package identity

Android release-block rule:

- do not publish Android as a trusted, store, stable, or raw-audited release until the release-build audit proves that localhost proxy, local DNS, libbox command, Clash API, and equivalent control surfaces are either unavailable to other apps or protected to an acceptable standard
- if that proof is missing, keep Android limited to the documented outside-store beta/owner-attested posture even if the app otherwise builds and signs correctly

Release handoff after the publishing owner has verified the exact candidate:

1. Select the versioned
   `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/release-handoff.json`.
2. Confirm its asset names, SHA-256 values, sizes, GitHub Releases URLs, and beta/manual-gate state against the retained bundle.
3. Validate the runtime sync without remote writes:

```powershell
python scripts/remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/release-handoff.json" `
  --dry-run
```

4. After review, rerun without `--dry-run` to apply the same metadata to the runtime environment.

Then copy the resulting URLs into runtime env:

- `APP_ANDROID_PLAY_URL`
- `APP_ANDROID_APK_URL`
- `APP_ANDROID_APK_ARM64_URL`
- `APP_ANDROID_APK_ARMEABI_V7A_URL`
- `APP_ANDROID_APK_X86_64_URL`
- `APP_ANDROID_APK_UNIVERSAL_URL`
- `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL`
- `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Prompt-based app update metadata is optional but should be set for release
handoff builds:

- `APP_RELEASE_CHANNEL`
- `APP_RELEASE_SCHEMA_VERSION`
- `APP_RELEASE_CANDIDATE_LABEL`
- `APP_RELEASE_HANDOFF_SHA256`
- `APP_RELEASE_ARTIFACT_SET_SHA256`
- `APP_RELEASE_CORE_VERSION`
- `APP_RELEASE_CORE_DESKTOP_ABI`
- `APP_RELEASE_CORE_ANDROID_PACKAGE`
- `APP_ANDROID_VERSION`
- `APP_ANDROID_MIN_SUPPORTED_VERSION`
- `APP_ANDROID_SHA256`
- `APP_ANDROID_SIZE_BYTES`
- `APP_ANDROID_ARM64_SHA256`
- `APP_ANDROID_ARM64_SIZE_BYTES`
- `APP_ANDROID_ARMEABI_V7A_SHA256`
- `APP_ANDROID_ARMEABI_V7A_SIZE_BYTES`
- `APP_ANDROID_X86_64_SHA256`
- `APP_ANDROID_X86_64_SIZE_BYTES`
- `APP_ANDROID_UNIVERSAL_SHA256`
- `APP_ANDROID_UNIVERSAL_SIZE_BYTES`
- `APP_ANDROID_RELEASE_NOTES`
- `APP_ANDROID_RELEASE_NOTES_URL`
- `APP_ANDROID_PUBLISHED_AT`
- `APP_WINDOWS_VERSION`
- `APP_WINDOWS_MIN_SUPPORTED_VERSION`
- `APP_WINDOWS_SHA256`
- `APP_WINDOWS_SIZE_BYTES`
- `APP_WINDOWS_RELEASE_NOTES`
- `APP_WINDOWS_RELEASE_NOTES_URL`
- `APP_WINDOWS_PUBLISHED_AT`

These fields feed `/api/client/apps` and only support prompt-based update UI.
They do not imply silent auto-update, store delivery, trusted Windows signing,
or stable `1.0.0`.

For strict v2, use `--dry-run` first. The preview must show schema `2`, the
expected candidate/channel, exact handoff and artifact-set hashes, Core
identity, and the canonical public APK/EXE records. A missing canonical asset
or invalid v2 document fails before SSH is opened. This local projection is not
runtime-sync or deploy evidence.

Preferred automation path:

```powershell
python scripts/remote_brain_apply_release_handoff.py `
  --brain-ip 82.21.114.104 `
  --metadata-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/release-handoff.json"
```

Or as part of the main rollout:

```powershell
python scripts/release_orchestrator.py `
  --brain-ip 82.21.114.104 `
  --release-metadata-file "C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/release-handoff.json"
```

Distribution rule until store URLs are live:

- GitHub release artifacts are the canonical Android and Windows binary source
- runtime app, bot, and authenticated WebApp download surfaces must read from the same release handoff URLs
- the versioned `release-handoff.json` under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/` is the canonical metadata input for that sync
- bridge-era `release-links.env` files remain compatibility evidence only
- `remote_brain_apply_release_handoff.py` does not rebuild static exports by itself
- if public Android or Windows URLs changed, rebuild and redeploy static marketing outputs so `NEXT_PUBLIC_APP_*` stays aligned with the same release handoff values

## Existing User Cutover

Release communication for existing users must explicitly say:

- `POKROV` is the official public app line
- Android and Windows should be treated as a fresh install path
- existing `kiwunaka.space` profiles stay temporarily compatible during migration, but they are legacy compatibility hosts rather than current public entrypoints
- users should install the new app, connect successfully, and only then remove the old app

Recommended migration order:

1. publish new Android and Windows artifacts
2. update runtime download URLs from release handoff
3. post migration notice in `@pokrov_vpn`
4. answer support with the same canonical instructions
5. keep old `kiwunaka.space` subscription hosts active until most users rotate to new profiles

Operator message template:

```text
POKROV is now the official app.

If you used the old app, install the new POKROV release as a separate app.
Do not delete the old app first.

1. Install POKROV
2. Open it and activate or import your access
3. Confirm that the new app connects successfully
4. Only after that remove the old app if you want

Old subscription links continue to work temporarily during migration.
If you need help, contact @pokrov_supportbot.
```

## Current Telegram Runtime Alignment

Current operational state:

- active public channel: `@pokrov_vpn`
- `@pokrov_vpnbot` is an administrator in that channel
- `@pokrov_feedbackbot` handles feedback intake for reviews and product suggestions
- production env should keep `PUBLIC_CHANNEL=pokrov_vpn`
- production env should keep `NEWS_CHANNEL_ID=@pokrov_vpn`

Post-deploy checks should also confirm:

- the public review feed loads with masked usernames
- featured review cards on the public homepage use the approved review copy
- download links across app, bot, and authenticated WebApp point to the same current Android and Windows artifacts
- marketing homepage download CTA point to the current built release URL or the install/docs fallback, never directly to `connect.pokrov.space`
- public `Открыть кабинет` CTA on `pokrov.space` points to `https://app.pokrov.space/`
- public pricing CTA enter through `https://pokrov.space/checkout/` with plan context, then continue via personal cabinet or Telegram route
- `robots.txt`, `sitemap.xml`, `manifest.webmanifest`, `favicon.ico`, and `apple-icon.png` return dedicated content instead of homepage HTML
- public homepage and SEO landing pages emit canonical, Open Graph, Twitter, and JSON-LD metadata
- node health findings are reported with explicit `current-origin`, `brain-origin`, and `RU-origin` check labels
