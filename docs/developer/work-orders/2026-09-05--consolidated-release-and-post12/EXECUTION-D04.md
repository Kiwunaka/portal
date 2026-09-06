# D04 — Android update authority, 2026-09-06

**PARTIAL / I3 / NEEDS_RUNTIME_PROOF.** Проверены существующие source boundaries
клиента `45036ab`; реализация не менялась.
[Команды, source/log SHA, шесть JUnit XML и device readback](evidence/d04-update-authority.json).

Direct updater проверяет canonical HTTPS GitHub origin, допустимые redirects,
ограничение размера, точные size/SHA256 и cancellation. До installer handoff он
повторно проверяет файл и APK identity. Policy сравнивает package, versionName,
возрастающий versionCode, SDK, ABI, разрешённого signer и continuity с установленным
signer. Тест rotation использует синтетическую platform-verified lineage; он не
выполняет проверку APK подписи Android PackageManager.

Store flavor возвращает `apk=null` и открывает `market://details` через
`com.android.vending`. Source contract проверяет отсутствие FileProvider,
unknown-source permission и APK installer MIME в этом flavor. Это проверка
исходного пути, а не доказательство отсутствия authority у установленного
store APK. Flutter bridge передаёт ограниченные identity fields и различает
store handoff; coordinator сериализует проверки и освобождает gate после ошибки.

Выполнены три существующих JVM класса в каждой Gradle task из
`scripts/run-tests.ps1`: 22 PASS, по 11 на direct/store; обе test tasks реально
выполнялись. Flutter channel/coordinator: 3 PASS. Повторно запускать весь client
набор без изменения исходников для этой сверки не потребовалось.

Свежий `adb.exe devices -l` завершился с exit 0: подключённых устройств 0.
Serials не сохранялись. Переходы ABI/universal/split, package/signing/versionCode
continuity, сохранение пользовательских данных и recovery при неподдерживаемом
переходе на установленных exact bytes остаются MANUAL_OWNER_TEST. Совпадение
versionName и локальный identity fixture не доказывают эти переходы.

D01 dependency и полный D04 открыты. Release APK/AAB не собирались; install,
signing, store action, push, merge, deploy и promotion не выполнялись. Client
diff остаётся прежним: только сохранённые generated registrants с разницей
окончаний строк. Retained release artifacts не менялись.
