"use client";

import {
  authByTelegramWebLogin,
  clearWebSessionToken,
  consumeCabinetHandoffTokenFromUrl,
  consumeWebSessionTokenFromUrl,
  finishTelegramOidcLogin,
  fetchAuthSession,
  fetchDashboard,
  fetchUser,
  hasWebSessionToken,
  setWebSessionToken,
  startTelegramOidcLogin,
  type DashboardSnapshot,
  type TelegramWebLoginPayload,
  type UserPayload,
} from "@/lib/api";
import {
  clearTelegramOidcCallback,
  describeTelegramOidcError,
  readTelegramOidcCallback,
} from "@/lib/telegram-oidc";
import {
  isTelegramAuthRefreshRequired,
  shouldRefreshTelegramWebLoginPayload,
  telegramAuthRefreshMessage,
} from "@/lib/telegram-login-refresh";
import { getTgUser, type TgUser } from "@/lib/telegram";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

type PortalSessionContextValue = {
  loading: boolean;
  coldStart: boolean;
  refreshing: boolean;
  error: string;
  webLoginRequired: boolean;
  webLoginBusy: boolean;
  webLoginError: string;
  user: UserPayload | null;
  dash: DashboardSnapshot | null;
  tgUser: TgUser | null;
  refresh: () => Promise<void>;
  startTelegramLogin: () => Promise<void>;
  loginByWidget: (payload: TelegramWebLoginPayload) => Promise<void>;
  logoutWebSession: () => void;
};

const PortalSessionContext = createContext<PortalSessionContextValue | null>(null);

function parseErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message || "Не удалось загрузить данные";
  }
  if (typeof error === "string") {
    return error;
  }
  return String((error as { message?: string })?.message || "Не удалось загрузить данные");
}

function isReauthMessage(message: string): boolean {
  if (isTelegramAuthRefreshRequired(message)) return true;
  const lowered = message.toLowerCase();
  return (
    lowered.includes("telegram auth required") ||
    lowered.includes("invalid telegram signature") ||
    lowered.includes("access denied") ||
    lowered.includes("сессия") ||
    lowered.includes("повторите вход") ||
    lowered.includes("обновите вход")
  );
}

type PortalSessionProviderProps = {
  children: React.ReactNode;
  mode?: "entry" | "dashboard";
};

/*
 * Warm-start snapshot: the last good {user, dash} pair is mirrored into
 * sessionStorage (5-minute TTL) so a reload paints real account state
 * immediately while `refreshing` revalidates in the background. Only
 * non-sensitive display data is stored: every field whose name matches
 * SENSITIVE_SNAPSHOT_FIELD_RE (tokens, keys, links, urls, secrets) is
 * stripped recursively before write and again after read.
 */
const SESSION_SNAPSHOT_STORAGE_KEY = "pokrov-session-snapshot:v1";
const SESSION_SNAPSHOT_TTL_MS = 5 * 60 * 1000;
const SENSITIVE_SNAPSHOT_FIELD_RE = /token|key|link|url|secret/i;

type SessionSnapshot = { user: UserPayload; dash: DashboardSnapshot };

function stripSensitiveSnapshotFields(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => stripSensitiveSnapshotFields(item));
  }
  if (value && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      if (SENSITIVE_SNAPSHOT_FIELD_RE.test(key)) continue;
      result[key] = stripSensitiveSnapshotFields(item);
    }
    return result;
  }
  return value;
}

function persistSessionSnapshot(user: UserPayload, dash: DashboardSnapshot): void {
  if (typeof window === "undefined") return;
  try {
    const payload = {
      savedAt: Date.now(),
      user: stripSensitiveSnapshotFields(user),
      dash: stripSensitiveSnapshotFields(dash),
    };
    window.sessionStorage.setItem(SESSION_SNAPSHOT_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Storage full or blocked: warm start is best-effort only.
  }
}

function clearSessionSnapshot(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(SESSION_SNAPSHOT_STORAGE_KEY);
  } catch {
    // ignore blocked storage
  }
}

function readSessionSnapshot(): SessionSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(SESSION_SNAPSHOT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { savedAt?: number; user?: unknown; dash?: unknown } | null;
    const savedAt = Number(parsed?.savedAt || 0);
    if (!savedAt || Date.now() - savedAt > SESSION_SNAPSHOT_TTL_MS) {
      clearSessionSnapshot();
      return null;
    }
    if (!parsed?.user || typeof parsed.user !== "object" || !parsed?.dash || typeof parsed.dash !== "object") {
      return null;
    }
    // Defense in depth: never trust stored data to be clean.
    const user = stripSensitiveSnapshotFields(parsed.user) as UserPayload;
    const dash = stripSensitiveSnapshotFields(parsed.dash) as DashboardSnapshot;
    if (!Number(user.tg_id || 0) || typeof dash.is_active !== "boolean") return null;
    return { user, dash };
  } catch {
    return null;
  }
}

