"use client";

import { apiFetch } from "@/lib/admin-api/client";
import type { AdminOperatorSessionData, AdminV2Envelope } from "@/lib/admin-api/types";

export type OperatorFrontendIdentity = {
  app: string;
  version: string;
  frontend_commit: string;
  built_at: string;
  source_state: "clean" | "dirty" | "unknown";
  route_manifest_hash: string;
  expected_api_schema: string;
  canonical_domain: string;
};

export type OperatorApiIdentity = {
  app: string;
  api_schema: string;
  portal_commit: string | null;
  deployed_at: string | null;
  db_schema: string | null;
  active_client_release: string | null;
  core_release: string | null;
  expected_frontend_app: string;
};

export type OperatorShellIdentity = {
  state: "ready" | "partial" | "mismatch";
  session: AdminOperatorSessionData;
  frontend: OperatorFrontendIdentity | null;
  api: OperatorApiIdentity | null;
  mismatches: string[];
  warnings: string[];
};

export type OperatorSessionInventoryItem = {
  id: string;
  current: boolean;
  created_at: string;
  last_seen_at: string;
  idle_expires_at: string;
  absolute_expires_at: string;
  step_up_at: string | null;
  revoked_at: string | null;
  revoke_reason: string | null;
};

function record(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function requiredString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function optionalString(value: unknown): string | null {
  return value === null || value === undefined ? null : requiredString(value);
}

function frontendIdentity(value: unknown): OperatorFrontendIdentity | null {
  const row = record(value);
  if (!row || row.schema !== "pokrov-operator-build-v1") return null;
  const app = requiredString(row.app);
  const version = requiredString(row.version);
  const frontendCommit = requiredString(row.frontend_commit);
  const builtAt = requiredString(row.built_at);
  const sourceState = requiredString(row.source_state);
  const routeManifestHash = requiredString(row.route_manifest_hash);
  const expectedApiSchema = requiredString(row.expected_api_schema);
  const canonicalDomain = requiredString(row.canonical_domain);
  if (
    !app
    || !version
    || !frontendCommit
    || !builtAt
    || !Number.isFinite(Date.parse(builtAt))
    || !sourceState
    || !["clean", "dirty", "unknown"].includes(sourceState)
    || !routeManifestHash
    || !expectedApiSchema
    || !canonicalDomain
  ) return null;
  return {
    app,
    version,
    frontend_commit: frontendCommit,
    built_at: builtAt,
    source_state: sourceState as OperatorFrontendIdentity["source_state"],
    route_manifest_hash: routeManifestHash,
    expected_api_schema: expectedApiSchema,
    canonical_domain: canonicalDomain
  };
}

function apiIdentity(value: unknown): OperatorApiIdentity | null {
  const row = record(value);
  if (!row) return null;
  const app = requiredString(row.app);
  const apiSchema = requiredString(row.api_schema);
  const expectedFrontendApp = requiredString(row.expected_frontend_app);
  if (!app || !apiSchema || !expectedFrontendApp) return null;
  return {
    app,
    api_schema: apiSchema,
    portal_commit: optionalString(row.portal_commit),
    deployed_at: optionalString(row.deployed_at),
    db_schema: optionalString(row.db_schema),
    active_client_release: optionalString(row.active_client_release),
    core_release: optionalString(row.core_release),
    expected_frontend_app: expectedFrontendApp
  };
}

async function loadFrontendIdentity(signal?: AbortSignal): Promise<OperatorFrontendIdentity> {
  const response = await fetch("/__build.json", {
    credentials: "same-origin",
    cache: "no-store",
    signal
  });
  if (!response.ok) throw new Error(`operator_build_identity_${response.status}`);
  const identity = frontendIdentity(await response.json());
  if (!identity) throw new Error("operator_build_identity_invalid");
  return identity;
}

export async function loadOperatorShellIdentity(
  sessionEnvelope: AdminV2Envelope<AdminOperatorSessionData>,
  signal?: AbortSignal
): Promise<OperatorShellIdentity> {
  const [frontendResult, apiResult] = await Promise.allSettled([
    loadFrontendIdentity(signal),
    apiFetch<AdminV2Envelope<OperatorApiIdentity>>("/api/admin/v2/meta", { signal })
  ]);
  const frontend = frontendResult.status === "fulfilled" ? frontendResult.value : null;
  const api = apiResult.status === "fulfilled" ? apiIdentity(apiResult.value.data) : null;
  const warnings = [
    ...(frontend ? [] : ["frontend_identity_unavailable"]),
    ...(api ? [] : ["api_identity_unavailable"]),
    ...(apiResult.status === "fulfilled"
      ? apiResult.value.warnings.map((warning) => warning.field || warning.code).filter(Boolean)
      : [])
  ];
  const mismatches: string[] = [];
  if (frontend && api) {
    if (frontend.app !== api.expected_frontend_app) mismatches.push("frontend_app_mismatch");
    if (frontend.expected_api_schema !== api.api_schema) mismatches.push("api_schema_mismatch");
    if (sessionEnvelope.meta.schema_version !== api.api_schema) mismatches.push("session_schema_mismatch");
  }
  return {
    state: mismatches.length ? "mismatch" : warnings.length ? "partial" : "ready",
    session: sessionEnvelope.data,
    frontend,
    api,
    mismatches,
    warnings
  };
}

export async function loadOperatorSessionInventory(
  signal?: AbortSignal
): Promise<{ items: OperatorSessionInventoryItem[]; count: number }> {
  const envelope = await apiFetch<AdminV2Envelope<{ items: OperatorSessionInventoryItem[]; count: number }>>(
    "/api/admin/v2/auth/sessions",
    { signal }
  );
  return envelope.data;
}
