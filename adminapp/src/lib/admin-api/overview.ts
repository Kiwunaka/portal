"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { OpsAlert, OpsOverview } from "./types";

export function fetchOpsOverview(init?: ApiRequestInit): Promise<OpsOverview> {
  return apiFetch<OpsOverview>("/api/admin/ops/overview", init);
}

export async function fetchAlerts(status = "active", init?: ApiRequestInit): Promise<OpsAlert[]> {
  const data = await apiFetch<{ alerts: OpsAlert[] }>(`/api/admin/alerts?status=${encodeURIComponent(status)}`, init);
  return data.alerts || [];
}
