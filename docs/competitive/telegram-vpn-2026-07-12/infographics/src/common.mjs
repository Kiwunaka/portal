const MISSING_VALUE = "нет данных";

const EVIDENCE_LABELS = Object.freeze({
  DIRECT_OR_PUBLIC_EVIDENCE: "подтверждено",
  MIXED_DIRECT_AND_INFERRED: "смешанные данные",
  INFERENCE: "вывод по сигналам",
});

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

export const formatInt = (value) => value == null
  ? MISSING_VALUE
  : new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(value);

export const formatPercent = (value) => value == null
  ? MISSING_VALUE
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

export function getChannel(data, id) {
  const channel = data?.channels?.find((row) => row.id === id);
  if (!channel) throw new Error(`Unknown channel id: ${id}`);
  return channel;
}

export function getMarketing(data, id) {
  return data?.marketing_analysis?.find((row) => row.id === id) ?? null;
}

export function getAppScale(data, id) {
  return data?.android_footprint_scale?.entries?.find((row) => row.id === id) ?? null;
}

export function evidenceLabel(value) {
  return EVIDENCE_LABELS[value] ?? MISSING_VALUE;
}

export function baseDocument({ title, themeClass, body, sourceHash }) {
  const safeTitle = escapeHtml(title);
  const safeThemeClass = escapeHtml(themeClass);
  const safeSourceHash = escapeHtml(sourceHash);

  return `<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1600, initial-scale=1">
  <meta name="source-sha256" content="${safeSourceHash}">
  <title>${safeTitle}</title>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; width: 1600px; min-width: 1600px; background: #eef2ef; }
    body { color: #16211c; font-family: "Golos Text", Arial, system-ui, sans-serif; }
    .infographic { width: 1600px; height: 5000px; overflow: hidden; position: relative; }
    svg { display: block; overflow: visible; }
    .section-header { margin: 0 0 44px; }
    .section-header__kicker { margin: 0 0 12px; font-size: 22px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    .section-header__title { margin: 0; font-size: 54px; line-height: 1.05; }
    .section-header__note { margin: 16px 0 0; max-width: 1180px; font-size: 24px; line-height: 1.4; }
  </style>
</head>
<body>
  <main class="infographic ${safeThemeClass}" data-source-sha256="${safeSourceHash}">${body}</main>
</body>
</html>`;
}

export function horizontalBars(items, options = {}) {
  const width = options.width ?? 1408;
  const rowHeight = options.rowHeight ?? 72;
  const labelWidth = options.labelWidth ?? 320;
  const valueWidth = options.valueWidth ?? 160;
  const barHeight = options.barHeight ?? 28;
  const getLabel = options.getLabel ?? ((item) => item.label ?? item.name ?? "");
  const getValue = options.getValue ?? ((item) => item.value);
  const formatValue = options.formatValue ?? formatInt;
  const values = items
    .map((item) => getValue(item))
    .filter((value) => Number.isFinite(value));
  const inferredMaximum = values.length > 0
    ? Math.max(...values.map((value) => Math.abs(value)))
    : 0;
  const maximum = Math.abs(options.maxValue ?? inferredMaximum);
  const chartWidth = Math.max(0, width - labelWidth - valueWidth);
  const height = rowHeight * items.length;
  const title = escapeHtml(options.title ?? "Горизонтальная диаграмма");
  const className = escapeHtml(options.className ?? "horizontal-bars");

  const rows = items.map((item, index) => {
    const rawValue = getValue(item);
    const hasValue = Number.isFinite(rawValue);
    const magnitude = hasValue && maximum > 0
      ? Math.min(Math.abs(rawValue) / maximum, 1)
      : 0;
    const y = index * rowHeight;
    const textY = y + rowHeight / 2;
    const rectY = textY - barHeight / 2;
    const fill = item.color
      ?? (rawValue < 0 ? options.negativeColor ?? "#d24a3a" : options.positiveColor ?? "#147a4b");
    const valueLabel = hasValue
      ? item.displayValue ?? formatValue(rawValue)
      : options.missingLabel ?? MISSING_VALUE;
    const bar = hasValue
      ? `<rect class="horizontal-bars__bar" x="${labelWidth}" y="${rectY}" width="${magnitude * chartWidth}" height="${barHeight}" rx="${barHeight / 2}" fill="${escapeHtml(fill)}" />`
      : "";

    return `<g class="horizontal-bars__row" data-index="${index}">
  <text class="horizontal-bars__label" x="0" y="${textY}" dominant-baseline="middle">${escapeHtml(getLabel(item))}</text>
  ${bar}
  <text class="horizontal-bars__value" x="${labelWidth + chartWidth + 24}" y="${textY}" dominant-baseline="middle">${escapeHtml(valueLabel)}</text>
</g>`;
  }).join("\n");

  return `<svg class="${className}" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="${title}" xmlns="http://www.w3.org/2000/svg">
${rows}
</svg>`;
}

export function sectionHeader(kicker, title, note) {
  const noteMarkup = note == null || note === ""
    ? ""
    : `\n  <p class="section-header__note">${escapeHtml(note)}</p>`;

  return `<header class="section-header">
  <p class="section-header__kicker">${escapeHtml(kicker)}</p>
  <h2 class="section-header__title">${escapeHtml(title)}</h2>${noteMarkup}
</header>`;
}
