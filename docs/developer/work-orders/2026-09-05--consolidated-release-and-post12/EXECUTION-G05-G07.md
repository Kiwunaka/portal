# R12-G05/G07 — metadata owners и граница исходников

Дата: 2026-09-06. Результат: **I3 / PARTIAL**.
Команды, source tuple, readbacks и hashes:
[evidence/g05-g07-metadata.json](evidence/g05-g07-metadata.json).
Platform test commit `bf4b6aa`; client doc/test commits `3b351b1`, `ded58b1`.
Финальный client `validate-seed.ps1` с явными platform/Core roots — PASS.

## Свежая сверка доступного состояния

- GitHub `Kiwunaka/pokrov/releases/latest` вернул public `v1.1.6`, без draft и
  prerelease. Все шесть бинарных assets из client release seed совпали по
  имени, GitHub-reported SHA-256 и размеру. Отдельно manifest/checksums присутствуют
  в восьми remote assets. Бинарники в этом этапе не скачивались и не запускались.
- Private candidate.33 Actions artifact `9928470408`: `expired=false`,
  срок `2026-09-18T08:01:25Z`, digest совпадает с cutover seed, source
  signed-index run — `63993fba699b68641b7e972071ab7729fa9ec43c`.
  Это readback сохранности private artifact, не новая криптографическая проверка.
- Latest public Core — `v1.0.3`. Continuing runtime seed связывает локальный
  Core `1.1.0` с `94dd310`, `release_tag_created=false`,
  `candidate_created=false`, `promotion_authorized=false`.
- Development target `1.2.0+4053` и retained candidate.33 имеют одинаковый номер
  сборки, но разные source tuples. `candidate_created=false` у continuing seed
  не отрицает существование private candidate.33 из отдельного cutover owner.

## Исправленные противоречия

В client cutover prose candidate.33 ошибочно назывался текущим `main`, а
continuing Core фиксировался на старом `cd8f0f4`. Теперь документ ссылается на
`config/runtime-artifacts.seed.json` для текущих bytes и сохраняет точный
старый tuple только у candidate.33. Ed25519 release-index signature явно
отделена от Windows Authenticode; Windows candidate остаётся
`SKIPPED_BY_OWNER_DIRECT_BETA_ONLY`.

Platform migration test требовал, чтобы successor build 4051 ещё не был создан,
хотя cutover owner уже содержит candidate.33/build4053. Before-run дал 1 FAIL
и 41 PASS. Проверка теперь читает существующий candidate из owner, отдельно
проверяя false для new public/store/pointer flags. После исправления — 42 PASS.

Artifact-boundary prose больше не объявляет недоступным публичный index только
из-за private статуса кандидата. Его status берётся из cutover owner. Hygiene
test также перестал требовать устаревшую строку `BLOCKED_BY_ACCESS` и проверяет
ссылку на владельца. Промежуточный FAIL этой проверки сохранён отдельно.

## Source и artifact boundary

Client generator берёт client revision из HEAD, Core revision/ABI/asset digests
из pinned runtime seed и выполняет parity. Platform validator ограничивает
четыре repository identities и требует полные SHA revisions. `Pokrov-client`,
`PORTALapp`, `latest` как Core revision и client repo вместо release index
отклонены четырьмя исполняемыми synthetic checks.

Client generator contract: 16 PASS, включая повторяемость, dirty/stable deny,
Core revision и artifact digest mismatch, caller-supplied observability contract,
отказ записи в retained release и tracked source destinations. Platform
preflight/rehearsal tests включают смешанный Core tuple и материализацию
commit objects вместо изменяемых worktree bytes. Эти тесты не заменяют проверку
того, что финальный APK/EXE действительно собран из заявленных исходников.

## Остаток и границы

G05 остаётся PARTIALLY_FIXED: свежий production app/catalog и новый exact
candidate metadata readback не выполнялись. G07 — NEEDS_RUNTIME_PROOF:
final packaged binary provenance, license/source obligations и публикация
требуют нового разрешённого candidate и соответствующих gates C05/G04/Q01.

Изменения — документы и их проверки. Новые binary builds, signing, candidate,
runtime mutation, push, merge и deploy не выполнялись. Candidate.33, versioned
releases и старые receipts не изменены. Source rollback — scoped commits;
concurrent generated registrants и marketing instruction files исключены.
