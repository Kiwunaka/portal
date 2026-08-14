# POKROV 1.0.6 Stable Release Work Order

Status: `ACTIVE_EXECUTION`

Owner outcome: выпустить прямой Android APK и Windows-пакет как стабильный
релиз без beta-канала, сохранить текущий аккаунт и сетевые контракты, убрать
найденные P0-поломки и синхронно обновить сайт, кабинет, бота, инструкции и
production metadata.

## Зафиксированные решения владельца

- Android и Windows распространяются напрямую, без стора.
- `99 ₽` — приветственный полный первый месяц один раз; дальше базовый месяц
  стоит `239 ₽`.
- Бесплатной ноды после окончания premium нет.
- Telegram-бонус `+5 дней` доступен до оплаты после привязки Telegram и
  подтверждения подписки на официальный канал.
- Реферальные награды начисляются только после первой успешной оплаты друга.
- First-party аналитика разрешена для пути `источник -> шаги -> препятствие ->
  конверсия`; сторонние рекламные SDK и история посещённых сайтов не нужны.
- Новые Apple/store задачи не входят в этот релиз.

## Обязательный результат

### Обновление и дистрибуция

- [x] Клиент ищет обновление анонимно через `/api/public/client-apps` и не
  создаёт trial/session ради проверки версии.
- [x] Канал по умолчанию в клиенте, API и сайте — `stable`.
- [x] Версия кандидата поднята до `1.0.6+15`, строго выше публичной beta 1.0.5.
- [x] Создан публичный GitHub release `v1.0.6` без prerelease-флага и назначен
  latest: <https://github.com/Kiwunaka/pokrov/releases/tag/v1.0.6>.
- [x] В релизе есть отдельные Android APK `arm64-v8a`, `armeabi-v7a`, `x86_64`
  и universal fallback, а также Windows setup/portable/manifest/checksums.
- [ ] Production metadata, бот и сайт отдают только точные stable URL, размеры
  и SHA-256 нового релиза.

### Android P0 и UX

- [x] На главной есть заметный колокольчик и локальный inbox уведомлений.
- [x] Плашка оставшегося premium ведёт в Профиль, а не сразу в checkout.
- [x] Основная кнопка использует знакомый power-icon; статус внутри неё явно
  выглядит как отдельное действие с подробностями.
- [x] В Профиле есть `О приложении` с версией, платформой и stable-каналом.
- [x] Внешние переходы помечены иконкой открытия в браузере.
- [x] Удалена бесполезная дублирующая строка `Статус` в Профиле.
- [x] Quick Settings tile больше не рисует ложное постоянно включённое
  состояние и ограничивает зависший transition.
- [x] Каталог приложений загружается вне UI-потока, сохраняет для поиска все
  launcher-приложения и отдельно ограничивает дорогую кодировку иконок.
- [x] Production-signed 1.0.6 повторно собран после финального catalog-fix,
  установлен на Huawei и проверен поиском Яндекс.Браузера.
- [x] На точном финальном APK проверены колокольчик, Профиль, Android TV code,
  плитка и базовый connect/disconnect без новых crash/ANR.

### Аккаунт, бонусы, TV и AI-поддержка

- [x] Production Android TV pairing code снова создаётся; отдельный HMAC secret
  настроен, readiness проверяет только наличие и длину без вывода секрета.
- [x] Telegram-бонус отделён от paid reward gate; wheel/calendar/referral
  остаются платными или post-payment по своим правилам.
- [x] ИИ получает только allowlisted read-only snapshot текущего
  аутентифицированного аккаунта: доступ, срок, тариф, Telegram-связь,
  устройства и безопасное состояние panel/runtime.
- [x] ИИ не получает UID, email, username, host, ключи, raw config, payment
  payload и не может выполнять произвольные API/DB операции.
- [ ] После deploy live trial-аккаунт видит Telegram-бонус без ложной ошибки и
  AI отвечает по фактическому состоянию этого же аккаунта.

### Сайт, кабинет, бот и инструкции

- [x] Главный showcase больше не рисует выдуманный интерфейс: Android Home,
  Locations и Profile заменены реальными Huawei-скриншотами; Windows использует
  реальный захват окна приложения.
- [x] Ключевые изображения атласа Home, Locations, Rules, Profile и
  Notifications обновлены реальными снимками 1.0.6.
- [x] Telegram-бот вручную пройден до Android-загрузок: первый слой короткий,
  но текущие production URL всё ещё указывают на beta 1.0.5 до релиза.
- [x] Пройден authenticated cabinet: устройства, активные подключения,
  статистика, пользователи на ключе, загрузки, поддержка и handoff обратно.
- [x] По точной runtime-конфигурации и regression-тесту доказано, что AdGuard
  DNS включает
  block-rule, и честно отделить DNS-блокировку доменов от блокировки любой
  рекламы внутри приложений.
- [x] Пересняты финальные Windows 1.0.6 Home/About; временный реальный
  Windows 1.0.4 screenshot в showcase.

## Проверки и публикация

- [x] Flutter focused regressions: PASS.
- [x] `flutter analyze` в `packages/app_shell`: PASS.
- [x] Полный `flutter test` в `packages/app_shell`: `276 passed`.
- [x] Android focused JVM contract: PASS.
- [x] Platform focused backend/bonus/AI/readiness tests: PASS.
- [x] Marketing lint/build до финального screenshot-swap: PASS.
- [x] Marketing lint/build/SEO/responsive после visual-swap: PASS, включая 19
  маршрутов на трёх viewport после удаления осиротевшего локального dev-server.
- [x] Platform/client full release gates и secret/diff checks: PASS.
- [x] Android production signer/hash/version/ABI проверены для universal и трёх
  split APK; финальный arm64 установлен на Huawei, x86_64 — в LDPlayer.
- [x] Windows stable setup/portable собраны с честным unsigned/SmartScreen warning.
- [x] Client release-коммит `c915aafb9a0aa1abf8f7cac9876e535695914796`
  запушен в feature branch и fast-forward в `main`; source-tag `v1.0.6` запушен.
- [ ] Закоммитить и запушить platform `master`.
- [ ] Задеплоить platform и статические web surfaces, выполнить current-origin
  и brain-origin readback, затем опубликовать stable update metadata.

## Текущие доказательства

- Реальный Huawei: `E:/POKROV-ops-evidence/2026-08-14-stable-release-audit/huawei-1.0.6/`.
- Competitor review: DedProxy APK, DedAI XAPK и предоставленное видео проверены
  только как UX-референсы; чужой код и ассеты в POKROV не копируются.
- Подробные post-release endurance/network/manual gates остаются в отдельном
  work order `docs/developer/work-orders/2026-08-14--postrelease-manual-proof/`
  и не подменяют критерии этого stable-релиза.

## Release honesty

GitHub stable release `v1.0.6` опубликован и его восемь assets сверены с
локальным staging по имени, размеру и SHA-256. До production metadata/deploy
прежняя `1.0.5-beta.1` ещё может встречаться в API, боте и сайте; это открытый
операционный шаг, а не состояние нового бинарного релиза. Windows остаётся
прямой unsigned-дистрибуцией с явным предупреждением, не trusted-signed/store
выпуском.
