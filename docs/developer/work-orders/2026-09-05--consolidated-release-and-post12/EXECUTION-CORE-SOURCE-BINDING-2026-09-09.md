# Согласование Core source binding — 2026-09-09

Client `5fdfc8dfd231265ea1d6c555d1ec56769c359b3b` теперь закреплён за Core
`c7a11f7d2fd974726095ad7aa0619c055273dd15`. Новый Core HEAD отличается от
прежнего `02a091c` только Apple build preflight и release documentation.
Две новые локальные сборки каждой платформы воспроизвели все пять файлов
предыдущих build trees побайтно. AAR, DLL и Cronet в клиенте имеют те же bytes.

В клиенте изменены source references, hashes новых build receipts/SBOM и
16 ссылок на source в native notices. Verbatim license text сохранён, библиотеки
и `artifacts/releases/**` не менялись. [Точный commit и client evidence](https://github.com/Kiwunaka/POKROV-app/commit/5fdfc8dfd231265ea1d6c555d1ec56769c359b3b)
сохраняют прежний manifest и отдельные Android/Windows receipts.

## Локальная проверка

Build commands выполнялись из clean `E:/r12core-implementation` на `c7a11f7`:

```powershell
./scripts/build-android.ps1 -GoExecutable C:/Users/kiwun/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.8.windows-amd64/bin/go.exe -AndroidSdk C:/Users/kiwun/AppData/Local/Android/Sdk -OutputDirectory E:/r12-core-rebinding-20260909/android-a
./scripts/build-android.ps1 -GoExecutable C:/Users/kiwun/go/pkg/mod/golang.org/toolchain@v0.0.1-go1.26.8.windows-amd64/bin/go.exe -AndroidSdk C:/Users/kiwun/AppData/Local/Android/Sdk -OutputDirectory E:/r12-core-rebinding-20260909/android-b
```

Windows: `scripts/build-windows.ps1` с тем же Go, `-CCompiler
E:/POKROV-tools/runtimes/mingw-13.2.0-ucrt-posix-seh/mingw64/bin/gcc.exe`,
точным `-CronetLibrary` из client runtime и отдельными `windows-a/windows-b`.
Первый запуск дал cgo exit 2; после добавления MinGW bin в PATH только процесса
оба builds завершились успешно. Исходный failed log сохранён.

`scripts/new-release-artifact-evidence.ps1 -RequireCleanSource` проверил обе
пары и записал receipts. Toolchain Go 1.26.8, pinned Android NDK 29.0.14206865,
MinGW-w64 GCC 13.2.0; CycloneDX generator v1.10.0. SBOM warnings о licenses
не превращены в юридический PASS. Полные build trees, SBOM и логи сохранены
в `E:/r12-core-rebinding-20260909`.

Сравнение обоих SBOM с предыдущей сборкой нашло только пять hashes исполняемого
generator в каждом файле. Component/dependency/license records прежние;
генератор в этот раз взят из `E:/POKROV-tools/go-tools/bin`, v1.10.0,
скомпилирован Go 1.25.13. Это объясняет смену SBOM digests без смены зависимостей.

Из `E:/r12client`:

- `scripts/test-windows-core-proxy-only.ps1 -CoreRoot E:/r12-core-rebinding-20260909/windows-a`
  — PASS, 100 cycles; TUN/DNS/route/device acceptance не выполнялась.
- `scripts/validate-seed.ps1 -PlatformRoot C:/Users/kiwun/Documents/ai/VPN-consolidated-plan-start -CoreRoot E:/r12core-implementation`
  — сначала FAIL на старой source binding, после обновления exit 0. Включает
  16 handoff-v2 cases, repository hygiene, docs и общие contracts.
- `scripts/sync-pokrov-core-runtime.ps1 -CoreRoot E:/r12core-implementation -Platforms android,windows`
  — PASS, точные существующие bytes.
- `git diff --check`, staged receipt/notice SHA-256 readback и проверка
  отсутствия release-artifact delta — PASS.

Отдельный повтор handoff-теста сообщил 16 PASS, но ad hoc wrapper ошибочно
использовал LASTEXITCODE ожидаемого negative child и завершился 1. Полный seed
validator выше завершился 0. Этот wrapper failure сохранён и не скрывается.

## Hosted CI и граница результата

Точная связка: client `5fdfc8d`, platform `0f6745d`, Core `c7a11f7`.
[CI run 34304294175](https://github.com/Kiwunaka/POKROV-app/actions/runs/34304294175)
— PASS; watcher exit 0. 644 Flutter tests PASS, один реальный Windows Core
тест пропущен на Linux; Windows signing runtime negatives также имеют явный
SKIPPED_BY_PLATFORM. Android direct/store unit tasks и Linux daemon
gofmt/test/vet/build PASS. Число JVM cases из Gradle BUILD SUCCESSFUL не выводится.
[Snapshot](evidence/core-source-binding-20260909/snapshot-final.json) сохраняет
все пять run statuses и точные PR heads; [receipt](evidence/core-source-binding-20260909/receipt.json)
связывает локальные и hosted results с hashes retained evidence.

Первый manual dispatch `34304277115` получил короткий client SHA и был
отвергнут проверкой входов. Корректный dispatch `34304294175` получил три
полных SHA. Обычный PR run `34304280737` завершился FAIL: прежний Core/main
ещё отличается от нового bound source. Guardrails platform `0f6745d`
(`34303104311`) PASS; его ordinary cross-repository run `34303104317` FAIL
на прежних promotion bindings.

Source commit отправлен в draft PR #94 без новых LFS objects. Защита branches,
бюджет $0 и параметры публикации не менялись. Exact-tuple replay не заменяет
совместимые promotion lines. Слияние, deploy, новый candidate, signing и
публикация релиза не выполнялись. Parent R12 IDs и full release acceptance
остаются открытыми; прежние device receipts сохраняют исходную идентичность.

Platform documentation checks: `python -B -m pytest -p no:cacheprovider
tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 PASS; `python -B scripts/agent_context_packet_audit.py --platform-context-root .`
— PASS. Work-order `validate_package.py` подтвердил 83 R12 IDs, 378 legacy IDs
и 436 local links. `git diff --check` PASS. PR #94 обновлён текущей связкой
и точными границами проверок.
