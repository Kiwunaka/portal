# Deployment And Access

Last updated: 2026-07-19

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
- owner-approved exception on `2026-04-24`: the live Telegram-only MTProto proxy runs on the dedicated free node (`151.245.217.23:9443`) through `portal-mtproto.service`; this is not a control-plane service and must not displace the free pool's existing `x-ui` listener on `tcp/443`
- `mini` / `RFMINI` is the canonical RU-origin sandbox when SSH credentials are current; if access is blocked, label the release evidence as `RU-origin check: BLOCKED_BY_ACCESS`
- current `mini` SSH access, verified on `2026-06-01`: use `kiwunaka@176.123.166.119:22` with the retained local password bundle; `29374` opens TCP but resets before the SSH banner and should not be used as the primary SSH path
- RU probe readiness itself is a tracked operational dependency for release confidence and is scoped to `POKROV` public hosts, API health, and delivery-node reachability
- current topology decision as of `2026-07-05`: `mini` remains a bridge/sandbox, not a normal RU delivery node; the planned new RU server may become a full RU node plus a second bridge after provisioning, but no public RU-origin/readiness claim is allowed until that host has current probe evidence
- target bridge topology after the new RU host is live: each eligible foreign non-US node may have two bridge paths, the existing `mini` bridge and the new RU bridge; rollout must keep per-bridge health, downstream target reachability, and rollback controls separate

## Operator Shell Policy

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

Typical use:

```powershell
python scripts/remote_deploy_brain_portal_code.py --brain-ip 82.21.114.104 --restart portal-api,portal-bot,portal-helpbot,portal-feedbackbot
```

Repo-side deploy rule:

- the default restart set is `portal-api`, `portal-bot`, `portal-helpbot`, and `portal-feedbackbot`
- a normal git `push` runs repository guardrails only; production backend/static deploy still requires the manual release workflow in `full` mode or an explicit operator-run deploy command
- backend code deploy is staged and fail-closed: files upload to `/root/portal_bot.deploy-staging/<release_id>/`, current live files are backed up under `/root/portal_bot.deploy-backups/<release_id>/`, and the script runs remote Python bytecode compilation plus shared JSON validation before promoting staged files into `/root/portal_bot` or `/root/shared`
- staged requirements are installed in a temporary staging venv first; the live venv is updated only after staged syntax/JSON/requirements preflight passes
- if preflight or requirements installation fails, the script exits before live file promotion and before any `systemctl restart`
- if a requested unit fails restart or does not report `active`, the script restores the previous backed-up backend/shared files and restarts the requested units on that previous file set
- `--restart` accepts only systemd-safe unit names; do not use shell fragments or chained commands in the unit list
- the deploy payload must include the full shared backend truth set under `/root/shared/`: `product-facts.json`, `public-urls.json`, `design-tokens.json`, `tariff-catalog.json`, `access-matrix.json`, `promo-slots.json`, `support-ai-knowledge.json`, and `support-agent-policy.json`
- the deploy step should be treated as failed if any requested unit does not become `active` after restart
- support AI is a `portal-api` and `portal-helpbot` runtime feature and remains disabled by default. The exact route table is: `SUPPORT_AI_ENABLED=false` selects local fallback; `SUPPORT_AI_ENABLED=true` with `SUPPORT_AI_AGENT_ENABLED=false` selects the legacy one-call helper; both flags `true` select the bounded harness. There is no shadow/double call.
- both provider paths use xCody OpenAI Chat Completions, default `https://api.xcody.dev/v1`, `minimax-m3`, and `SUPPORT_AI_REASONING_EFFORT=medium`. Keep the owner-provided enterprise URL in `SUPPORT_AI_API_BASE_URL` and the credential only in `XCODY_API_KEY` or the compatibility alias `SUPPORT_AI_API_KEY`; never place it in files or command output.
- harness ceilings default to a 25-second run, 12-second provider request, two requests, one tool call, two concurrent runs with a 250 ms acquisition wait, 60-minute/256-session process-local memory, six requests per authenticated owner per rolling minute, three pre-retrieved topics, five tool-result topics, 6,000 retrieved characters, 36,000 serialized input characters, and 700 output tokens. Environment values may lower these ceilings but cannot raise them; invalid values disable the harness and select fallback.
- the only tool is read-only local `search_support_docs` over the deployed validated public-support assets. The runtime has no DB, account, attachment, key/config, shell, arbitrary-file, or command-execution access; `safeDiagnostics` values never enter provider context.
- knowledge refresh is operator-side: first run `python scripts/pokrov_support_ai_kb_refresh.py run-xcody --dry-run`, then only with an owner-side `XCODY_API_KEY` run `python scripts/pokrov_support_ai_kb_refresh.py run-xcody --apply`; review the KB diff before any separately authorized deploy.
- local tests and a successful dry-run do not prove the production enterprise route. Enablement requires retained live evidence for the exact base URL/model/reasoning candidate, including zero payload-format HTTP 400 responses and honest latency/error/cache metrics.

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

