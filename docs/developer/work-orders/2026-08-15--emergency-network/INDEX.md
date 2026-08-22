# POKROV Emergency Network

Document class: `EVIDENCE`

Status: `RELEASED_WITH_MANUAL_GATES`

This record owns the released `1.0.10` wave only. Current 1.2.0 emergency and
FRKN gates require fresh exact-candidate evidence from the 1.2.0 megaplan.

Created: `2026-08-15`

## Goal

Добавить trial/paid-пользователям из РФ отдельный раздел **«Экстренная сеть
POKROV»** для ограниченной сети/БС. Клиент получает не слепую стороннюю
подписку, а подписанный POKROV-каталог максимум из 20 серверно проверенных
VLESS+REALITY резервов, сохраняет bootstrap и last-known-good offline и умеет
строить три reserve-first маршрута:

| Режим | Физический путь | Конечный выход |
| --- | --- | --- |
| Свободный доступ | устройство → резерв | резерв |
| Через POKROV | устройство → резерв → наша иностранная нода | наша иностранная нода |
| Усиленная цепочка | устройство → резерв → наш RU-хоп → наша иностранная нода | наша иностранная нода |

Цель включает platform/backend, adminapp, Android/Windows client, exact POKROV
Core 1.0.3 validation, synthetic БС/firewall proof, canary, release, deploy и
rollback. Она не включает обновление или переписывание POKROV Core.

## Owner Decisions

- Доступ: только активный `trial` или `paid`; постоянного free-доступа нет.
- География: cached server-derived RU eligibility без хранения raw IP плюс
  ручной режим `Ограниченная сеть`; текущий IP не является единственным gate.
- Основное имя: `Экстренная сеть POKROV`; карточки не получают ярлыки
  `публичный`/`внешний`.
- Спокойное раскрытие обязательно при первом входе и в справке: direct emergency
  exit может быть узлом согласованного внешнего пула и не управляется POKROV.
- Источник согласован с его разработчиком (`OPERATOR_ATTESTED`). Репозиторий
  GPL-3.0; POKROV использует его только как upstream data input, сохраняет
  attribution и не запускает сторонний код.
- Никакой профиль из источника не становится активным без нашей нормализации,
  проверки, подписи и server-side promotion.
- Emergency mode не поддерживает WARP. WARP не добавляется скрыто ни в один из
  трёх маршрутов.
- Synthetic firewall lab выполняется агентом; реальный российский LTE/БС
  проверяет owner позже.
- POKROV Core 1.0.3 и embedded sing-box 1.13.0 остаются production baseline;
  core-next/1.13.18 migration из этой волны исключены.

## Product Invariants

1. Каталог содержит от 4 до 20 активных резервов; меньше 4 не продвигается.
2. `reserve-01` — display ordinal, а не identity. Stable ID вычисляется из
   нормализованного endpoint material без публикации credentials.
3. При одном автоматическом обновлении нельзя заменить больше половины active
   набора без operator approval.
4. Источник не может задавать DNS, route rules, local inbounds, executable
   payload, arbitrary JSON, remote rule-set URL или `allowInsecure`.
5. Public locations API отдаёт только stable ID, страну, status, latency,
   freshness и поддержанные chain modes. UUID, host, SNI, Reality keys и raw
   config выдаются только в авторизованном managed profile.
6. Managed profile fail-closed проверяет entitlement, RU eligibility, endpoint
   freshness, unique tags, максимум три proxy hops, отсутствие циклов и точный
   foreign exit для режимов POKROV.
7. Endpoint и DNS для следующего хопа разрешаются через уже доступный reserve
   path либо безопасный pinned address; local DNS не должен быть скрытым
   обязательным условием.
8. Offline bootstrap/LKG не расширяет entitlement: expired user не получает
   рабочий emergency profile только из локального кэша.
9. Недоступность API или плохой snapshot не стирает последний подписанный
   рабочий каталог. Expired/revoked snapshot не продвигается молча.
10. Статусы различают `Работает`, `Проверяется`, `Недоступен`, `Данные устарели`,
    `Проверено в лаборатории БС` и `Проверено при реальном БС`. Последний статус
    невозможен без RU-origin physical evidence.
11. Synthetic lab не меняет глобальный firewall рабочего Windows-хоста и не
    выключает Hiddify, от которого зависит operator/Codex session.
12. Ни источник, ни его endpoint operators не получают POKROV account identity,
    Telegram ID, install ID, raw IP history или browsing telemetry.

## Queue

| Work order | Outcome | Depends on | Status |
| --- | --- | --- | --- |
| [WO-001](WO-001-source-contract-and-catalog-fixture.md) | Точный источник, зеркала, allowlist schema, sanitizer и безопасная tracked fixture | — | `DONE` |
| [WO-002](WO-002-ingestion-storage-promotion.md) | Snapshot/endpoint storage, probes, signing, staging→active, LKG и rollback | WO-001 | `DONE` |
| [WO-003](WO-003-admin-controls-and-observability.md) | Admin preview, promotion, disable, rollback, rejection reasons и freshness | WO-002 | `DONE` |
| [WO-004](WO-004-api-entitlement-and-profile-chains.md) | Safe locations API, entitlement/RU gates и три exact managed-profile chains | WO-001, WO-002 | `DONE` |
| [WO-005](WO-005-client-ui-and-offline-cache.md) | Emergency UX, disclosure, statuses, manual mode, signed bootstrap/LKG, no WARP | WO-004 | `DONE` |
| [WO-006](WO-006-exact-runtime-and-synthetic-bs-proof.md) | Exact Core 1.0.3, DNS/route/chain validation and isolated firewall proof on Android/Windows | WO-004, WO-005 | `CLOSED_WITH_MANUAL_GATE` |
| [WO-007](WO-007-canary-release-and-production.md) | Stable-direct artifacts, deploy, monitoring and rollback | WO-003, WO-006 | `CLOSED_STABLE_DIRECT_WITH_MANUAL_GATES` |

