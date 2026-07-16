# POKROV Admin Command Center and RU Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Превратить `adminapp` в русскоязычный операционный command center со всеми 15 согласованными разделами, подробной карточкой каждой ноды, долговечными RU-origin проверками каждые 6 часов и серверной защитой опасных действий.

**Architecture:** Реализация идёт пятью сборочными вертикальными срезами поверх текущих Next.js/FastAPI/SQLAlchemy компонентов. Монолитный frontend постепенно заменяется route-модулями с ленивой загрузкой, backend получает отдельные сервисы RU probe, exact-candidate release evidence и action intent, а `mini` пишет неизменяемые schema-v2 артефакты в spool и доставляет их exact-byte HMAC ingest. Старый экран каждого маршрута удаляется только после паритета нового.

**Tech Stack:** Next.js 16 static export, React 19, TypeScript 5, Tailwind CSS 4, TanStack Table, Recharts, Playwright; Python 3, FastAPI, Pydantic, SQLAlchemy, SQLite/PostgreSQL; systemd, Python stdlib networking/HMAC/filesystem primitives; pytest.

## Global Constraints

- Канонический дизайн: `docs/superpowers/specs/2026-07-15-adminapp-command-center-ru-observability-design.md`.
- Работать только в platform repository. Android/Windows client repository `C:/Users/kiwun/Documents/ai/POKROV-app` не входит в этот план.
- Не использовать WSL. Команды запускаются из PowerShell через `npm.cmd`, `python`, `rg.exe`, `git`.
- До каждого изменения выполнять `git status --short --branch` и scoped `git diff -- <paths>`. Сейчас `portal_bot/api.py`, `portal_bot/worker.py` и `docs/operations/deployment-and-access.md` уже содержат посторонние незакоммиченные правки; их необходимо сохранить и согласовать изменения построчно. `docs/README.md` тоже уже изменён вне этой работы и в план не входит.
- Не выполнять deploy, SSH-команды, установку unit-файлов на `mini`, production migration или production ingest. Локальная реализация не является доказательством RU-origin готовности.
- Все основные подписи, ошибки, подтверждения и подсказки интерфейса — на русском. Английский допустим только как вторичный технический код.
- Отсутствие значения отображается как `—` плюс «Нет данных», а не как `0`, «Норма» или пустая строка.
- `current-origin`, `brain-origin` и `RU-origin` остаются отдельными источниками. Ни frontend, ни aggregate endpoint не объединяют их в ложный PASS.
- RU probe запускается раз в 6 часов; пригодный результат становится stale через 7 часов по `finished_at`. UI polling не меняет возраст evidence.
- Google failure означает недоступность RU probe environment, а не отказ всех нод.
- Любой current RU PASS требует полный текущий server manifest, совпавшие endpoint fingerprints и PASS всех server-required стадий.
- HMAC проверяется по точным raw bytes до JSON parse; секреты, подписи, subscription URL, private keys и raw provider payload не логируются и не попадают в UI.
- L2/L3 endpoint без валидного server action intent отвечает `428 intent_required`; stale/mismatch отвечает `409`; write-команды автоматически не повторяются.
- Release readiness всегда привязан к exact candidate ID/hash. Skip, attestation, access block и missing никогда не стилизуются как PASS.
- Каждый task следует red-green-refactor: сначала failing test, затем минимальная реализация, focused PASS, scoped review и отдельный commit.
- Стадировать только перечисленные файлы task. Не использовать blanket `git add .`.
- Любой helper из тестового фрагмента (`valid_payload`, `installAdminApiMock`, `prepare_intent`, seeded fixture) создаётся в том же test task с фиксированными redacted данными; исполнитель не должен предполагать скрытую fixture.

---

## File Structure and Ownership

### Backend and contracts

- Create: `portal_bot/ru_probe_contract.py`
  - Единственная stdlib-реализация canonical JSON, manifest/fingerprint hash и schema-v2 structural validation. Её импортируют backend и runner.
- Create: `portal_bot/internal_request_auth.py`
  - Key registry, path normalization, exact-byte HMAC, timestamp/key-scope/host binding и durable nonce consume.
- Create: `portal_bot/ru_probe_service.py`
  - Manifest build, ingest, server verdicts, latest/history/uploader/node read models и RU alert candidates.
- Create: `portal_bot/release_evidence_service.py`
  - Canonical candidate ID, redacted evidence import, RU retention hold и readiness.
- Create: `portal_bot/admin_action_intent_service.py`
  - Action policy registry, preview snapshot, confirmation, entity version, consume/idempotency и audit binding.
- Modify: `portal_bot/models.py`
  - RU, nonce, release and action-intent SQLAlchemy models.
- Modify: `portal_bot/migrations.py`
  - Idempotent SQLite/PostgreSQL bootstrap for the new tables, constraints and indexes.
- Modify: `portal_bot/api.py`
  - Thin DTO/auth/status-code handlers and migration of existing L2/L3 endpoints to intent enforcement.
- Modify: `portal_bot/admin_ops_service.py`
  - Merge server-derived RU freshness/heartbeat candidates into durable ops alerts without changing RU verdict authority.
- Modify: `portal_bot/worker.py`
  - 180-day unheld RU retention, nonce cleanup and prepared-intent cleanup.

### RU runner and host-side delivery

- Modify: `scripts/ru_probe_runner.py`
  - Manifest-driven schema-v2 runner, real large-body GET, strict TLS semantics and transport adapter calls.
- Create: `scripts/internal_hmac_client.py`
  - Exact-byte request signing shared by manifest fetch and uploader.
- Create: `scripts/ru_probe_uploader.py`
  - Atomic spool writer, uploader state machine, immutable sidecar verification and separate heartbeat.
- Create: `scripts/ru_probe_payload.schema.json`
  - Executable JSON Schema for v2 run artifacts.
- Create: `infra/pokrov-ru-probe.service`
- Create: `infra/pokrov-ru-probe.timer`
- Create: `infra/pokrov-ru-probe-uploader.service`
- Create: `infra/pokrov-ru-probe-uploader.timer`
  - Static unit templates only; this plan does not install them.

### Frontend

- Create: `adminapp/src/components/ops/`
  - Shell, grouped navigation, mobile drawer, top bar, command palette, route boundary and shared action-intent dialog.
- Create: `adminapp/src/components/ui/`
  - Button, status badge, source row, tooltip, dialog, empty/error/loading states and table primitives.
- Create: `adminapp/src/features/{overview,nodes,users,network,revenue,support,control}/`
  - Domain route modules. A feature imports only its own endpoint client and shared primitives.
- Create: `adminapp/src/lib/admin-api/`
  - Authenticated client plus typed overview, nodes, users, network, revenue, support and control endpoints.
- Create: `adminapp/src/lib/ops-status/`
  - Server enum/freshness to Russian presentation mapping; it never computes backend facts.
- Create: `adminapp/src/lib/url-state.ts`
  - Typed query-state read/write with history/back-forward support.
- Create: `adminapp/src/lib/use-route-resource.ts`
  - AbortController-based route/detail loading and visible-tab polling.
- Modify: `adminapp/src/components/ops-dashboard.tsx`
  - End as a thin active-route dispatcher; no cross-route data loading.
- Modify: `adminapp/src/components/shell.tsx`
  - End as a compatibility re-export of the new shell.
- Modify: `adminapp/src/lib/api.ts`
  - Transitional re-exports only; remove after all consumers move to `lib/admin-api/`.
- Modify: `adminapp/src/app/globals.css`
  - Dense dark command-center tokens, focus, responsive drawer/detail and reduced-motion behavior.

### Tests and documentation

- Create focused backend tests:
  - `tests/test_internal_request_auth.py`
  - `tests/test_ru_probe_contract.py`
  - `tests/test_ru_probe_migrations.py`
  - `tests/test_ru_probe_service.py`
  - `tests/test_ru_probe_ingest_api.py`
  - `tests/test_ru_probe_uploader.py`
  - `tests/test_admin_action_intents.py`
  - `tests/test_release_evidence_service.py`
  - `tests/test_adminapp_command_center_contract.py`
- Split Playwright coverage into:
  - `adminapp/e2e/fixtures/admin-api.ts`
  - `adminapp/e2e/shell-and-overview.spec.ts`
  - `adminapp/e2e/nodes.spec.ts`
  - `adminapp/e2e/clients.spec.ts`
  - `adminapp/e2e/network-and-revenue.spec.ts`
  - `adminapp/e2e/control.spec.ts`
  - `adminapp/e2e/accessibility.spec.ts`
- Update canonical docs:
  - `adminapp/README.md`
  - `docs/architecture/system-overview.md`
  - `docs/operations/monitoring-and-visibility.md`
  - `docs/operations/ru-origin-probe-handoff.md`
  - `docs/operations/publishing-and-signing-guide.md`
  - `docs/operations/deployment-and-access.md`

---

## Frozen Cross-Cutting Contracts

### Status vocabulary

```ts
export type OpsStatusCode =
  | "ok"
  | "degraded"
  | "failed"
  | "stale"
  | "unavailable"
  | "missing"
  | "BLOCKED_BY_ACCESS";

export type SourceKind = "current" | "brain" | "ru";

export type OpsStatusPresentation = {
  label: "Норма" | "Требует внимания" | "Сбой" | "Устарело" | "Недоступно" | "Нет данных" | "Доступ заблокирован";
  tone: "success" | "warning" | "danger" | "neutral";
  explanation: string;
};
```

### Internal request signature

```text
METHOD + "\n" + normalized_path + "\n" + timestamp + "\n" + nonce + "\n" + raw_body
```

Required headers are `X-Internal-Key-Id`, `X-Internal-Timestamp`, `X-Internal-Nonce`, `X-Internal-Signature`. Request skew is ±300 seconds; `(key_id, nonce)` is durable for 24 hours.

### Action-intent execution headers

Existing domain endpoints keep their URL and JSON payload and require these headers for L2/L3 execution:

```text
X-Admin-Intent-Id: 00000000-0000-4000-8000-000000000001
X-Admin-Idempotency-Key: 00000000-0000-4000-8000-000000000002
X-Admin-Confirmation-SHA256: e8b1377a618599615bb50a2ab60846ec4d477374da9128d98c6983ac626324a6
```

The last value is SHA-256 of NFC-normalized, trimmed UTF-8 confirmation text (`ПОДТВЕРДИТЬ` in this example). Browser and backend use the same normalization; raw Cyrillic is not placed in an HTTP header or log.

### Baseline verification checkpoint

Before Task 1, record current results without changing product code:

```powershell
git status --short --branch
git diff -- portal_bot/api.py portal_bot/worker.py
cd adminapp
npm.cmd run build
npm.cmd run lint
npm.cmd run test:e2e
cd ..
python -B -m pytest -p no:cacheprovider tests/test_admin_ops_api.py tests/test_admin_payments_api.py tests/test_ru_probe_runner.py tests/test_worker_retention.py -q
```

Label pre-existing failures exactly; do not convert them into PASS.

---

## Slice 1 — Foundation

### Task 1: Russian Status and UI Primitive Contract

**Files:**
- Create: `tests/test_adminapp_command_center_contract.py`
- Create: `adminapp/src/lib/ops-status/types.ts`
- Create: `adminapp/src/lib/ops-status/presentation.ts`
- Create: `adminapp/src/components/ui/button.tsx`
- Create: `adminapp/src/components/ui/status-badge.tsx`
- Create: `adminapp/src/components/ui/source-row.tsx`
- Create: `adminapp/src/components/ui/tooltip.tsx`
- Create: `adminapp/src/components/ui/dialog.tsx`
- Create: `adminapp/src/components/ui/data-table.tsx`
- Create: `adminapp/src/components/ui/states.tsx`
- Create: `adminapp/src/components/ui/index.ts`
- Modify: `adminapp/src/components/data-table.tsx`
- Modify: `adminapp/src/app/globals.css`

**Interfaces:**
- `statusPresentation(code: OpsStatusCode): OpsStatusPresentation`
- `formatSourceAge(sampledAt: string | null, now?: Date): string`
- `<OpsTooltip id content source sampledAt threshold action>` supports hover, keyboard focus, `Escape` and focus return.
- `<SourceRow source status sampledAt threshold detail>` never substitutes missing numeric values with zero.

- [ ] **Step 1: Write the failing static contract tests**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_status_mapper_has_the_seven_approved_russian_labels() -> None:
    text = (ROOT / "adminapp/src/lib/ops-status/presentation.ts").read_text(encoding="utf-8")
    for label in (
        "Норма",
        "Требует внимания",
        "Сбой",
        "Устарело",
        "Недоступно",
        "Нет данных",
        "Доступ заблокирован",
    ):
        assert label in text


