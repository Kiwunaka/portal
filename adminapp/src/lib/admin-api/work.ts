"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { AdminV2Envelope } from "./types";

export type OperatorTaskStatus = "open" | "in_progress" | "blocked" | "done" | "cancelled";
export type OperatorTaskPriority = "critical" | "high" | "normal" | "low";

export type OperatorTask = {
  id: string;
  environment: string;
  title: string;
  owner_operator_id: string | null;
  owner_team: string | null;
  status: OperatorTaskStatus;
  priority: OperatorTaskPriority;
  due_at: string | null;
  next_action: string | null;
  source: string;
  linked_entity: { type: string; id: string } | null;
  version: number;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ShiftQueueItem = {
  id?: number;
  title?: string;
  status?: string;
  updated_at?: string | null;
  [key: string]: unknown;
};

export type ShiftReadModel = {
  environment: string;
  operator_id: string;
  teams: string[];
  mine: OperatorTask[];
  team: OperatorTask[];
  unassigned: OperatorTask[];
  failed_commands: ShiftQueueItem[];
  tickets: ShiftQueueItem[];
  incident_work: OperatorIncident[];
  payment_review: ShiftQueueItem[];
  release_blockers: ShiftQueueItem[];
  source_failures: IncidentAlert[];
};

export type IncidentAlert = {
  id: number;
  source: string;
  severity: string;
  status: string;
  title: string;
  node_code: string | null;
  incident_id: string | null;
  version: number;
  first_seen_at: string | null;
  last_seen_at: string | null;
  acknowledged_at: string | null;
};

export type OperatorIncident = {
  id: string;
  key: string;
  environment: string;
  title: string;
  summary: string;
  severity: string;
  public_status: string;
  workflow_status: "investigating" | "identified" | "monitoring" | "resolved" | "cancelled" | string;
  version: number;
  owner_operator_id: string | null;
  owner_team: string | null;
  impact: string | null;
  started_at: string;
  ended_at: string | null;
  next_update_at: string | null;
  runbook_url: string | null;
  communications_summary: string | null;
  postmortem_status: string;
  postmortem_url: string | null;
  affected_node_codes: string[];
  compensation: {
    days: number;
    impacted_accounts: number;
    granted_accounts: number;
    started_at: string | null;
    completed_at: string | null;
  };
  created_at: string;
  updated_at: string;
};

export type OperatorIncidentDetail = OperatorIncident & {
  timeline: Array<{
    id: string;
    version: number;
    event_type: string;
    from_status: string | null;
    to_status: string | null;
    note: string | null;
    actor_operator_id: string | null;
    created_at: string;
  }>;
  linked_entities: Array<{
    id: string;
    type: string;
    entity_id: string;
    label: string | null;
    created_at: string;
  }>;
  alerts: IncidentAlert[];
  follow_up_tasks: OperatorTask[];
};

export async function fetchShift(init?: ApiRequestInit): Promise<ShiftReadModel> {
  const response = await apiFetch<AdminV2Envelope<ShiftReadModel>>("/api/admin/v2/shift", init);
  return response.data;
}

export async function fetchOperatorTasks(init?: ApiRequestInit): Promise<OperatorTask[]> {
  const response = await apiFetch<AdminV2Envelope<{ items: OperatorTask[]; count: number }>>(
    "/api/admin/v2/tasks",
    init,
  );
  return response.data.items;
}

export async function fetchIncidents(init?: ApiRequestInit): Promise<OperatorIncident[]> {
  const response = await apiFetch<AdminV2Envelope<{ items: OperatorIncident[]; count: number }>>(
    "/api/admin/v2/incidents",
    init,
  );
  return response.data.items;
}

export async function fetchIncidentDetail(
  incidentId: string,
  init?: ApiRequestInit,
): Promise<OperatorIncidentDetail> {
  const response = await apiFetch<AdminV2Envelope<OperatorIncidentDetail>>(
    `/api/admin/v2/incidents/${encodeURIComponent(incidentId)}`,
    init,
  );
  return response.data;
}
