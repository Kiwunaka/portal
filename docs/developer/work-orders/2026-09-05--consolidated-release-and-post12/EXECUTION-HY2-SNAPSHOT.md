# HY2 — согласованная выдача material, 2026-09-06

**PARTIAL / I3.** Продолжение проверки существующего lab provisioning после
[AWG A04](EXECUTION-A04.md) и [TCP fallback A07](EXECUTION-A07.md).
Platform source commit `f19a32c`.
Scope A04 по AWG не расширяется до публичного HY2 rollout.
[Source commit, команды и SHA логов](evidence/hy2-material-snapshot.json).

HY2 повторял активный запрос между readiness и рендерингом. В регрессии первая
запись прошла проверку generation `hy2-lab-v1`, а вторая имела generation
`hy2-lab-v2` и другой порт. До исправления renderer выдал второй endpoint с
metadata первой generation. Проверка одного ожидаемого порта дала FAIL.

Readiness helper теперь возвращает проверенную запись. Renderer расшифровывает
и проверяет hash этой же записи; публичная boolean readiness функция сохранена.
Условия generation/contract/age/server/node binding не менялись. Это тот же
локальный подход, который уже применён для AWG2/AWG3.1, без общей новой
абстракции, таблицы или offline entitlement модели. Canonical API owner теперь
явно включает HY2 в эту гарантию выдачи.

Регрессия использует два синтетических encrypted material и подменяет порядок
ответов `_active_material` в SQLite fixture. После исправления lab suites дают
45 PASS. API/rollout/docs: 45 PASS; обязательный backend router: 154 PASS и
8 subtests PASS за 749.10 с. Context audit, package validation (153 links) и
diff check: PASS. Точные выполненные команды и результаты — в JSON evidence.
Ни placeholder secrets, ни raw config не копировались в report.

Это доказательство согласованности одного issuance snapshot. Multi-process
PostgreSQL rotation, отзыв уже выданного password на сервере, server expiry,
потеря устройства и независимый traffic proof здесь не проверялись. A04/A07
dependencies и весь релиз остаются открыты. Новые Core/client/native bytes,
release candidate и runtime bundle не создавались. Push, merge, deploy,
изменение cohort, signing и публикация не выполнялись. Retained release
artifacts сохранены. Rollback исходников — scoped revert source commit,
указанного в evidence; runtime rollback не запускался.
