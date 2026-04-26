function normalizeBase(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

export function resolveCandidateApiBases({
  envBase = "",
  origin = "",
  directApiBase = "",
  hasSessionToken = false,
  enableLegacyPortFallback = false,
} = {}) {
  const seen = new Set();
  const bases = [];

  const push = (value) => {
    const normalized = normalizeBase(value);
    if (!normalized || seen.has(normalized)) return;
    seen.add(normalized);
    bases.push(normalized);
  };

  const configured = normalizeBase(envBase);
  const canonical = normalizeBase(directApiBase);
  const appOrigin = normalizeBase(origin);

  if (configured) push(configured);
  if (canonical) push(canonical);
  if (appOrigin) push(appOrigin);

  if (enableLegacyPortFallback && appOrigin) {
    try {
      const url = new URL(appOrigin);
      push(`${url.protocol}//${url.hostname}:2096`);
    } catch {
      // Ignore malformed origins.
    }
  }

  if (!hasSessionToken && canonical && appOrigin && bases[0] === appOrigin) {
    return [canonical, ...bases.filter((base) => base !== canonical)];
  }

  return bases;
}

export function resolvePrimaryApiBase(options = {}) {
  return resolveCandidateApiBases(options)[0] || normalizeBase(options.directApiBase);
}

export function classifyApiPayload({ bodyText = "", contentType = "" } = {}) {
  const text = String(bodyText || "").trim();
  const type = String(contentType || "").toLowerCase();

  if (!text) return "empty";
  if (type.includes("application/json") || type.includes("+json")) return "json";
  if (type.includes("text/html")) return "html";
  if (/^<!doctype html/i.test(text) || /^<html[\s>]/i.test(text)) return "html";
  if ((text.startsWith("{") && text.endsWith("}")) || (text.startsWith("[") && text.endsWith("]"))) return "json";

  return "text";
}
