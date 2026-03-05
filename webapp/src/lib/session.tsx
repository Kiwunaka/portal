"use client";

import {
  authByTelegramWebLogin,
  clearWebSessionToken,
  consumeWebSessionTokenFromUrl,
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

export function PortalSessionProvider({ children }: { children: React.ReactNode }) {
  const tgUser = useMemo(() => getTgUser(), []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [webLoginRequired, setWebLoginRequired] = useState(false);
  const [webLoginBusy, setWebLoginBusy] = useState(false);
  const [webLoginError, setWebLoginError] = useState("");
  const [user, setUser] = useState<UserPayload | null>(null);
  const [dash, setDash] = useState<DashboardSnapshot | null>(null);

  const refresh = useCallback(async () => {
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
      const dashboard = await fetchDashboard();
      const profile = await fetchUser(Number(dashboard.tg_id));
      setDash(dashboard);
      setUser(profile);
    } catch (error) {
      const message = parseErrorMessage(error);
      if (!tgUser && message.toLowerCase().includes("telegram auth required")) {
        clearWebSessionToken();
        setWebLoginRequired(true);
        setError("");
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }, [tgUser]);

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
