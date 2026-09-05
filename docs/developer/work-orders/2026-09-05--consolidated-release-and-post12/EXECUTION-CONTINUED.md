# Продолжение исполнения R12 — 2026-09-05

Статус: `ACTIVE / PARTIAL / RELEASE_BLOCKED`. Команда владельца «Делай план до конца»
исполняется; этот документ фиксирует промежуточный результат и не закрывает 83 ID.
Он дополняет [предыдущий отчёт](EXECUTION-LOCAL.md), где commit/binding/PostgreSQL
статусы отражают более ранний момент. Нового candidate, push, merge или deploy нет.

## Полученные результаты

- Core source: два локальных коммита `9476df5` и
  `3f52efd4635218967cc84d58cb06b2fa593fd563`. Первый привязывает endpoint proof к
  конкретному вызову; второй делает то же для selector/urltest group. Новый путь
  захватывает выбранный proxy leaf и отклоняет смену выбора/runtime, timeout,
  direct и циклический selector. Общий URL-test cache не подтверждает здоровье.
- PASS: `go -C engine/sing-box test -race -count=1 ./daemon ./experimental/libbox`
  и `pwsh -NoProfile -File scripts/test.ps1 -GoExecutable E:/POKROV-tools/go1.25.13/go/bin/go.exe`.
  Logs: `E:/r12-group-probe-race.log`, `E:/r12-group-core-full.log`.
- PASS: Android и Windows Core собраны дважды, обе пары совпали побайтно.
  Финальные build trees, SBOM и JSON evidence: `E:/r12-artifacts/final`.
  Точный manifest клиента — `E:/r12client/config/runtime-artifacts.seed.json`;
  build evidence retained также в client docs/operations/evidence/2026-09-05-r12-core-binding/final.
  SBOM warnings о недостающих license/version metadata не являются license clearance.
- PASS: AAR содержит четыре ABI, `probeEndpoint`, `probeSelectedOutbound` и
  consumer rules, сохраняющие методы при R8. Оба Android flavor JVM suites прошли:
  `gradlew.bat :app:testDirectDebugUnitTest :app:testStoreDebugUnitTest`.
  Log: `E:/r12-final-android-tests.log`. Это не packaged/device proof.
- PASS: `pwsh -NoProfile -File scripts/test-windows-core-proxy-only.ps1 -CoreRoot E:/r12-artifacts/final/core-windows-first` — 100 start/stop cycles без смены системных маршрутов.
  Log: `E:/r12-final-windows-proxy.log`.
- PASS: client `validate-seed.ps1 -CoreRoot E:/r12core-implementation -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start`.
  Log: `E:/r12-final-seed.log`. Synthetic release-input SHA обновлён вместе с
  runtime binding; historical candidate manifests не изменены.
- N02 local correction: native regression воспроизвёл удаление старого staged
  profile при отказе SecureFile после замены. SecureFile перенесён на pending file
  до atomic rename. После исправления CTest 5/5: runtime, security, protocol,
  events, crash-profile. Logs: `E:/r12-windows-stage-before.log`,
  `E:/r12-windows-native-ctest.log`. Harness `E:/r12-windows-tests` использует
  оригинальные CMake service targets и compiler settings. Служба на host не менялась.
- B05 PASS: `python -u -B -m pytest -p no:cacheprovider tests/test_public_checkout_postgres.py -q`
  с disposable loopback PostgreSQL — **8 passed, 78.98 s**.
  Шесть HTTP cases используют два backend PID: intent/base quote × success,
  timeout-after-local-commit, late terminal order update. Один order/provider call.
  Два commercial cases проверяют повтор одного резерва и конкуренцию за offer cap.
  Это не fulfillment/live-provider callback proof. Runner `E:/r12-run-postgres-checkout.py`
  передаёт локальный URL через env, не печатая credential; log `E:/r12-postgres-checkout.log`.
- Fixture corrections: PostgreSQL session timezone явно UTC для UTC timestamp
  models; fixture campaign cap не меняется в обход pilot approval. В concurrency
  oracle ограничена квота offer, как в существующей serial test. Assertions не ослаблены.
- PASS: `python -u -B -m pytest -p no:cacheprovider tests/test_admin_ops_api.py tests/test_admin_payments_api.py -q` — **52 passed, 319.77 s**.

## Общий local quality gate

