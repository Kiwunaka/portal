# Hiddify v4: критика, аудит и POKROV patch stack

Статус: `EXPERIMENTAL`, advisory research

Срез: `2026-07-22`

## Вердикт

Hiddify можно допилить. При отдельном разрешении это самый короткий путь для
POKROV, но только как наш fork и backend library. Готовый Hiddify app нам не нужен,
а release `hiddify-core v4.1.0` нельзя считать готовым drop-in artifact.

Правильная цель:

```text
POKROV app/host
    -> versioned PokrovCoreBackend
    -> POKROV fork of Hiddify Core v4
    -> reviewed hiddify-sing-box on sing-box 1.13.x baseline
```

`v4.1.0` — source baseline. Первый ship candidate — наш reproducible build с
исправленным ABI, безопасным config handling, отключенными лишними control
surfaces и проверенным sing-box patch level.

## Что мы наследуем, а что нет

POKROV уже владеет UI, bootstrap, аккаунтом, managed profiles, Android
`VpnService`, Apple packet tunnel и desktop host. Поэтому большая часть жалоб на
Hiddify app не переносится на нас автоматически.

Наследуем:

- Hiddify core/config code и `hiddify-sing-box` fork;
- native ABI/gomobile bindings;
- network engine crashes, memory ownership и TUN/libbox defects;
- dependency/build-tag/submodule chain.

Не наследуем напрямую:

- Hiddify Flutter UI, updater, deep links и profile screens;
- его Android permission flow и background-service orchestration;
- его Windows Flutter shell;
- Hiddify app telemetry/branding/product behavior.

## За что Hiddify ругают

Issue tracker — источник конкретных regressions, не статистика качества. Несколько
показательных случаев:

