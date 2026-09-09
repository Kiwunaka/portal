# Brain — production snapshot и проверка текущего backend на восстановленной базе

**PASS_BOUNDED; полный B08 и выпуск открыты.** Разрешение действий текущего плана
записано в [решении владельца](OWNER-DECISIONS-2026-09-09.md).
Source: platform `235e8a4`, client `5760f41`, Core `02a091c`.
[Brain receipt](evidence/brain-rehearsal-20260909/receipt.json) и
[local quality receipt](evidence/integrated-quality-20260909/receipt.json).

## Текущий локальный комплект

15/15 local quality steps PASS: 473 app-shell tests, analyze/seed/contracts,
69 cabinet E2E, webapp lint/build, marketing build/SEO/responsive/reduced-motion,
adminapp build и static performance. Stop-пределы 9/9 PASS, пять target-значений
не достигнуты. Node 22.14.0, Flutter 3.38.5. Все три source checkout чистые.
Preflight `READY_LOCAL_FREEZE`, 0 blockers; 22 candidate rows ниже I3 остаются
в реестре preflight. Это не release/candidate/device approval.

Из `E:/r12-current-quality-platform-20260908`:

```powershell
python -B scripts/release_1_2_local_quality_gate.py --platform-root E:/r12-current-quality-platform-20260908 --client-root E:/r12-current-inputs-client-20260908 --core-root E:/r12core-implementation --evidence-dir E:/r12-integrated-quality-20260909
python -B scripts/release_1_2_candidate_preflight.py --platform-root E:/r12-current-quality-platform-20260908 --client-root E:/r12-current-inputs-client-20260908 --core-root E:/r12core-implementation --release-index-root C:/Users/kiwun/Documents/ai/pokrov-release-index --output E:/r12-integrated-quality-20260909/preflight.json
```

PATH выбирал указанные Node/Flutter; Playwright browsers — существующий локальный
cache. Старые quality checkout переведены с прежних detached commits на указанные
commits после проверки чистоты. Предыдущие evidence и архивы сохранены.

## Реальная PostgreSQL-копия

Read-only source probe: Brain совпадает с новым source в 172/203 runtime files;
там прежний backend. До работ: база 1,95 GB, свободно 17,50 GB, source lock waiters
0, пять production units active с `NRestarts=0`.

Canonical `remote_postgres_backup_restore_gate.py` экспортировал repeatable-read
snapshot `portal`, создал зашифрованный custom-format backup и восстановил его
в новую `portal_r12_20260909_rehearsal`. **121 таблица, 2 466 128 строк** совпали
по точным counts. Ordinary app role владеет target/schema/objects, PUBLIC access
отозван. Support ownership PASS. Snapshot закрыт commit; source DDL/DML не было.

Архив **137 069 152 bytes**, SHA-256 `58caef8c…d05dad`, mode `0600`, остаётся
в `/root/backups/r12-20260909/`; полный путь/hash в receipt. Passphrase сохранён
через Windows DPAPI вне Git, в plaintext не сохранён. Новый отдельный backup
каталог и retain-count 30 сохранили прежние backup families. Target не reset.

PLAN затем APPLY использовали source/confirm `portal`, target/confirm
`portal_r12_20260909_rehearsal`, backup-dir `/root/backups/r12-20260909`.
Полная команда и загрузка protected passphrase сохранены в
[run-backup.ps1](evidence/brain-rehearsal-20260909/run-backup.ps1) и
[retry-backup.ps1](evidence/brain-rehearsal-20260909/retry-backup.ps1).
Первая попытка упала на SSH до snapshot/target creation; отдельный strict auth
readback прошёл, повтор с теми же credentials PASS. При подготовке повтора
локальный DPAPI reader сначала отверг trailing newline до запуска Python;
исправлен только разбор зашифрованного файла. Первоначальный FAIL сохранён.

## Exact candidate на восстановленном production volume

`git archive` из `235e8a4` для `portal_bot shared`: 233 tracked files,
SHA-256 `aa1f9e6e…26f5f`. PLAN и APPLY
`remote_postgres_candidate_gate.py` проверили этот archive/commit и тот же
подтверждённый target. [Результат](evidence/brain-rehearsal-20260909/candidate-apply.json):

- Ordinary role/target identity и владение 1191 public objects PASS.
- DDL lock timeout 756 ms, advisory lock, `FOR UPDATE SKIP LOCKED` PASS.
- `db.init_db()` дважды: 877/755 ms, сохранение counts и legacy entitlement
  fingerprint, schema contract PASS.
- Concurrent bind: один winner, один `already_bound`, retry `canonical_existing`.
- Реальная protocol-level потеря commit ACK: ошибка клиента, одна committed row.
- Synthetic rows/DDL cleanup подтверждён. Remote scratch удалён canonical gate.

Это выполнение candidate database/cleanup code на Brain и реальных объёмах
в копии. Production API/bot/worker новым кодом ещё не запускались.

## Файлы и текущая сохранность

Отдельный зашифрованный tar сохранил durable support/promo directories; новый
root-only restore directory содержит те же **три promo-файла, 1 868 520 bytes**.
Hash manifests до capture, после capture и после restore одинаковы. Архив
`1 873 952 bytes`, SHA-256 `692ce9bb…cb6a20`, mode `0600`; restore root `0700`.
Архив и восстановленные файлы остались на Brain. Raw filenames/content не
возвращались. [Plan/apply](evidence/brain-rehearsal-20260909/volume-apply-v2.json).

Support attachments в source/clone: 0. Bundle directories отсутствуют;
`promo_slots_config_v1` отсутствует в обеих БД. Не заявляется восстановление
заполненных attachments или действующей promo campaign. Первый volume PLAN
имел неверное написание default accepted directory; canonical path исправлен
в V2 до APPLY, первая версия сохранена как superseded. DB snapshot и file
capture выполнены отдельно; атомарный cross-store snapshot не заявляется.

Последний readback: пять production units сохраняют прежние PIDs,
`NRestarts=0`, active; source lock waiters 0, свободно 14,71 GB. Production
backend source, service configuration, `.env` и исходные files не менялись.
Обычный трафик продолжался, поэтому общий размер live DB менялся.

## Следующий scope

Rehearsal/backup больше не являются отсутствующим Brain-volume доказательством
для этого tuple. Открыты deployed API/bot/worker, shared AWG key migration и
permanent revoke worker activation, installed-client revoke/expiry и остальные
release gates. Push, merge, production code deploy и новый release candidate
в этом срезе не выполнялись. B08 не получает полный PASS только из этой копии.

Документальные проверки: 33 tests PASS (`test_agent_docs_contract.py`,
`test_agent_context_packet_audit.py`), context audit PASS, package validator
PASS — 83 R12 IDs, 378 legacy IDs, 401 local links; `git diff --check` PASS.
