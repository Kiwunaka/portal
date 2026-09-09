# Объединение исходников и проверки promotion lines — 2026-09-09

**PASS в scope исходников; runtime и release acceptance открыты.**
Разрешение — [решение владельца](OWNER-DECISIONS-2026-09-09.md), бюджет $0.
Сохранены [receipt](evidence/source-promotion-20260909/receipt.json) и
[все попытки CI](evidence/source-promotion-20260909/ci-converged-promotion-lines.json).

## Точные исходники

| Репозиторий | PR / проверенный signed head | Promotion commit |
| --- | --- | --- |
| Platform | [#243](https://github.com/Kiwunaka/portal/pull/243), `2310d761fdeca64df28604231bf5b0b987eddedd` | master `03920525bfc3993591a39d21e35bbe2e7e1d663d` |
| Client | [#95](https://github.com/Kiwunaka/POKROV-app/pull/95), `9f19edf6a9ae591d1c4f3807e36a80022cd45b36` | main `c05b58b268bbd789aa96fb662cb46c9768558ef0` |
| Core | [#9](https://github.com/Kiwunaka/pokrov-core/pull/9), `1f9a5a8865b80067784b893ef99d43c63f943777` | main `7444e531af6d9bf9b37d8f14e022f04182e447cc` |

GitHub подписал exact source trees. Перед каждым squash merge required checks
прошли; после merge подтверждены подпись и равенство tree. Linear history
требует squash: первая попытка platform merge commit отклонена, затем выполнен
штатный squash без bypass. Исходные feature branches и draft PR #242/#94/#8
сохранены. Strict app-bound checks/signatures/admin enforcement не ослаблялись.

Для последовательного объединения platform PR #243 использовал закреплённые
client/Core source, client PR #95 — закреплённый Core. Исключения ограничены
номерами этих PR. После объединения всех трёх репозиториев выполнены обычные
promotion-line workflows, без этих исключений:

- Platform contract [34307351132, attempt 2](https://github.com/Kiwunaka/portal/actions/runs/34307351132/attempts/2)
  PASS; Guardrails `34307351129` и signing custody `34307351196` PASS.
- Client contract [34308102145, attempt 2](https://github.com/Kiwunaka/POKROV-app/actions/runs/34308102145/attempts/2)
  PASS: 644 Flutter tests, Android direct/store и Linux. Windows runtime и
  signing negatives, неприменимые на Linux, остаются skips тестового выполнения;
  зелёный workflow не является Windows runtime proof.
- Core [34308331531](https://github.com/Kiwunaka/pokrov-core/actions/runs/34308331531)
  PASS: release-contract, test, Android/Windows reproducibility, Apple source build.

Предыдущие failures на прежних cross-repository bindings сохранены по attempts.
Они не переименованы в PASS. Core PR attempt 2 повторял только упавший contract;
последующий обычный main run выполнил все пять jobs заново.

## Локальная проверка объединённых исходников

Platform `0392052`, client `c05b58b`, Core `c7a11f7`: **15/15 PASS**, exit 0,
все worktrees чистые. Client seed закрепляет `c7a11f7`; его полный Git tree
совпадает с merged Core `7444e53`. Это сохраняет точную source authority seed.
Node 22.14.0, Flutter 3.38.5, GOTOOLCHAIN go1.26.8.

```powershell
python -B scripts/release_1_2_local_quality_gate.py --platform-root E:/r12-promoted-platform-20260909 --client-root E:/r12-promoted-client-20260909 --core-root E:/r12core-implementation --evidence-dir E:/r12-promoted-quality-20260909
python -B scripts/release_1_2_candidate_preflight.py --platform-root E:/r12-promoted-platform-20260909 --client-root E:/r12-promoted-client-20260909 --core-root E:/r12core-implementation --release-index-root C:/Users/kiwun/Documents/ai/pokrov-release-index --output E:/r12-promoted-quality-20260909/preflight.json
```

Preflight `READY_LOCAL_FREEZE`, blockers 0, candidate_created false. Manual/device/
origin lanes в gate остаются открытыми; source PASS не заменяет их результаты.

## Подготовка Brain и инициализация ключа — без выкладки кода

В 04:08 UTC все 197 существующих runtime files совпали побайтно с retained
baseline: backend `f530005` плюс `control_panel` из `1207b63`. Пять units active,
NRestarts 0; API PID изменён параллельной задачей, поэтому порядок выкладки
согласуется с ней до mutation. Пять rollback snapshots сохранены.

Payload из чистого `0392052`: 203 файла / 6 238 652 bytes. Git bytes каждого
файла совпадают с уже проверенным на восстановленной production DB `235e8a4`.
Шесть schema/dependency inputs равны live baseline. Worker peer targets не
настроены, автоматическое удаление AWG peers при code deploy не включается.

Обнаружен отсутствующий `COMMERCIAL_OFFER_HMAC_SECRET` и в API process, и в
`.env`; коммерческих reservations 0. Новый base checkout quote требует этот
ключ. В 04:11 UTC выполнена
[серверная инициализация](evidence/source-promotion-20260909/commercial-key-initialized.json):
новый отдельный key, версия `r12-commercial-20260909`, все прежние bytes `.env`
сохранены, права `0600`, unexpired holds повторно 0. Службы не перезапускались;
секрет и токены не экспортированы. Checkout без offer token остаётся
поддержанным, поэтому backend допускает выкладку перед static frontend.

Legacy AWG material всё ещё содержит общие ключи: A04 worker activation требует
индивидуальной миграции разрешённых устройств и проверки server peers. В этом
срезе AWG keys, rollout и production source не менялись. Новый candidate, public
release и final installed-client proof не выполнены.

## Проверки отчёта

`python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q`
— 33 passed. `python -B scripts/agent_context_packet_audit.py --platform-context-root .`
— PASS platform-context; `git diff --check` — PASS. Секреты и raw customer/provider
payloads в retained файлы не включены.
