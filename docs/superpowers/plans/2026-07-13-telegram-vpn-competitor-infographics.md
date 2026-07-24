# Telegram VPN Competitor Infographics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three deterministic internal POKROV infographics from the archived Telegram VPN competitor dataset and export each as an editable standalone HTML plus an exact `1600 × 5000` PNG.

**Architecture:** A shared Node.js renderer reads the single archived JSON source, validates it, computes only presentation-safe derived values, and calls one template module per approved direction. Each template returns a complete fixed-canvas HTML document containing inline CSS and SVG charts. A system Chrome headless render step opens each generated HTML file with a forced `1600 × 5000` viewport and device scale `1`, captures an exact PNG, verifies dimensions, and writes a SHA-256 manifest.

**Tech Stack:** Node.js ESM, built-in `fs/path/crypto/child_process`, system Chrome headless CLI, semantic HTML, inline SVG, CSS, Python/Pillow for independent PNG verification, pytest for repository tests.

## Global Constraints

- Output exactly three visual directions: analytical report, war room, growth-mechanism map.
- Every PNG must be exactly `1600 × 5000 px`.
- Primary data source is `docs/competitive/telegram-vpn-2026-07-12/archive/infographic-data.json`.
- Snapshot is `2026-07-12`; post window is `2026-05-12 — 2026-07-12`.
- Missing or invalid values render as text labels, never zero.
- Luma `+199.7%` and Cats `+94.0%` use outlier cards/insets and do not compress the ordinary growth chart.
- POKROV public growth renders as `нет подтверждённой сопоставимой метрики`.
- Marketing aggression is visibly labelled `аналитическая шкала 0–5`.
- Source-of-growth blocks use `inflow_evidence_class`, not unlabelled causal claims.
- App bubble size uses only `android_footprint_scale.entries[].tier`; unknown stays unknown.
- Optional Telegram `+10 days` is a side branch in the POKROV flow, never a required step.
- No invented conversion, retention, churn, CAC, LTV, revenue, demographic or market-share metrics.
- Do not stage, commit, push, deploy or publish; Git actions were not requested.
- Preserve unrelated modifications in `AGENTS.md`, `docs/README.md` and concurrent research files.

---

## File Structure

### Source files

- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/common.mjs`
  - Data validation, escaping, number formatting, shared CSS, SVG helpers, evidence labels and app-tier lookup.
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/analytical.mjs`
  - Template for the light analytical report.
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/war-room.mjs`
  - Template for the dark competitive-intelligence board.
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/growth-funnel.mjs`
  - Template for the warm acquisition/mechanism map.
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/build.mjs`
  - Orchestration, HTML writing, browser launch, PNG capture and manifest generation.
- Create: `tests/test_telegram_vpn_infographics.py`
  - Dataset, HTML, displayed-number, dimension and manifest contract tests.

### Generated deliverables

- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/01-analytical-report.html`
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/01-analytical-report.png`
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/02-war-room.html`
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/02-war-room.png`
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/03-growth-funnel.html`
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/03-growth-funnel.png`
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/manifest.json`

---

### Task 1: Shared Data and Rendering Contract

**Files:**
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/common.mjs`
- Create: `tests/test_telegram_vpn_infographics.py`

**Interfaces:**
- Consumes: parsed `infographic-data.json`.
- Produces:
  - `validateDataset(data): void`
  - `formatInt(value): string`
  - `formatPercent(value): string`
  - `escapeHtml(value): string`
  - `getChannel(data, id): object`
  - `getMarketing(data, id): object | null`
  - `getAppScale(data, id): object | null`
  - `evidenceLabel(value): string`
  - `baseDocument({ title, themeClass, body, sourceHash }): string`
  - `horizontalBars(items, options): string`
  - `sectionHeader(kicker, title, note): string`

- [ ] **Step 1: Write the failing dataset contract test**

```python
def test_infographic_dataset_contract():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert len(data["channels"]) == 19
    assert len(data["marketing_analysis"]) == 19
    assert len(data["android_footprint_scale"]["entries"]) == 9
    assert max(row["growth_30d"] for row in data["channels"]) == 386_200
    assert sum(row["growth_30d"] > 0 for row in data["channels"]) == 15
    assert sum(row["growth_30d"] < 0 for row in data["channels"]) == 4
    assert all("inflow_evidence_class" in row for row in data["marketing_analysis"])
