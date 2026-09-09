"use client";

import { CANONICAL_API_BASE_URL } from "@/lib/portal";
import { matchAdminV2Operation } from "./generated/admin-v2";
import type { AdminOperatorSessionData, AdminV2Envelope } from "./types";

const LEGACY_AUTH_STORAGE_KEYS = [
  "portal_web_session_token",
  "pokrov_admin_init_data",
  "pokrov_admin_session_token"
] as const;
const ADMIN_CSRF_HEADER = "X-Pokrov-Admin-CSRF";
const DEFAULT_TIMEOUT_MS = 15000;
const ADMIN_V2_PREFIX = "/api/admin/v2/";
let adminCsrfToken = "";

export type ApiRequestInit = RequestInit & { timeoutMs?: number };

export class AdminApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly correlationId: string | null;

  constructor(message: string, status: number, code: string | null, correlationId: string | null) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
  }
}

function getTelegramInitData(): string {
  if (typeof window === "undefined") return "";
  const tg = (window as typeof window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
  return String(tg?.initData || "").trim();
}

export function hasTelegramMiniAppIdentity(): boolean {
  return Boolean(getTelegramInitData());
}

export function purgeLegacyAdminAuthStorage(): void {
  if (typeof window === "undefined") return;
  for (const key of LEGACY_AUTH_STORAGE_KEYS) {
    try {
      window.sessionStorage?.removeItem(key);
      window.localStorage?.removeItem(key);
    } catch {
      // A blocked storage API must not bypass server session validation.
    }
  }
}

export function clearAdminSessionMemory(): void {
  adminCsrfToken = "";
}

function authHeaders(method: string): Headers {
  const headers = new Headers();
  if (!["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase()) && adminCsrfToken) {
    headers.set(ADMIN_CSRF_HEADER, adminCsrfToken);
  }
  return headers;
}

function apiBase(): string {
  const envBase = String(process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
  return (envBase || CANONICAL_API_BASE_URL || "https://api.pokrov.space").replace(/\/+$/, "");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function assertGeneratedAdminV2Route(path: string, method: string): void {
  if (!path.startsWith(ADMIN_V2_PREFIX) || matchAdminV2Operation(path, method) !== null) return;
  throw new AdminApiError(
    "Admin API v2 request is absent from the generated contract.",
    0,
    "admin_v2_contract_mismatch",
    null,
  );
}

function assertAdminV2Envelope(path: string, value: unknown): void {
  if (!path.startsWith(ADMIN_V2_PREFIX)) return;
  if (!isRecord(value)) {
    throw new AdminApiError("Admin API v2 response is not an object.", 502, "admin_v2_envelope_invalid", null);
  }
  const keys = Object.keys(value).sort();
  const meta = value.meta;
  const metaKeys = isRecord(meta) ? Object.keys(meta).sort() : [];
  if (
    keys.join(",") !== "data,meta,sources,warnings" ||
    !isRecord(meta) ||
    !["generated_at,query_ms,schema_version", "generated_at,query_ms,schema_version,trace_id"].includes(metaKeys.join(",")) ||
    typeof meta.generated_at !== "string" ||
    typeof meta.schema_version !== "string" ||
    !meta.schema_version.startsWith("admin-v2.") ||
    typeof meta.query_ms !== "number" ||
    (meta.trace_id !== undefined && meta.trace_id !== null && typeof meta.trace_id !== "string") ||
    !Array.isArray(value.sources) ||
    !value.sources.every(isRecord) ||
    !Array.isArray(value.warnings) ||
    !value.warnings.every(isRecord)
  ) {
    throw new AdminApiError(
      "Admin API v2 response does not match the generated envelope.",
      502,
      "admin_v2_envelope_invalid",
      isRecord(meta) && typeof meta.trace_id === "string" ? meta.trace_id : null,
    );
  }
}

type ParsedApiError = {
  message: string;
  code: string | null;
  correlationId: string | null;
};

function optionalErrorField(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

async function parseApiError(response: Response): Promise<ParsedApiError> {
  let body: Record<string, unknown> = {};
  try {
    const parsed = await response.json();
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      body = parsed as Record<string, unknown>;
    }
  } catch {
    // Keep the HTTP metadata even when the response body is absent or malformed.
  }

  const detail = body.detail && typeof body.detail === "object" && !Array.isArray(body.detail)
    ? (body.detail as Record<string, unknown>)
    : {};
  const v2Error = body.error && typeof body.error === "object" && !Array.isArray(body.error)
    ? (body.error as Record<string, unknown>)
    : {};
  const v2Meta = body.meta && typeof body.meta === "object" && !Array.isArray(body.meta)
    ? (body.meta as Record<string, unknown>)
    : {};
  const message =
    optionalErrorField(v2Error.message) ||
    optionalErrorField(body.detail) ||
    optionalErrorField(body.message) ||
    optionalErrorField(detail.message) ||
    `API error ${response.status}`;
  const code = optionalErrorField(v2Error.code) || optionalErrorField(body.code) || optionalErrorField(detail.code);
  const correlationId =
    optionalErrorField(body.correlation_id) ||
    optionalErrorField(body.correlationId) ||
    optionalErrorField(detail.correlation_id) ||
    optionalErrorField(detail.correlationId) ||
    optionalErrorField(v2Meta.trace_id) ||
    optionalErrorField(response.headers.get("x-correlation-id")) ||
    optionalErrorField(response.headers.get("x-request-id"));

  return { message, code, correlationId };
}

export async function apiFetch<T>(path: string, init?: ApiRequestInit): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...requestInit } = init || {};
  const method = requestInit.method || "GET";
  assertGeneratedAdminV2Route(path, method);
  const controller = new AbortController();
  const abortFromCaller = () => controller.abort();
  signal?.addEventListener("abort", abortFromCaller, { once: true });
  if (signal?.aborted) controller.abort();
  let timedOut = false;
  const timer = window.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const headers = new Headers(requestInit.headers || {});
  for (const [key, value] of authHeaders(method)) headers.set(key, value);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      ...requestInit,
      headers,
      credentials: "include",
      signal: controller.signal
    });
    if (!response.ok) {
      const parsedError = await parseApiError(response);
      throw new AdminApiError(parsedError.message, response.status, parsedError.code, parsedError.correlationId);
    }
    if (response.status === 204) return {} as T;
    const payload: unknown = await response.json();
    assertAdminV2Envelope(path, payload);
    return payload as T;
  } catch (error) {
    if (timedOut && !signal?.aborted) {
      throw new AdminApiError("Время ожидания ответа истекло. Повторите запрос.", 0, "request_timeout", null);
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
    signal?.removeEventListener("abort", abortFromCaller);
  }
}

