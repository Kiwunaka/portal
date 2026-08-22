"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { AdminActionResult } from "./actions";
import type { AdminV2Envelope } from "./types";

export type ReleaseEvidenceStatus =
  | "PASS"
  | "FAIL"
  | "MANUAL_OWNER_TEST"
  | "OPERATOR_ATTESTED"
  | "SKIPPED_BY_OWNER"
  | "SKIPPED_BY_OPERATOR"
  | "BLOCKED_BY_ACCESS"
  | "NOT_REQUESTED"
  | "MISSING"
  | string;

export type ReleaseCandidateSummary = {
  candidate_id: string;
  component: string;
  version: string;
  revision: string;
  artifact_sha256: string;
  descriptor_sha256: string;
  imported_at: string | null;
  age_seconds: number | null;
};

export type ReleaseCandidatePage = {
  items: ReleaseCandidateSummary[];
  next_cursor: string | null;
  limit: number;
};

export type ReleaseEvidenceCheck = {
  origin: "current" | "brain" | "ru" | string;
  check_name: string;
  required: boolean;
  status: ReleaseEvidenceStatus;
  observed_at: string | null;
  evidence_ref: string | null;
  evidence_sha256: string | null;
  ru_probe_run_id: string | null;
  detail: Record<string, unknown>;
  reason: string;
};

export type ReleaseOriginReadiness = {
  origin: "current" | "brain" | "ru" | string;
  status: ReleaseEvidenceStatus;
  checks: ReleaseEvidenceCheck[];
  diagnostics: ReleaseEvidenceCheck[];
};

export type ReleaseReadiness = {
  candidate: ReleaseCandidateSummary;
  candidate_id: string;
  required_check_matrix_version: number;
  status: ReleaseEvidenceStatus;
  ready: boolean;
  generated_at: string | null;
  origins: ReleaseOriginReadiness[];
};

export async function fetchReleaseCandidates(init?: ApiRequestInit): Promise<ReleaseCandidatePage> {
  const response = await apiFetch<AdminV2Envelope<ReleaseCandidatePage>>(
    "/api/admin/v2/releases/candidates?limit=50",
    init,
  );
  return response.data;
}

export type ReleaseGateMatrix = {
  status: ReleaseEvidenceStatus;
  ready: boolean;
  origin_readiness_status: ReleaseEvidenceStatus;
  checks: Array<{ check_name: string; status: ReleaseEvidenceStatus }>;
};

export type ReleaseRolloutState = {
  candidate_id: string;
  candidate_version?: string;
  platform: "android" | "windows" | string;
  status: string;
  rollout_percent: number;
  paused: boolean;
  min_supported_version?: string | null;
  observation_started_at?: string | null;
  observation_ends_at?: string | null;
  observation_closed_at?: string | null;
  previous_candidate_id?: string | null;
  rollback_candidate_id?: string | null;
  thresholds?: Record<string, number>;
  updated_at?: string | null;
};

export type ReleaseAdoption = {
  window_days: number;
  window_start: string | null;
  authority: string;
  cohorts: Array<{
    platform: string;
    app_version: string;
    observed_installations: number;
    last_seen_at: string | null;
    share_percent: number;
  }>;
  platform_totals: Record<string, number>;
};

export type ReleaseCockpit = {
  candidate: ReleaseCandidateSummary;
  components: Array<{
    candidate_id: string;
    component: string;
    version: string;
    revision: string;
    artifact_sha256: string;
    descriptor_sha256: string;
    imported_at: string | null;
  }>;
  readiness: ReleaseReadiness;
  gate_matrix: ReleaseGateMatrix;
  rollout: {
    states: ReleaseRolloutState[];
    active_by_platform: Record<string, string>;
    source: string;
  };
  adoption: ReleaseAdoption;
  health: { groups?: Array<Record<string, unknown>>; [key: string]: unknown };
  health_gate: {
    status: ReleaseEvidenceStatus;
    reason: string;
    thresholds: Record<string, number>;
    groups: Array<Record<string, unknown>>;
    breaches?: Array<Record<string, unknown>>;
  };
  support_delta: {
    authority: string;
    current: number;
    previous: number;
    delta: number;
    window_hours: number;
  };
  known_issues: Array<Record<string, unknown>>;
  generated_at: string | null;
};

export async function fetchReleaseCockpit(
  candidateId: string,
  init?: ApiRequestInit,
): Promise<ReleaseCockpit> {
  const response = await apiFetch<AdminV2Envelope<ReleaseCockpit>>(
    `/api/admin/v2/releases/candidates/${encodeURIComponent(candidateId)}/cockpit?hours=24`,
    init,
  );
  return response.data;
}

export async function fetchReleaseAdoption(init?: ApiRequestInit): Promise<ReleaseAdoption> {
  const response = await apiFetch<AdminV2Envelope<ReleaseAdoption>>(
    "/api/admin/v2/releases/adoption?days=30",
    init,
  );
  return response.data;
}

export function fetchActionIntentStatus(
  intentId: string,
  init?: ApiRequestInit,
): Promise<AdminActionResult> {
  return apiFetch<AdminV2Envelope<AdminActionResult>>(
    `/api/admin/v2/growth/action-intents/${encodeURIComponent(intentId)}`,
    init,
  ).then((response) => response.data);
}

export type BroadcastDeliverySummary = {
  campaign_intent_id: string;
  recipients: number;
  delivered: number;
  failed: number;
  retryable_failed: number;
  terminal_failed: number;
  attempts: number;
  reason_counts: Record<string, number>;
  average_duration_ms: number | null;
  first_started_at: string | null;
  last_finished_at: string | null;
  freshness_seconds: number | null;
};

export async function fetchBroadcastDelivery(
  intentId: string,
  init?: ApiRequestInit,
): Promise<BroadcastDeliverySummary> {
  const data = await apiFetch<AdminV2Envelope<BroadcastDeliverySummary>>(
    `/api/admin/v2/growth/broadcasts/${encodeURIComponent(intentId)}/delivery`,
    init,
  );
  return data.data;
}

export type NewsDraftRow = {
  id: number;
  source_name: string;
  source_url: string;
  source_title: string;
  source_published_at: string | null;
  status: "pending" | "approved" | string;
  live_update_id: number | null;
  discovered_at: string | null;
  reviewed_at: string | null;
};

export type NewsDraftRun = {
  run_id: string;
  status: string;
  sources_total: number;
  sources_succeeded: number;
  sources_failed: number;
  candidates_seen: number;
  drafts_created: number;
  duplicates_skipped: number;
  duration_ms: number | null;
  failure_code: string | null;
  started_at: string | null;
  finished_at: string | null;
};

export type NewsDraftPage = {
  worker: {
    enabled: boolean;
    configuration_state: string;
    interval_seconds: number | null;
    sources: string[];
  };
  counts: Record<string, number>;
  latest_run: NewsDraftRun | null;
  drafts: NewsDraftRow[];
  freshness_at: string | null;
};

export async function fetchNewsDrafts(init?: ApiRequestInit): Promise<NewsDraftPage> {
  const response = await apiFetch<AdminV2Envelope<NewsDraftPage>>(
    "/api/admin/v2/growth/news-drafts?status=all&limit=100",
    init,
  );
  return response.data;
}
