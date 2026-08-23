"use client";

import { apiFetch, type ApiRequestInit } from "./client";
import type { AdminV2Envelope } from "./types";

export type AccessPlan = {
  code: string;
  label: string;
  duration_days: number;
  device_limit: number;
  is_public: boolean;
};

export type EntitlementGrantRow = {
  grant_ref: string;
  account_ref: string | null;
  source: string;
  status: string;
  grant_kind: string;
  plan_code: string | null;
  starts_at: string | null;
  expires_at: string | null;
  activated_at: string | null;
  reversed_at: string | null;
  reversal_reason: string | null;
  provider: string | null;
  order_ref: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type GiftCodeRow = {
  gift_ref: string;
  code_hint: string;
  code_sha256: string | null;
  card_type: string;
  redeemed: boolean;
  created_at: string | null;
  redeemed_at: string | null;
};

export type MoneyAccessPayload = {
  generated_at: string | null;
  authority: {
    payments: string;
    entitlements: string;
    provisioning: string;
    telemetry_confirms_payment: boolean;
  };
  claim_counts: Record<string, number>;
  grant_counts: Record<string, number>;
  outbox: Record<string, unknown>;
  access_key_counts: Record<string, number>;
  recent_grants: EntitlementGrantRow[];
  gift_codes: GiftCodeRow[];
  plans: AccessPlan[];
};

export type WheelOutcome = { kind: string; value: number; weight: number };
export type LoyaltyTier = { days: number; bonus_days: number; perk: string };
export type BonusConfiguration = {
  wheel: { preset: string; cooldown_hours: number; weights: WheelOutcome[] };
  loyalty: { enabled: boolean; tiers: LoyaltyTier[] };
};

export type ProgramApplication = {
  id: string;
  account_ref: string;
  kind: string;
  status: string;
  source_name: string | null;
  seats: number | null;
  summary: string;
  contact: string | null;
  operator_note: string | null;
  reward_days: number;
  rewarded: boolean;
  reward_grant_ref: string | null;
  created_at: string | null;
  updated_at: string | null;
  reviewed_at: string | null;
};

export async function fetchMoneyAccess(init?: ApiRequestInit): Promise<MoneyAccessPayload> {
  const response = await apiFetch<AdminV2Envelope<MoneyAccessPayload>>("/api/admin/v2/money/access", init);
  return response.data;
}

export async function fetchBonusConfiguration(init?: ApiRequestInit): Promise<BonusConfiguration> {
  const response = await apiFetch<AdminV2Envelope<BonusConfiguration>>("/api/admin/v2/growth/bonuses", init);
  return response.data;
}

export async function fetchProgramApplications(
  filters: { status?: string; kind?: string },
  init?: ApiRequestInit,
): Promise<ProgramApplication[]> {
  const query = new URLSearchParams({ limit: "200" });
  if (filters.status?.trim()) query.set("status", filters.status.trim());
  if (filters.kind?.trim()) query.set("kind", filters.kind.trim());
  const response = await apiFetch<AdminV2Envelope<{ applications?: ProgramApplication[] }>>(`/api/admin/v2/growth/programs?${query.toString()}`, init);
  return Array.isArray(response.data.applications) ? response.data.applications : [];
}
