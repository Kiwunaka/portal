# W05 — Windows idle CPU/RAM

**PASS_BOUNDED**, client `e88dff9`, Core `02a091c`, current-origin owned Win11
VM. [Receipt](evidence/windows-idle-2026-09-08.json) связывает клиентский
отчёт, exact source, installer и сохранённые измерения. Полный W05 открыт.

Двухсекундный observer сообщал UI/tray об изменениях даже при одинаковом
runtime snapshot: тест воспроизвёл 60 лишних уведомлений за две минуты.
Client `e88dff9` сравнивает все 35 полей, включая profile source/revision,
и пропускает одинаковый результат. Polling и защита от поздних ответов
сохранены; изменение здоровья/профиля и падение службы по-прежнему доходят
до интерфейса. Регрессия проходит с нулём лишних уведомлений.

| Пакет | UI CPU p95 | Service CPU p95 | CPU вместе p95 | RAM вместе p95 |
| --- | ---: | ---: | ---: | ---: |
| До: `68a44e5` | 1,498057% | 0% | **1,498296% FAIL** | 117 440 512 B |
| После: `e88dff9` | 0,748937% | 0,749664% | **0,749983% PASS** | 120 459 264 B |

Перцентили процессов отдельно не складываются. Ноль service p95 до изменения
получен из доступных накопительных счётчиков; отсутствие счётчика останавливает
замер. Дельты всех 90 интервалов пересчитаны независимо, native UI readback
совпал с WMI. Оба прогона: одна загрузка VM, 2 vCPU/4 GiB, Windows 11
10.0.26200, Balanced, NIC none, foreground disconnected UI и LocalSystem
service. 30 прогревочных и 60 зачётных интервалов; номинальный шаг 1 с,
зачётное время 62,5838301 / 62,6141668 с. CPU нормирован по двум vCPU.

Канонический `performance_budget_gate.py` вычислил PASS по лимиту CPU 1%.
Fingerprint RAM совпал с новым baseline до исправления: рост **2,570452%**,
PASS по ограничению 10%. Абсолютного RAM-порога это не устанавливает.

Installer `29a87a13…9fbeea` установлен обычным wizard/UAC. Изменился только
`data/app.so`; 305 установленных файлов совпали, saved state сохранён,
reboot не понадобился, обычный owner IPC accepted/trusted. Первый запуск
collector отказался от сбора из-за UI, перезапущенного Restart Manager;
он сохранён отдельно и не входит в выборку. После остановки того процесса
новый прогон завершился. Финальные 305 hashes совпали, UI 0, service Running.
VM выключена, NIC none; source VM оставалась off; host routes/DNS прежние.
Backend и сеть host не менялись.

Проверки клиента: shell 188 PASS; runtime 81 PASS и 1 opt-in skip;
Windows Flutter 24 PASS; analyze без замечаний; explicit-root seed PASS;
build/package PASS в отдельной локальной папке. Логи привязаны к receipt.

Проверка сохранённого результата:

- `python -B E:/r12-windows-performance-20260908/normalize.py`: все 90 дельт
  каждого прогона совпали; canonical before CPU FAIL / after CPU PASS.
- `python -B E:/r12-windows-performance-20260908/compare-memory.py`: matching
  fingerprint и RAM regression PASS.
- Из client: `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/validate-seed.ps1 -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start -CoreRoot E:/r12core-implementation`: PASS.
- Из platform: `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`: 33 PASS.
- `python -B scripts/agent_context_packet_audit.py --platform-context-root .`: PASS.
- `python -B docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/validate_package.py`:
  PASS, 13 imports / 83 R12 / 378 legacy IDs / 309 local links;
  `git diff --check`: PASS. `artifacts/releases/**`
  не менялись. Client evidence commit: `c6858e7`.

Зачёт полезного cold start прежнего candidate.33 отозван в текущем owner:
terminal того collector требовал только responsive window и UIA Pane,
а готовность экрана защиты не проверял. Старые 1499,404 ms и raw evidence
сохранены как исторический замер появления окна. Полезный cold start,
warm/cold/post-reboot distributions, Win10, physical/comparable hardware,
connected/tray-hidden состояния и final-channel gate остаются открытыми.
Публикации, promotion, deploy и нового release candidate не было.
