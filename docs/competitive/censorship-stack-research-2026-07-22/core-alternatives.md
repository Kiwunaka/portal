# Альтернативы Hiddify Core

Статус: `EXPERIMENTAL`, advisory

Дата: `2026-07-22`

Контекст: owner подтвердил, что у POKROV есть отдельная лицензия и разрешение на
Hiddify. Это `OPERATOR_ATTESTED`; confidential grant в research не читался.
При этом client, UI, bootstrap, TUN и routing остаются POKROV-owned независимо от
выбранного core.

## Короткий ответ

При действующем разрешении Hiddify v4 — самый дешевый рациональный путь. Он уже
дает cross-platform artifacts, знакомую архитектуру и hiddify-sing-box с нужными
build tags. Но обновление требует настоящего API/config port.

Запасной порядок:

1. Hiddify Core v4 — основной target.
2. Direct sing-box/libbox — ближайший fallback.
3. Xray-core — fallback, если XHTTP станет обязательным differentiator.
4. Mihomo — permissive-license replacement при полном отказе от sing-box family.
5. Leaf или набор отдельных permissive cores — только при сознательной большой
   переработке.
6. Собственный protocol/crypto core — не делать.

## Сравнение

| Вариант | Public license | Сильные стороны | Цена для POKROV | Решение |
| --- | --- | --- | --- | --- |
| [Hiddify Core v4.1.0](https://github.com/hiddify/hiddify-core/releases/tag/v4.1.0) | Public GPLv3 + restrictions; у POKROV отдельное разрешение `OPERATOR_ATTESTED` | Android/iOS/macOS/Windows libs, sing-box 1.13 family, Naive/AWG build tags, близко к текущему stack | Medium: breaking bindings и config migration | `PRIMARY` |
| [sing-box v1.13.14](https://github.com/SagerNet/sing-box/releases/tag/v1.13.14) | GPLv3-or-later | VLESS/REALITY, Naive, Hysteria2, зрелый libbox/TUN | High: свой Windows ABI, mobile command-service port, больше supply-chain ownership | `FALLBACK_B` |
| [Xray-core v26.3.27](https://github.com/XTLS/Xray-core/releases/tag/v26.3.27) | MPL-2.0 | Native owner VLESS/REALITY/XHTTP; file-level copyleft вместо GPL | High: нет готовой POKROV mobile library boundary, свой wrapper/TUN lifecycle; нет Naive/Hysteria2 contour | `FALLBACK_C` |
| [Mihomo v1.19.29](https://github.com/MetaCubeX/mihomo/releases/tag/v1.19.29) | MIT | VLESS/REALITY, Hysteria2, TUIC, AnyTLS, TUN, активный project | Very high: Clash config model, новые bindings, profile/routing rewrite; нет Naive/XHTTP/AWG parity | `FALLBACK_D` |
| [Leaf v0.14.2](https://github.com/eycorsican/leaf/releases/tag/v0.14.2) | Apache-2.0 | Rust, cross-platform TUN, outbound VLESS/REALITY | Very high: меньше нужных transports/ecosystem evidence, другой config/runtime contract | `RESEARCH_ONLY` |
| NaiveProxy + Hysteria + AmneziaWG отдельными engines | BSD/MIT family, но нужен полный dependency audit | Можно выбирать лучшие узкие implementations | Extreme: 3 lifecycles, 3 update chains, routing/TUN arbitration, особенно плохо на iOS | `REJECT_NEAR_TERM` |
| Собственный Rust/Go protocol | Наш copyright, но все dependency obligations остаются | Полный контроль | Extreme и постоянный: crypto audit, protocol evolution, DPI research, clients/server compatibility | `REJECT` |

Public license — только название upstream license, не юридическое заключение и не
анализ transitive dependencies. Запуск core отдельным процессом сам по себе не
является автоматическим способом снять license obligations.

## Вариант A — Hiddify v4

Почему теперь первый:

- отдельное разрешение убирает главный business blocker;
- release уже содержит `hiddify-lib-android`, `hiddify-lib-ios`,
  `hiddify-lib-macos` и `hiddify-lib-windows-amd64`;
- GitHub release metadata публикует SHA-256 для каждого artifact;
- Hiddify build включает Naive и AWG, а базовый sing-box слой закрывает VLESS,
  REALITY и Hysteria2;
- текущие client hosts уже построены вокруг Hiddify/libbox concepts.

Что реально придется переписать:

| Surface | v3/current client | v4 target |
| --- | --- | --- |
| Mobile setup | `MobileSetup(base, work, temp, debug)` | `Setup(SetupOptions, PlatformInterface)` |
| Mobile config | `MobileParse`, `MobileBuildConfig` | Удалены; managed JSON подается в новый start/validation path |
| Mobile runtime | Direct `Libbox.newService` / `LibboxNewService` | v4 `Start(configPath, configContent)` / `Stop` либо новый libbox command-service contract |
| Desktop setup | 5 args + `setupOnce` | 8 args: mode/listen/secret/statusPort; `setupOnce` отсутствует |
| Desktop transform | `parse`, `changeHiddifyOptions` | Экспорты отсутствуют; POKROV должен выдавать final managed config |
| Artifacts | `hiddify-core-*`, `libcore.*` | `hiddify-lib-*`, `hiddify-core.*` / `HiddifyCore.xcframework` |
| Embedded schema | sing-box 1.8 family | sing-box 1.13 family |

Правильная реализация — отдельный `PokrovCoreBackend` contract. Внутри может быть
Hiddify v3 или v4; остальной Flutter/native код не должен знать конкретные symbols.

### Migration gates

1. Зафиксировать v3 behavior tests: setup, validate, start, stop, crash, reconnect,
   TUN open/close, route modes и DNS recovery.
2. Сохранить только internal reference на permission: entity, covered versions,
   redistribution/modification/platform scope и срок. Сам документ не коммитить.
3. Pin exact v4 tag, submodule commits, Go/NDK/gomobile versions и build tags.
4. Проверять release digest до extract; для собственных builds публиковать наш
   digest, SBOM и provenance.
5. Сначала портировать config schema и Windows ABI в изолированном client worktree,
   затем Android, затем Apple readiness lane.
6. Запустить old/new differential tests на одинаковых managed profiles.
7. Выпустить закрытый cohort с мгновенным rollback на v3; не смешивать с rollout
   Naive/Hysteria/AWG в том же candidate.

Обновление Hiddify само по себе не чинит текущий `xray-json` gap: bootstrap
отвергает такой manifest до вызова core. XHTTP остается отдельным решением.

## Вариант B — direct sing-box/libbox

Это архитектурно ближайшая альтернатива, потому что Hiddify v4 сам построен вокруг
sing-box 1.13 family. Плюс — меньше Hiddify-specific API/fork delta. Минусы:

- POKROV сам владеет Windows DLL/process ABI;
- Android/iOS надо портировать на upstream `SetupOptions` + `CommandServer`;
- свой build/release/security response pipeline становится обязательным;
- GPL obligations требуют отдельного review;
- upstream sing-box не дает Hiddify AWG fork из коробки.

Переключаться сюда стоит, если Hiddify v4 не проходит reliability/performance
gates, permission перестает покрывать нужный scope или Hiddify fork слишком далеко
уходит от upstream.

## Вариант C — Xray-core

Сильнейшая причина выбрать Xray — обязательный XHTTP. Xray имеет MPL-2.0 и владеет
VLESS/REALITY/XHTTP. Но для POKROV это не «поменять DLL»:

- нужен собственный stable C/JNI/ObjC wrapper;
- Android/iOS host по-прежнему сам владеет TUN/routes;
- profile/config model другой;
- Naive и Hysteria2 потребуют дополнительного engine;
- два cores удваивают lifecycle, telemetry, crash/update и test matrix.

Поэтому Xray стоит добавлять только после RU experiment, где XHTTP стабильно
закрывает измеренный gap, который Hiddify contours не закрывают.

## Варианты D/E — Mihomo, Leaf, отдельные engines

Mihomo — реальная permissive альтернатива, а не мертвый проект: active release,
MIT, VLESS/REALITY/Hysteria2/AnyTLS/TUIC и TUN. Но он заставляет перейти на Clash
config model и не дает полного transport parity. Это запасной новый фундамент, а
не migration shortcut.

Leaf интересен Apache-2.0, Rust и cross-platform TUN, но поддерживаемый набор и
полевая база уже. Набор отдельных Naive/Hysteria/AWG cores имеет хорошие licenses,
но превращает клиент в оркестратор нескольких network engines. Для Windows это
еще возможно; для Android/iOS цена и риск выше выгоды.

## Итог

Выбираем Hiddify v4, но защищаемся от следующей миграции своим узким adapter
contract, reproducible builds и capability-aware manifests. Direct sing-box
остается документированным Plan B, Xray — evidence-gated Plan C. Остальные cores
не дают преимущества, которое оправдывает переписывание текущего POKROV client.