```

- [ ] **Step 2: Run the focused test and verify the output contract is not yet complete**

Run:

```powershell
python.exe -B -m pytest -p no:cacheprovider tests/test_telegram_vpn_infographics.py::test_infographic_dataset_contract -q
```

Expected: PASS for the archived dataset; later output tests remain absent.

- [ ] **Step 3: Implement strict shared validation**

```javascript
export function validateDataset(data) {
  if (!data || !Array.isArray(data.channels) || data.channels.length !== 19) {
    throw new Error("Expected exactly 19 channel records");
  }
  if (!Array.isArray(data.marketing_analysis) || data.marketing_analysis.length !== 19) {
    throw new Error("Expected exactly 19 marketing records");
  }
  const ids = new Set(data.channels.map((row) => row.id));
  if (ids.size !== data.channels.length) throw new Error("Duplicate channel id");
  if (!data.marketing_analysis.every((row) => ids.has(row.id))) {
    throw new Error("Marketing record without matching channel");
  }
  if (!data.marketing_analysis.every((row) => row.inflow_evidence_class)) {
    throw new Error("Missing inflow evidence class");
  }
  const luma = data.channels.find((row) => row.id === "luma-vpn");
  const cats = data.channels.find((row) => row.id === "cats-vpn");
  if (luma?.growth_30d_percent !== 199.7 || cats?.growth_30d_percent !== 94.0) {
    throw new Error("Outlier values drifted");
  }
}
```

- [ ] **Step 4: Implement formatting and escaping helpers**

```javascript
export const formatInt = (value) => value == null
  ? "нет данных"
  : new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(value);

export const formatPercent = (value) => value == null
  ? "нет данных"
  : `${value > 0 ? "+" : ""}${new Intl.NumberFormat("ru-RU", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value)}%`;

