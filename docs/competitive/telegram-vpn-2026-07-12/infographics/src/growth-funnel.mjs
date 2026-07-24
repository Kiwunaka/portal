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
<section class="growth-section" data-section="${name}" style="top: ${top}px; height: ${height}px">
  ${content}
</section>`;

const signedInt = (value) => formatInt(value).replace(/^-/, "−");

export function renderGrowthFunnel(data, sourceHash) {
  validateDataset(data);
  const channel = (id) => getChannel(data, id);
  const evidence = (id) => evidenceLabel(getMarketing(data, id)?.inflow_evidence_class);
  const examples = (ids) => ids.map((id) =>
    `<span class="example" data-example-id="${escapeHtml(id)}">${escapeHtml(channel(id).name)}</span>`
  ).join("");

  const engines = [
    ["prizes", "Призы", ["hitvpn", "batya-vpn"], "MIXED_DIRECT_AND_INFERRED"],
    ["creators-affiliate", "Creators / affiliate", ["atlanta-vpn"], "DIRECT_OR_PUBLIC_EVIDENCE"],
    ["app-store", "App / store", ["hitvpn", "sota-vpn", "lagom-vpn", "batya-vpn"], "INFERENCE"],
    ["mandatory-gate", "Mandatory gate", ["cats-vpn", "nosok-vpn", "shuka-vpn", "atlanta-vpn"], "MIXED_DIRECT_AND_INFERRED"],
    ["proxy-utility", "Proxy / utility", ["luma-vpn"], "MIXED_DIRECT_AND_INFERRED"],
    ["referral-reseller", "Referral / reseller", ["platina-vpn", "durev-vpn", "shuka-vpn", "atlanta-vpn"], "MIXED_DIRECT_AND_INFERRED"],
  ].map(([id, title, ids, evidenceClass]) => `<article class="engine-card" data-inflow-engine="${id}">
    <span class="evidence" data-evidence-label="${escapeHtml(evidenceClass)}">${escapeHtml(evidenceLabel(evidenceClass))}</span>
    <h3>${escapeHtml(title)}</h3><div class="examples">${examples(ids)}</div>
  </article>`).join("");

  const highGrowth = [
    ["hitvpn", "app scale ↔ giveaway ↔ bot / channel"],
    ["atlanta-vpn", "creator payout → gated bot → referral / partner economics"],
    ["cats-vpn", "anonymous login → gate → web continuity"],
  ].map(([id, mechanism]) => `<article class="case-card" data-growth-case="${id}">
    <span class="evidence" data-evidence-label="${escapeHtml(getMarketing(data, id).inflow_evidence_class)}">${escapeHtml(evidence(id))}</span>
    <h3>${escapeHtml(channel(id).name)}</h3><strong>${escapeHtml(mechanism)}</strong>
    <p>Сочетание механик наблюдалось одновременно с ростом канала; аналитическая интерпретация не доказывает причинный цикл.</p>
  </article>`).join("");

  const cadence = ["genvpn", "nashvpn", "mori-vpn"].map((id) => {
    const row = channel(id);
    const cadenceText = row.posts_30d != null ? `${row.posts_30d} постов / 30 дней` : `${row.posts_60d} постов / 60 дней`;
    return `<article class="cadence-card" data-cadence-decline="${id}">
      <span class="evidence" data-evidence-label="${escapeHtml(getMarketing(data, id).inflow_evidence_class)}">${escapeHtml(evidence(id))}</span>
      <div><h3>${escapeHtml(row.name)}</h3><b>${escapeHtml(signedInt(row.growth_30d))}</b></div>
      <p>${escapeHtml(cadenceText)} наблюдалось одновременно с отрицательной 30-дневной динамикой; не доказывает причинность.</p>
    </article>`;
  }).join("");

  const marketNodes = [
    "Внешний источник",
    "Telegram gate / канал",
    "Бот: trial / payment surface",
    "App / client: activation surface",
    "Lifecycle / referral surface",
  ].map((label, index, nodes) => `<span class="flow-node">${escapeHtml(label)}</span>${
    index < nodes.length - 1 ? '<span class="route-arrow" aria-hidden="true">→</span>' : ""
  }`).join("");

  const mainSteps = [
    ["search", "Search / creator / content"],
    ["app", "App"],
    ["trial", "5-day trial без карты"],
    ["connection", "Первое подключение"],
    ["cabinet-account", "Cabinet / support"],
    ["paid-key", "Paid key / renewal"],
  ].map(([id, label], index, steps) => `<span class="pokrov-node" data-main-step="${id}">${escapeHtml(label)}</span>${
    index < steps.length - 1 ? '<span class="main-arrow" aria-hidden="true">→</span>' : ""
  }`).join("");

  const priorities = [
    ["foundation", "FOUNDATION", ["recovery", "diagnostics", "status", "signing"]],
    ["acquisition", "ACQUISITION", ["creators", "referral", "SEO / platform landings"]],
    ["scale", "SCALE", ["stores", "app proof", "lifecycle governance"]],
  ].map(([id, title, items], index) => `<article class="priority-card" data-priority="${id}">
    <span>0${index + 1}</span><h3>${title}</h3><p>${items.map(escapeHtml).join(" · ")}</p>
  </article>`).join("");

  const capturedDate = escapeHtml(data.snapshot.captured_date);
  const postWindow = `${escapeHtml(data.snapshot.post_window_start)} — ${escapeHtml(data.snapshot.post_window_end)}`;
  const body = `<style>
    .growth-funnel { background:#f5efe3; --ink:#251d2c; --muted:#6e6571; --line:#d8cbd6; --violet:#7044a8; --magenta:#bd3f79; --emerald:#147A4B; --amber:#D88914; --risk:#D24A3A; --paper:#fffaf1; --body-size:28px; --note-size:22px; --label-size:24px; color:var(--ink); }
    .growth-section { position:absolute; left:0; width:1600px; padding:28px 96px; overflow:hidden; border-bottom:1px solid var(--line); }
    .growth-section[data-section="hero and measurement warning"] { padding-top:88px; }
    .growth-section[data-section="north-star principle and sources"] { padding-top:10px; padding-bottom:88px; }
    .growth-section:nth-of-type(even) { background:#fbf6ed; } .section-header { margin-bottom:22px; }
    .section-header__kicker,.eyebrow,.evidence { color:var(--violet); font-size:var(--label-size); font-weight:800; letter-spacing:.07em; text-transform:uppercase; }
    .section-header__title { font-size:44px; } .section-header__note,.source-note { color:var(--muted); font-size:var(--note-size); }
    h1 { max-width:980px; margin:18px 0; font-size:84px; line-height:.94; letter-spacing:-.045em; } h3,p { margin-top:0; }
    .hero-layout { display:grid; grid-template-columns:1.5fr .8fr; gap:52px; height:100%; align-items:center; }
    .hero-copy,.warning-card p,.case-card p,.cadence-card p,.priority-card p,.hypothesis p { font-size:var(--body-size); line-height:1.34; }
    .warning-card { padding:28px; border:2px solid var(--magenta); border-radius:28px; background:var(--paper); }
    .warning-card b { color:var(--magenta); font-size:var(--label-size); } .warning-card p { margin:14px 0 0; }
    .market-flow,.pokrov-main { display:flex; align-items:stretch; gap:12px; }
    .flow-node { display:flex; flex:1; min-height:220px; padding:22px; align-items:center; justify-content:center; border:2px solid var(--violet); border-radius:26px; background:var(--paper); text-align:center; font-size:var(--body-size); font-weight:750; }
    .route-arrow,.main-arrow { align-self:center; color:var(--magenta); font-size:44px; font-weight:900; }
    .measurement-note { margin:30px 0 0; padding:22px 28px; border-left:8px solid var(--magenta); background:#f1dfdf; font-size:var(--body-size); font-weight:750; }
    .engine-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }
    .engine-card { min-height:344px; padding:22px; border:1px solid var(--line); border-radius:24px; background:var(--paper); }
    .engine-card h3,.case-card h3,.cadence-card h3,.priority-card h3 { margin:15px 0; font-size:32px; }
    .examples { display:flex; flex-wrap:wrap; gap:10px; } .example { padding:9px 13px; border-radius:999px; background:#eee2f0; font-size:var(--label-size); }
    .case-grid,.cadence-grid,.priority-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:18px; }
    .case-card,.cadence-card,.priority-card { padding:22px; border:1px solid var(--line); border-radius:24px; background:var(--paper); }
    .case-card { min-height:380px; } .case-card strong { display:block; min-height:72px; color:var(--magenta); font-size:var(--label-size); line-height:1.35; }
    .hypothesis { display:grid; grid-template-columns:1fr 1.4fr; gap:24px; margin-top:20px; padding:18px 22px; border-left:8px solid var(--violet); background:#eee5f1; }
    .hypothesis b { color:var(--violet); font-size:var(--label-size); } .hypothesis p { margin:0; }
    .cadence-card { min-height:260px; padding:16px 20px; } .cadence-card div { display:flex; align-items:center; justify-content:space-between; }
    .cadence-card h3 { margin:8px 0; } .cadence-card p { margin:8px 0 0; line-height:1.25; }
    .cadence-card b { color:var(--risk); font-size:36px; } .pokrov-main { gap:8px; }
    .pokrov-node { display:flex; flex:1; min-height:126px; padding:14px; align-items:center; justify-content:center; border:2px solid var(--emerald); border-radius:20px; background:#f2fbf5; text-align:center; font-size:var(--label-size); font-weight:800; }
    .main-arrow { color:var(--emerald); } .optional-path { width:390px; margin:30px 0 0 900px; padding:18px 22px; border:2px dashed var(--emerald); border-radius:22px; background:#e3f3e8; }
    .optional-path::before { content:"↓"; display:block; text-align:center; margin-top:-54px; color:var(--emerald); font-size:40px; }
    .optional-path h3 { margin:8px 0; color:var(--emerald); font-size:30px; } .optional-path p { margin:5px 0; font-size:var(--body-size); line-height:1.25; }
    .priority-card { min-height:220px; } .priority-card>span { color:var(--emerald); font-size:var(--label-size); font-weight:900; }
    .north-star { display:grid; grid-template-columns:1.7fr 1fr; gap:32px; align-items:center; height:100%; }
    .north-star blockquote { margin:0; color:var(--emerald); font-size:30px; line-height:1.18; font-weight:850; }
    .source-note { line-height:1.1; } .source-note code { color:var(--ink); }
  </style>
  ${section(0, 580, "hero and measurement warning", `<div class="hero-layout"><div><span class="eyebrow">POKROV · GROWTH MAP · ${capturedDate}</span><h1>От внимания к продукту</h1><p class="hero-copy">Какие механики ведут внешний трафик в канал, бот и продуктовые поверхности.</p></div><aside class="warning-card"><b>НЕ КОНВЕРСИОННАЯ ВОРОНКА</b><p>Рост канала не доказывает оплату, активацию или удержание. Здесь показаны наблюдаемые и предполагаемые механики.</p></aside></div>`)}
  ${section(580, 740, "market mechanism map", `${sectionHeader("01 · MARKET ROUTE", "Карта рыночной механики", "Маршруты показывают механику, а не измеренную конверсию.")}<div class="market-flow">${marketNodes}</div><p class="measurement-note">Рост канала не доказывает оплату, активацию или удержание.</p>`)}
  ${section(1320, 1000, "six inflow engines", `${sectionHeader("02 · INFLOW ENGINES", "Шесть двигателей притока", "Evidence label относится к блоку целиком; примеры не доказывают коммерческий результат.")}<div class="engine-grid">${engines}</div>`)}
  ${section(2320, 780, "three high-growth mechanism cases", `${sectionHeader("03 · CO-OCCURRING SIGNALS", "Три high-growth кейса", "Интерпретация совместно наблюдаемых механик без причинных claims.")}<div class="case-grid">${highGrowth}</div><div class="hypothesis"><b>QUALITY × SPEED · стратегическая гипотеза</b><p>Быстрый приток: prizes / gates. Product continuation: app, cabinet, recovery, status, support. Конверсия и удержание не измерены.</p></div>`)}
  ${section(3100, 520, "three cadence-with-decline cases", `${sectionHeader("04 · CADENCE ≠ GROWTH", "Контент сосуществовал со спадом", "Частота публикаций не объясняет знак динамики сама по себе.")}<div class="cadence-grid">${cadence}</div>`)}
  ${section(3620, 680, "POKROV main path and optional Telegram branch", `${sectionHeader("05 · POKROV", "Основной путь без Telegram gate", "Главная линия заканчивается paid key / renewal; боковая ветка не возвращается в обязательный путь.")}<div class="pokrov-main" data-pokrov-path="main">${mainSteps}</div><aside class="optional-path" data-pokrov-path="optional-telegram" data-branches-from="cabinet-account" data-rejoins="none"><h3>Telegram — необязательная ветка</h3><p>Explicit link + membership → <b>+10 дней</b></p><p>Support / community; не возвращается в обязательный путь.</p></aside>`)}
  ${section(4300, 480, "priority build sequence", `${sectionHeader("06 · BUILD ORDER", "Сначала фундамент, затем масштаб", "Без выдуманных сроков и целевых метрик.")}<div class="priority-grid">${priorities}</div>`)}
  ${section(4780, 220, "north-star principle and sources", `<div class="north-star"><blockquote>Не покупать рост любой ценой. Строить приток, который доходит до первого подключения и остаётся из-за продукта.</blockquote><footer class="source-note"><b>retained dataset</b> · ${escapeHtml(data.snapshot.status)}<br>${capturedDate} · ${postWindow}<br>POKROV: нет подтверждённой сопоставимой метрики.<br>SHA-256: <code>${escapeHtml(sourceHash.slice(0, 16))}…</code></footer></div>`)} `;

  return baseDocument({ title: "POKROV — от внимания к продукту", themeClass: "growth-funnel", body, sourceHash });
}
