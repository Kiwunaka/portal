"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Check, Loader2 } from "lucide-react";

import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, SectionTitle } from "@/components/ui";
import { ErrorState, LoadingState } from "@/components/ui/states";
import {
  AdminApiError,
  clearAdminInitData,
  clearAdminSessionToken,
  createAdminSession,
  hasAdminAuthMaterial,
  saveAdminInitData,
  saveAdminSessionToken
} from "@/lib/admin-api/client";

function isAccessDenied(error: unknown): boolean {
  return error instanceof AdminApiError && (error.status === 401 || error.status === 403);
}

export function adminApiErrorText(error: AdminApiError | null, fallback: string): string {
  if (!error) return fallback;
  const correlation = error.correlationId ? ` Код обращения: ${error.correlationId}.` : "";
  return `${error.message}${correlation}`;
}

export function AdminRouteBoundary({
  children,
  onShellStatus
}: {
  children: ReactNode;
  onShellStatus?: (status: OpsShellStatus) => void;
}) {
  const [ready, setReady] = useState(false);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const checkedAuthRef = useRef(false);

  const startSession = useCallback(async (initData?: string, options?: { silent?: boolean }) => {
    setBusy(true);
    if (!options?.silent) setError("");
    try {
      const clean = String(initData || "").trim();
      if (clean) saveAdminInitData(clean);
      const session = await createAdminSession();
      saveAdminSessionToken(session.token);
      clearAdminInitData();
      setReady(true);
    } catch (reason) {
      onShellStatus?.({
        api: "missing",
        session: isAccessDenied(reason) ? "failed" : "unavailable",
        oldestRequiredSourceAt: null
      });
      if (!options?.silent) {
        setError(reason instanceof Error ? reason.message : "Не удалось открыть сессию. Проверьте доступ и повторите вход.");
      }
    } finally {
      setBusy(false);
    }
  }, [onShellStatus]);

  useEffect(() => {
    if (checkedAuthRef.current) return;
    checkedAuthRef.current = true;
    onShellStatus?.({ api: "missing", session: "missing", oldestRequiredSourceAt: null });
    if (hasAdminAuthMaterial()) {
      const timer = window.setTimeout(() => setReady(true), 0);
      return () => window.clearTimeout(timer);
    }
    const timer = window.setTimeout(() => void startSession("", { silent: true }), 0);
    return () => window.clearTimeout(timer);
  }, [onShellStatus, startSession]);

  if (ready) return children;

  return (
    <div className="grid min-h-[62vh] place-items-center">
      <Card className="w-full max-w-xl">
        <SectionTitle
          title="Вход в админку"
          description="Сначала проверяем текущую web-сессию. Если доступа нет, вставьте Telegram WebApp initData один раз."
        />
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          aria-label="Telegram WebApp initData"
          placeholder="query_id=...&user=...&auth_date=...&hash=..."
          className="min-h-28 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-xs outline-none focus:border-[color:var(--atlas-focus)]"
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <Button tone="primary" disabled={busy} onClick={() => void startSession()}>
            {busy ? <Loader2 className="animate-spin" size={15} /> : <Check size={15} />} Войти через текущую сессию
          </Button>
          <Button tone="secondary" disabled={busy || !value.trim()} onClick={() => void startSession(value)}>
            {busy ? <Loader2 className="animate-spin" size={15} /> : <Check size={15} />} Войти по initData
          </Button>
          <Button
            tone="ghost"
            disabled={busy}
            onClick={() => {
              clearAdminInitData();
              clearAdminSessionToken();
              setValue("");
              setError("");
            }}
          >
            Сбросить
          </Button>
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
