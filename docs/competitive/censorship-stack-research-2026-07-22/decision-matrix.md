# Матрица решений

Статус: `EXPERIMENTAL`, advisory

Дата: `2026-07-22`

Приоритеты означают порядок исследования/исправления, а не разрешение на deploy.
Любой runtime candidate проходит точные client, device и RU-origin gates.

Лицензия/разрешение Hiddify для POKROV отмечены как `OPERATOR_ATTESTED`; confidential
grant не был прочитан и не является repository artifact.

## Core и client

| Компонент | Решение | Приоритет | Что именно делаем | Gate |
| --- | --- | --- | --- | --- |
| POKROV UI/bootstrap | `KEEP` | — | Оставляем собственный app-first client | Existing client tests; без замены UI |
| Android `VpnService` + TUN host | `KEEP_AND_PORT` | P0 | Сохраняем ownership, переносим interface bindings на libbox 1.13 | Android unit/build + physical-device TUN proof |
| Apple packet tunnel | `KEEP_AND_PORT` | P0 | Сохраняем provider/flow, обновляем libbox bindings | Source build; signing и device proof остаются manual gates |
| Hiddify Core `v3.1.8` | `ROLLBACK_BRIDGE` | P0 | Заморозить; оставить только до parity v4 | Bounded rollback milestone |
| Hiddify Core `v4.1.0` | `SOURCE_BASELINE` | P0 | POKROV-owned fork через compatibility adapter; upstream binary не ship-ить без patches | API/config parity, permission reference, TUN, crash/reconnect/soak |
| Released `hiddify-sing-box@0a02b77` | `PIN_AUDIT_BACKPORT` | P0 | Сохранить exact lineage; классифицировать отсутствующие upstream commits до `1.13.14`; backport security/correctness patches по одному | Commit manifest, provenance, config/protocol parity and soak; no blanket rebase |
| Hiddify desktop C ABI | `FIX_IN_FORK` | P0 | Убрать error-string use-after-free; caller всегда вызывает `free_string` | Error-path ASan/stress + allocation ownership tests |
| Hiddify config persistence/logging | `FIX_IN_FORK` | P0 | No raw logs/settings copy; Unix `0700/0600`, Windows app-private ACL; checked writes; bounded cleanup | Credential canary absent from logs/DB; file ACL/mode checks |
| Hiddify old command server/pprof | `DISABLE` | P0 | Не включать неиспользуемые control/profiling surfaces | Listener inventory and hostile-local-client test |
| Hiddify WARP endpoint | `KEEP_FIX_OPT_IN` | P0/P1 | Typed readiness/error, profile bounds validation, protected private-key cache; не использовать stub RPC | Unit/fuzz malformed profile, offline/API-detour, readiness timeout, cache ACL and reconnect |
| Upstream sing-box/libbox `1.13.x` | `FALLBACK_B` | P1 | Сохранить ADR/spike path без реализации до проблемы с Hiddify | Больше собственного glue, GPL review |
| Xray/libXray second client engine | `DEFER` | P2 | Wrapper существует, но API unstable/latest-only; не добавлять ради уже написанного backend profile | Только измеренный Xray-vs-Hiddify XHTTP gap + lifecycle/update/security budget |
| `shoes` Rust engine | `SERVER_LAB` | P2 | Exact VLESS/Reality/Naive/Hysteria benchmark/interoperability only | No production until control/multi-user/XHTTP/platform gaps and supply chain pass |
| Qeli | `R_AND_D_ONLY` | — | Заимствовать тесты/lifecycle lessons; не ship-ить custom protocol/TLS | 1.0, independent external audit, interop/field evidence and license decision would be prerequisites |
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
| XHTTP | `DEFER_CLIENT_ROLLOUT` | P2 | Hiddify fork уже имеет implementation; Xray остается reference owner | Сейчас backend/client contract сломан; exact build registration/config/server interop и RU evidence отсутствуют |
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
| WARP as censorship dependency | `REMOVE_FROM_CORE_PATH` | P1 | Оставить сильной optional egress/bridge capability Hiddify | Cloudflare API/WireGuard могут быть недоступны; readiness и private-key cache надо исправить |
| Remnawave migration | `REJECT_WITHOUT_CASE` | — | Не менять control plane по Habr-инструкции | Нужен отдельный TCO/capability migration case |
| 3x-ui as production authority | `DECOUPLE` | P1 | Xray оставить; сделать POKROV canonical config + exact-check/atomic runner/rollback; panel временно adapter/UI | Official README says personal-only/no production; parity and rollback before removing dependency |

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

- ADR фиксирует POKROV adapter → Hiddify v4 boundary и versioned Windows ABI;
- source baseline — exact `v4.1.0`, первый ship candidate — POKROV fork с patch
  manifest, а не upstream release artifact;
- Hiddify root/submodule commits, Go/gomobile versions и tags pinned;
- exact Hiddify fork lineage сохранена; upstream commits до `1.13.14`
  классифицированы; каждый выбранный backport имеет provenance и focused tests;
- downloader сверяет digest до extract;
- SBOM и internal permission reference сохраняются рядом с candidate metadata;
- Android/iOS host interfaces компилируются против v4 bindings;
- Windows adapter больше не требует удаленных `setupOnce`, `parse` и
  `changeHiddifyOptions`, а новый `setup` вызывается по точной v4 ABI;
- каждый C result копируется и освобождается через `free_string`; error path не
  возвращает freed pointer;
- managed JSON идет через `check_config`/`start_raw`, не переписывается скрытым
  Hiddify builder, не сохраняется в settings и не попадает в logs;
- old command server, pprof и неиспользуемые gRPC/listeners выключены;
- WARP endpoint не сообщает ready до фактической готовности, profile bounds
  проверяются, private key не попадает в logs/settings и cache защищен;
- direct sing-box остается документированным fallback, а не параллельным core.

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

### WP6 — server runtime authority

Owner: platform node runtime.

- Xray остается protocol engine current baseline;
- canonical config/profile state принадлежит POKROV, не 3x-ui DB/UI;
- runner делает exact-binary validate, atomic activate, health и rollback;
- 3x-ui сначала становится совместимым adapter, затем удаляется только после
  доказанной provisioning/accounting/rollback parity;
- native Hysteria/AWG/sing-box contours живут отдельными processes/listeners и не
  получают неявного доступа к общему routing state.
