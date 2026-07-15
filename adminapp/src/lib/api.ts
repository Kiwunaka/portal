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

export type AdminUserRow = Record<string, unknown> & {
  tg_id: number;
  username?: string | null;
  display_name?: string | null;
  sub_type?: string | null;
  status?: string | null;
  origin?: string | null;
  expiry_at?: string | null;
  observer_state?: string | null;
};

export type AdminUsersPayload = {
  page: number;
  page_size: number;
  total: number;
  sort: string;
  users: AdminUserRow[];
};

export type AdminUserCardPayload = Record<string, unknown> & {
  user?: Record<string, unknown>;
  tickets?: Array<Record<string, unknown>>;
  key_policies?: Array<Record<string, unknown>>;
  key_history?: Array<Record<string, unknown>>;
  admin_actions?: Array<Record<string, unknown>>;
  payment_orders?: Array<Record<string, unknown>>;
  observer?: Record<string, unknown>;
  risk?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  keys?: Array<Record<string, unknown>>;
  keys_state?: {
    summary?: Record<string, unknown>;
    keys?: Array<Record<string, unknown>>;
  };
};

export type NodeHealthRow = Record<string, unknown> & {
  code: string;
  name?: string | null;
  enabled?: boolean;
  accepting_new_clients?: boolean;
  is_draining?: boolean;
  is_healthy?: boolean;
  health_score?: number | null;
  capacity_state?: string | null;
  freshness_status?: string | null;
  online_keys_now?: number | null;
  online_connections_now?: number | null;
  panel_latency_ms?: number | null;
  dataplane_ok?: boolean | null;
  dataplane_rtt_ms?: number | null;
  ipv4_health?: string | null;
  ipv6_health?: string | null;
  observer_is_stale?: boolean | null;
};

export type NodeRuntimePayload = {
  ok: boolean;
  updated_at?: string;
  nodes: Array<Record<string, unknown>>;
};

export type OnlineUserRow = Record<string, unknown> & {
  identity: string;
  tg_id?: number | null;
  username?: string | null;
  display_name?: string | null;
  sub_type?: string | null;
  status?: string | null;
  nodes_online?: string[];
  online_keys_now?: number;
  online_connections_now?: number;
  ip_count?: number;
  risk_flags?: string[];
  last_online_at?: string | null;
  raw_ip_exposed?: boolean;
};

export type OnlineUsersPayload = {
  ok: boolean;
  generated_at?: string;
  rows: OnlineUserRow[];
  total: number;
  limit: number;
  summary: Record<string, unknown>;
  panel_errors?: Array<Record<string, unknown>>;
  notes?: string[];
};

export type PaymentsSummaryPayload = {
  ok: boolean;
  period: Record<string, unknown>;
  revenue: {
    currency: string;
    paid_count: number;
    amount: number;
    by_currency?: Array<Record<string, unknown>>;
  };
  status_counts: Record<string, number>;
  attention: {
    pending_count: number;
    manual_review_count: number;
    failed_count: number;
    problem_count: number;
  };
  abandoned: Record<string, unknown>;
  problem_orders: Array<Record<string, unknown>>;
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

export class AdminApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly correlationId: string | null;

  constructor(message: string, status: number, code: string | null, correlationId: string | null) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
  }
}

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

type ParsedApiError = {
  message: string;
  code: string | null;
  correlationId: string | null;
};

function optionalErrorField(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

async function parseApiError(response: Response): Promise<ParsedApiError> {
  let body: Record<string, unknown> = {};
  try {
    const parsed = await response.json();
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      body = parsed as Record<string, unknown>;
    }
  } catch {
    // Keep the HTTP metadata even when the response body is absent or malformed.
  }

  const detail = body.detail && typeof body.detail === "object" && !Array.isArray(body.detail)
    ? (body.detail as Record<string, unknown>)
    : {};
  const message =
    optionalErrorField(body.detail) ||
    optionalErrorField(body.message) ||
    optionalErrorField(detail.message) ||
    `API error ${response.status}`;
  const code = optionalErrorField(body.code) || optionalErrorField(detail.code);
  const correlationId =
    optionalErrorField(body.correlation_id) ||
    optionalErrorField(body.correlationId) ||
    optionalErrorField(detail.correlation_id) ||
    optionalErrorField(detail.correlationId) ||
    optionalErrorField(response.headers.get("x-correlation-id")) ||
    optionalErrorField(response.headers.get("x-request-id"));

  return { message, code, correlationId };
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
    if (!response.ok) {
      const parsedError = await parseApiError(response);
      throw new AdminApiError(parsedError.message, response.status, parsedError.code, parsedError.correlationId);
    }
    if (response.status === 204) return {} as T;
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timer);
  }
}

export function fetchOpsOverview(init?: ApiRequestInit): Promise<OpsOverview> {
  return apiFetch<OpsOverview>("/api/admin/ops/overview", init);
}

export function createAdminSession(): Promise<AdminSessionPayload> {
  return apiFetch<AdminSessionPayload>("/api/admin/auth/session", { method: "POST" });
}

