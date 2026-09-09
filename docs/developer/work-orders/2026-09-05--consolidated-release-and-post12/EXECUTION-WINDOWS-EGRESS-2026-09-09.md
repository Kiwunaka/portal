# Windows — отказ выхода через установленный Core

**FAIL_EGRESS_UNCONFIRMED**, current-origin owned Windows VM; client
`c05b58b268bbd789aa96fb662cb46c9768558ef0`, Core
`c7a11f7d2fd974726095ad7aa0619c055273dd15`. Установка совпала по всем 304
файлам, session и secure storage сохранены. Подключения к обычным профилям
Милана и Франкфурта не проходят; новый candidate и выпуск не созданы.

Canonical evidence находится в client:
`docs/operations/evidence/2026-09-09-r12-windows-egress/README.md` и
`receipt.json`. Исходные captures и диагностические инструменты сохранены в
`E:/r12-win-egress-20260909/`. Receipt содержит hashes 15 safe captures и восьми
локальных instrument files, включая compiled probe. Строки из Windows UTF-16
и UTF-8/BOM нормализованы в UTF-8/LF с сохранением обоих hashes.
Client evidence commits `c4c13d9` и `f35a146` отправлены в feature branch;
15 hashes повторно совпали со staged Git blobs. Product source не изменился.

После штатного выключения VM её NIC переключён из none в NAT и проверен.
Истёкшая owned Windows identity получила один день через обычный
`user.extend` action-intent; payment/refund не выполнялись. Проверка backend
показала частичную синхронизацию: шесть нод из семи. На обеих проверяемых нодах
запись включена, UUID совпадает с User и UserNode; трафик этой identity равен
нулю, last-online отсутствует. Это не blanket PASS provisioning.

Пробы отделили отказ Core от доступности API:

- Та же WinHTTP-проверка вне туннеля: 219 ms, HTTP 204, ожидаемый marker.
- При наличии `tun0`: WinHTTP 12002/12007, service
  `core_egress_probe_failed`, rollback в `config_staged` без работающего TUN.
- HTTPS с заранее разрешённым адресом API и обычной проверкой сертификата:
  curl 35 / HTTP 000 при работающем TUN. Отдельный DNS query не получил адрес.
- Core mixed listener присутствует, но SOCKS5 remote-DNS request вернул curl
  97 / HTTP 000 до rollback. Отказ не сводится к отсутствию listener или
  системному DNS Windows.
- Все девять сравнений inbound Франкфурта с backend совпали. Порты Милана
  443/10443 различаются; без сверки внешнего forwarding path это не доказанный
  дефект доставки и не основание менять production-конфигурацию.

Диагностический CLI содержит собственный source marker `0218e89`; он не
подменяет источник установленного клиента `c05b58b`. Первые сборки отдельной
пробы не запускались без dynamic C++ runtime; static build исправил только
инструмент. Первая DNS-проба остановилась на обработке stderr в PowerShell;
v2 сохранила ошибку curl и завершила наблюдение. Ошибки инструментов не
приписаны установленному пакету.

Автоматическая проверка отклонила запуск reader с повышением прав:
`blocked by policy`; он не выполнялся. Владелец получил готовый read-only
`C:/Users/Public/R12Current/read-protected.ps1` для ручного запуска в VM.
Он сохраняет коды событий Core и безопасную проекцию DNS без ключей/raw
профиля. Этот результат и устранение причины отказа остаются открытыми.
На последнем readback служба Running, `tun0` отсутствует. VM пока оставлена
с NAT для ожидаемого чтения; после проверок нужен возврат к offline baseline.
Huawei не виден в ADB; установленный AWG и UI readback после исправления
подписки не выполнялись.

Изменений product code, host network, server keys или runtime policy в этом
срезе нет. N01/N02/N03/W01/W03 остаются active; успешная установка и rollback
не закрывают положительное подключение или весь план.

Проверки: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; work-order `validate_package.py` — 83 R12
ID и 471 local links PASS. Client `validate-seed.ps1` с явными platform/Core
roots — PASS; 15 hashes/JSON и восемь instrument hashes совпали.
`git diff --check` — PASS в обоих worktrees; release artifacts без изменений.
