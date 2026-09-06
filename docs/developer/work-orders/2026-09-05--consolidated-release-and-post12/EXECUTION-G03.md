# G03 — актуальные inputs и зависимости evidence

Дата: 2026-09-06. Результат: **I3 / PARTIALLY_FIXED**.
Точная карта: [change-impact-20260906.json](evidence/change-impact-20260906.json).
Проверки: [g03-evidence-review.json](evidence/g03-evidence-review.json).
Ранние [change-impact-current.json](evidence/change-impact-current.json) и
[change-impact.json](evidence/change-impact.json) сохранены как исторические срезы.

## Исправление классификатора

В существующие проверки добавлены три фактических repository paths:

- `portal_bot/requirements.txt`: раньше `documentation_only`, теперь
  `packaged_dependency_toolchain`;
- `marketing/package-lock.json`: раньше `manual_classification_required`,
  теперь `packaged_dependency_toolchain`;
- `infra/owned-smart-dns/README.md`: раньше `deployment_migration`, теперь
  `documentation_only`.

Первые два cases дали FAIL до изменения; третий отдельно воспроизведён как
FAIL при разборе нового diff. После исправления все 4 теста comparator/classifier
прошли. Existing oracle/config/origin mismatch и missing inputs продолжают
инвалидировать перенос. Равные declared inputs остаются только основанием
для review, не release PASS. `requirements-ops.txt` и `requirements-test.txt`
также считаются dependency manifests, а не обычным текстом.

Path hints не заменяют анализ зависимости теста: README может определять
scope/oracle, а runtime внутри `infra/` не превращается в конфигурацию из-за
имени каталога. В срезе явно отмечены ручные уточнения для Smart DNS Go runtime,
web interaction source, collectors, Core emitter и retained evidence.

## Текущий source tuple

| Lane | HEAD среза | Изменённых файлов от task baseline | От candidate.33 source |
| --- | --- | ---: | ---: |
| Platform | `e6a374e9a9ff5b6219f5175f38755df6d52ff728` | 147 | 213 |
| Client | `ded58b1906bbfb1096ff919085ef37f5be942eb7` | 85 | 98 |
| Core | `94dd31012ac91fb9ecf2c98ad7383afb54102dd4` | 18 | 18 |

Срез содержит SHA-256 именно committed Git blobs. Чужие untracked instructions
и четыре клиентских generated registrants не включены в product inputs.
Исправленный classifier идентифицирован отдельным hash текущего write set;
таблица HEAD не выдаётся за commit, уже содержащий эту правку и новый отчёт.

Release-index проверен только через локальные Git objects: checkout `7a6b2ce`,
tracking `origin/main` `9169f27`, candidate.33 source `63993fb`. Это разные
указатели. Checkout не обновлялся; свежий remote readback не заявляется.

## Что зависит от изменённых inputs

| Область | Повторно устанавливаемая связь evidence |
| --- | --- |
| Managed runtime | Core/AAR/DLL, host protocol, profile ACK, configuration и oracle → N/W/D runtime matrix; старые installed bytes не подтверждают новые |
| Transport provisioning | AWG/HY2 approval/material, Core capability, server revision и origin → affected interop, revoke/expiry, fallback/canary; независимая правка docs не требует повторения неизменного interop сама по себе |
| Payments/acquisition | Browser intent/quote/return, callback amount/order, outbox/DB и provider → B/M/O06; provider fixtures не заменяют actual payment/receipt/reconciliation |
| Presentation/diagnostics | Producer/catalog/consumer, native sinks, browser bundle и device/viewport oracle → D05/F/O/V; новый collector может менять вывод при тех же runtime bytes |
| Release contracts/collectors | Handoff schema, validators и scope collectors → G/C/Q; перенос требует всех значимых artifact/config/toolchain/oracle/scope/environment/origin inputs |

Полные parent IDs и inputs каждой группы сохранены в JSON. Это проверенная
карта исполнения изменённых областей, не автоматически извлечённый полный
build/test dependency graph. Diff от task baseline не заменяет diff от
candidate.33; оба основания сохранены раздельно.

## Следующий исполнимый этап

1. Для конкретного acceptance run выбрать source/artifact/server/device tuple
   и полный набор значимых зависимостей его oracle. Недостающие inputs означают
   `MISSING_OR_INVALID_INPUTS`, а не reuse.
2. Существующие локальные PASS сохранить с исходными source/log hashes.
   Переносить их только после проверки совпадения входов и достаточности oracle;
   одно совпавшее имя файла или общий Git HEAD этого не доказывают.
3. Для завершения релиза остаются незакрытые решения N02/O03/V02, seller/provider
   данные M01/B06 и предусмотренная release-процедура. Hosted CI, signing,
   физический Android, Windows VM и owned origin/server proof остаются OPEN.
   Доступные локальные требования можно продолжать независимо от этих gates.

Ни один runtime receipt или исторический Gate F не получил reuse от этой
карты. Полный G03 не закрыт: применение полной dependency identity к будущему
exact-candidate acceptance ещё не выполнено. Product/runtime bytes, публичные
каналы и разрешения не изменились; push, deploy и новая сборка не выполнялись.
