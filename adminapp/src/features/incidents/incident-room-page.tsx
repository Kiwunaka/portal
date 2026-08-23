"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  ExternalLink,
  Link2,
  MessageSquareText,
  RefreshCw,
  ShieldAlert,
  Siren,
  UsersRound,
} from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import { ErrorState, LoadingState } from "@/components/ui/states";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import {
  fetchIncidentDetail,
  fetchIncidents,
  type IncidentAlert,
  type OperatorIncident,
  type OperatorIncidentDetail,
} from "@/lib/admin-api/work";
import { useRouteResource } from "@/lib/use-route-resource";

const POLL_MS = 45_000;

function severityTone(value: string): Tone {
  if (value === "critical") return "danger";
  if (value === "major") return "warning";
  if (value === "degraded") return "info";
  return "neutral";
}

function statusTone(value: string): Tone {
  if (["resolved", "cancelled"].includes(value)) return "success";
  if (["investigating", "identified"].includes(value)) return "danger";
  return "warning";
}

function statusLabel(value: string): string {
  return {
    investigating: "Расследуем",
    identified: "Причина найдена",
    monitoring: "Наблюдаем",
    resolved: "Закрыт",
    cancelled: "Отменён",
  }[value] || value;
}

function dateTime(value: string | null | undefined): string {
  if (!value || Number.isNaN(Date.parse(value))) return "Нет данных";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function incidentRequest(
  incident: OperatorIncidentDetail,
  payload: Record<string, unknown>,
): ActionIntentRequest {
  return {
    action: "incident.update",
    target: { type: "incident", id: incident.id },
    payload: { expected_version: incident.version, ...payload },
    endpoint: "",
    workspace: "incidents",
  };
}

function AlertRow({ alert, onAction }: { alert: IncidentAlert; onAction: (request: ActionIntentRequest) => void }) {
  const acknowledged = alert.status === "acknowledged" || Boolean(alert.acknowledged_at);
  return (
    <article className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{alert.title}</p>
          <p className="mt-1 text-[11px] text-[color:var(--atlas-text-muted)]">{alert.source} · {dateTime(alert.last_seen_at)}</p>
        </div>
        <Badge tone={alert.severity === "critical" ? "danger" : "warning"}>{alert.status}</Badge>
      </div>
      {!acknowledged ? (
        <Button
          size="compact"
          tone="secondary"
          className="mt-3"
          onClick={() => onAction({
            action: "alert.ack",
            target: { type: "alert", id: String(alert.id) },
            payload: { expected_version: alert.version },
            endpoint: "",
            workspace: "incidents",
          })}
        >
          <CheckCircle2 size={15} /> Подтвердить получение
        </Button>
      ) : null}
    </article>
  );
}

function IncidentDetailPanel({
  incident,
  onAction,
}: {
  incident: OperatorIncidentDetail;
  onAction: (request: ActionIntentRequest) => void;
}) {
  const [note, setNote] = useState("");
  const [entityType, setEntityType] = useState("release");
  const [entityId, setEntityId] = useState("");
  const active = !["resolved", "cancelled"].includes(incident.workflow_status);
  const canCompensate = incident.public_status === "resolved"
    && incident.compensation.days > 0
    && !incident.compensation.completed_at;

  return (
    <div className="space-y-3">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={severityTone(incident.severity)}>{incident.severity}</Badge>
              <Badge tone={statusTone(incident.workflow_status)}>{statusLabel(incident.workflow_status)}</Badge>
              <span className="font-mono text-[11px] text-[color:var(--atlas-text-muted)]">{incident.key}</span>
            </div>
            <h2 className="mt-3 text-xl font-semibold tracking-[-0.02em]">{incident.title}</h2>
            <p className="mt-2 text-sm leading-6 text-[color:var(--atlas-text-soft)]">{incident.summary}</p>
          </div>
          <div className="text-right text-[11px] text-[color:var(--atlas-text-muted)]">
            <p>Версия {incident.version}</p>
            <p className="mt-1">Начало {dateTime(incident.started_at)}</p>
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3"><p className="text-[10px] text-[color:var(--atlas-text-muted)]">Влияние</p><p className="mt-1 text-xs font-semibold">{incident.impact || "Не зафиксировано"}</p></div>
          <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3"><p className="text-[10px] text-[color:var(--atlas-text-muted)]">Владелец</p><p className="mt-1 text-xs font-semibold">{incident.owner_team || incident.owner_operator_id || "Не назначен"}</p></div>
          <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3"><p className="text-[10px] text-[color:var(--atlas-text-muted)]">Следующий апдейт</p><p className="mt-1 text-xs font-semibold">{dateTime(incident.next_update_at)}</p></div>
          <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3"><p className="text-[10px] text-[color:var(--atlas-text-muted)]">Postmortem</p><p className="mt-1 text-xs font-semibold">{incident.postmortem_status}</p></div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {active && incident.workflow_status !== "monitoring" ? (
            <Button tone="secondary" onClick={() => onAction(incidentRequest(incident, { workflow_status: "monitoring", note: "Переведено в наблюдение из Incident Room." }))}>
              <Clock3 size={15} /> Перевести в наблюдение
            </Button>
          ) : null}
          {active ? (
            <Button tone="primary" onClick={() => onAction(incidentRequest(incident, { workflow_status: "resolved", ended_at: new Date().toISOString(), note: "Инцидент закрыт оператором." }))}>
              <CheckCircle2 size={15} /> Закрыть инцидент
            </Button>
          ) : null}
          {canCompensate ? (
            <Button tone="danger" onClick={() => onAction({
              action: "incident.compensate",
              target: { type: "incident", id: incident.id },
              payload: { expected_version: incident.version },
              endpoint: "",
              workspace: "incidents",
            })}>
              <ShieldAlert size={15} /> Выдать компенсацию
            </Button>
          ) : null}
          {incident.runbook_url ? <a href={incident.runbook_url} target="_blank" rel="noreferrer" className="inline-flex min-h-10 items-center gap-2 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] px-3 text-xs font-semibold"><ExternalLink size={15} /> Runbook</a> : null}
        </div>
      </Card>

      <div className="ops-workspace xl:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
        <Card className="min-h-0">
          <SectionTitle title="Timeline" description="Append-only события с версией инцидента и операторским контекстом." />
          <ol className="space-y-3 border-l border-[color:var(--atlas-border-strong)] pl-4">
            {incident.timeline.map((event) => (
              <li key={event.id} className="relative rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 before:absolute before:-left-[1.28rem] before:top-4 before:h-2 before:w-2 before:rounded-full before:bg-[color:var(--atlas-primary)]">
                <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-xs font-semibold">{event.event_type}</span><span className="text-[10px] text-[color:var(--atlas-text-muted)]">v{event.version} · {dateTime(event.created_at)}</span></div>
                {event.note ? <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{event.note}</p> : null}
                {event.from_status && event.to_status ? <p className="mt-1 text-[10px] text-[color:var(--atlas-text-muted)]">{statusLabel(event.from_status)} → {statusLabel(event.to_status)}</p> : null}
              </li>
            ))}
          </ol>

          <label className="mt-4 block text-xs font-semibold">
            Операторская заметка
            <textarea value={note} onChange={(event) => setNote(event.target.value)} maxLength={2000} className="mt-2 min-h-24 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]" placeholder="Факт, решение или следующий шаг — без секретов и пользовательских данных" />
          </label>
          <Button className="mt-2" disabled={!note.trim()} onClick={() => { onAction(incidentRequest(incident, { note: note.trim() })); setNote(""); }}><MessageSquareText size={15} /> Добавить через preview</Button>
        </Card>

        <div className="space-y-3">
          <Card className="min-h-0">
            <SectionTitle title="Связанные сущности" description="Release, node, ticket и другие ссылки без копирования их бизнес-данных." />
            <div className="space-y-2">
              {incident.linked_entities.map((link) => <div key={link.id} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-xs"><p className="font-semibold">{link.label || link.type}</p><p className="mt-1 font-mono text-[10px] text-[color:var(--atlas-text-muted)]">{link.type}:{link.entity_id}</p></div>)}
              {!incident.linked_entities.length ? <EmptyState title="Связей нет" description="Добавьте ссылку на релиз, ноду или тикет." className="min-h-24" /> : null}
            </div>
            <div className="mt-3 grid gap-2 sm:grid-cols-[0.65fr_1fr]">
              <input aria-label="Тип связанной сущности" value={entityType} onChange={(event) => setEntityType(event.target.value)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm" />
              <input aria-label="ID связанной сущности" value={entityId} onChange={(event) => setEntityId(event.target.value)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm" placeholder="1.2.0-rc.1" />
            </div>
            <Button tone="secondary" className="mt-2" disabled={!entityType.trim() || !entityId.trim()} onClick={() => {
              onAction({ action: "incident.link", target: { type: "incident", id: incident.id }, payload: { expected_version: incident.version, entity_type: entityType.trim(), entity_id: entityId.trim() }, endpoint: "", workspace: "incidents" });
              setEntityId("");
            }}><Link2 size={15} /> Связать</Button>
          </Card>

          <Card className="min-h-0">
            <SectionTitle title="Алерты" description="Acknowledge меняет alert lifecycle; incident authority остаётся отдельным." />
            <div className="space-y-2">{incident.alerts.length ? incident.alerts.map((alert) => <AlertRow key={alert.id} alert={alert} onAction={onAction} />) : <EmptyState title="Алертов нет" description="К этому инциденту ещё не привязаны алерты." className="min-h-24" />}</div>
          </Card>

          <Card className="min-h-0">
            <SectionTitle title="Follow-up" description="Задачи с linked_entity=incident остаются в My Shift после закрытия инцидента." />
            <div className="space-y-2">{incident.follow_up_tasks.length ? incident.follow_up_tasks.map((task) => <div key={task.id} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3 text-xs"><div className="flex justify-between gap-2"><span className="font-semibold">{task.title}</span><Badge tone={task.status === "done" ? "success" : "info"}>{task.status}</Badge></div><p className="mt-1 text-[color:var(--atlas-text-muted)]">{task.next_action || "Следующий шаг не указан"}</p></div>) : <EmptyState title="Follow-up нет" description="Создайте связанную задачу в My Shift, если работа продолжится после закрытия." className="min-h-24" />}</div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export function IncidentRoomPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const loadList = useCallback((signal: AbortSignal) => fetchIncidents({ signal }), []);
  const loadDetail = useCallback((signal: AbortSignal) => {
    if (!selectedId) throw new Error("Инцидент не выбран");
    return fetchIncidentDetail(selectedId, { signal });
  }, [selectedId]);
  const list = useRouteResource("operator-incidents", loadList, { enabled: true, pollMs: POLL_MS });
  const detail = useRouteResource(`operator-incident:${selectedId || "none"}`, loadDetail, { enabled: Boolean(selectedId), pollMs: POLL_MS });

  useEffect(() => {
    const errors = [list.error, selectedId ? detail.error : null].filter((error): error is AdminApiError => error !== null);
    const success = Number(list.data !== null) + Number(detail.data !== null);
    onShellStatus?.({
      api: errors.length ? success ? "degraded" : "failed" : list.loading ? "missing" : "ok",
      session: errors.some((error) => [401, 403].includes(error.status)) ? "failed" : success ? "ok" : errors.length ? "unavailable" : "missing",
      oldestRequiredSourceAt: [list.updatedAt, detail.updatedAt].filter((value): value is string => Boolean(value)).sort().at(0) || null,
    });
  }, [detail.data, detail.error, detail.updatedAt, list.data, list.error, list.loading, list.updatedAt, onShellStatus, selectedId]);

  const active = useMemo(() => (list.data || []).filter((incident) => !["resolved", "cancelled"].includes(incident.workflow_status)), [list.data]);
  const refreshAll = () => { list.reload(); if (selectedId) detail.reload(); };

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={list.error || detail.error ? "warning" : list.data ? "success" : "neutral"}>{list.error || detail.error ? "Есть сбой источника" : list.data ? "Incident authority загружен" : "Загружаем"}</Badge>
          <span>{list.updatedAt ? `Обновлено ${dateTime(list.updatedAt)}` : "Снимок ещё не получен"}</span>
        </div>
        <Button tone="secondary" disabled={list.loading || list.refreshing || detail.refreshing} onClick={refreshAll}><RefreshCw size={15} className={list.refreshing || detail.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      {list.data ? (
        <MetricStrip label="Сводка инцидентов">
          <MetricCell icon={<Siren size={17} />} label="Активные" value={active.length} detail="Investigating, identified, monitoring" tone={active.length ? "danger" : "success"} />
          <MetricCell icon={<ShieldAlert size={17} />} label="Критические" value={active.filter((item) => item.severity === "critical").length} detail="Требуют incident commander" tone={active.some((item) => item.severity === "critical") ? "danger" : "success"} />
          <MetricCell icon={<UsersRound size={17} />} label="Без владельца" value={active.filter((item) => !item.owner_operator_id && !item.owner_team).length} detail="Нужно назначение" tone="warning" />
          <MetricCell icon={<AlertTriangle size={17} />} label="Ждут компенсацию" value={(list.data || []).filter((item) => item.compensation.days > 0 && !item.compensation.completed_at && item.public_status === "resolved").length} detail="L3 + step-up" tone="warning" />
        </MetricStrip>
      ) : null}

      <RouteBoundary loading={list.loading} refreshing={list.refreshing} error={list.error} hasData={list.data !== null} retryLabel="Повторить загрузку инцидентов" onRetry={list.reload}>
        <div className="ops-workspace xl:grid-cols-[minmax(19rem,0.38fr)_minmax(0,1.62fr)]">
          <Card className={`min-h-[420px] p-3 ${selectedId ? "max-xl:hidden" : ""}`}>
            <SectionTitle title="Инциденты" description="Список отсортирован по началу; environment scope применяется сервером." />
            <div className="ops-scrollbar max-h-[calc(100dvh-16rem)] space-y-2 overflow-auto pr-1">
              {(list.data || []).map((incident: OperatorIncident) => (
                <button key={incident.id} type="button" aria-current={selectedId === incident.id ? "true" : undefined} onClick={() => setSelectedId(incident.id)} className={`w-full rounded-[var(--pokrov-radius-card)] border p-3 text-left transition-colors ${selectedId === incident.id ? "border-[color:var(--atlas-border-strong)] bg-[color:var(--pokrov-nav-active-bg)]" : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] hover:border-[color:var(--atlas-border-strong)]"}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2"><Badge tone={severityTone(incident.severity)}>{incident.severity}</Badge><span className="text-[10px] text-[color:var(--atlas-text-muted)]">v{incident.version}</span></div>
                  <p className="mt-2 text-sm font-semibold">{incident.title}</p>
                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{incident.impact || incident.summary}</p>
                  <div className="mt-2 flex items-center justify-between gap-2"><Badge tone={statusTone(incident.workflow_status)}>{statusLabel(incident.workflow_status)}</Badge><span className="text-[10px] text-[color:var(--atlas-text-muted)]">{dateTime(incident.started_at)}</span></div>
                </button>
              ))}
              {!list.data?.length ? <EmptyState title="Инцидентов нет" description="Сервер не вернул инцидентов в текущем environment." /> : null}
            </div>
          </Card>

          <section className={`min-w-0 ${selectedId ? "" : "max-xl:hidden"}`}>
            {selectedId ? <Button tone="ghost" className="mb-2 xl:hidden" onClick={() => setSelectedId(null)}><ArrowLeft size={15} /> Назад к списку</Button> : null}
            {selectedId && detail.loading && !detail.data ? <LoadingState title="Загружаем Incident Room" description="Timeline, links и alerts читаются отдельным запросом." /> : null}
            {selectedId && detail.error && !detail.data ? <ErrorState title="Incident Room недоступен" description={adminApiErrorText(detail.error, "Повторите загрузку карточки.")} action={<Button onClick={detail.reload}>Повторить</Button>} /> : null}
            {detail.data ? <IncidentDetailPanel incident={detail.data} onAction={setRequest} /> : null}
            {!selectedId ? <Card className="hidden min-h-[420px] xl:block"><EmptyState title="Выберите инцидент" description="Карточка загрузит timeline, alerts, links и follow-up tasks." /></Card> : null}
          </section>
        </div>
      </RouteBoundary>

      <ActionIntentDialog
        open={request !== null}
        request={request}
        onOpenChange={(open) => { if (!open) setRequest(null); }}
        onKnownOutcome={refreshAll}
        onCheckState={refreshAll}
      />
    </div>
  );
}