export async function apiFetchBlob(path: string, init?: ApiRequestInit): Promise<Blob> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...requestInit } = init || {};
  const method = requestInit.method || "GET";
  assertGeneratedAdminV2Route(path, method);
  const controller = new AbortController();
  const abortFromCaller = () => controller.abort();
  signal?.addEventListener("abort", abortFromCaller, { once: true });
  if (signal?.aborted) controller.abort();
  let timedOut = false;
  const timer = window.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const headers = new Headers(requestInit.headers || {});
  for (const [key, value] of authHeaders(method)) headers.set(key, value);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      ...requestInit,
      headers,
      credentials: "include",
      signal: controller.signal,
    });
    if (!response.ok) {
      const parsedError = await parseApiError(response);
      throw new AdminApiError(parsedError.message, response.status, parsedError.code, parsedError.correlationId);
    }
    return await response.blob();
  } catch (error) {
    if (timedOut && !signal?.aborted) {
      throw new AdminApiError("Время ожидания ответа истекло. Повторите запрос.", 0, "request_timeout", null);
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
    signal?.removeEventListener("abort", abortFromCaller);
  }
}

function acceptAdminSession(
  payload: AdminV2Envelope<AdminOperatorSessionData>
): AdminV2Envelope<AdminOperatorSessionData> {
  adminCsrfToken = String(payload.data.session.csrf_token || "").trim();
  return payload;
}

export async function getCurrentAdminSession(): Promise<AdminV2Envelope<AdminOperatorSessionData>> {
  return acceptAdminSession(
    await apiFetch<AdminV2Envelope<AdminOperatorSessionData>>("/api/admin/v2/auth/me")
  );
}

export async function bootstrapAdminSession(): Promise<AdminV2Envelope<AdminOperatorSessionData>> {
  const headers = new Headers();
  const initData = getTelegramInitData();
  if (initData) headers.set("X-Telegram-Init-Data", initData);
  return acceptAdminSession(
    await apiFetch<AdminV2Envelope<AdminOperatorSessionData>>("/api/admin/v2/auth/bootstrap", {
      method: "POST",
      headers
    })
  );
}

type AdminOidcStartData = {
  mode: "login" | "step_up";
  provider: "telegram_oidc";
  auth_url: string;
  redirect_uri: string;
};

export async function startAdminOidc(
  mode: "login" | "step_up" = "login"
): Promise<AdminV2Envelope<AdminOidcStartData>> {
  return apiFetch<AdminV2Envelope<AdminOidcStartData>>(
    `/api/admin/v2/auth/oidc/start?mode=${mode}`
  );
}

export async function finishAdminOidcSession(
  code: string,
  state: string
): Promise<AdminV2Envelope<AdminOperatorSessionData>> {
  return acceptAdminSession(
    await apiFetch<AdminV2Envelope<AdminOperatorSessionData>>(
      "/api/admin/v2/auth/oidc/finish",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, state })
      }
    )
  );
}

export async function finishAdminOidcStepUp(
  code: string,
  state: string
): Promise<AdminV2Envelope<{ step_up_at: string; valid_for_seconds: number; method: "telegram_oidc" }>> {
  return apiFetch<AdminV2Envelope<{ step_up_at: string; valid_for_seconds: number; method: "telegram_oidc" }>>(
    "/api/admin/v2/auth/step-up",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, state })
    }
  );
}
