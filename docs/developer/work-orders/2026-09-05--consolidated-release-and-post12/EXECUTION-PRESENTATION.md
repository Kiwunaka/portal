# R12-C04 / F01 / F04 — lifecycle и presentation, 2026-09-06

**PARTIAL / I3 / NEEDS_RUNTIME_PROOF.** Client commit `fa62f04`.
[Точные команды, SHA исходников/логов и ограничения](evidence/c04-presentation.json).

## C04: подтверждённое исправление

Скрытые вкладки уже имели `TickerMode` и `RepaintBoundary`. Общего gate на
неактивность приложения не было: в живом Flutter fixture с открытым modal
opacity skeleton продолжала меняться после `inactive`. До исправления
0.674155693501234 превратилось в 0.5665494240820408 за 250 ms.

`PokrovAppMotionGate` в существующем motion module отслеживает app lifecycle.
Он оборачивает navigator через MaterialApp builder и глушит widget tickers
в non-resumed состояниях. После возврата tickers продолжаются с сохранением
дерева и modal. Runtime operations, timers и foreground refresh имеют прежних
владельцев. Новых part, зависимостей и runtime polling нет; root содержит
только подключение gate. DESIGN и motion capture procedure обновлены.

Регрессия теперь проходит. Общий прогон — 216 PASS, включая deterministic
critical-state goldens; analyze и validate-seed — PASS. Локальный прогон
проверяет событие Flutter, а не доставку focus/lifecycle реальным host.

Открыто по полному C04: эксперимент traffic 2–4 Hz, подтверждение rebuild
изоляции profile на traces, reference Android/Windows frame/CPU/battery
измерения. Уменьшение CPU, энергии или latency здесь не заявляется.

## F01 / F04: сверка уже существующего поведения

| Требование | Текущий source / проверка | Результат |
| --- | --- | --- |
| Один Home presenter для state/CTA/disc/copy/semantics | ConnectionExperienceReducer, ConnectionPresentation, ProtectionViewState; presentation boundary | I3 PASS |
| STARTED без proof не даёт success | connection_experience tests: all host enums, unverified/degraded, отдельные disconnect/reconnect intents | I3 PASS |
| Haptics и раскрытие технических деталей | ConnectionHapticCoordinator tests; protection details/repair и semantic-source widget tests | I3 PASS |
| Basic и advanced rules, объяснение reconnect | rules-advanced disclosure; advanced controls persist; one apply/one reconnect widget tests | I3 PASS |
| Latency unknown/age и origin | device RTT test скрывает server RTT до локального замера; locations source отображает timestamp/age/stale | I3 PASS для fixtures; stale aging на устройстве OPEN |
| Access/devices/support выше rewards | profile_surface порядок блоков; profile/support widget scenarios | SOURCE_REVIEW, полный visual/semantics acceptance OPEN |
| Smart DNS не равен полной VPN-защите | В проверенных текущих protection/rules surfaces нет Smart DNS режима; его отдельная активация остаётся gate планов | NOT_REQUESTED для этой реализации; перед активацией нужен отдельный acceptance |

F01/F04 переведены из NOT_REVIEWED в active I3 с указанными границами.
Полная device/VM acceptance, N03/N08 effective route proof и последующие
Smart DNS изменения не закрыты. Это не новый релизный GO.

Core/AAR/DLL и `artifacts/releases/**` не изменялись. Push, merge, deploy,
новый candidate, signing и публикация: NOT_PERFORMED.
Rollback — scoped revert `fa62f04`; серверных и системных сетевых изменений нет.
