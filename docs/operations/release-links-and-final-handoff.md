# Передача по финальным ссылкам и релизному handoff

Last updated: 2026-04-15

## Зачем нужен этот файл

Используйте эту инструкцию после публикации клиентских артефактов и до того, как объявлять релиз завершённым.

Этот шаг нужен, чтобы приложение, бот, webapp и marketing указывали на одни и те же актуальные Android- и Windows-ссылки.

## Когда сразу останавливаемся

Сразу считаем релиз заблокированным, если нет хотя бы одного пункта:

- хотя бы одной рабочей Android release URL
- хотя бы одной рабочей Windows release URL
- `APP_DOCS_URL`
- успешной проверки URL
- синхронизации runtime env на `brain`
- rebuild/redeploy статических страниц, если публичные ссылки менялись

## Что нужно получить от вас

Нужны финальные публичные ссылки для:

- `APP_ANDROID_PLAY_URL` или `APP_ANDROID_APK_URL` или `APP_ANDROID_MIRROR_URL`
- `APP_WINDOWS_EXE_URL` или `APP_WINDOWS_MIRROR_URL`
- `APP_DOCS_URL`

Для проверки ссылок должно быть заполнено:

- хотя бы одна Android-ссылка
- хотя бы одна Windows-ссылка
- ссылка на docs/install

## Что делать по шагам

1. Опубликуйте финальные Android- и Windows-артефакты.
2. Сформируйте файл релизных ссылок:

```powershell
pwsh external/client-fork/scripts/release_handoff.ps1 `
  -AndroidApkUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-android-universal.apk" `
  -WindowsExeUrl "https://github.com/<org>/<repo>/releases/download/<tag>/pokrov-windows-setup-x64.exe" `
  -DocsUrl "https://pokrov.space/install/"
```

3. Проверьте ссылки:

```powershell
python external/client-fork/scripts/check_release_urls.py --env-file external/client-fork/release-links.env
```

4. Примените `APP_*` значения на `brain`:

```powershell
python scripts/remote_brain_apply_release_handoff.py --brain-ip 82.21.114.104 --env-file external/client-fork/release-links.env
```

5. Если Android- или Windows-ссылки изменились, пересоберите и заново выкатите static marketing, чтобы `NEXT_PUBLIC_APP_*` тоже указывали на тот же релиз.
6. После синхронизации перепроверьте download-поверхности, которые тянут ссылки из runtime.
7. Только после этого пишите финальный release handoff.

Важно по поверхностям:

- marketing прямые download CTA сейчас зависят именно от `APP_ANDROID_APK_URL` и `APP_WINDOWS_EXE_URL`; только `Play` или только mirror-ссылки не дают той же прямой кнопки на публичной landing/install-странице
- sync `APP_*` на `brain` обновляет runtime app, bot и authenticated webapp, но сам по себе не перестраивает static marketing или его build-time fallback
- brain-local verify после sync полезен, но он не заменяет отдельные `current-origin check` и `RU-origin check`

## Что обязательно должно быть в финальном handoff

Финальное сообщение должно быть простым и прямым:

- что именно изменилось
- что именно проверили
- что ещё заблокировано, если не всё готово
- находится ли система в rollback-safe состоянии

Если в этом же handoff фигурирует доступность из разных точек, обязательно отдельными строками:

- `current-origin check`
- `brain-origin check`
- `RU-origin check`

Не надо сливать их в одну общую строчку.

## Что нужно прислать мне обратно

Пришлите:

- какой именно `release-links.env` использовали
- команду проверки URL и её exit code
- команду sync на `brain` и её exit code
- какие сервисы на `brain` перезапускались
- был ли rebuild/redeploy marketing
- доказательство, что app, bot, webapp и marketing теперь смотрят на одни и те же релизные ссылки

## Частые причины блокировки

- ссылки есть, но checker падает
- runtime env уже обновили, а marketing всё ещё показывает старые ссылки
- обновили только одну поверхность
- Android signing или Android physical-device audit ещё не закрыты
- финальные signed Android или Windows artifacts ещё не подтверждены как production-ready
- в handoff написано "готово", но нет доказательств по origin checks или release URLs

## Связанные инструкции

- [Передача для production-подписи Android](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Передача для проверки Android на реальном устройстве](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-physical-device-audit-handoff.md)
- [Передача для RU-origin probe](C:/Users/kiwun/Documents/ai/VPN/docs/operations/ru-origin-probe-handoff.md)
- [Deployment And Access](C:/Users/kiwun/Documents/ai/VPN/docs/operations/deployment-and-access.md)
