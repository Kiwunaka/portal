import {
  baseDocument,
  escapeHtml,
  evidenceLabel,
  formatInt,
  getChannel,
  getMarketing,
  sectionHeader,
  validateDataset,
} from "./common.mjs";

const section = (top, height, name, content) => `
<section class="war-section" data-section="${name}" style="top: ${top}px; height: ${height}px">
  ${content}
</section>`;

const scoreLabel = (value) => new Intl.NumberFormat("ru-RU", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
}).format(value);

const signedInt = (value) => {
  const formatted = formatInt(value).replace(/^-/, "−");
  return value > 0 ? `+${formatted}` : formatted;
};

const list = (items) => `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;

export function renderWarRoom(data, sourceHash) {
  validateDataset(data);
  const postWindow = `${data.snapshot.post_window_start} — ${data.snapshot.post_window_end}`;
  const nameOf = (id) => getChannel(data, id).name;
  const evidenceOf = (id) => evidenceLabel(getMarketing(data, id)?.inflow_evidence_class);
  const scored = [...data.marketing_analysis]
    .filter((row) => row.score != null)
    .sort((a, b) => b.score - a.score);
  const noScore = data.marketing_analysis.filter((row) => row.score == null);
  const selectedApps = ["Quattro", "HiroVPN", "Kubik", "MantaRay"]
    .map((prefix) => data.apps.find((app) => app.name.startsWith(prefix)))
    .filter(Boolean);
  const cadenceIds = ["genvpn", "nashvpn", "mori-vpn", "blancvpn"];
  const moat = [0, 2, 1, 6, 7].map((index) => data.pokrov.strengths[index]);
  const flank = [0, 2, 3, 4, 6].map((index) => data.pokrov.weaknesses[index]);

  const scoreCards = scored.map((row) => `<article class="score-card" data-competitor-id="${escapeHtml(row.id)}">
    <div><strong>${escapeHtml(nameOf(row.id))}</strong><b>${escapeHtml(scoreLabel(row.score))}</b></div>
    <span>аналитическая шкала 0–5</span><span>${escapeHtml(evidenceLabel(row.inflow_evidence_class))}</span>
  </article>`).join("");
  const noScoreRow = `<div class="no-score-row"><b>НЕТ ОЦЕНКИ</b>${noScore.map((row) =>
    `<span data-no-score="${escapeHtml(row.id)}">${escapeHtml(nameOf(row.id))} · ${escapeHtml(evidenceLabel(row.inflow_evidence_class))}</span>`
  ).join("")}</div>`;

  const threatClasses = [
    ["SCALE + APP MOAT", "HitVPN · Sota · Lagom · Batya", "аналитический вывод: app-store footprint — видимый moat"],
    ["PRIZE MACHINE", "HitVPN · Batya", "видимый источник: повторяющиеся призовые циклы"],
    ["CREATOR / AFFILIATE", "Atlanta", "видимый источник: creators, bounty, referral и partner offer"],
    ["UTILITY / PROXY", "Luma · Cats VPN · Nosok VPN", "аналитический вывод по proxy, gate и utility-сигналам"],
  ];
  const threatCards = threatClasses.map(([title, names, note]) => `<article class="threat-card">
    <span>${title}</span><h3>${names}</h3><p>${note}</p>
  </article>`).join("");

  const mechanics = [
    ["hitvpn", "iPhone loop + требование подписки на канал и подключения бота"],
    ["atlanta-vpn", "creators + 50 RUB bounty + 30% referral + 50% partner offer"],
    ["batya-vpn", "непрерывные призы + review reward + fear sales"],
    ["luma-vpn", "proxy-to-paid funnel; связь источника и результата — аналитический вывод"],
    ["nosok-vpn", "placement reach 568765 + mandatory gate"],
  ].map(([id, text]) => `<article class="mechanic-card"><span>${escapeHtml(evidenceOf(id))}</span>
    <h3>${escapeHtml(nameOf(id))}</h3><p><b>Видимый источник:</b> ${escapeHtml(text)}.</p>
  </article>`).join("");

  const cadenceCards = cadenceIds.map((id) => {
    const channel = getChannel(data, id);
    const cadence = channel.posts_30d != null
      ? `${channel.posts_30d} постов / 30д`
      : `${channel.posts_60d} постов / 60д`;
    return `<article class="cadence-card" data-cadence-id="${escapeHtml(id)}"><div><strong>${escapeHtml(channel.name)}</strong><b>${escapeHtml(signedInt(channel.growth_30d))}</b></div>
      <p>${escapeHtml(cadence)}; это наблюдалось одновременно с ${channel.growth_30d < 0 ? "отрицательной" : "положительной"} 30-дневной динамикой.</p>
      <span>${escapeHtml(evidenceOf(id))} · Аналитический вывод: сосуществование сигналов не доказывает причинность.</span></article>`;
  }).join("");

  const riskCards = selectedApps.map((app) => `<article class="risk-card" data-app-card="${escapeHtml(app.package)}">
    <h3>${escapeHtml(app.name)}</h3>${list(app.risks)}
  </article>`).join("");

  const priorities = [
    ["creator attribution", "creator engine with measurable attribution"],
    ["two-sided referral", "simple two-sided referral"],
    ["store + signing", "store/signing and release provenance"],
    ["status / roadmap", "public status/roadmap"],
    ["recovery without Telegram", "recovery without Telegram"],
  ];

  const body = `<style>
    .war-room { background:#111820; --paper:#f2eee6; --muted:#aeb9bc; --line:#344149; --amber:#D88914; --risk:#D24A3A; --opportunity:#147A4B; --opportunity-text:#72d3a7; --body-size:28px; --note-size:22px; --label-size:24px; color:var(--paper); }
    .war-section { position:absolute; left:0; width:1600px; padding:24px 96px; overflow:hidden; border-bottom:1px solid var(--line); }
    .war-section[data-section="hero and threat summary"] { padding-top:88px; }
    .war-section[data-section="aggression leaderboard"] { padding-top:16px; padding-bottom:16px; }
    .war-section[data-section="POKROV moat and vulnerable flank"] { padding-top:12px; padding-bottom:12px; }
    .war-section[data-section="POKROV moat and vulnerable flank"] .section-header { margin-bottom:10px; }
    .war-section[data-section="attack window and evidence footer"] { padding-top:0; padding-bottom:88px; }
    .war-section:nth-of-type(even) { background:#151e26; } .section-header { margin-bottom:18px; }
    .section-header__kicker { color:var(--amber); font-size:var(--label-size); } .section-header__title { font-size:42px; }
    .section-header__note { color:var(--muted); font-size:var(--note-size); margin-top:7px; }
    .hero-grid { display:grid; grid-template-columns:1.45fr .8fr; gap:68px; align-items:end; height:100%; padding-bottom:38px; }
    .eyebrow { color:var(--amber); font-size:var(--label-size); font-weight:800; letter-spacing:.13em; } h1 { margin:18px 0 24px; font-size:78px; line-height:.95; letter-spacing:-.045em; }
    .hero-copy { margin:0; max-width:900px; color:#d8dfe0; font-size:var(--body-size); line-height:1.4; } .threat-summary { padding:28px; border:1px solid var(--line); border-radius:22px; background:#0c1217; }
    .threat-summary b { display:block; color:var(--amber); font-size:var(--label-size); } .threat-summary strong { display:block; margin:12px 0; font-size:44px; } .threat-summary p { margin:0; color:var(--muted); font-size:var(--body-size); line-height:1.38; }
    .threat-grid,.mechanics-grid,.risk-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:18px; }
    .threat-card { min-height:280px; padding:24px; border:1px solid var(--line); border-radius:18px; background:#0e151b; }
    .threat-card span { color:var(--amber); font-size:var(--label-size); font-weight:800; letter-spacing:.08em; } .threat-card h3 { margin:28px 0 16px; font-size:32px; line-height:1.15; }
    .threat-card p,.mechanic-card p { color:var(--muted); font-size:var(--body-size); line-height:1.36; }
    .score-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:7px 12px; }
    .score-card { min-height:102px; padding:8px 12px; border:1px solid var(--line); border-radius:12px; background:#0d141a; }
    .score-card div { display:flex; justify-content:space-between; font-size:var(--body-size); } .score-card b { color:var(--paper); font-size:30px; }
    .score-card span { display:block; margin-top:2px; color:var(--muted); font-size:var(--label-size); line-height:1.08; }
    .no-score-row { display:flex; gap:22px; align-items:center; margin-top:9px; padding:8px 14px; border:1px solid var(--line); font-size:var(--label-size); }
    .no-score-row b { color:var(--amber); } .mechanics-grid { grid-template-columns:repeat(5,1fr); gap:14px; }
    .mechanic-card { min-height:345px; padding:18px; border:1px solid var(--line); border-radius:18px; }
    .mechanic-card>span { color:var(--amber); font-size:var(--label-size); } .mechanic-card h3 { margin:12px 0 18px; font-size:32px; }
    .mechanic-card p { margin:0; } .mechanic-card p b { color:var(--paper); }
    .cadence-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
    .cadence-card { min-height:390px; padding:18px; border:1px solid var(--line); border-radius:16px; }
    .cadence-card div { display:flex; justify-content:space-between; gap:8px; font-size:var(--body-size); } .cadence-card p { margin:16px 0 12px; color:#d1d9da; font-size:var(--body-size); line-height:1.35; }
    .cadence-card span { color:var(--muted); font-size:var(--label-size); line-height:1.3; } .risk-card { min-height:370px; padding:18px; border-top:4px solid var(--risk); border-radius:14px; background:#0c1318; }
    .risk-card h3 { margin:0 0 16px; color:var(--risk); font-size:30px; } ul { margin:0; padding-left:26px; }
    li { margin:0 0 8px; font-size:var(--body-size); line-height:1.25; } .risk-card li::marker { color:var(--risk); }
    .position-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:22px; } .position-card { min-height:315px; padding:14px 20px; border:1px solid var(--line); border-radius:18px; }
    .position-card h3 { margin:0 0 12px; font-size:30px; } .position-card[data-pokrov-side="moat"] { border-color:var(--opportunity); }
    .position-card[data-pokrov-side="moat"] h3,.position-card[data-pokrov-side="moat"] li::marker { color:var(--opportunity); }
    .footer-grid { display:grid; grid-template-columns:1.8fr 1fr; gap:24px; align-items:start; } .attack-window { display:grid; grid-template-columns:repeat(5,1fr); gap:6px; }
    .attack-label { display:block; margin-bottom:6px; color:var(--opportunity-text); font-size:var(--body-size); } .priority { padding:4px 6px; border:1px solid var(--opportunity); border-radius:14px; color:#bcebd7; font-size:var(--label-size); line-height:1.1; }
    .source { color:var(--muted); font-size:var(--label-size); line-height:1.15; } .source code { color:var(--paper); word-break:break-all; }
  </style>
  ${section(0, 600, "hero and threat summary", `<div class="hero-grid"><div><div class="eyebrow">POKROV · WAR ROOM · ${escapeHtml(data.snapshot.captured_date)} · ПОСТЫ ${escapeHtml(postWindow)}</div><h1>Карта захвата внимания</h1><p class="hero-copy">Кто давит призами, кто покупает партнёров, кто вывозит продуктом. Канальные сигналы не доказывают оплату, удержание или VPN MAU.</p></div><aside class="threat-summary"><b>СИЛЬНЕЙШИЙ ВИДИМЫЙ СИГНАЛ</b><strong>HitVPN · 5,0</strong><p>аналитическая шкала 0–5 · ${escapeHtml(evidenceOf("hitvpn"))}. Все score — аналитический вывод, не коммерческая метрика.</p></aside></div>`)}
  ${section(600, 780, "market threat classes", `${sectionHeader("01 · КЛАССЫ ДАВЛЕНИЯ", "Четыре видимых контура", "Размещение основано на retained dataset; класс не доказывает источник оплаты или качество аудитории.")}<div class="threat-grid">${threatCards}</div>`)}
  ${section(1380, 820, "aggression leaderboard", `${sectionHeader("02 · AGGRESSION", "Лидерборд давления", "Все значения — аналитическая шкала 0–5; evidence class указывает основание, а не точность бизнес-эффекта.")}<div class="score-grid">${scoreCards}</div>${noScoreRow}`)}
  ${section(2200, 800, "observed attack mechanics", `${sectionHeader("03 · МЕХАНИКИ", "Наблюдаемые ходы", "Видимый источник и аналитический вывод разделены; причинность и продуктовая конверсия не измерены.")}<div class="mechanics-grid">${mechanics}</div>`)}
  ${section(3000, 660, "cadence coexisting with decline", `${sectionHeader("04 · CADENCE × ДИНАМИКА", "Давление сосуществует и со спадом", "GenVPN, NashVPN и MORI снижались; BlancVPN показывает низкое давление и продуктовую коммуникацию.")}<div class="cadence-grid">${cadenceCards}</div>`)}
  ${section(3660, 600, "app and release risks", `${sectionHeader("05 · RELEASE SURFACE", "Риски из retained JSON", "Только зафиксированные analyst-read формулировки; дополнительная severity не присваивается.")}<div class="risk-grid">${riskCards}</div>`)}
  ${section(4260, 520, "POKROV moat and vulnerable flank", `${sectionHeader("06 · POKROV", "Защитный moat и уязвимый flank", "Позиция описана продуктовым контрактом; публичный рост не подменяется score.")}<div class="position-grid"><article class="position-card" data-pokrov-side="moat"><h3>ЗАЩИТНЫЙ MOAT</h3>${list(moat)}</article><article class="position-card" data-pokrov-side="flank"><h3>УЯЗВИМЫЙ FLANK</h3>${list(flank)}</article></div>`)}
  ${section(4780, 220, "attack window and evidence footer", `<div class="footer-grid"><div><b class="attack-label">ОКНО АТАКИ</b><div class="attack-window">${priorities.map(([label, fullLabel]) => `<span class="priority" title="${escapeHtml(fullLabel)}">${escapeHtml(label)}</span>`).join("")}</div></div><footer class="source"><b>retained dataset</b> · ${escapeHtml(data.snapshot.status)} · ${escapeHtml(data.snapshot.captured_date)}<br>POKROV growth: нет подтверждённой сопоставимой метрики.<br>SHA-256: <code>${escapeHtml(sourceHash.slice(0, 16))}…</code></footer></div>`)} `;

  return baseDocument({ title: "POKROV — карта захвата внимания", themeClass: "war-room", body, sourceHash });
}