### Static sites deploy

- [remote_deploy_brain_static_sites.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_static_sites.py)
- static deploy packages `marketing/out`, `webapp/out`, and `adminapp/out` as local `tar.gz` bundles, uploads one archive per surface, extracts them into a versioned release directory, validates required files, then atomically switches `/var/www/portal/{marketing,webapp,adminapp}` symlinks
- `python scripts/remote_deploy_brain_static_sites.py --brain-ip 82.21.114.104 --plan-only` validates and bundles local `marketing/out`, `webapp/out`, and `adminapp/out` without opening SSH; local and remote validation must reject legacy `marketing/out/fk-verify.html` and `marketing/out/fk-payment-theme.css` files because Lava.top/hosted checkout is the current public payment path
- before bundling, static deploy removes only the legacy `v=<release>` query field from exported `/_next/static/*` references while preserving unrelated query fields and fragments; Next chunk, CSS, font, and media filenames are content-hashed, HTML is revalidated, and inconsistent query-busted chunk identities can prevent soft navigation from committing
- `app.pokrov.space` and `admin.pokrov.space`/`www.admin.pokrov.space` should serve HTML with `Cache-Control: no-cache, must-revalidate`, while `/_next/static/*` assets should serve `Cache-Control: public, max-age=31536000, immutable`
- `admin.pokrov.space` serves the dedicated `adminapp/` static export and must route API calls to `https://api.pokrov.space`; `https://admin.pokrov.space` is part of the default credentialed API CORS allowlist, reuses the existing POKROV admin auth model, and does not make `webapp/` the admin host
- public Caddy on `brain` should keep HTTP/3 disabled with `servers { protocols h1 h2 }` and should serve `Alt-Svc: clear` on public HTTPS responses while browsers may still have the previous `h3=":8444"` alternative cached; this avoids user networks that fail QUIC or non-standard UDP paths while preserving standard HTTPS on `443`
- public HTTP redirects are explicit in `infra/Caddyfile.internal`; do not rely on Caddy's automatic HTTPS redirect on the internal `:8444` listener, because public users must see `https://host/path`, not `https://host:8444/path`
- `www.app.pokrov.space`, `www.api.pokrov.space`, `www.connect.pokrov.space`, and `www.pay.pokrov.space` are HTTPS redirect aliases to their canonical non-`www` hosts; `www.admin.pokrov.space` remains a served admin alias until `admin.pokrov.space` DNS is confirmed on authoritative and public resolvers
- security baseline for `brain`: expose only `80/tcp`, `443/tcp`, and the active SSH port publicly; Caddy `:8444`, API `:8080`, legacy `:2096`, and panel ports must be loopback-only or firewall allowlisted
- `infra/brain-haproxy-l4.cfg` and `infra/portal-transport-front.cfg` use HAProxy TCP stick-tables as a self-hosted burst guard; this is not a volumetric DDoS guarantee and hoster/network filtering remains a separate incident-control layer
- `infra/Caddyfile.internal` owns the public HTTP security headers (`nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors`, `Alt-Svc: clear`) while API path limits remain backend-owned
- [remote_deploy_brain_caddy_config.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_deploy_brain_caddy_config.py) validates the repo Caddy config, uploads it to `brain`, backs up `/etc/caddy/Caddyfile`, validates the installed file, and reloads Caddy; use it for Caddy-only changes instead of the older legacy proxy patch helper
- fresh node/bootstrap paths must enable UFW default-deny and fail2ban `sshd` with escalating bans; root password access is retained only as break-glass until the owner approves a key-only cutover
- repo-managed systemd units should carry `NoNewPrivileges`, `PrivateTmp`, and read-mostly system protections unless a unit has a documented operational need for broader write access

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

