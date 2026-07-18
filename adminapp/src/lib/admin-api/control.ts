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
