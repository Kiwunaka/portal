# Support Security Boundary Slice

Date: 2026-07-14
Status: platform Tasks A-B candidates implemented; promotion blocked on recovery-aware client slice and manual support-ownership gates; deploy not requested

## Scope

Task A was implemented in shared worktree
`C:/Users/kiwun/Documents/ai/VPN/.worktrees/support-security-foundation` on
branch `codex/support-security-foundation`, based on
`a887040f176f53b2b3554388a39f9c91291ddcc8`.

Only these paths changed:

- `portal_bot/support_ai_service.py`
- recovery-scope and ticket response checks in `portal_bot/api.py`
- review-approved fixed-code persistence logging in `portal_bot/helpbot.py`
- review-approved SQLAlchemy parameter hiding in `portal_bot/db.py`
- `tests/test_support_ai_service.py`
- `portal_bot/tests/test_email_auth.py`
- `tests/test_api_auth_and_tickets.py` (test-only Telegram isolation)
- `docs/architecture/api-contracts.md`
- `docs/architecture/support-feedback-flow.md`
- this completion note

Task A did not change account ownership, models, migrations, `tickets_repo`,
bot, webapp, payments, or integrations. Task B adds the canonical support
ownership slice described below on its separate assigned branch. No
final-candidate test called Telegram or any other live provider/system.

## Task B Canonical Ownership

Task B was implemented in
`C:/Users/kiwun/Documents/ai/VPN/.worktrees/support-account-ownership` on
`codex/support-account-ownership`, based on
`7162481e5ff6c948ecb40c4d2835f9466b7e3470`.

- Nullable indexed canonical owners were added to tickets and uploads with
  additive rerunnable SQLite/PostgreSQL migrations. Legacy Telegram ownership,
  message attribution, bodies, media, and files remain unchanged.
- Marker-gated `migration.support_account_ownership.v1` runs after account
  foundation and atomically commits assignments, safe idempotent merge reviews,
  and its marker. Resolution uses only exact direct-user, explicit linked
  Telegram, or enabled Telegram-identity evidence and bounded merge traversal.
- Repository, API, main bot, and helpbot enforce account-first access with
  legacy fallback only for `NULL` owners. Read-only checks do not claim rows;
  eligible user writes may claim an exact legacy ticket. Account-linked
  identities share history, while a tempting legacy ID cannot override a
  different non-null owner.
- Account merge retargets ticket/upload owners without deleting or changing
  support history. Bounded notification routing prefers explicit linked
  Telegram, then enabled Telegram-identity evidence, then only a real
  historical Telegram ID; missing real targets are skipped and safely logged.
- Rehearsal ordering and account-orphan checks cover both new fields without
  weakening existing user/message checks. Manual/test cleanup preserves all
  account-owned support history.

## Task B TDD And Verification

All Task B Python commands used only
`C:/Users/kiwun/Documents/ai/VPN/.worktrees/market-ready-cis-integration/.tmp/venv-auth-sessions/Scripts/python.exe`,
with this worktree's `portal_bot` on `PYTHONPATH` and worktree-local pytest
basetemp paths.

- RED was captured before each production slice: model/migration `3 failed`,
  backfill service import `5 failed`, repository behavior `3 failed`,
  merge/rehearsal `3 failed`, startup/API `2 failed`, and bot/helpbot/cleanup
  `3 failed`. Each focused group passed after its implementation.
- Final exact-candidate regression over ownership service/repository,
  migrations/rehearsal, account foundation/merge, API/auth/recovery, main bot,
  and helpbot: `PASS`, `177 passed in 303.13s`.
- Focused final account-merge authority check: `PASS`, `7 passed in 10.48s`.
- Python compilation: `PASS` for all changed Python production and test paths.
- Documentation checks: `PASS`, 30 link checks and 4 agent-context/app-bot
  contract tests.
- `git diff --check`: `PASS` with only Git LF-to-CRLF conversion notices.
- Added-line high-confidence credential-shape scan: `PASS`, no matches.

## Implemented Contract

- One support sanitizer runs before truncation for outbound user text and
  inbound model text. Oversized input fails closed before any string scan;
  provider chunks are sliced before concatenation. Normal work is limited to
  65,536 input/output characters, three percent-decode passes, one
  non-recursive decoded URL rescan, bounded URL nesting, and linear spans.
  Residual deeper percent-encoded URL signatures fail closed through a linear
  structural probe. NFKC is incremental and stops before expansion can cross
  the output bound. JSON escapes, HTML entities, zero-width characters, IDNA
  separators, fullwidth forms, quotes, and Unicode dash variants are normalized
  within the same bound.
