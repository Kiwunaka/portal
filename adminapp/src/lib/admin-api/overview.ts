"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { AdminV2Envelope, OpsOverview } from "./types";

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

export async function fetchOpsOverview(init?: ApiRequestInit): Promise<OpsOverview> {
  const response = await apiFetch<AdminV2Envelope<OpsOverview>>("/api/admin/v2/shift/overview", init);
  return response.data;
}

export async function fetchRuLatest(init?: ApiRequestInit): Promise<RuLatestStatus> {
  const response = await apiFetch<AdminV2Envelope<RuLatestStatus>>("/api/admin/v2/network/ru/latest", init);
  return response.data;
}
