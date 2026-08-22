"use client";

import { apiFetch } from "./client";
import type { AdminV2Envelope } from "./types";

export type ActionRiskLevel = "L2" | "L3" | string;

export type ActionIntentPreview = {
  title: string;
  summary: string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  warnings: string[];
  selection?: {
    count?: number;
    without_target?: number;
    hash?: string;
  };
};

export type PreparedActionIntent = {
  ok: boolean;
  intent_id: string;
  action: string;
  target: { type: string; id: string };
  risk_level: ActionRiskLevel;
  preview: ActionIntentPreview;
  payload_hash: string;
  snapshot_hash: string;
  entity_version_hash: string;
  confirmation_challenge: string;
  confirmation_challenge_kind: string;
  expires_at: string;
};

export type AdminActionResult = {
  ok: boolean;
  status: "completed" | "failed" | "uncertain" | "executing" | string;
  action_intent_id: string;
  audit_id: number | null;
  result_code?: string;
  result?: Record<string, unknown>;
  node?: Record<string, unknown>;
  pairing_code?: string;
  gift_code?: { code: string; card_type: string; days?: number; stars?: number };
  issued?: Array<{ key: string; plan?: Record<string, unknown>; issued_at?: string }>;
};

export type ActionIntentRequest = {
  action: string;
  target: { type: string; id: string };
  payload: Record<string, unknown>;
  endpoint: string;
  method?: "POST" | "PUT" | "PATCH" | "DELETE";
  workspace?: "shift" | "incidents" | "support" | "network" | "money" | "growth" | "releases" | "governance";
};

export function prepareActionIntent(
  request: Pick<ActionIntentRequest, "action" | "target" | "payload" | "workspace">,
): Promise<PreparedActionIntent> {
  const path = request.workspace
    ? `/api/admin/v2/${request.workspace}/action-intents`
    : "/api/admin/action-intents";
  const pending = apiFetch<PreparedActionIntent | AdminV2Envelope<PreparedActionIntent>>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: request.action,
      target: request.target,
      payload: request.payload,
    }),
    timeoutMs: 15_000,
  });
  return pending.then((response) => request.workspace
    ? (response as AdminV2Envelope<PreparedActionIntent>).data
    : response as PreparedActionIntent);
}

export async function confirmationSha256(input: string): Promise<string> {
  const normalized = String(input || "").normalize("NFC").trim();
  const bytes = new TextEncoder().encode(normalized);
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
}

export async function executeAdminAction({
  endpoint,
  payload,
  intent,
  confirmation,
  method = "POST",
  idempotencyKey = globalThis.crypto.randomUUID(),
  workspace,
  action,
  target,
}: {
  endpoint: string;
  payload: Record<string, unknown>;
  intent: PreparedActionIntent;
  confirmation: string;
  method?: "POST" | "PUT" | "PATCH" | "DELETE";
  idempotencyKey?: string;
  workspace?: "shift" | "incidents" | "support" | "network" | "money" | "growth" | "releases" | "governance";
  action?: string;
  target?: { type: string; id: string };
}): Promise<AdminActionResult> {
  const confirmationHash = await confirmationSha256(confirmation);
  const path = workspace
    ? `/api/admin/v2/${workspace}/action-intents/${encodeURIComponent(intent.intent_id)}/execute`
    : endpoint;
  const body = workspace
    ? { action, target, payload }
    : payload;
  const response = await apiFetch<AdminActionResult | AdminV2Envelope<AdminActionResult>>(path, {
    method: workspace ? "POST" : method,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Intent-Id": intent.intent_id,
      "X-Admin-Idempotency-Key": idempotencyKey,
      "X-Admin-Confirmation-SHA256": confirmationHash,
    },
    body: JSON.stringify(body),
    timeoutMs: 45_000,
  });
  return workspace
    ? (response as AdminV2Envelope<AdminActionResult>).data
    : response as AdminActionResult;
}
