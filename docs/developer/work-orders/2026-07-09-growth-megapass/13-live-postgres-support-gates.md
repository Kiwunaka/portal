# Live PostgreSQL And Support Gates

Date: 2026-07-15

Status: authorized live gates executed without deploy, merge, push, source DDL,
or source data mutation. Exact raw reports, encrypted backup, candidate archives,
and protected recovery material remain outside Git.

## PostgreSQL Clone

- `PASS`: production is PostgreSQL 14, not MySQL. A repeatable-read source
  snapshot was streamed through `pg_dump -Fc` directly into encrypted storage.
- `PASS`: the authoritative evidence connection starts with `BEGIN ... READ
  ONLY`, imports that snapshot, and emits aggregate JSON through read-only
  `SELECT` plus psql `\gexec`; it creates no source temporary tables and runs no
  source DDL/DML.
- `PASS`: the retained rehearsal database restored 62 public tables and every
  source/target table count matched exactly.
- Latest retained source-snapshot aggregates: 73 users, 73 access keys, 34
  support tickets, 92 support messages, zero support attachments, 1,045,575
  node-health samples, 151,286 runtime metric rows, and 42,054 observer batches.
- Source size was about 1.14 GB; the clean restored target was about 788 MB.
  The size difference is consistent with a logical restore omitting source
  bloat and is not used as a row-integrity shortcut.
- The encrypted archive is retained root-only on the control plane. Its
  passphrase is retained only as a current-user/SYSTEM protected local blob.
- `PASS`: the target is owned by the guarded ordinary live application role,
  all 526 restored public objects are owned by that role, and default
  database/schema access from `PUBLIC` is revoked. No role or database URL is
  present in the retained report.
- The source snapshot transaction completed normally. No production table,
  index, row, service, or connection was changed by the clone gate.
- Older reports remain historical evidence only. In particular, the prior
  123-object ownership query covered only a subset of object catalogs, and an
  earlier source-evidence command created session-local temporary tables before
  entering `READ ONLY`. Neither is used for the final strict-source claim.

## Candidate Gate Contract

`remote_postgres_candidate_gate.py` accepts only exact `portal` source
confirmation and a different lowercase `_rehearsal` target. It validates a clean
`git archive HEAD portal_bot shared`, strict SSH host keys, private atomic
upload, runner SHA-256 identity, process-level timeout, and scratch cleanup. The
standalone target-only runner checks:

- target database/session identity, ordinary role attributes, database and
  public-object ownership, schema privileges, and `users` read access before
  any application count or DDL;
- blocked additive `ALTER TABLE` and `CREATE INDEX` under bounded lock timeouts;
- the canonical `pokrov_schema_bootstrap` advisory lock;
- two `db.init_db()` runs with unchanged second-run aggregate counts;
- exact account/support schema marker, table, column and index counts; legacy
  totals; unchanged legacy `entitlement_grants` row-content and schema SHA-256
  signatures derived from server-side row hashes without report payloads; and
  separate `account_entitlement_grants` growth;
- real PostgreSQL `FOR UPDATE SKIP LOCKED` behavior;
- two-connection attachment bind/retry with one message and one winner;
- a loopback PostgreSQL wire proxy that forwards `COMMIT`, drops its
  `CommandComplete`, requires a client error, then proves exactly one committed
  row through a direct connection;
- confirmed removal of all synthetic rows and probe DDL.

The authoritative exact-commit apply result is the no-clobber outside-Git
candidate report created after the final commit. This tracked document does not
promote an unrun or older candidate to `PASS`.

## Reverse Proxy And Support

- `PASS`: health, invalid auth branch selection, CORS allow/deny, and HTTP-to-
  HTTPS redirect behavior passed through the public HAProxy/Caddy/API contour.
- `BLOCKED_BY_ACCESS`: valid cookie, bearer, and Telegram initData attachment
  download. No valid session secret or live attachment fixture was available.
- `NOT_APPLICABLE_NO_FIXTURES`: live private historical ACL/missing-file matrix;
  production had no support attachment rows or private attachment references.
- `PASS`: synthetic owner/admin/recovery/missing-file and ACK-loss regression
  remained available locally; live non-private history was counted, not copied.
- `PASS`: `portal-worker` manual restart and current supervision. Candidate code
  was not deployed. `portal-helpbot` has a separate stale transaction incident
  requiring explicit operator action.

## Filesystem Durability

- `PASS`: 50,001-file ext4 enumeration, bounded selected window, frozen mtime
  cutoff, file fsync, parent-directory fsync, and process termination after the
  durable rename.
- `PASS`: successful cleanup unlink batches now fsync their parent directory on
  POSIX. Fsync failure is reported through the existing integer error counter
  and retains the frozen file-window cursor for retry.
- `NOT_RUN_SAFETY`: physical datacenter power removal. A process-kill test is not
  equivalent to pulling server power.

## Origin Evidence

The runner was physically executed at each named origin. `--probe-host` was not
treated as transport; it only labels a report.

- `current-origin`: `PASS`; all three canonical public surfaces, all five
  delivery nodes, and both reserve ingress checks were reachable.
- `brain-origin`: `FAIL`; canonical surfaces, four of five delivery nodes, and
  both reserve checks passed, but the US delivery node timed out on TCP.
- `RU-origin` from canonical `mini`: `FAIL`; canonical surfaces, four of five
  delivery nodes, and both reserve checks passed, but the same US node timed out.
- `rf1` is the tested reserve XHTTP/Hysteria target, not a second canonical RU
  probe origin. Inventory lists `mini` as the only RU probe host.

No broad RU-origin readiness claim is allowed while one delivery node fails
from both brain and RU origin. The current-origin pass does not override those
two failures.

## Rollback And Remaining Manual Work

- The migration is additive. Rollback returns application code while retaining
  account/support rows, attachment files, columns, and indexes; do not rebuild or
  bulk-delete them.
- The rehearsal target and encrypted backup remain retained. Dispose of the
  target only through a separately approved operator action after evidence is no
  longer needed.
- A storage operation reported as failed after commit may still have committed
  if the acknowledgement was lost. Reconcile canonical DB state before retrying
  or deleting a file.
- Remaining manual gates are valid authenticated attachment download, physical
  power-loss testing if a disposable host is approved, the `portal-helpbot`
  transaction incident, and the normal production deploy/signing/device/store
  gates outside this workstream.