- Production provider responses are rejected by declared size or incremental
  stream reads after 262,144 bytes and before JSON parsing. The test-only text
  fake compatibility path also checks encoded byte length before parsing.
- Stable category placeholders cover Unicode email, proxy links, structurally
  classified token-bearing HTTP(S) URLs, recovery and activation codes,
  hyphenated/compact UUIDs, `pkr_rt_`, signed/JWT-like session tokens,
  English/Russian labelled credentials, API/private keys, Basic/Bearer
  authorization, long digits, and labelled or raw Telegram init data. Telegram
  classification requires a realistic numeric `auth_date` plus 64-hex `hash`;
  `query_id`, `user`, and `signature` are optional. Recognized blobs are
  replaced through the end of their line, including fields after top-level
  pipes and HTML-escaped separators. Empty/placeholder prose remains readable.
- After bounded normalization and Telegram redaction, one scanner emits
  alternating non-URL and URL spans. Generic matching runs only on non-URL
  spans; a safe URL is emitted directly and a private URL is replaced directly.
  The old marker shielding/restoration mechanism is absent. Encoded userinfo,
  sensitive canonical query/fragment keys, semicolon and quoted nested
  assignments, keyless JWT fragments, nested proxy/subscription URLs, POKROV
  endpoint tokens, subscription paths, and ticket UUIDs are private. Exact
  known GitHub/POKROV public-reference hosts preserve genuine commit/docs
  references; host dots and arbitrary `docs.*`/`status.*` names are untrusted.
- Sanitized model output is the only model output returned to callers for
  ticket storage. Provider failure logs contain only bounded status plus a
  fixed code; provider body and exception detail are excluded. API/helpbot
  persistence failures use only `support_reply_persist_error`; rollback failure
  detail is contained. Session-close failure is contained under only
  `support_reply_cleanup_error`, and SQLAlchemy exception rendering hides
  statement parameters.
- Recovery authorization now uses an exact HTTP method plus FastAPI route
  template allowlist. Missing and unknown `request.scope["route"].path` values
  fail closed. Prefix matching and standalone support AI access were removed.
- Recovery support is text-only. Upload, attachment download, standalone AI,
  subscription, managed-profile, and normal networking routes return
  `403 recovery_scope_forbidden`.
- Recovery ticket create/message rejects any nonempty `media_type`,
  `media_file_id`, or `media_payload`. Ticket list/get/create/message omits all
  three keys from every recovery-visible message, including historical
  attachments. Normal client/admin message serialization remains compatible.

## TDD Evidence

- Initial support RED: `23 failed, 6 passed, 7 subtests passed`; failures were
  the new sanitizer categories, model-output boundary, and fixed provider-log
  contract. GREEN after implementation: `8 passed, 29 subtests passed`.
- Recovery RED initially hit four setup errors because the worktree-local
  `.tmp` parent did not yet exist. After creating that local directory, the
  unchanged focused command produced the expected behavioral RED:
  `4 failed, 15 deselected`. GREEN: `4 passed, 15 deselected`.
- UUIDv7 self-review RED: `1 failed, 1 passed, 25 subtests passed` for the new
  v7 case. After broadening the canonical UUID pattern, the full support file
  passed `8 passed, 30 subtests passed`.
- Blocking-review sanitizer RED: `41 failed, 9 passed, 34 subtests passed in
  1.57s`. This reproduced encoded/Unicode token bypasses, optional-`query_id`
  Telegram data, unsafe URL mutation, and missing normalization bounds. The
  first review GREEN was `10 passed, 74 subtests passed in 0.55s`.
- Blocking-review persistence RED: `3 failed in 17.88s` for API logging,
  helpbot logging, and SQLAlchemy parameter rendering. Focused GREEN was
  `3 passed in 15.38s`.
- Self-review added two further RED cases: decoded Telegram `user` JSON left a
  value behind (`1 failed, 1 passed, 62 subtests passed`), and NFKC expansion
  exceeded the work bound (`1 failed, 1 passed, 1 subtest passed`). Their
  focused GREEN results were `1 passed, 63 subtests passed` and
  `1 passed, 2 subtests passed` respectively.
