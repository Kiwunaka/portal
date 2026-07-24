"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, ArrowLeft, CircleCheck, Clock3, Inbox, RefreshCw } from "lucide-react";

import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import type { AdminApiError } from "@/lib/admin-api/client";
import { fetchTicketDetail, fetchTickets, type AdminTicket, type TicketPriority, type TicketPriorityFilter, type TicketStatusFilter } from "@/lib/admin-api/support";
import { formatSourceAge } from "@/lib/ops-status/presentation";
import { pushUrlState, readUrlState, replaceUrlState, subscribeToUrlState, type UrlStateCodec, type UrlStateCodecs } from "@/lib/url-state";
import { useRouteResource } from "@/lib/use-route-resource";

import { TicketDetail } from "./ticket-detail";

const TICKET_STATUSES = ["active", "open", "in_progress", "closed"] as const;
const TICKET_PRIORITIES = ["all", "critical", "high", "normal", "low"] as const;
const PRIORITY_RANK: Record<TicketPriority, number> = { critical: 4, high: 3, normal: 2, low: 1 };

type TicketsUrlState = {
  status: TicketStatusFilter;
  priority: TicketPriorityFilter;
  selected: number | null;
};

function cleanEnumCodec<T extends string>(values: readonly T[], defaultValue: T): UrlStateCodec<T> {
  const allowed = new Set(values);
  return { parse: (value) => value && allowed.has(value as T) ? value as T : defaultValue, serialize: (value) => value === defaultValue ? null : value };
}

const positiveIdCodec: UrlStateCodec<number | null> = {
  parse: (value) => {
    if (!value || !/^[1-9]\d*$/.test(value)) return null;
    const parsed = Number(value);
    return Number.isSafeInteger(parsed) ? parsed : null;
  },
  serialize: (value) => value !== null && Number.isSafeInteger(value) && value > 0 ? String(value) : null,
};

const TICKETS_URL_CODECS: UrlStateCodecs<TicketsUrlState> = {
  status: cleanEnumCodec<TicketStatusFilter>(TICKET_STATUSES, "active"),
  priority: cleanEnumCodec<TicketPriorityFilter>(TICKET_PRIORITIES, "all"),
  selected: positiveIdCodec,
};

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function priorityLabel(value: TicketPriority): string {
  if (value === "critical") return "Критический";
  if (value === "high") return "Высокий";
  if (value === "normal") return "Обычный";
  return "Низкий";
}

function priorityTone(value: TicketPriority): Tone {
  if (value === "critical") return "danger";
  if (value === "high") return "warning";
  if (value === "normal") return "info";
  return "neutral";
}

function statusLabel(value: string): string {
  if (value === "open") return "Открыт";
  if (value === "in_progress") return "В работе";
  if (value === "closed") return "Закрыт";
  return "Неизвестно";
}

export function sortTicketQueue(rows: readonly AdminTicket[]): AdminTicket[] {
  return [...rows].sort((left, right) => {
    const priority = PRIORITY_RANK[right.priority] - PRIORITY_RANK[left.priority];
    if (priority !== 0) return priority;
    const leftTime = left.updatedAt ? Date.parse(left.updatedAt) : Number.POSITIVE_INFINITY;
    const rightTime = right.updatedAt ? Date.parse(right.updatedAt) : Number.POSITIVE_INFINITY;
    if (leftTime !== rightTime) return leftTime - rightTime;
    return left.id - right.id;
  });
}

