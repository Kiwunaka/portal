# Матрица решений

Статус: `EXPERIMENTAL`, advisory

Дата: `2026-07-22`

Приоритеты означают порядок исследования/исправления, а не разрешение на deploy.
Любой runtime candidate проходит точные client, device и RU-origin gates.

## Core и client

| Компонент | Решение | Приоритет | Что именно делаем | Gate |
| --- | --- | --- | --- | --- |
| POKROV UI/bootstrap | `KEEP` | — | Оставляем собственный app-first client | Existing client tests; без замены UI |
| Android `VpnService` + TUN host | `KEEP_AND_PORT` | P0 | Сохраняем ownership, переносим interface bindings на libbox 1.13 | Android unit/build + physical-device TUN proof |
| Apple packet tunnel | `KEEP_AND_PORT` | P0 | Сохраняем provider/flow, обновляем libbox bindings | Source build; signing и device proof остаются manual gates |
| Hiddify Core `v3.1.8` | `TEMPORARY_BRIDGE` | P0 | Не расширять; оставить только пока новый adapter не пройдет parity | Bounded removal milestone |
| Hiddify Core `v4.1.0` | `REJECT_AS_TARGET` | P0 | Не делать in-place update и не форкать | Breaking API + `LEGAL_REVIEW_REQUIRED` NonCommercial term |
| Upstream sing-box/libbox `1.13.x` | `MIGRATE_TO` | P0 | POKROV-owned reproducible builds и thin adapters | Config parity, TUN, crash/reconnect/soak, license review |
| Xray second engine | `DEFER` | P2 | Не добавлять ради уже написанного backend profile | Только измеренный gap + lifecycle/update/security budget |
| `advanced_fallback_core: xray` | `REMOVE_OR_HIDE` | P0 | Canonical contract должен совпасть с shipped capability | Contract and UI tests |
| `xray-json` assignment | `BLOCK_FOR_CURRENT_CLIENT` | P0 | Capability-aware manifest selection | Client никогда не получает неподдерживаемый format |
| Legacy sing-box 1.8 config | `MIGRATE` | P0 | TUN, DNS, route actions, block, WireGuard/endpoints | Validate against exact embedded binary |
| Desktop mixed listeners | `REMOVE_OR_AUTHENTICATE` | P0 | Удалить, если не нужны; иначе random per-session auth/lifecycle | Local hostile-process/browser regression tests |
| Runtime artifact downloader | `FIX` | P0 | Verify expected SHA-256/digest before extract/sync | Corrupt/wrong digest must fail closed |
| Build provenance | `ADD` | P0 | Pin commit/toolchain/tags; retain SBOM and hashes | Rebuild produces attributable candidate |

## Транспортные контуры

| Контур | Решение | Приоритет | Роль | Причина/ограничение |
| --- | --- | --- | --- | --- |
| VLESS + REALITY + Vision/RAW | `KEEP_BASELINE` | P0 | Дешевый TCP baseline | Работает не везде; нельзя единственным маршрутом |
| Generic donor `yahoo.com` | `REMOVE_DEFAULT` | P0 | — | Общий внешний failure/kill switch; reachability меняется |
| Per-node REALITY target/SNI | `FIX` | P0 | Self-steal/операторски проверенный target | Нужен reachability + TLS compatibility probe с самого node |
| gRPC over 443 | `KEEP_CANARY` | P1 | Compatibility contour | Нет доказательств для названия `primary` |
| Naive H2 | `ADD_CANARY` | P1 | Независимый TCP/browser-stack contour | Core 1.13, single tunnel first, memory/perf/traffic-shape soak |
| Naive QUIC/H3 | `DEFER` | P2 | Comparator | Свежие полевые сообщения об instability/QUIC filtering |
| Hysteria2 | `ADD_CANARY` | P1 | Независимый UDP/QUIC contour | Никогда не sole path; carrier-dependent QUIC blocks |
| AmneziaWG | `SPIKE` | P2 | Второй UDP comparator | Интеграционная цена и недостаток POKROV exact evidence |
| AnyTLS | `SPIKE_IF_NEEDED` | P2 | TCP comparator | Не нужен до результатов Naive |
| XHTTP | `DEFER_CLIENT_ROLLOUT` | P2 | Возможный Xray-only contour | Сейчас backend/client contract сломан; свежие failure reports |
| Cloak | `DROP_FROM_CORE_PLAN` | — | — | Отдельный stack, слабее текущего priority set, блокировки hoster/traffic |
| TUIC | `DROP_FROM_NEAR_TERM` | — | — | Старый официальный release и пересечение роли с Hysteria2 |

## Маршрутизация и инфраструктура