- Second-review sanitizer RED reproduced the common credential, strict-host,
  quoted URL, complete initData span, exact truncation, provider materialization,
  and linear-path findings: `27 failed, 10 passed, 83 subtests passed in 3.21s`.
  The first crafted path was intentionally large and exposed the old quadratic
  behavior by exceeding the command yield window; that exact local pytest was
  terminated, the fixture was reduced while retaining a deterministic
  O(n)-versus-O(n^2) call-count assertion, and the quoted RED count is from the
  bounded rerun.
- Second-review persistence RED was `2 failed, 20 deselected in 24.21s` when
  rollback itself raised. Test-isolation RED was `1 failed, 69 deselected in
  11.28s` before the suite-wide Telegram `AsyncMock` was installed.
- The first attempted sanitizer GREEN exposed a local regex syntax typo and was
  not counted as evidence. After correction, three URL classification cases
  remained; final GREEN is the exact support result below.
- Bound-before-work self-review RED was `1 failed, 13 deselected, 2 subtests
  passed in 0.56s`; GREEN after moving the length check before NUL replacement
  was `1 passed, 13 deselected, 2 subtests passed in 0.35s`.
- Third-review structural RED was `25 failed, 12 passed, 105 subtests passed in
  1.25s`. It reproduced marker shielding, host-dot trust, nested URL
  assignments/schemes, ticket UUID disclosure, realistic Telegram line
  boundaries, useful diagnostic-code mutation, whole-string NFKC, pre-slice
  chunk concatenation, and missing provider byte limits. The first structural
  GREEN was `18 passed, 126 subtests passed in 0.66s`.
- Third-review cleanup RED was `2 failed, 20 deselected in 13.15s`; both API and
  helpbot propagated synthetic `close()` failures after persistence/rollback
  handling. Focused GREEN was `2 passed, 20 deselected in 15.12s` with fixed
  cleanup-code logging only.
- Final self-review added a deterministic deep nested-URL call-count case. RED
  was `1 failed, 18 deselected in 0.64s` with 114 classifier calls. GREEN was
  `1 passed, 18 deselected in 0.43s` after constant-depth propagation and
  fail-closed handling. The resulting full sanitizer count is recorded below.
- Final authority-differential review RED was `3 failed, 1 passed, 9 subtests
  passed in 0.54s` for encoded `#`/`?` delimiters before userinfo and an empty
  port on an allowlisted host. GREEN was `1 passed, 12 subtests passed in
  0.54s` after validating each bounded percent-decode layer before host trust.
- Fifth-review RED was `4 failed, 1 passed in 0.84s` for mixed encoded schemes,
  quote-delimited userinfo, and raw Telegram init data containing a URL. GREEN
  was `2 passed, 3 subtests passed in 0.36s` after a decoded URL rescan and a
  whole-line Telegram pass before URL span partitioning.
- Sixth-review RED reproduced quote/space userinfo continuation and excessive
  recursive decoder work: the authority cases were `2 failed, 2 passed, 3
  subtests passed in 4.78s`; the deterministic 63,551-character work fixture
  was `1 failed in 5.08s` after processing 1,476,478 decoder-input characters.
  GREEN was `2 passed, 5 subtests passed in 1.01s` after limiting decoded URL
  rescanning to one non-recursive level and failing closed beyond it.
- Seventh-review RED was `1 failed, 2 passed, 5 subtests passed in 1.42s` for a
  seven-layer encoded subscription URL left beyond the three-pass budget.
  GREEN was `2 passed, 6 subtests passed in 0.77s` after adding a linear
  structural probe for residual nested percent escapes. Independent re-review
  returned `PASS`; its four focused tests reported `33 subtests passed` and
  preserved supported-depth public references.

## Verification

All review-fix Python commands used only
`C:/Users/kiwun/Documents/ai/VPN/.worktrees/market-ready-cis-integration/.tmp/venv-auth-sessions/Scripts/python.exe`,
with `PYTHONPATH=portal_bot` for Python test/compile commands and worktree-local
pytest basetemp paths.

- Final sanitizer/provider boundary file:
  `$env:PYTHONPATH=(Resolve-Path 'portal_bot').Path; & 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\market-ready-cis-integration\.tmp\venv-auth-sessions\Scripts\python.exe' -m pytest tests/test_support_ai_service.py -q --basetemp .tmp/pytest-controller-seventh-review-full-support`
  -> `PASS`, `30 passed, 184 subtests passed in 1.27s`.