export function TicketsPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<TicketsUrlState>(() => readUrlState(TICKETS_URL_CODECS));
  const selected = urlState.selected;
  const listScrollRef = useRef<HTMLDivElement | null>(null);
  const openedFromListRef = useRef(false);

  useEffect(() => subscribeToUrlState<TicketsUrlState>(TICKETS_URL_CODECS, setUrlState), []);

  const loadTickets = useCallback((signal: AbortSignal) => fetchTickets({ status: urlState.status, limit: 100 }, { signal }), [urlState.status]);
  const loadDetail = useCallback((signal: AbortSignal) => {
    if (selected === null) throw new Error("Тикет не выбран");
    return fetchTicketDetail(selected, { signal });
  }, [selected]);
  const tickets = useRouteResource(`tickets:${urlState.status}`, loadTickets, { enabled: true });
  const detail = useRouteResource(`ticket-detail:${selected ?? "none"}`, loadDetail, { enabled: selected !== null });

  const queue = useMemo(() => sortTicketQueue((tickets.data?.tickets || []).filter((ticket) => urlState.priority === "all" || ticket.priority === urlState.priority)), [tickets.data, urlState.priority]);

  useEffect(() => {
    const errors = [tickets.error, selected !== null ? detail.error : null].filter((error): error is AdminApiError => error !== null);
    const successCount = Number(tickets.data !== null) + Number(selected !== null && detail.data !== null);
    const sourceTimes = [tickets.updatedAt, selected !== null ? detail.updatedAt : null]
      .filter((value): value is string => Boolean(value))
      .sort();
    onShellStatus?.({
      api: errors.length ? successCount ? "degraded" : "failed" : tickets.loading ? "missing" : "ok",
      session: errors.some(isAccessDenied) ? "failed" : successCount ? "ok" : errors.length ? "unavailable" : "missing",
      oldestRequiredSourceAt: sourceTimes.at(0) || null,
    });
  }, [detail.data, detail.error, detail.updatedAt, onShellStatus, selected, tickets.data, tickets.error, tickets.loading, tickets.updatedAt]);

  useEffect(() => {
    if (selected !== null) return;
    const scrollTop = Number((window.history.state as { pokrovTicketsListScroll?: unknown } | null)?.pokrovTicketsListScroll);
    if (!Number.isFinite(scrollTop) || scrollTop <= 0) return;
    window.requestAnimationFrame(() => listScrollRef.current?.scrollTo({ top: scrollTop }));
  }, [selected, tickets.data]);

  function selectTicket(ticketId: number) {
    const currentState = window.history.state && typeof window.history.state === "object" ? window.history.state : {};
    window.history.replaceState({ ...currentState, pokrovTicketsListScroll: listScrollRef.current?.scrollTop || 0 }, "");
    openedFromListRef.current = true;
    pushUrlState<TicketsUrlState>({ selected: ticketId }, TICKETS_URL_CODECS);
  }

  function backToTickets() {
    if (openedFromListRef.current) {
      window.history.back();
      return;
    }
    pushUrlState<TicketsUrlState>({ selected: null }, TICKETS_URL_CODECS);
  }

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={tickets.error || (selected !== null && detail.error) ? "warning" : tickets.data ? "success" : "neutral"}>{tickets.error || (selected !== null && detail.error) ? "Есть сбой источника" : tickets.data ? "Очередь загружена" : "Ожидаем очередь"}</Badge>
          <span>{tickets.data ? `${queue.length} тикетов по фильтру` : "Очередь ещё не получена"}</span>
          {tickets.refreshing || detail.refreshing ? <Badge tone="info">Обновляем</Badge> : null}
        </div>
        <Button tone="secondary" disabled={tickets.loading || tickets.refreshing || detail.refreshing} onClick={() => { tickets.reload(); if (selected !== null) detail.reload(); }}><RefreshCw size={15} className={tickets.refreshing || detail.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      {tickets.data ? (
        <MetricStrip label="Сводка тикетов">
          <MetricCell icon={<Inbox aria-hidden="true" size={17} />} label="По текущему фильтру" value={queue.length} detail={`Статус: ${urlState.status}`} tone={queue.length ? "info" : "success"} />
          <MetricCell icon={<AlertTriangle aria-hidden="true" size={17} />} label="Критические" value={queue.filter((ticket) => ticket.priority === "critical").length} detail="Сортируются первыми" tone={queue.some((ticket) => ticket.priority === "critical") ? "danger" : "success"} />
          <MetricCell icon={<Clock3 aria-hidden="true" size={17} />} label="В работе" value={queue.filter((ticket) => ticket.status === "in_progress").length} detail="Оператор уже начал разбор" tone="warning" />
          <MetricCell icon={<CircleCheck aria-hidden="true" size={17} />} label="Закрытые" value={(tickets.data.tickets || []).filter((ticket) => ticket.status === "closed").length} detail="В загруженном ответе" tone="success" />
        </MetricStrip>
      ) : null}

      <div className="ops-workspace xl:grid-cols-[minmax(21rem,0.72fr)_minmax(0,1.28fr)]">
        <section aria-label="Очередь тикетов" className={`min-w-0 ${selected !== null ? "max-xl:hidden" : ""}`}>
          <Card className="min-h-[420px] p-3">
            <SectionTitle title="Очередь тикетов" description="Сначала критический приоритет, затем высокий и более старые обращения. Выбор и фильтры сохраняются в URL." />
            <div className="grid gap-2 sm:grid-cols-2">
              <select aria-label="Статус тикетов" value={urlState.status} onChange={(event) => replaceUrlState<TicketsUrlState>({ status: event.target.value as TicketStatusFilter, selected: null }, TICKETS_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]">
                <option value="active">Активные</option>
                <option value="open">Открытые</option>
                <option value="in_progress">В работе</option>
                <option value="closed">Закрытые</option>
              </select>
              <select aria-label="Приоритет тикетов" value={urlState.priority} onChange={(event) => replaceUrlState<TicketsUrlState>({ priority: event.target.value as TicketPriorityFilter, selected: null }, TICKETS_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]">
                <option value="all">Все приоритеты</option>
                <option value="critical">Критический</option>
                <option value="high">Высокий</option>
                <option value="normal">Обычный</option>
                <option value="low">Низкий</option>
              </select>
            </div>

            <div className="mt-3">
              <RouteBoundary loading={tickets.loading} refreshing={tickets.refreshing} error={tickets.error} hasData={tickets.data !== null} retryLabel="Повторить загрузку тикетов" onRetry={tickets.reload}>
                {queue.length ? (
                  <div ref={listScrollRef} className="ops-scrollbar max-h-[calc(100dvh-19rem)] space-y-2 overflow-auto pr-1">
                    {queue.map((ticket) => (
                      <button key={ticket.id} type="button" aria-current={selected === ticket.id ? "true" : undefined} onClick={() => selectTicket(ticket.id)} className={`w-full rounded-[var(--pokrov-radius-card)] border p-3 text-left transition-colors ${selected === ticket.id ? "border-[color:var(--atlas-border-strong)] bg-[color:var(--pokrov-nav-active-bg)]" : "border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] hover:border-[color:var(--atlas-border-strong)]"}`}>
                        <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-semibold">Тикет #{ticket.id}</span><div className="flex gap-2"><Badge tone={priorityTone(ticket.priority)}>{priorityLabel(ticket.priority)}</Badge><Badge tone={ticket.status === "open" ? "warning" : ticket.status === "closed" ? "success" : "info"}>{statusLabel(ticket.status)}</Badge></div></div>
                        <p className="mt-2 text-sm font-semibold">{ticket.subject}</p>
                        <p className="mt-1 line-clamp-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{ticket.lastMessagePreview || "Нет сообщения"}</p>
                        <div className="mt-2 flex flex-wrap justify-between gap-2 text-[11px] text-[color:var(--atlas-text-muted)]"><span>Пользователь {ticket.userTgId}</span><span>{ticket.updatedAt ? formatSourceAge(ticket.updatedAt) : "Возраст неизвестен"}</span></div>
                      </button>
                    ))}
                  </div>
                ) : tickets.data ? <EmptyState title="Тикеты не найдены" description="По текущим фильтрам очередь пуста." className="min-h-32" /> : null}
              </RouteBoundary>
            </div>
          </Card>
        </section>

        <section aria-label="Карточка тикета" className={`min-w-0 ${selected !== null ? "" : "max-xl:hidden"}`}>
          {selected === null ? <Card className="hidden min-h-[420px] xl:block"><EmptyState title="Выберите тикет" description="Полная переписка загрузится отдельным запросом после выбора строки." /></Card> : null}
          {selected !== null ? <Button tone="ghost" className="mb-2 xl:hidden" onClick={backToTickets}><ArrowLeft size={15} /> Назад к очереди</Button> : null}
          {selected !== null && detail.loading && !detail.data ? <LoadingState title="Загружаем полную переписку" description="Очередь остаётся доступна, сообщения запрашиваются отдельно." /> : null}
          {selected !== null && detail.error && !detail.data ? <ErrorState title="Тикет недоступен" description={adminApiErrorText(detail.error, "Повторите загрузку полной переписки.")} action={<Button tone="secondary" onClick={detail.reload}>Повторить загрузку</Button>} /> : null}
          {selected !== null && detail.data ? <TicketDetail ticket={detail.data} onRefresh={() => { tickets.reload(); detail.reload(); }} /> : null}
        </section>
      </div>
    </div>
  );
}
