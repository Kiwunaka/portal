"use client";

import { CANONICAL_API_BASE_URL } from "@/lib/portal";

const WEB_SESSION_TOKEN_KEY = "portal_web_session_token";
const ADMIN_INIT_DATA_KEY = "pokrov_admin_init_data";
const ADMIN_SESSION_TOKEN_KEY = "pokrov_admin_session_token";
const DEFAULT_TIMEOUT_MS = 15000;

export type OpsAlert = {
  id: number;
  fingerprint: string;
  source: string;
  severity: "critical" | "warning" | "info" | string;
  status: "active" | "silenced" | "resolved" | string;
  title: string;
  body?: string | null;
  node_code?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  resolved_at?: string | null;
  acknowledged_at?: string | null;
  silence_until?: string | null;
};

export type ProviderQuotaStatus = {
  node_code: string;
  node_name?: string | null;
  configured: boolean;
  enabled: boolean;
  state: string;
  included_gb: number;
  used_gb: number;
  remaining_gb: number;
  used_pct: number;
  cycle_start?: string | null;
  cycle_end?: string | null;
  reset_day?: number;
  timezone?: string;
  warning_ratio?: number;
  critical_ratio?: number;
  source: string;
};

export type ProviderQuotaConfig = {
  id: number;
  node_code: string;
  included_bytes: number;
  included_gb: number;
  reset_day: number;
  timezone: string;
  warning_ratio: number;
  critical_ratio: number;
  enabled: boolean;
  notes?: string | null;
  updated_by?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type FreeTierSummary = {
  free_users: number;
  sampled_users: number;
  limit_gb_per_user: number;
  cycle_days: number;
  used_gb: number;
  limit_gb_total: number;
  remaining_gb: number;
  used_pct: number;
  near_cap_users: number;
  over_cap_users: number;
  burn_rate_gb_per_day: number;
  source: string;
};

export type FreeTierUser = {
  tg_id: number;
  username?: string | null;
  display_name?: string | null;
  is_active: boolean;
  used_gb: number;
  limit_gb: number;
  remaining_gb: number;
  used_pct: number;
  state: string;
  cycle_start?: string | null;
  cycle_end?: string | null;
  source: string;
};

export type TrafficSummaryRow = {
  date: string;
  node_code: string;
  pool_code: string;
  traffic_bytes: number;
  traffic_gb: number;
  samples: number;
};

export type NodeTimeseriesRow = {
  sampled_at: string;
  node_code: string;
  source: string;
  cpu_percent?: number | null;
  memory_used_mb?: number | null;
  memory_total_mb?: number | null;
  disk_used_gb?: number | null;
  disk_total_gb?: number | null;
  network_rx_mbps?: number | null;
  network_tx_mbps?: number | null;
  network_total_mbps?: number | null;
  traffic_bytes_total?: number | null;
  active_clients?: number | null;
  score?: number | null;
  capacity_score?: number | null;
  capacity_state?: string | null;
};

export type OpsOverview = {
  ok: boolean;
  generated_at: string;
  summary: {
    users: {
      total: number;
      active: number;
      free: number;
      paid: number;
      unique_install_ids_24h?: number;
      unique_install_ids_7d?: number;
    };
    tickets: { open: number };
    nodes: { total: number; healthy: number };
    errors: Record<string, number | boolean>;
    observer?: { watch_users: number; suspicious_users: number };
  };
  metrics: {
    status: string;
    age_seconds?: number | null;
    alerts?: Record<string, number>;
    nodes: Array<Record<string, unknown>>;
  };
  capacity: {
    nodes: Array<Record<string, unknown>>;
  };
  free_tier: FreeTierSummary;
  provider_quotas: ProviderQuotaStatus[];
  alerts: {
    active: OpsAlert[];
    active_count: number;
    critical_count: number;
    warning_count: number;
  };
};

export type AdminModulePayload = {
  section: string;
  rows: Array<Record<string, unknown>>;
  payload: Record<string, unknown>;
};

export type AdminSessionPayload = {
  ok: boolean;
  token: string;
  expires_in: number;
  user?: {
    id: number;
    username?: string | null;
    role?: string | null;
  };
};

type ApiRequestInit = RequestInit & { timeoutMs?: number };

function getCookieValue(name: string): string {
  if (typeof document === "undefined") return "";
  const prefix = `${encodeURIComponent(name)}=`;
  for (const part of document.cookie.split(";")) {
    const item = part.trim();
    if (item.startsWith(prefix)) return decodeURIComponent(item.slice(prefix.length));
  }
  return "";
}

function getStoredValue(key: string): string {
  if (typeof window === "undefined") return "";
  try {
    return String(window.localStorage?.getItem(key) || "").trim();
  } catch {
    return "";
  }
}

function getAdminInitDataFromStorage(): string {
  if (typeof window === "undefined") return "";
  try {
    const sessionValue = String(window.sessionStorage?.getItem(ADMIN_INIT_DATA_KEY) || "").trim();
    if (sessionValue) return sessionValue;
  } catch {
    // Ignore blocked storage.
  }
  try {
    const legacyValue = String(window.localStorage?.getItem(ADMIN_INIT_DATA_KEY) || "").trim();
    if (!legacyValue) return "";
    window.sessionStorage?.setItem(ADMIN_INIT_DATA_KEY, legacyValue);
    window.localStorage?.removeItem(ADMIN_INIT_DATA_KEY);
    return legacyValue;
  } catch {
    return "";
  }
}

function getTelegramInitData(): string {
  if (typeof window === "undefined") return "";
  const tg = (window as typeof window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
  return String(tg?.initData || getAdminInitDataFromStorage() || "").trim();
}

function getAdminSessionToken(): string {
  if (typeof window === "undefined") return "";
  try {
    return String(window.sessionStorage?.getItem(ADMIN_SESSION_TOKEN_KEY) || "").trim();
  } catch {
    return "";
  }
}

function getWebSessionToken(): string {
  return getStoredValue(WEB_SESSION_TOKEN_KEY) || getCookieValue(WEB_SESSION_TOKEN_KEY);
}

function authHeaders(): Headers {
  const headers = new Headers();
  const token = getAdminSessionToken() || getWebSessionToken();
  const initData = getTelegramInitData();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
    headers.set("X-Web-Auth-Token", token);
  }
  if (initData) headers.set("X-Telegram-Init-Data", initData);
  return headers;
}

function apiBase(): string {
  const envBase = String(process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
  return (envBase || CANONICAL_API_BASE_URL || "https://api.pokrov.space").replace(/\/+$/, "");
}

async function parseApiError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return String(body?.detail || body?.message || `API error ${response.status}`);
  } catch {
    return `API error ${response.status}`;
  }
}