## Acceptance Oracle

Repository implementation is complete only when:

1. hostile/malformed source rows cannot affect config outside the allowlisted
   outbound fields and cannot enter active catalog;
2. at least four real candidates pass controlled auth plus deterministic
   download/payload probe and one signed active catalog can rollback to the prior
   version;
3. API projects no secrets while an entitled RU device receives an exact
   materialized profile for each of the three chain modes;
4. the exact embedded Core 1.0.3 validates and starts all three profiles, and
   negative tests reject cycles, missing hops, stale material and wrong exit;
5. Android and Windows show the same safe catalog, survive offline/API failure,
   reconnect without stale selection and never inject WARP;
6. an isolated lab proves RU control destinations remain direct/reachable while
   foreign control destinations and the normal first hop are blocked, after
   which at least one emergency route transfers a deterministic hashed payload;
7. operator can preview, promote, disable and rollback without editing secrets or
   deploying new client code;
8. exact candidate is committed/pushed on platform `master` and client `main`,
   deployed, current-origin checked and reversible.

`MANUAL_OWNER_TEST`: real Russian LTE/БС, carrier/region evidence and the label
`Проверено при реальном БС`. Without it, code and synthetic canary may be
`PASS`, but 100% RU rollout and the real-BS claim remain `PARTIAL`.

## Non-Goals

- POKROV Core upgrade, rebase, Hiddify migration or core-next.
- WARP in emergency mode.
- Permanent free tier or access for expired accounts.
- Blind import of 150/500 configs into the client.
- Third-party executable code, DNS/routing policy or advertising SDK.
- Claims that one SNI, hoster, ASN, operator or endpoint is permanently
  whitelisted.
- iOS/macOS/store release scope.
- Global firewall mutation on the operator workstation.

## Baseline

- Platform: `master@b093ccdb84161fbf701f86812e9945acedfb767c`.
- Active client: `main@95dc49db0c31284798252fca4d9efc7294a5c1d5`.
- POKROV Core: `main@69a74545101708e56183c92e31f2b4c7b2509884`,
  product version `1.0.3`, embedded sing-box `1.13.0`.
- Public app release: stable `v1.0.9`.
- Repositories were clean and matched their promotion refs when this wave was
  created.

## Evidence And Manual Gates

Evidence must distinguish `local`, `exact_candidate`, `current_origin`,
`brain_origin`, `ru_origin` and `physical_device`. Source feed health and a TCP
connect are signals, not tunnel proof. Do not retain raw credentials, source
payloads, user IPs or visiting history in docs or evidence.

Manual gate:

- name: `MANUAL_OWNER_TEST_REAL_RU_BS`
- owner: POKROV owner
- target: exact public Android candidate on real Russian LTE under observed БС
- required evidence: carrier, region coarse label, timestamp bucket, candidate
  version/hash, selected reserve stable ID, route mode, deterministic payload/DNS
  verdict, disconnect/restore result, redacted screenshot/log
- effect if unavailable: no real-BS badge and no 100% rollout claim

## Promotion Boundaries

Platform and active-client changes are committed separately. POKROV Core is
read-only in this wave. Backend/admin/runtime may be deployed with the worker
disabled so the exact isolated proof can use the production profile builder;
public client publication and cohort enablement still require WO-001..WO-006,
diff/secret checks and retained rollback to be green.

## Current State And Next Action

- Goal and owner decisions: fixed.
- Platform implementation and production deploy: complete through
  `master@c567787`.
- Client runtime implementation: `POKROV-app/main@43af4a6`; stable release
  metadata: `6f52ad6`. Public `v1.0.10` contains four production-signed Android
  APKs plus Windows setup/portable/manifest and `SHA256SUMS.txt`; GitHub reports
  exact size and SHA-256 for all eight assets.
- Production key material was created on brain with worker disabled. Only its
  public Ed25519 key entered the client build; private material stayed server-side.
- WO-001 parser/fixture/source audit: `DONE`; focused and docs contract checks
  pass and no upstream credential material is retained.
- Production catalog: active snapshot with 21 candidates, 13 healthy probe
  states and five published active reserves. Promotion/rollback remains
  available through the redacted admin surface.
- Final client verification: Flutter analyze PASS, 296/296 tests PASS,
  seed/docs contracts PASS, exact production signing PASS and live signed
  LDPlayer catalog/UI/topology proof retained on `E:`.
- Production release verification: public stable non-prerelease `v1.0.10`,
  GitHub asset digest PASS 8/8, five-repeat brain readiness PASS and authenticated
  plus anonymous runtime client-catalog smoke PASS for Android/Windows 1.0.10.
- `BLOCKED_BY_ACCESS`: LDPlayer and the normal POKROV control profile both fail
  the Reality data plane on this host network; the isolated firewall executor
  and controlled fixture are unavailable. No clean Windows network test was
  attempted because Hiddify must stay connected.
- `MANUAL_OWNER_TEST_REAL_RU_BS`: exact Huawei/RU-LTE proof remains required and
  forbids the real-БС badge. It is a post-release manual gate under the owner's
  stable-direct decision, not a fabricated PASS.