def test_tooltip_contract_is_not_a_title_attribute() -> None:
    text = (ROOT / "adminapp/src/components/ui/tooltip.tsx").read_text(encoding="utf-8")
    assert "aria-describedby" in text
    assert 'role="tooltip"' in text
    assert 'event.key === "Escape"' in text
    assert " title=" not in text
```

- [ ] **Step 2: Run the contract test and confirm it fails because the new files do not exist**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_adminapp_command_center_contract.py -q
```

Expected: FAIL at the first missing file.

- [ ] **Step 3: Implement the exact status mapping**

```ts
const STATUS_PRESENTATION: Record<OpsStatusCode, OpsStatusPresentation> = {
  ok: { label: "Норма", tone: "success", explanation: "Свежие обязательные проверки прошли." },
  degraded: { label: "Требует внимания", tone: "warning", explanation: "Источник дал данные, но есть частичное отклонение." },
  failed: { label: "Сбой", tone: "danger", explanation: "Проверка выполнилась и вернула явный отказ." },
  stale: { label: "Устарело", tone: "warning", explanation: "Последнее пригодное измерение старше допустимого окна." },
  unavailable: { label: "Недоступно", tone: "neutral", explanation: "Источник или путь проверки не позволил получить вердикт." },
  missing: { label: "Нет данных", tone: "neutral", explanation: "Пригодного измерения пока нет." },
  BLOCKED_BY_ACCESS: { label: "Доступ заблокирован", tone: "danger", explanation: "Есть подписанное доказательство отсутствия требуемого доступа." }
};
```

Implement `formatSourceAge` with these outputs: null → `Нет данных`; `<60s` → `только что`; `<60m` → `N мин назад`; `<24h` → `N ч назад`; otherwise `N дн назад`. Keep exact timestamp in `<time dateTime>`.

Move the generic TanStack table behavior from the root `components/data-table.tsx` into the new shared primitive without changing current legacy imports yet; Task 21 removes the compatibility file after every route migrates.

- [ ] **Step 4: Add dense dark tokens and accessible focus behavior**

Define command-center canvas/surface/border/text/status tokens, 40px minimum controls, `:focus-visible` ring, `prefers-reduced-motion`, 1280/1440 density and `<1024px` drawer/detail rules. Do not remove existing shared design-token imports.

- [ ] **Step 5: Run focused checks**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_adminapp_command_center_contract.py -q
cd adminapp
npm.cmd run lint
npm.cmd run build
cd ..
git diff --check
```

Expected: PASS.

- [ ] **Step 6: Commit only Task 1 files**

```powershell
git add tests/test_adminapp_command_center_contract.py adminapp/src/lib/ops-status adminapp/src/components/ui adminapp/src/components/data-table.tsx adminapp/src/app/globals.css
git commit -m "feat(adminapp): add Russian status primitives"
```

### Task 2: Grouped Shell, Mobile Navigation and Command Palette

**Files:**
- Modify: `adminapp/src/lib/sections.ts`
- Create: `adminapp/src/lib/url-state.ts`
- Create: `adminapp/src/components/ops/navigation.tsx`
- Create: `adminapp/src/components/ops/mobile-navigation.tsx`
- Create: `adminapp/src/components/ops/topbar.tsx`
- Create: `adminapp/src/components/ops/command-palette.tsx`
- Create: `adminapp/src/components/ops/ops-shell.tsx`
- Modify: `adminapp/src/components/ops-dashboard.tsx`
- Modify: `adminapp/src/components/ui/dialog.tsx`
- Modify: `adminapp/src/components/shell.tsx`
- Modify: `adminapp/src/lib/api.ts`
- Modify: `adminapp/e2e/adminapp-smoke.spec.ts`
- Create: `adminapp/e2e/fixtures/admin-api.ts`
- Create: `adminapp/e2e/shell-and-overview.spec.ts`

**Interfaces:**
- `OPS_GROUPS` contains exactly the approved 15 routes in five groups.
- `readUrlState<T>()`, `replaceUrlState(patch)`, `pushUrlState(patch)` preserve unrelated query keys.
- `Ctrl+K` opens navigation/search; `Escape` closes; selection returns focus and updates canonical URL.
- Global search calls only `GET /api/admin/search?q=` after two non-space characters.

- [ ] **Step 1: Write the failing grouped-shell E2E**

```ts
test("оболочка группирует 15 разделов и открывает палитру с клавиатуры", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  for (const group of ["Команда", "Сеть", "Клиенты", "Деньги и рост", "Управление"]) {
    await expect(page.getByRole("navigation").getByText(group, { exact: true })).toBeVisible();
  }
  await expect(page.getByRole("link")).toHaveCount(15);
  await page.keyboard.press("Control+k");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeHidden();
});
```

- [ ] **Step 2: Run the E2E and confirm it fails against the flat legacy shell**

```powershell
cd adminapp
npx.cmd playwright test e2e/shell-and-overview.spec.ts --project=chromium
```

Expected: FAIL because grouped navigation and command dialog do not exist.

- [ ] **Step 3: Replace the section registry with this exact information architecture**

```ts
export const OPS_GROUPS = [
  { label: "Команда", sections: [{ id: "dashboard", label: "Главная", href: "/" }] },
  { label: "Сеть", sections: [
    { id: "nodes", label: "Ноды", href: "/nodes" },
    { id: "traffic", label: "Трафик", href: "/traffic" },
    { id: "alerts", label: "Алерты", href: "/alerts" },
    { id: "provider-caps", label: "Лимиты провайдеров", href: "/provider-caps" },
    { id: "free-tier", label: "Бесплатный контур", href: "/free-tier" }
  ] },
  { label: "Клиенты", sections: [
    { id: "users", label: "Пользователи", href: "/users" },
    { id: "online", label: "Сейчас онлайн", href: "/online" },
    { id: "tickets", label: "Тикеты", href: "/tickets" }
  ] },
  { label: "Деньги и рост", sections: [
    { id: "payments", label: "Платежи", href: "/payments" },
    { id: "funnel", label: "Воронка", href: "/funnel" },
    { id: "promos", label: "Промо", href: "/promos" },
    { id: "referrals", label: "Рефералы", href: "/referrals" }
  ] },
  { label: "Управление", sections: [
    { id: "release", label: "Релиз", href: "/release" },
    { id: "broadcast", label: "Рассылка", href: "/broadcast" }
  ] }
] as const;
```

Derive `OPS_SECTIONS` by `flatMap`; do not maintain a second route list.

- [ ] **Step 4: Implement URL state and the shell**

Use `history.pushState/replaceState`, `popstate`, typed query codecs and a `<1024px` dialog drawer. Topbar shows Russian section name, oldest required source age, «Обновить», «Команды» and API/session state. The shell must not fetch domain data.

- [ ] **Step 5: Implement the typed search result contract in the fixture and palette**

```ts
export type AdminSearchResult = {
  kind: "user" | "order" | "node" | "key";
  id: string;
  title: string;
  subtitle: string;
  href: string;
};
```

The mock returns safe subtitles and canonical hrefs such as `/nodes?selected=nl` and `/users?selected=1001`; it never returns raw IP, subscription URL or token.

Until Task 10 adds the production search endpoint, a `404` renders the inline state «Поиск пока недоступен» while section navigation remains usable; it must not close the shell or replace the current route.

- [ ] **Step 6: Run checks**

```powershell
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/shell-and-overview.spec.ts --project=chromium
cd ..
python -B -m pytest -p no:cacheprovider tests/test_adminapp_command_center_contract.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 7: Commit only Task 2 files**

```powershell
git add adminapp/src/lib/sections.ts adminapp/src/lib/url-state.ts adminapp/src/lib/api.ts adminapp/src/components/ops adminapp/src/components/ops-dashboard.tsx adminapp/src/components/ui/dialog.tsx adminapp/src/components/shell.tsx adminapp/e2e/adminapp-smoke.spec.ts adminapp/e2e/fixtures/admin-api.ts adminapp/e2e/shell-and-overview.spec.ts
git commit -m "feat(adminapp): build grouped operations shell"
```

### Task 3: Route-Only Loading and Action-First Home

**Files:**
- Create: `adminapp/src/lib/admin-api/client.ts`
- Create: `adminapp/src/lib/admin-api/types.ts`
- Create: `adminapp/src/lib/admin-api/overview.ts`
- Create: `adminapp/src/lib/use-route-resource.ts`
- Create: `adminapp/src/components/ops/route-boundary.tsx`
- Create: `adminapp/src/features/overview/action-queue.tsx`
- Create: `adminapp/src/features/overview/overview-page.tsx`
- Create: `adminapp/src/features/legacy/legacy-section.tsx`
- Create: `adminapp/src/features/registry.tsx`
- Modify: `adminapp/src/components/ops-dashboard.tsx`
- Modify: `adminapp/src/lib/api.ts`
- Modify: `adminapp/e2e/adminapp-smoke.spec.ts`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`
- Modify: `adminapp/e2e/shell-and-overview.spec.ts`

**Interfaces:**
- `apiFetch<T>(path, init)` preserves current session/initData behavior and adds typed `AdminApiError { status, code, correlationId }`.
- `useRouteResource` aborts stale requests, retains the last successful value as «Обновляем» and polls only while `document.visibilityState === "visible"`.
- Home loads `/api/admin/ops/overview`, `/api/admin/alerts?status=active` and, after Task 9 becomes available, `/api/admin/probes/ru-origin/latest`; no other route endpoints.
- Action queue sort key: severity rank descending, affected count descending, source timestamp ascending, stable ID ascending.

- [ ] **Step 1: Add a failing request-isolation E2E**

```ts
test("главная не загружает данные скрытых разделов", async ({ page }) => {
  const calls: string[] = [];
  await installAdminApiMock(page, { onRequest: (path) => calls.push(path) });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();

  expect(calls).toContain("/api/admin/ops/overview");
  expect(calls).not.toContain("/api/admin/users?page_size=50");
  expect(calls).not.toContain("/api/admin/nodes/runtime");
  expect(calls).not.toContain("/api/admin/payments/orders?limit=80");
});
```

- [ ] **Step 2: Run the test and confirm the current `Promise.allSettled` loader violates it**

```powershell
cd adminapp
npx.cmd playwright test e2e/shell-and-overview.spec.ts --project=chromium -g "скрытых разделов"
```

Expected: FAIL with unexpected endpoint calls.

- [ ] **Step 3: Extract the authenticated client without changing auth semantics**

Move existing session/initData helpers and `apiFetch` into `lib/admin-api/client.ts`. Keep `lib/api.ts` as explicit re-exports so legacy sections compile during migration.

- [ ] **Step 4: Implement route resource behavior**

```ts
export type RouteResourceState<T> = {
  data: T | null;
  error: AdminApiError | null;
  loading: boolean;
  refreshing: boolean;
  updatedAt: string | null;
  reload: () => void;
};

export function useRouteResource<T>(
  key: string,
  load: (signal: AbortSignal) => Promise<T>,
  options: { pollMs?: number; enabled?: boolean }
): RouteResourceState<T>;
```

Abort on key/unmount, ignore aborted errors, retain last data during refresh and pause polling in hidden tabs.

- [ ] **Step 5: Build the action-first home**

Render, in order: «Требует реакции», 4–6 compact KPI, node contour, separate Brain/RU freshness rows and recent admin events. Do not render deep traffic/payment/funnel charts. One failed source renders an inline retry state while successful blocks remain visible.

- [ ] **Step 6: Make `OpsDashboard` a thin active-route dispatcher**

`features/registry.tsx` maps the active `OpsSectionId` to one component. Move the current unmigrated section renderers into `features/legacy/legacy-section.tsx` and replace their loader with an explicit per-section endpoint switch. An unmigrated key mounts only that selected legacy renderer. The old global `Promise.allSettled` is removed now; Task 21 deletes the adapter after the last route migrates.

- [ ] **Step 7: Run focused regression**

```powershell
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/shell-and-overview.spec.ts --project=chromium
cd ..
python -B -m pytest -p no:cacheprovider tests/test_adminapp_command_center_contract.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 3 files**

```powershell
git add adminapp/src/lib/admin-api adminapp/src/lib/use-route-resource.ts adminapp/src/components/ops/route-boundary.tsx adminapp/src/features adminapp/src/components/ops-dashboard.tsx adminapp/src/lib/api.ts adminapp/e2e/adminapp-smoke.spec.ts adminapp/e2e/fixtures/admin-api.ts adminapp/e2e/shell-and-overview.spec.ts
git commit -m "refactor(adminapp): load only the active operations route"
```

---

## Slice 2 — Network and RU Origin

### Task 4: RU Probe Persistence and Idempotent Migrations

**Files:**
- Modify: `portal_bot/models.py`
- Modify: `portal_bot/migrations.py`
- Create: `tests/test_ru_probe_migrations.py`
- Modify: `tests/test_migrations_retention_templates.py`
- Modify: `tests/test_postgres_migration_helpers.py`

**Tables and invariants:**

