"use client";

import { apiFetch, type ApiRequestInit } from "@/lib/admin-api/client";
import type {
  AdminModulePayload,
  AdminUserCardPayload,
  AdminUsersPayload,
  FreeTierUser,
  NodeHealthRow,
  NodeRuntimePayload,
  NodeTimeseriesRow,
  OnlineUsersPayload,
  OpsAlert,
  PaymentsSummaryPayload,
  ProviderQuotaConfig,
  TrafficSummaryRow
} from "@/lib/admin-api/types";

export {
  AdminApiError,
  apiFetch,
  clearAdminInitData,
  clearAdminSessionToken,
  createAdminSession,
  hasAdminAuthMaterial,
  saveAdminInitData,
  saveAdminSessionToken
} from "@/lib/admin-api/client";
export { fetchAlerts, fetchOpsOverview } from "@/lib/admin-api/overview";
export type { ApiRequestInit } from "@/lib/admin-api/client";
export type {
  AdminModulePayload,
  AdminSessionPayload,
  AdminUserCardPayload,
  AdminUserRow,
  AdminUsersPayload,
  FreeTierSummary,
  FreeTierUser,
  NodeHealthRow,
  NodeRuntimePayload,
  NodeTimeseriesRow,
  OnlineUserRow,
  OnlineUsersPayload,
  OpsAlert,
  OpsOverview,
  PaymentsSummaryPayload,
  ProviderQuotaConfig,
  ProviderQuotaStatus,
  TrafficSummaryRow
} from "@/lib/admin-api/types";

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
