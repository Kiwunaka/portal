import {
  baseDocument,
  escapeHtml,
  evidenceLabel,
  formatInt,
  formatPercent,
  getAppScale,
  getMarketing,
  horizontalBars,
  sectionHeader,
  validateDataset,
} from "./common.mjs";

const section = (top, height, name, content) => `
<section class="report-section" data-section="${name}" style="top: ${top}px; height: ${height}px">
  ${content}
</section>`;

const signedInt = (value) => {
  const formatted = formatInt(value).replace(/^-/, "−");
  return value > 0 ? `+${formatted}` : formatted;
};

const tierRadius = (tier) => ({
  unknown: 7, "1k_plus": 8, "10k_plus": 9, "50k_plus": 10,
  "100k_plus": 11, "500k_plus": 13, "1m_plus": 14,
  "5m_plus": 17, "10m_plus": 19,
}[tier] ?? 7);

function scaleGrowthPlot(data) {
  const ordinary = data.channels.filter((row) =>
    row.id !== "cats-vpn" && row.id !== "luma-vpn"
    && row.growth_30d_percent != null && row.growth_30d_percent <= 16
  );
  const width = 900;
  const height = 480;
  const left = 68;
  const right = 32;
  const top = 28;
  const bottom = 48;
  const minLog = Math.log10(Math.min(...ordinary.map((row) => row.subscribers)));
  const maxLog = Math.log10(Math.max(...ordinary.map((row) => row.subscribers)));
  const x = (value) => left + ((Math.log10(value) - minLog) / (maxLog - minLog)) * (width - left - right);
  const y = (value) => top + ((16 - value) / 20) * (height - top - bottom);
  const offsets = {
    quattro: [18, 12, "start"], "nosok-vpn": [26, 34, "start"],
    "platina-vpn": [-44, 38, "end"], "mori-vpn": [119, 26, "start"],
    nashvpn: [16, 36, "start"], hitvpn: [-18, -17, "end"],
    "sota-vpn": [0, -18, "middle"], "lagom-vpn": [0, -22, "middle"],
    genvpn: [-18, 26, "end"], "atlanta-vpn": [-31, -17, "end"],
    "shuka-vpn": [10, 31, "start"], "groza-vpn": [0, 24, "middle"],
    "batya-vpn": [0, -19, "middle"], "durev-vpn": [0, -17, "middle"],
    "opengate-vpn": [0, -14, "middle"], blancvpn: [90, 11, "start"],
    net4ebur: [12, -13, "start"],
  };
  const yTicks = [-4, 0, 4, 8, 12, 16].map((tick) => `
    <g><line x1="${left}" y1="${y(tick)}" x2="${width - right}" y2="${y(tick)}" />
    <text x="${left - 14}" y="${y(tick) + 5}" text-anchor="end">${tick}%</text></g>`).join("");
  const xTicks = [10000, 100000, 1000000].filter((tick) => tick >= 10 ** minLog && tick <= 10 ** maxLog)
    .map((tick) => `
    <g><line x1="${x(tick)}" y1="${top}" x2="${x(tick)}" y2="${height - bottom}" />
    <text x="${x(tick)}" y="${height - 15}" text-anchor="middle">${tick >= 1000000 ? "1 млн" : `${tick / 1000} тыс.`}</text></g>`).join("");
  const points = ordinary.map((row) => {
    const tier = getAppScale(data, row.id)?.tier ?? "unknown";
    const growthLabel = formatPercent(row.growth_30d_percent);
    const [dx, dy, anchor] = offsets[row.id] ?? [12, -10, "start"];
    return `<g data-channel-id="${escapeHtml(row.id)}" data-app-tier="${tier}" data-growth-label="${escapeHtml(growthLabel)}" transform="translate(${x(row.subscribers)} ${y(row.growth_30d_percent)})">
      <title>${escapeHtml(row.name)} · ${escapeHtml(growthLabel)}</title><circle r="${tierRadius(tier)}" /><text x="${dx}" y="${dy}" text-anchor="${anchor}">${escapeHtml(row.name)}</text>
    </g>`;
  }).join("\n");
  return `<div class="plot" data-chart="scale-growth-main" data-y-min="-4" data-y-max="16">
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Масштаб канала и рост за 30 дней">
      <g class="grid">${yTicks}${xTicks}</g><line class="zero" x1="${left}" y1="${y(0)}" x2="${width - right}" y2="${y(0)}" />${points}
    </svg>
  </div>`;
}