export const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#39;");
```

- [ ] **Step 5: Add shared fixed-canvas HTML and SVG primitives**

`baseDocument()` must create a complete HTML document with:

```css
html, body { margin: 0; width: 1600px; min-width: 1600px; background: #eef2ef; }
.infographic { width: 1600px; height: 5000px; overflow: hidden; position: relative; }
svg { display: block; overflow: visible; }
* { box-sizing: border-box; }
```

It must also include:

```html
<meta name="viewport" content="width=1600, initial-scale=1">
<meta name="source-sha256" content="${sourceHash}">
<main class="infographic ${themeClass}" data-source-sha256="${sourceHash}">${body}</main>
```

- [ ] **Step 6: Add output-contract tests**

```python
@pytest.mark.parametrize("name", [
    "01-analytical-report",
    "02-war-room",
    "03-growth-funnel",
])
def test_generated_html_contract(name):
    html = (OUTPUT / f"{name}.html").read_text(encoding="utf-8")
    assert 'width: 1600px' in html
    assert 'height: 5000px' in html
    assert 'data-source-sha256=' in html
    assert "2026-07-12" in html
    assert "нет подтверждённой сопоставимой метрики" in html
```

- [ ] **Step 7: Check the scoped diff**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only authorized infographic/test/plan files added. Do not stage or commit.

---

### Task 2: Analytical Report Template

**Files:**
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/analytical.mjs`

**Interfaces:**
- Consumes: `renderAnalytical(data, sourceHash)` arguments and helpers from `common.mjs`.
- Produces: `renderAnalytical(data, sourceHash): string` — complete HTML.

- [ ] **Step 1: Add the analytical content test**

```python
def test_analytical_required_content():
    html = (OUTPUT / "01-analytical-report.html").read_text(encoding="utf-8")
    for value in ["386 200", "+15,3%", "+94,0%", "+199,7%", "−2 940"]:
        assert value in html
    assert "proxy/repost anomaly" in html
    assert "аналитическая шкала 0–5" in html
    assert "POKROV против рынка" in html
```

- [ ] **Step 2: Build the exact analytical section stack**

`renderAnalytical()` must render these vertically bounded regions:

```javascript
const sections = [
  [0, 620, "hero and methodology"],
  [620, 1420, "absolute growth leaderboard"],
  [1420, 2220, "scale versus growth with outlier inset"],
  [2220, 2920, "cadence coexisting with growth or decline"],
  [2920, 3600, "marketing pressure ladder"],
  [3600, 4440, "POKROV versus market matrix"],
  [4440, 5000, "decisions and source footer"],
];
```

The DOM must carry matching `data-section` attributes so tests can verify every block exists.

- [ ] **Step 3: Implement the growth leaderboard**

Use the top 11 channels sorted by `growth_30d`. Bars scale to HitVPN `386200`. Luma is tagged `АНОМАЛИЯ`, and the declining tail shows MORI, NashVPN, GenVPN and 4ebur as signed values.

```javascript
const leaders = [...data.channels]
  .filter((row) => row.growth_30d > 0)
  .sort((a, b) => b.growth_30d - a.growth_30d)
  .slice(0, 11);
```

- [ ] **Step 4: Implement scale-versus-growth without compressed ordinary values**

The main plot includes only rows where `growth_30d_percent <= 16` and excludes Luma/Cats. Plot x on a log scale using channel subscribers and y on `−4…16`. Render Cats and Luma as separate outlier cards with their evidence labels.

```javascript
const ordinary = data.channels.filter((row) =>
  row.id !== "cats-vpn" &&
  row.id !== "luma-vpn" &&
  row.growth_30d_percent != null &&
  row.growth_30d_percent <= 16
);
```

- [ ] **Step 5: Implement qualitative POKROV matrix**

Rows: entry, trial, Telegram dependency, platform breadth, store reach, recovery, routing depth, trust, social proof and growth engine. Values are text-only `сильнее`, `слабее`, `смешанно`, `не доказано`; no numeric score.

- [ ] **Step 6: Render once and inspect at full resolution**

Run the build command from Task 5, then open `01-analytical-report.png` with the local image viewer. Expected: no clipping at section boundaries and no overlapped plot labels.

- [ ] **Step 7: Check the scoped diff**

Run `git diff --check`; do not stage or commit.

---

### Task 3: War Room Template

**Files:**
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/war-room.mjs`

**Interfaces:**
- Consumes: `renderWarRoom(data, sourceHash)` arguments and helpers from `common.mjs`.
- Produces: `renderWarRoom(data, sourceHash): string` — complete HTML.

- [ ] **Step 1: Add the war-room content test**

```python
def test_war_room_required_content():
    html = (OUTPUT / "02-war-room.html").read_text(encoding="utf-8")
    for label in ["HitVPN", "Atlanta", "Batya", "Kubik", "HiroVPN", "MantaRay"]:
        assert label in html
    assert "5,0" in html
    assert "debug signing" in html.lower()
    assert "окно атаки" in html.lower()
```

- [ ] **Step 2: Build the exact war-room section stack**

```javascript
const sections = [
  [0, 600, "hero and threat summary"],
  [600, 1380, "market threat classes"],
  [1380, 2200, "aggression leaderboard"],
  [2200, 3000, "observed attack mechanics"],
  [3000, 3660, "cadence coexisting with decline"],
  [3660, 4260, "app and release risks"],
  [4260, 4780, "POKROV moat and vulnerable flank"],
  [4780, 5000, "attack window and evidence footer"],
];
```

- [ ] **Step 3: Implement aggression ranking with explicit inference label**

Sort non-null scores descending. Sota/Lagom render in a separate `НЕТ ОЦЕНКИ` row. Every score area includes `аналитическая шкала 0–5` and `inflow_evidence_class` translated by `evidenceLabel()`.

- [ ] **Step 4: Implement observed mechanics, not causal claims**

Cards must say `наблюдалось одновременно с`, `видимый источник` or `аналитический вывод`; never `привело к оплате`, `удержало` or `конвертировало`.

- [ ] **Step 5: Implement product/release risk panel**

Populate only from `data.apps`: Quattro, HiroVPN, Kubik and MantaRay. Risks are copied verbatim from the JSON risk arrays. No vulnerability severity beyond the archived analyst read.

- [ ] **Step 6: Render and inspect at full resolution**

Expected: dark surface with readable off-white text, red/orange limited to risks, emerald limited to POKROV opportunity, no military decoration or tiny terminal text.

- [ ] **Step 7: Check the scoped diff**

Run `git diff --check`; do not stage or commit.

---

### Task 4: Growth Mechanism Template

**Files:**
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/src/growth-funnel.mjs`

**Interfaces:**
- Consumes: `renderGrowthFunnel(data, sourceHash)` arguments and helpers from `common.mjs`.
- Produces: `renderGrowthFunnel(data, sourceHash): string` — complete HTML.

- [ ] **Step 1: Add the growth-map content test**

```python
def test_growth_map_required_content():
    html = (OUTPUT / "03-growth-funnel.html").read_text(encoding="utf-8")
    assert "От внимания к продукту" in html
    assert "наблюдаемые и предполагаемые механики" in html
    assert "Telegram — необязательная ветка" in html
    assert "+10 дней" in html
    assert "не доказывает оплату" in html
```

- [ ] **Step 2: Build the exact mechanism-map section stack**

```javascript
const sections = [
  [0, 580, "hero and measurement warning"],
  [580, 1320, "market mechanism map"],
  [1320, 2320, "six inflow engines"],
  [2320, 3100, "three high-growth mechanism cases"],
  [3100, 3620, "three cadence-with-decline cases"],
  [3620, 4300, "POKROV main path and optional Telegram branch"],
  [4300, 4780, "priority build sequence"],
  [4780, 5000, "north-star principle and sources"],
];
```

- [ ] **Step 3: Implement the market mechanism map**

Render nodes for external source, Telegram gate/channel, bot trial/payment surface, app/client activation surface and lifecycle/referral surface. Use arrows only as route/mechanism connectors. Add a persistent note: `Рост канала не доказывает оплату, активацию или удержание`.

- [ ] **Step 4: Implement six inflow-engine blocks**

Each block receives one evidence class and concrete examples:

```javascript
const engines = [
  ["Призы", ["hitvpn", "batya-vpn"]],
  ["Creators / affiliate", ["atlanta-vpn"]],
  ["App / store", ["hitvpn", "sota-vpn", "lagom-vpn", "batya-vpn"]],
  ["Mandatory gate", ["cats-vpn", "nosok-vpn", "shuka-vpn", "atlanta-vpn"]],
  ["Proxy / utility", ["luma-vpn"]],
  ["Referral / reseller", ["platina-vpn", "durev-vpn", "shuka-vpn", "atlanta-vpn"]],
];
```

- [ ] **Step 5: Implement POKROV with a non-required Telegram branch**

The main horizontal path ends in paid key/renewal. The `+10 days` Telegram node branches vertically from cabinet/account and rejoins nowhere. Text must explicitly say `необязательная ветка`.

- [ ] **Step 6: Render and inspect at full resolution**

Expected: warm cream surface, connectors remain legible, no arrow suggests measured conversion, optional Telegram is visually off the main line.

- [ ] **Step 7: Check the scoped diff**

Run `git diff --check`; do not stage or commit.

---

### Task 5: Build, Browser Capture and Manifest

**Files:**
- Create: `docs/competitive/telegram-vpn-2026-07-12/infographics/build.mjs`
- Generate: all three HTML, all three PNG and `manifest.json`.

**Interfaces:**
- Consumes:
  - JSON source path.
  - optional `CHROME_EXECUTABLE_PATH` environment variable.
- Produces:
  - `buildAll(): Promise<Manifest>`
  - `renderPng(htmlPath, pngPath): Promise<void>`
  - manifest entries `{ html, png, width, height, sha256, source_sha256 }`.

- [ ] **Step 1: Add manifest and dimension tests**

```python
def test_manifest_and_png_dimensions():
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["outputs"]) == 3
    for item in manifest["outputs"]:
        image_path = OUTPUT / item["png"]
        with Image.open(image_path) as image:
            assert image.size == (1600, 5000)
        assert item["width"] == 1600
        assert item["height"] == 5000
        assert len(item["sha256"]) == 64
```

- [ ] **Step 2: Implement browser selection without downloads**

```javascript
const candidates = [
  process.env.CHROME_EXECUTABLE_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
].filter(Boolean);

const executablePath = candidates.find((candidate) => fsSync.existsSync(candidate));
if (!executablePath) throw new Error("No local Chrome/Edge executable found");
```

- [ ] **Step 3: Implement exact fixed-size browser capture**

Use `promisify(execFile)` and run the local browser directly:

```javascript
await execFileAsync(executablePath, [
  "--headless=new",
  "--disable-gpu",
  "--hide-scrollbars",
  "--force-device-scale-factor=1",
  "--window-size=1600,5000",
  `--screenshot=${pngPath}`,
  pathToFileURL(htmlPath).href,
], { timeout: 120000, windowsHide: true });
```

Do not download a browser. The independent Pillow test decides whether the CLI output is exactly `1600 × 5000`.

- [ ] **Step 4: Verify that Chrome wrote the requested file**

```javascript
const stat = await fs.stat(pngPath);
if (stat.size < 10000) throw new Error(`Suspicious PNG size: ${stat.size}`);
```

- [ ] **Step 5: Implement source/output hashing and manifest writing**

Use `crypto.createHash("sha256")`. Manifest top-level fields:

```json
{
  "generated_at": "ISO-8601",
  "source": "../archive/infographic-data.json",
  "source_sha256": "64 lowercase hex chars",
  "dimensions": { "width": 1600, "height": 5000 },
  "outputs": []
}
```

- [ ] **Step 6: Run the builder**

```powershell
& 'C:\Users\kiwun\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' 'docs\competitive\telegram-vpn-2026-07-12\infographics\build.mjs'
```

Expected: JSON summary reporting three HTML files, three `1600x5000` PNG files and a manifest.

- [ ] **Step 7: Run focused artifact tests**

```powershell
python.exe -B -m pytest -p no:cacheprovider tests/test_telegram_vpn_infographics.py -q
```

Expected: all infographic tests pass.

---

### Task 6: Visual QA, Reconciliation and Handoff

**Files:**
- Modify only if QA finds defects: the three template modules or shared CSS.
- Modify: `docs/competitive/telegram-vpn-2026-07-12/archive/README.md`
  - Add links to the final infographic directory and manifest.

**Interfaces:**
- Consumes: generated PNG/HTML/manifest.
- Produces: verified deliverables and compact handoff.

- [ ] **Step 1: Open all three PNG files at original resolution**

Check:

- text does not clip at `y=5000`;
- no section overlaps;
- all chart labels fit;
- Cats/Luma outliers are separate;
- missing values read `нет данных`;
- optional Telegram is visibly a side branch;
- POKROV has no invented growth value;
- war-room dark contrast remains readable.

- [ ] **Step 2: Reconcile displayed facts**

Programmatically scan generated HTML for the required values and forbidden claims:

```python
required = ["386 200", "+15,3%", "+94,0%", "+199,7%", "−2 940"]
for html_path in OUTPUT.glob("*.html"):
    text = html_path.read_text(encoding="utf-8")
    assert "платящих клиентов" not in text.lower()
    assert "конверсия" not in text.lower() or "не доказывает" in text.lower()
```

- [ ] **Step 3: Run repository documentation checks**

```powershell
python.exe -B -m pytest -p no:cacheprovider tests/test_agent_docs_contract.py tests/test_agent_context_packet_audit.py -q
python.exe -B scripts/agent_context_packet_audit.py --platform-context-root .
git diff --check
```

Expected: 25 documentation tests pass; platform-context audit PASS; no diff-check errors. A Windows pytest temp-cleanup warning may appear after the successful result and does not change the test status.

- [ ] **Step 4: Recheck scoped status and preserve concurrent work**

```powershell
git status --short --branch
git diff --stat
```

Expected: no staging, commit, push or deploy; unrelated `AGENTS.md`, `docs/README.md` and concurrent competitive research remain untouched.

- [ ] **Step 5: Update the archive entry point**

Add direct links for:

- `01-analytical-report.png`
- `02-war-room.png`
- `03-growth-funnel.png`
- `manifest.json`

- [ ] **Step 6: Final handoff**

Report:

- the three output links;
- exact dimensions and validation result;
- source dataset/manifest link;
- tests and audit results;
- explicit `not staged / not committed / not deployed` state.

---

## Self-Review

- Spec coverage: every design-spec section maps to Tasks 2–4; shared data and evidence rules map to Task 1; browser/dimension/hash requirements map to Task 5; QA and archive links map to Task 6.
- Placeholder scan: no `TBD`, `TODO`, “implement later”, generic error-handling instruction or undefined follow-up step remains.
- Type consistency: all three template functions consume `(data, sourceHash)` and return complete HTML strings; `build.mjs` owns file output and Chrome headless capture; tests read only generated artifacts.
- Scope: one project subsystem (`docs/competitive/.../infographics`) plus one test file and one archive-link update. No product code, account mutation or external publication.
- Git policy: commit steps are intentionally replaced with diff/status checks because the user did not request staging or commits.
