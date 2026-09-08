# R12 — текущий результат и граница исполнения

**PARTIAL / RELEASE_BLOCKED. План целиком не завершён; последующие срезы датированы ниже.**

[Windows service crash](EXECUTION-WINDOWS-SERVICE-CRASH-2026-09-08.md): исправлен
ложный «Подключено» после завершения службы. Client `68a44e5` установлен в VM:
crash/recovery, обычный retry, exact routes/DNS и 305 hashes PASS_BOUNDED.
Первый clean SCM sample — 15,6 с. Backend восстановлен, VM off/NIC none,
host network прежний. Sleep/handoff, Win10 и полный W02 остаются открытыми.

[Android APK с новым Core](EXECUTION-ANDROID-AWG-PACKAGES-2026-09-08.md): client
`76614b1` / Core `02a091c`, ARM64 101,23 МБ, universal 295,23 МБ; четыре ABI
варианта прошли signer/package/native hash audit. Физической установки этих
bytes ещё нет, device/LTE приёмка открыта. Это подготовка, не публикация.

[A03 в новом Windows-пакете](EXECUTION-WINDOWS-AWG-CROSSFIELD-2026-09-08.md):
client `295ceac` / Core `02a091c` установлен в VM. Upgrade, 305 hashes и обычные
AWG3.1 → AWG2 → AWG3.1 reconnect PASS_BOUNDED; все три disconnect восстановили
routes/DNS. Серверная настройка восстановлена, VM off/NIC none, сеть host прежняя.
Это следующий срез после отсутствия installed proof в отчёте ниже. Независимый
route, новые Android bytes, полный MTU и остальные release gates открыты.

[A03 cross-field и новый Core](EXECUTION-A03-CROSSFIELD-2026-09-08.md):
исправлены доказанные пробелы H/S/MTU/timing validation. Core `02a091c`, client
`295ceac`: две побайтно одинаковые сборки AAR/DLL, 100 DLL cycles, 80 runtime,
8 Android Flutter и 376 JVM tests PASS. Шесть живых MTU cases на Pi PASS.
Новые библиотеки привязаны в source; старые установленные phone/VM пакеты
не обновлялись. Их приёмка не переносится на новые bytes. Полный план открыт.


[Windows managed switching](EXECUTION-WINDOWS-SWITCHING-2026-09-08.md):
обычные reconnect AWG3.1 → AWG2 → AWG3.1 прошли на установленном v3 пакете.
Защищённый файл службы сменился и вернулся к исходному SHA; все три отключения
восстановили routes/DNS, 305 installed hashes совпали. Независимый route proof
остаётся OPEN: одинаковый внешний IP и неподтверждённый SSH host key DE.
Временная серверная настройка восстановлена; clone выключен, NIC none.

[Windows upgrade / installed cancellation](EXECUTION-WINDOWS-UPGRADE-MANAGED-2026-09-08.md):
исправлено завершение UI установщиком и удаление одного старого test EXE.
Повторный Win11 upgrade, 305 hashes, сохранённое состояние и обычный IPC PASS.
Реальный AWG31 connect и отмена проверены в ограниченном сценарии: 2110 мс,
TUN удалён, routes/DNS восстановлены. Одинаковый внешний IP ограничивает route
proof. Серверный cohort полностью восстановлен; host network прежний;
clone выключен, NIC отключён. Полная Windows/runtime/release матрица OPEN.
Локальная реализация и проверки ниже выполнены; production, новый release
candidate и postrelease activation не выполнены. Ранние отчёты сохранены как
последовательные срезы. Точные команды, SHA логов и source tuple —
[evidence/handoff-local.json](evidence/handoff-local.json).

[Windows IPC cancellation](EXECUTION-WINDOWS-IPC-CANCELLATION-2026-09-08.md):
client `0218e89` добавляет отмену активного connect, status во время операции,
отказ параллельным mutations, отмену WinHTTP и worker для вызовов из UI.
Native 12/12, Windows Flutter 24, runtime Flutter 80 PASS; Win11 component
fixtures PASS с сохранённым повтором integration после исправления payload.
Отмена/синтетический rollback — 31 мс, HTTP — 94 мс; installed 305 hashes прежние.
Новая пара UI/service с реальным TUN, Core blocking calls, WFP, Win10 и candidate OPEN.