- Final exact-candidate support regression:
  `$env:PYTHONPATH=(Resolve-Path 'portal_bot').Path; & 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\market-ready-cis-integration\.tmp\venv-auth-sessions\Scripts\python.exe' -m pytest tests/test_support_ai_service.py portal_bot/tests/test_email_auth.py tests/test_api_auth_and_tickets.py tests/test_helpbot_lifecycle.py -q --basetemp .tmp/pytest-controller-seventh-review-combined`
  -> `PASS`, `130 passed, 184 subtests passed in 264.47s`.
- `$env:PYTHONPATH='portal_bot'; & 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\market-ready-cis-integration\.tmp\venv-auth-sessions\Scripts\python.exe' -m py_compile portal_bot/support_ai_service.py portal_bot/api.py portal_bot/helpbot.py portal_bot/db.py tests/test_support_ai_service.py portal_bot/tests/test_email_auth.py tests/test_api_auth_and_tickets.py`
  -> `PASS`.
- `& 'C:\Users\kiwun\Documents\ai\VPN\.worktrees\market-ready-cis-integration\.tmp\venv-auth-sessions\Scripts\python.exe' scripts/check-links.py --report .tmp/support-security-controller-seventh-final-link-check.md`
  -> `PASS`, 30 link-contract checks reported `PASS`.
- `git diff --check` -> `PASS`; Git reported only existing LF-to-CRLF worktree
  conversion warnings.
- Added-line high-confidence secret scan found no production credential shape.
  Three PEM headers and three URL-userinfo matches are intentional synthetic
  fixtures in `tests/test_support_ai_service.py`; no match exists in runtime or
  documentation paths.

## Manual Gates

An earlier pre-isolation regression run attempted one Telegram send using
synthetic invalid test configuration. That run is excluded from final evidence
and is not a live-success claim. The exact-candidate API runs above globally
patched `_telegram_send_message` to `AsyncMock`; their evidence is offline.

- `MANUAL_OWNER_TEST`: measure production PostgreSQL `ALTER TABLE` and index
  lock impact for both additive support ownership fields before deployment.
- `MANUAL_OWNER_TEST`: run backup/restore against the exact deployment
  candidate and retain redacted before/after ticket, attachment, assignment,
  unresolved/conflict review, and marker counts.
- `MANUAL_OWNER_TEST`: exercise real PostgreSQL concurrency between account
  merge/backfill and support create/reply/upload writes. SQLite and unit lock
  tests are not live deadlock or lost-update evidence.
- `MANUAL_OWNER_TEST`: verify the configured model/provider and production log
  collector never retain raw user/model/provider echo material.
- `MANUAL_OWNER_TEST`: exercise the exact deployed API revision through the
  real reverse proxy with a real recovery session; local TestClient evidence is
  not deployment proof.
- **Promotion blocker:** the active `POKROV-app` adapter always includes app
  diagnostics in support ticket traffic and has a standalone assistant path.
  This platform slice must not be promoted as recovery-ready until a separate
  recovery-aware client slice omits diagnostics/media for recovery sessions and
  bypasses standalone `/api/client/support/assistant` in favor of allowed text
  ticket endpoints. `POKROV-app` was read only and was not modified here.
- `MANUAL_OWNER_TEST`: after that client slice exists, verify Android and
  Windows recovery UX handles text-only tickets, omitted attachment metadata,
  device revoke, logout, and reissue. Local server tests do not prove client UX.
- `MANUAL_OWNER_TEST`: verify existing private attachment history remains
  available to normal owners/admins and unavailable to recovery sessions in the
  deployed database/object filesystem.
- `NOT_REQUESTED`: live provider, Telegram, email, panel, node, payment, deploy,
  push, signing, physical-device, current-origin, brain-origin, and RU-origin
  checks.

## Handoff State

The repository candidate is locally tested only. It is not production proof or
release authorization. The slice is retained in one scoped feature-branch
commit for collision review and replay; no push or deploy was performed.

## Task C: Private Support Attachment Binding

### Implemented Boundary

- `support_attachments` gains nullable indexed `ticket_id`, nullable unique and
  indexed `message_id`, nullable `attached_at`, and nullable indexed
  `expires_at`. SQLite and PostgreSQL migration helpers are additive and
  rerunnable; they do not rebuild the table or install a physical foreign key.
