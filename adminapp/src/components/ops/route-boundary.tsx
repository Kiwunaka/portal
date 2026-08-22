"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Loader2, LogIn } from "lucide-react";

import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, SectionTitle } from "@/components/ui";
import { ErrorState, LoadingState } from "@/components/ui/states";
import {
  AdminApiError,
  bootstrapAdminSession,
  clearAdminSessionMemory,
  finishAdminOidcSession,
  finishAdminOidcStepUp,
  getCurrentAdminSession,
  hasTelegramMiniAppIdentity,
  purgeLegacyAdminAuthStorage,
  startAdminOidc
} from "@/lib/admin-api/client";
import {
  loadOperatorShellIdentity,
  type OperatorShellIdentity
} from "@/lib/admin-api/identity";

function isAccessDenied(error: unknown): boolean {
  return error instanceof AdminApiError && (error.status === 401 || error.status === 403);
}

function takeOidcCallback(): { code: string; state: string } | null {
  const url = new URL(window.location.href);
  const code = String(url.searchParams.get("code") || "").trim();
  const state = String(url.searchParams.get("state") || "").trim();
  if (!code && !state) return null;
  url.searchParams.delete("code");
  url.searchParams.delete("state");
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  if (!code || !state) throw new Error("operator_oidc_callback_invalid");
  return { code, state };
}

export function adminApiErrorText(error: AdminApiError | null, fallback: string): string {
  if (!error) return fallback;
  const message = error.status === 401
    ? "Сессия истекла. Войдите снова."
    : error.status === 403
      ? "Недостаточно прав для этого раздела."
      : error.status === 404
        ? "Запрошенные данные не найдены."
        : error.status === 409
          ? "Данные изменились. Обновите раздел и повторите проверку."
          : error.status === 422
            ? "Сервер отклонил параметры запроса. Проверьте введённые данные."
            : error.status === 429
              ? "Слишком много запросов. Подождите и повторите позже."
              : error.status >= 500
                ? "Сервис временно недоступен. Повторите запрос позже."
                : fallback;
  const safeCode = error.code && /^[a-z0-9._-]{1,96}$/i.test(error.code) ? error.code : null;
  const safeCorrelation = error.correlationId && /^[a-z0-9._:-]{1,128}$/i.test(error.correlationId) ? error.correlationId : null;
  const technical = [
    safeCode ? `Технический код: ${safeCode}.` : "",
    safeCorrelation ? `ID обращения: ${safeCorrelation}.` : ""
  ].filter(Boolean).join(" ");
  return technical ? `${message} ${technical}` : message;
}