[Windows connect interruption](EXECUTION-WINDOWS-CONNECT-INTERRUPTION-2026-09-08.md):
просроченный или остановленный connect больше не фиксирует защиту после позднего
возврата Core/probe. Между этапами выполняется проверка и штатный rollback;
ошибка восстановления сохраняет recovery_required. Native 8/8, runtime 80 PASS.
Прерывание внутри блокирующих вызовов, IPC cancel и concurrent mutations OPEN.

[Windows IPC timeout](EXECUTION-WINDOWS-IPC-TIMEOUT-2026-09-08.md): исправлена
блокировка единственного pipe и SCM stop зависшим клиентом. В VM новая служба
освобождает pipe за 3.0–3.05 с; stop при непрочитанном ответе — 10 мс.
После проверки восстановлен прежний пакет, все 305 хешей совпали. Полная
отмена сетевых операций и concurrent mutation acceptance ещё OPEN.

[Installed Windows IPC](EXECUTION-WINDOWS-IPC-2026-09-07.md): восемь проверок
реальной службы под обычным владельцем и отказ другому пользователю PASS.
PID named pipe совпал с SCM; все 305 installed hashes прежние. W06 остаётся
OPEN для cancellation/concurrency, WFP coexistence, Win10 и final channel.

[Windows installer](EXECUTION-WINDOWS-INSTALLER-2026-09-07.md): исправлен
отказ clean install для обычной учётной записи при UAC через другого admin.
На exact local package прошли install, standard UI/IPC, 305 file hashes,
uninstall/reinstall и auto SCM start после reboot. Managed network, connected
update/recovery, Win10 и final channel остаются открытыми.

Выполнен [Windows 11 component lab](EXECUTION-WINDOWS-LAB.md): отдельный linked
clone без NIC, текущие service/test bytes, семь native fixtures PASS. Подготовлен
SCM start/status/stop сценарий на том срезе ещё ожидал UAC. [Новый SCM run](EXECUTION-WINDOWS-SCM-2026-09-07.md)
прошёл с текущим Core: LocalSystem, IPC под ограниченным токеном, Initialize
и штатная остановка. W01–W03 и
реальный TUN/installer/network proof остаются OPEN.

Предыдущий [readback условий следующей приёмки](NEXT_ACCEPTANCE.md): найден выключенный
POKROV Win11 lab; Android 0; platform/client CI не стартует по billing/spending
annotations, enforcement API 403. VM availability не является runtime PASS.

Обновлён [G03 — source inputs и зависимости evidence](EXECUTION-G03.md):
250 изменённых файлов от task baseline, отдельный diff от candidate.33;
исправлена классификация dependency manifests и infra README. Старые runtime
receipts не получили автоматического reuse; final candidate proof остаётся OPEN.

Проверен [G01 scope record и M01 legal/seller review](EXECUTION-G01-M01.md):
все 83 slice metadata и 378 legacy references сохранены; G01 VERIFIED как
документационный критерий. M01 ждёт утверждённого продавца и receipt evidence;
legal/channel launch остаётся закрытым, дата части 10.8 — 01.09.2025.

Выполнен [B08 — локальный PostgreSQL restore и deployment contract](EXECUTION-B08.md):
encrypted snapshot/restore, additive migration, два workers и poison message PASS
на synthetic PostgreSQL; 198-file payload audit PASS. Последующий
[Linux SSH/systemd drill](EXECUTION-B08-DEPLOY-LAB.md) подтвердил автоматический
rollback при health 503 и delayed crash с восстановлением SHA всех 198 файлов.
[Полный remote PostgreSQL gate](EXECUTION-B08-REMOTE-PG.md) затем прошёл в этой
Linux VM: snapshot/restore 117 таблиц, ownership 1077 объектов, независимые
content hashes и исключение поздней записи; два synthetic attachment files
восстановлены отдельно из encrypted archive.
[Previous/current API compatibility](EXECUTION-B08-APP-COMPAT.md): настоящие
API из candidate.33 source и feature branch прошли 25 HTTP checks на общей
PostgreSQL, включая совместную работу и перезапуск previous. Production
recovery, exact deployed tuple/units и полный provider E2E остаются OPEN.