Команда: `python -u -B scripts/release_1_2_local_quality_gate.py --platform-root C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start --client-root E:/r12client --core-root E:/r12core-implementation --evidence-dir E:/r12-final-quality --keep-going`.

Первый результат — `FAIL`: только marketing responsive остановился на networkidle
из-за внешнего catalog fetch без deadline. Остальные шаги прошли, включая client
analyze/widget/seed/docs, cabinet lint/build/E2E, marketing build/SEO, admin build
и 9 static performance stop budgets. Некоторые целевые performance targets не
достигнуты: hard-budget PASS не переименовывается в target compliance.

Исправлен F02/F06 local slice: на home/install catalog reads deadline 8 секунд.
Configured approved links сохраняются; без них home ведёт на install, а install
показывает недоступность вместо бесконечного loading. Responsive harness блокирует
внешние запросы; добавлен stalled catalog oracle для обеих страниц. Результат
повторного `npm.cmd --prefix marketing run check:responsive` — PASS, exit 0,
log `E:/r12-final-responsive-recheck.log`. Исходный failed gate не переписывается.

## Границы и следующая очередь

- `G06 BLOCKED_BY_ACCESS`: API rules/protection приватных portal/client вернул 403.
  Latest public release readback: release-index `v1.1.6`, Core `v1.0.3`.
  [Сохранённый readback](evidence/governance-readback.json). 404 protection не объявлен
  доказательством наличия защиты; пустые rulesets публичных repos сохранены как readback.
- N01 целиком ещё открыт: server revision/digest → fetched → staged → service-effective
  readback. N02 целиком открыт: durable last-known-good/entitlement rollback и
  packaged AWG31→AWG2→AWG31. Локальные исправления выше не закрывают эти требования.
- N03/N04 local proof улучшен; exact route-mode/app coverage и packaged runtime
  остаются отдельными gates. Не переносить candidate.33 device PASS на новый Core.
- G04 hosted CI для нового source tuple не исполнен. Signing/new candidate,
  Windows VM, physical Android, RU-origin, provider/refund/reconciliation и rollout
  требуют своих exact environments/guards. Никаких production mutations не было.
- Остальные R12 строки остаются queued до проверки по текущей реализации.
  ATS/CR/WP/HAPP/shortlink идут по зависимостям postrelease плана; public activation,
  новая когорта, spend и Linux public scope не следуют из local implementation.

Рабочие source changes platform/client пока не закоммичены. Core — два локальных
source commits; push/merge отсутствуют. Старые worktrees и release artifacts сохранены.

## N01B — Windows stage/start content identity

Scoped source result: IMPLEMENTATION_VERIFIED / I3 for local Windows service
content identity, not all N01. The before regression in
`E:/r12-identity-before.log` failed because staged/effective digests were absent.
Service and native UI now negotiate ProfileIdentity capability bit 5. The exact
stage-request SHA-256 includes flags and bundled rulesets. Connect carries that
digest, rejects replacement/stale intent before start, and effective digest is
published only after egress and transaction commit. Stop/failure clears effective;
failed atomic staging preserves the prior acknowledged digest. Native parsing
is atomic and rejects malformed/mismatched proof; UI polls remain bound to their
own intent. The Flutter snapshot carries bounded digests and a fixed local origin.
Server assignment revision is not inferred from a hash or local counter.

PASS commands (client cwd unless specified):
- Native: CMake from Visual Studio BuildTools, `--build E:/r12-windows-tests/build
  --config Debug`; `ctest --test-dir E:/r12-windows-tests/build -C Debug
  --output-on-failure` — 8/8, exit 0. Includes isolated user-process named-pipe
  integration, not an SCM install. `E:/r12-identity-ctest.log`.
- `flutter test test/runtime_engine_test.dart` from packages/runtime_engine —
  78 passed, 1 existing exact-DLL opt-in skip. `E:/r12-identity-flutter-test.log`.
- `flutter build windows --debug` from apps/windows_shell — exit 0.
  `E:/r12-identity-windows-debug-final.log`. This is a local debug build,
  not a packaged/signed release candidate and was not launched as a VPN.
- `flutter analyze` from client root — no issues, exit 0.
- `pwsh -NoProfile -File scripts/run-tests.ps1` — workspace Flutter and both
  Android flavor gates passed. `E:/r12-identity-workspace-tests.log`.

Protocol consumer and producer land together. Mixed old/new UI/service is
intentionally incompatible until a matching bundle is installed; rollback must
restore both. Core ABI2 and retained artifacts/releases remain unchanged.
Remaining N01: explicit server/fetched lineage and Android stage/effective
identity, then exact candidate Windows VM and physical Android proof.

