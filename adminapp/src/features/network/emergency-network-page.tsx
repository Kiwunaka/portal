"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ArchiveRestore, Ban, CircleGauge, Database, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { MissingData } from "@/components/ops/missing-data";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchEmergencyCatalogStatus, type EmergencyCatalogSnapshot } from "@/lib/admin-api/network";
import { useRouteResource } from "@/lib/use-route-resource";

function tone(status: string): Tone {
  if (["active", "healthy", "ready"].includes(status)) return "success";
  if (["staging", "pending", "disabled"].includes(status)) return "warning";
  if (["invalid", "unavailable", "rejected"].includes(status)) return "danger";
  return "neutral";
}

function statusText(status: string): string {
  return ({
    active: "Активен",
    healthy: "Доступен",
    ready: "Готов",
    staging: "Подготовка",
    pending: "Ожидает проверки",
    disabled: "Выключен",
    invalid: "Ошибка настройки",
    unavailable: "Недоступен",
    rejected: "Отклонён",
    superseded: "Архивный",
    expired: "Просрочен",
  } as Record<string, string>)[status] || status;
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "— · Нет данных";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function SnapshotCard({
  snapshot,
  canRollback,
  onAction,
}: {
  snapshot: EmergencyCatalogSnapshot;
  canRollback: boolean;
  onAction: (request: ActionIntentRequest) => void;
}) {
  return (
    <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{snapshot.catalog_version}</p>
          <p className="mt-1 font-mono text-[10px] text-[color:var(--atlas-text-muted)]">{snapshot.snapshot_id}</p>
        </div>
        <Badge tone={tone(snapshot.status)}>{statusText(snapshot.status)}</Badge>
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
        <div><dt className="text-[color:var(--atlas-text-muted)]">Кандидаты</dt><dd className="mt-1 font-semibold tabular-nums">{snapshot.candidate_count}</dd></div>
        <div><dt className="text-[color:var(--atlas-text-muted)]">Проверены</dt><dd className="mt-1 font-semibold tabular-nums">{snapshot.healthy_count}</dd></div>
        <div><dt className="text-[color:var(--atlas-text-muted)]">Активны</dt><dd className="mt-1 font-semibold tabular-nums">{snapshot.active_endpoint_count}</dd></div>
        <div><dt className="text-[color:var(--atlas-text-muted)]">Обновлён</dt><dd className="mt-1 font-semibold">{dateText(snapshot.updated_at)}</dd></div>
      </dl>
      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-[color:var(--atlas-border)] pt-3">
        {snapshot.status === "staging" ? (
          <Button
            tone="primary"
            disabled={snapshot.healthy_count < 4}
            onClick={() => onAction({
              action: "emergency_catalog.promote",
              target: { type: "emergency_snapshot", id: snapshot.snapshot_id },
              payload: {},
              endpoint: `/api/admin/emergency-network/snapshots/${encodeURIComponent(snapshot.snapshot_id)}/promote`,
            })}
          >
            <ShieldCheck size={15} /> Продвинуть
          </Button>
        ) : null}
        {canRollback ? (
          <Button
            tone="danger"
            onClick={() => onAction({
              action: "emergency_catalog.rollback",
              target: { type: "emergency_snapshot", id: snapshot.snapshot_id },
              payload: {},
              endpoint: `/api/admin/emergency-network/snapshots/${encodeURIComponent(snapshot.snapshot_id)}/rollback`,
            })}
          >
            <ArchiveRestore size={15} /> Откатить на этот снимок
          </Button>
        ) : null}
        {snapshot.status === "active" ? (
          <Button
            tone="danger"
            onClick={() => onAction({
              action: "emergency_catalog.disable",
              target: { type: "emergency_snapshot", id: snapshot.snapshot_id },
              payload: {},
              endpoint: `/api/admin/emergency-network/snapshots/${encodeURIComponent(snapshot.snapshot_id)}/disable`,
            })}
          >
            <Ban size={15} /> Остановить выдачу
          </Button>
        ) : null}
        {snapshot.rejection_code ? <Badge tone="danger">{snapshot.rejection_code}</Badge> : null}
      </div>
    </div>
  );
}

export function EmergencyNetworkPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const load = useCallback((signal: AbortSignal) => fetchEmergencyCatalogStatus({ signal }), []);
  const resource = useRouteResource("emergency-network", load, { enabled: true, pollMs: 60_000 });

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.distribution?.updated_at || resource.data?.generated_at || null,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const rollbackIds = useMemo(
    () => new Set(resource.data?.rollback_candidates.map((item) => item.snapshot_id) || []),
    [resource.data?.rollback_candidates],
  );

  function openAction(next: ActionIntentRequest) {
    setRequest(next);
    setDialogOpen(true);
  }

  const data = resource.data;
  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={data ? tone(data.worker.configuration_state) : resource.error ? "danger" : "neutral"}>
            Сборщик: {data ? statusText(data.worker.configuration_state) : "нет данных"}
          </Badge>
          <span>Только агрегаты; адреса, ключи и raw-конфиги не передаются в браузер.</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            tone="primary"
            disabled={!data || data.worker.configuration_state !== "ready"}
            onClick={() => openAction({
              action: "emergency_catalog.stage",
              target: { type: "emergency_catalog", id: "global" },
              payload: {},
              endpoint: "/api/admin/emergency-network/stage",
            })}
          >
            <Database size={15} /> Получить staging
          </Button>
          <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}>
            <RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить
          </Button>
        </div>
      </div>

      {data ? (
        <MetricStrip label="Состояние экстренной сети">
          <MetricCell icon={<CircleGauge size={17} />} label="Сборщик" value={data.worker.enabled ? "Включён" : "Выключен"} detail={data.worker.interval_seconds ? `Каждые ${Math.round(data.worker.interval_seconds / 60)} мин.` : "Запусков нет"} tone={tone(data.worker.configuration_state)} />
          <MetricCell icon={<ShieldCheck size={17} />} label="Здоровые пробы" value={data.probe_summary.healthy} detail={`Из ${data.probe_summary.total}`} tone={data.probe_summary.healthy >= 4 ? "success" : "warning"} />
          <MetricCell icon={<TriangleAlert size={17} />} label="Недоступны" value={data.probe_summary.unavailable} detail={`${data.probe_summary.pending} ожидают`} tone={data.probe_summary.unavailable ? "danger" : "neutral"} />
          <MetricCell icon={<ArchiveRestore size={17} />} label="Откат" value={data.rollback_candidates.length} detail="Удерживаемые снимки" tone={data.rollback_candidates.length ? "info" : "neutral"} />
        </MetricStrip>
      ) : null}

      {data?.distribution?.status === "disabled" ? (
        <Card>
          <div className="flex items-start gap-3">
            <Ban className="mt-0.5 shrink-0 text-[color:var(--atlas-danger)]" size={18} />
            <div>
              <p className="text-sm font-semibold">Выдача экстренного каталога остановлена оператором</p>
              <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">
                Worker может готовить staging, но не включит его сам. Уже выданный подписанный офлайн-кэш может работать до указанного в нём срока.
              </p>
            </div>
          </div>
        </Card>
      ) : null}

      <Card>
        <SectionTitle title="Каталог аварийных маршрутов" description="Активная ревизия, staging и последние удерживаемые снимки. Продвижение и откат требуют серверного action-intent." />
        {resource.error && !data ? (
          <EmptyState title="Источник недоступен" description={resource.error.message} />
        ) : data?.snapshots.length ? (
          <div className="grid gap-2">
            {data.snapshots.map((snapshot) => (
              <SnapshotCard key={snapshot.snapshot_id} snapshot={snapshot} canRollback={rollbackIds.has(snapshot.snapshot_id)} onAction={openAction} />
            ))}
          </div>
        ) : data ? (
          <EmptyState title="Снимков пока нет" description="Сначала настройте worker и получите staging из утверждённого quorum-источника." />
        ) : (
          <MissingData />
        )}
      </Card>

      <ActionIntentDialog
        open={dialogOpen}
        request={request}
        onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }}
        onKnownOutcome={resource.reload}
        onCheckState={resource.reload}
      />
    </div>
  );
}
