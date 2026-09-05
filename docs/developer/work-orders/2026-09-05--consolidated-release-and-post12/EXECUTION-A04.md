# A04 — согласованность AWG material при выдаче, 2026-09-06

**PARTIAL / I3.** Локальный slice существующего managed provisioning.
Platform commit `c98b58f`.
[Точные команды, SHA логов и source](evidence/a04-material-snapshot.json).

AWG2 и AWG3.1 дважды выбирали активную device-bound запись: при проверке
готовности и перед рендерингом. Между чтениями ротация могла заменить запись,
и endpoint новой generation выдавался с metadata прежней разрешённой generation.
Два synthetic regression fixtures воспроизвели несовпадение до исправления.

Теперь readiness helper возвращает проверенную запись, а renderer расшифровывает
её же. Публичный boolean readiness interface сохранён. Условия contract,
generation, endpoint revision, server/node binding и возраста material прежние.
Новых таблиц, API, зависимостей и offline entitlement модели нет.

Оба целевых теста PASS после исправления. Полные AWG lab, network rollout API
и AWG contract sync проверки: 43 PASS. Обязательный backend router набор:
154 PASS и 8 subtests PASS за 685.67 с. Docs contracts: 33 PASS; context audit,
package validation (142 links) и diff check: PASS. Точные команды и SHA логов
сохранены в evidence. Canonical API owner обновлён.

Границы: проверена согласованность одного issuance snapshot на synthetic SQLite
fixtures с подменой последовательных чтений. Это не multi-process PostgreSQL
race proof и не interop с owned AWG server. Отзыв уже выданного peer, expiry на
сервере, потеря устройства и RU-origin traffic остаются OPEN. A02 dependency,
полный A04 и release readiness этим изменением не закрываются.

Rollback — scoped revert локального commit. Production, push, merge, deploy,
новый candidate, подпись и публикация: NOT_PERFORMED. Client/Core bytes и
retained release artifacts не менялись.
