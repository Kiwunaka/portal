# POKROV 1.0.7 — Promos, Variant Status And RU App Presets

Status: `ACTIVE_EXECUTION`

Owner outcome: выпустить следующий прямой стабильный Android/Windows-релиз
после `1.0.6`, в котором удалён временный демонстрационный характер remote
promos, пользователь видит честную доступность каждого white-list варианта, а
настройка маршрутов для российских приложений не требует ручного знания package
ID. После реализации пройти все пользовательские и операторские поверхности,
собрать точные артефакты, опубликовать stable release, синхронно задеплоить
platform и сохранить воспроизводимые доказательства.

## Зафиксированные решения владельца

- Прямые Android APK и Windows-пакеты остаются основным каналом; Apple и stores
  вне этой задачи.
- Remote promo может появиться без обновления клиента, быть временным,
  медийным, закрываемым или обязательным. В production нельзя оставлять
  тестовую кампанию после согласованного окна.
- Готовая инфографика или ролик могут быть всей карточкой: текст, badge и CTA не
  обязательны.
- Для акции нужен серверный интервал и живой countdown, например `−70%` и
  `23:59:59`, а не запечённое в APK обещание.
- В ограниченной сети пользователь должен видеть не только страну/город, но и
  какие white-list варианты реально доступны сейчас, какой выбран и какой
  используется runtime.
- Нельзя выдавать backend health, group URL-test или TCP ping за доказательство
  маршрута конкретного приложения. Значение `1 ms` без реального замера не
  показывается.
- RU-приложения определяются только по поддерживаемым точным идентификаторам
  пакетов/исполняемых файлов. Название — подпись, не источник истины. Пресет
  применяется только после понятного preview и подтверждения.
- Список установленных приложений остаётся локально на устройстве и не
  отправляется на сервер без отдельного будущего product/privacy решения.
- Поддержка остаётся AI-first, но переход к живому человеку/feedback-боту не
  прячется в overflow-меню: на экране чата нужна явная компактная кнопка. Как
  UX-референс проверяется реальный DedProxy в LDPlayer — FAQ, быстрые ответы,
  чат и Telegram action; их код, тексты и ассеты не копируются.
- Hiddify на рабочем ПК не выключать: от него зависит текущая сессия.

## Baseline, который задача обязана исправить

### Remote promos

- Production уже доказал динамическую загрузку семи allowlisted app slots без
  APK update, starts/ends и server-side audience.
- На узком Android viewport `app.home.banner` оказался слишком крупным: body
  обрезался, CTA занимал строку, большой визуальный круг крестика перекрывал
  контент.
- Клиент скрыто ограничивает ответ `.take(4)`, поэтому admin и устройство могут
  показывать разное число слотов без объяснимого правила.
- Текущая схема поддерживает image URL и layouts `logo|banner`, но не
  типизированные video/GIF/poster/fallback, countdown policy и upload lifecycle.
- Админка редактирует базовый copy/цвета/аудиторию/расписание, но не даёт
  полноценный mobile preview, asset upload, video poster, countdown и явное
  правило приоритета/лимита.

### Nodes and white-list variants

- `/api/client/locations` отдаёт node-level health/load/latency и только safe
  id/label/description доступных вариантов. Недоступные варианты исчезают.
- Device TCP probe измеряет город/основной endpoint, но не каждый white-list
  вариант.
- Variant sheet различает selected/available/locked, но не состояния
  `checking/available/unavailable/stale`, latency и возраст замера.
- В публичный API нельзя раскрывать host, port, keys, outbound tags или raw
  profile material.

### RU applications

- Picker уже загружает все Android launcher apps и поддерживает поиск, но
  рекомендуемый набор мал и не имеет first-party RU-классификации.
- Режимы `Россия напрямую`, `Только выбранные`, `Кроме выбранных` существуют,
  но пользователь вручную строит список и легко получает обратный результат.

## Product и API contract

### 1. Promo content model

Каждое назначение остаётся привязанным к allowlisted slot и содержит:

- стабильный `id`, `slot`, `enabled`, `priority`, `audience/access_states`;
- `starts_at`, `ends_at` и опциональный countdown policy, вычисляемый по
  серверному времени/offset, с локальным tick и fail-closed expiry;
- `dismissible=true|false`; у обязательного promo нет крестика, но он не может
  перекрывать VPN-кнопку, системную навигацию или другой критичный control;
- `whole_card_clickable`, allowlisted `cta_label`, safe `cta_href`;
- необязательные `badge`, `title`, `body` и brand-safe цвета;
- типизированный media object: `image|animated_image|video`, URL, MIME, width,
  height, bytes, optional duration, poster и static fallback;