Выполнен [B07 — Linux DB/HTTP/outbox profile](EXECUTION-B07-PROFILE.md):
повторные burst measurements с queue wait и event-loop samples, reuse 20 HTTP
connections; два worker доставили 120 synthetic outbox events в provisioning
queue. Production profile остаётся OPEN; лимиты по fixture не менялись.
[B07 runtime readback и observer](EXECUTION-B07-RUNTIME.md): current-origin
health и brain-origin read-only SQL показали idle DB counters и пустую открытую
outbox queue. Добавлен lifespan-owned event-loop lag collector; проверен в
Linux API lab, на production не развёрнут. Нагрузочный профиль остаётся OPEN.

Исправлен [B06 — amount validation, outbox race и provider event dedupe](EXECUTION-B06.md):
`58e3684`; реальный PostgreSQL race PASS, provider/API fixtures PASS. Live
payment/refund и order binding нового reversal envelope остаются OPEN.

Исправлен [M05 — атрибуция и серверная воронка](EXECUTION-M05.md): клиентские
payment/self-report events больше не дают paid/connected outcome; IP referrer
и source очищаются на сервере и в browser cache. Provider E2E остаётся OPEN.

Последующий срез N05 — [наблюдения, новые Core bytes и проверки](EXECUTION-N05.md).
Он дополняет этот сохранённый срез от 2026-09-05.
Следом исправлен [лимит незавершённых Smart Connect probes — N06](EXECUTION-N06.md).

Дополнительно проверен [N08 — режимы маршрутизации и direct в VPN selectors](EXECUTION-N08.md).
Продолжение N08 (`5606fdc`): готовые Windows-профили применяют process/DNS-режимы с сохранением настроенных resolvers; локально 116 + 80 PASS, VM/device proof открыт.

Добавлено [C04/F01/F04 — остановка фоновых animation tickers и сверка presentation](EXECUTION-PRESENTATION.md): client `fa62f04`, 216 локальных тестов PASS; reference device performance открыт.

Исправлен [N01/N04 — repair против pending invalidation и смены режима](EXECUTION-N01-REPAIR.md): client `f024861`, 178 widget/lifecycle PASS.

Добавлен [A04 — согласованная выдача AWG material при ротации](EXECUTION-A04.md): 43 focused checks PASS; server revoke/expiry и interop OPEN.

Исправлен [A08 — ECH с разрешённым внешним SNI в Smart DNS](EXECUTION-A08.md): source `959d1f5`, Go/tooling/client checks PASS; live access/QUIC/fallback OPEN.

Добавлен [A07 — ограниченный переход lab → managed TCP](EXECUTION-A07.md): platform `f03a6a7`, client `45036ab`; 56 rollout/lab и 7 финальных client checks PASS, backend 154 + 8 subtests PASS; реальная UDP blackhole matrix OPEN.

Продолжение provisioning: [HY2 — одна проверенная запись при выдаче](EXECUTION-HY2-SNAPSHOT.md). Воспроизведена и исправлена подмена generation между readiness и render; server revoke/expiry остаются OPEN.

Сверен [D04 — direct/store update authority](EXECUTION-D04.md): существующие исходники, 22 JVM + 3 Flutter PASS; ADB 0 устройств, реальные update/data-preservation переходы OPEN.

Исправлен [D05 — фильтрация до native log sinks](EXECUTION-D05.md): Core `94dd310`, client `4539753`, новые AAR/DLL; 372 JVM, 190 shell, 80 runtime и 100 DLL cycles PASS. Physical lockscreen/journal/native-log/counters проверки OPEN.

Исправлен [V04 — связь обращения, попытки и версии](EXECUTION-V04.md): `2ba8e8e`; missing-linked attempt больше не подменяется, смена build обновляет known issues. 110 support/AI, 55 API и 80 browser tests PASS; live case и effective-profile proof OPEN.

Исправлен [V02 — сводка диагностического пакета](EXECUTION-V02.md): egress не подменяется последним служебным событием; unknown и отсутствие счётчика попыток сохраняются явно. 23 focused checks PASS; полная effective-profile correlation и O03 source decision OPEN.

