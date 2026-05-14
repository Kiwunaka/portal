function normalizeBase(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function isLocalBase(value) {
  try {
    const url = new URL(value);
    return (
      url.hostname === "localhost" ||
      url.hostname === "127.0.0.1" ||
      url.hostname === "::1" ||
      url.hostname.endsWith(".local")
    );
  } catch {
    return false;
  }
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

  const appOrigin = normalizeBase(origin);
  const canonical = normalizeBase(directApiBase);
  const shouldSkipAppShellBase = (value) => {
    const normalized = normalizeBase(value);
    return Boolean(
      normalized &&
        appOrigin &&
        canonical &&
        normalized === appOrigin &&
        normalized !== canonical &&
        !isLocalBase(normalized),
    );
  };

  const push = (value) => {
    const normalized = normalizeBase(value);
    if (!normalized || seen.has(normalized) || shouldSkipAppShellBase(normalized)) return;
    seen.add(normalized);
    bases.push(normalized);
  };

  const configured = normalizeBase(envBase);

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