export function PortalSessionProvider({ children, mode = "dashboard" }: PortalSessionProviderProps) {
  const [tgUser] = useState<TgUser | null>(() => getTgUser());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [webLoginRequired, setWebLoginRequired] = useState(false);
  const [webLoginBusy, setWebLoginBusy] = useState(false);
  const [webLoginError, setWebLoginError] = useState("");
  const [user, setUser] = useState<UserPayload | null>(null);
  const [dash, setDash] = useState<DashboardSnapshot | null>(null);
  const lastGoodRef = useRef<{ user: UserPayload; dash: DashboardSnapshot } | null>(null);
  const lastFocusRefreshAtRef = useRef(0);

  const consumeTelegramOidcRedirect = useCallback(async (): Promise<boolean> => {
    const callback = readTelegramOidcCallback();
    if (!callback) return false;

    setWebLoginBusy(true);
    setWebLoginError("");
    try {
      if (callback.error || !callback.code || !callback.state) {
        throw new Error(describeTelegramOidcError(callback));
      }
      const auth = await finishTelegramOidcLogin({
        code: callback.code,
        state: callback.state,
      });
      if (!auth?.token) {
        throw new Error("Не получилось открыть вход. Войдите снова или напишите в поддержку.");
      }
      setWebSessionToken(auth.token);
      return true;
    } catch (error) {
      clearWebSessionToken();
      setUser(null);
      setDash(null);
      lastGoodRef.current = null;
      clearSessionSnapshot();
      setError("");
      setWebLoginRequired(true);
      setWebLoginError(telegramAuthRefreshMessage(error));
      return false;
    } finally {
      clearTelegramOidcCallback();
      setWebLoginBusy(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    if (typeof window !== "undefined") {
      try {
        const current = new URL(window.location.href);
        if (current.searchParams.get("clear_web_session") === "1") {
          clearWebSessionToken();
          current.searchParams.delete("clear_web_session");
          window.history.replaceState({}, "", `${current.pathname}${current.search}${current.hash}` || "/");
        }
      } catch {
        // ignore malformed location
      }
    }

    const completedOidcFromUrl = await consumeTelegramOidcRedirect();
    const cabinetHandoffResult = await consumeCabinetHandoffTokenFromUrl();
    const consumedFromUrl = consumeWebSessionTokenFromUrl();
    const hasSession = hasWebSessionToken() || completedOidcFromUrl || cabinetHandoffResult.exchanged || consumedFromUrl;
    if (!tgUser && !hasSession) {
      lastGoodRef.current = null;
      clearSessionSnapshot();
      setUser(null);
      setDash(null);
      setLoading(false);
      setRefreshing(false);
      setWebLoginBusy(false);
      setError("");
      setWebLoginError(cabinetHandoffResult.errorMessage || "");
      setWebLoginRequired(true);
      return;
    }

    // Warm start: hydrate the persisted display snapshot so the shell renders
    // instantly and `refreshing` (not the bootstrap skeleton) covers the
    // revalidation. Skipped when a URL just carried fresh auth material —
    // that may be a different account than the stored snapshot.
    const consumedAuthFromUrl = completedOidcFromUrl || cabinetHandoffResult.exchanged || consumedFromUrl;
    if (mode !== "entry" && !consumedAuthFromUrl && !lastGoodRef.current) {
      const warmSnapshot = readSessionSnapshot();
      if (warmSnapshot) {
        lastGoodRef.current = warmSnapshot;
        setUser(warmSnapshot.user);
        setDash(warmSnapshot.dash);
      }
    }

    const hasWarmSnapshot = mode !== "entry" && Boolean(lastGoodRef.current?.user && lastGoodRef.current?.dash);
    setLoading(!hasWarmSnapshot);
    setRefreshing(hasWarmSnapshot);
    setError("");
    setWebLoginRequired(false);
    setWebLoginError("");

    try {
      const authSession = await fetchAuthSession();
      const authTgId = Number(authSession?.user?.id || tgUser?.id || 0);

      if (mode === "entry") {
        setUser(null);
        setDash(null);
        lastGoodRef.current = null;
        return;
      }

      let dashboard: DashboardSnapshot;
      let profile: UserPayload;
      if (authTgId > 0) {
        [dashboard, profile] = await Promise.all([fetchDashboard(), fetchUser(authTgId)]);
      } else {
        dashboard = await fetchDashboard();
        profile = await fetchUser(Number(dashboard.tg_id));
      }
      setDash(dashboard);
      setUser(profile);
      lastGoodRef.current = { user: profile, dash: dashboard };
      persistSessionSnapshot(profile, dashboard);
    } catch (error) {
      const message = parseErrorMessage(error);
      if (isReauthMessage(message)) {
        clearWebSessionToken();
        setUser(null);
        setDash(null);
        lastGoodRef.current = null;
        clearSessionSnapshot();
        setWebLoginRequired(true);
        setWebLoginBusy(false);
        setWebLoginError(telegramAuthRefreshMessage(message));
        setError("");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [consumeTelegramOidcRedirect, mode, tgUser]);

  useEffect(() => {
    lastFocusRefreshAtRef.current = Date.now();
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (typeof window === "undefined" || mode === "entry") return;
    const refreshAfterFocus = () => {
      if (typeof document !== "undefined" && document.visibilityState && document.visibilityState !== "visible") return;
      const now = Date.now();
      if (now - lastFocusRefreshAtRef.current < 8000) return;
      lastFocusRefreshAtRef.current = now;
      void refresh();
    };
    window.addEventListener("focus", refreshAfterFocus);
    window.addEventListener("pageshow", refreshAfterFocus);
    document.addEventListener("visibilitychange", refreshAfterFocus);
    return () => {
      window.removeEventListener("focus", refreshAfterFocus);
      window.removeEventListener("pageshow", refreshAfterFocus);
      document.removeEventListener("visibilitychange", refreshAfterFocus);
    };
  }, [mode, refresh]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const onAuthRequired = (event: Event) => {
      const detail = (event as CustomEvent<{ code?: string | null; message?: string | null }>).detail || {};
      const message = String(detail.message || "").trim();
      clearWebSessionToken();
      setUser(null);
      setDash(null);
      lastGoodRef.current = null;
      clearSessionSnapshot();
      setError("");
      setWebLoginError(telegramAuthRefreshMessage(message || detail.code || "telegram_login_deprecated"));
      setWebLoginRequired(true);
      setLoading(false);
      setRefreshing(false);
    };
    window.addEventListener("portal-auth-required", onAuthRequired as EventListener);
    return () => window.removeEventListener("portal-auth-required", onAuthRequired as EventListener);
  }, []);

  const loginByWidget = useCallback(async (payload: TelegramWebLoginPayload) => {
    setWebLoginBusy(true);
    setWebLoginError("");
    try {
      if (shouldRefreshTelegramWebLoginPayload(payload)) {
        const message = telegramAuthRefreshMessage("telegram_login_deprecated");
        clearWebSessionToken();
        setUser(null);
        setDash(null);
        lastGoodRef.current = null;
        clearSessionSnapshot();
        setWebLoginRequired(true);
        setError("");
        setWebLoginError(message);
        throw new Error(message);
      }
      const auth = await authByTelegramWebLogin(payload);
      if (!auth?.token) throw new Error("Не получилось открыть вход. Войдите снова или напишите в поддержку.");
      setWebSessionToken(auth.token);
      if (typeof window !== "undefined") {
        const current = new URL(window.location.href);
        current.searchParams.delete("clear_web_session");
        window.location.replace(`${current.pathname}${current.search}${current.hash}` || "/");
        return;
      }
      await refresh();
    } catch (error) {
      const message = parseErrorMessage(error);
      if (isReauthMessage(message)) {
        clearWebSessionToken();
        setUser(null);
        setDash(null);
        lastGoodRef.current = null;
        clearSessionSnapshot();
        setWebLoginRequired(true);
        setError("");
        setWebLoginError(telegramAuthRefreshMessage(message));
      } else {
        setWebLoginError(message);
      }
      throw error;
    } finally {
      setWebLoginBusy(false);
    }
  }, [refresh]);

  const startTelegramLogin = useCallback(async () => {
    setWebLoginBusy(true);
    setWebLoginError("");
    try {
      const auth = await startTelegramOidcLogin();
      const authUrl = String(auth?.auth_url || "").trim();
      if (!authUrl) {
        throw new Error("Telegram OAuth URL is missing");
      }
      if (typeof window !== "undefined") {
        window.location.assign(authUrl);
        return;
      }
    } catch (error) {
      const message = parseErrorMessage(error);
      setWebLoginError(isReauthMessage(message) ? telegramAuthRefreshMessage(message) : message);
      setWebLoginBusy(false);
      throw error;
    }
  }, []);

  const logoutWebSession = useCallback(() => {
    clearWebSessionToken();
    setUser(null);
    setDash(null);
    lastGoodRef.current = null;
    clearSessionSnapshot();
    setError("");
    setWebLoginError("");
    setWebLoginBusy(false);
    setRefreshing(false);
    setWebLoginRequired(true);
    if (typeof window !== "undefined") {
      window.location.assign("/");
    }
  }, []);

  const value = useMemo(
    () => ({
      loading,
      coldStart: loading,
      refreshing,
      error,
      webLoginRequired,
      webLoginBusy,
      webLoginError,
      user,
      dash,
      tgUser,
      refresh,
      startTelegramLogin,
      loginByWidget,
      logoutWebSession,
    }),
    [
      loading,
      refreshing,
      error,
      webLoginRequired,
      webLoginBusy,
      webLoginError,
      user,
      dash,
      tgUser,
      refresh,
      startTelegramLogin,
      loginByWidget,
      logoutWebSession,
    ],
  );

  return (
    <PortalSessionContext.Provider value={value}>
      {children}
    </PortalSessionContext.Provider>
  );
}

export function usePortalSession(): PortalSessionContextValue {
  const context = useContext(PortalSessionContext);
  if (!context) {
    throw new Error("usePortalSession must be used inside PortalSessionProvider");
  }
  return context;
}