function renderMatrix() {
  const rows = [
    ["Вход", "сильнее", "app-first, без обязательного gate"],
    ["Пробный период", "сильнее", "5 дней premium без карты"],
    ["Зависимость от Telegram", "сильнее", "Telegram — усилитель, не входной барьер"],
    ["Ширина платформ", "слабее", "Android + Windows; рынок местами шире"],
    ["Охват магазинов", "слабее", "outside-store beta"],
    ["Восстановление", "смешанно", "app → web cabinet → Telegram; публичная сопоставимость неполная"],
    ["Глубина маршрутизации", "слабее", "уступает MantaRay"],
    ["Доверие", "сильнее", "без fake counters, prize spam и third-party ads"],
    ["Социальное доказательство", "слабее", "меньше публичного масштаба"],
    ["Двигатель роста", "не доказано", "нет подтверждённой сопоставимой метрики"],
  ];
  return `<div class="matrix"><div class="matrix-head"><span>Критерий</span><span>POKROV</span><span>Основание</span></div>${rows.map(([name, value, note]) => `
    <div class="matrix-row" data-assessment="${value}"><strong>${name}</strong><b>${value}</b><span>${note}</span></div>`).join("")}</div>`;
}

export function renderAnalytical(data, sourceHash) {
  validateDataset(data);
  const leaders = [...data.channels].filter((row) => row.growth_30d > 0)
    .sort((a, b) => b.growth_30d - a.growth_30d).slice(0, 11);
  const decliners = [...data.channels].filter((row) => row.growth_30d < 0)
    .sort((a, b) => a.growth_30d - b.growth_30d);
  const leaderboard = horizontalBars(leaders.map((row) => ({
    label: row.id === "luma-vpn" ? `${row.name} · АНОМАЛИЯ` : row.name,
    value: row.growth_30d,
    displayValue: formatInt(row.growth_30d),
    color: row.id === "hitvpn" ? "#147A4B" : row.id === "luma-vpn" ? "#D88914" : "#66ad84",
  })), { width: 980, rowHeight: 48, labelWidth: 320, valueWidth: 135, maxValue: 386200, title: "Абсолютный прирост за 30 дней" });
  const cadence = [...data.channels].filter((row) => row.posts_30d != null || row.posts_60d != null)
    .sort((a, b) => ((b.posts_30d ?? b.posts_60d / 2) - (a.posts_30d ?? a.posts_60d / 2))).slice(0, 10);
  const marketing = [...data.marketing_analysis].filter((row) => row.score != null)
    .sort((a, b) => b.score - a.score).slice(0, 12);
  const noScore = data.marketing_analysis.filter((row) => row.score == null);
  const cats = data.channels.find((row) => row.id === "cats-vpn");
  const luma = data.channels.find((row) => row.id === "luma-vpn");
  const hitvpn = data.channels.find((row) => row.id === "hitvpn");
  const sota = data.channels.find((row) => row.id === "sota-vpn");
  const positiveCount = data.channels.filter((row) => row.growth_30d > 0).length;
  const decliningCount = data.channels.filter((row) => row.growth_30d < 0).length;
  const postWindow = `${data.snapshot.post_window_start} — ${data.snapshot.post_window_end}`;
  const ownershipNotes = data.android_footprint_scale.entries
    .filter((row) => row.ownership_state.includes("not proven"))
    .map((row) => `<span class="ownership-note" data-ownership-id="${escapeHtml(row.id)}">${escapeHtml(row.ownership_state)}</span>`)
    .join("");
  const body = `<style>
    .analytical { background:#edf2ee; --ink:#14221b; --green:#147A4B; --amber:#D88914; --risk:#D24A3A; --body-size:28px; --note-size:22px; --label-size:24px; }
    .report-section { position:absolute; left:0; width:1600px; padding:36px 96px; overflow:hidden; border-bottom:1px solid #c9d5cd; }
    .report-section[data-section="hero and methodology"] { padding-top:88px; }
    .report-section[data-section="decisions and source footer"] { padding-bottom:88px; }
    .report-section:nth-of-type(even) { background:#f8faf7; } .hero-shell { display:grid; gap:22px; }
    .hero { display:grid; grid-template-columns:1.55fr .85fr; gap:40px; align-items:start; }
    .eyebrow { font-size:var(--label-size); font-weight:800; letter-spacing:.08em; color:var(--green); } h1 { margin:12px 0 18px; font-size:64px; line-height:1.02; letter-spacing:-.035em; }
    .lead { margin:0; font-size:var(--body-size); line-height:1.34; } .method { padding:20px 24px; border-radius:22px; background:#14221b; color:white; font-size:var(--note-size); line-height:1.35; }
    .method b { color:#83d4a7; } .method p { margin:0 0 10px; } .method p:last-child { margin-bottom:0; }
    .kpi-strip { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; } .kpi-card { min-height:128px; padding:14px 18px; border-radius:18px; background:white; border-top:5px solid var(--green); }
    .kpi-card span { display:block; color:#5e6d65; font-size:var(--note-size); } .kpi-card strong { display:block; margin-top:6px; font-size:30px; line-height:1.08; }
    .section-header { margin-bottom:16px; } .section-header__kicker { color:var(--green); font-size:var(--label-size); } .section-header__title { font-size:44px; }
    .section-header__note { font-size:var(--note-size); margin-top:10px; line-height:1.3; }
    .leader-grid { display:grid; grid-template-columns:1000px 1fr; gap:28px; } .horizontal-bars text { font-size:var(--label-size); fill:var(--ink); } .horizontal-bars__value { font-weight:800; }
    .decline { padding:20px; border-radius:22px; background:#fff0e8; } .decline h3 { margin:0 0 12px; font-size:30px; }
    .decline-row { display:flex; justify-content:space-between; padding:12px 0; border-top:1px solid #e7c7b7; font-size:var(--label-size); } .decline-row b { color:var(--risk); } .decline p { font-size:var(--note-size); line-height:1.3; }
    .tier-legend { margin:-4px 0 8px; font-size:var(--label-size); line-height:1.2; color:#5d6c64; }
    .ownership-notes { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin:0 0 10px; } .ownership-note { padding:8px 12px; border-left:4px solid #8b948f; background:#e1e7e3; font-size:var(--note-size); line-height:1.25; }
    .scale-grid { display:grid; grid-template-columns:1fr 230px 230px; gap:18px; } .plot { height:480px; border:1px solid #becdc4; border-radius:22px; background:white; padding:8px; }
    .plot svg { width:100%; height:460px; overflow:hidden; } .grid line { stroke:#dae3dd; } .grid text { font-size:var(--label-size); fill:#63736a; } .zero { stroke:#82968a; stroke-width:2; }
    .plot circle { fill:var(--green); stroke:white; stroke-width:2; } .plot g[data-app-tier="unknown"] circle { fill:none; stroke:#8b948f; stroke-width:3; } .plot g>text { font-size:var(--label-size); font-weight:700; fill:#203229; }
    .outlier { height:480px; padding:18px; border-radius:22px; background:#17261e; color:white; } .scale-grid>.outlier { background:var(--amber); color:var(--ink); } .scale-grid>.outlier small { color:var(--ink); }
    .outlier-tag { color:#ffd19f; font-size:var(--label-size); font-weight:800; letter-spacing:.05em; } .outlier strong { display:block; margin:10px 0 6px; font-size:32px; line-height:1.05; } .outlier>span { font-size:var(--label-size); } .outlier small { display:block; margin-top:10px; font-size:var(--note-size); line-height:1.25; color:#d5ded8; }
    .cadence-table { display:grid; grid-template-columns:repeat(2,1fr); gap:10px 24px; } .cadence-row { display:grid; grid-template-columns:1.2fr .8fr .8fr; padding:12px 18px; border-radius:14px; background:white; font-size:var(--label-size); }
    .cadence-row b:last-child { text-align:right; color:var(--green); } .cadence-row.negative b:last-child { color:var(--risk); }
    .pressure { display:grid; grid-template-columns:repeat(4,1fr); gap:8px 10px; } .pressure-card { min-height:86px; padding:10px 14px; border-radius:14px; background:white; border-left:5px solid #66ad84; }
    .pressure-card b { display:flex; justify-content:space-between; gap:8px; font-size:var(--label-size); } .pressure-card small { display:block; margin-top:6px; color:#66756d; font-size:var(--note-size); } .pressure-note { margin:10px 0 0; font-size:var(--note-size); }
    .no-score { display:flex; gap:18px; align-items:center; margin-top:8px; padding:9px 14px; border-radius:12px; background:#e2e9e4; font-size:var(--note-size); } .no-score b { color:#536159; }
    .matrix { border-radius:20px; overflow:hidden; background:white; } .matrix-head,.matrix-row { display:grid; grid-template-columns:1.25fr .55fr 1.8fr; align-items:center; }
    .matrix-head { min-height:52px; padding:10px 20px; background:#17261e; color:white; font-size:var(--label-size); font-weight:800; } .matrix-row { min-height:62px; padding:8px 20px; border-bottom:1px solid #dce5df; font-size:var(--body-size); line-height:1.16; }
    .matrix-row b { color:var(--green); } .matrix-row[data-assessment="слабее"] b { color:var(--risk); } .matrix-row[data-assessment="смешанно"] b { color:#9a6400; } .matrix-row[data-assessment="не доказано"] b { color:#6d7470; }
    .decisions { display:grid; grid-template-columns:1.8fr 1fr; gap:30px; } .decision-columns { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }
    .decision-panel { padding:14px 18px; border-radius:18px; background:white; } .decision-panel h3 { margin:0 0 6px; font-size:30px; } .decision-panel ul { margin:0; padding-left:26px; } .decision-panel li { margin:3px 0; font-size:var(--body-size); line-height:1.15; }
    .decision-panel--avoid { background:#fff0e8; } .source { padding:20px; border-radius:18px; background:#17261e; color:white; font-size:var(--note-size); line-height:1.35; } .source code { color:#99d6b3; }
  </style>
  ${section(0, 700, "hero and methodology", `<div class="hero-shell"><div class="hero"><div><div class="eyebrow">TELEGRAM VPN · СРЕЗ ${escapeHtml(data.snapshot.captured_date)} · ПОСТЫ ${escapeHtml(postWindow)}</div><h1>Telegram VPN 2026: рост, дистрибуция, продукт</h1><p class="lead">Кто растёт, за счёт чего и где POKROV может выиграть без forced gate и призового спама</p></div><aside class="method"><p><b>ФАКТ:</b> subscribers, net growth, reach, cadence и public Android tiers.</p><p><b>ВЫВОД:</b> inflow evidence и аналитическая шкала 0–5 не измеряют продажи.</p><p><b>ОГРАНИЧЕНИЕ:</b> рост канала не доказывает оплату, удержание или VPN MAU.</p></aside></div><div class="kpi-strip"><article class="kpi-card" data-kpi="hitvpn-absolute-growth"><span>HitVPN · max absolute</span><strong>${escapeHtml(signedInt(hitvpn.growth_30d))}</strong></article><article class="kpi-card" data-kpi="sota-relative-growth"><span>Sota · fastest ordinary app-backed</span><strong>${escapeHtml(formatPercent(sota.growth_30d_percent))}</strong></article><article class="kpi-card" data-kpi="positive-declining"><span>19 каналов</span><strong>${positiveCount} / ${decliningCount}</strong><span>positive / declining</span></article><article class="kpi-card" data-kpi="pokrov-public-growth"><span>POKROV · public growth</span><strong>нет подтверждённой метрики</strong></article></div></div>`)}
  ${section(700, 780, "absolute growth leaderboard", `${sectionHeader("01 · АБСОЛЮТНЫЙ РОСТ", "Кто прибавил больше всего", "Топ-11 по growth_30d; длина bars нормирована к HitVPN = 386 200.")}<div class="leader-grid"><div>${leaderboard}</div><aside class="decline"><h3>Отрицательный хвост</h3>${decliners.map((row) => `<div class="decline-row"><span>${escapeHtml(row.name)}</span><b>${escapeHtml(signedInt(row.growth_30d))}</b></div>`).join("")}<p><b>ВЫВОД:</b> публикации у MORI, NashVPN, GenVPN и 4ebur сосуществовали со спадом; это не доказывает причинность.</p></aside></div>`)}
  ${section(1480, 850, "scale versus growth with outlier inset", `${sectionHeader("02 · МАСШТАБ × ТЕМП", "Обычный рынок без сжатия", "X — subscribers (log); Y — −4…16%. Маркер — только public Android tier.")}<div class="tier-legend">app tiers: hollow unknown · 1K+ · 10K+ · 50K+ · 100K+ · 500K+ · 1M+ · 5M+ · 10M+</div><div class="ownership-notes" data-ownership-notes="app-footprint">${ownershipNotes}</div><div class="scale-grid">${scaleGrowthPlot(data)}<div data-chart="scale-growth-outliers"><article class="outlier"><span class="outlier-tag">OUTLIER · GATE</span><strong>${escapeHtml(cats.name)} ${escapeHtml(formatPercent(cats.growth_30d_percent))}</strong><span>gate/cross-promo</span><small>${escapeHtml(evidenceLabel(getMarketing(data, cats.id).inflow_evidence_class))}; вне основной шкалы.</small></article></div><article class="outlier"><span class="outlier-tag">АНОМАЛИЯ</span><strong>${escapeHtml(luma.name)} ${escapeHtml(formatPercent(luma.growth_30d_percent))}</strong><span>proxy/repost anomaly</span><small>${escapeHtml(evidenceLabel(getMarketing(data, luma.id).inflow_evidence_class))}; ERR/reach несопоставимы.</small></article></div>`)}
  ${section(2330, 560, "cadence coexisting with growth or decline", `${sectionHeader("03 · CADENCE", "Частота сосуществует и с ростом, и со спадом", "Публикации — наблюдаемый сигнал; корреляция не доказывает причинность.")}<div class="cadence-table">${cadence.map((row) => `<div class="cadence-row ${row.growth_30d < 0 ? "negative" : ""}"><strong>${escapeHtml(row.name)}</strong><span>${row.posts_30d ?? row.posts_60d} постов / ${row.posts_30d != null ? "30" : "60"}д</span><b>${escapeHtml(signedInt(row.growth_30d))}</b></div>`).join("")}</div>`)}
  ${section(2890, 650, "marketing pressure ladder", `${sectionHeader("04 · ДАВЛЕНИЕ", "От forced loops к product-led", "аналитическая шкала 0–5; качественная классификация, не измерение продаж.")}<div class="pressure">${marketing.map((row) => `<article class="pressure-card"><b><span>${escapeHtml(data.channels.find((channel) => channel.id === row.id).name)}</span><span>${row.score.toFixed(1)}</span></b><small>${escapeHtml(evidenceLabel(row.inflow_evidence_class))}</small></article>`).join("")}</div><div class="no-score"><b>Без score — неполная инспекция:</b>${noScore.map((row) => `<span>${escapeHtml(data.channels.find((channel) => channel.id === row.id).name)} · ${escapeHtml(evidenceLabel(row.inflow_evidence_class))}</span>`).join("")}</div><p class="pressure-note">Top-12 оценённых кейсов; остальные сохранены в source dataset.</p>`)}
  ${section(3540, 900, "POKROV versus market matrix", `${sectionHeader("05 · ПОЗИЦИЯ", "POKROV против рынка", "Качественная матрица; публичный рост POKROV не подменяется score.")}${renderMatrix()}`)}
  ${section(4440, 560, "decisions and source footer", `${sectionHeader("06 · РЕШЕНИЯ", "Копировать систему, не шум", "Усиливать дистрибуцию без forced gate и недоказуемых обещаний.")}<div class="decisions"><div class="decision-columns"><article class="decision-panel"><h3>КОПИРОВАТЬ</h3><ul><li>creators</li><li>simple referral</li><li>store + signing</li><li>status / roadmap</li><li>diagnostics</li></ul></article><article class="decision-panel decision-panel--avoid"><h3>НЕ КОПИРОВАТЬ</h3><ul><li>mandatory gate</li><li>prizes</li><li>incentivized reviews</li><li>ad-SDK overload</li><li>fake claims</li></ul></article></div><footer class="source"><b>ИСТОЧНИК:</b> infographic-data.json · <b>EVIDENCE / ADVISORY</b><br>Срез: ${escapeHtml(data.snapshot.captured_date)} · Посты: ${escapeHtml(postWindow)}<br>SHA-256: <code>${escapeHtml(sourceHash.slice(0, 16))}…</code><br>Канальные метрики не подтверждают paid users, revenue, churn или VPN MAU.</footer></div>`)} `;
  return baseDocument({ title: "POKROV — аналитический отчёт рынка Telegram VPN", themeClass: "analytical", body, sourceHash });
}
