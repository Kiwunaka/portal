"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button } from "@/components/ui";
import { ErrorState } from "@/components/ui/states";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchOpsOverview, fetchRuLatest } from "@/lib/admin-api/overview";
import type { OpsAlert } from "@/lib/admin-api/types";
import { useRouteResource } from "@/lib/use-route-resource";

import { actionQueueFromAlerts } from "./action-queue";
import { TriageWorkspace } from "./triage-workspace";

const OVERVIEW_POLL_MS = 60_000;

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function alertQueueId(alert: OpsAlert): string {
  return String(alert.fingerprint || `alert-${alert.id}`);
}

export function OverviewPage({
  onShellStatus,
  onNavigate
}: {
  onShellStatus?: (status: OpsShellStatus) => void;
  onNavigate?: (href: string) => void;
}) {
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const loadOverview = useCallback((signal: AbortSignal) => fetchOpsOverview({ signal }), []);
  const loadRuLatest = useCallback((signal: AbortSignal) => fetchRuLatest({ signal }), []);
  const overview = useRouteResource("overview", loadOverview, { pollMs: OVERVIEW_POLL_MS, enabled: true });
  const ruLatest = useRouteResource("overview-ru-latest", loadRuLatest, { pollMs: OVERVIEW_POLL_MS, enabled: true });

  useEffect(() => {
    const successCount = Number(overview.data !== null) + Number(ruLatest.data !== null);
    const errors = [overview.error, ruLatest.error].filter((error): error is AdminApiError => error !== null);
    const loading = overview.loading || ruLatest.loading;
    const api = errors.length
      ? successCount > 0 ? "degraded" : "failed"
      : loading && successCount < 2 ? "missing" : "ok";
    const session = errors.some(isAccessDenied)
      ? "failed"
      : successCount > 0 ? "ok" : errors.length ? "unavailable" : "missing";
    const requiredSourceTimes = [
      overview.data?.generated_at,
      ruLatest.data?.sampled_at,
      ruLatest.data?.latest_eligible_run?.finished_at
    ].filter((value): value is string => Boolean(value)).sort();
    onShellStatus?.({
      api,
      session,
      oldestRequiredSourceAt: requiredSourceTimes.at(0) || null
    });
  }, [
    onShellStatus,
    overview.data,
    overview.error,
    overview.loading,
    ruLatest.data,
    ruLatest.error,
    ruLatest.loading
  ]);

  const activeAlerts = useMemo(() => overview.data?.alerts?.active ?? [], [overview.data]);
  const queueItems = useMemo(() => actionQueueFromAlerts(activeAlerts), [activeAlerts]);
  const resolvedSelectedId = selectedActionId && queueItems.some((item) => item.id === selectedActionId)
    ? selectedActionId
    : queueItems.at(0)?.id || null;
  const selectedAlert = activeAlerts.find((alert) => alertQueueId(alert) === resolvedSelectedId) || null;
  const refreshing = overview.refreshing || ruLatest.refreshing;
  const lastUpdated = [overview.updatedAt, ruLatest.updatedAt]
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1) || null;
  const hasSourceError = Boolean(overview.error || ruLatest.error);
  const refreshAll = () => {
    overview.reload();
    ruLatest.reload();
  };

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={hasSourceError ? "warning" : "success"}>{hasSourceError ? "Есть сбой источника" : "Источники отвечают"}</Badge>
          <span>{lastUpdated ? `Обновлено ${new Date(lastUpdated).toLocaleString("ru-RU")}` : "Данные ещё не получены"}</span>
          {refreshing ? <Badge tone="info">Обновляем</Badge> : null}
        </div>
        <Button
          variant="secondary"
          disabled={overview.loading || ruLatest.loading || refreshing}
          onClick={refreshAll}
        >
          <RefreshCw aria-hidden="true" size={15} strokeWidth={1.8} className={refreshing ? "animate-spin" : ""} />
          Обновить
        </Button>
      </div>

      {ruLatest.error ? (
        <ErrorState
          title="RU-origin не загрузился"
          description={`${adminApiErrorText(ruLatest.error, "Повторите запрос RU-origin.")} Остальные блоки обзора сохранены.`}
          action={<Button variant="secondary" onClick={ruLatest.reload}>Повторить загрузку RU-origin</Button>}
          className="min-h-0"
        />
      ) : null}

      <RouteBoundary
        loading={overview.loading}
        refreshing={overview.refreshing}
        error={overview.error}
        hasData={overview.data !== null}
        retryLabel="Повторить загрузку overview"
        onRetry={overview.reload}
      >
        {overview.data ? (
          <TriageWorkspace
            overview={overview.data}
            alerts={activeAlerts}
            selectedAlert={selectedAlert}
            selectedActionId={resolvedSelectedId}
            loading={overview.loading}
            refreshing={overview.refreshing}
            ruLatest={ruLatest.data}
            ruLoading={ruLatest.loading}
            ruError={ruLatest.error}
            onSelect={setSelectedActionId}
            onNavigate={onNavigate}
            onRefresh={refreshAll}
          />
        ) : null}
      </RouteBoundary>
    </div>
  );
}
