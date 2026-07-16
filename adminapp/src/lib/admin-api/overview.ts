"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { OpsAlert, OpsOverview } from "./types";

export type RuLatestSource = {
  status: string;
  sampled_at?: string | null;
  age_seconds?: number | null;
  threshold_seconds: number;
  reason_code: string;
};

export type RuRunSummary = {
  run_id: string;
  finished_at?: string | null;
  received_at?: string | null;
  release_verdict?: string | null;
  current_eligible?: boolean;
};

export type RuLatestStatus = RuLatestSource & {
  ok: boolean;
  generated_at: string;
  environment_verdict: string;
  environment: RuLatestSource & { verdict?: string };
  latest_received_attempt: RuRunSummary | null;
  latest_eligible_run: RuRunSummary | null;
  nodes: Array<RuLatestSource & { node_code: string }>;
};

export function fetchOpsOverview(init?: ApiRequestInit): Promise<OpsOverview> {
  return apiFetch<OpsOverview>("/api/admin/ops/overview", init);
}

export function fetchRuLatest(init?: ApiRequestInit): Promise<RuLatestStatus> {
  return apiFetch<RuLatestStatus>("/api/admin/probes/ru-origin/latest", init);
}

export async function fetchAlerts(status = "active", init?: ApiRequestInit): Promise<OpsAlert[]> {
  const data = await apiFetch<{ alerts: OpsAlert[] }>(`/api/admin/alerts?status=${encodeURIComponent(status)}`, init);
  return data.alerts || [];
}
