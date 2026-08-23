"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  ClipboardList,
  CreditCard,
  RefreshCw,
  ShieldAlert,
  Ticket,
  UserRoundCheck,
  UsersRound,
} from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchShift, type OperatorTask, type ShiftQueueItem } from "@/lib/admin-api/work";
import { useRouteResource } from "@/lib/use-route-resource";

const POLL_MS = 45_000;

function priorityTone(priority: OperatorTask["priority"]): Tone {
  if (priority === "critical") return "danger";
  if (priority === "high") return "warning";
  if (priority === "normal") return "info";
  return "neutral";
}

function priorityLabel(priority: OperatorTask["priority"]): string {
  return { critical: "Критично", high: "Высокий", normal: "Обычный", low: "Низкий" }[priority];
}

function statusLabel(status: string): string {
  return {
    open: "Открыта",
    in_progress: "В работе",
    blocked: "Заблокирована",
    done: "Готово",
    cancelled: "Отменена",
  }[status] || status;
}

function TaskRow({
  task,
  operatorId,
  onAction,
}: {
  task: OperatorTask;
  operatorId: string;
  onAction: (request: ActionIntentRequest) => void;
}) {
  const owned = task.owner_operator_id === operatorId;
  const open = task.status !== "done" && task.status !== "cancelled";
  const nextStatus = task.status === "in_progress" ? "done" : "in_progress";
  const actionLabel = task.status === "in_progress" ? "Завершить" : owned ? "Начать" : "Взять";
  const payload: Record<string, unknown> = {
    expected_version: task.version,
    status: nextStatus,
    next_action: nextStatus === "done" ? "Проверить закрытие по источнику" : task.next_action,
  };
  if (!owned) payload.owner_operator_id = operatorId;

  return (
    <article className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-[color:var(--atlas-text)]">{task.title}</p>
          <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">
            {task.next_action || "Следующее действие не зафиксировано"}
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge tone={priorityTone(task.priority)}>{priorityLabel(task.priority)}</Badge>
          <Badge tone={task.status === "blocked" ? "danger" : task.status === "in_progress" ? "warning" : "neutral"}>
            {statusLabel(task.status)}
          </Badge>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[11px] text-[color:var(--atlas-text-muted)]">
        <span>{task.owner_team ? `Команда: ${task.owner_team}` : task.owner_operator_id ? "Назначена оператору" : "Без владельца"}</span>
        <span>{task.due_at ? new Date(task.due_at).toLocaleString("ru-RU") : `Источник: ${task.source}`}</span>
      </div>
      {open ? (
        <Button
          tone={nextStatus === "done" ? "primary" : "secondary"}
          size="compact"
          className="mt-3 w-full sm:w-auto"
          onClick={() => onAction({
            action: "operator_task.update",
            target: { type: "operator_task", id: task.id },
            payload,
            endpoint: "",
            workspace: "shift",
          })}
        >
          {nextStatus === "done" ? <CheckCircle2 size={15} /> : <UserRoundCheck size={15} />}
          {actionLabel}
        </Button>
      ) : null}
    </article>
  );
}

function TaskQueue({
  title,
  description,
  tasks,
  operatorId,
  onAction,
}: {
  title: string;
  description: string;
  tasks: OperatorTask[];
  operatorId: string;
  onAction: (request: ActionIntentRequest) => void;
}) {
  return (
    <section>
      <div className="mb-2 flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="text-[11px] text-[color:var(--atlas-text-muted)]">{description}</p>
        </div>
        <Badge tone={tasks.length ? "info" : "success"}>{tasks.length}</Badge>
      </div>
      <div className="space-y-2">
        {tasks.length ? tasks.map((task) => (
          <TaskRow key={task.id} task={task} operatorId={operatorId} onAction={onAction} />
        )) : <EmptyState title="Очередь пуста" description="Сервер не вернул активных задач для этой группы." className="min-h-24" />}
      </div>
    </section>
  );
}

function AttentionQueue({
  icon,
  title,
  items,
  empty,
}: {
  icon: ReactNode;
  title: string;
  items: ShiftQueueItem[];
  empty: string;
}) {
  return (
    <Card className="min-h-0 p-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold">{icon}{title}</h3>
        <Badge tone={items.length ? "warning" : "success"}>{items.length}</Badge>
      </div>
      <div className="mt-3 space-y-2">
        {items.slice(0, 5).map((item, index) => (
          <div key={String(item.id ?? item.intent_id ?? `${title}-${index}`)} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 py-2">
            <p className="truncate text-xs font-semibold">{String(item.title || item.action || item.issue_code || item.order_id || `Запись ${item.id || index + 1}`)}</p>
            <p className="mt-1 truncate text-[10px] text-[color:var(--atlas-text-muted)]">{String(item.status || item.severity || item.provider || "Требует разбора")}</p>
          </div>
        ))}
        {!items.length ? <p className="text-xs leading-5 text-[color:var(--atlas-text-muted)]">{empty}</p> : null}
      </div>
    </Card>
  );
}