## N01C — Android stage/start identity and atomic file replacement

Local source now persists a content/options digest and binds direct,
consent-delayed and Quick Settings service starts to it. The service validates
saved metadata and file bytes before replacing a live session, then pins the
verified string. Same-path replacement cannot inherit an old intent. Deferred
consent tokens compare digest as well as path; completion of an old request
cannot release a newer request. Missing legacy digest requires refresh through
the app. Staging different input invalidates old egress proof; stop/failure clear
active identity. Public mismatch copy gives the existing refresh/reconnect path.

The observed N02 file gap was delete-before-rename. Staging now restricts the
pending file, then uses Android OS atomic rename; the old target is preserved if
rename fails. Preferences follow the file commit; an interrupted two-part write
fails digest validation. Physical filesystem crash/rename-failure proof remains
MANUAL_OWNER_TEST; this is not a durable entitlement-aware last-good rollback.

PASS: both Android flavor JVM suites, exit 0, 162 tasks,
`E:/r12-android-identity-final.log`. PASS: `pwsh -NoProfile -File
scripts/run-tests.ps1`, full client workspace Flutter and both Gradle gates,
`E:/r12-android-identity-workspace-final.log`. The latter gate preceded the Dart
source-lineage addition below. No new APK/release candidate was built or installed.

## N01D — fetched server revision to acknowledged/effective digest

Managed bootstrap and signed emergency envelopes now carry a typed source
revision/origin on their materialized payload. Runtime snapshots keep fetched,
staged and effective source separate. Only an acknowledged digest can associate
an upstream source with a staged input; effective source additionally requires
running state, successful egress and matching active/staged/acknowledged digest.
A stage rejection can leave fetched B while A remains staged/effective. Delayed
A proof cannot confirm B. Process restart does not infer source authority from
a local hash or persisted filename. Server desired assignment is known only at
the fetch instant; future changes require another fetch.

PASS: `flutter test test/runtime_engine_test.dart` from packages/runtime_engine:
79 passed, one existing exact-DLL opt-in skip; `E:/r12-source-lineage-runtime.log`.
PASS: `flutter test test/app_first_runtime_bootstrap_test.dart` from
packages/app_shell: 86 passed; `E:/r12-source-lineage-bootstrap.log`.
Initial runs exposed a misplaced method parameter and missing test import, both
corrected before these passes. An initial root-level Flutter test invocation had
no pubspec and was rerun from the actual package. No failed run is counted as PASS.

Remaining N01 I4: exact candidate Windows VM/physical Android AWG31→AWG2→AWG31,
including server assignment and native readback. O03 operator projection and V02
safe diagnostic export of source lineage remain separate platform slices.

## C03A — standalone managed-profile lifecycle owner

Client behavior/binding changes were committed locally as
`8176c3b66fd64e5ad0868cd441b99f02aa4e634b`. The subsequent pure extraction is
`cebbe851a7d92d3751de9d552e3470b4f63e3382`. `ManagedProfileLifecycle` now owns
dirty/local revision, coalesced host invalidation, deadlines and disposal.
Shell delegates through a narrow host callback; no `part` was added. The root
shrunk by 93 lines. This is a maintainability boundary, not a speed claim.
Existing connection, presentation, support and update coordinators remain.
The full C03 sequence is not declared complete from this one extraction.

PASS: `flutter test test/managed_profile_lifecycle_test.dart
test/pokrov_seed_app_test.dart`, 173 tests (`E:/r12-profile-lifecycle-tests.log`).
PASS: client-root `flutter analyze` and explicit-root `validate-seed.ps1`
(`E:/r12-profile-lifecycle-analyze.log`, `E:/r12-profile-lifecycle-seed.log`).
The earlier N01D analyze/seed also passed with corresponding
`E:/r12-source-lineage-{analyze,seed}.log`. Source/binding commits are local;
no push, merge, deployment or new release candidate exists.

## B07A — HTTP/resource inventory

[Retained inventory](evidence/http-session-inventory.json) lists 15 direct
`aiohttp.ClientSession` constructor sites with file SHA and enclosing function.
They cover Telegram operations, legacy panel usage, the bot-to-owned-API payment
hop, email/mirror/news, panel instance lifecycle and OIDC. A missing constructor
timeout in that inventory does not mean an unbounded request: request-level
timeouts were inspected separately. The authenticated panel client owns its
cookie session per instance; it must not be combined with unrelated callers.