| Компонент | Решение | Приоритет | Что меняем | Gate |
| --- | --- | --- | --- | --- |
| Managed materialized profiles | `KEEP` | P0 | Добавить explicit core/schema capabilities | Authenticated delivery + exact-core validation |
| Per-carrier/cohort rollout | `KEEP` | P0 | Добавить region/time/network evidence dimensions | Deterministic selection + rollback |
| RU bridge detour | `KEEP_MECHANISM` | P1 | Multi-endpoint, multi-ASN, expiring eligibility | Fresh payload probe, no static whitelist claim |
| Hardcoded Yandex/VK whitelist premise | `REMOVE` | P0 | Не связывать cloud ASN с consumer service brand | Only measured endpoint eligibility |
| Single ingress/egress | `AVOID` | P1 | Разнести failure domains и rotation | Provider/ASN failure simulation |
| WARP as censorship dependency | `REMOVE_FROM_CORE_PATH` | P1 | Можно оставить отдельной optional egress feature | Не считать обходом блокировок/доступом к RU by default |
| Remnawave/3x-ui migration | `REJECT_WITHOUT_CASE` | — | Не менять control plane по Habr-инструкции | Нужен отдельный TCO/capability migration case |

## Measurement

| Проверка | Сейчас | Решение | Acceptance criterion |
| --- | --- | --- | --- |
| DNS/TCP/TLS stages | Есть | `KEEP` | Stage status остается честным `pass/fail/not_run/not_applicable` |
| 64 KiB GET | Есть, считается число байт | `EXTEND` | Несколько payload sizes + expected SHA-256 |
| Upload | Нет | `ADD` | Подтвержденный body hash/length на controlled endpoint |
| Exact managed manifest | Нет | `ADD` | Fetch через authenticated production-equivalent API path |
| Exact shipped core | Нет | `ADD` | Запуск candidate artifact и его schema validator |
| Exact TUN/split route | Нет | `ADD` | DNS и traffic проходят ожидаемым route mode; RU/direct assertions |
| Reconnect/network handover | Не release gate | `ADD` | No stale session, DNS restored, old TUN closed |
| Concurrency/traffic shape | Нет | `ADD` | 1 и N streams/sessions; protocol-specific counters retained |
| IPv4/IPv6 | Частично есть | `KEEP_AND_EXTEND` | Отдельный verdict по семье через exact transport |
| Carrier/region/time | Недостаточно | `ADD` | Evidence keyed by origin, carrier, region and time bucket |
| TCP connect scan | Доступен как signal | `NEVER_RELEASE_PROOF` | Не повышает transport в `PASS` без payload |

## Локальные инструменты, которые не надо смешивать с core

| Инструмент | Решение | Граница |
| --- | --- | --- |
| zapret | `OPTIONAL_RECOVERY` | Windows/router power-user surface, отдельный install/update/lifecycle |
| GoodbyeDPI | `DROP_FROM_PRODUCT_CORE` | Старый release; локальный DPI workaround, не managed VPN transport |
| Runet censorship bypass extension | `OUT_OF_SCOPE` | Browser-only; не покрывает device tunnel |
| TURN/WebRTC service abuse | `REJECT_PRODUCTION` | Third-party accounts, CAPTCHA, ToS/rate-limit and abrupt breakage |

## Конкретные work packages

### WP0 — capability truth

Owners: platform manifest selection + client product contract.

- backend выбирает format только из advertised client capabilities;
- `xray-json` никогда не попадает текущему build;
- Xray fallback скрыт из current product truth;
- tests покрывают carrier/cohort/operator-lab paths.

### WP1 — core adapter and supply chain

Owner: отдельный `POKROV-app` worktree.

- ADR фиксирует direct sing-box/libbox boundary и Windows ABI;
- source commit, Go/gomobile versions и tags pinned;
- downloader сверяет digest до extract;
- SBOM/license bundle сохраняются рядом с candidate;
- Android/iOS host interfaces компилируются против 1.13;
- Windows adapter имеет минимальный versioned ABI.

### WP2 — config migration

Owners: platform config builders + client TUN overlay.

- один schema version/capability contract;
- legacy 1.8 fields удалены;
- config валидируется candidate binary в CI;
- route modes `all`, `all-except-RU`, selected apps и DNS behavior проходят
  focused tests;
- rollback на последний совместимый manifest доказан.

### WP3 — local listener hardening

Owner: desktop runtime.

- документирован каждый loopback port и consumer;
- неиспользуемые listeners отсутствуют;
- используемые listeners имеют random session secret и закрываются при stop/crash;
- hostile local client не получает proxy access без secret.

### WP4 — exact RU probe

Owners: platform probe contract + client probe harness.

- controlled endpoint отдает deterministic payload и принимает deterministic upload;
- manifest/profile/core/device IDs привязаны к evidence без secrets;
- hash, upload, DNS, split route, handover, concurrency и address families;
- distinct evidence для `current-origin`, `brain-origin`, `RU-origin`;
- `not_run` никогда не превращается в pass.

### WP5 — transport canaries

Owner: network rollout.

Порядок: Naive H2 → Hysteria2 → только затем AWG/AnyTLS/XHTTP comparator.
Каждый contour получает отдельные ingress/egress, SLO, cohort, expiry и one-click
rollback. Никаких автоматических default promotions по единичным форумным отчетам.
