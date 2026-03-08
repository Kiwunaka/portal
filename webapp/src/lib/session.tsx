"use client";

import {
  authByTelegramWebLogin,
  clearWebSessionToken,
  consumeWebSessionTokenFromUrl,
  fetchAuthSession,
  fetchDashboard,
  fetchUser,
  hasWebSessionToken,
  setWebSessionToken,
  type DashboardSnapshot,
  type TelegramWebLoginPayload,
  type UserPayload,
} from "@/lib/api";
import { getTgUser, type TgUser } from "@/lib/telegram";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

type PortalSessionContextValue = {
  loading: boolean;
  error: string;
  webLoginRequired: boolean;
  webLoginBusy: boolean;
  webLoginError: string;
  user: UserPayload | null;
  dash: DashboardSnapshot | null;
  tgUser: TgUser | null;
  refresh: () => Promise<void>;
  loginByWidget: (payload: TelegramWebLoginPayload) => Promise<void>;
  logoutWebSession: () => void;
};

const PortalSessionContext = createContext<PortalSessionContextValue | null>(null);

function parseErrorMessage(error: unknown): string {
  return String((error as { message?: string })?.message || error || "Не удалось загрузить данные");
}

type PortalSessionProviderProps = {
  children: React.ReactNode;
  mode?: "entry" | "dashboard";
};

export function PortalSessionProvider({ children, mode = "dashboard" }: PortalSessionProviderProps) {
  const tgUser = useMemo(() => getTgUser(), []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [webLoginRequired, setWebLoginRequired] = useState(false);
  const [webLoginBusy, setWebLoginBusy] = useState(false);
  const [webLoginError, setWebLoginError] = useState("");
  const [user, setUser] = useState<UserPayload | null>(null);
  const [dash, setDash] = useState<DashboardSnapshot | null>(null);

  const refresh = useCallback(async () => {
    if (typeof window !== "undefined") {
      try {
        const current = new URL(window.location.href);
        if (current.searchParams.get("clear_web_session") === "1") {
          clearWebSessionToken();
          current.searchParams.delete("clear_web_session");
          window.history.replaceState({}, "", `${current.pathname}${current.search}${current.hash}` || "/webapp/");
        }
      } catch {
        // ignore malformed location
      }
    }

    const consumedFromUrl = consumeWebSessionTokenFromUrl();
    const hasSession = hasWebSessionToken() || consumedFromUrl;
    if (!tgUser && !hasSession) {
      setLoading(false);
      setError("");
      setWebLoginRequired(true);
      return;
    }

    setLoading(true);
    setError("");
    setWebLoginRequired(false);
    setWebLoginError("");

    try {
      const authSession = await fetchAuthSession();
      const authTgId = Number(authSession?.user?.id || tgUser?.id || 0);

      if (mode === "entry") {
        setUser(null);
        setDash(null);
        return;
      }

      const [dashboard, profile] = await Promise.all([
        fetchDashboard(),
        authTgId > 0 ? fetchUser(authTgId) : fetchDashboard().then((payload) => fetchUser(Number(payload.tg_id))),
      ]);
      setDash(dashboard);
      setUser(profile);
    } catch (error) {
      const message = parseErrorMessage(error);
      const lowered = message.toLowerCase();
      if (
        !tgUser &&
        (lowered.includes("telegram auth required") ||
          lowered.includes("invalid telegram signature") ||
          lowered.includes("access denied"))
      ) {
        clearWebSessionToken();
        setUser(null);
        setDash(null);
        setWebLoginRequired(true);
        setError("");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }, [mode, tgUser]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const loginByWidget = useCallback(async (payload: TelegramWebLoginPayload) => {
    setWebLoginBusy(true);
    setWebLoginError("");
    try {
      const auth = await authByTelegramWebLogin(payload);
      if (!auth?.token) throw new Error("Не получен web session token");
      setWebSessionToken(auth.token);
      await refresh();
    } catch (error) {
      setWebLoginError(parseErrorMessage(error));
      throw error;
    } finally {
      setWebLoginBusy(false);
    }
  }, [refresh]);

  const logoutWebSession = useCallback(() => {
    clearWebSessionToken();
    setUser(null);
    setDash(null);
    setError("");
    setWebLoginError("");
    setWebLoginRequired(true);
    if (typeof window !== "undefined") {
      window.location.assign("/webapp/");
    }
  }, []);

  return (
    <PortalSessionContext.Provider
      value={{
        loading,
        error,
        webLoginRequired,
        webLoginBusy,
        webLoginError,
        user,
        dash,
        tgUser,
        refresh,
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