| Table | Required key/constraints |
|---|---|
| `ru_probe_runs` | unique `run_id`; indexed `finished_at`, `release_verdict`, `current_eligible`, `probe_host_label`; raw body is represented only by `artifact_sha256`, never stored as secret-bearing log text |
| `ru_probe_target_results` | FK `run_db_id → ru_probe_runs.id ON DELETE CASCADE`; unique `(run_db_id,target_id)`; server verdict column `overall_status`; indexes `node_code`, `target_kind`, `overall_status`, `(node_code,observed_at)` and `(run_db_id,node_code)` |
| `ru_probe_uploader_heartbeats` | unique `(probe_host_id,observed_at)`; indexes `received_at`, `probe_host_id` and `(probe_host_id,observed_at)`; DTO fields are allowlisted columns/JSON only |
| `internal_ingest_nonces` | unique `(key_scope,key_id,nonce_hash)`; index `expires_at`; stores nonce SHA-256 plus path/timestamp/body hash for audit, never raw nonce, secret or signature |

- [ ] **Step 1: Write failing SQLite model/migration assertions**

```python
def test_ru_probe_tables_have_required_constraints(api_module) -> None:
    from sqlalchemy import inspect

    inspector = inspect(api_module.engine)
    assert {
        "ru_probe_runs",
        "ru_probe_target_results",
        "ru_probe_uploader_heartbeats",
        "internal_ingest_nonces",
    }.issubset(set(inspector.get_table_names()))
    assert any(
        item["name"] == "uq_ru_probe_target_run_target"
        for item in inspector.get_unique_constraints("ru_probe_target_results")
    )
```

Also assert the target FK has `ondelete=CASCADE`, nonce unique is `(key_scope,key_id,nonce_hash)`, no raw `nonce` column exists, and running `run_migrations(engine)` twice succeeds.

- [ ] **Step 2: Run and confirm missing tables fail**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_migrations.py -q
```

Expected: FAIL because the tables do not exist.

- [ ] **Step 3: Add SQLAlchemy models with exact domain columns**

`RuProbeRun` includes IDs/version/origin/host, started/finished/received timestamps, manifest/execution/environment/release/current fields, server booleans, redacted reason/summary, artifact/key identity and retention hold fields. `RuProbeTargetResult` stores identity, endpoint/stages/address-family/transport JSON, server verdict and bounded redacted detail. Heartbeat stores the schema-v1 counters, disk/archive state and allowlisted last error. Nonce stores only `key_scope`, `key_id`, SHA-256 `nonce_hash`, normalized request path, request timestamp, body SHA-256, expiry and creation time; it stores no raw nonce, secret or signature.

- [ ] **Step 4: Add `_ensure_ru_probe_domain_sqlite` and `_ensure_ru_probe_domain_postgres`**

Call them immediately after the existing admin-ops domain helpers at `migrations.py` SQLite and PostgreSQL paths. Use explicit `CREATE TABLE IF NOT EXISTS`, named unique constraints and `CREATE INDEX IF NOT EXISTS`; do not rely only on `Base.metadata.create_all` for legacy DBs.

- [ ] **Step 5: Prove both migration paths**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_migrations.py tests/test_migrations_retention_templates.py tests/test_postgres_migration_helpers.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 6: Commit only Task 4 files**

```powershell
git add portal_bot/models.py portal_bot/migrations.py tests/test_ru_probe_migrations.py tests/test_migrations_retention_templates.py tests/test_postgres_migration_helpers.py
git commit -m "feat(ops): add durable RU probe storage"
```

### Task 5: Exact-Byte Internal HMAC and Durable Replay Protection

**Files:**
- Create: `portal_bot/internal_request_auth.py`
- Create: `tests/test_internal_request_auth.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class InternalServiceKey:
    key_id: str
    secret: bytes
    subject: str
    scopes: frozenset[str]
    origins: frozenset[str]
    enabled: bool


@dataclass(frozen=True)
class AuthenticatedInternalRequest:
    key_id: str
    subject: str
    nonce: str
    request_timestamp: datetime
    body_sha256: str
```

Functions to implement with these exact signatures:

- `normalize_signed_path(path: str) -> str`
- `signature_preimage(method: str, path: str, timestamp: str, nonce: str, raw_body: bytes) -> bytes`
- `sign_internal_request(secret: bytes, method: str, path: str, timestamp: str, nonce: str, raw_body: bytes) -> str`
- `authenticate_internal_request(session, registry, *, method, path, raw_body, headers, required_scope, required_origin, now) -> AuthenticatedInternalRequest`

`normalize_signed_path` accepts only absolute URL paths, rejects query/fragment/backslash/dot segments, collapses duplicate slashes and removes a trailing slash except `/`.

- [ ] **Step 1: Write failing golden-vector and replay tests**

```python
def test_signature_binds_exact_bytes_method_path_timestamp_and_nonce() -> None:
    secret = b"test-secret-not-for-production"
    body = b'{"label":"\xd0\xbc\xd0\xb8\xd0\xbd\xd0\xb8"}'
    signature = sign_internal_request(
        secret,
        "POST",
        "/api/internal/probes/ru-origin/runs",
        "1784102400",
        "nonce-001",
        body,
    )
    assert signature == hmac.new(
        secret,
        b"POST\n/api/internal/probes/ru-origin/runs\n1784102400\nnonce-001\n" + body,
        hashlib.sha256,
    ).hexdigest()


def test_nonce_replay_is_rejected_after_first_commit(session, registry, headers, raw_body) -> None:
    authenticate_internal_request(session, registry, method="POST", path=RUNS_PATH, raw_body=raw_body, headers=headers, required_scope="ru_probe:ingest", required_origin="ru", now=NOW)
    with pytest.raises(InternalAuthError) as exc:
        authenticate_internal_request(session, registry, method="POST", path=RUNS_PATH, raw_body=raw_body, headers=headers, required_scope="ru_probe:ingest", required_origin="ru", now=NOW)
    assert exc.value.status_code == 409
    assert exc.value.code == "replayed_nonce"
```

Add cases for modified whitespace/body, wrong method/path, unknown/disabled key, missing scope, host/origin binding, ±301s skew and concurrent unique violation.

- [ ] **Step 2: Run and confirm import failure**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_internal_request_auth.py -q
```

Expected: FAIL because `internal_request_auth` does not exist.

- [ ] **Step 3: Implement key loading and authentication**

Load keys only from `INTERNAL_HMAC_KEYS_FILE`, a JSON file outside the repository with mode checked by deployment. Test fixtures use a temporary file containing dummy secrets. Registry records `subject`, `scopes`, `origins`, `enabled`; errors expose stable codes but never key material or signatures.

Keep module-level signing/path helpers stdlib-only. Import `InternalIngestNonce` and database-specific exceptions inside the verifier path so `scripts/internal_hmac_client.py` can reuse the pure signing functions without importing the application ORM on `mini`.

- [ ] **Step 4: Implement durable nonce insertion in the caller transaction**

Validate size/timestamp/key/scope/HMAC first, then create `InternalIngestNonce(key_scope=required_scope, key_id=key.key_id, nonce_hash=hashlib.sha256(nonce.encode("utf-8")).hexdigest(), request_path=path, request_timestamp=request_time, body_sha256=body_hash, expires_at=now + timedelta(hours=24))`, add it to the caller session and call `flush()`. Never persist the raw nonce. Convert the unique race to `409 replayed_nonce`; the API task will commit nonce and domain rows together.

- [ ] **Step 5: Run focused tests**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_internal_request_auth.py tests/test_ru_probe_migrations.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 6: Commit only Task 5 files**

```powershell
git add portal_bot/internal_request_auth.py tests/test_internal_request_auth.py
git commit -m "feat(security): verify exact-byte internal requests"
```

### Task 6: Server Manifest, Canonical Hashes and Payload Schema

**Files:**
- Create: `portal_bot/ru_probe_contract.py`
- Create: `portal_bot/ru_probe_service.py`
- Create: `scripts/ru_probe_payload.schema.json`
- Create: `tests/fixtures/ru_probe_manifest_vector.json`
- Create: `tests/test_ru_probe_contract.py`
- Create: `tests/test_ru_probe_service.py`

**Interfaces:**

```python
MANIFEST_SCHEMA_VERSION = 1
RUN_SCHEMA_VERSION = 2
ALLOWED_ADDRESS_FAMILIES = ("ipv4", "ipv6")
ALLOWED_STAGES = ("dns", "tcp", "tls", "http_large_body", "transport_handshake")
ALLOWED_PROBE_MODES = (
    "google_https",
    "canonical_https_large_body",
    "delivery_tls",
    "xhttp_handshake",
    "hysteria_handshake",
)
```

Functions to implement with these exact signatures:

- `canonical_json_bytes(value: object) -> bytes`
- `endpoint_fingerprint(endpoint: dict[str, object]) -> str`
- `manifest_revision(targets: list[dict[str, object]]) -> str`
- `validate_run_payload(payload: object) -> dict[str, object]`
- `build_ru_manifest(session, *, now: datetime) -> dict[str, object]`
- `evaluate_ru_run(session, payload: dict[str, object], *, now: datetime) -> EvaluatedRuRun`

`ru_probe_contract.py` stays stdlib-only so `scripts/ru_probe_runner.py` can import the same canonicalization on `mini`.

- [ ] **Step 1: Write failing canonicalization tests**

```python
def test_manifest_revision_ignores_envelope_time_and_orders_targets() -> None:
    targets = [VECTOR["targets"][1], VECTOR["targets"][0]]
    assert manifest_revision(targets) == VECTOR["manifest_revision"]
    assert endpoint_fingerprint(VECTOR["targets"][0]["endpoint"]) == VECTOR["endpoint_fingerprints"]["environment:google"]


def test_payload_schema_rejects_extra_fields_and_more_than_256_targets() -> None:
    payload = valid_payload()
    payload["unexpected"] = True
    with pytest.raises(RuProbeContractError) as exc:
        validate_run_payload(payload)
    assert exc.value.code == "unknown_field"
```

Golden vector uses UTF-8 Cyrillic label, targets in reverse order, reversed address families and exact expected SHA-256 strings generated once from the approved canonicalization.

- [ ] **Step 2: Write failing manifest membership tests**

Cover: enabled node included; draining node included; disabled node with mapped clients included; disabled node without clients omitted as `not_in_scope`; fixed Google target; canonical public targets; configured XHTTP/Hysteria reserve targets; no secret material.

- [ ] **Step 3: Run and confirm failure**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_contract.py tests/test_ru_probe_service.py -q
```

Expected: FAIL because contract/service files do not exist.

- [ ] **Step 4: Implement canonicalization exactly**

Use UTF-8, `ensure_ascii=False`, sorted object keys and separators `(',', ':')`. Sort targets by `target_id`; normalize `address_families` and `required_stages` in allowlist order. Hash manifest preimage exactly as `{ "manifest_schema_version": 1, "targets": normalized_targets }`. Hash endpoint object alone for fingerprint.

- [ ] **Step 5: Implement deterministic target sources**

- Google is fixed as `environment:google`, `google.com:443`, mode `google_https`, required `dns,tcp,tls,http_large_body`, minimum body 65,536 bytes.
- Canonical defaults are `pokrov.space`, `app.pokrov.space`, `api.pokrov.space`; override only through validated `RU_PROBE_CANONICAL_TARGETS_JSON` public config.
- Reserve targets come only from validated `RU_PROBE_RESERVE_TARGETS_JSON`; a transport target contains a local profile ID name, never profile material.
- Delivery target `node:<code>` uses `Node.host`, `Node.vless_port`, `Node.reality_sni`, a normalized public transport profile and server-required `dns,tcp,tls`.
- Include a delivery node when `enabled`, `is_draining` or mapped/provisioned client count is positive.

- [ ] **Step 6: Write the complete JSON Schema**

Schema draft 2020-12 enforces envelope and nested `additionalProperties: false`, `schema_version: const 2`, UUID run ID, `origin: const ru`, timezone-aware UTC strings, enumerated execution/stage/probe values, 1–256 unique-by-service targets, bounded labels/codes/detail and the exact endpoint/stage/transport object properties from the design spec. Service performs semantic uniqueness, UTC, host/SNI, timestamp-order and fingerprint checks that JSON Schema cannot express.

- [ ] **Step 7: Implement server verdict tests and logic**

Test Google-down → `unavailable_probe_host`; required stage fail → node `failed`; `not_run` → `incomplete`; old manifest → `superseded_manifest`; extra diagnostic does not affect release; protocol alive only from `transport_handshake=pass`; aggregate release PASS only when every release-required target passes.

- [ ] **Step 8: Run focused tests**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_contract.py tests/test_ru_probe_service.py tests/test_ru_probe_migrations.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 9: Commit only Task 6 files**

```powershell
git add portal_bot/ru_probe_contract.py portal_bot/ru_probe_service.py scripts/ru_probe_payload.schema.json tests/fixtures/ru_probe_manifest_vector.json tests/test_ru_probe_contract.py tests/test_ru_probe_service.py
git commit -m "feat(ops): define RU probe manifest and verdict contract"
```

### Task 7: Manifest-Driven RU Runner v2

**Files:**
- Create: `scripts/internal_hmac_client.py`
- Modify: `scripts/ru_probe_runner.py`
- Modify: `scripts/ru_probe_sample.json`
- Modify: `tests/test_ru_probe_runner.py`
- Modify: `tests/test_render_ru_probe_report.py`

**Runner CLI:**

```text
--api-base-url https://api.pokrov.space
--key-id ru-mini-v1
--secret-file /etc/pokrov-ru-probe/hmac.key
--manifest-cache /var/lib/pokrov-ru-probe/manifest-cache.json
--spool-root /var/lib/pokrov-ru-probe
--probe-host-id mini
--probe-host-label mini
--profile-registry /etc/pokrov-ru-probe/profiles.json
--timeout-sec 10
```

`profiles.json` maps an allowlisted `local_probe_profile_id` to an absolute executable plus fixed argv. Runner invokes it with `shell=False`, passes public endpoint JSON through stdin and accepts one bounded JSON response:

```json
{
  "schema_version": 1,
  "profile_id": "reserve-hysteria",
  "protocol": "hysteria2",
  "handshake_status": "pass",
  "classification": "ok",
  "detail_code": null
}
```

Missing registry/profile/executable produces `not_run` with `probe_material_unavailable`; it never produces PASS.

- [ ] **Step 1: Replace the obsolete reachability test with failing strict-stage tests**

```python
def test_delivery_tcp_success_does_not_mask_tls_failure(self) -> None:
    with mock.patch.object(
        self.module.dataplane_probe,
        "probe_node_endpoint",
        return_value={
            "ok": False,
            "stage": "tls",
            "error_kind": "tls_handshake_failed",
            "error_message": "handshake failed",
            "resolved_ips": ["198.51.100.10"],
            "latency_ms": 20,
            "tls_protocol": "",
            "tls_cipher": "",
        },
    ):
        result = self.module.run_manifest_target(delivery_target(), timeout_sec=5.0, profile_registry={})
    self.assertEqual(result["stages"]["tcp"]["status"], "pass")
    self.assertEqual(result["stages"]["tls"]["status"], "fail")


