# A01 — закреплённый AWG baseline и границы lab

**VERIFIED / I4** для исходного R12-A01: pin, отдельные wire/config contracts,
потребители и ограничение lab-доступа. [Acceptance](evidence/a01-acceptance-20260908/acceptance.json)
связывает Core `02a091c`, client `5760f41` и platform `6e8f337`; runtime inputs
последних двух соответствуют `f479fd4` и `16407b8`.

AWG3.1 закреплён на `github.com/amnezia-vpn/amneziawg-go/v3 v3.1.20260814`,
source `1b86b2ae0e493e7ea93f8c1a0f0cb6735b1551f1`. Контракт
`pokrov.awg31.endpoint.v1` имеет SHA-256
`1bb49b61549ba7c4a3c2d56df445e919ebb1ed12d42e04b0cb3c915d23240818`.
Отдельный AWG2 `pokrov.awg2.endpoint.v1` —
`c473c411025825bfef5a76c64990c5c921e9658b3581210d3a86d72e454fdea8`.
Оба consumer sync checks PASS для Core/platform/client. Android и Windows
потребляют свои declared contracts; AWG3.1 явно несовместим с AWG2 по wire,
требует отдельного managed profile. [A02](EXECUTION-A02-2026-09-08.md)
сохраняет отдельные interop/server/material receipts обоих labs.

Обе capability записи запрещают публичное runtime advertisement; AWG2 имеет
статус `prototype_disabled_by_default`, AWG3.1 — `lab_disabled_by_default`.
Первый verifier ошибочно ожидал одинаковую строку статуса: assertion FAIL
сохранён как ошибка локального oracle в receipt, v2 проверяет реальные разные
контракты. Product metadata для прохождения проверки не менялась.

Свежий Brain readback в `SET TRANSACTION READ ONLY` подтвердил прежний config
hash `cd0add7b4805b863531ba0cd49b44c9749dbe38d6e740be6154114631b6920a3`.
Флаги обоих lab gates **enabled=true / kill_switch=false**; это не состояние
`enabled=false`. При этом обе identity allowlists пусты, общих lab defaults /
carrier rules и lab cohorts нет. Действующие access functions отклонили
синтетическую неназначенную identity. Пустые списки закрывают доступ всем
identity по той же проверенной логике, а не означают wildcard.

Три deployed файла соответствуют retained source `f530005`, не текущим полным
файлам platform. Все восемь default/normalization/access функций совпали по AST
с текущими. Остальные source changes не считаются развёрнутыми. Это подтверждает
наблюдаемую границу доступа и источник проверенных gates; не live acceptance
нового provisioning кода.

Команды из platform worktree — все exit 0:

```powershell
python -B scripts/verify_awg31_contract_sync.py --platform-root . --core-root E:/r12core-implementation --client-root E:/r12client --output E:/r12-a01-acceptance-20260908/awg31-sync.json
python -B scripts/verify_awg2_contract_sync.py --platform-root . --core-root E:/r12core-implementation --client-root E:/r12client --output E:/r12-a01-acceptance-20260908/awg2-sync.json
python -B -m pytest -p no:cacheprovider tests/test_awg31_lab_service.py tests/test_awg2_lab_service.py tests/test_verify_awg31_contract_sync.py tests/test_verify_awg2_contract_sync.py -q
python -B E:/r12-a01-acceptance-20260908/read-scope-effective.py
python -B E:/r12-a01-acceptance-20260908/verify-acceptance-v2.py
```

34 tests PASS. [Receipt](evidence/a01-acceptance-20260908/receipt.json) сохраняет
10 файлов, включая первоначальный REVIEW_REQUIRED и оба verifier scripts.
Ни source pin, ни endpoint/key material, ни backend configuration не менялись.
Публичное включение AWG по-прежнему требует отдельного product scope decision
и runtime/origin matrix. Новый candidate, push, deploy и publication отсутствуют;
полные A04–A09 и остальные release criteria остаются открытыми по своим условиям.

Документационные проверки: 33 tests, platform-context audit и package validator
(83 R12 IDs / 378 legacy IDs / 371 local links) PASS; `git diff --check` PASS.
Изменение статуса затронуло только A01; source worktrees и retained release
artifacts не менялись.