export function saveAdminInitData(value: string): void {
  if (typeof window === "undefined") return;
  const clean = String(value || "").trim();
  if (!clean) return;
  try {
    window.sessionStorage.setItem(ADMIN_INIT_DATA_KEY, clean);
    window.localStorage.removeItem(ADMIN_INIT_DATA_KEY);
  } catch {
    // Auth gate will stay visible if storage is unavailable.
  }
}

export function clearAdminInitData(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(ADMIN_INIT_DATA_KEY);
    window.localStorage.removeItem(ADMIN_INIT_DATA_KEY);
  } catch {
    // Ignore blocked storage.
  }
}

export function saveAdminSessionToken(token: string): void {
  if (typeof window === "undefined") return;
  const clean = String(token || "").trim();
  if (!clean) return;
  try {
    window.sessionStorage.setItem(ADMIN_SESSION_TOKEN_KEY, clean);
  } catch {
    // Auth gate will stay visible if storage is unavailable.
  }
}

export function clearAdminSessionToken(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(ADMIN_SESSION_TOKEN_KEY);
  } catch {
    // Ignore blocked storage.
  }
}

export function hasAdminAuthMaterial(): boolean {
  return Boolean(getAdminSessionToken() || getWebSessionToken() || getTelegramInitData());
}

export async function apiFetch<T>(path: string, init?: ApiRequestInit): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...requestInit } = init || {};
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const headers = new Headers(requestInit.headers || {});
  for (const [key, value] of authHeaders()) headers.set(key, value);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      ...requestInit,
      headers,
      credentials: "include",
      signal: signal || controller.signal
    });
    if (!response.ok) throw new Error(await parseApiError(response));
    if (response.status === 204) return {} as T;
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timer);
  }
}

export function fetchOpsOverview(): Promise<OpsOverview> {
  return apiFetch<OpsOverview>("/api/admin/ops/overview");
}

export function createAdminSession(): Promise<AdminSessionPayload> {
  return apiFetch<AdminSessionPayload>("/api/admin/auth/session", { method: "POST" });
}