| Жалоба | Где дефект | Что это значит для POKROV |
| --- | --- | --- |
| [Core #112](https://github.com/hiddify/hiddify-core/issues/112): `C.CString` leak в v3 Dart bridge | Core bridge | Реальный дефект текущей v3-линии; v3 держать только как bounded rollback |
| [App #2284](https://github.com/hiddify/hiddify-app/issues/2284): sporadic allocator panic в app `4.1.1` / sing-box `1.13.0` | Core/fork/runtime path | Exact candidate надо воспроизвести/soak; номер upstream patch сам по себе не доказывает fix |
| [App #2281](https://github.com/hiddify/hiddify-app/issues/2281): Android 16 background disconnect без auto-reconnect | App lifecycle | Hiddify app host не брать; свой POKROV service обязан иметь supervisor/recovery |
| [App #2047](https://github.com/hiddify/hiddify-app/issues/2047): connect method сообщает success до фактической готовности | App method-channel contract | Не наследуем код, но обязаны сделать readiness handshake в своем adapter |
| [App #2246](https://github.com/hiddify/hiddify-app/issues/2246): Windows crash в `flutter_windows.dll` | Hiddify app/Flutter shell | Наш shell защищает от этого конкретного дефекта; это не аргумент выкидывать core |
| [App #1964](https://github.com/hiddify/hiddify-app/issues/1964): Windows TUN timeout при рабочем system proxy | Platform/TUN path | Нужны exact-candidate Windows TUN tests; issue не доказывает universal core failure |

К Hiddify обычно предъявляют четыре обоснованные претензии: breaking upgrades,
fork lag, тяжелая supply chain и неровный lifecycle вокруг core. Все четыре
контролируются pinning, собственным adapter, нашим ограниченным hardening patch
stack и release gates. Но inherited `hiddify-sing-box` fork сам по себе большой;
это не «маленькая дельта к upstream».

## Проверенные дефекты и риски в `v4.1.0`

Это code audit tag `v4.1.0`, а не пересказ отзывов.

| Finding | Приоритет | Доказательство | Исправление |
| --- | --- | --- | --- |
| Desktop error string освобождается до возврата caller: `defer C.free(...)` перед `return str` | P0 | [`platform/desktop/custom.go#L65-L75`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/platform/desktop/custom.go#L65-L75) | Убрать premature free; caller всегда делает `freeString` после копирования |
| Success/error strings выделяются через `C.CString`; текущий POKROV v3 caller только делает `toDartString()` | P0 | v4 [`freeString`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/platform/desktop/custom.go#L101-L105) и local `runtime_engine.dart` | Versioned ABI и обязательный `try/finally free_string` для каждого результата |
| Final config всегда пишется в `data/current-config.json`; mode `0755/0644` | P0 | [`debug.go#L14-L25`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/config/debug.go#L14-L25), [`start.go#L111-L120`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/hcore/start.go#L111-L120) | `0700/0600`, проверять ошибки, минимизировать persistence, удалять/rotating при logout/stop |
| При debug полный config, включая proxy credentials, пишется в log | P0 | [`start.go#L115-L120`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/hcore/start.go#L115-L120) | Полностью запретить raw config logs; только redacted structured diagnostics |
| `ConfigContent` сохраняется как `lastStartRequestContent` в settings DB | P0 | [`start.go`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/hcore/start.go) | Не сохранять managed material в settings; restart получает config заново от POKROV |
| Desktop `start/restart` принудительно включает old command server | P0 | [`custom.go#L108-L140`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/platform/desktop/custom.go#L108-L140) | `false`; не поднимать неиспользуемый listener/control plane |
| Managed final JSON по умолчанию проходит через Hiddify config builder; `EnableRawConfig` не выставлен desktop/mobile exports | P0 | [`buildconfighelper.go#L28-L42`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/hcore/buildconfighelper.go#L28-L42) | Экспортировать явный `start_raw`/`check_config`; POKROV final config не должен тихо переписываться |
| Mobile и gRPC code импортируют `net/http/pprof` | P1 | [`platform/mobile/mobile.go`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/platform/mobile/mobile.go), [`grpc_server.go`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/hcore/grpc_server.go) | Убрать из production build, если profiling endpoint не используется |
| Released fork основан на sing-box 1.13-era code, но содержит 156 собственных commits/236 changed files и не включает 191 upstream stable commits на дату среза | P0 | Exact submodule `0a02b77`, `git merge-base/rev-list/diff`; [`hiddify-fork-delta.md`](hiddify-fork-delta.md) | Не делать blind module replace/rebase. Классифицировать upstream commits и backport-ить security/correctness fixes с provenance/tests |
| WARP endpoint начинает profile/bootstrap в goroutine и возвращает success до readiness; failures только логируются | P0 | [`endpoint_warp.go`](https://github.com/hiddify/hiddify-sing-box/blob/0a02b7729f6a211436bb8bdcd8696c283eb27767/protocol/wireguard/endpoint_warp.go) | Typed readiness/failure callback, timeout и adapter state gate |
| WARP cache содержит private key; malformed profile может дать empty `Peers`/ports и panic | P0/P1 | Тот же exact source | App-private encrypted/ACL-controlled storage; validate profile before indexing/random choice; fuzz/unit tests |
| Hiddify Core `GenerateWarpConfig` фактически stub, а legacy `patchWarp` содержит unreachable code после early return | P1 | [`v2/hcore/warp.go`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/hcore/warp.go), [`v2/config/warp.go`](https://github.com/hiddify/hiddify-core/blob/v4.1.0/v2/config/warp.go) | Не публиковать эти helpers в POKROV contract до исправления; использовать exact endpoint config path |

Проверка [`main` desktop ABI](https://github.com/hiddify/hiddify-core/blob/main/platform/desktop/custom.go)
и [`main` config persistence](https://github.com/hiddify/hiddify-core/blob/main/v2/config/debug.go)
на дату среза показала те же patterns. Ждать неизвестного будущего release вместо
своего fix нельзя.

## Что чиним где

### В POKROV adapter

- единый contract: `abi_version`, `capabilities`, `setup`, `check_config`,
  `start_raw`, `stop`, status/error callbacks и `free_string`;
- адаптация v3/v4 не протекает в Flutter, Kotlin и Swift business code;
- explicit state machine `stopped -> starting -> ready -> stopping -> stopped`;
- connect success только после TUN/core readiness;
- idempotent stop, crash recovery, Wi-Fi/LTE handover, bounded backoff;
- exact embedded-core validation до start;
- быстрый rollback на frozen v3 candidate до parity milestone.

### В POKROV fork Hiddify Core

- исправить desktop C ownership/use-after-free;
- добавить стабильные `start_raw` и `check_config` exports;
- выключить old command server, pprof и неиспользуемые gRPC/listeners;
- перестать сохранять raw `ConfigContent`; для необходимого runtime file применять
  `0700/0600` на Unix-like systems и app-private directory/ACL на Windows;
- запретить raw config logging и проверять ошибки записи;
- pin root commit, all submodules, Go/gomobile/NDK и build tags;
- сохранить exact released Hiddify lineage; составить manifest отсутствующих
  upstream commits и backport-ить только нужные security/correctness fixes;
- собирать Android/Apple/Windows artifacts самим с hashes, SBOM и provenance.

### Отправляем upstream

Generic fixes стоит оформить upstream PR/issues: C string ownership, safe file
modes/error handling, отсутствие raw-config logging и возможность raw start. Но
release POKROV не должен зависеть от срока принятия PR: наш pin остается source of
truth.

## Что оставить и что убрать

Оставить:

- hiddify-sing-box protocol breadth;
- libbox/TUN integration;
- Naive/AWG build path, если они входят в утвержденный experiment plan;
- cross-platform build recipes;
- Hiddify WARP/config helpers только как явные opt-in capabilities.

WARP endpoint implementation оставить, но пустой `GenerateWarpConfig` RPC и
legacy unreachable path не считать рабочим product API. Readiness и private-key
storage должны принадлежать нашему adapter/security contract.

Убрать из shipped surface:

- Hiddify app UI/updater/branding/telemetry;
- arbitrary public-subscription/profile conversion в основном managed path;
- автоматическую Hiddify config mutation для final POKROV JSON;
- old command server, pprof, неиспользуемый gRPC/control plane;
- extensions/build tags, которым нет consumer и acceptance test.

Не надо механически вырезать все build tags в первом port: сначала получить parity,
затем отдельно измерить APK/artifact size, memory и startup cost. Если нужен Naive,
Cronet и заметный размер artifact — осознанная цена capability.

## P0 patch stack до первого candidate

1. Создать POKROV fork от exact `v4.1.0`; сохранить upstream tag/root/submodule
   provenance.
2. Зафиксировать exact Hiddify submodule lineage и upstream-fix manifest до
   `1.13.14`; выбрать и backport-ить fixes по одному. Не делать blanket rebase.
3. Исправить C ABI ownership и добавить ABI/capability versioning.
4. Добавить `check_config` и `start_raw`; запретить скрытую перестройку managed JSON.
5. Закрыть config-at-rest/logging issues.
6. Отключить old command server, pprof и неиспользуемые listeners.
7. Исправить WARP validation/readiness/cache handling и покрыть opt-in capability
   отдельными tests.
8. Портировать Android/iOS host bindings и Windows FFI на adapter.
9. Мигрировать schema 1.8 -> 1.13 и валидировать exact candidate binary.
10. Выпустить reproducible artifacts с SHA-256, SBOM и build metadata.
11. Пройти differential profiles, TUN/DNS, reconnect, handover, crash, memory и
    long-soak tests до canary.

Не смешивать core migration и rollout Naive/Hysteria/AWG в одном candidate. Сначала
parity старого контура, затем новые transports отдельными cohorts.

## Решение о замене core

Перейти на direct upstream sing-box стоит только если наш Hiddify fork:

- систематически не проходит crash/memory/TUN gates;
- требует все больше несвязанных product patches ради сохранения нужных features;
- блокирует timely security updates;
- теряет нужный scope разрешения.

До появления такого evidence direct libbox несет больше работы, а не меньше.
Karing/NekoBox forks добавляют еще одного посредника и не дают POKROV преимущества.
Xray оправдан только измеренным XHTTP gap; Mihomo — только сознательной сменой
config/runtime family.

Точный состав fork, WARP semantics и три update strategy:
[`hiddify-fork-delta.md`](hiddify-fork-delta.md).