export function ShiftPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const load = useCallback((signal: AbortSignal) => fetchShift({ signal }), []);
  const resource = useRouteResource("operator-shift", load, { enabled: true, pollMs: POLL_MS });

  useEffect(() => {
    const denied = resource.error && [401, 403].includes(resource.error.status);
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: denied ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.updatedAt,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading, resource.updatedAt]);

  const actionCount = useMemo(() => resource.data
    ? resource.data.failed_commands.length
      + resource.data.tickets.length
      + resource.data.incident_work.length
      + resource.data.payment_review.length
      + resource.data.release_blockers.length
      + resource.data.source_failures.length
    : 0, [resource.data]);

  function openAction(next: ActionIntentRequest) {
    setRequest(next);
  }

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>
            {resource.error ? "Смена частично недоступна" : resource.data ? `Контур ${resource.data.environment}` : "Загружаем смену"}
          </Badge>
          <span>{resource.updatedAt ? `Обновлено ${new Date(resource.updatedAt).toLocaleString("ru-RU")}` : "Первый снимок ещё не получен"}</span>
        </div>
        <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}>
          <RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      {resource.data ? (
        <MetricStrip label="Сводка смены">
          <MetricCell icon={<ClipboardList size={17} />} label="Мои задачи" value={resource.data.mine.length} detail="Я — текущий владелец" tone={resource.data.mine.length ? "info" : "success"} />
          <MetricCell icon={<UsersRound size={17} />} label="Командные" value={resource.data.team.length} detail={resource.data.teams.join(", ") || "Команда не назначена"} tone="neutral" />
          <MetricCell icon={<ShieldAlert size={17} />} label="Активные инциденты" value={resource.data.incident_work.length} detail="Investigating, identified, monitoring" tone={resource.data.incident_work.length ? "danger" : "success"} />
          <MetricCell icon={<CircleDot size={17} />} label="Всего внимания" value={actionCount} detail="Шесть серверных очередей" tone={actionCount ? "warning" : "success"} />
        </MetricStrip>
      ) : null}

      <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку смены" onRetry={resource.reload}>
        {resource.data ? (
          <div className="ops-workspace xl:grid-cols-[minmax(0,1.18fr)_minmax(20rem,0.82fr)]">
            <Card className="min-h-0">
              <SectionTitle title="Работа смены" description="Мои, командные и неназначенные задачи читаются из одной модели. Любой переход требует server preview и совпадения версии." />
              <div className="space-y-5">
                <TaskQueue title="Мои" description="Задачи, назначенные текущему оператору" tasks={resource.data.mine} operatorId={resource.data.operator_id} onAction={openAction} />
                <TaskQueue title="Команда" description="Работа по активным ролям смены" tasks={resource.data.team.filter((task) => !resource.data!.mine.some((mine) => mine.id === task.id))} operatorId={resource.data.operator_id} onAction={openAction} />
                <TaskQueue title="Без владельца" description="Можно взять на себя через action-intent" tasks={resource.data.unassigned} operatorId={resource.data.operator_id} onAction={openAction} />
              </div>
            </Card>

            <section aria-label="Очереди внимания" className="grid content-start gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <AttentionQueue icon={<AlertTriangle size={15} />} title="Сбойные команды" items={resource.data.failed_commands} empty="Неопределённых или упавших команд нет." />
              <AttentionQueue icon={<Ticket size={15} />} title="Тикеты" items={resource.data.tickets} empty="Активных тикетов нет." />
              <AttentionQueue icon={<ShieldAlert size={15} />} title="Инциденты" items={resource.data.incident_work as unknown as ShiftQueueItem[]} empty="Активных инцидентов нет." />
              <AttentionQueue icon={<CreditCard size={15} />} title="Платёжная проверка" items={resource.data.payment_review} empty="Платежи не ждут ручной проверки." />
              <AttentionQueue icon={<CircleDot size={15} />} title="Блокеры релиза" items={resource.data.release_blockers} empty="Открытых блокеров релиза нет." />
              <AttentionQueue icon={<AlertTriangle size={15} />} title="Сбои источников" items={resource.data.source_failures as unknown as ShiftQueueItem[]} empty="Источники не сообщают активных сбоев." />
            </section>
          </div>
        ) : null}
      </RouteBoundary>

      {resource.error && resource.data ? (
        <Card className="border-[color:var(--atlas-status-warning-line)] text-xs text-[color:var(--atlas-status-warning-text)]">
          {adminApiErrorText(resource.error as AdminApiError, "Последний успешный снимок оставлен на экране.")}
        </Card>
      ) : null}

      <ActionIntentDialog
        open={request !== null}
        request={request}
        onOpenChange={(open) => { if (!open) setRequest(null); }}
        onKnownOutcome={resource.reload}
        onCheckState={resource.reload}
      />
    </div>
  );
}