- New uploads are staged with the public settings
  `SUPPORT_PENDING_UPLOAD_TTL_HOURS=24`,
  `SUPPORT_PENDING_UPLOAD_MAX_COUNT=5`, and
  `SUPPORT_PENDING_UPLOAD_MAX_BYTES=52428800`. Quota is canonical-account first,
  otherwise exact legacy Telegram owner, and includes only unexpired unbound
  rows. Admission cleanup is limited to expired unbound rows whose expiry is
  non-null and deletes files only after a conditional row delete succeeds.
  Same-owner admission is serialized through a fixed 256-stripe process lock;
  PostgreSQL additionally takes a deterministic transaction advisory lock for
  cleanup and reacquires it after the cleanup commit so quota read, file write,
  row insert, and persistence commit share one locked transaction. Distinct
  owners retain distinct quota and advisory keys without an unbounded lock
  registry; a process-local stripe collision only adds conservative local
  serialization and does not merge owner quota scope.
- Files are written to an exclusive temporary file in the destination
  directory and atomically renamed. Database persistence failure removes both
  temporary and final paths. Upload responses retain the legacy attachment
  objects and add the opaque stored server identifier as `attachment_id`.
- Ticket create/reply binds `attachment_id` in the same transaction after the
  message flush. Ownership, expiry, mixed media, duplicate binding, forged old
  private references, and concurrent losers have stable 400/404/409 contracts.
  Recovery sessions cannot upload, bind, or download media, including when the
  synthetic recovery actor number equals `ADMIN_ID`.
- Rolling compatibility accepts an exact owned `support/{stored_name}` legacy
  private triplet only when its metadata is semantically consistent, then
  canonicalizes and binds it. Non-private Telegram/client media triplets remain
  unchanged. Bound downloads use bound-ticket access; legacy/unbound rows keep
  exact owner/admin fallback. The WebApp sends only `attachment_id`, fetches
  private blobs with the normal API auth behavior, allows only canonical or
  rewritten retired private paths, and revokes object URLs.
- Rehearsal reports counts/status only and verifies attachment ticket presence,
  message presence, and attachment/message ticket agreement. Monitoring owners
  now name bounded rejection/cleanup/binding counters and redacted bound,
  unbound, expired, and dangling gauges; no production metric result is claimed.

### TDD Evidence

- Migration RED:
  `4 failed in 2.04s` for missing columns, indexes, dependencies, and rehearsal
  invariants. Migration GREEN/regression:
  `35 passed in 10.43s`.
- Backend RED:
  `7 failed, 1 passed, 94 deselected in 21.28s` for missing opaque ID/expiry,
  quota cleanup, create/reply binding, rolling private triplet behavior, bound
  ACL, concurrency, and recovery attachment rejection. Focused GREEN was
  `8 passed, 94 deselected in 21.06s`; the final focused regression after the
  cleanup-race adjustment was `13 passed, 89 deselected in 35.88s`.
- Controller regression for the restored safe-diagnostics assertions:
  `1 passed, 78 deselected in 3.53s`. The exact recovery-actor-equals-admin
  download regression is included in the final backend suite.
- WebApp behavioral RED was `2 failed`: no authenticated blob request was made
  and the picker remained too permissive. Focused GREEN, including ID-only
  create and reply payloads, was `2 passed in 6.3s`.
- Final self-review RED was `2 failed`: mismatched extension/MIME pairs were
  accepted and the canonical-path scenario did not complete its expected
  authenticated fetch. After sharing the exact server stored-name normalizer and
  MIME mapping, focused build/TypeScript and E2E GREEN was `2 passed in 5.7s`.
- Independent-review quota RED was `2 failed, 80 deselected in 6.11s`: both
  canonical-account count and exact legacy-owner byte races admitted two
  concurrent uploads. PostgreSQL helper RED was `1 failed, 82 deselected in
  3.71s`; transaction-boundary RED was `1 failed, 83 deselected in 3.92s`
  because only the pre-cleanup advisory lock existed; bounded-registry RED was
  `1 failed, 83 deselected in 3.46s`. Combined quota GREEN was `6 passed, 78
  deselected in 15.92s` after fixed stripes and post-cleanup lock reacquisition.