export async function fetchAlerts(status = "active"): Promise<OpsAlert[]> {
  const data = await apiFetch<{ alerts: OpsAlert[] }>(`/api/admin/alerts?status=${encodeURIComponent(status)}`);
  return data.alerts || [];
}

export async function fetchProviderQuotas(init?: ApiRequestInit): Promise<ProviderQuotaConfig[]> {
  const data = await apiFetch<{ quotas: ProviderQuotaConfig[] }>("/api/admin/provider-quotas", init);
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

export async function fetchFreeUsers(init?: ApiRequestInit): Promise<FreeTierUser[]> {
  const data = await apiFetch<{ users: FreeTierUser[] }>("/api/admin/free-tier/users?limit=500", init);
  return data.users || [];
}

export async function fetchTrafficSummary(init?: ApiRequestInit): Promise<TrafficSummaryRow[]> {
  const data = await apiFetch<{ rows: TrafficSummaryRow[] }>("/api/admin/traffic/summary", init);
  return data.rows || [];
}

export async function fetchNodeTimeseries(nodeCode = "", init?: ApiRequestInit): Promise<NodeTimeseriesRow[]> {
  const qs = nodeCode ? `?node_code=${encodeURIComponent(nodeCode)}` : "";
  const data = await apiFetch<{ rows: NodeTimeseriesRow[] }>(`/api/admin/nodes/timeseries${qs}`, init);
  return data.rows || [];
}

export async function fetchAdminModule(section: string, init?: ApiRequestInit): Promise<AdminModulePayload> {
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
  const payload = await apiFetch<Record<string, unknown>>(path, init);
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

export async function fetchAdminUsers(params?: { q?: string; status?: string; limit?: number; offset?: number; sort?: string }, init?: ApiRequestInit): Promise<AdminUsersPayload> {
  const query = new URLSearchParams();
  query.set("page_size", String(Math.max(1, Math.min(Number(params?.limit || 50), 200))));
  query.set("offset", String(Math.max(0, Number(params?.offset || 0))));
  if (params?.q) query.set("q", params.q);
  if (params?.status) query.set("status", params.status);
  if (params?.sort) query.set("sort", params.sort);
  return apiFetch<AdminUsersPayload>(`/api/admin/users?${query.toString()}`, init);
}

export function fetchAdminUserCard(tgId: number, init?: ApiRequestInit): Promise<AdminUserCardPayload> {
  return apiFetch<AdminUserCardPayload>(`/api/admin/users/${encodeURIComponent(String(tgId))}`, init);
}

export async function fetchNodesHealth(init?: ApiRequestInit): Promise<NodeHealthRow[]> {
  const data = await apiFetch<{ nodes: NodeHealthRow[] }>("/api/admin/nodes/health", init);
  return data.nodes || [];
}

export function fetchNodesRuntime(init?: ApiRequestInit): Promise<NodeRuntimePayload> {
  return apiFetch<NodeRuntimePayload>("/api/admin/nodes/runtime", init);
}

export function fetchNodesDrift(init?: ApiRequestInit): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/admin/nodes/drift", init);
}

export async function fetchKeyPressure(init?: ApiRequestInit): Promise<Array<Record<string, unknown>>> {
  const data = await apiFetch<Record<string, unknown>>("/api/admin/keys/pressure?limit=80", init);
  const rows = data.rows || data.keys || data.pressure || [];
  return Array.isArray(rows) ? (rows as Array<Record<string, unknown>>) : [];
}

export function fetchOnlineUsers(params?: { limit?: number; only?: string }, init?: ApiRequestInit): Promise<OnlineUsersPayload> {
  const query = new URLSearchParams();
  query.set("limit", String(Math.max(1, Math.min(Number(params?.limit || 200), 500))));
  if (params?.only) query.set("only", params.only);
  return apiFetch<OnlineUsersPayload>(`/api/admin/online/users?${query.toString()}`, init);
}

export function fetchPaymentsSummary(period: "today" | "7d" | "30d", init?: ApiRequestInit): Promise<PaymentsSummaryPayload> {
  return apiFetch<PaymentsSummaryPayload>(`/api/admin/payments/summary?period=${encodeURIComponent(period)}`, init);
}

export async function fetchPaymentOrders(limit = 80, init?: ApiRequestInit): Promise<Array<Record<string, unknown>>> {
  const data = await apiFetch<Record<string, unknown>>(`/api/admin/payments/orders?limit=${Math.max(1, Math.min(Number(limit || 80), 200))}`, init);
  const rows = data.orders || data.payments || [];
  return Array.isArray(rows) ? (rows as Array<Record<string, unknown>>) : [];
}

export function nodeLifecycleAction(
  nodeCode: string,
  action: "drain" | "enable" | "undrain" | "disable",
  payload?: { force?: boolean }
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/admin/nodes/${encodeURIComponent(nodeCode)}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });
}

export function nodeResync(nodeCode: string, payload?: { limit?: number; dry_run?: boolean }): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/admin/nodes/${encodeURIComponent(nodeCode)}/resync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });
}

export async function sendBroadcast(payload: { text: string; segment: string; limit: number; tg_ids?: number[]; dry_run?: boolean }): Promise<Record<string, unknown>> {
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