def test_udp_send_without_valid_protocol_response_is_not_hysteria_pass(self) -> None:
    result = self.module.transport_stage_from_adapter(
        "hysteria_handshake",
        {"handshake_status": "not_run", "classification": "viability_hint", "detail_code": "sent_no_response"},
    )
    self.assertEqual(result["status"], "not_run")
```

Add tests proving large-body GET reads at least 65,536 bytes, `HEAD` is never used, unavailable profile is `not_run`, cached manifest is accepted only within `max_cache_age_seconds`, and output validates as schema v2.

- [ ] **Step 2: Run and confirm old semantics fail**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_runner.py tests/test_ru_probe_contract.py -q
```

Expected: FAIL on renamed API and strict TLS/UDP assertions.

- [ ] **Step 3: Implement shared request signing for GET and POST**

`internal_hmac_client.py` reads secret bytes from a mode-restricted file, generates a new random nonce and current Unix timestamp per attempt, signs exact body bytes with `sign_internal_request`, and returns headers. It must not print secret, signature or body.

- [ ] **Step 4: Fetch and cache the manifest atomically**

Signed GET uses empty raw body. Write cache through `.tmp`, file `0600`, `flush`, `fsync`, atomic `os.replace` and parent-directory `fsync`. On network error use cache only when its `generated_at + max_cache_age_seconds` has not elapsed; include the cached revision unchanged.

- [ ] **Step 5: Replace target inference with strict `probe_mode` dispatch**

Implement dispatch for `google_https`, `canonical_https_large_body`, `delivery_tls`, `xhttp_handshake`, `hysteria_handshake`. Initialize all five stages. A required unexecuted stage is `not_run`; a non-required stage is `not_applicable`. Copy the manifest endpoint and fingerprint exactly into each result.

- [ ] **Step 6: Implement real HTTPS large-body GET**

Send `GET`, validate TLS/SNI, accept HTTP 2xx–3xx only, read chunks until at least `min_body_bytes`, EOF or timeout, and record actual bytes read. `http_large_body=pass` requires at least 65,536 bytes. Do not disable certificate verification for canonical hosts.

- [ ] **Step 7: Implement protocol adapter enforcement**

Validate profile ID with `^[a-z0-9][a-z0-9_-]{0,63}$`, resolve only a registry entry, require absolute executable path and fixed string argv, use `subprocess.run(command_argv, input=request_bytes, capture_output=True, shell=False, timeout=timeout_sec, check=False)`, cap stdout/stderr capture, validate response schema and require matching protocol/profile. Exit timeout/malformed response is `fail`; absent safe material is `not_run`.

- [ ] **Step 8: Build the schema-v2 envelope**

Use UUID `run_id`, aware UTC start/finish, `origin=ru`, runner version `2.0`, manifest revision, completed/partial/runner_error/blocked status, host identity and exact target results. Remove v1 aggregate authority fields from verdict logic; optional diagnostic summaries may remain only where schema explicitly allows them.

- [ ] **Step 9: Update the redacted sample and report compatibility**

Make `scripts/ru_probe_sample.json` a valid schema-v2 artifact with documentation IPs and no material. Update report renderer tests so `true`, `false`, `not_run` and `not_applicable` remain distinct.

- [ ] **Step 10: Run focused tests**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_runner.py tests/test_ru_probe_contract.py tests/test_render_ru_probe_report.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 11: Commit only Task 7 files**

```powershell
git add scripts/internal_hmac_client.py scripts/ru_probe_runner.py scripts/ru_probe_sample.json tests/test_ru_probe_runner.py tests/test_render_ru_probe_report.py
git commit -m "feat(probes): run manifest-driven RU checks"
```

### Task 8: Immutable Spool, Uploader, Heartbeat and systemd Templates

**Files:**
- Create: `scripts/ru_probe_uploader.py`
- Create: `tests/test_ru_probe_uploader.py`
- Create: `infra/pokrov-ru-probe.service`
- Create: `infra/pokrov-ru-probe.timer`
- Create: `infra/pokrov-ru-probe-uploader.service`
- Create: `infra/pokrov-ru-probe-uploader.timer`
- Modify: `scripts/ru_probe_runner.py`
- Modify: `scripts/manifest.yaml`

**Spool contract:**

```text
/var/lib/pokrov-ru-probe/
  pending/<run_id>.json
  pending/<run_id>.sha256
  blocked/<run_id>.json
  blocked/<run_id>.sha256
  blocked/<run_id>.reason.json
  quarantine/<run_id>.json
  quarantine/<run_id>.sha256
  quarantine/<run_id>.reason.json
  archive/<run_id>.json
  archive/<run_id>.sha256
```

Directories are `0700`, files `0600`. Artifact bytes and sidecar hash never change between attempts.

- [ ] **Step 1: Write failing atomic-write and transition tests**

```python
def test_write_artifact_is_atomic_and_hash_matches_exact_bytes(tmp_path) -> None:
    artifact = b'{"schema_version":2,"run_id":"00000000-0000-4000-8000-000000000001"}'
    path = write_pending_artifact(tmp_path, "00000000-0000-4000-8000-000000000001", artifact)
    assert path.read_bytes() == artifact
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.with_suffix(".sha256").read_text(encoding="ascii").strip() == hashlib.sha256(artifact).hexdigest()
    assert not list(tmp_path.rglob("*.tmp"))


@pytest.mark.parametrize(
    ("status", "code", "destination"),
    [(201, "created", "archive"), (503, "temporary", "pending"), (403, "key_disabled", "blocked"), (422, "invalid_payload", "quarantine")],
)
def test_upload_transition_matrix(status, code, destination, spool, transport) -> None:
    transport.respond(status=status, body={"code": code, "correlation_id": "corr-1"})
    outcome = upload_one(spool.pending_artifact, transport=transport, now=NOW)
    assert outcome.destination == destination
```

Add cases for 408/425/429/5xx retry, `409 replayed_nonce` one re-sign then quarantine, `409 payload_conflict`, archive move/fsync failure keeping pending, sidecar mismatch quarantine and heartbeat DTO redaction.

- [ ] **Step 2: Run and confirm missing uploader fails**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_uploader.py -q
```

Expected: FAIL because uploader module does not exist.

- [ ] **Step 3: Implement atomic artifact creation**

Use `os.open` with `O_CREAT|O_EXCL`, write/fsync/close, then atomic rename and directory fsync. Create the sidecar from exact artifact bytes with the same durability sequence. Refuse overwrite of an existing run ID with different bytes.

- [ ] **Step 4: Implement upload classification and backoff**

Every attempt gets a fresh timestamp/nonce and signs unchanged file bytes. Exponential delay is `min(3600, 60 * 2**attempt)` plus bounded random jitter. Reason sidecars contain only status, stable code, correlation ID and timestamp. Successful archive requires artifact and sidecar moves plus directory fsync; otherwise keep pending.

- [ ] **Step 5: Implement separate heartbeat creation**

Schema v1 fields are host ID, observed time, service version, pending/blocked/quarantine counts, oldest pending, archive write state, disk free/state and allowlisted last error code. Heartbeat is generated per uploader invocation and never written into or appended to a run artifact.

- [ ] **Step 6: Add hardened unit templates**

Probe timer uses `OnCalendar=*-*-* 00,06,12,18:00:00`, `Persistent=true` and at most five minutes randomized delay. Uploader timer uses `OnBootSec=2m`, `OnUnitActiveSec=15m`, `Persistent=true`. Services use `User=pokrov-ru-probe`, `StateDirectory=pokrov-ru-probe`, `StateDirectoryMode=0700`, `UMask=0077`, `NoNewPrivileges=true`, `PrivateTmp=true`, read-only system paths and explicit writable state path. Secrets come from `/etc/pokrov-ru-probe/`, not unit text.

- [ ] **Step 7: Register only static files in the script manifest**

Add runner, uploader, contract schema and four unit templates to `scripts/manifest.yaml`; do not run a deploy script.

- [ ] **Step 8: Run focused checks**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_uploader.py tests/test_ru_probe_runner.py tests/test_check_script_manifest.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 9: Commit only Task 8 files**

```powershell
git add scripts/ru_probe_uploader.py scripts/ru_probe_runner.py scripts/manifest.yaml tests/test_ru_probe_uploader.py infra/pokrov-ru-probe.service infra/pokrov-ru-probe.timer infra/pokrov-ru-probe-uploader.service infra/pokrov-ru-probe-uploader.timer
git commit -m "feat(probes): add durable RU spool delivery"
```

### Task 9: RU Manifest, Run and Heartbeat HTTP APIs

**Files:**
- Modify: `portal_bot/api.py`
- Modify: `portal_bot/ru_probe_service.py`
- Create: `tests/test_ru_probe_ingest_api.py`
- Modify: `tests/test_admin_ops_api.py`

**Endpoints:**
- `GET /api/internal/probes/ru-origin/manifest` — scope `ru_probe:manifest`, empty exact body.
- `POST /api/internal/probes/ru-origin/runs` — scope `ru_probe:ingest`, maximum 512 KiB.
- `POST /api/internal/probes/ru-origin/heartbeat` — scope `ru_probe:heartbeat`, maximum 64 KiB.

**Stable run response:**

```json
{
  "code": "created",
  "run_db_id": 17,
  "run_id": "00000000-0000-4000-8000-000000000001",
  "created": true,
  "current_eligible": true,
  "correlation_id": "request-correlation-id"
}
```

- [ ] **Step 1: Write failing API tests for auth and idempotency**

Test: valid manifest GET; missing signature `401`; wrong scope `403`; body over limit `413`; malformed/duplicate target `422`; first run `201`; same run and exact bytes with new nonce `200`; same run/different bytes `409 payload_conflict`; repeated nonce `409 replayed_nonce`; host binding mismatch `403`; heartbeat does not modify run rows.

```python
def test_same_run_same_exact_bytes_is_idempotent(client, signed_headers, valid_run_bytes) -> None:
    first = client.post(RUNS_PATH, content=valid_run_bytes, headers=signed_headers(valid_run_bytes, nonce="n-1"))
    second = client.post(RUNS_PATH, content=valid_run_bytes, headers=signed_headers(valid_run_bytes, nonce="n-2"))
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["run_db_id"] == second.json()["run_db_id"]
    assert second.json()["created"] is False
```

- [ ] **Step 2: Run and confirm routes are missing**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_ingest_api.py -q
```

Expected: FAIL with 404/import errors.

- [ ] **Step 3: Add thin raw-body handlers**