- Independent-review bind-boundary RED was `2 failed, 1 passed, 84 deselected in
  3.70s`: expiry and deletion between lookup and conditional update both
  returned 409. GREEN was `3 passed, 82 deselected, 2 subtests passed in 8.41s`;
  both races now return 404 and roll back the flushed message, while a real
  already-bound concurrent loser remains 409.
- Persistence-test RED was `1 failed, 84 deselected in 3.51s`: the original
  fixture never reached `os.replace`. The corrected fixture allows cleanup
  commit and fails the attachment-row persistence commit; GREEN was `1 passed,
  84 deselected in 3.52s`, with replace observed and no temp path, final path,
  or database row. That prior immediate-final-cleanup expectation is superseded
  by the final commit-ambiguity contract and evidence below.
- PostgreSQL migration-harness RED was `1 failed, 3 deselected in 0.48s` for the
  missing executable helper. GREEN/regression was `35 passed in 9.95s`: a
  stateful recording connection runs the helper twice, suppresses second-run
  ALTER statements, retains the unique message index and legacy-row marker,
  and rejects FK, rebuild, or data-mutation SQL. This is helper-level evidence,
  not a live PostgreSQL execution claim.
- Second independent-review API RED was `3 failed, 1 passed in 11.55s`:
  same-owner admission deleted another owner's expired file, explicit-expiry
  unbound downloads remained available to owner/admin, and upload rejection
  telemetry used an unstable reason. GREEN was `4 passed in 13.12s`; recovery
  scope remained an exact `403 recovery_scope_forbidden` even when its actor ID
  equals `ADMIN_ID`.
- Lazy-download RED was `1 failed`: thread mount made two authenticated Blob
  requests before user action. Focused Playwright GREEN was `1 passed in 15.4s`;
  the request now starts only after the explicit load action, retains auth/cookie
  behavior, creates a Blob URL, and the component aborts/revokes on replacement
  or unmount.
- Reconciler contract RED was `1 failed` for the missing module. Concrete cleanup
  RED was `2 failed, 1 passed in 0.77s` for the unimplemented orphan/temp and
  expired-row behavior; worker wiring RED was `1 failed in 3.09s`. Initial GREEN
  was `4 passed in 2.92s` across cleanup and worker wiring.
- Reconciler observability RED was `2 failed in 0.96s`: no bounded DB-row
  missing-file count existed and a malformed historical stored name could unlink
  another row's canonical basename. GREEN was `5 passed in 0.91s`; the scan is
  deterministic, limited, non-destructive, and exact-name validated. These are
  local counters and wiring evidence, not proof of live production scheduling.
- Cleanup boundary self-review RED was `1 failed in 0.71s` when a replacement
  row appeared after expired-row commit but before unlink, and admission RED was
  `1 failed in 4.09s` when a malformed same-owner DB name mapped onto another
  owner's canonical basename. Final cleanup GREEN was `6 passed in 0.77s`, and
  focused API GREEN was `3 passed in 9.24s`: every unlink now requires an exact
  canonical basename, and expired unlink rechecks that no DB row exists.
- Final controller starvation contract RED was `1 failed in 1.68s` for the
  missing bounded cursor; its micro-GREEN was `1 passed in 0.88s`. Behavioral
  RED was `1 failed in 1.26s` because the reconciler rejected `cursor` and fixed
  first windows could not advance. GREEN was `9 passed in 1.24s`: successive
  runs reach file and DB rows beyond `scan_limit`, then wrap, with bounded memory
  and integer-only reports. The worker-held cursor resets after process restart;
  no durable cursor or live worker claim is made.
- Wrap-observability RED was `1 failed in 1.10s` because the integer-only report
  did not expose completed file/row wraps. GREEN was `9 passed in 2.06s` with
  bounded `file_window_wrapped` and `row_window_wrapped` flags; cursor values
  remain process-local and absent from logs.
- Final security-review cursor-contract RED was `1 failed in 1.05s`: the
  process-local cursor lacked frozen filesystem and DB cycle boundaries. Its
  micro-GREEN was `1 passed in 0.89s`. Sustained-growth and deletion-gap RED was
  `2 failed in 1.28s`: new entries could keep extending the active windows and
  empty snapshots did not expose completion. Cleanup GREEN was `11 passed in
  2.24s`: each cycle now freezes a filesystem mtime cutoff and DB max-ID
  high-water, advances in bounded candidate/row windows, completes despite
  continued newer inserts, revisits changed older entries in the next cycle,
  handles deleted/empty gaps, and reports integers only.
