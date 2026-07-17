"use client";

import { apiFetch, type ApiRequestInit } from "./client";

export type TrafficRange = "7d" | "30d" | "90d";

export type TrafficRow = {
  date: string;
  node_code: string;
  pool_code: string;
  traffic_bytes: number | null;
  traffic_gb: number | null;
  samples: number | null;
};

export type TrafficPayload = {
  ok?: boolean;
  from: string | null;
  to: string | null;
  rows: TrafficRow[];
};

export type NetworkAlert = {
  id: number;
  fingerprint: string;
  source: string;
  severity: string;
  status: string;
  title: string;
  body: string | null;
  node_code: string | null;
  tg_id: number | null;
  key_id: number | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
  resolved_at: string | null;
  acknowledged_at: string | null;
  silence_until: string | null;
};

export type AlertsPayload = {
  ok?: boolean;
  generated_at: string | null;
  alerts: NetworkAlert[];
};

export type ProviderQuotaConfig = {
  id: number;
  node_code: string;
  included_bytes: number | null;
  included_gb: number | null;
  reset_day: number | null;
  timezone: string | null;
  warning_ratio: number | null;
  critical_ratio: number | null;
  enabled: boolean;
  notes_present: boolean;
  notes_length: number;
  notes_sha256: string;
  created_at: string | null;
  updated_at: string | null;
};

export type ProviderQuotaStatus = {
  node_code: string;
  node_name: string | null;
  configured: boolean;
  enabled: boolean;
  state: string;
  included_gb: number | null;
  used_gb: number | null;
  remaining_gb: number | null;
  used_pct: number | null;
  warning_ratio: number | null;
  critical_ratio: number | null;
  cycle_start: string | null;
  cycle_end: string | null;
  reset_day: number | null;
  timezone: string | null;
  sample_count: number | null;
  source: string | null;
  updated_at: string | null;
};

export type ProviderQuotasPayload = {
  configs: ProviderQuotaConfig[];
  statuses: ProviderQuotaStatus[];
  generatedAt: string | null;
};

export type FreeTierFacts = {
  node_pool: string | null;
  traffic_limit_gb: number | null;
  cycle_days: number | null;
  speed_limit_mbps: number | null;
  device_limit: number | null;
  monthly_reset: boolean | null;
  source: string | null;
};

export type FreeTierSummary = {
  generated_at: string | null;
  free_users: number | null;
  sampled_users: number | null;
  limit_gb_per_user: number | null;
  cycle_days: number | null;
  used_gb: number | null;
  limit_gb_total: number | null;
  remaining_gb: number | null;
  used_pct: number | null;
  near_cap_users: number | null;
  over_cap_users: number | null;
  burn_rate_gb_per_day: number | null;
  source: string | null;
};

export type FreeTierUser = {
  tg_id: number;
  username: string | null;
  display_name: string | null;
  is_active: boolean;
  current_plan_code: string | null;
  used_gb: number | null;
  limit_gb: number | null;
  remaining_gb: number | null;
  used_pct: number | null;
  state: string;
  cycle_start: string | null;
  cycle_end: string | null;
  next_reset_at: string | null;
  source: string | null;
  rollup_count: number | null;
};

export type FreeTierPayload = {
  summary: FreeTierSummary;
  facts: FreeTierFacts;
  users: FreeTierUser[];
  total: number | null;
  generatedAt: string | null;
};

function rangeBounds(range: TrafficRange): { from: string; to: string } {
  const days = range === "7d" ? 7 : range === "90d" ? 90 : 30;
  const to = new Date();
  const from = new Date(to);
  from.setUTCDate(from.getUTCDate() - days + 1);
  return { from: from.toISOString(), to: to.toISOString() };
}

export async function fetchTrafficSummary(range: TrafficRange, init?: ApiRequestInit): Promise<TrafficPayload> {
  const bounds = rangeBounds(range);
  const query = new URLSearchParams(bounds);
  const data = await apiFetch<Partial<TrafficPayload>>(`/api/admin/traffic/summary?${query.toString()}`, init);
  return {
    ok: data.ok,
    from: typeof data.from === "string" ? data.from : null,
    to: typeof data.to === "string" ? data.to : null,
    rows: Array.isArray(data.rows) ? data.rows : [],
  };
}

export async function fetchNetworkAlerts(status: string, init?: ApiRequestInit): Promise<AlertsPayload> {
  const data = await apiFetch<Partial<AlertsPayload>>(`/api/admin/alerts?status=${encodeURIComponent(status)}`, init);
  return {
    ok: data.ok,
    generated_at: typeof data.generated_at === "string" ? data.generated_at : null,
    alerts: Array.isArray(data.alerts) ? data.alerts : [],
  };
}

export async function acknowledgeAlert(id: number): Promise<NetworkAlert> {
  const data = await apiFetch<{ alert: NetworkAlert }>(`/api/admin/alerts/${id}/ack`, { method: "POST" });
  return data.alert;
}

export async function silenceAlert(id: number, minutes: number): Promise<NetworkAlert> {
  const data = await apiFetch<{ alert: NetworkAlert }>(`/api/admin/alerts/${id}/silence`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ minutes }),
  });
  return data.alert;
}

export async function fetchProviderQuotas(init?: ApiRequestInit): Promise<ProviderQuotasPayload> {
  const [configs, statuses] = await Promise.all([
    apiFetch<{ quotas?: ProviderQuotaConfig[] }>("/api/admin/provider-quotas", init),
    apiFetch<{ generated_at?: string | null; nodes?: ProviderQuotaStatus[] }>("/api/admin/provider-quotas/status", init),
  ]);
  return {
    configs: Array.isArray(configs.quotas) ? configs.quotas : [],
    statuses: Array.isArray(statuses.nodes) ? statuses.nodes : [],
    generatedAt: typeof statuses.generated_at === "string" ? statuses.generated_at : null,
  };
}

export async function fetchFreeTier(q: string, init?: ApiRequestInit): Promise<FreeTierPayload> {
  const userQuery = new URLSearchParams({ limit: "500" });
  if (q.trim()) userQuery.set("q", q.trim());
  const [summaryData, usersData] = await Promise.all([
    apiFetch<{ summary: FreeTierSummary; facts: FreeTierFacts }>("/api/admin/free-tier/summary", init),
    apiFetch<{ generated_at?: string | null; total?: number | null; facts: FreeTierFacts; users?: FreeTierUser[] }>(`/api/admin/free-tier/users?${userQuery.toString()}`, init),
  ]);
  return {
    summary: summaryData.summary,
    facts: summaryData.facts || usersData.facts,
    users: Array.isArray(usersData.users) ? usersData.users : [],
    total: typeof usersData.total === "number" && Number.isFinite(usersData.total) ? usersData.total : null,
    generatedAt: typeof usersData.generated_at === "string" ? usersData.generated_at : summaryData.summary?.generated_at || null,
  };
}