Use `_read_limited_request_body` before JSON parse. Build a plain lowercase header map, call `authenticate_internal_request`, validate/evaluate with `ru_probe_service`, commit nonce plus domain rows once, and translate typed service errors to stable status/code. Never echo signature or secret.

- [ ] **Step 4: Implement transactional run idempotency**

Compute `artifact_sha256` from raw request bytes. Query by `run_id` inside the transaction. Equal hash returns existing row; different hash raises conflict. Catch the unique race after flush, roll back to savepoint, re-read the winner and return `200` or `409` instead of `500`.

- [ ] **Step 5: Preserve incomplete and superseded runs honestly**

Valid partial/missing-target/old-manifest payloads are stored with `current_eligible=false` and a stable `ineligible_reason`; none can update latest eligible PASS. A run older than retention is stored as ineligible historical/quarantine evidence and does not restore deleted current history.

- [ ] **Step 6: Implement heartbeat ingest**

Validate the exact schema-v1 allowlist, host binding and timestamps, then insert or idempotently read `(probe_host_id,observed_at)`. Derive no local reason when a heartbeat is absent.

- [ ] **Step 7: Run API regression**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_ingest_api.py tests/test_internal_request_auth.py tests/test_ru_probe_service.py tests/test_admin_ops_api.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 9 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/ru_probe_service.py tests/test_ru_probe_ingest_api.py tests/test_admin_ops_api.py
git commit -m "feat(api): ingest signed RU probe evidence"
```

### Task 10: RU Read Models, Search, Alerts and Retention

**Files:**
- Modify: `portal_bot/ru_probe_service.py`
- Modify: `portal_bot/admin_ops_service.py`
- Modify: `portal_bot/api.py`
- Modify: `portal_bot/worker.py`
- Modify: `tests/test_ru_probe_service.py`
- Modify: `tests/test_admin_ops_api.py`
- Modify: `tests/test_worker_retention.py`
- Modify: `adminapp/src/lib/admin-api/overview.ts`
- Modify: `adminapp/src/features/overview/overview-page.tsx`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`
- Modify: `adminapp/e2e/shell-and-overview.spec.ts`

**Endpoints:**
- `GET /api/admin/probes/ru-origin/latest`
- `GET /api/admin/probes/ru-origin/runs?node_code=&from=&to=&verdict=&limit=&cursor=`
- `GET /api/admin/probes/ru-origin/uploader-status`
- `GET /api/admin/nodes/{code}/observability`
- `GET /api/admin/search?q=`

- [ ] **Step 1: Write failing latest/out-of-order tests**

```python
def test_latest_eligible_uses_finished_at_not_received_at(session, seeded_manifest) -> None:
    newer = store_run(session, finished_at=NOW, received_at=NOW, current_eligible=True, release_verdict="pass")
    store_run(session, finished_at=NOW - timedelta(hours=2), received_at=NOW + timedelta(minutes=1), current_eligible=True, release_verdict="pass")
    latest = get_latest_ru_status(session, now=NOW + timedelta(minutes=2))
    assert latest["eligible_run"]["run_id"] == newer.run_id


def test_google_failure_is_unavailable_not_node_failure(session) -> None:
    latest = ingest_fixture(session, "google-down.json")
    assert latest["environment_verdict"] == "unavailable"
    assert {row["status"] for row in latest["nodes"]} == {"unavailable"}
```

Add stale at 7h, missing without run, newest received attempt separate from last eligible, opaque `(finished_at,id)` cursor, unknown node diagnostic, heartbeat fresh/stale at 45m, and admin-auth on every endpoint.

- [ ] **Step 2: Write failing retention tests**

Cover unheld run older than `RU_PROBE_RETENTION_DAYS=180` deleted with target cascade; held run retained; nonce older than 24h deleted; late old run never replaces current. Task 12 adds its own prepared-intent cleanup assertions when that table is introduced.

- [ ] **Step 3: Run and confirm missing read models fail**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_service.py tests/test_admin_ops_api.py tests/test_worker_retention.py -q
```

Expected: FAIL on new cases/routes.

- [ ] **Step 4: Implement latest/history/uploader projections**

`latest` returns threshold metadata, separate `latest_received_attempt` and `latest_eligible_run`, environment/reserve statuses and every known node with `ok/degraded/failed/stale/unavailable/missing`. History omits raw heavy JSON and uses deterministic descending order. Uploader status reports accepted DTO facts and server-derived age only.

- [ ] **Step 5: Implement node observability aggregation**

Return node metadata, lifecycle, capacity, Brain metrics/observer, current runtime, RU latest/history summary, transports and alerts. Every source row carries its own `sampled_at`, threshold and stable reason codes. Do not return credentials or raw IP lists.

- [ ] **Step 6: Implement typed safe search**

Search Telegram ID, username/display name, install ID, order ID, node code and key/email. Limit to 20 grouped results. Each result is `{kind,id,title,subtitle,href}`; subtitle is safe and never contains raw IP, subscription URL/token, callback body or provider payload.

- [ ] **Step 7: Add RU alert candidates**

`ru_probe_run_stale` after 7h, `ru_probe_uploader_heartbeat_stale` after 45m, backlog/quarantine/disk/archive alerts only from a received heartbeat. Merge via existing durable `OpsAlert` fingerprint flow; do not let alert refresh compute RU verdicts.

- [ ] **Step 8: Add retention helpers to the existing telemetry job**

Delete only unheld old runs, expired nonce rows and old heartbeats according to configured retention. Preserve release-held runs. Reconcile changes with the pre-existing dirty `worker.py` diff before applying.

- [ ] **Step 9: Add RU latest to the overview client and home**

Modify `adminapp/src/lib/admin-api/overview.ts`, `adminapp/src/features/overview/overview-page.tsx` and the shell fixture so Brain and RU freshness are separate; a failed RU request leaves other overview blocks intact.

- [ ] **Step 10: Run focused regression**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_ru_probe_service.py tests/test_admin_ops_api.py tests/test_worker_retention.py -q
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/shell-and-overview.spec.ts --project=chromium
cd ..
git diff --check
```

Expected: PASS.

- [ ] **Step 11: Commit only Task 10 files**

```powershell
git add -p portal_bot/api.py
git add -p portal_bot/worker.py
git add portal_bot/ru_probe_service.py portal_bot/admin_ops_service.py tests/test_ru_probe_service.py tests/test_admin_ops_api.py tests/test_worker_retention.py adminapp/src/lib/admin-api/overview.ts adminapp/src/features/overview/overview-page.tsx adminapp/e2e/fixtures/admin-api.ts adminapp/e2e/shell-and-overview.spec.ts
git commit -m "feat(ops): expose RU freshness and node evidence"
```

### Task 11: Node Master–Detail and RU History UI

**Files:**
- Create: `adminapp/src/lib/admin-api/nodes.ts`
- Create: `adminapp/src/features/nodes/nodes-page.tsx`
- Create: `adminapp/src/features/nodes/node-list.tsx`
- Create: `adminapp/src/features/nodes/node-detail.tsx`
- Create: `adminapp/src/features/nodes/node-source-summary.tsx`
- Create: `adminapp/src/features/nodes/ru-history.tsx`
- Create: `adminapp/src/features/nodes/uploader-status.tsx`
- Create: `adminapp/e2e/nodes.spec.ts`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`
- Modify: `adminapp/src/features/registry.tsx`

**URL state:** `q`, `state`, `freshness`, `country`, `hoster`, `transport`, `alert`, `selected`, `tab`, `range`.

- [ ] **Step 1: Write failing master–detail E2E**

```ts
test("карточка ноды открывается за два действия и разделяет три источника", async ({ page }) => {
  await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  await page.goto("/nodes");
  await page.getByRole("row", { name: /NL/ }).click();
  await expect(page).toHaveURL(/selected=nl/);
  await expect(page.getByRole("heading", { name: "Нода NL" })).toBeVisible();
  await expect(page.getByText("Текущий контур", { exact: true })).toBeVisible();
  await expect(page.getByText("Brain-origin", { exact: true })).toBeVisible();
  await expect(page.getByText("RU-origin", { exact: true })).toBeVisible();
});
```

Add scenarios `google-down`, `stale`, `missing`, `superseded-manifest`, `incomplete-latest-with-last-good`, `uploader-backlog`, `uploader-heartbeat-stale`, and true/false/not-applicable stage rendering.

- [ ] **Step 2: Run and confirm legacy node UI fails**

```powershell
cd adminapp
npx.cmd playwright test e2e/nodes.spec.ts --project=chromium
```

Expected: FAIL because route module/RU detail is absent.

- [ ] **Step 3: Add typed node endpoint clients**

Define `NodeListRow`, `NodeObservability`, `RuLatest`, `RuRunSummary`, `RuUploaderStatus` with nullable values and stable enums. Fetch list summaries on route load; fetch observability/history only after `selected` is set. Use separate AbortControllers for list and detail.

- [ ] **Step 4: Build the dense list**

Show code/country, lifecycle, worst-status reasons, Brain/RU badges, CPU/port load, provisioned clients, online hint and oldest required source age. Search/filter in URL. Missing numeric values use `—`; filters never infer missing as zero.

- [ ] **Step 5: Build the detail tabs**

Tabs: «Обзор», «Проверки из РФ», «Нагрузка», «Клиенты», «Транспорт», «Алерты», «Технические детали». The first layer uses Russian explanations and source ages. Technical codes/endpoint fingerprints stay in collapsed details.

- [ ] **Step 6: Render honest RU attempt/history states**

Show latest received attempt separately from last eligible result; show old manifest, incomplete and Google-down explicitly. Stage matrix preserves pass/fail/not_run/not_applicable. Uploader stale says «Нет свежей связи с загрузчиком» and does not guess auth/network/disk.

- [ ] **Step 7: Add responsive behavior and polling**

At desktop use list/detail columns; below 1024px selected node becomes a sequential detail screen with «Назад к нодам». Poll list/latest every 60s only in visible tab. Do not poll history unless the history tab is active.

- [ ] **Step 8: Run frontend checks**

```powershell
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/nodes.spec.ts --project=chromium
cd ..
python -B -m pytest -p no:cacheprovider tests/test_adminapp_command_center_contract.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 9: Commit only Task 11 files**

```powershell
git add adminapp/src/lib/admin-api/nodes.ts adminapp/src/features/nodes adminapp/src/features/registry.tsx adminapp/e2e/nodes.spec.ts adminapp/e2e/fixtures/admin-api.ts
git commit -m "feat(adminapp): add node RU observability workspace"
```

### Task 12: Server Action-Intent Storage and Core Service

**Files:**
- Modify: `portal_bot/models.py`
- Modify: `portal_bot/migrations.py`
- Create: `portal_bot/admin_action_intent_service.py`
- Modify: `portal_bot/api.py`
- Create: `tests/test_admin_action_intents.py`
- Modify: `tests/test_ru_probe_migrations.py`
- Modify: `tests/test_worker_retention.py`

**Table:** `admin_action_intents` stores UUID, actor, action, target type/id, risk, canonical payload/hash, redacted preview snapshot/hash, challenge kind/hash, entity-version hash, status, expiry/consume/result fields, unique client idempotency key and nullable `admin_audit_id FK admin_audit.id ON DELETE RESTRICT`.

**Preview endpoint:** `POST /api/admin/action-intents`

```json
{
  "action": "node.disable",
  "target": {"type": "node", "id": "nl"},
  "payload": {"force": false}
}
```

Response includes `intent_id`, `risk_level`, redacted `preview`, hashes, `entity_version_hash`, `confirmation_challenge`, `expires_at`.

- [ ] **Step 1: Write failing intent lifecycle tests**

Cover unknown action, actor/action/target/payload mismatch, 10-minute expiry, stale entity version, incorrect confirmation, concurrent consume, same idempotency key returning stored result, different key after consumed returning conflict, and fail-closed audit creation.

```python
def test_execute_requires_intent_and_rechecks_entity_version(client, admin_headers, seeded_node) -> None:
    direct = client.post("/api/admin/nodes/nl/disable", json={"force": False}, headers=admin_headers)
    assert direct.status_code == 428
    assert direct.json()["detail"]["code"] == "intent_required"

    intent = prepare_intent(client, admin_headers, action="node.disable", target_id="nl", payload={"force": False})
    mutate_node_version(seeded_node)
    result = execute_node_disable(client, admin_headers, intent, confirmation="NL")
    assert result.status_code == 409
    assert result.json()["detail"]["code"] == "stale_intent"
```

