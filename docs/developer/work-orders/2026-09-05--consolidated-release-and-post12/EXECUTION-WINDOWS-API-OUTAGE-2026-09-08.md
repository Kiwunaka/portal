# N02/N07 — установленный Win11 при отказе API

**PASS_BOUNDED**, unchanged installed client `e88dff9` / Core `02a091c`, Win11
`10.0.26200`, owned VM с NAT, managed AWG3.1, current-origin.
[Receipt](evidence/windows-api-outage-2026-09-08.json) связывает 13 phase samples,
23 observations, cache metadata и 44 retained artifacts. Все 305 installed
files совпали до и после. Полные N02/N07 и final channel остаются открытыми.

Два временных program-scoped firewall rules блокировали TCP 80/443 у stock UI
и контрольного PowerShell. Контрольный HTTPS-запрос получал ConnectFailure,
отдельный Curl-запрос к нашему `/health` возвращал 200. Core/Curl не блокировались.
Это локальная имитация недоступности клиентского web/API-трафика; live API
не выключался и carrier-side outage не утверждается.

- Работающий туннель: 23 healthy samples за 61 023 мс, те же UI/service PIDs.
- Disconnect/reconnect при блокировке: новое runtime proof, connected event
  отмечает сохранённые настройки.
- Остановка и новый запуск UI при блокировке: новый PID, cached connect и
  runtime proof. Кеш восстановлен из защищённого хранилища.
- После снятия блока обычный reconnect снова скачал профиль. Исходное время
  проверки 06:43:49.127336 UTC сменилось на 06:54:39.360313 UTC.

Во всех семи blocked phases timestamp, binding/revision/payload/cache-entry
hashes downloaded/proven records неизменны. Read-only DPAPI collector работает
в той же обычной guest identity; он сохраняет только времена и comparison
hashes, не пишет store и не экспортирует profiles/credentials/keys.
Реальное истечение 24 часов, explicit 401/403 и remote revocation на installed
bytes не проверялись. Это не разрешение на бессрочный офлайн-доступ.

Все четыре disconnect восстановили routes/DNS; TUN удалён. 488 исходных
firewall rules и выбранные filters сохранились. Два fixture rules удалены,
click task отсутствует, UI остановлен, Auto LocalSystem service Running перед
shutdown. Backend rollout полностью восстановлен; VM off/NIC none, source VM
off, host routes/DNS прежние. IPC helper с собственной меткой `0218e89` привязан
отдельным SHA; эта метка не подменяет application source.

Открыты Win10, network-side/API-only варианты, independent route/effective
location и exact final channel. Код и пакет не менялись; build/push/promotion/
publication/deploy не было, `artifacts/releases/**` неизменны.

Guest: `firewall.ps1 -Mode Prepare|Enable|Disable|Cleanup` через обычный UAC,
`sample.ps1 -Label <phase>`, `observe-outage.ps1`, `final-identity.ps1` завершились
успешно. Соединением управлял stock UI. Host:
`python -B E:/r12-windows-api-outage-20260908/retain-evidence.py` — PASS для
13 phases / 23 observations / unchanged cache / online renewal / 44 hashes;
`pwsh -NoProfile -File E:/r12-windows-api-outage-20260908/finish.ps1` — PASS.

Client evidence commit `d482d18`: explicit-root `scripts/validate-seed.ps1`
PASS после возврата retained candidate label в первые 45 строк readiness;
первый failed log сохранён. Platform docs/context tests — 33 PASS;
`python -B scripts/agent_context_packet_audit.py --platform-context-root .` — PASS.
Work-order `validate_package.py` — PASS: 13 imports, 83 R12, 378 legacy,
317 links. `git diff --check` PASS; release artifacts неизменны. Логи в lab dir.
