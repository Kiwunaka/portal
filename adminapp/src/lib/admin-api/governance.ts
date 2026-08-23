import { apiFetch, apiFetchBlob, type ApiRequestInit } from "./client";
import type { AdminV2Envelope } from "./types";

export type GovernanceRole = {
  id: string;
  role_code: string;
  environment: string;
  grant_kind: "standing" | "jit" | "break_glass" | string;
  grant_reason: string | null;
  granted_by_operator_id: string | null;
  granted_at: string | null;
  expires_at: string | null;
  active: boolean;
  review_status: string;
  reviewed_by_operator_id: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  revoked_at: string | null;
  revoke_reason: string | null;
};

export type GovernanceOperator = {
  id: string;
  legacy_actor_tg_id: number | null;
  display_name: string | null;
  identity_source: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  suspended_at: string | null;
  active_roles: GovernanceRole[];
  pending_reviews: number;
  active_sessions: number;
  last_seen_at: string | null;
};

export type GovernanceSession = {
  id: string;
  environment: string;
  created_at: string | null;
  last_seen_at: string | null;
  idle_expires_at: string | null;
  absolute_expires_at: string | null;
  step_up_at: string | null;
  revoked_at: string | null;
  revoke_reason: string | null;
  active: boolean;
};

export type GovernanceOperatorDetail = {
  operator: Omit<GovernanceOperator, "active_roles" | "pending_reviews" | "active_sessions" | "last_seen_at">;
  roles: GovernanceRole[];
  sessions: GovernanceSession[];
  generated_at: string;
};

export type GovernanceAuditRow = {
  id: string;
  operator_id: string;
  operator_name: string | null;
  legacy_actor_tg_id: number | null;
  session_id: string | null;
  action: string;
  result: string;
  reason_code: string | null;
  environment: string;
  roles: string[];
  permissions: string[];
  trace_id: string | null;
  resource: { type: string; id: string | null } | null;
  command_intent_id: string | null;
  legacy_audit_id: number | null;
  created_at: string | null;
};

export type GovernancePrivacy = {
  raw_policy: { default_days: number; longer_lived_data: string; cleanup_authority: string; mode: string };
  retention: Array<{
    code: string;
    raw_retention_days: number;
    policy_source: string;
    disposition: string;
    rows: number;
    oldest_at: string | null;
    expired_backlog: number;
  }>;
  deletion_anonymization: {
    policy: {
      raw_ip_hours: number;
      full_ip_hmac_days: number;
      prefix_ip_hmac_days: number;
      disposition: string;
    };
    backlog: Record<string, number>;
  };
  diagnostic_bundles: {
    accepted_retention_days: number;
    quarantine_retention_days: number;
    incomplete_grace_days: number;
    access_audit_retention_days: number;
    uploads: number;
    retention_holds: number;
    access_audits: number;
    expired_unheld_backlog: number;
    expired_held: number;
    access_audit_unheld_backlog: number;
    access_audit_held: number;
  };
  field_inventory: Array<{
    family: string;
    fields: string[];
    classification: string;
    excluded?: string[];
  }>;
  generated_at: string;
};

export type SensitiveAccessRow = {
  grant_id: string;
  upload_id: string;
  ticket_id: number;
  actor_tg_id: number;
  actor_role: string;
  action: string;
  reason_code: string;
  expires_at: string | null;
  used_at: string | null;
  retention_hold: boolean;
  created_at: string | null;
};

export type GovernanceOverview = {
  catalog: {
    roles: Array<{ code: string; permissions: string[] }>;
    grant_kinds: string[];
    temporal_limits_minutes: Record<string, { min: number; max: number }>;
    rules: Record<string, string>;
  };
  operators: { items: GovernanceOperator[]; count: number; environment: string; generated_at: string };
  audit: { items: GovernanceAuditRow[]; count: number; generated_at: string };
  privacy: GovernancePrivacy;
  sensitive: {
    items: SensitiveAccessRow[];
    count: number;
    source_scope: string;
    generated_at: string;
  };
};

async function data<T>(path: string, init?: ApiRequestInit): Promise<T> {
  return (await apiFetch<AdminV2Envelope<T>>(path, init)).data;
}

export async function fetchGovernanceOverview(init?: ApiRequestInit): Promise<GovernanceOverview> {
  const [catalog, operators, audit, privacy, sensitive] = await Promise.all([
    data<GovernanceOverview["catalog"]>("/api/admin/v2/governance/roles", init),
    data<GovernanceOverview["operators"]>("/api/admin/v2/governance/operators?limit=200", init),
    data<GovernanceOverview["audit"]>("/api/admin/v2/governance/audit?limit=100", init),
    data<GovernancePrivacy>("/api/admin/v2/governance/privacy", init),
    data<GovernanceOverview["sensitive"]>("/api/admin/v2/governance/sensitive-access?limit=100", init),
  ]);
  return { catalog, operators, audit, privacy, sensitive };
}

export function fetchGovernanceOperator(operatorId: string, init?: ApiRequestInit): Promise<GovernanceOperatorDetail> {
  return data<GovernanceOperatorDetail>(
    `/api/admin/v2/governance/operators/${encodeURIComponent(operatorId)}`,
    init,
  );
}

export function exportGovernanceAudit(init?: ApiRequestInit): Promise<Blob> {
  return apiFetchBlob("/api/admin/v2/governance/audit/export?limit=1000", init);
}
