"use client";

import { apiFetch } from "./client";

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
};

export type ActionIntentRequest = {
  action: string;
  target: { type: string; id: string };
  payload: Record<string, unknown>;
  endpoint: string;
  method?: "POST" | "PUT";
};

export function prepareActionIntent(
  request: Pick<ActionIntentRequest, "action" | "target" | "payload">,
): Promise<PreparedActionIntent> {
  return apiFetch<PreparedActionIntent>("/api/admin/action-intents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: request.action,
      target: request.target,
      payload: request.payload,
    }),
    timeoutMs: 15_000,
  });
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
}: {
  endpoint: string;
  payload: Record<string, unknown>;
  intent: PreparedActionIntent;
  confirmation: string;
  method?: "POST" | "PUT";
  idempotencyKey?: string;
}): Promise<AdminActionResult> {
  const confirmationHash = await confirmationSha256(confirmation);
  return apiFetch<AdminActionResult>(endpoint, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Intent-Id": intent.intent_id,
      "X-Admin-Idempotency-Key": idempotencyKey,
      "X-Admin-Confirmation-SHA256": confirmationHash,
    },
    body: JSON.stringify(payload),
    timeoutMs: 45_000,
  });
}
