"use client";

import { apiFetch, type ApiRequestInit } from "./client";

export type NodeLifecycleFilter = "all" | "enabled" | "draining" | "disabled";
export type NodeFreshnessFilter = "all" | "fresh" | "stale" | "missing";
export type NodeAlertFilter = "all" | "with" | "without";
export type NodeDetailTab = "overview" | "ru" | "load" | "clients" | "transport" | "alerts" | "technical";
export type RuHistoryRange = "24h" | "7d" | "30d" | "180d";

export type RuSourceStatus =
  | "ok"
  | "degraded"
  | "failed"
  | "stale"
  | "unavailable"
  | "missing"
  | "BLOCKED_BY_ACCESS"
  | "not_in_scope";

export type RuStageStatus = "pass" | "fail" | "not_run" | "not_applicable";
export type RuExecutionStatus = "completed" | "partial" | "runner_error" | "blocked_by_access";
export type RuVerdict = "pass" | "fail" | "incomplete" | "superseded_manifest" | "blocked_by_access";

export type NodeTransportProfile = {
  name: string;
  enabled: boolean;
  kind: string;
  port: number | null;
  has_inbound?: boolean;
};

export type NodeListRow = {
  code: string;
  name: string | null;
  country_code?: string | null;
  enabled: boolean;
  accepting_new_clients: boolean;
  is_draining: boolean;
  mapped_users: number | null;
  is_healthy: boolean | null;
  health_score: number | null;
  capacity_state: string | null;
  capacity_reject_reason: string | null;
  cpu_percent: number | null;
  network_utilization_percent: number | null;
  provisioned_clients_count: number | null;
  online_connections_hint: number | null;
  freshness_status: string | null;
  freshness_age_seconds: number | null;
  last_health_at?: string | null;
  hoster_family: string | null;
  hoster_asn: string | null;
  subnet: string | null;
  alert_kinds: string[];
  transport_profiles: NodeTransportProfile[];
};

export type RuStageResult = {
  status: RuStageStatus;
  latency_ms: number | null;
};

export type RuTargetSummary = {
  target_id: string;
  target_kind: string;
  scope: string;
  node_code: string | null;
  observed_at: string | null;
  overall_status: string;
  current_eligible: boolean;
  ineligible_reason: string | null;
  reason_code: string | null;
  stages: {
    dns: RuStageResult;
    tcp: RuStageResult;
    tls: RuStageResult;
    http_large_body: RuStageResult;
    transport_handshake: RuStageResult;
  };
  address_family_status: { ipv4: RuStageStatus; ipv6: RuStageStatus };
  transport: {
    profile: string;
    probe_mode: string;
    handshake_status: RuStageStatus;
    classification: string;
  };
};

export type RuRunSummary = {
  run_db_id: number;
  run_id: string;
  origin: "ru";
  probe_host_id: string;
  probe_host_label: string;
  runner_version: string;
  started_at: string | null;
  finished_at: string | null;
  received_at: string | null;
  manifest_revision: string;
  execution_status: RuExecutionStatus;
  evidence_code: string | null;
  environment_verdict: string;
  release_verdict: RuVerdict;
  current_eligible: boolean;
  ineligible_reason: string | null;
  google_reachable: boolean | null;
  xhttp_alive: boolean | null;
  hysteria_alive: boolean | null;
  server_reason: string | null;
  server_summary: string | null;
  targets?: RuTargetSummary[];
};

export type SourceSnapshot<TDetails = Record<string, unknown>> = {
  status: RuSourceStatus;
  sampled_at: string | null;
  age_seconds: number | null;
  threshold_seconds: number;
  reason_code: string;
  details: TDetails;
};

export type RuNodeStatus = Omit<SourceSnapshot, "details"> & {
  node_code: string;
  run_id: string | null;
  target: RuTargetSummary | null;
};

export type RuLatest = Omit<SourceSnapshot, "details"> & {
  ok: boolean;
  generated_at: string;
  environment_verdict: string;
  environment: Omit<SourceSnapshot, "details"> & { verdict?: string };
  latest_received_attempt: RuRunSummary | null;
  latest_eligible_run: RuRunSummary | null;
  eligible_run?: RuRunSummary | null;
  nodes: RuNodeStatus[];
};

export type RuRunHistory = {
  items: RuRunSummary[];
  next_cursor: string | null;
  limit: number;
};

export type RuUploaderHeartbeat = {
  probe_host_id: string;
  observed_at: string | null;
  received_at: string | null;
  service_version: string;
  pending_count: number;
  blocked_count: number;
  quarantine_count: number;
  oldest_pending_at: string | null;
  archive_write_ok: boolean;
  disk_free_bytes: number | null;
  disk_state: string;
  last_error_code: string | null;
};