Исправлен [release contract digest после N05](EXECUTION-RELEASE-CONTRACT.md): `aff9653`, 102 release tooling tests и 21 subtests PASS; synthetic fixture не является новым кандидатом.

Сверены [G05/G07 — metadata owners и source boundary](EXECUTION-G05-G07.md): 6/6 public asset metadata совпали с GitHub; private candidate artifact не истёк. Устранено смешение retained candidate с текущим source в client docs. 42 platform и 16 generator checks PASS; финальные packaged provenance/license и новый candidate остаются OPEN.

## Изменения

- Core: correlated endpoint/selector proof; Android/Windows AAR/DLL собраны
  повторно с побайтным совпадением и привязаны к клиенту. ABI2 сохранён.
- Клиент: reconnect обновляет профиль; stage/start/proof связаны с digest и
  upstream revision. Windows и Android сохраняют прежний файл при отказе
  до atomic replacement. Delayed consent/probe не подтверждает другой профиль.
- Клиент: отдельный owner managed-profile lifecycle; ограниченный retry
  250/500 мс + jitter; future-dated/старше 24 ч cache запрещён. Это не новый
  offline entitlement lease и не доказанный durable LKG rollback.
- Checkout: server-signed quote, немедленная invalidation ввода, deadline,
  честный legacy return и same-intent recovery. Реальный disposable PostgreSQL
  дал 8 PASS; повторный счёт провайдера не создаётся в выполненных fixtures.
- Cockpit: `pokrov.operator-cockpit-gates/v1`, count и `gate_f_decision=NOT_EVALUATED`.
  11 operational checks отделены от 19 final Gate F checks; связка областей
  описана в canonical monitoring owner. Registry rollback не выдаётся за deploy.
- Marketing: catalog deadlines и контраст hero-подписей во время входа.

## Последние проверки

- PASS: Core race/full suites, native CTest 8/8, оба Android flavor JVM gates,
  client workspace tests/analyze/seed. Подробные команды и границы —
  [EXECUTION-CONTINUED.md](EXECUTION-CONTINUED.md).
- PASS: новый cache-clock test + gate suite 5; AWG contracts 32; commercial
  revision/capacity contracts 23; diagnostics/observability contracts 33.
- PASS: cockpit service/evidence/manifest 27 + focused API 1; admin lint,
  build и 78 browser cases. Ранее полный admin API набор — 52 PASS.
- PASS: marketing build/SEO/responsive/axe; девять checkout scenarios;
  copy/governance/docs 72; 9/9 static performance stop budgets.
  Несколько целевых performance targets остаются недостигнутыми.
- Общий quality gate сохранён как FAIL из-за одного contrast finding.
  После `bf72daa` затронутые marketing и web-static checks прошли повторно.
  Client/cabinet checks из общего прогона не изменялись этим UI diff.
- Browser review: localhost 3187/3188, marketing 1180×820 и 390×844,
  admin 1440×900; непустые страницы, правильные title/URL, без overlay/page errors.
  Смена кандидата сохраняет заметку о незагруженном Gate F. Synthetic API,
  внешние запросы заменены fixtures. Скриншоты: `E:/r12-ui-review/`.

## Что требуется для продолжения обязательной цепочки

| Условие | Связанные пункты | Фактическое состояние |
| --- | --- | --- |
| Источник operator profile/proof данных | O03/V02/V04 | NEEDS_CONTEXT: pending выбор opt-in support bundle либо нового минимального account-bound отчёта. Новый сбор не включён. |
| Exact source tuple, candidate и hosted CI/signing lane | G04/G06/G07/C05/Q01 | Source commits локальные; нового кандидата нет; private rules readback вернул 403. Финальный license/privacy scan требует новых packaged bytes. |
| Разрешённая Windows VM и exact package | W01–W06/N01–N03/N08/F07 | Найдена выключенная POKROV-Win11-Test; см. NEXT_ACCEPTANCE. Current guest baseline и exact new installed-package proof не проверены; host VPN не заменялся. |
| Физический Android и primary ARM64 APK | D01–D06/N01–N03/N08/F05/F07 | ADB readback: 0 устройств. JVM и desktop screenshot не заменяют physical/Doze/radio proof. |
| Owned lab/server + независимые origins | A02/A04–A09/N07/Q02 | Новый artifact/server/profile tuple и runtime/origin матрица не выполнены. 32 local AWG tests не являются interop PASS. |
| Provider, restore/deploy rehearsal и operator identity | B06/B08/O01/O02/O04/O06/M01 | Реальные payment/refund, DB recovery, OIDC и deployed fingerprint не проверены. Local API/browser fixtures ограничены I3. |
| Exact candidate acceptance и owner release decision | Q01–Q05 | Отдельное решение Gate F ещё невозможно; public rollout, channel, cohort и observation требуют конкретного разрешения после gates. |