- [ ] **Step 2: Run and confirm endpoint/model absence**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py -q
```

Expected: FAIL.

- [ ] **Step 3: Add model and both idempotent migration paths**

Name constraints `uq_admin_action_intents_idempotency` and `fk_admin_action_intents_audit`. Add indexes on actor/status/expires/action/target. Preserve completed/failed/uncertain rows; worker deletes only prepared/expired rows older than seven days with no audit.

- [ ] **Step 4: Implement canonical payload and policy registry**

Each policy declares action, target type, L2/L3 risk, payload normalizer, entity snapshot/version builder, preview builder, challenge kind and executor kind (`db` or `external`). Canonical JSON uses the same deterministic serializer but action policies never reuse RU/release hashes semantically. Confirmation is normalized with Unicode NFC plus trim, hashed as UTF-8 SHA-256 and compared constant-time to `X-Admin-Confirmation-SHA256`.

- [ ] **Step 5: Refactor admin audit without breaking L1 call sites**

Add `_add_admin_audit(session, actor_tg_id, action, target_tg_id, meta) -> AdminAudit`, which flushes and returns the row. Keep `_audit_admin` as the compatibility wrapper for existing L1 handlers. L2/L3 paths pass their current session and treat audit failure as transaction failure.

- [ ] **Step 6: Implement prepare and consume semantics**

Prepare rereads the entity, stores immutable redacted snapshot and 10-minute expiry. DB executor locks intent/entity, verifies headers/body/challenge/version, performs mutation, creates audit, stores completed result and commits once. External executor atomically marks `executing` with audit ID before side effect; exception/timeout becomes `uncertain` and is never auto-retried.

- [ ] **Step 7: Expose stable API errors**

No intent → `428 intent_required`; expired/mismatch/stale/consumed conflict → `409` with stable code; invalid confirmation → `409 confirmation_mismatch`; unknown action → `422 unknown_action`. Responses contain intent ID and audit ID where created, never canonical payload or full external message.

- [ ] **Step 8: Run focused backend tests**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_ru_probe_migrations.py tests/test_worker_retention.py tests/test_admin_ops_api.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 9: Commit only Task 12 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/models.py portal_bot/migrations.py portal_bot/admin_action_intent_service.py tests/test_admin_action_intents.py tests/test_ru_probe_migrations.py tests/test_worker_retention.py tests/test_admin_ops_api.py
git commit -m "feat(admin): add server action intents"
```

### Task 13: Node Lifecycle Actions Through Server Intents

**Files:**
- Modify: `portal_bot/admin_action_intent_service.py`
- Modify: `portal_bot/api.py`
- Modify: `tests/test_admin_action_intents.py`
- Create: `adminapp/src/lib/admin-api/actions.ts`
- Create: `adminapp/src/components/ops/action-intent-dialog.tsx`
- Create: `adminapp/src/features/nodes/node-actions.tsx`
- Modify: `adminapp/src/features/nodes/node-detail.tsx`
- Modify: `adminapp/e2e/nodes.spec.ts`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`

**Action policies:**

| Action | Risk | Confirmation | Executor |
|---|---|---|---|
| `node.drain` | L2 | `ПОДТВЕРДИТЬ` | DB |
| `node.undrain` | L2 | `ПОДТВЕРДИТЬ` | DB |
| `node.enable` | L2 | `ПОДТВЕРДИТЬ` | DB |
| `node.resync` | L2 | `ПОДТВЕРДИТЬ` | external panel operation |
| `node.disable` | L3 | exact uppercase node code | DB |

- [ ] **Step 1: Extend failing backend tests over every node endpoint**

Assert direct calls to drain/undrain/enable/disable/resync all return `428`; valid intent executes once; node version mismatch returns `409`; resync uncertain outcome does not retry; completed result contains `action_intent_id` and `audit_id`.

- [ ] **Step 2: Add failing dialog E2E**

```ts
test("отключение ноды выполняется только после серверного preview и ввода кода", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/nodes?selected=nl");
  await page.getByRole("button", { name: "Отключить ноду" }).click();
  await expect(page.getByRole("dialog", { name: "Проверка действия" })).toContainText("Будет отключена нода NL");
  await page.getByLabel("Подтверждение").fill("NL");
  await page.getByRole("button", { name: "Выполнить" }).click();
  await expect(page.getByText(/ID аудита:/)).toBeVisible();
});
```

- [ ] **Step 3: Run and confirm unguarded endpoints/UI fail**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py -q
cd adminapp
npx.cmd playwright test e2e/nodes.spec.ts --project=chromium -g "серверного preview"
cd ..
```

Expected: FAIL.

- [ ] **Step 4: Move node mutation bodies behind policy executors**

Do not keep parallel unguarded helpers. Reuse the same normalized payload in preview and execute. DB lifecycle changes, intent consume and audit commit in one session. Resync freezes source node/user selection in preview and follows external uncertain semantics.

- [ ] **Step 5: Implement the shared frontend intent flow**

`prepareActionIntent` POSTs action/target/payload. `executeAdminAction` sends the original domain payload, intent/idempotency UUID headers and the lowercase SHA-256 of `input.normalize("NFC").trim()` as the confirmation header. Dialog renders server preview/before-after, risk, prompt, expiry and Russian states for `428`, expired, stale, uncertain and completed. It never auto-retries a write.

- [ ] **Step 6: Refresh authoritative node state after a known outcome**

On completed, refetch node list/detail and display audit ID. On uncertain, keep the dialog result and offer «Проверить состояние ноды», not «Повторить действие».

- [ ] **Step 7: Run full node slice checks**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_ops_api.py -q
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/nodes.spec.ts --project=chromium
cd ..
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 13 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/admin_action_intent_service.py tests/test_admin_action_intents.py adminapp/src/lib/admin-api/actions.ts adminapp/src/components/ops/action-intent-dialog.tsx adminapp/src/features/nodes adminapp/e2e/nodes.spec.ts adminapp/e2e/fixtures/admin-api.ts
git commit -m "feat(admin): guard node lifecycle commands"
```

---

## Slice 3 — Clients and Support

### Task 14: Guard User, Key and Ticket Mutations

**Files:**
- Modify: `portal_bot/admin_action_intent_service.py`
- Modify: `portal_bot/api.py`
- Modify: `tests/test_admin_action_intents.py`
- Modify: `tests/test_admin_ops_api.py`

**Required policies:**

| Actions | Risk/challenge | Executor |
|---|---|---|
| `user.manual_create`, `user.extend`, `user.key_toggle`, `user.key_limits`, `user.key_reset_traffic`, `user.key_resync_subid`, `user.loyalty_grant`, `user.preset_run` | L2 / `ПОДТВЕРДИТЬ` | DB or panel-backed external according to current handler |
| `user.block`, `user.regenerate_token`, `user.safe_delete`, `user.delete_test`, `user.bulk_key_action`, `key.rotate` | L3 / exact Telegram ID or key ID | DB/external according to current handler |
| `user.message`, `ticket.reply` | L2 / `ОТПРАВИТЬ` | external Telegram effect |
| `ticket.status` | L2 / `ПОДТВЕРДИТЬ` | DB, with the current close notification handled as an external post-commit effect |

The duplicate legacy routes `/manual/extend` and `/manual-extend` share one action policy and one guarded executor; neither remains unguarded.

- [ ] **Step 1: Parameterize failing direct-call coverage**

```python
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/api/admin/users/1001/manual/block", {"reason": "incident"}),
        ("POST", "/api/admin/users/1001/keys/nl/reset-traffic", {}),
        ("PUT", "/api/admin/users/1001/key-limits/nl", {"max_devices": 2}),
        ("POST", "/api/admin/tickets/7/reply", {"text": "Проверили, доступ восстановлен."}),
        ("POST", "/api/admin/keys/17/rotate", {"reason": "operator"}),
    ],
)
def test_client_mutation_requires_action_intent(client, admin_headers, method, path, body) -> None:
    response = client.request(method, path, json=body, headers=admin_headers)
    assert response.status_code == 428
    assert response.json()["detail"]["code"] == "intent_required"
```

Add a case for every policy row, plus entity-version change, payload mismatch, external uncertain outcome and audit redaction.

- [ ] **Step 2: Run and confirm existing endpoints are still unguarded**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_ops_api.py -q
```

Expected: FAIL on direct-call assertions.

- [ ] **Step 3: Extract existing bodies into policy executors**

Preserve current domain semantics and response fields. Preview reads current user/key/ticket state and emits a redacted before/after summary. External message bodies are represented in intent/audit only by SHA-256 and length; user IDs are bounded/frozen where bulk action applies.

- [ ] **Step 4: Apply transactional and external rules**

DB-only changes, intent consume and audit commit together. Panel/Telegram operations enter `executing` before the call and end `completed`, `failed` or `uncertain`; repeated idempotency key returns stored result and never sends twice.

- [ ] **Step 5: Verify compatibility aliases and privacy**

Both manual-extend URLs require the same intent action. General endpoint responses still omit raw IP except the explicit user detail endpoint. Audit metadata contains IDs/hashes/counts, not message body, token or subscription URL.

- [ ] **Step 6: Run focused backend regression**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_ops_api.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 7: Commit only Task 14 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/admin_action_intent_service.py tests/test_admin_action_intents.py tests/test_admin_ops_api.py
git commit -m "feat(admin): guard client and ticket mutations"
```

### Task 15: Users, Online and Tickets Route Modules

**Files:**
- Create: `adminapp/src/lib/admin-api/users.ts`
- Create: `adminapp/src/lib/admin-api/support.ts`
- Create: `adminapp/src/features/users/users-page.tsx`
- Create: `adminapp/src/features/users/user-list.tsx`
- Create: `adminapp/src/features/users/user-detail.tsx`
- Create: `adminapp/src/features/users/user-actions.tsx`
- Create: `adminapp/src/features/support/online-page.tsx`
- Create: `adminapp/src/features/support/tickets-page.tsx`
- Create: `adminapp/src/features/support/ticket-detail.tsx`
- Create: `adminapp/e2e/clients.spec.ts`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`
- Modify: `adminapp/src/features/registry.tsx`

**URL state:**
- Users: `q`, `status`, `sort`, `selected`, `tab`.
- Online: `node`, `source`, `q`.
- Tickets: `status`, `priority`, `selected`.

- [ ] **Step 1: Write failing route/privacy E2E**

```ts
test("общий online-список не содержит raw IP, а user detail открывает расследование", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/online");
  await expect(page.getByText("203.0.113.44")).toHaveCount(0);
  await page.getByRole("link", { name: /Пользователь 1001/ }).click();
  await expect(page).toHaveURL(/\/users\?.*selected=1001/);
  await page.getByRole("tab", { name: "Расследование" }).click();
  await expect(page.getByText("203.0.113.44")).toBeVisible();
});
```

Add direct loads for all three routes, lazy user/ticket detail, back-forward restoration, 30-second visible-tab online polling and action-intent reply/block flows.

- [ ] **Step 2: Run and confirm legacy route behavior fails**

```powershell
cd adminapp
npx.cmd playwright test e2e/clients.spec.ts --project=chromium
```

Expected: FAIL.

- [ ] **Step 3: Implement typed endpoint clients**

Move existing user/card/online/ticket fetches from `lib/api.ts`. Define nullable source-age fields explicitly. Add action wrappers that always use the shared intent dialog for Task 14 policies.

- [ ] **Step 4: Build user master–detail**

The first layer shows access state, expiry, plan, online/source age and node assignments. Detail tabs expose keys, payments, tickets, observer/risk, audit and investigation. Raw IP is requested/rendered only inside selected-user investigation and never cached in global search/online rows.

- [ ] **Step 5: Build online and ticket workflows**

Online is a bounded live aggregate with source/age and no raw IP. Tickets use action queue ordering, lazy thread detail, preserved list position and action-intent reply/status. Failed reply keeps the draft; uncertain result offers state refresh.

- [ ] **Step 6: Switch only these three registry entries after parity**

Remove their imports from the legacy adapter only after direct-load, navigation, filters, details and writes pass. Other routes remain on their current new/legacy entry.

- [ ] **Step 7: Run slice regression**

```powershell
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/clients.spec.ts e2e/shell-and-overview.spec.ts --project=chromium
cd ..
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_ops_api.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 15 files**

```powershell
git add adminapp/src/lib/admin-api/users.ts adminapp/src/lib/admin-api/support.ts adminapp/src/features/users adminapp/src/features/support adminapp/src/features/registry.tsx adminapp/e2e/clients.spec.ts adminapp/e2e/fixtures/admin-api.ts
git commit -m "feat(adminapp): add client and support workspaces"
```

---

## Slice 4 — Network, Money and Growth

### Task 16: Traffic, Alerts, Provider Limits and Free Contour

**Files:**
- Modify: `portal_bot/admin_action_intent_service.py`
- Modify: `portal_bot/api.py`
- Modify: `tests/test_admin_action_intents.py`
- Create: `adminapp/src/lib/admin-api/network.ts`
- Create: `adminapp/src/features/network/traffic-page.tsx`
- Create: `adminapp/src/features/network/alerts-page.tsx`
- Create: `adminapp/src/features/network/provider-limits-page.tsx`
- Create: `adminapp/src/features/network/free-tier-page.tsx`
- Create: `adminapp/e2e/network-and-revenue.spec.ts`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`
- Modify: `adminapp/src/features/registry.tsx`