- layout `logo|banner|media_only`; `media_only` работает без copy и CTA;
- first-party события `impression`, `click`, `dismiss`, `expired` без сторонних
  SDK, рекламных идентификаторов и истории посещённых сайтов.

Правила media:

- upload принимается только операторским authenticated endpoint, проверяет
  MIME по содержимому, расширение, размеры/длительность и безопасное имя;
- публичная раздача идёт с правильным Content-Type, cache policy и без
  выполнения HTML/SVG/script;
- видео muted, inline, без обязательного autoplay; respect reduced motion и
  data-saving, poster/static fallback обязателен;
- ошибка media не ломает карточку и не создаёт бесконечный layout shift;
- удаление asset запрещено, пока его использует active/rollback config.

Adaptive UI:

- при узкой ширине copy и CTA переходят в вертикальную композицию;
- close hit target не меньше 44–48 dp, но видимый круг/иконка компактны и
  вынесены из контента;
- текст не режется без явного `Подробнее`; кнопки не сжимаются ниже hit target;
- admin mobile preview использует те же layout tokens и показывает каждый
  placement, dismiss policy, countdown, image/video fallback и overflow state;
- скрытый `.take(4)` удаляется либо заменяется единым документированным
  `priority + per-placement limit`, одинаковым в API, admin preview и клиенте.

### 2. Variant availability contract

Публичный catalog продолжает отдавать только safe metadata. Клиентский runtime
может проверить уже авторизованный staged profile и вернуть только:

- safe variant id;
- `unknown|checking|available|unavailable|stale`;
- измеренную задержку в ms или `null`;
- `measured_at`, timeout/error category без endpoint/transport material;
- признак selected preference и отдельно active runtime variant.

UI и сортировка:

- рабочие варианты: зелёная отметка, затем latency; недоступные: красный крест;
- порядок `available fastest -> checking/unknown -> stale -> unavailable`, но
  вручную выбранный вариант остаётся видимым и подписанным;
- `Обновить` проверяет все варианты, а строка может повторить один замер;
- loading, timeout, offline, stale и server-catalog error различимы;
- node health/load и variant availability визуально и семантически разделены;
- screen reader получает статус, latency, свежесть и selected/active state;
- long labels, 320–408 logical px, font scale и 4+ variants не overflow;
- manual/auto choice, reconnect semantics, WARP and route gates остаются
  fail-closed; недоступный вариант не материализуется как безопасный fallback.

### 3. RU app catalog and presets

- Репозиторий владеет версионированным catalog с exact Android package IDs и
  Windows executable/app IDs, human label, category и review metadata.
- Локальный picker сопоставляет только exact normalized ID, сохраняет все
  launcher apps и помечает известные RU apps без сети.
- Первый слой предлагает два понятных действия:
  - `RU-приложения напрямую, остальные через VPN`;
  - `Только выбранные RU-приложения через VPN`.
- До применения показывается число найденных apps, список изменений, что будет
  через VPN/напрямую, и ссылка на ручную корректировку.
- Нулевой/устаревший catalog не применяет пустой набор молча; пользователь
  получает понятное объяснение и остаётся в ручном режиме.
- Preset не меняет WARP/location и не запускает VPN сам; существующая
  materialization/Android package planner проверяется focused regressions.

## Implementation checklist

### Platform/API/admin/media

- [x] `DONE_LOCAL` Зафиксировать failing contract tests текущего promo schema/normalizer.
- [x] `DONE_LOCAL` Добавить media/countdown/priority contract без ослабления slot/URL/color
  allowlists и fingerprinted publish action.
- [x] `DONE_LOCAL` Реализовать безопасный upload/read lifecycle и rollback-safe asset refs.
- [x] `DONE_LOCAL` Довести admin form, validation, mobile placement previews и publish/readback.
- [x] `DONE_LOCAL` Сохранить first-party funnel events и добавить promo event contract.
- [x] `DONE_LOCAL` Обновить canonical API/admin/operations documentation.

### Android/Windows client promos

- [x] `DONE_LOCAL` Реализовать общий adaptive promo renderer и typed media fallback.
- [x] `DONE_LOCAL` Исправить close placement/visual size и non-dismissible state.
- [x] `DONE_LOCAL` Реализовать server-aligned countdown/expiry и reduced-motion/data-saving.
- [x] `DONE_LOCAL` Удалить скрытый four-slot mismatch.
- [ ] Проверить home/rewards/profile/support/protection/global на узких экранах.

### Variant status

