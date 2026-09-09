# A07 — bounded managed TCP fallback, 2026-09-06

**PARTIAL / I3 / NEEDS_RUNTIME_PROOF.** Platform `f03a6a7`, client `45036ab`.
[Точные команды, source SHA и SHA локальных логов](evidence/a07-tcp-fallback.json).

Lab manifests уже перечисляли `legacy_reality_fallback`, но клиент не использовал
этот список. У AWG2/AWG3.1/HY2 нет обычного Smart Connect node, поэтому прежний
node retry не запускал резервный транспорт. До исправления API игнорировал
fallback query (три регрессии FAIL), а клиент после lab failure делал только
один connect вместо ожидаемого перехода на резервный профиль.

Теперь сервер принимает `fallback_from_revision` только для текущей разрешённой
device-bound lab revision. Он повторяет обычные TCP provisioning, entitlement
и node checks, выдаёт REALITY с отдельной revision и сохраняет routing/DNS
policy. Несовпадение revision и уход устройства из lab дают HTTP 409.
Запрос не меняет сохранённый cohort. Тест проверяет настоящий renderer VLESS;
lab material и panel readiness заменены изолированными fixtures.

Клиент сохраняет предложение fallback только из lab manifest, который явно
содержит обычный резервный транспорт. Подтверждённый
`core_egress_probe_failed` запускает его через существующий fetch/stage/start
путь. Transport transition и дальнейшие node retries делят лимит двух повторов,
backoff и generation fence. Отсутствие proof не считается подтверждённым
сетевым отказом. Старый отказавший профиль запрещён для offline retry; чужой
transport/revision в ответе сервера отклоняется до staging. Сохраняются режим,
списки приложений и локальные routing preferences. WARP использует существующую
consent/fallback policy. Ручное действие Home или смена локации отменяет pending
transport choice.

| Проверка | Результат | Граница |
| --- | --- | --- |
| API: AWG2 / AWG3.1 / HY2, stale revision, normal provisioning, cohort unchanged | 3 PASS; весь rollout/lab набор 56 PASS | Synthetic session и panel; настоящий TCP config renderer |
| Android node/lab, Windows immediate failure, failed TCP, unavailable proof, refused bootstrap | 6 widget cases PASS | MethodChannel fixtures; не устройство/VM |
| HTTP bootstrap: AWG2/AWG3.1 → VLESS, ignored query/wrong revision rejected | 1 PASS, оба lab внутри | Local HTTP/config materialization; не внешний traffic |
| Client regression suite | 311 PASS | До добавления последнего refusal case; финальный focused run 7 PASS после него и форматирования |
| Runtime engine suite | 80 PASS / 1 existing opt-in DLL skip | Native DLL smoke не выполнен |
| Backend router | 154 PASS / 8 subtests PASS | Local API/service/auth/subscription fixtures |
| Analyzer / seed / docs / context / package / diff | PASS | Source contracts; не release approval |

Во время focused Python run обнаружен устаревший HY2 fixture: дата выдачи была
фиксирована, а возраст проверялся относительно текущего времени. Fixture clock
теперь фиксирован рядом с датой выдачи. Production expiry policy не менялась.
Первый результат 55 PASS / 1 FAIL сохранён, затем весь набор дал 56 PASS.

Platform API должен попасть в runtime до использования нового client recovery:
старый сервер может игнорировать query, но клиент отвергнет такой ответ.
Rollback исходников — scoped revert `45036ab` и `f03a6a7`; deployed rollback
не выполнялся. Core/native bytes и retained release artifacts не менялись.

A05/N06 dependencies, весь A07 и общий план остаются открыты. Реальная UDP
blackhole matrix, Android device, Windows VM, TCP traffic/privacy proof,
current-/brain-/RU-origin и актуальный release candidate здесь не проверены.
Подтверждённый lab egress failure сам по себе не доказывает блокировку UDP.
Push, merge, deploy, lab activation, signing и публикация не выполнялись.
