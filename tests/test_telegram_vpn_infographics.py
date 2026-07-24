import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "docs"
    / "competitive"
    / "telegram-vpn-2026-07-12"
    / "archive"
    / "infographic-data.json"
)
OUTPUT = (
    ROOT
    / "docs"
    / "competitive"
    / "telegram-vpn-2026-07-12"
    / "infographics"
)
COMMON = OUTPUT / "src" / "common.mjs"
ANALYTICAL = COMMON.with_name("analytical.mjs")
BUILD = OUTPUT / "build.mjs"


def _run_common(script):
    bootstrap = """
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const common = await import(pathToFileURL(process.argv[1]).href);
const data = JSON.parse(await readFile(process.argv[2], "utf8"));
"""
    completed = subprocess.run(
        [
            "node.exe",
            "--input-type=module",
            "--eval",
            bootstrap + script,
            str(COMMON),
            str(DATA),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _render_analytical():
    bootstrap = """
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const analytical = await import(pathToFileURL(process.argv[1]).href);
const data = JSON.parse(await readFile(process.argv[2], "utf8"));
const html = analytical.renderAnalytical(data, "test-source-hash");
console.log(JSON.stringify(html));
"""
    completed = subprocess.run(
        [
            "node.exe",
            "--input-type=module",
            "--eval",
            bootstrap,
            str(ANALYTICAL),
            str(DATA),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_infographic_dataset_contract():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    assert len(data["channels"]) == 19
    assert len(data["marketing_analysis"]) == 19
    assert len(data["android_footprint_scale"]["entries"]) == 9
    assert max(row["growth_30d"] for row in data["channels"]) == 386_200
    assert sum(row["growth_30d"] > 0 for row in data["channels"]) == 15
    assert sum(row["growth_30d"] < 0 for row in data["channels"]) == 4
    assert all("inflow_evidence_class" in row for row in data["marketing_analysis"])


def test_common_validation_and_dataset_lookups():
    result = _run_common(
        """
const validationError = (mutate) => {
  const candidate = structuredClone(data);
  mutate(candidate);
  try {
    common.validateDataset(candidate);
    return null;
  } catch (error) {
    return error.message;
  }
};

common.validateDataset(data);
let missingChannel;
try {
  common.getChannel(data, "missing");
} catch (error) {
  missingChannel = error.message;
}

console.log(JSON.stringify({
  channel: common.getChannel(data, "cats-vpn").id,
  marketing: common.getMarketing(data, "cats-vpn").id,
  missingMarketing: common.getMarketing(data, "missing"),
  appTier: common.getAppScale(data, "hitvpn").tier,
  missingAppTier: common.getAppScale(data, "missing"),
  missingChannel,
  errors: {
    channels: validationError((candidate) => candidate.channels.pop()),
    marketing: validationError((candidate) => candidate.marketing_analysis.pop()),
    duplicate: validationError((candidate) => {
      candidate.channels[1].id = candidate.channels[0].id;
    }),
    orphan: validationError((candidate) => {
      candidate.marketing_analysis[0].id = "missing";
    }),
    evidence: validationError((candidate) => {
      candidate.marketing_analysis[0].inflow_evidence_class = "";
    }),
    outlier: validationError((candidate) => {
      candidate.channels.find((row) => row.id === "luma-vpn").growth_30d_percent = 200;
    }),
  },
}));
"""
    )

    assert result == {
        "channel": "cats-vpn",
        "marketing": "cats-vpn",
        "missingMarketing": None,
        "appTier": "10m_plus",
        "missingAppTier": None,
        "missingChannel": "Unknown channel id: missing",
        "errors": {
            "channels": "Expected exactly 19 channel records",
            "marketing": "Expected exactly 19 marketing records",
            "duplicate": "Duplicate channel id",
            "orphan": "Marketing record without matching channel",
            "evidence": "Missing inflow evidence class",
            "outlier": "Outlier values drifted",
        },
    }


def test_common_formatting_escaping_and_evidence_labels():
    result = _run_common(
        """
console.log(JSON.stringify({
  ints: [common.formatInt(386200), common.formatInt(-2940), common.formatInt(null)],
  percents: [
    common.formatPercent(15.3),
    common.formatPercent(-3.8),
    common.formatPercent(0),
    common.formatPercent(null),
  ],
  escaped: common.escapeHtml(`<tag a="one">Tom & 'Cat'</tag>`),
  evidence: [
    common.evidenceLabel("DIRECT_OR_PUBLIC_EVIDENCE"),
    common.evidenceLabel("MIXED_DIRECT_AND_INFERRED"),
    common.evidenceLabel("INFERENCE"),
    common.evidenceLabel("UNKNOWN"),
  ],
}));
"""
    )

    assert [value.replace("\xa0", " ") for value in result["ints"]] == [
        "386 200",
        "-2 940",
        "нет данных",
    ]
    assert result["percents"] == ["+15,3%", "-3,8%", "0,0%", "нет данных"]
    assert result["escaped"] == (
        "&lt;tag a=&quot;one&quot;&gt;Tom &amp; &#39;Cat&#39;&lt;/tag&gt;"
    )
    assert result["evidence"] == [
        "подтверждено",
        "смешанные данные",
        "вывод по сигналам",
        "нет данных",
    ]


def test_common_document_and_svg_primitives():
    result = _run_common(
        """
const document = common.baseDocument({
  title: "Отчёт <контроль>",
  themeClass: `light" onclick="alert(1)`,
  body: "<section>2026-07-12</section>",
  sourceHash: `abc"def`,
});
const bars = common.horizontalBars([
  { label: "Cats <VPN>", value: 10, displayValue: "+10" },
  { label: "Нет & данных", value: null },
], {
  width: 800,
  rowHeight: 80,
  labelWidth: 240,
  maxValue: 20,
  title: "Рост & риск",
});
const header = common.sectionHeader(
  "ФАКТ & ВЫВОД",
  "Рост <канала>",
  "Не доказывает оплату",
);

console.log(JSON.stringify({ document, bars, header }));
"""
    )

    document = result["document"]
    assert document.startswith("<!doctype html>")
    assert "<title>Отчёт &lt;контроль&gt;</title>" in document
    assert '<meta name="viewport" content="width=1600, initial-scale=1">' in document
    assert '<meta name="source-sha256" content="abc&quot;def">' in document
    assert "html, body { margin: 0; width: 1600px; min-width: 1600px;" in document
    assert ".infographic { width: 1600px; height: 5000px;" in document
    assert "svg { display: block; overflow: visible; }" in document
    assert "* { box-sizing: border-box; }" in document
    assert (
        '<main class="infographic light&quot; onclick=&quot;alert(1)" '
        'data-source-sha256="abc&quot;def"><section>2026-07-12</section></main>'
        in document
    )

    bars = result["bars"]
    assert bars.startswith('<svg class="horizontal-bars"')
    assert 'width="800"' in bars
    assert 'height="160"' in bars
    assert 'aria-label="Рост &amp; риск"' in bars
    assert "Cats &lt;VPN&gt;" in bars
    assert "Нет &amp; данных" in bars
    assert "+10" in bars
    assert "нет данных" in bars
    assert "NaN" not in bars

    header = result["header"]
    assert '<header class="section-header">' in header
    assert "ФАКТ &amp; ВЫВОД" in header
    assert "Рост &lt;канала&gt;" in header
    assert "Не доказывает оплату" in header


def test_analytical_renderer_contract():
    html = _render_analytical()
    normalized = html.replace("\xa0", " ")

    assert "width: 1600px" in html
    assert "height: 5000px" in html
    assert 'data-source-sha256="test-source-hash"' in html
    assert "Telegram VPN 2026: рост, дистрибуция, продукт" in html
    assert (
        "Кто растёт, за счёт чего и где POKROV может выиграть без forced gate "
        "и призового спама"
    ) in html
    assert "2026-05-12 — 2026-07-12" in html

    kpis = {
        "hitvpn-absolute-growth": "+386 200",
        "sota-relative-growth": "+15,3%",
        "positive-declining": "15 / 4",
        "pokrov-public-growth": "нет подтверждённой метрики",
    }
    for kpi_id, value in kpis.items():
        marker = f'data-kpi="{kpi_id}"'
        start = html.index(marker)
        card = html[start : html.index("</article>", start)]
        assert value in card.replace("\xa0", " ")

    sections = [
        (0, 700, "hero and methodology"),
        (700, 1480, "absolute growth leaderboard"),
        (1480, 2330, "scale versus growth with outlier inset"),
        (2330, 2890, "cadence coexisting with growth or decline"),
        (2890, 3540, "marketing pressure ladder"),
        (3540, 4440, "POKROV versus market matrix"),
        (4440, 5000, "decisions and source footer"),
    ]
    for start, end, name in sections:
        assert f'data-section="{name}"' in html
        assert f'top: {start}px; height: {end - start}px' in html

    for value in ["386 200", "+15,3%", "+94,0%", "+199,7%", "−2 940"]:
        assert value in normalized
    for value in ["MORI", "NashVPN", "GenVPN", "4ebur"]:
        assert value in html
    assert "АНОМАЛИЯ" in html
    assert "proxy/repost anomaly" in html
    assert "gate/cross-promo" in html

    assert 'data-chart="scale-growth-main"' in html
    assert 'data-y-min="-4"' in html
    assert 'data-y-max="16"' in html
    plot_start = html.index('data-chart="scale-growth-main"')
    plot_end = html.index('data-chart="scale-growth-outliers"')
    ordinary_plot = html[plot_start:plot_end]
    assert 'data-channel-id="cats-vpn"' not in ordinary_plot
    assert 'data-channel-id="luma-vpn"' not in ordinary_plot

    data = json.loads(DATA.read_text(encoding="utf-8"))
    source_tiers = {
        row["id"]: row["tier"]
        for row in data["android_footprint_scale"]["entries"]
    }
    for row in data["channels"]:
        if row["id"] in {"cats-vpn", "luma-vpn"}:
            continue
        if row["growth_30d_percent"] is None or row["growth_30d_percent"] > 16:
            continue
        expected_tier = source_tiers.get(row["id"], "unknown")
        assert (
            f'data-channel-id="{row["id"]}" data-app-tier="{expected_tier}"'
            in ordinary_plot
        )

    analytical_style_start = html.index(".analytical")
    analytical_style = html[
        analytical_style_start : html.index("</style>", analytical_style_start)
    ]
    assert "--body-size:28px" in analytical_style
    assert "--note-size:22px" in analytical_style
    assert "--label-size:24px" in analytical_style
    assert "padding:36px 96px" in analytical_style
    assert '--green:#147A4B' in analytical_style
    assert '--amber:#D88914' in analytical_style
    assert '--risk:#D24A3A' in analytical_style
    assert 'data-section="hero and methodology"] { padding-top:88px' in analytical_style
    assert 'data-section="decisions and source footer"] { padding-bottom:88px' in analytical_style
    assert ".horizontal-bars text { font-size:var(--label-size)" in analytical_style
    assert ".grid text { font-size:var(--label-size)" in analytical_style
    assert ".plot g>text { font-size:var(--label-size)" in analytical_style
    assert 'horizontal-bars__bar" x="320"' in html
    assert ".outlier { height:480px" in analytical_style
    assert "grid-template-columns:1.25fr .55fr 1.8fr" in analytical_style
    for tiny_size in range(10, 22):
        assert f"font-size:{tiny_size}px" not in analytical_style
        assert f"font-size: {tiny_size}px" not in analytical_style

    assert (
        '.plot g[data-app-tier="unknown"] circle { fill:none; '
        "stroke:#8b948f; stroke-width:3; }"
    ) in analytical_style
    assert 'data-ownership-notes="app-footprint"' in html
    ownership_notes = [
        row["ownership_state"]
        for row in data["android_footprint_scale"]["entries"]
        if "not proven" in row["ownership_state"]
    ]
    assert ownership_notes
    assert all(note in html for note in ownership_notes)
    assert "Shuka ownership not proven" in html

    assert "аналитическая шкала 0–5" in html
    assert "не доказывает причинность" in html
    assert "POKROV против рынка" in html
    assert "нет подтверждённой сопоставимой метрики" in html
    matrix_start = html.index('data-section="POKROV versus market matrix"')
    matrix_end = html.index(
        'data-section="decisions and source footer"', matrix_start
    )
    matrix = html[matrix_start:matrix_end]
    for row in [
        "Вход",
        "Пробный период",
        "Зависимость от Telegram",
        "Ширина платформ",
        "Охват магазинов",
        "Восстановление",
        "Глубина маршрутизации",
        "Доверие",
        "Социальное доказательство",
        "Двигатель роста",
    ]:
        assert row in matrix
    assert "numeric-score" not in matrix
    assert "маркетинговый балл" not in matrix.lower()
    assessments = ["сильнее", "слабее", "смешанно", "не доказано"]
    assert all(f'data-assessment="{value}"' in matrix for value in assessments)

    decision_start = html.index('data-section="decisions and source footer"')
    decision = html[decision_start:]
    for value in [
        "creators",
        "simple referral",
        "store + signing",
        "status / roadmap",
        "diagnostics",
        "mandatory gate",
        "prizes",
        "incentivized reviews",
        "ad-SDK overload",
        "fake claims",
    ]:
        assert value in decision


def test_infographic_archive_entry_point_is_current():
    archive_readme = DATA.with_name("README.md").read_text(encoding="utf-8")
    assert "источник будущей инфографики" not in archive_readme
    for name in [
        "01-analytical-report",
        "02-war-room",
        "03-growth-funnel",
    ]:
        assert f"../infographics/{name}.png" in archive_readme
        assert f"../infographics/{name}.html" in archive_readme
    assert "../infographics/manifest.json" in archive_readme


def test_manifest_source_path_tracks_custom_input():
    bootstrap = """
import { pathToFileURL } from "node:url";
const build = await import(pathToFileURL(process.argv[2]).href);
console.log(JSON.stringify({
  defaultSource: build.manifestSourcePath(process.argv[3]),
  customSource: build.manifestSourcePath(process.argv[4]),
}));
"""
    custom_source = ROOT / "custom-infographic-data.json"
    completed = subprocess.run(
        [
            "node.exe",
            "--input-type=module",
            "--eval",
            bootstrap,
            "manifest-helper",
            str(BUILD),
            str(DATA),
            str(custom_source),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result == {
        "defaultSource": "../archive/infographic-data.json",
        "customSource": Path(os.path.relpath(custom_source, OUTPUT)).as_posix(),
    }


@pytest.mark.parametrize(
    "name",
    [
        pytest.param(
            "01-analytical-report",
            marks=pytest.mark.skipif(
                not (OUTPUT / "01-analytical-report.html").is_file(),
                reason="analytical report has not been generated yet",
            ),
        ),
        pytest.param(
            "02-war-room",
            marks=pytest.mark.skipif(
                not (OUTPUT / "02-war-room.html").is_file(),
                reason="war-room report has not been generated yet",
            ),
        ),
        pytest.param(
            "03-growth-funnel",
            marks=pytest.mark.skipif(
                not (OUTPUT / "03-growth-funnel.html").is_file(),
                reason="growth-funnel report has not been generated yet",
            ),
        ),
    ],
)
def test_generated_html_contract(name):
    html = (OUTPUT / f"{name}.html").read_text(encoding="utf-8")
    assert "width: 1600px" in html
    assert "height: 5000px" in html
    assert "data-source-sha256=" in html
    assert "2026-07-12" in html
    assert "нет подтверждённой сопоставимой метрики" in html


def test_war_room_renderer_contract():
    war_room = COMMON.with_name("war-room.mjs")
    bootstrap = """
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const renderer = await import(pathToFileURL(process.argv[1]).href);
const data = JSON.parse(await readFile(process.argv[2], "utf8"));
const html = renderer.renderWarRoom(data, "test-source-hash");
console.log(JSON.stringify(html));
"""
    completed = subprocess.run(
        [
            "node.exe",
            "--input-type=module",
            "--eval",
            bootstrap,
            str(war_room),
            str(DATA),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0, completed.stderr
    html = json.loads(completed.stdout)

    assert "width: 1600px" in html
    assert "height: 5000px" in html
    assert 'data-source-sha256="test-source-hash"' in html
    assert "background:#111820" in html
    assert "--paper:#f2eee6" in html
    assert "2026-05-12 — 2026-07-12" in html

    sections = [
        (0, 600, "hero and threat summary"),
        (600, 1380, "market threat classes"),
        (1380, 2200, "aggression leaderboard"),
        (2200, 3000, "observed attack mechanics"),
        (3000, 3660, "cadence coexisting with decline"),
        (3660, 4260, "app and release risks"),
        (4260, 4780, "POKROV moat and vulnerable flank"),
        (4780, 5000, "attack window and evidence footer"),
    ]
    assert html.count('class="war-section"') == len(sections)
    for start, end, name in sections:
        assert f'data-section="{name}"' in html
        assert f'top: {start}px; height: {end - start}px' in html

    data = json.loads(DATA.read_text(encoding="utf-8"))
    channel_names = {row["id"]: row["name"] for row in data["channels"]}
    evidence_labels = {
        "DIRECT_OR_PUBLIC_EVIDENCE": "подтверждено",
        "MIXED_DIRECT_AND_INFERRED": "смешанные данные",
        "INFERENCE": "вывод по сигналам",
    }
    scored = sorted(
        (row for row in data["marketing_analysis"] if row["score"] is not None),
        key=lambda row: row["score"],
        reverse=True,
    )
    for row in scored:
        marker = f'data-competitor-id="{row["id"]}"'
        assert marker in html
        score_area = html[html.index(marker) : html.index("</article>", html.index(marker))]
        assert channel_names[row["id"]] in score_area
        assert f'{row["score"]:.1f}'.replace(".", ",") in score_area
        assert "аналитическая шкала 0–5" in score_area
        assert evidence_labels[row["inflow_evidence_class"]] in score_area

    assert 'data-no-score="sota-vpn"' in html
    assert 'data-no-score="lagom-vpn"' in html
    assert "НЕТ ОЦЕНКИ" in html
    no_score_area = html[html.index('class="no-score-row"') :]
    assert "аналитическая шкала 0–5" not in no_score_area.split("</div>", 1)[0]

    for name in ["HitVPN", "Atlanta", "Batya", "Kubik", "HiroVPN", "MantaRay"]:
        assert name in html
    for phrase in ["наблюдалось одновременно с", "видимый источник", "аналитический вывод"]:
        assert phrase in html.lower()
    for forbidden in [
        "привело к оплате",
        "удержало",
        "конвертировало",
        "критическая уязвимость",
        "высокая уязвимость",
        "conversion rate",
    ]:
        assert forbidden not in html.lower()

    selected_apps = [
        app
        for app in data["apps"]
        if any(app["name"].startswith(name) for name in ["Quattro", "HiroVPN", "Kubik", "MantaRay"])
    ]
    assert html.count("data-app-card=") == 4
    for app in selected_apps:
        for risk in app["risks"]:
            assert risk in html

    assert 'data-pokrov-side="moat"' in html
    assert 'data-pokrov-side="flank"' in html
    assert "app-first onboarding" in html
    assert "outside-store beta; Windows is unsigned" in html
    assert "ОКНО АТАКИ" in html
    assert "creator engine with measurable attribution" in html
    assert "recovery without Telegram" in html
    assert "--body-size:28px" in html
    assert "--note-size:22px" in html
    assert "--label-size:24px" in html
    war_style = html[html.index(".war-room") : html.index("</style>", html.index(".war-room"))]
    assert "padding:24px 96px" in war_style
    assert "--amber:#D88914" in war_style
    assert "--risk:#D24A3A" in war_style
    assert "--opportunity:#147A4B" in war_style
    assert 'data-section="hero and threat summary"] { padding-top:88px' in war_style
    assert 'data-section="attack window and evidence footer"] { padding-top:0; padding-bottom:88px' in war_style
    for tiny_size in range(10, 22):
        assert f"font-size:{tiny_size}px" not in war_style
        assert f"font-size: {tiny_size}px" not in war_style

    cadence_start = html.index('data-section="cadence coexisting with decline"')
    cadence_end = html.index('data-section="app and release risks"')
    cadence_section = html[cadence_start:cadence_end]
    for competitor_id in ["genvpn", "nashvpn", "mori-vpn", "blancvpn"]:
        marker = f'data-cadence-id="{competitor_id}"'
        assert marker in cadence_section
        card = cadence_section[
            cadence_section.index(marker) : cadence_section.index(
                "</article>", cadence_section.index(marker)
            )
        ]
        source_row = next(
            row for row in data["marketing_analysis"] if row["id"] == competitor_id
        )
        assert evidence_labels[source_row["inflow_evidence_class"]] in card
        assert "наблюдалось одновременно с" in card
        assert "не доказывает причинность" in card
        assert "и давление " not in card


def test_growth_funnel_renderer_contract():
    growth_funnel = COMMON.with_name("growth-funnel.mjs")
    bootstrap = """
import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const renderer = await import(pathToFileURL(process.argv[1]).href);
const data = JSON.parse(await readFile(process.argv[2], "utf8"));
const html = renderer.renderGrowthFunnel(data, "test-source-hash");
console.log(JSON.stringify(html));
"""
    completed = subprocess.run(
        [
            "node.exe",
            "--input-type=module",
            "--eval",
            bootstrap,
            str(growth_funnel),
            str(DATA),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0, completed.stderr
    html = json.loads(completed.stdout)
    normalized = html.replace("\xa0", " ")

    assert "width: 1600px" in html
    assert "height: 5000px" in html
    assert 'data-source-sha256="test-source-hash"' in html
    assert "background:#f5efe3" in html

    sections = [
        (0, 580, "hero and measurement warning"),
        (580, 1320, "market mechanism map"),
        (1320, 2320, "six inflow engines"),
        (2320, 3100, "three high-growth mechanism cases"),
        (3100, 3620, "three cadence-with-decline cases"),
        (3620, 4300, "POKROV main path and optional Telegram branch"),
        (4300, 4780, "priority build sequence"),
        (4780, 5000, "north-star principle and sources"),
    ]
    assert html.count('class="growth-section"') == len(sections)
    for start, end, name in sections:
        assert f'data-section="{name}"' in html
        assert f'top: {start}px; height: {end - start}px' in html

    assert "От внимания к продукту" in html
    assert "наблюдаемые и предполагаемые механики" in html
    for node in [
        "Внешний источник",
        "Telegram gate / канал",
        "Бот: trial / payment surface",
        "App / client: activation surface",
        "Lifecycle / referral surface",
    ]:
        assert node in html
    assert "Рост канала не доказывает оплату, активацию или удержание" in html
    assert "Маршруты показывают механику, а не измеренную конверсию" in html

    engines = {
        "prizes": ("Призы", ["hitvpn", "batya-vpn"]),
        "creators-affiliate": ("Creators / affiliate", ["atlanta-vpn"]),
        "app-store": (
            "App / store",
            ["hitvpn", "sota-vpn", "lagom-vpn", "batya-vpn"],
        ),
        "mandatory-gate": (
            "Mandatory gate",
            ["cats-vpn", "nosok-vpn", "shuka-vpn", "atlanta-vpn"],
        ),
        "proxy-utility": ("Proxy / utility", ["luma-vpn"]),
        "referral-reseller": (
            "Referral / reseller",
            ["platina-vpn", "durev-vpn", "shuka-vpn", "atlanta-vpn"],
        ),
    }
    assert html.count("data-inflow-engine=") == len(engines)
    for engine_id, (title, competitor_ids) in engines.items():
        marker = f'data-inflow-engine="{engine_id}"'
        start = html.index(marker)
        card = html[start : html.index("</article>", start)]
        assert title in card
        assert "data-evidence-label=" in card
        assert any(
            label in card
            for label in ["подтверждено", "смешанные данные", "вывод по сигналам"]
        )
        for competitor_id in competitor_ids:
            assert f'data-example-id="{competitor_id}"' in card
    for label in ["подтверждено", "смешанные данные", "вывод по сигналам"]:
        assert label in html
    mandatory_start = html.index('data-inflow-engine="mandatory-gate"')
    mandatory_card = html[mandatory_start : html.index("</article>", mandatory_start)]
    assert 'data-evidence-label="MIXED_DIRECT_AND_INFERRED"' in mandatory_card
    assert "смешанные данные" in mandatory_card

    high_growth_cases = {
        "hitvpn": "app scale ↔ giveaway ↔ bot / channel",
        "atlanta-vpn": "creator payout → gated bot → referral / partner economics",
        "cats-vpn": "anonymous login → gate → web continuity",
    }
    for competitor_id, mechanism in high_growth_cases.items():
        marker = f'data-growth-case="{competitor_id}"'
        start = html.index(marker)
        card = html[start : html.index("</article>", start)]
        assert mechanism in card
        assert "наблюдалось одновременно с" in card
        assert "не доказывает причинный цикл" in card
        assert "data-evidence-label=" in card

    for competitor_id in ["genvpn", "nashvpn", "mori-vpn"]:
        marker = f'data-cadence-decline="{competitor_id}"'
        start = html.index(marker)
        card = html[start : html.index("</article>", start)]
        assert "наблюдалось одновременно с отрицательной 30-дневной динамикой" in card
        assert "не доказывает причинность" in card
        assert "data-evidence-label=" in card
        assert "route-arrow" not in card
    for value in ["−301", "−996", "−2 940"]:
        assert value in normalized

    main_start = html.index('data-pokrov-path="main"')
    main_end = html.index("</div>", main_start)
    main_path = html[main_start:main_end]
    for step in [
        "Search / creator / content",
        "App",
        "5-day trial без карты",
        "Первое подключение",
        "Cabinet / support",
        "Paid key / renewal",
    ]:
        assert step in main_path
    optional_start = html.index('data-pokrov-path="optional-telegram"')
    optional_end = html.index("</aside>", optional_start)
    optional_path = html[optional_start:optional_end]
    assert optional_start > main_end
    assert 'data-branches-from="cabinet-account"' in optional_path
    assert 'data-rejoins="none"' in optional_path
    assert "Telegram — необязательная ветка" in optional_path
    assert "+10 дней" in optional_path
    assert "не возвращается в обязательный путь" in optional_path

    priorities = {
        "foundation": ["recovery", "diagnostics", "status", "signing"],
        "acquisition": ["creators", "referral", "SEO / platform landings"],
        "scale": ["stores", "app proof", "lifecycle governance"],
    }
    for priority_id, items in priorities.items():
        marker = f'data-priority="{priority_id}"'
        start = html.index(marker)
        card = html[start : html.index("</article>", start)]
        assert all(item in card for item in items)
    assert "стратегическая гипотеза" in html
    assert "нет подтверждённой сопоставимой метрики" in html
    assert "2026-07-12" in html
    assert "2026-05-12 — 2026-07-12" in html
    assert "--body-size:28px" in html
    assert "--note-size:22px" in html
    assert "--label-size:24px" in html
    growth_style_start = html.index(".growth-funnel")
    growth_style = html[
        growth_style_start : html.index("</style>", growth_style_start)
    ]
    assert "padding:28px 96px" in growth_style
    assert "--emerald:#147A4B" in growth_style
    assert "--amber:#D88914" in growth_style
    assert "--risk:#D24A3A" in growth_style
    assert 'data-section="hero and measurement warning"] { padding-top:88px' in growth_style
    assert 'data-section="north-star principle and sources"] { padding-top:10px; padding-bottom:88px' in growth_style
    for tiny_size in range(10, 22):
        assert f"font-size:{tiny_size}px" not in growth_style
        assert f"font-size: {tiny_size}px" not in growth_style

    for forbidden in [
        "привело к оплате",
        "удержало",
        "конвертировало",
        "conversion rate",
        "retention rate",
    ]:
        assert forbidden not in html.lower()


def test_manifest_and_png_dimensions():
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_names = [
        "01-analytical-report",
        "02-war-room",
        "03-growth-funnel",
    ]
    source_sha256 = hashlib.sha256(DATA.read_bytes()).hexdigest()

    assert manifest["source"] == "../archive/infographic-data.json"
    resolved_source = (manifest_path.parent / manifest["source"]).resolve()
    assert resolved_source == DATA.resolve()
    assert resolved_source.is_file()
    assert manifest["source_sha256"] == source_sha256
    assert manifest["dimensions"] == {"width": 1600, "height": 5000}
    assert [item["html"] for item in manifest["outputs"]] == [
        f"{name}.html" for name in expected_names
    ]
    assert [item["png"] for item in manifest["outputs"]] == [
        f"{name}.png" for name in expected_names
    ]

    for item in manifest["outputs"]:
        image_path = OUTPUT / item["png"]
        with Image.open(image_path) as image:
            assert image.size == (1600, 5000)
        assert item["width"] == 1600
        assert item["height"] == 5000
        assert item["source_sha256"] == source_sha256
        assert item["sha256"] == hashlib.sha256(image_path.read_bytes()).hexdigest()