- [x] `DONE_LOCAL` Добавить privacy-safe runtime probe bridge и exact id mapping.
- [x] `DONE_LOCAL` Расширить client model/store/cache/freshness без раскрытия transport data.
- [x] `DONE_LOCAL` Реализовать all/one refresh, state machine, sort и accessible variant rows.
- [ ] Проверить restricted/offline/timeout/stale/selected/active/reconnect cases.
- [x] `DONE_LOCAL` Обновить canonical client/runtime/security documentation.

### RU app presets

- [x] `DONE_LOCAL` Создать reviewed first-party catalog и validation test на duplicate IDs.
- [x] `DONE_LOCAL` Добавить local classification, search chips/sort и preview confirmation.
- [x] `DONE_LOCAL` Реализовать оба route presets через существующие route modes/planner.
- [x] `DONE_LOCAL` Доказать отсутствие upload установленного app list и безопасный empty case.

## Audit and release gates

### Fresh user/admin surface audit

- [ ] Сайт: acquisition -> install -> auth -> checkout/support.
- [ ] Telegram bot: first layer -> login/download/account handoff.
- [ ] Cabinet: subscription/devices/connections/users/downloads/support/promos.
- [ ] Android: onboarding/home/inbox/locations/variants/rules/RU preset/profile/
  rewards/support/update/notification/tile and every promo placement.
- [x] `DONE_LOCAL` LDPlayer benchmark of owner's `DedProxy-3.3.0-release.apk`: capture its
  support center, compact chat, FAQ/quick answers and direct operator action;
  compare against POKROV and keep POKROV's AI-first flow with a clear explicit
  feedback-bot/human escape instead of automatic escalation.
- [x] `DONE_LOCAL` POKROV support: keep grounded AI/diagnostics first, add a directly visible
  feedback-bot/human action in the chat surface, and verify that FAQ/actions do
  not immediately or automatically escalate.
- [ ] Windows: home/location/rules/profile/support/update and promo rendering.
- [ ] Admin: login/dashboard/users/nodes/variants/promos/media preview/publish/
  rollback/support/releases.
- [ ] Сохранить свежие screenshots, numbered UX/accessibility findings, strengths,
  limitations и exact candidate hashes. Screenshot сам по себе не считается
  доказательством runtime behavior.

### Automated and runtime gates

- [ ] Platform focused API/admin/media/security tests and affected regression.
- [ ] Admin/marketing/webapp lint, build, responsive/E2E and contract guards.
- [x] `PASS_LOCAL_FINAL` Flutter focused widget/runtime tests, `flutter analyze`, full
  `flutter test` (283/283) and runtime-engine suite (39 pass, one explicit real-core skip).
- [x] `PASS_LOCAL_FINAL` Android focused/full JVM tests, release build,
  signer/version/ABI verification for `1.0.7+16`.
- [x] `PASS_LDPLAYER` LDPlayer release-APK rendering/network-safe QA via ADB proved
  persisted per-variant failure status, RU preset preview, the direct feedback-bot
  action and a grounded AI WARP answer; Huawei only when owner
  leaves it connected and unlocked.
- [ ] Windows build/smoke/UI/logs; do not claim clean egress while Hiddify is
  required for this session.
- [ ] Docs/seed/diff/secret scans and exact release gate report.

### Promotion and deployment

- [ ] Raise versions above `1.0.6+15`; build stable split/universal Android and
  Windows setup/portable/manifest/checksums.
- [ ] Verify names, sizes, SHA-256, signer, ABI, update metadata and rollback set.
- [ ] Scoped commits to platform feature branch and client feature branch.
- [ ] Push and fast-forward platform `master` and client `main` only after gates.
- [ ] Publish non-prerelease stable GitHub release and verify every public asset.
- [ ] Deploy backend/static/admin; perform brain-origin/current-origin readbacks.
- [ ] Confirm no test promo remains active and retain rollback evidence.

## Evidence locations

- Heavy screenshots, recordings, APKs and logs:
  `E:/POKROV-ops-evidence/2026-08-14-stable-1.0.7/`.
- Repository keeps only compact reports, hashes and canonical contracts; generated
  builds/caches are not copied to `C:`.

## Release honesty

This work order is not a release claim. A checkbox becomes `PASS` only for the
exact final source/artifact/environment. Backend health cannot substitute for
device variant availability; URL-test cannot substitute for per-app egress;
LDPlayer cannot substitute for Huawei-only behavior; current-origin cannot
substitute for RU-origin. Missing physical-device or external-origin proof is
reported with its exact manual label rather than converted into a pass.