- Filesystem processing and selection memory are bounded by `scan_limit`, and
  the implementation performs one directory enumeration per run. That
  enumeration is `O(total directory entries)`, not a bounded scan; no production
  large-directory latency or live worker-cadence claim is made.
- Final commit-ambiguity RED was `3 failed, 1 passed in 17.99s`: both the
  acknowledged-then-raised commit and the pre-commit post-rename failure lost
  their final files, and no parent-directory fsync helper existed. Micro-GREEN
  was `4 passed in 16.13s`: a real second attachment commit followed by lost
  acknowledgement preserves its durable row and final file; a pre-commit
  failure preserves a rowless final until grace-period reconciliation; POSIX
  parent-directory fsync is explicit and Windows upload tests remain no-op safe.
- The strengthened frozen-cycle test now inserts lexicographically later `z*`
  files with mtimes strictly above the frozen cutoff before every subsequent
  run. It asserts the original five-entry snapshot completes in exactly three
  windows (`2, 2, 1`), both boundaries remain fixed until wrap, and changed old
  entries are revisited in the next cycle.
- WebApp size-preflight RED was one failed cabinet E2E scenario (`10.3s`): the
  oversized TXT proceeded through submission instead of showing a local error.
  GREEN was `1 passed in 14.3s`; the 20 MiB guard runs before `arrayBuffer()`,
  while backend size enforcement remains authoritative.

### Verification

All Python commands used only
`C:/Users/kiwun/Documents/ai/VPN/.worktrees/market-ready-cis-integration/.tmp/venv-auth-sessions/Scripts/python.exe`,
with this worktree's `portal_bot` as `PYTHONPATH` and worktree-local pytest
basetemp directories.

- Final backend regression across migrations, rehearsal, ticket repositories,
  account ownership, API/email recovery, support AI, and helpbot lifecycle:
  `199 passed, 186 subtests passed in 316.40s`.
- Independent-review focused backend regression: `16 passed, 92 deselected, 2
  subtests passed in 39.96s`.
- Changed Python module/test `py_compile`: `PASS`.
- Frontend copy guard: `10 passed in 0.81s`.
- `npm.cmd run lint`: `PASS` with zero errors and three pre-existing warnings in
  unrelated files.
- `npm.cmd run test:e2e:cabinet`: build and TypeScript `PASS`; final Playwright
  result `29 passed in 52.4s`. An earlier full run had `28 passed, 1 failed`
  because the unchanged desktop navigation locator timed out; the exact test
  then passed alone and again in the final full run. The independent backend
  review did not touch frontend code and did not rerun this prior evidence.
- `scripts/app_bot_parity_smoke.py`: `7 passed, 0 failed, 2 manual owner tests`.
- `scripts/check-links.py --report .tmp/task-c-link-check.md`: `PASS`, all 30
  link-contract checks passed.
- `git diff --check`: `PASS` with only LF-to-CRLF worktree conversion warnings.

Second independent-review final verification for the current amended candidate:

- Full Task C backend regression across migrations, cleanup/worker, account
  ownership/foundation, repositories, main-bot attachments, API/email recovery,
  support AI, and helpbot: `235 passed, 186 subtests passed in 536.19s`.
- Focused advisory-lock, quota, bind race, cleanup, telemetry, atomic failure,
  download, and recovery regression: `19 passed, 2 subtests passed in 35.20s`.
- Final cursor/wrap-focused cleanup/worker/API regression: `13 passed in 17.87s`.
- Frozen-cycle cleanup, directly affected worker wiring, upload admission lock,
  quota cleanup, and post-rename DB-failure regression: `15 passed in 16.70s`.
- Final ACK-loss/pre-commit-orphan, reconciler, worker wiring, upload quota,
  advisory-lock, telemetry, and staging regression: `24 passed in 74.58s`.
- Final strict finalization-order selector (`replace`, parent fsync, real second
  attachment commit), rowless grace cleanup, POSIX helper, and frozen cycle:
  `4 passed in 14.99s`.
- Changed Python module/test `py_compile`: `PASS` using only the pinned Python.
- `npm.cmd run lint`: `PASS` with zero errors and three pre-existing warnings in
  unrelated files. `npm.cmd run build`: compile and TypeScript `PASS`.