**Write policies:** provider quota create/update are L2 with `ПОДТВЕРДИТЬ`; delete is L3 with exact node code. Alert acknowledge/silence remain L1 and keep normal audit without an action intent.

- [ ] **Step 1: Write failing provider guard tests**

Assert unguarded POST/PATCH/DELETE provider quota calls return `428`, preview contains server-computed before/after and projected exhaustion, stale quota version returns `409`, delete requires exact node code. Assert alert ack/silence still work without intent and remain audited.

- [ ] **Step 2: Write failing route E2E**

Test direct load of `/traffic`, `/alerts`, `/provider-caps`, `/free-tier`; identical range/node filters for chart/table; null point creates a chart gap and table «Нет данных»; free and paid pools stay separate; provider review uses intent; alert links to entity context.

- [ ] **Step 3: Run and confirm failures**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_ops_api.py -q
cd adminapp
npx.cmd playwright test e2e/network-and-revenue.spec.ts --project=chromium -g "Сеть"
cd ..
```

Expected: FAIL.

- [ ] **Step 4: Guard provider mutations and preserve quota audit**

Use canonical normalized bytes/ratios/timezone in payload hash. DB quota mutation, `ProviderTrafficQuotaAudit`, `AdminAudit` and intent completion commit together. Delete preview includes dependent node/status facts and requires node code confirmation.

- [ ] **Step 5: Build the four route modules**

Traffic uses summary, range, one primary chart, breakdowns and source table. Alerts use action queue and inline detail with source/age/duration. Provider limits use table/edit drawer/server review. Free contour shows burn rate, total/user limits and user rows without mixing paid pool.

- [ ] **Step 6: Keep missing data honest**

Recharts receives `null` for a missing point with `connectNulls={false}`. Tables render `—` and status mapping. No client-side fallback converts null to zero.

- [ ] **Step 7: Switch the four registry entries and run checks**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_ops_api.py -q
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/network-and-revenue.spec.ts --project=chromium -g "Сеть"
cd ..
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 16 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/admin_action_intent_service.py tests/test_admin_action_intents.py adminapp/src/lib/admin-api/network.ts adminapp/src/features/network adminapp/src/features/registry.tsx adminapp/e2e/network-and-revenue.spec.ts adminapp/e2e/fixtures/admin-api.ts
git commit -m "feat(adminapp): add network operations routes"
```

### Task 17: Payments, Funnel, Promos and Referrals

**Files:**
- Modify: `portal_bot/admin_action_intent_service.py`
- Modify: `portal_bot/api.py`
- Modify: `tests/test_admin_action_intents.py`
- Modify: `tests/test_admin_payments_api.py`
- Create: `adminapp/src/lib/admin-api/revenue.ts`
- Create: `adminapp/src/features/revenue/payments-page.tsx`
- Create: `adminapp/src/features/revenue/funnel-page.tsx`
- Create: `adminapp/src/features/revenue/promos-page.tsx`
- Create: `adminapp/src/features/revenue/referrals-page.tsx`
- Modify: `adminapp/e2e/network-and-revenue.spec.ts`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`
- Modify: `adminapp/src/features/registry.tsx`

**Write policies:** `payment.reconcile`, `promo.create`, `promo.update`, `referral.process` are L2; `promo.delete` is L3 with exact promo code. The admin UI never creates a new payment or alters provider callback evidence.

- [ ] **Step 1: Write failing server-guard tests**

Direct reconcile/promo/referral mutations return `428`. Reconcile preview freezes provider/order/status and requires note; stale callback/order version returns `409`. Promo preview shows exact before/after/expiry. Referral preview shows queue item and basis, not a new payment mechanism.

- [ ] **Step 2: Extend failing E2E**

Test `/payments`, `/funnel`, `/promos`, `/referrals`; periods today/7d/30d; stuck/provider states separate; chart/table filter parity; no raw JSON; promo edit/delete intent; referral action queue stable sort; partial source errors preserve other blocks.

- [ ] **Step 3: Run and confirm failures**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_payments_api.py -q
cd adminapp
npx.cmd playwright test e2e/network-and-revenue.spec.ts --project=chromium -g "Деньги"
cd ..
```

Expected: FAIL.

- [ ] **Step 4: Guard backend actions**

Keep payment ledger/callback immutable. Reconcile mutation, intent and audit commit together and retain the required operator note. Promo/referral DB changes follow the same transaction rule. Audit contains order/provider/code/queue IDs and hashes, not raw callback payload.

- [ ] **Step 5: Build the four route modules**

Payments uses KPI, attention queue and lazy order detail. Funnel uses stages/source breakdown and source table. Promos uses table/edit drawer. Referrals uses deterministic decision queue/history. All writes go through the shared intent dialog.

- [ ] **Step 6: Switch registry entries and run regression**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_admin_payments_api.py tests/test_admin_ops_api.py -q
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/network-and-revenue.spec.ts --project=chromium
cd ..
git diff --check
```

Expected: PASS.

- [ ] **Step 7: Commit only Task 17 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/admin_action_intent_service.py tests/test_admin_action_intents.py tests/test_admin_payments_api.py adminapp/src/lib/admin-api/revenue.ts adminapp/src/features/revenue adminapp/src/features/registry.tsx adminapp/e2e/network-and-revenue.spec.ts adminapp/e2e/fixtures/admin-api.ts
git commit -m "feat(adminapp): add revenue and growth operations"
```

---

## Slice 5 — Release, Broadcast and Full Guard Coverage

### Task 18: Exact-Candidate Release Evidence Backend

**Files:**
- Modify: `portal_bot/models.py`
- Modify: `portal_bot/migrations.py`
- Create: `portal_bot/release_evidence_service.py`
- Modify: `portal_bot/api.py`
- Create: `tests/test_release_evidence_service.py`
- Modify: `tests/test_ru_probe_migrations.py`
- Modify: `tests/test_internal_request_auth.py`
- Modify: `tests/test_worker_retention.py`

**Tables:**
- `release_candidates`: unique canonical `candidate_id`, component/version/revision/artifact hash, canonical descriptor/hash, ingest key and import time.
- `release_origin_evidence`: FK candidate, origin/check/status/evidence hash/time/redacted detail, optional `ru_probe_run_id FK ru_probe_runs.id ON DELETE RESTRICT`, unique `(candidate_id,origin,check_name,evidence_sha256)`.

**Import DTO:**

```json
{
  "schema_version": 1,
  "candidate_id": "c6287c3ec0a4f9ffc6fd9aa2ea8415e25efa1af5983e3f927238e87a01590583",
  "candidate": {
    "component": "adminapp",
    "version": "2026.07.15.1",
    "revision": "9da042c9da042c9da042c9da042c9da042c9da0",
    "artifact_sha256": "1111111111111111111111111111111111111111111111111111111111111111"
  },
  "evidence": [
    {
      "origin": "ru",
      "check_name": "ru_origin_reachability",
      "status": "PASS",
      "observed_at": "2026-07-15T12:00:00Z",
      "evidence_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
      "ru_probe_run_id": "00000000-0000-4000-8000-000000000001",
      "detail": {"source": "retained-run"}
    }
  ]
}
```

- [ ] **Step 1: Write failing candidate identity and honesty tests**

Test server recomputes `candidate_id = sha256(canonical_json(candidate))`; mismatched ID/conflicting descriptor returns `409`; same body/new nonce is idempotent; evidence of candidate A cannot satisfy B; skip/attested/blocked/missing never aggregate to PASS.

- [ ] **Step 2: Write failing RU hold tests**

RU PASS evidence requires an existing current-eligible full run with environment/release PASS. Import sets `retention_hold=true`, reason referencing candidate/check and held time. Deleting held run is restricted. Ineligible/superseded/incomplete run cannot import as PASS.

- [ ] **Step 3: Run and confirm missing backend fails**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_release_evidence_service.py tests/test_ru_probe_migrations.py -q
```

Expected: FAIL.

- [ ] **Step 4: Add models and both migration paths**

Use named foreign/unique/index constraints. Release evidence never cascades away a RU run. Candidate/evidence rows contain redacted descriptors and hashes only; no signing key, private key, raw provider payload or client secret.

- [ ] **Step 5: Implement canonical import and readiness**

Allowed statuses are `PASS`, `FAIL`, `MANUAL_OWNER_TEST`, `OPERATOR_ATTESTED`, `SKIPPED_BY_OWNER`, `SKIPPED_BY_OPERATOR`, `BLOCKED_BY_ACCESS`, `MISSING`. Readiness is PASS only when every required current/brain/RU check for the same candidate is PASS. Return individual status, timestamp, evidence ref and reason without relabeling.

- [ ] **Step 6: Add signed import and admin read APIs**

- `POST /api/internal/releases/candidates` uses scope `release:evidence`, exact-byte HMAC, durable nonce and maximum 256 KiB.
- `GET /api/admin/releases/candidates?limit=&cursor=` requires admin auth.
- `GET /api/admin/releases/{candidate_id}/readiness` requires admin auth.

- [ ] **Step 7: Prove retention and auth regression**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_release_evidence_service.py tests/test_ru_probe_migrations.py tests/test_internal_request_auth.py tests/test_worker_retention.py tests/test_admin_ops_api.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 18 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/models.py portal_bot/migrations.py portal_bot/release_evidence_service.py tests/test_release_evidence_service.py tests/test_ru_probe_migrations.py tests/test_internal_request_auth.py tests/test_worker_retention.py tests/test_admin_ops_api.py
git commit -m "feat(release): bind readiness to exact evidence"
```

### Task 19: Release Checklist and Frozen Broadcast UI

**Files:**
- Modify: `portal_bot/admin_action_intent_service.py`
- Modify: `portal_bot/api.py`
- Modify: `tests/test_admin_action_intents.py`
- Create: `adminapp/src/lib/admin-api/control.ts`
- Create: `adminapp/src/features/control/release-page.tsx`
- Create: `adminapp/src/features/control/broadcast-page.tsx`
- Create: `adminapp/e2e/control.spec.ts`
- Modify: `adminapp/e2e/fixtures/admin-api.ts`
- Modify: `adminapp/src/features/registry.tsx`

**Broadcast policy:** `broadcast.send`, L3, confirmation `ОТПРАВИТЬ`, external executor. Preview freezes exact sorted recipient IDs, segment inputs and message SHA-256. Its stored canonical payload is exactly `{segment, limit, requested_tg_ids_hash, message_sha256, message_length}`; the full message returns only on execute and must hash identically. Intent/audit store count and hashes, not message text or recipient list.

- [ ] **Step 1: Write failing broadcast freeze/idempotency tests**

```python
def test_broadcast_executes_only_frozen_recipients_and_message(client, admin_headers, users) -> None:
    intent = prepare_broadcast_intent(client, admin_headers, segment="all_active", text="Плановые работы")
    activate_another_user(users)
    changed = execute_broadcast(client, admin_headers, intent, text="Другой текст", confirmation="ОТПРАВИТЬ")
    assert changed.status_code == 409
    assert changed.json()["detail"]["code"] == "payload_mismatch"
    sent = execute_broadcast(client, admin_headers, intent, text="Плановые работы", confirmation="ОТПРАВИТЬ")
    assert sent.status_code == 200
    assert sent.json()["attempted"] == intent["preview"]["recipient_count"]
```

Add network-timeout → uncertain/no retry and same idempotency key → stored result.

- [ ] **Step 2: Write failing control-route E2E**

Test exact candidate ID/hash visible; current/brain/RU separate; skip/attested/block/missing use non-success tones; candidate switch changes URL/readiness; broadcast draft survives API error; preview shows frozen count/message hash; execute requires `ОТПРАВИТЬ`; uncertain outcome offers status check.

- [ ] **Step 3: Run and confirm failures**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_release_evidence_service.py -q
cd adminapp
npx.cmd playwright test e2e/control.spec.ts --project=chromium
cd ..
```

Expected: FAIL.

- [ ] **Step 4: Move real broadcast behind the intent executor**

`dry_run=true` may remain a non-sending L0 preview for compatibility, but `dry_run=false` always requires the frozen intent. Selection occurs during prepare, not execute. External status transitions follow Task 12; no automatic resend.

- [ ] **Step 5: Build release checklist**

List exact candidates with component/version/revision/artifact hash and age. Detail renders current, brain and RU checks as separate source rows with evidence refs/timestamps. Aggregate label comes only from backend readiness; technical hash is copyable but secondary.

- [ ] **Step 6: Build protected broadcast form**

Flow: draft → server preview → frozen recipient count/hash → explicit input → execute result with audit/intent ID. Store only a nonsecret draft in session storage. On `401`, preserve draft and URL; on uncertain, do not show a retry-send button.

- [ ] **Step 7: Switch control registry entries and run checks**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_intents.py tests/test_release_evidence_service.py tests/test_admin_ops_api.py -q
cd adminapp
npm.cmd run lint
npm.cmd run build
npx.cmd playwright test e2e/control.spec.ts --project=chromium
cd ..
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 19 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/admin_action_intent_service.py tests/test_admin_action_intents.py adminapp/src/lib/admin-api/control.ts adminapp/src/features/control adminapp/src/features/registry.tsx adminapp/e2e/control.spec.ts adminapp/e2e/fixtures/admin-api.ts
git commit -m "feat(adminapp): add exact release and broadcast control"
```