N02 остаётся PARTIALLY_FIXED: исправлен сбой завершения recovery journal
после `recovered`, client commit `20b997a`, native 9/9 PASS.
[Новый срез N02](EXECUTION-N02.md) сохраняет regression/evidence и вопрос
политики rollback. Durable last-known-good с entitlement/expiry ещё не доказан.
N05/N06/C03/C04/F04 и другие оставшиеся source/optimization
части не объявлены завершёнными из соседних PASS; их не требуется механически
переписывать без проверенного дефекта или измеренного узкого результата.
Полный текущий статус всех 83 строк сохранён в [реестре](R12-REGISTER.csv).

Linux beta, новый ATS/Broker, Smart DNS/HAPP и `/t/` остаются в условной/postrelease
очереди по исходной последовательности. Release 1.2.0 не закрыт, owner не менял
activation gate. Внешний маркетинговый пилот, spend и публикации не запускались.

## Git и rollback

Platform feature branch: `codex/consolidated-plan-start-20260905` — product
commits `917612f`, `5577bb7`, `bf72daa`, `7e8beab`.
Client feature branch: `codex/r12-client-implementation` — `8176c3b`,
`cebbe851`, `61d1838`, `4dbe2c6`, `20b997a`.
Core feature branch/HEAD — в source tuple, commits `9476df5`, `3f52efd`.
Push, merge, deploy и новый candidate: **NOT_PERFORMED**.

Rollback source — отмена соответствующего scoped commit в своей feature branch;
UI/service identity protocol возвращать согласованной парой. Candidate.33 и
historical receipts сохранены; прежние release artifacts не переписаны.
Основной dirty checkout и чужие файлы не включены. Generated instruction files
marketing/AGENTS.md и CLAUDE.md и четыре line-ending-only client registrants
оставлены вне commit. Временные browser servers этой проверки остановлены;
логи и скриншоты сохранены.

## C05 — Core dependency remediation, 2026-09-06

[Исправлены два reachable SSH deadlock advisory](EXECUTION-C05.md): Core `8dc57a8`, Go 1.26.8 / x/crypto 0.56.0 / tfo-go 2.3.3 и совместимый Psiphon TLS mirror. Две пары локальных DLL/AAR byte-identical; full gate, 15 exports и 100 proxy-only cycles PASS. Binary findings имеют module precision (0 extracted symbols); девять ID и license gaps сохранены. Client binding пока D05, final APK/EXE/license/privacy gate открыт.

## C05 consumer binding — 2026-09-06

[Client C05 binding и backtests](EXECUTION-C05-BINDING.md): `c2c6f96` использует Core `8dc57a8`. 80 runtime + 8 Android Flutter + 372 JVM tests и 100 synced DLL proxy cycles PASS. Обнаруженная Git normalization исправлена для новых receipt JSON; проверены committed blobs и LFS OIDs. Final package/license/privacy и device/SCM/origin gates остаются открытыми.

## C05 package audit — 2026-09-06

[Локальные APK/EXE inventories и packaging fixes](EXECUTION-C05-PACKAGES.md): client `7a8fd55`. Исправлены отсутствие Golos OFL и попадание native test EXE в Windows bundle. Четыре local debug-signed release-mode APK, Windows release bundle, 8 CTest, analyze/seed/docs PASS. OSV: 0 IDs для 138 Pub/Maven runtime graph records; native/Flutter/Cronet scope этим не покрыт. Сохранены 128 Go module entries и 130 root notices; native/source/privacy и exact candidate gates остаются OPEN.


## C05 Cronet origin — 2026-09-06