Payment providers already use lifespan-owned `PaymentHttpRegistry` with bounded
connector pools, connect/read/total timeouts and response limits. Payment DB work
uses the existing bounded worker path and records queue-wait/duration counters.
PASS: `python -u -B -m pytest -p no:cacheprovider tests/test_payment_db_runtime.py
tests/test_payment_http_registry.py -q`, 11 tests, 5.15 s
(`E:/r12-payment-resource-gates.log`). It covers event-loop responsiveness under
blocked synthetic DB work and the managed HTTP resource contract.

Production pool wait, event-loop lag and payment outbox age were not measured.
No blanket lifespan conversion, connection pooling rewrite or async ORM rewrite
was made without a measured bottleneck. B07 remains partial.

## O03/V02 data-source decision

Current User360 adapts Product Event rows into bounded opaque attempt/session
references. It does not receive the client's new source/digest association.
Operational release-health ingest deliberately excludes individual correlation
and profile data; support bundles follow consent, encryption, server validation,
case-bound access and retention. A new automatic account-bound connection report
would be a different collection contract. The owner was asked to choose between
existing opt-in support evidence (UNKNOWN without it) and that new report.
No new collection or plaintext profile export has been introduced while this
choice is pending. Server-side bundle validation already derives a closed L1
summary; a future opt-in extension can reuse that boundary rather than inventing
individual release-health telemetry.

## N06A — bounded automatic retry backoff

Client `61d1838bebff9cf15f09959d5ddecefed946d514` replaces the fixed 250 ms
location retry delay with 250/500 ms backoff plus 0–250 ms jitter. Existing
maximum two attempts, 15-minute/eight-entry negative cache, manual-node boundary,
unavailable-proof handling and owner-generation cancellation are retained.
No new transport selector, broker or public AWG behavior is introduced.
PASS: the existing automatic Android failed-node/quarantine/retry widget scenario,
`flutter test test/pokrov_seed_app_test.dart --plain-name 'automatic Android
connect quarantines a confirmed failed node and retries'`, 1 passed.
`flutter analyze --no-pub` from app_shell and explicit-root client
`validate-seed.ps1` passed. Logs: `E:/r12-failover-backoff-{tests,analyze,seed}.log`.
No fleet/WAN performance or full N06 matrix is inferred from this local check.

## G03A — declared evidence-input classifier

[Classifier](classify_evidence_inputs.py) separates path hints for documentation,
harness, copy, API/schema, profile/policy, Core/runtime, packaged dependency and
deployment changes. Unknown paths require manual classification. Reuse comparison
requires artifact/configuration/toolchain/oracle/scope SHA-256 plus exact
environment and origin; additional declared dependency hashes are also compared.
Equal supplied inputs return only `DECLARED_INPUTS_MATCH_REVIEW_REQUIRED`, never
release PASS. The utility cannot establish completeness or authenticity of a
receipt and cannot turn a missing artifact into evidence.

PASS: `python -B -m unittest discover -s
docs/developer/work-orders/2026-09-05--consolidated-release-and-post12
-p test_evidence_inputs.py -v`, 4 tests. Collector change with unchanged runtime,
configuration/origin changes, missing inputs and unknown path handling are covered.
[Current change inventory](evidence/change-impact-current.json) retains actual
source file hashes and exact roots' base/HEAD context. Its preliminary
[earlier inventory](evidence/change-impact.json) remains retained. Candidate.33
runtime/device evidence is not granted reuse for the changed Core and host tuple.
The classifier is an audit helper in this work order, not a replacement for the
existing release orchestrator or an automatic promotion authority.

## Latest local handoff

See [HANDOFF.md](HANDOFF.md) and [exact commands/source/log hashes](evidence/handoff-local.json).
New client commit `4dbe2c6` rejects future cache timestamps and retains the 24-hour
bound; 5 tests, analyzer and seed passed. Platform product changes are now in
`917612f`, `5577bb7`, `bf72daa`, `7e8beab`. The latter two fix the observed hero
contrast failure and separate cockpit policy from final Gate F. Service/API and
browser checks passed. The retained whole-quality failure is not overwritten.
No new release candidate, push, merge or deployment occurred. Whole-plan status
is PARTIAL / RELEASE_BLOCKED; remaining source and physical gates are explicit.