### Task 20: Close Every Remaining L2/L3 Bypass

**Files:**
- Modify: `portal_bot/admin_action_intent_service.py`
- Modify: `portal_bot/api.py`
- Create: `tests/test_admin_action_policy_coverage.py`
- Modify: `tests/test_admin_action_intents.py`
- Modify: `tests/test_admin_ops_api.py`
- Modify: `tests/test_admin_payments_api.py`

**Remaining guarded families:** plans, live updates, start links, wheel config, network rollout config, WARP material, promo slots, loyalty config, campaigns, templates, access-key issue, gift-code create and global node sync.

**Explicit non-L2/L3 POST allowlist:** auth session L0; alert acknowledge/silence L1; campaign-link build L0 preview; broadcast `dry_run=true` L0 preview. Every other admin mutation decorator must map to an action policy.

- [ ] **Step 1: Add a failing route-policy coverage test**

```python
def test_every_admin_mutation_is_guarded_or_explicitly_low_risk() -> None:
    mutations = discover_admin_mutation_routes(API_PATH.read_text(encoding="utf-8"))
    exempt = {
        ("POST", "/api/admin/auth/session"),
        ("POST", "/api/admin/alerts/{alert_id}/ack"),
        ("POST", "/api/admin/alerts/{alert_id}/silence"),
        ("POST", "/api/admin/campaign-links/build"),
    }
    guarded = set(action_policy_route_keys())
    assert ("POST", "/api/admin/broadcast") in guarded
    assert mutations == guarded | exempt
```

The test parser reads only decorator lines and normalizes method/path. Add a dedicated assertion that non-dry-run broadcast invokes the guard.

- [ ] **Step 2: Run and capture the exact uncovered route set**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_policy_coverage.py -q
```

Expected: FAIL listing remaining endpoint families.

- [ ] **Step 3: Add policies with explicit risk and challenge**

Create/update configuration is L2 with `ПОДТВЕРДИТЬ`; delete/material replacement/access-key issue/gift-code creation/global node sync are L3 with exact target code/key or `ПОДТВЕРДИТЬ УПРАВЛЕНИЕ` as policy-specific challenge. Preview is redacted and entity-versioned. WARP/key material snapshots contain fingerprints only.

- [ ] **Step 4: Move each handler behind its sole executor**

No duplicate unguarded function remains. DB-only actions use one transaction with audit/intent. External/control-panel actions use executing/uncertain semantics. Compatibility URLs share a policy instead of bypassing it.

- [ ] **Step 5: Verify full route coverage and regressions**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_admin_action_policy_coverage.py tests/test_admin_action_intents.py tests/test_admin_ops_api.py tests/test_admin_payments_api.py -q
git diff --check
```

Expected: PASS with exact equality in the coverage test.

- [ ] **Step 6: Commit only Task 20 files**

```powershell
git add -p portal_bot/api.py
git add portal_bot/admin_action_intent_service.py tests/test_admin_action_policy_coverage.py tests/test_admin_action_intents.py tests/test_admin_ops_api.py tests/test_admin_payments_api.py
git commit -m "feat(admin): enforce intent coverage on risky writes"
```

### Task 21: Remove Legacy Monolith and Prove Russian/A11y/Mobile Parity

**Files:**
- Modify: `adminapp/src/components/ops-dashboard.tsx`
- Delete: `adminapp/src/components/ui.tsx`
- Delete: `adminapp/src/components/data-table.tsx`
- Delete: `adminapp/src/features/legacy/legacy-section.tsx`
- Delete: `adminapp/src/lib/api.ts`
- Delete after migrated coverage exists: `adminapp/e2e/adminapp-smoke.spec.ts`
- Create: `adminapp/e2e/accessibility.spec.ts`
- Modify: `adminapp/e2e/shell-and-overview.spec.ts`
- Modify: `adminapp/e2e/nodes.spec.ts`
- Modify: `adminapp/e2e/clients.spec.ts`
- Modify: `adminapp/e2e/network-and-revenue.spec.ts`
- Modify: `adminapp/e2e/control.spec.ts`
- Modify: `tests/test_adminapp_command_center_contract.py`

- [ ] **Step 1: Add failing all-route parity test**

```ts
for (const route of ["/", "/nodes", "/traffic", "/alerts", "/provider-caps", "/free-tier", "/users", "/online", "/tickets", "/payments", "/funnel", "/promos", "/referrals", "/release", "/broadcast"]) {
  test(`прямое открытие ${route}`, async ({ page }) => {
    await installAdminApiMock(page);
    await page.goto(route);
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByText("Ops admin")).toHaveCount(0);
    await expect(page.getByText("Free tier", { exact: true })).toHaveCount(0);
  });
}
```

- [ ] **Step 2: Add failing keyboard/mobile/accessibility tests**

Cover tooltip hover/focus/Escape/focus return, command palette focus trap, dialog focus trap/return, visible focus ring, reduced motion, master-detail mobile back flow, mobile nav drawer, table horizontal scroll and 1280/1440 screenshots without overlap.

- [ ] **Step 3: Add static Russian and architecture guardrails**

Assert `ops-dashboard.tsx` has no `Promise.allSettled` or domain fetch import, `lib/api.ts` has only re-exports or is removed, all 15 Russian labels exist, legacy visible labels `Ops admin`/`Free tier` are absent, tooltip ARIA remains, and route modules do not import sibling domain features.

- [ ] **Step 4: Run tests and confirm legacy files/labels fail**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_adminapp_command_center_contract.py -q
cd adminapp
npx.cmd playwright test --project=chromium
cd ..
```

Expected: FAIL until final migration/cleanup.

- [ ] **Step 5: Remove the old renderer only after all 15 routes pass**

Keep `ops-dashboard.tsx` as the thin registry call. Migrate the final imports to `components/ui/`, verify `rg.exe` finds no consumer of the root `ui.tsx`, root `data-table.tsx` or `features/legacy/legacy-section.tsx`, then delete those three files, legacy API re-exports and the giant smoke test. Split tests must cover every old smoke assertion before deletion.

- [ ] **Step 6: Finish Russian copy and accessible interactions**

Map raw backend errors to stable Russian messages plus correlation ID. Every tooltip answers what/source/age/threshold/action where available. Every modal closes on Escape, traps focus and returns it. Use secondary technical codes, never English as the primary operator label.

- [ ] **Step 7: Run the complete frontend suite**

```powershell
cd adminapp
npm.cmd run lint
npm.cmd run build
npm.cmd run test:e2e
cd ..
python -B -m pytest -p no:cacheprovider tests/test_adminapp_command_center_contract.py tests/test_admin_design_guardrails.py -q
git diff --check
```

Expected: PASS.

- [ ] **Step 8: Commit only Task 21 files**

```powershell
git add adminapp/src adminapp/e2e tests/test_adminapp_command_center_contract.py
git commit -m "refactor(adminapp): remove legacy operations monolith"
```

### Task 22: Canonical Documentation and Full Candidate Verification

**Files:**
- Modify: `adminapp/README.md`
- Modify: `docs/architecture/system-overview.md`
- Modify: `docs/operations/monitoring-and-visibility.md`
- Create: `docs/operations/ru-origin-probe-handoff.md`
- Modify: `docs/operations/publishing-and-signing-guide.md`
- Modify: `docs/operations/deployment-and-access.md`
- Modify: `tests/test_agent_docs_contract.py`
- Modify: `tests/test_agent_context_packet_audit.py`

- [ ] **Step 1: Write documentation assertions before prose changes**

Extend `tests/test_agent_docs_contract.py` to require links among the admin README, system overview, monitoring owner and RU handoff plus the 6h cadence, 7h stale window, 180-day DB retention, exact-candidate rule and no-deploy evidence disclaimer. Extend `tests/test_agent_context_packet_audit.py` to require the new handoff to remain classified as current operations documentation and reachable from its canonical owner.

- [ ] **Step 2: Run and confirm missing canonical text/link failures**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
```

Expected: FAIL on new assertions.

- [ ] **Step 3: Update each owner without duplicating truth**

- `adminapp/README.md`: 15 route modules, Russian interaction patterns, URL state, refresh schedule, action-intent flow and local verification.
- `system-overview.md`: mini → spool → HMAC ingest → RU tables → admin read boundary; release/action services.
- `monitoring-and-visibility.md`: source separation, server verdict semantics, 6h/7h/45m windows, 180-day unheld retention and honest missing/unavailable interpretation.
- `ru-origin-probe-handoff.md`: redacted prerequisites, unit templates, spool states, local validation, heartbeat interpretation, rollback and `MANUAL_OWNER_TEST`/`BLOCKED_BY_ACCESS` labels; no live secret or host mutation command.
- `publishing-and-signing-guide.md` and `deployment-and-access.md`: exact-candidate redacted evidence import, retention hold and explicit statement that local tests are not production/RU proof.

- [ ] **Step 4: Run complete backend and contract suites**

```powershell
python -B -m pytest -p no:cacheprovider tests/test_internal_request_auth.py tests/test_ru_probe_contract.py tests/test_ru_probe_migrations.py tests/test_ru_probe_service.py tests/test_ru_probe_ingest_api.py tests/test_ru_probe_runner.py tests/test_ru_probe_uploader.py tests/test_admin_action_intents.py tests/test_admin_action_policy_coverage.py tests/test_release_evidence_service.py tests/test_admin_ops_api.py tests/test_admin_payments_api.py tests/test_worker_retention.py tests/test_adminapp_command_center_contract.py tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
```

Expected: PASS. If pytest emits a Windows temporary-directory cleanup warning after the PASS summary, record the warning separately and do not hide it.

- [ ] **Step 5: Run complete frontend verification**

```powershell
cd adminapp
npm.cmd run build
npm.cmd run lint
npm.cmd run test:e2e
cd ..
```

Expected: PASS.

- [ ] **Step 6: Run scope, secret and diff checks**

```powershell
git status --short --branch
git diff --stat
git diff --check
rg.exe -n 'BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|X-Internal-Signature|subscription_url.*https://' portal_bot scripts infra adminapp docs/operations
```

Expected: no secret-bearing match; documented header names alone are reviewed manually and are not secret values. Review scoped diffs for `portal_bot/api.py` and `portal_bot/worker.py` against their pre-task dirty state.

- [ ] **Step 7: Commit only canonical documentation/tests**

```powershell
git add -p docs/operations/deployment-and-access.md
git add adminapp/README.md docs/architecture/system-overview.md docs/operations/monitoring-and-visibility.md docs/operations/ru-origin-probe-handoff.md docs/operations/publishing-and-signing-guide.md tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py
git commit -m "docs(ops): document command center and RU evidence"
```

- [ ] **Step 8: Produce the final evidence-backed handoff**

State exact commit/candidate, commands and results, manual checks, blocked checks, warning details, no-deploy state and remaining concerns. Production deployment, actual `mini` timer installation and a real RU-origin PASS remain `NOT_REQUESTED` or `MANUAL_OWNER_TEST` until separately authorized and retained.

---

## Plan Self-Review Checklist

- [ ] Every one of the 15 routes is assigned to a concrete frontend task and direct-load E2E.
- [ ] Manifest, runner, spool, uploader, heartbeat, HMAC, DB, read API, node UI and retention form one complete RU vertical slice.
- [ ] Six-hour schedule, seven-hour stale threshold, 45-minute heartbeat threshold, 180-day DB retention and held-run exclusion are frozen in tests/docs.
- [ ] Google-down, stale, missing, superseded manifest, incomplete latest attempt, last-known-good and unknown diagnostic target remain distinct.
- [ ] Exact candidate evidence cannot be reused across candidates and RU evidence sets a protected retention hold.
- [ ] Every L2/L3 admin mutation is covered by an action policy or fails the exact route-policy test.
- [ ] No task instructs deployment, remote mutation, secret creation in repository or release readiness claim.
- [ ] Interface names/types used by later tasks are introduced by an earlier task.
- [ ] Each task has failing test, focused fail command, implementation boundary, PASS command, scoped staging and commit.
- [ ] Run an unresolved-marker scan over this plan and replace any abbreviation for unfinished work, three-dot omission, generic deferred instruction or undefined follow-up before execution.
