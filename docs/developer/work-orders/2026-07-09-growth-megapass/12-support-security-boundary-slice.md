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
