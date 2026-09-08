# W01 — подготовка Windows 10 и блокер активации

**BLOCKED_BY_ACCESS: WINDOWS10_EVALUATION_NOT_LICENSED.** Отдельная owned VM
с Windows 10 Enterprise LTSC 2021 Evaluation установлена, но POKROV на ней
не устанавливался и runtime-проверки не запускались. [Receipt](evidence/win10-access-2026-09-08.json)
связывает клиентский отчёт с сохранёнными результатами. Полный W01 открыт.

Официальный Microsoft ISO — 4 898 582 528 байт; SHA-256
`e4ab2e3535be5748252a8d5d57539a6e59be8d6726345ee10e7afd2cb89fefb5`
совпал с официальным PDF и повторно проверен при сохранении evidence.
Гость: 21H2 / `10.0.19044.1288`, 2 vCPU, 4 GiB configured RAM.
Первый unattended setup остановился на license-terms dialog; после удаления
пустого ProductKey node установка завершилась. История обеих попыток сохранена.
Обычная тестовая учётная запись не входит в Administrators; UAC и Defender
включены, POKROV UI/service отсутствуют.

Evaluation сразу сообщила LicenseStatus 5 / GracePeriodRemaining 0. Две обычные
elevated попытки `slmgr.vbs /ato` в 05:52 и 05:58 UTC вернули `0x87E10BC6`,
статус и grace не изменились. Первичный activation endpoint подтвердил TLS 1.2;
вторая TLS-проверка legacy endpoint завершилась ошибкой. Это не доказывает
необратимое отключение активации Microsoft или необходимость покупки лицензии.
Доступ к уже лицензированному Win10-стенду запрошен у владельца; ответа пока нет.

Запланированный локальный пакет — client `e88dff9` / Core `02a091c`, installer
SHA-256 `29a87a13906909e400037a947f1e4f876ca59821e7e34c73060e623f2d9fbeea`.
Его приёмка Win11 не переносится на Win10. Ключи не приобретались и не вводились,
таймер evaluation не сбрасывался, время не переводилось назад.

Конечное состояние: новая VM выключена, NIC none, ISO на host размонтирован,
routes/DNS host неизменны. Исходная VM и Win11 lab также выключены.
Приватные credentials и answer media не включены в evidence; receipt удерживает
23 выбранных file/hash references, включая ISO. Нового build/release candidate,
push, promotion, publication или deploy в этом срезе не было.

Проверки документации: client evidence commit `2d93c95`; explicit-root
`scripts/validate-seed.ps1` PASS, включая docs contract.
`python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py --platform-context-root .`
— PASS. Work-order `validate_package.py` — PASS: 13 imports, 83 R12, 378 legacy,
313 local links. `git diff --check` PASS; `artifacts/releases/**` неизменны.
Логи сохранены в `E:/r12-win10-lab-20260908/`.
