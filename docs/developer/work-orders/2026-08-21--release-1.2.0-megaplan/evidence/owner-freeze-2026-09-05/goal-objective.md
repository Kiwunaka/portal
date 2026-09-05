# Goal at owner freeze — 2026-09-05

Historical objective preserved verbatim below. Execution is paused by the owner for replanning; this is not release completion. Later decisions and exact candidate evidence take precedence over the original objective wording. Product goal tool remains `blocked`; no replacement goal was created.

POKROV 1.2.0 MEGA-RELEASE. Исполнить пять приложенных планов: REL+logging (REL/OBS), Operator Center v2 (OC), frontend (FE), marketing (MKT), FRKN (FRKN). Все backlog/acceptance/DoD входят в scope.

Аудиты — датированные inputs/evidence. Каждый срез сверять с AGENTS.md, canonical owners и текущим runtime; старое evidence≠PASS. Не делать big-bang, dual-write/второй truth; сохранять repo lanes/dirty work. Production/external actions — только по отдельной авторизации.

Индекс: I0 NOT_STARTED, I1 BASELINED, I2 IMPLEMENTED, I3 VERIFIED_LOCAL, I4 CANDIDATE_PROVEN, I5 RELEASE_PROVEN. По ID вести owner/repo, dependencies, exact candidate/environment/origin, evidence, blocker, rollback/docs. SKIPPED/ATTESTED/BLOCKED≠PASS. Старт: overall 0%; Gates 0/6; REL 0/20; OBS 0/6 и 0/90; OC 0/7; FE 0/11 и P12 0/64; MKT 0/10 и 0/7; FRKN 0/4 и AWG 0/10; RC 0%.

Порядок:
00 BASELINE/FREEZE — exact SHA/version/deploy, dependency/capability matrix, единый release contract/ledger, один owner/destination; admin.pokrov.space+portal/adminapp каноничны, дубли freeze.
01 RELEASE/SUPPLY — signed manifest app/portal/core/schemas/commercial/artifacts/SBOM/provenance; generated contracts; same-byte promotion; protected branches/CI/CODEOWNERS/signing; STOP-SHIP/P0 tests: payments, app/core CI, Windows non-elevated/clean TUN-DNS, updater identity.
02 STATE/CORE — разрез god-модулей по owners; generation-safe reducer/presenter; connected только после DNS+egress; deterministic stop/recovery/migrations; ABI/capabilities/events и platform/security/reproducibility/lifecycle gates.
03 PLATFORMS — Windows user UI+service/authenticated IPC/journal/rollback/matrix; Android thin VpnService/concurrency/MTU/direct-store/privacy/OEM matrix; Linux beta: non-root UI+daemon/polkit/NM/resolved/nft/packages/distro matrix.
04 OBS — OBS-001…090: 4 data modes, envelope/error/correlation, bounded secret-free logs, planted-secret gate, diagnostics, previewed encrypted bundle без plaintext, isolated ingest, support console/RBAC/audit/retention, release health/alerts, PB-01…14. Mandatory 1.2 не переносить.
05 PORTAL — modular-monolith/strangler APIs; immutable idempotent payment truth/callback/outbox; async DB/shared HTTP; versioned support/OBS/release contracts.
06 COMMERCIAL — MKT-000…400: legal/seller/channel fail-closed; server Offer+signed token+atomic quota/order; revision/readback/rollback; campaign→payment→entitlement→first-connect→retention/refund; capacity 300/auto-pause; honest urgency/claims.
07 OC — OC-000…640: API v2, HttpOnly/CSRF/OIDC, backend RBAC/JIT/step-up/action-intent, SDK/fingerprints/CI; 7 workspaces/screen contracts; strangler/redirects/authenticated proof/rollback.
08 FE — PR-00…10 и P12 P0/P1: acquisition→permission→verified protection, typed UI truth, adaptive/reduced motion, downloads/checkout, a11y/perf/analytics/CI/E2E/device matrices/flags. ABI v3 не блокирует adapter; Linux не обещать без proof.
09 MKT — MKT-500…900/stages 0–6: legal/evidence copy, lifecycle/suppression, first-party attribution, net revenue/capacity. Pilot: expired paid 7–30d, 10% 3/6m, cap20, 72h, ≤2 creatives, green/yellow, postmortem. Broad RF ads — legal+authorization only.
10 FRKN — traffic proof/multi-family/immutable artifacts. AWG2 via current Core/sing-box: schema/license/fixtures, fail-closed converter, Android/Windows interop, MTU/routes/modes/network/power/rollback/RU canary; затем Hysteria2. Monitor AWG3/Gecko/Mimic; reject Dopamine fork/second Xray/raw configs/secrets/mutable APK/raw protocol UI.
11 RC — Gates E/F: migration/install/update/chaos/security/privacy/payment/a11y/perf/device/origin/rollback evidence; same-byte rollout/kill; docs/exact labels. Stable запрещён при P0, false-green, leak/rollback, secret, legal/commercial/auth/RBAC/action-intent/provenance failure.

DONE: REL DoD, OBS mandatory, OC oracle, FE P0/P1, MKT-000…900+pilot и FRKN evidence-based GO/NO-GO закрыты; no P0; exact candidate proven; rollback/docs/ledger current; публикация отдельно авторизована.
