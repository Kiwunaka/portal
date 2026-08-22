"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { AdminV2Envelope } from "./types";

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
  version: number;
  fingerprint: string;
  source: string;
  severity: string;
  status: string;
  title: string;
  body: string | null;
  node_code: string | null;
  tg_id: number | null;
  key_id: number | null;
  incident_id: string | null;
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

export type EmergencyCatalogSnapshot = {
  snapshot_id: string;
  catalog_version: string;
  source_revision: string;
  status: string;
  candidate_count: number;
  healthy_count: number;
  active_endpoint_count: number;
  rejection_code: string | null;
  operator_approved: boolean;
  issued_at: string | null;
  expires_at: string | null;
  activated_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type EmergencyCatalogStatus = {
  generated_at: string | null;
  worker: {
    enabled: boolean;
    configuration_state: "ready" | "disabled" | "invalid" | string;
    interval_seconds: number | null;
    probe_concurrency: number | null;
  };
  snapshot_counts: Record<string, number>;
  active: EmergencyCatalogSnapshot | null;
  distribution: EmergencyCatalogSnapshot | null;
  probe_summary: {
    snapshot_id: string | null;
    pending: number;
    healthy: number;
    unavailable: number;
    total: number;
  };
  rollback_candidates: Array<{
    snapshot_id: string;
    catalog_version: string;
    endpoint_count: number;
    activated_at: string | null;
  }>;
  snapshots: EmergencyCatalogSnapshot[];
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
  const response = await apiFetch<AdminV2Envelope<Partial<TrafficPayload>>>(`/api/admin/v2/network/traffic?${query.toString()}`, init);
  const data = response.data;
  return {
    ok: data.ok,
    from: typeof data.from === "string" ? data.from : null,
    to: typeof data.to === "string" ? data.to : null,
    rows: Array.isArray(data.rows) ? data.rows : [],
  };
}

export async function fetchNetworkAlerts(status: string, init?: ApiRequestInit): Promise<AlertsPayload> {
  const response = await apiFetch<AdminV2Envelope<{ generated_at?: string | null; items?: NetworkAlert[] }>>(`/api/admin/v2/network/alerts?status=${encodeURIComponent(status)}`, init);
  const data = response.data;
  return {
    generated_at: typeof data.generated_at === "string" ? data.generated_at : null,
    alerts: Array.isArray(data.items) ? data.items : [],
  };
}

export async function fetchProviderQuotas(init?: ApiRequestInit): Promise<ProviderQuotasPayload> {
  const response = await apiFetch<AdminV2Envelope<{ generated_at?: string | null; configs?: ProviderQuotaConfig[]; statuses?: ProviderQuotaStatus[] }>>("/api/admin/v2/network/providers", init);
  const data = response.data;
  return {
    configs: Array.isArray(data.configs) ? data.configs : [],
    statuses: Array.isArray(data.statuses) ? data.statuses : [],
    generatedAt: typeof data.generated_at === "string" ? data.generated_at : null,
  };
}

export async function fetchFreeTier(q: string, init?: ApiRequestInit): Promise<FreeTierPayload> {
  const userQuery = new URLSearchParams({ limit: "500" });
  if (q.trim()) userQuery.set("q", q.trim());
  const response = await apiFetch<AdminV2Envelope<{ generated_at?: string | null; summary: FreeTierSummary; facts: FreeTierFacts; total?: number | null; users?: FreeTierUser[] }>>(`/api/admin/v2/money/free-archive?${userQuery.toString()}`, init);
  const data = response.data;
  return {
    summary: data.summary,
    facts: data.facts,
    users: Array.isArray(data.users) ? data.users : [],
    total: typeof data.total === "number" && Number.isFinite(data.total) ? data.total : null,
    generatedAt: typeof data.generated_at === "string" ? data.generated_at : data.summary?.generated_at || null,
  };
}

export async function fetchEmergencyCatalogStatus(init?: ApiRequestInit): Promise<EmergencyCatalogStatus> {
  const response = await apiFetch<AdminV2Envelope<EmergencyCatalogStatus>>("/api/admin/v2/network/emergency", init);
  return response.data;
}
