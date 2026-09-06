import { CANONICAL_API_BASE_URL } from "./pokrov";

const STORAGE_KEY = "pokrov-acquisition-v1";
const SESSION_KEY = "pokrov-funnel-session";
const STORAGE_TTL_MS = 180 * 24 * 60 * 60 * 1000;

export type AcquisitionTouch = {
  source: string;
  campaign: string;
  content: string;
  ref: string;
  entryRoute: string;
  referrerHost: string;
};

type StoredAcquisition = {
  version: 1;
  sessionId: string;
  first: AcquisitionTouch;
  last: AcquisitionTouch;
  expiresAt: number;
};

export type AcquisitionContext = StoredAcquisition;

function cleanSlug(value: string | null | undefined, fallback = ""): string {
  const normalized = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_.:-]+/g, "_")
    .replace(/^[._:-]+|[._:-]+$/g, "")
    .slice(0, 64);
  return normalized || fallback;
}

function cleanRoute(value: string): string {
  try {
    const url = new URL(value, window.location.origin);
    return /^\/[A-Za-z0-9/_-]*$/.test(url.pathname) ? url.pathname.slice(0, 128) || "/" : "/";
  } catch {
    return "/";
  }
}

function isIpLiteral(value: string): boolean {
  try {
    const raw = value.trim().replace(/\.$/, "");
    const host = new URL(`http://${raw.includes(":") && !raw.startsWith("[") ? `[${raw}]` : raw}/`).hostname;
    return host.startsWith("[") || /^\d+(?:\.\d+){3}$/.test(host);
  } catch {
    return false;
  }
}

function cleanSource(value: string | null | undefined): string {
  return isIpLiteral(String(value || "")) ? "" : cleanSlug(value);
}

function cleanReferrerHost(value: string): string {
  return /^[a-z0-9.-]+$/i.test(value) && !isIpLiteral(value) ? value.toLowerCase().slice(0, 128) : "";
}

function externalReferrerHost(): string {
  try {
    if (!document.referrer) return "";
    const referrer = new URL(document.referrer);
    if (referrer.origin === window.location.origin) return "";
    return cleanReferrerHost(referrer.hostname);
  } catch {
    return "";
  }
}

function newSessionId(): string {
  try {
    const existing = window.localStorage.getItem(SESSION_KEY);
    if (existing && /^[A-Za-z0-9._:-]{8,96}$/.test(existing)) return existing;
    const next =
      typeof window.crypto?.randomUUID === "function"
        ? window.crypto.randomUUID()
        : `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 18)}`;
    window.localStorage.setItem(SESSION_KEY, next);
    return next;
  } catch {
    return `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 18)}`;
  }
}

function currentTouch(): { touch: AcquisitionTouch; explicit: boolean } {
  const params = new URLSearchParams(window.location.search);
  const referrerHost = externalReferrerHost();
  const utmSource = cleanSource(params.get("utm_source"));
  const campaign = cleanSlug(params.get("utm_campaign") || params.get("campaign"));
  const content = cleanSlug(params.get("utm_content"));
  const ref = cleanSlug(params.get("ref"));
  const explicit = Boolean(utmSource || campaign || content || ref || referrerHost);
  return {
    explicit,
    touch: {
      source: utmSource || cleanSlug(referrerHost) || "direct",
      campaign,
      content,
      ref,
      entryRoute: cleanRoute(window.location.href),
      referrerHost,
    },
  };
}

function readStored(): StoredAcquisition | null {
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "null") as StoredAcquisition | null;
    if (
      !parsed ||
      parsed.version !== 1 ||
      !/^[A-Za-z0-9._:-]{8,96}$/.test(parsed.sessionId || "") ||
      !Number.isFinite(parsed.expiresAt) ||
      parsed.expiresAt <= Date.now()
    ) {
      return null;
    }
    for (const touch of [parsed.first, parsed.last]) {
      touch.source = cleanSource(touch.source) || "direct";
      touch.referrerHost = cleanReferrerHost(touch.referrerHost || "");
    }
    return parsed;
  } catch {
    return null;
  }
}

function writeStored(value: StoredAcquisition): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    // Attribution is best-effort and never blocks product access.
  }
}

export function getAcquisitionContext(): AcquisitionContext {
  const observed = currentTouch();
  const stored = readStored();
  const next: StoredAcquisition = stored
    ? {
        ...stored,
        last: observed.explicit ? observed.touch : { ...stored.last, entryRoute: observed.touch.entryRoute },
        expiresAt: Date.now() + STORAGE_TTL_MS,
      }
    : {
        version: 1,
        sessionId: newSessionId(),
        first: observed.touch,
        last: observed.touch,
        expiresAt: Date.now() + STORAGE_TTL_MS,
      };
  writeStored(next);
  return next;
}

export function attributionEventFields(context = getAcquisitionContext()) {
  return {
    source: context.last.source,
    session_id: context.sessionId,
    campaign: context.last.campaign || undefined,
    utm_content: context.last.content || undefined,
    ref: context.last.ref || undefined,
    entry_route: cleanRoute(window.location.href),
    referrer: context.last.referrerHost ? `https://${context.last.referrerHost}/` : undefined,
  };
}

export async function mintAcquisitionHandoff(
  purpose: "android_install" | "windows_install" | "account_continue" | "checkout" | "telegram_continue",
  asset?: string,
  apiBaseUrl = CANONICAL_API_BASE_URL,
): Promise<{ handle: string; purpose: string; expires_at?: string | null } | null> {
  const context = getAcquisitionContext();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 2500);
  try {
    const apiBase = String(apiBaseUrl || CANONICAL_API_BASE_URL).trim().replace(/\/+$/, "");
    const response = await fetch(`${apiBase}/api/acquisition/handoffs`, {
      method: "POST",
      credentials: "omit",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...attributionEventFields(context),
        channel: "marketing",
        purpose,
        asset: asset || undefined,
      }),
      signal: controller.signal,
    });
    if (!response.ok) return null;
    const payload = (await response.json()) as { handle?: string; purpose?: string; expires_at?: string | null };
    const handle = String(payload.handle || "");
    if (!/^[A-Za-z0-9_-]{32,160}$/.test(handle)) return null;
    return { handle, purpose: String(payload.purpose || purpose), expires_at: payload.expires_at };
  } catch {
    return null;
  } finally {
    window.clearTimeout(timeout);
  }
}
