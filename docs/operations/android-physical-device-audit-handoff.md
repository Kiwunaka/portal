# Передача для проверки Android на реальном устройстве

Last updated: 2026-04-15

## Зачем нужен этот файл

Используйте эту инструкцию для обязательной проверки Android release-сборки на настоящем телефоне или планшете.

Это именно тот релизный барьер, который должен доказать, что приложение не открывает наружу опасные localhost-поверхности: прокси, DNS, command-server, Clash API и похожие управляющие интерфейсы.

## Когда сразу останавливаемся

Сразу считаем Android заблокированным, если нет хотя бы одного пункта:

- реального Android-устройства, подключённого по `adb`
- серийного номера устройства
- установленной release-сборки на этом устройстве
- времени, чтобы пройти все 3 фазы проверки:
  - после запуска приложения
  - после подключения
  - после отключения

Эмулятор можно использовать только для репетиции команд. Публичный Android-релиз он не разблокирует.

## Что нужно получить от вас

- serial устройства из `adb devices`
- подтверждение, что на устройстве стоит именно release-сборка
- имя пакета, если оно отличается от `space.pokrov.pokrov_android_shell`
- другое время ожидания, если стандартного не хватает

Значения по умолчанию:

- package: `space.pokrov.pokrov_android_shell`
- `--launch-wait-sec 5`
- `--connect-wait-sec 30`
- `--disconnect-wait-sec 15`

## Что делать по шагам

1. Подключите один реальный Android-девайс или заранее решите, какой exact serial будете использовать.
2. Проверьте, что на нём уже установлена release-сборка.
3. Из корня репозитория запустите проверку:

```powershell
python scripts/android_localhost_audit.py --serial <device-serial> --package space.pokrov.pokrov_android_shell --release-evidence "<artifact/version/checksum>" --require-release-build --connect-wait-sec 30 --disconnect-wait-sec 15
```

4. Если имя пакета другое, добавьте:

```powershell
--package <package-name>
```

5. Дождитесь запуска приложения.
6. Когда скрипт попросит подключиться, вручную включите подключение в приложении и подтвердите системное Android VPN-разрешение, если появится окно.
7. Когда скрипт попросит отключиться, вручную разорвите подключение.
8. Сохраните JSON-отчёт. По умолчанию он пишется сюда:

```text
ops-local/android-localhost-audit.json
```

## Evidence and scratch hygiene

- Retained formal evidence: keep `ops-local/android-localhost-audit*.json` and any intentionally promoted audit records under `docs/audit-artifacts/`.
- Disposable repo-local scratch: screenshots, UI XML dumps, logcat captures, and ad hoc runtime snapshots created for one Android audit run stay disposable unless they are deliberately copied into `docs/audit-artifacts/`.
- Outside repo cleanup scope: machine-local Android tooling noise such as `C:\Windows\adb.exe`, `%TEMP%`, SDK install directories, and `~/.android` is workstation state, not repo cleanup state.

9. Если времени не хватило, перезапустите проверку с большими таймаутами и запишите, какие значения использовали.

## Как включить это в общий release gate

Если хотите, чтобы та же проверка попала в общий локальный release-report, сначала выставьте serial:

```powershell
$env:ANDROID_AUDIT_SERIAL="<device-serial>"
$env:ANDROID_AUDIT_PACKAGE="space.pokrov.pokrov_android_shell"
$env:ANDROID_AUDIT_RELEASE_EVIDENCE="<artifact/version/checksum>"
python scripts/release_gate_check.py --client-platform-gates windows,android-apk,android-aab
```

Но это всё равно должно быть именно реальное устройство, а не эмулятор.

## Когда считаем, что проверка пройдена

Проверка считается успешной только если:

- скрипт завершился с кодом `0`
- JSON-отчёт реально создан
- в отчёте нет новых открытых localhost listener
- в отчёте нет успешных неавторизованных localhost probe

Проверка считается проваленной, если:

- скрипт завершился с ошибкой
- устройство отвалилось во время проверки
- на любой фазе появился открытый localhost listener
- хотя бы один неавторизованный probe сработал

## Что нужно прислать мне обратно

Пришлите:

- модель устройства
- `adb` serial
- имя пакета
- точную команду, которую запускали
- путь к JSON-отчёту
- подтверждение, что были пройдены все 3 фазы: after launch, after connect, after disconnect
- итоговый exit code

Лучше прислать сам JSON или ссылку на него, а не копировать его целиком в markdown.

## Частые причины блокировки

- под рукой только эмулятор
- release-сборка ещё не установлена
- оператор не успел подключить или отключить приложение в нужный момент
- `adb` не видит устройство
- указан неправильный package name
- отчёт показывает доступную localhost-поверхность

## Связанные инструкции

- [Передача для production-подписи Android](C:/Users/kiwun/Documents/ai/VPN/docs/operations/android-production-signing-handoff.md)
- [Передача по финальным ссылкам и релизному handoff](C:/Users/kiwun/Documents/ai/VPN/docs/operations/release-links-and-final-handoff.md)
- [Publishing And Signing Guide](C:/Users/kiwun/Documents/ai/VPN/docs/operations/publishing-and-signing-guide.md)