- `npm.cmd run test:e2e:cabinet`: fresh production build plus `29 passed in
  1.0m`; the oversized preflight scenario passed in `8.3s`, and no Task C E2E
  listener remained afterward. Lint remained zero errors with three unrelated
  pre-existing warnings.
- Frontend text integrity/copy guards: `10 passed in 1.38s`. Link contract check: `PASS`, all
  30 checks passed; the final repeat report is
  `.tmp/task-c-final-ack-loss-link-check.md`.
- Artifact guard initially reported only local test/build output (`__pycache__`,
  `.pytest_cache`, `webapp/out`, and one test SQLite file). After scoped removal
  inside this worktree, the repeated guard was `PASS`.
- Base-diff plus untracked secret-pattern gate: `PASS`; no private key or known
  live credential format found. No external or live-system check was run.

### Rollback And Manual Gates

Rollback disables new attachment staging/binding at the application layer and
returns the WebApp to the rolling-compatible client revision. The additive
columns and indexes remain in place so bound history is not destroyed; operators
must not bulk-delete bound rows, legacy null-expiry rows, or attachment files.

- `MANUAL_OWNER_TEST`: measure production PostgreSQL additive DDL and index-lock
  impact before deployment.
- `MANUAL_OWNER_TEST`: prove backup/restore with redacted before/after bound,
  unbound, and dangling attachment counts.
- `MANUAL_OWNER_TEST`: exercise real PostgreSQL concurrent create, reply, and
  retry binding plus cross-process same-owner upload count/byte admission,
  including deterministic losers with no duplicate ticket or message mutation.
- `MANUAL_OWNER_TEST`: verify cookie, bearer, and Telegram initData attachment
  download through the production reverse proxy.
- `MANUAL_OWNER_TEST`: sample old private/non-private history and the complete
  owner/admin/recovery/missing-file response matrix.
- `MANUAL_OWNER_TEST`: verify the supervised support attachment cleanup worker
  is running at the configured production cadence and review redacted integer
  counters for expired, orphan, malformed-name, and missing-file outcomes.
- `MANUAL_OWNER_TEST`: measure one-pass support-upload directory enumeration and
  cleanup-job latency against the real production directory size; local tests
  prove bounded selected processing/memory, not bounded enumeration time.
- `MANUAL_OWNER_TEST`: simulate PostgreSQL commit acknowledgement loss and POSIX
  power loss around file rename, parent-directory fsync, and row commit; verify
  durable row-plus-file preservation and grace-delayed rowless-orphan cleanup.
- `NOT_REQUESTED`: live-system mutation, deploy, push, merge, physical-device,
  current-origin, brain-origin, and RU-origin proof.

### 2026-07-15 Manual-Gate Addendum

- `PASS`: production reverse proxy rejected missing, invalid bearer, invalid
  Web token, invalid cookie, and invalid Telegram initData on a private
  attachment route with `401`; allowed CORS preflight returned the exact app
  origin with credentials, an untrusted origin was rejected, and HTTP redirected
  to HTTPS.
- `BLOCKED_BY_ACCESS`: a valid cookie/bearer/initData attachment download could
  not be proven because no valid session material was extracted and production
  contained no attachment fixture. Browser/session secrets were intentionally
  not harvested.
- `NOT_APPLICABLE_NO_FIXTURES`: production had zero support attachment rows and
  zero private `support/*` references. One historical non-private media
  reference remains and must be preserved by additive migration.
- `PASS`: the supervised `portal-worker` was manually restarted, returned
  active with a new process ID, and had no fresh journal error. This proves the
  current worker supervision path, not candidate deployment.
- `PASS`: a real ext4 scratch run covered 50,001 entries, frozen mtime windows,
  file and parent-directory fsync, and process termination after durable rename.
  Physical datacenter power removal remains `NOT_RUN_SAFETY`.
- Cleanup now fsyncs the upload directory after successful POSIX unlink batches;
  a failure increments the existing integer `file_errors` counter and preserves
  the frozen file-window cursor so a deletion that reappears after power loss is
  retried before the scan advances.
- A long-lived `portal-helpbot` idle-in-transaction session was observed. It was
  not killed or restarted because that production mutation was not authorized;
  treat it as a separate P1 operator incident.

See `13-live-postgres-support-gates.md` for the redacted cross-gate summary.
