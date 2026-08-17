"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { AdminActionResult } from "./actions";

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

export function fetchReleaseCandidates(init?: ApiRequestInit): Promise<ReleaseCandidatePage> {
  return apiFetch<ReleaseCandidatePage>("/api/admin/releases/candidates?limit=50", init);
}

export function fetchReleaseReadiness(
  candidateId: string,
  init?: ApiRequestInit,
): Promise<ReleaseReadiness> {
  return apiFetch<ReleaseReadiness>(
    `/api/admin/releases/${encodeURIComponent(candidateId)}/readiness`,
    init,
  );
}

export function fetchActionIntentStatus(
  intentId: string,
  init?: ApiRequestInit,
): Promise<AdminActionResult> {
  return apiFetch<AdminActionResult>(
    `/api/admin/action-intents/${encodeURIComponent(intentId)}`,
    init,
  );
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
  const data = await apiFetch<{ ok: boolean } & BroadcastDeliverySummary>(
    `/api/admin/broadcasts/${encodeURIComponent(intentId)}/delivery`,
    init,
  );
  return data;
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

export function fetchNewsDrafts(init?: ApiRequestInit): Promise<NewsDraftPage> {
  return apiFetch<NewsDraftPage>("/api/admin/news-drafts?status=all&limit=100", init);
}
