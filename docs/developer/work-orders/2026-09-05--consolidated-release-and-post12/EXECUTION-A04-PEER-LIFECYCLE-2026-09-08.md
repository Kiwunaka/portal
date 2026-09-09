# A04 — отзыв и замена отдельного peer на owned AWG server

**PASS_BOUNDED** для серверного удаления и замены временного peer в AWG2 и
AWG3.1. Полный A04 остаётся **ACTIVE / I3 / NEEDS_RUNTIME_PROOF**: тест управляет
peer непосредственно через `awg`, не через account/device provisioning API.

Точный Core `02a091cb0e369192a5ad0909b56ccba8aa1dce17` собран в отдельный
Linux ARM64 test binary SHA-256
`0f1d735609fb00b9dd0480b6090d4b8c1cbdce5661cd9b7d9b629d192482fb08`.
Исполнение — owned Raspberry Pi 4, SSH `shrek`, с проверкой прямого default
route. Это один RU lab origin; Android/Windows package и независимая
операторская матрица этим запуском не проверяются.

DE использует прежний native server `amneziawg-go-v3.1.20260814`, SHA-256
`4ede58a7d4bc79bce152850ef7aa0ee5885de592d5d095352ae869b3fe8f172d`.
Исходные service/config/process identities связаны с [A02](EXECUTION-A02-2026-09-08.md).
Каждый протокол получил два новых случайных тестовых ключа и отдельный
неиспользуемый адрес в существующей lab-подсети. Исходный peer не удалялся
и не переназначался. Приватные ключи и endpoint material оставались в памяти
и SSH stdin; в evidence сохранены только hashes и безопасные результаты.

Для каждого протокола выполнена последовательность:

1. Добавление ключа A: TLS и ожидаемый authenticated HTTP egress marker PASS;
   сервер подтвердил handshake и двусторонние counters.
2. Удаление peer A: тот же клиентский ключ не получил outer response за
   45-секундный deadline. Проверен отказ выбранного subtest, а не произвольный
   process error или пропуск.
3. Добавление ключа B на тот же тестовый адрес: authenticated egress PASS,
   новый handshake и двусторонние counters.
4. Повтор со старым A после замены: такой же ожидаемый отказ.
5. Повтор с B: authenticated egress PASS. Это отделяет отказ A от общей
   недоступности пути в выполненной последовательности.

Итого 10 ожидаемых результатов: шесть положительных и четыре отрицательных.
Отрицательные результаты являются PASS oracle отзыва, но сохраняют реальный
test exit code 1 и classification `failed_no_outer_response`.
Проверялся MTU 1280; новая полная MTU/performance матрица не заявляется.

Контроллер удалил только созданные test peers через `finally`; EOF и отдельный
20-минутный deadline также вызывают cleanup. Оба live static config hashes
вернулись к исходным; исходные peer identities, сохранённые configuration files,
units и running binary hashes совпали. Временные Pi binaries удалены.
Server configuration files, backend settings, accounts, sessions, телефон,
Windows VM и host VPN не менялись.

## Проверки и evidence

[Receipt](evidence/a04-peer-lifecycle-20260908/receipt.json) связывает безопасные
результаты, retained collector scripts, exact build и независимые server
readbacks до/после. Raw captured test output не сохранён; его SHA-256 и
классификация вычислены в памяти. Это ограничение диагностики явно сохранено.

Команды из `E:/r12-a04-peer-lifecycle-20260908`, exit 0:

```powershell
python -B prepare.py
python -B E:/r12-a02-server-20260908/server-readback.py E:/r12-a04-peer-lifecycle-20260908/server-before.json
python -B run.py awg2_lab
python -B run.py awg31_lab
python -B E:/r12-a02-server-20260908/server-readback.py E:/r12-a04-peer-lifecycle-20260908/server-after.json
python -B verify-and-retain-v3.py
```

Итоговый verifier проверил 14 retained files. Две предыдущие ошибки verifier
сохранены: v1 требовал неизменности TX нового peer в период проверки старого
ключа; RX и handshake фактически не менялись, а причину роста TX этот тест
не устанавливает. V2 затем принял строку PEM-маркера в собственном исходнике
за ключ. V3 проверяет нужные RX/handshake поля и форму блока PEM. Runtime и
сами результаты не менялись; частично скопированные файлы сохранены побайтно.

Документационные gates: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py
--platform-context-root .` — PASS; `validate_package.py` — 83 R12 IDs,
378 legacy IDs и 376 local links PASS; `git diff --check` — PASS.

Остаются отдельными: API/device-bound rotate/revoke/expiry и утрата устройства,
одноразовые/повторные запросы, concurrent PostgreSQL issuance, installed-client
реакция и полная telemetry/support проверка. В частности, ручной `awg remove`
не доказывает автоматическое удаление peer после device revocation или expiry.
Новый candidate, push, merge, production deploy и публикация не выполнялись.