[Происхождение pinned Windows Cronet](EXECUTION-C05-CRONET.md): upstream release asset побайтно совпал с DLL; закреплены tag `82e1521` и declared native gitlink `2be061b6`. Source archive: 30561 exact + 30 line-ending-only matches, без необъяснённых расхождений. Сохранён 69-file source license review archive; exact Windows linked notices и source reproducibility остаются OPEN. Client manifest и readiness обновлены, runtime bytes прежние.


## C05 native notices — 2026-09-06

[Windows Cronet graph и обязательный notice в bundle](EXECUTION-C05-NOTICES.md): 558 recursive GN dependencies; восстановлены отсутствовавшие Perfetto/Protobuf/compiler-rt licenses и дополнительные attributions. 28 секций включены через CMake; изолированный bundle содержит 301 файл, остальные 300 побайтно прежние. Полный C05 licensing/privacy gate, source reproducibility и release/device/runtime gates остаются OPEN.

## C05 Go notices в пакетах — 2026-09-06

[Поставка native Go notices](EXECUTION-C05-GO-NOTICES.md): client `1032c48`.
145 license/patent текстов включены общим asset и связаны с Core source,
toolchain и SHA-256. Четыре internal debug-signed APK и unsigned Windows bundle
содержат точные notice bytes; Core binaries прежние. Windows: 302 файла,
добавлен notice, изменён AssetManifest, остальные 300 прежние. Seed/docs PASS.
Psiphon utls, вложенные/native notices, source delivery и полный C05 остаются OPEN.

## C05 вложенные Go notices — 2026-09-06

[Вложенные notices и utls upstream readback](EXECUTION-C05-NESTED-NOTICES.md):
client `b0f4374`, ещё 28 текстов, всего 173. Пять графов с флагами из AAR/DLL
покрыли все 128 записанных modules; fresh build-info совпал. Четыре APK и
Windows bundle PASS; в Windows изменился только notice, 301 файл прежний.
298 файлов Psiphon utls совпали с upstream: root license действительно отсутствует.
Scoped dicttls license добавлен; полный C05, source delivery и runtime gates OPEN.

## C05 residual advisory triage — 2026-09-06

[Статический разбор девяти ID](EXECUTION-C05-TRIAGE.md): семь not_actionable
для текущих пяти runtime targets; два sumdb needs_review из-за неподтверждённой
истории аутентификации module cache. Go 1.26.8 исправлен, runtime sumdb отсутствует.
Исходные scanner records сохранены. C05 остаётся PARTIALLY_FIXED; новый candidate,
runtime checks, push/merge/deploy в этом срезе не выполнялись.

## C05 sumdb source authentication — 2026-09-06

[Независимая проверка 123 внешних modules](EXECUTION-C05-MODULE-AUTH.md):
246 checksums и 16 868 файлов совпали с fresh authenticated downloads,
6751 выбранный source file неизменен. Два sumdb needs_review закрыты как
not_actionable для текущего source/artifact tuple; прежний triage сохранён.
Полный C05 остаётся PARTIALLY_FIXED: licenses/source delivery/installed privacy
и final candidate gates открыты. Runtime bytes, push/merge/deploy не менялись.

## C05 source preparation — 2026-09-06

[Пакет исходников Core](EXECUTION-C05-SOURCE-PACKET.md): 3670 verified entries,
3161 Git blob, 123 authenticated modules и отдельные Android/Windows native
source archives. Пять offline source graphs совпали с исходными. Android
Cronet .a связываются с `f21660be` → `30f3a568`; Windows остаётся `2be061b6`.
Это SOURCE_PREPARATION_ONLY, полный C05 открыт; publication, native reproduction,
client licensing и installed privacy не подменены локальной упаковкой.

- 2026-09-07: [W04 Windows shell](EXECUTION-W04-SHELL.md) — hidden startup and native teardown fixed; exact offline UI regression/exit proof retained, full Windows matrix open.

- 2026-09-07: [Pi/Huawei hardware runs](EXECUTION-RUNTIME-SURFACES-2026-09-07.md) — exact-Core AWG2/AWG3.1 PASS on owned Pi; bounded Android handoff/protection, first interruption retained as unresolved.
