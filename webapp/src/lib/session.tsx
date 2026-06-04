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
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

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
        throw new Error("Не получен web session token");
      }
      setWebSessionToken(auth.token);
      return true;
    } catch (error) {
      clearWebSessionToken();
      setUser(null);
      setDash(null);
      lastGoodRef.current = null;
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
    } catch (error) {
      const message = parseErrorMessage(error);
      if (isReauthMessage(message)) {
        clearWebSessionToken();
        setUser(null);
        setDash(null);
        lastGoodRef.current = null;
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
        setWebLoginRequired(true);
        setError("");
        setWebLoginError(message);
        throw new Error(message);
      }
      const auth = await authByTelegramWebLogin(payload);
      if (!auth?.token) throw new Error("Не получен web session token");
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
    setError("");
    setWebLoginError("");
    setWebLoginBusy(false);
    setRefreshing(false);
    setWebLoginRequired(true);
    if (typeof window !== "undefined") {
      window.location.assign("/");
    }
  }, []);

  return (
    <PortalSessionContext.Provider
      value={{
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
      }}
    >
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