export function AdminRouteBoundary({
  children,
  onShellStatus,
  onIdentity
}: {
  children: ReactNode;
  onShellStatus?: (status: OpsShellStatus) => void;
  onIdentity?: (identity: OperatorShellIdentity | null) => void;
}) {
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const checkedAuthRef = useRef(false);

  const startSession = useCallback(async (options?: { silent?: boolean; legacy?: boolean }) => {
    setBusy(true);
    if (!options?.silent) setError("");
    let callbackAttempted = false;
    try {
      const callback = takeOidcCallback();
      callbackAttempted = callback !== null;
      let session: Awaited<ReturnType<typeof getCurrentAdminSession>>;
      let hadSession = false;
      try {
        session = await getCurrentAdminSession();
        hadSession = true;
      } catch (reason) {
        if (!isAccessDenied(reason)) throw reason;
        clearAdminSessionMemory();
        if (callback) {
          session = await finishAdminOidcSession(callback.code, callback.state);
        } else if (options?.legacy) {
          session = await bootstrapAdminSession();
        } else {
          throw reason;
        }
      }
      if (callback && hadSession) {
        await finishAdminOidcStepUp(callback.code, callback.state);
        session = await getCurrentAdminSession();
      }
      onIdentity?.(await loadOperatorShellIdentity(session));
      setReady(true);
      onShellStatus?.({ api: "missing", session: "ok", oldestRequiredSourceAt: null });
    } catch (reason) {
      onIdentity?.(null);
      setReady(false);
      onShellStatus?.({
        api: "missing",
        session: isAccessDenied(reason) ? "failed" : "unavailable",
        oldestRequiredSourceAt: null
      });
      if (!options?.silent || callbackAttempted) {
        setError(reason instanceof AdminApiError
          ? adminApiErrorText(reason, "Не удалось открыть сессию. Проверьте доступ и повторите вход.")
          : "Не удалось открыть сессию. Проверьте доступ и повторите вход.");
      }
    } finally {
      setBusy(false);
    }
  }, [onIdentity, onShellStatus]);

  const beginOidc = useCallback(async () => {
    setBusy(true);
    setError("");
    try {
      const envelope = await startAdminOidc("login");
      const authUrl = new URL(envelope.data.auth_url);
      if (authUrl.protocol !== "https:" || authUrl.hostname !== "oauth.telegram.org") {
        throw new Error("operator_oidc_authorize_url_invalid");
      }
      window.location.assign(authUrl.toString());
    } catch (reason) {
      setError(reason instanceof AdminApiError
        ? adminApiErrorText(reason, "OIDC-вход временно недоступен.")
        : "OIDC-вход временно недоступен.");
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (checkedAuthRef.current) return;
    checkedAuthRef.current = true;
    purgeLegacyAdminAuthStorage();
    onShellStatus?.({ api: "missing", session: "missing", oldestRequiredSourceAt: null });
    const timer = window.setTimeout(() => void startSession({ silent: true }), 0);
    return () => window.clearTimeout(timer);
  }, [onShellStatus, startSession]);

  if (ready) return children;

  return (
    <div className="grid min-h-[62vh] place-items-center">
      <Card className="w-full max-w-xl">
        <SectionTitle
          title="Вход в админку"
          description="Серверная операторская сессия не подтвердилась. Основной вход использует Telegram OIDC; оператор и роль должны быть заведены заранее."
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <Button tone="primary" disabled={busy} onClick={() => void beginOidc()}>
            {busy ? <Loader2 className="animate-spin" size={15} /> : <LogIn size={15} />} Войти через Telegram OIDC
          </Button>
          {hasTelegramMiniAppIdentity() ? (
            <Button tone="secondary" disabled={busy} onClick={() => void startSession({ legacy: true })}>
              Compatibility-вход
            </Button>
          ) : null}
        </div>
        {error ? <div className="mt-3"><Badge tone="danger">{error}</Badge></div> : null}
      </Card>
    </div>
  );
}

export function RouteBoundary({
  loading,
  refreshing,
  error,
  hasData,
  retryLabel,
  onRetry,
  children
}: {
  loading: boolean;
  refreshing: boolean;
  error: AdminApiError | null;
  hasData: boolean;
  retryLabel: string;
  onRetry: () => void;
  children: ReactNode;
}) {
  if (loading && !hasData) {
    return <LoadingState title="Загружаем данные" description="Источник ещё отвечает. Остальные блоки остаются доступны." />;
  }
  if (error && !hasData) {
    return (
      <ErrorState
        title="Источник не ответил"
        description={adminApiErrorText(error, "Проверьте соединение и повторите загрузку.")}
        action={<Button tone="secondary" onClick={onRetry}>{retryLabel}</Button>}
      />
    );
  }
  return (
    <div className="space-y-3">
      {refreshing ? <Badge tone="info">Обновляем</Badge> : null}
      {error ? (
        <ErrorState
          title="Не удалось обновить источник"
          description={`${adminApiErrorText(error, "Повторите загрузку.")} Последние успешные данные сохранены.`}
          action={<Button tone="secondary" onClick={onRetry}>{retryLabel}</Button>}
          className="min-h-0"
        />
      ) : null}
      {children}
    </div>
  );
}