### Lava.top Checkout Enablement

The backend supports `lavatop` as the active RUB provider for public beta; public provider env must stay Lava-only (`RUB_PAYMENT_PROVIDER_ENABLED=lavatop`, `RUB_PAYMENT_PROVIDER_ORDER=lavatop`). As of `2026-05-15`, the authenticated cabinet beta path has redacted live evidence for invoice creation, authenticated success callback handling, invalid-auth rejection, account extension, and fulfillment idempotency. Required env is documented in [Lava.top Payment Operations](C:/Users/kiwun/Documents/ai/VPN/docs/operations/lavatop-payment-operations.md): `LAVATOP_API_KEY`, `LAVATOP_OFFER_ID` or per-plan `LAVATOP_OFFER_ID_<PLAN_CODE>`, and either `LAVATOP_WEBHOOK_API_KEY` or Basic webhook credentials. Anonymous public checkout also requires configured email delivery (`EMAIL_DELIVERY_WEBHOOK_URL` plus relay secret/SMTP env) before it can safely issue paid access keys.

Retained evidence: [Paid Checkout Launch Evidence - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/paid-checkout-launch-evidence-brain-2026-05-15.json), [Brain Post-Deploy Live Probe - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/brain-post-deploy-live-probe-2026-05-15.json), and [Live Payment And Email Confirmation - 2026-05-15](C:/Users/kiwun/Documents/ai/VPN/docs/audit-artifacts/live-payment-email-confirmation-2026-05-15.md). Failed-payment no-fulfillment and paid access-key delivery have beta evidence; refund/chargeback reconciliation remains an operator runbook requirement before stronger production checkout claims.

### External RU probe runner

- [ru_probe_runner.py](C:/Users/kiwun/Documents/ai/VPN/scripts/ru_probe_runner.py)

Typical use from the external RU host:

```powershell
python scripts/ru_probe_runner.py --reserve-host rf1.pokrov.space --probe-host mini --out ops-local/ru-probe.json
python scripts/render_ru_probe_report.py --input ops-local/ru-probe.json
```

Current SSH note for running the probe remotely: `mini` is reachable as `kiwunaka@176.123.166.119:22`. Do not copy the password into docs or reports; use the retained local password bundle or an approved secret channel.

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

### Telegram MTProto proxy on free node

- [remote_install_mtproto_proxy.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_mtproto_proxy.py)

Current state:

- the dedicated free node (`151.245.217.23`) hosts `portal-mtproto.service` on `tcp/9443`
- `x-ui.service` continues to own `tcp/443` on the free node for normal free-pool delivery
- the previous `mini:443` MTProto attempt is disabled; this compatibility proxy is kept only on the dedicated free node
- the MTProto secret and share links live only in `/etc/portal-mtproto.env` on the free node; do not copy them into docs, commits, or handoff reports
- `portal-mtproto-config-refresh.timer` is enabled on the free node because it can reach `core.telegram.org`
- the official Telegram MTProxy source currently needs a PID namespace workaround on this host, so the systemd unit starts it through `unshare --fork --pid --mount-proc`

Typical install or refresh from the repository root:

```powershell
python scripts/remote_install_mtproto_proxy.py --node-code free --node-host 151.245.217.23 --ssh-port 29374 --listen-port 9443 --enable-refresh-timer
```

