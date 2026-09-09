# W05 — готовность экрана защиты при запуске Windows

**PASS_BOUNDED**, local client `e88dff9`, Core `02a091c`, owned Windows 11 VM,
current-origin. [Receipt](evidence/windows-startup-2026-09-08.json) привязывает
клиентский отчёт, package identity, сырые измерения и canonical gate. Код
приложения и установленный пакет в этом срезе не менялись. Полный W05 открыт.

| Сценарий | Warmups / retained | p95 | Максимум retained | Предел 3500 мс | Цель 2000 мс |
| --- | ---: | ---: | ---: | --- | --- |
| Новый процесс, прогретая ОС и file cache | 3 / 20 | 765,5534 мс | 818,7529 мс | PASS | Достигнута |
| Первый UI после power-on/login VM | 3 / 20 | 2311,4823 мс | 2628,5073 мс | PASS | **Не достигнута** |

Вторая серия включает 23 shutdown/power-on/login цикла с разными фактическими
boot timestamps Windows. Первые три отброшены; двадцать сохранены. В каждом
цикле подтверждены исходный logged-out state, обычный owner login, отсутствие
UI и Run-key autorun. Таймер запускается через две секунды после login guard,
не включает загрузку ОС, вход пользователя и автоматический запуск службы.
Служба уже Running. Это распределение после загрузки VM; physical disk-cache
и power-cold условия оно не доказывает.

Terminal требует доступные видимые кнопки «Подключить» и состояния защиты,
навигацию «Защита», положительные размеры controls, отсутствие onboarding и
ошибок accessibility. MSAA `OBJID_CLIENT` читается только у `FLUTTERVIEW`;
сохраняются allowlisted labels. Найденная кнопка состояния отдельно нажата:
открылись подробности защиты, screenshot сохранён. Responsive window больше
не даёт полезный startup PASS. Старый candidate.33 Pane-only credit остаётся
отозванным; исторические bytes и результаты сохранены.

Stopwatch считает от `Start-Process` до этого terminal, включая MSAA
activation/inspection с номинальным шагом 25 мс. Это верхняя наблюдаемая граница
семантической готовности, не точный pixel-render timestamp. Независимо проверены
все 46 terminal records и разметка samples. P95 рассчитан canonical validator
методом nearest rank; fingerprints двух сценариев различаются, regression
baseline не использован и пороги не изменены.

Окружение: Windows 11 Enterprise Evaluation `10.0.26200`, VirtualBox,
2 vCPU / 4274917376 B RAM, Balanced, Flutter 3.38.5 release,
PowerShell 5.1.26100.9168, NIC none, обычный non-admin collector. Все 305 файлов
сверены перед warm batch, **после** каждого post-boot sample и перед выключением.
Это исключает прогрев app files проверкой хешей перед post-boot замером.
Финально UI 0, Auto LocalSystem service Running, VM off/NIC none, source VM off,
host routes/DNS unchanged. Backend не менялся.

Ранние PowerShell COM walkers отказали до измерений и сохранены отдельно.
Первый normalizer остановился на `.5000000Z` против `.5Z`; сравнение parsed UTC
instants подтвердило все 23 разные загрузки без правки raw evidence. Временные
ошибки VBox console query при shutdown не удовлетворяли poweroff guard:
дальнейший power-on требовал успешного подтверждения выключения.

Команды измерения и проверки:

- `pwsh -NoProfile -File E:/r12-windows-startup-20260908/run-postboot-series.ps1`:
  MEASURED, 23/23; исходный warm collector — 23/23.
- `pwsh -NoProfile -File E:/r12-windows-startup-20260908/finish-startup.ps1`:
  305 hashes PASS, return state PASS.
- `python -B E:/r12-windows-startup-20260908/normalize.py`:
  оба stop PASS; postboot target false. Existing outputs защищены от overwrite.
- Из client: `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/validate-seed.ps1 -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start -CoreRoot E:/r12core-implementation`:
  PASS, включая client docs contract; evidence commit `f972a4c`.
- Из platform: `python -B -m pytest -p no:cacheprovider tests/test_performance_budget_gate.py tests/test_collect_web_performance.py tests/test_api_latency_probe.py tests/test_new_performance_evidence.py tests/test_release_1_2_local_quality_gate.py -q`:
  30 PASS.
- `python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`:
  33 PASS; `python -B scripts/agent_context_packet_audit.py --platform-context-root .`:
  PASS.
- `python -B docs/developer/work-orders/2026-09-05--consolidated-release-and-post12/validate_package.py`:
  PASS, 13 imports / 83 R12 / 378 legacy / 311 local links;
  `git diff --check`: PASS. `artifacts/releases/**` не менялись.

Windows 10, physical/comparable hardware, physical cold-cache conditions,
connected/tray-hidden performance и exact final channel остаются открытыми.
Публикации, promotion, deploy и нового release candidate не было.