export async function fetchAlerts(status = "active"): Promise<OpsAlert[]> {
  const data = await apiFetch<{ alerts: OpsAlert[] }>(`/api/admin/alerts?status=${encodeURIComponent(status)}`);
  return data.alerts || [];
}

export async function fetchProviderQuotas(): Promise<ProviderQuotaConfig[]> {
  const data = await apiFetch<{ quotas: ProviderQuotaConfig[] }>("/api/admin/provider-quotas");
  return data.quotas || [];
}

export async function saveProviderQuota(
  nodeCode: string,
  payload: {
    included_gb: number;
    reset_day: number;
    timezone: string;
    warning_ratio: number;
    critical_ratio: number;
    enabled: boolean;
    notes?: string;
  },
  configured: boolean
): Promise<ProviderQuotaConfig> {
  const path = configured ? `/api/admin/provider-quotas/${encodeURIComponent(nodeCode)}` : "/api/admin/provider-quotas";
  const body = configured ? payload : { ...payload, node_code: nodeCode };
  const data = await apiFetch<{ quota: ProviderQuotaConfig }>(path, {
    method: configured ? "PATCH" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  return data.quota;
}

export async function deleteProviderQuota(nodeCode: string): Promise<void> {
  await apiFetch<{ ok: boolean }>(`/api/admin/provider-quotas/${encodeURIComponent(nodeCode)}`, { method: "DELETE" });
}

export async function ackAlert(id: number): Promise<OpsAlert> {
  const data = await apiFetch<{ alert: OpsAlert }>(`/api/admin/alerts/${id}/ack`, { method: "POST" });
  return data.alert;
}

export async function silenceAlert(id: number, minutes = 60): Promise<OpsAlert> {
  const data = await apiFetch<{ alert: OpsAlert }>(`/api/admin/alerts/${id}/silence`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ minutes })
  });
  return data.alert;
}

export async function fetchFreeUsers(): Promise<FreeTierUser[]> {
  const data = await apiFetch<{ users: FreeTierUser[] }>("/api/admin/free-tier/users?limit=500");
  return data.users || [];
}

export async function fetchTrafficSummary(): Promise<TrafficSummaryRow[]> {
  const data = await apiFetch<{ rows: TrafficSummaryRow[] }>("/api/admin/traffic/summary");
  return data.rows || [];
}

export async function fetchNodeTimeseries(nodeCode = ""): Promise<NodeTimeseriesRow[]> {
  const qs = nodeCode ? `?node_code=${encodeURIComponent(nodeCode)}` : "";
  const data = await apiFetch<{ rows: NodeTimeseriesRow[] }>(`/api/admin/nodes/timeseries${qs}`);
  return data.rows || [];
}

export async function fetchAdminModule(section: string): Promise<AdminModulePayload> {
  const normalized = String(section || "").trim();
  const pathBySection: Record<string, string> = {
    users: "/api/admin/users?page_size=50",
    tickets: "/api/admin/tickets?status=&limit=50",
    payments: "/api/admin/payments/orders?limit=50",
    promos: "/api/admin/promos?limit=100",
    referrals: "/api/admin/referrals/pending?limit=100&status=",
    release: "/api/admin/live-updates?include_inactive=true",
    funnel: "/api/admin/funnel/summary"
  };
  const path = pathBySection[normalized];
  if (!path) return { section: normalized, rows: [], payload: {} };
  const payload = await apiFetch<Record<string, unknown>>(path);
  const rows =
    (Array.isArray(payload.users) && payload.users) ||
    (Array.isArray(payload.tickets) && payload.tickets) ||
    (Array.isArray(payload.orders) && payload.orders) ||
    (Array.isArray(payload.payments) && payload.payments) ||
    (Array.isArray(payload.promos) && payload.promos) ||
    (Array.isArray(payload.rows) && payload.rows) ||
    (Array.isArray(payload.updates) && payload.updates) ||
    [];
  return { section: normalized, rows: rows as Array<Record<string, unknown>>, payload };
}

export async function sendBroadcast(payload: { text: string; segment: string; limit: number; tg_ids?: number[] }): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/admin/broadcast", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function adminCommand(path: string, method: "POST" | "PATCH" | "DELETE", payload?: Record<string, unknown>): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(path, {
    method,
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined
  });
}