If the endpoint must be registered with Telegram, send `151.245.217.23:9443` or an approved DNS name that resolves to `151.245.217.23` and still uses port `9443`.

### Feedback bot service install

- [remote_install_feedbackbot_service.py](C:/Users/kiwun/Documents/ai/VPN/scripts/remote_install_feedbackbot_service.py)

## Transport Rollout And Node Shaping

The transport rollout stays additive: the current Reality path remains in place while app-first cohorts are moved to `grpc_443_primary` through rollout policy and per-node transport catalogs.

Transport policy rule:

- `nodes.transport_profiles_json` is the canonical per-node transport catalog for rollout and should carry the fixed profile set `legacy_reality_fallback`, `grpc_443_primary`, `reserve_xhttp_cdn`, and `operator_lab`; `ru_bridge_relay` lives in `network_rollout_config` because it is a cross-node RU bridge, not a node-local delivery inbound
- legacy node fields such as `inbound_id`, `vless_port`, and `reality_*` remain compatibility input and should synthesize `legacy_reality_fallback` when the transport catalog is empty
- `AppSetting.network_rollout_config` is the operator-controlled rollout source of truth for `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `network_rollout_config` is a JSON policy blob with `version`, `defaults`, `carrier_overrides`, `cohort_overrides`, `reserve_xhttp_cdn`, `ru_bridge_relay`, `operator_lab`, `package_catalog_feed`, `routing_rules_feed`, and `support_recovery_order`
- old node-inventory markdown moved to `docs/archive/flat-docs/08-node-inventory.md`; `scripts/node_inventory.py` keeps legacy bootstrap, DNS, and remote-maintenance helpers compatible with that retained IP snapshot, but live deployment decisions must still use Postgres/admin API state, rollout config, and current probe evidence
- `defaults` normally pin `routing_mode_default=all_except_ru`, `transport_profile=legacy_reality_fallback`, and `dns_policy=ru_direct_split`; live incident response may temporarily set `transport_profile=ru_bridge_relay`
- `carrier_overrides` and `cohort_overrides` may only change `transport_profile`, `dns_policy`, `routing_mode_default`, and `ip_version_preference`
- `reserve_xhttp_cdn` stays opt-in, disabled by default, and is intended only as a reserve path on eligible nodes until a later rollout wave promotes it explicitly
- `ru_bridge_relay` stays opt-in unless an incident commander explicitly promotes it; app-managed sing-box manifests expose countries at the top level and nested `Обычный` / `Белые списки` endpoint choices under non-US nodes, while US remains a direct-only target and is never routed through the RU bridge
- app-managed sing-box configs load runtime rule sets from `https://connect.pokrov.space/rules/geoip-ru.srs` and `https://connect.pokrov.space/rules/adblock.srs`; the brain host mirrors those files under `/var/www/portal/rules/` and refreshes them with `pokrov-singbox-rules-refresh.timer`
- BitTorrent routing is RU-only when the rendered paid profile contains `ru`/`ru_spb` delivery outbounds: the generated config adds a hidden RU torrent selector and points `protocol=bittorrent` at it before the `geoip-ru` direct rule. Profiles without RU outbounds keep the old direct fallback.
- `operator_lab` remains allowlist-only, carries `enabled`, `allowlist_install_ids`, `allowlist_tg_ids`, `allowlist_node_codes`, and `expires_at`, and must stay hidden from public UI and mass session/profile payloads
- app-managed session and profile delivery should use the rollout-selected transport profile, while manual/export compatibility links stay on `legacy_reality_fallback` until the share-link parity wave lands
- `GET /api/client/profile/managed` is the primary app-managed provisioning endpoint; `subscription_url` stays manual/import fallback only
- capacity-aware app routing uses `GET /api/client/nodes/candidates`, `POST /api/client/nodes/select`, and optional `selected_node_code` on `GET /api/client/profile/managed`; `POST /api/client/nodes/latency-samples` remains compatibility telemetry
- subscription rendering dynamically orders nodes while `SUBSCRIPTION_DYNAMIC_ORDERING=true`; `SUBSCRIPTION_EXCLUDE_HARD_REJECT=false` is the default so paid/trial subscriptions keep fallback countries even when a node is penalized by low `health_score`; `true` is an emergency opt-in that can temporarily hide explicitly hard-rejected nodes without deleting metrics or keys
- observer-lite deployments whose Xray access log emits naive timestamps must set `PORTAL_OBSERVER_SOURCE_TIMEZONE` (or pass `--source-timezone`) to `UTC`, `Z`, or a strict fixed offset such as `+03:00` or `-04:00`; IANA names, absent settings, and invalid or out-of-bounds offsets make each affected line a counted parse error and no observation is sent for that line
- offset-aware observer timestamps are converted to canonical UTC `Z` before batching; the collector never interprets a naive timestamp as server-local time or UTC implicitly
- core rollout/rollback flags are `CAPACITY_AWARE_NODE_SELECTION`, `SUBSCRIPTION_DYNAMIC_ORDERING`, `SUBSCRIPTION_EXCLUDE_HARD_REJECT`, `KEY_PRESSURE_SCORING`, `KEY_PRESSURE_FAIR_USE_ROUTING`, `APP_NODES_SELECT_ENDPOINT`, `XRAY_METRICS_COLLECTOR`, `NODE_AGENT_METRICS`, and `USERNODE_MAPPING_AS_CANDIDATE_LIMIT`
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
- `scripts/verify_brain_ready.py` is brain-local verification, not a replacement for separate `current-origin` or `RU-origin` evidence
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
- marketing and checkout probes should use route/function markers such as `Android + Windows`, `app.pokrov.space`, `checkout-shell`, `ключ доступа`, and canonical URLs, not old hero copy that can change without a deploy failure
- transport rollout verification on the canary node with `scripts/remote_apply_node_qdisc.py show`
- transport front verification with `scripts/remote_transport_front_smoke.py`
- `tc -s qdisc` on the shaped interface
- `scripts/remote_node_qdisc_smoke.py` results for heavy-flow saturation and small-probe latency
- when observer-lite is enabled on any node, `portal-node-observer.timer` freshness on that node plus `/api/admin/metrics/status` and `/api/admin/nodes/health` observer fields
- observer-lite promotion requires a manual exact-candidate proof that a retained Xray log timestamp and its configured source zone produce the expected UTC `Z` observation, trial activation at that UTC instant, and expiry exactly `5 days` later; also prove that a naive fixture with the setting removed is skipped and increments batch `parse_error_count`
- after any REALITY target rotation, verify the node inbound `dest/serverNames`, the `brain` `nodes.reality_sni` row, and `python scripts/predeploy_node_readiness.py --brain-ip 82.21.114.104` in the same handoff

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

- `https://api.pokrov.space/` is the canonical API base for browser flows
- `app.pokrov.space` may host the UI, but it must not be treated as an API origin when it returns HTML

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

- public distribution is the public GitHub prerelease handoff for the outside-store beta through the current cabinet/runtime contract
- distributed version: `1.0.0-beta`
- target candidate: `1.0.0-rc.1`
- stable `1.0.0` is not proven
- artifact creation, signing, and candidate publication are owned by [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md); this guide owns runtime application and deploy access

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
- `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL`
- `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Prompt-based app update metadata is optional but should be set for release
handoff builds:

- `APP_RELEASE_CHANNEL`
- `APP_ANDROID_VERSION`
- `APP_ANDROID_MIN_SUPPORTED_VERSION`
- `APP_ANDROID_SHA256`
- `APP_ANDROID_SIZE_BYTES`
- `APP_ANDROID_ARM64_SHA256`
- `APP_ANDROID_ARM64_SIZE_BYTES`
- `APP_ANDROID_ARMEABI_V7A_SHA256`
- `APP_ANDROID_ARMEABI_V7A_SIZE_BYTES`
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
