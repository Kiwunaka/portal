"use client";

import { CANONICAL_API_BASE_URL } from "@/lib/portal";
import type { AdminSessionPayload } from "./types";

const WEB_SESSION_TOKEN_KEY = "portal_web_session_token";
const ADMIN_INIT_DATA_KEY = "pokrov_admin_init_data";
const ADMIN_SESSION_TOKEN_KEY = "pokrov_admin_session_token";
const DEFAULT_TIMEOUT_MS = 15000;

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

function getCookieValue(name: string): string {
  if (typeof document === "undefined") return "";
  const prefix = `${encodeURIComponent(name)}=`;
  for (const part of document.cookie.split(";")) {
    const item = part.trim();
    if (item.startsWith(prefix)) return decodeURIComponent(item.slice(prefix.length));
  }
  return "";
}

function getStoredValue(key: string): string {
  if (typeof window === "undefined") return "";
  try {
    return String(window.localStorage?.getItem(key) || "").trim();
  } catch {
    return "";
  }
}

function getAdminInitDataFromStorage(): string {
  if (typeof window === "undefined") return "";
  try {
    const sessionValue = String(window.sessionStorage?.getItem(ADMIN_INIT_DATA_KEY) || "").trim();
    if (sessionValue) return sessionValue;
  } catch {
    // Ignore blocked storage.
  }
  try {
    const legacyValue = String(window.localStorage?.getItem(ADMIN_INIT_DATA_KEY) || "").trim();
    if (!legacyValue) return "";
    window.sessionStorage?.setItem(ADMIN_INIT_DATA_KEY, legacyValue);
    window.localStorage?.removeItem(ADMIN_INIT_DATA_KEY);
    return legacyValue;
  } catch {
    return "";
  }
}

function getTelegramInitData(): string {
  if (typeof window === "undefined") return "";
  const tg = (window as typeof window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
  return String(tg?.initData || getAdminInitDataFromStorage() || "").trim();
}

function getAdminSessionToken(): string {
  if (typeof window === "undefined") return "";
  try {
    return String(window.sessionStorage?.getItem(ADMIN_SESSION_TOKEN_KEY) || "").trim();
  } catch {
    return "";
  }
}

function getWebSessionToken(): string {
  return getStoredValue(WEB_SESSION_TOKEN_KEY) || getCookieValue(WEB_SESSION_TOKEN_KEY);
}

function authHeaders(): Headers {
  const headers = new Headers();
  const token = getAdminSessionToken() || getWebSessionToken();
  const initData = getTelegramInitData();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
    headers.set("X-Web-Auth-Token", token);
  }
  if (initData) headers.set("X-Telegram-Init-Data", initData);
  return headers;
}

function apiBase(): string {
  const envBase = String(process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
  return (envBase || CANONICAL_API_BASE_URL || "https://api.pokrov.space").replace(/\/+$/, "");
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
  const message =
    optionalErrorField(body.detail) ||
    optionalErrorField(body.message) ||
    optionalErrorField(detail.message) ||
    `API error ${response.status}`;
  const code = optionalErrorField(body.code) || optionalErrorField(detail.code);
  const correlationId =
    optionalErrorField(body.correlation_id) ||
    optionalErrorField(body.correlationId) ||
    optionalErrorField(detail.correlation_id) ||
    optionalErrorField(detail.correlationId) ||
    optionalErrorField(response.headers.get("x-correlation-id")) ||
    optionalErrorField(response.headers.get("x-request-id"));

  return { message, code, correlationId };
}

export function saveAdminInitData(value: string): void {
  if (typeof window === "undefined") return;
  const clean = String(value || "").trim();
  if (!clean) return;
  try {
    window.sessionStorage.setItem(ADMIN_INIT_DATA_KEY, clean);
    window.localStorage.removeItem(ADMIN_INIT_DATA_KEY);
  } catch {
    // Auth gate will stay visible if storage is unavailable.
  }
}

export function clearAdminInitData(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(ADMIN_INIT_DATA_KEY);
    window.localStorage.removeItem(ADMIN_INIT_DATA_KEY);
  } catch {
    // Ignore blocked storage.
  }
}

export function saveAdminSessionToken(token: string): void {
  if (typeof window === "undefined") return;
  const clean = String(token || "").trim();
  if (!clean) return;
  try {
    window.sessionStorage.setItem(ADMIN_SESSION_TOKEN_KEY, clean);
  } catch {
    // Auth gate will stay visible if storage is unavailable.
  }
}

export function clearAdminSessionToken(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(ADMIN_SESSION_TOKEN_KEY);
  } catch {
    // Ignore blocked storage.
  }
}

export function hasAdminAuthMaterial(): boolean {
  return Boolean(getAdminSessionToken() || getWebSessionToken() || getTelegramInitData());
}

export async function apiFetch<T>(path: string, init?: ApiRequestInit): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...requestInit } = init || {};
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const headers = new Headers(requestInit.headers || {});
  for (const [key, value] of authHeaders()) headers.set(key, value);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      ...requestInit,
      headers,
      credentials: "include",
      signal: signal || controller.signal
    });
    if (!response.ok) {
      const parsedError = await parseApiError(response);
      throw new AdminApiError(parsedError.message, response.status, parsedError.code, parsedError.correlationId);
    }
    if (response.status === 204) return {} as T;
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timer);
  }
}

export async function apiFetchBlob(path: string, init?: ApiRequestInit): Promise<Blob> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, signal, ...requestInit } = init || {};
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const headers = new Headers(requestInit.headers || {});
  for (const [key, value] of authHeaders()) headers.set(key, value);
  try {
    const response = await fetch(`${apiBase()}${path}`, {
      ...requestInit,
      headers,
      credentials: "include",
      signal: signal || controller.signal,
    });
    if (!response.ok) {
      const parsedError = await parseApiError(response);
      throw new AdminApiError(parsedError.message, response.status, parsedError.code, parsedError.correlationId);
    }
    return await response.blob();
  } finally {
    window.clearTimeout(timer);
  }
}

export function createAdminSession(): Promise<AdminSessionPayload> {
  return apiFetch<AdminSessionPayload>("/api/admin/auth/session", { method: "POST" });
}