export type RuUploaderStatus = Omit<SourceSnapshot, "details"> & {
  ok: boolean;
  generated_at: string;
  heartbeat: RuUploaderHeartbeat | null;
};

type BrainDetails = {
  cpu_percent?: number | null;
  memory_used_mb?: number | null;
  memory_total_mb?: number | null;
  disk_used_gb?: number | null;
  disk_total_gb?: number | null;
  network_rx_mbps?: number | null;
  network_tx_mbps?: number | null;
  network_total_mbps?: number | null;
  panel_latency_ms?: number | null;
  panel_error_rate?: number | null;
  probe_stage?: string | null;
  probe_error_kind?: string | null;
  probe_classification?: string | null;
};

type RuntimeDetails = {
  source?: string | null;
  provisioned_clients_count?: number | null;
  online_connections_hint?: number | null;
  network_rx_mbps_1m?: number | null;
  network_tx_mbps_1m?: number | null;
  network_rx_mbps_5m?: number | null;
  network_tx_mbps_5m?: number | null;
  capacity_score?: number | null;
  capacity_state?: string | null;
  reject_reason?: string | null;
};

type ObserverDetails = {
  last_batch_id?: string | null;
  unmatched_count?: number | null;
  parse_error_count?: number | null;
};

export type NodeObservability = {
  ok: boolean;
  generated_at: string;
  node: {
    code: string;
    name: string;
    hoster_family: string | null;
    hoster_asn: string | null;
    subnet: string | null;
    weight: number | null;
  };
  lifecycle: {
    enabled: boolean;
    accepting_new_clients: boolean;
    is_draining: boolean;
    mapped_users: number | null;
  };
  capacity: {
    state: string;
    score: number | null;
    reject_reason: string | null;
    tx_mbps: number | null;
    tx_ratio: number | null;
    capacity_mbps: number | null;
    provisioned_clients_count: number | null;
    online_connections_hint: number | null;
  };
  sources: {
    brain_metrics: SourceSnapshot<BrainDetails>;
    runtime: SourceSnapshot<RuntimeDetails>;
    observer: SourceSnapshot<ObserverDetails>;
    ru_origin: RuNodeStatus;
  };
  network: {
    ipv4_health: string | null;
    ipv6_health: string | null;
    dataplane_ok: boolean | null;
    dataplane_rtt_ms: number | null;
    packet_loss_percent: number | null;
    tcp_retrans_percent: number | null;
    probe_classification: string | null;
    last_probe_stage: string | null;
    last_probe_error_kind: string | null;
  };
  transports: NodeTransportProfile[];
  ru: { latest: RuNodeStatus; history: RuRunHistory };
  alerts: Array<{
    id: number;
    fingerprint: string;
    source: string;
    severity: string;
    status: string;
    title: string;
    first_seen_at: string | null;
    last_seen_at: string | null;
    resolved_at: string | null;
    acknowledged_at: string | null;
    silence_until: string | null;
  }>;
};

export async function fetchNodeList(init?: ApiRequestInit): Promise<NodeListRow[]> {
  const payload = await apiFetch<{ nodes: NodeListRow[] }>("/api/admin/nodes/health", init);
  return Array.isArray(payload.nodes) ? payload.nodes : [];
}

export function fetchRuLatest(init?: ApiRequestInit): Promise<RuLatest> {
  return apiFetch<RuLatest>("/api/admin/probes/ru-origin/latest", init);
}

export function fetchNodeObservability(nodeCode: string, init?: ApiRequestInit): Promise<NodeObservability> {
  return apiFetch<NodeObservability>(`/api/admin/nodes/${encodeURIComponent(nodeCode)}/observability`, init);
}

const RANGE_SECONDS: Record<RuHistoryRange, number> = {
  "24h": 24 * 60 * 60,
  "7d": 7 * 24 * 60 * 60,
  "30d": 30 * 24 * 60 * 60,
  "180d": 180 * 24 * 60 * 60
};

export function fetchRuHistory(nodeCode: string, range: RuHistoryRange, init?: ApiRequestInit): Promise<RuRunHistory> {
  const query = new URLSearchParams();
  query.set("node_code", nodeCode);
  query.set("from", new Date(Date.now() - RANGE_SECONDS[range] * 1000).toISOString());
  query.set("limit", "50");
  return apiFetch<RuRunHistory>(`/api/admin/probes/ru-origin/runs?${query.toString()}`, init);
}

export function fetchRuUploaderStatus(init?: ApiRequestInit): Promise<RuUploaderStatus> {
  return apiFetch<RuUploaderStatus>("/api/admin/probes/ru-origin/uploader-status", init);
}
