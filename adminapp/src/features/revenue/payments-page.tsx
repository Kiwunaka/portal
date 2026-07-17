"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw, ShieldCheck } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, SectionTitle, type Tone } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchPaymentOrder, fetchPaymentOrders, fetchPaymentSummary, type PaymentOrder, type PaymentPeriod } from "@/lib/admin-api/revenue";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type PaymentsUrlState = { period: PaymentPeriod; status: string; q: string; selected: string | null };
const PAYMENT_URL_CODECS = {
  period: urlCodecs.enum(["today", "7d", "30d"] as const, "7d"),
  status: urlCodecs.string(""),
  q: urlCodecs.string(""),
  selected: urlCodecs.optionalString(),
};

function finite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberText(value: unknown, suffix = ""): string {
  const normalized = finite(value);
  return normalized === null ? "—" : `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(normalized)}${suffix}`;
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function statusLabel(value: string): string {
  return ({ paid: "Оплачен", created: "Создан", pending: "Ожидает", pending_verification: "Проверка", manual_review: "Ручная проверка", failed: "Ошибка", cancelled: "Отменён", refunded: "Возврат", chargeback: "Чарджбэк" } as Record<string, string>)[value] || value || "—";
}

function statusTone(value: string): Tone {
  if (value === "paid") return "success";
  if (["failed", "cancelled", "refunded", "chargeback"].includes(value)) return "danger";
  if (["manual_review", "pending_verification"].includes(value)) return "warning";
  return "neutral";
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function PaymentsPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<PaymentsUrlState>(() => readUrlState(PAYMENT_URL_CODECS));
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [note, setNote] = useState("");
  const [nextStatus, setNextStatus] = useState("manual_review");
  const [formError, setFormError] = useState("");
  useEffect(() => subscribeToUrlState<PaymentsUrlState>(PAYMENT_URL_CODECS, setUrlState), []);

  const loadSummary = useCallback((signal: AbortSignal) => fetchPaymentSummary(urlState.period, { signal }), [urlState.period]);
  const summary = useRouteResource(`payments-summary:${urlState.period}`, loadSummary, { enabled: true, pollMs: 60_000 });
  const loadOrders = useCallback((signal: AbortSignal) => fetchPaymentOrders({ status: urlState.status, q: urlState.q }, { signal }), [urlState.q, urlState.status]);
  const orders = useRouteResource(`payments-orders:${urlState.status}:${urlState.q}`, loadOrders, { enabled: true, pollMs: 60_000 });
  const selectedHint = useMemo(() => {
    const id = Number(urlState.selected);
    if (!Number.isFinite(id)) return null;
    return [...(orders.data?.orders || []), ...(summary.data?.problem_orders || [])].find((row) => row.id === id) || null;
  }, [orders.data, summary.data, urlState.selected]);
  const loadDetail = useCallback((signal: AbortSignal) => {
    if (!selectedHint) throw new Error("Заказ не выбран.");
    return fetchPaymentOrder(selectedHint.provider, selectedHint.order_id, { signal });
  }, [selectedHint]);
  const detail = useRouteResource(`payment-detail:${selectedHint?.id || "none"}`, loadDetail, { enabled: Boolean(selectedHint) });

  useEffect(() => {
    const errors = [summary.error, orders.error, detail.error].filter(Boolean);
    const hasData = Boolean(summary.data || orders.data || detail.data);
    onShellStatus?.({
      api: errors.length ? hasData ? "degraded" : "failed" : summary.loading || orders.loading ? "missing" : "ok",
      session: errors.some((error) => isAccessDenied(error)) ? "failed" : hasData ? "ok" : errors.length ? "unavailable" : "missing",
      oldestRequiredSourceAt: summary.data?.period.from || null,
    });
  }, [detail.data, detail.error, onShellStatus, orders.data, orders.error, orders.loading, summary.data, summary.error, summary.loading]);

  const columns = useMemo<ColumnDef<PaymentOrder>[]>(() => [
    { header: "Заказ", cell: ({ row }) => <button className="text-left font-semibold hover:underline" onClick={() => replaceUrlState<PaymentsUrlState>({ selected: String(row.original.id) }, PAYMENT_URL_CODECS)}>{row.original.order_id}<span className="block text-[11px] font-normal text-[color:var(--atlas-text-muted)]">{row.original.provider || "— · Нет данных"}</span></button> },
    { header: "Пользователь", cell: ({ row }) => row.original.tg_id === null ? <MissingData /> : <span className="tabular-nums">{row.original.tg_id}</span> },
    { header: "Сумма", cell: ({ row }) => finite(row.original.amount) === null ? <MissingData /> : <span className="tabular-nums">{numberText(row.original.amount)} {row.original.currency || "—"}</span> },
    { header: "Статус заказа", cell: ({ row }) => row.original.status ? <Badge tone={statusTone(row.original.status)}>{statusLabel(row.original.status)}</Badge> : <MissingData /> },
    { header: "Callback", cell: ({ row }) => row.original.last_event?.processed_ok === true ? <Badge tone="success">Обработан</Badge> : row.original.last_event?.processed_ok === false ? <Badge tone="warning">Требует проверки</Badge> : <MissingData /> },
    { header: "Создан", cell: ({ row }) => row.original.created_at ? <span>{dateText(row.original.created_at)}</span> : <MissingData /> },
  ], []);

  function reloadAll() {
    summary.reload();
    orders.reload();
    detail.reload();
  }

  function openReconcile(order: PaymentOrder) {
    const cleanNote = note.trim();
    if (cleanNote.length < 8) {
      setFormError("Добавьте примечание оператора: минимум 8 символов.");
      return;
    }
    setFormError("");
    setRequest({
      action: "payment.reconcile",
      target: { type: "payment", id: String(order.id) },
      payload: { status: nextStatus, note: cleanNote },
      endpoint: `/api/admin/payments/orders/${encodeURIComponent(order.provider)}/${encodeURIComponent(order.order_id)}/reconcile`,
      method: "POST",
    });
    setDialogOpen(true);
  }

  const selected = detail.data || selectedHint;
  const attention = summary.data?.attention;
  const revenue = summary.data?.revenue;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2 text-xs"><Badge tone={summary.error || orders.error ? "warning" : summary.data || orders.data ? "success" : "neutral"}>{summary.error || orders.error ? "Часть источников недоступна" : summary.data || orders.data ? "Платёжные данные получены" : "Платёжные данные ещё не получены"}</Badge><span className="text-[color:var(--atlas-text-soft)]">Callback и provider payload доступны только как безопасные статусы.</span></div>
        <Button tone="secondary" disabled={summary.refreshing || orders.refreshing} onClick={reloadAll}><RefreshCw size={15} className={summary.refreshing || orders.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      <section aria-labelledby="payments-kpi">
        <div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Деньги" description="Выручка, подтверждённые оплаты и диагностические потери. Нулевые значения показаны только когда источник действительно вернул 0." /><label className="text-xs font-semibold">Период<select aria-label="Период платежей" value={urlState.period} onChange={(event) => replaceUrlState<PaymentsUrlState>({ period: event.target.value as PaymentPeriod }, PAYMENT_URL_CODECS)} className="ml-2 min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="today">Сегодня</option><option value="7d">7 дней</option><option value="30d">30 дней</option></select></label></div>
        <RouteBoundary loading={summary.loading} refreshing={summary.refreshing} error={summary.error} hasData={summary.data !== null} retryLabel="Повторить сводку" onRetry={summary.reload}>
          <div id="payments-kpi" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              ["Выручка", revenue?.amount, revenue?.currency ? ` ${revenue.currency}` : ""],
              ["Оплачено", revenue?.paid_count, ""],
              ["Зависшие", attention?.problem_count, ""],
              ["Checkout без оплаты", summary.data?.abandoned.checkout_not_paid, ""],
            ].map(([label, value, suffix]) => <Card key={String(label)}><p className="text-xs text-[color:var(--atlas-text-soft)]">{label}</p>{finite(value) === null ? <div className="mt-2"><MissingData /></div> : <p className="mt-2 text-2xl font-semibold tabular-nums">{numberText(value, String(suffix))}</p>}</Card>)}
          </div>
        </RouteBoundary>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)]">
        <div className="space-y-4">
          <Card><SectionTitle title="Требуют внимания" description="Зависший статус заказа и состояние provider callback показаны раздельно." />{summary.data?.problem_orders.length ? <DataTable data={summary.data.problem_orders} columns={columns} empty="Нет проблемных заказов" /> : summary.data ? <EmptyState title="Очередь пуста" description="Источник не вернул проблемных заказов за выбранный период." /> : <MissingData />}</Card>
          <Card>
            <div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Реестр заказов" description="Поиск не читает и не показывает raw JSON. Браузер не создаёт новые платежи." /><div className="flex flex-wrap gap-2"><input aria-label="Поиск платежей" defaultValue={urlState.q} placeholder="order ID или Telegram ID" onBlur={(event) => replaceUrlState<PaymentsUrlState>({ q: event.target.value }, PAYMENT_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs" /><select aria-label="Статус платежей" value={urlState.status} onChange={(event) => replaceUrlState<PaymentsUrlState>({ status: event.target.value }, PAYMENT_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs"><option value="">Все статусы</option><option value="paid">Оплачен</option><option value="pending">Ожидает</option><option value="manual_review">Ручная проверка</option><option value="failed">Ошибка</option></select></div></div>
            <RouteBoundary loading={orders.loading} refreshing={orders.refreshing} error={orders.error} hasData={orders.data !== null} retryLabel="Повторить реестр" onRetry={orders.reload}>{orders.data?.orders.length ? <DataTable data={orders.data.orders} columns={columns} empty="Нет заказов" /> : orders.data ? <EmptyState description="Заказы не найдены. Это не подтверждение нулевой выручки." /> : null}</RouteBoundary>
          </Card>
        </div>

        <aside aria-label="Карточка платёжного заказа">
          <Card className="xl:sticky xl:top-4">
            <SectionTitle title={selected ? `Заказ ${selected.order_id}` : "Карточка заказа"} description="Детали загружаются после выбора строки; callback evidence остаётся неизменяемым." />
            {!selectedHint ? <EmptyState title="Выберите заказ" description="Откройте строку из очереди или реестра." /> : (
              <RouteBoundary loading={detail.loading} refreshing={detail.refreshing} error={detail.error} hasData={selected !== null} retryLabel="Повторить карточку" onRetry={detail.reload}>
                {selected ? <div className="space-y-3 text-xs">
                  <dl className="grid grid-cols-2 gap-2"><dt className="text-[color:var(--atlas-text-soft)]">Провайдер</dt><dd className="font-semibold">{selected.provider || "— · Нет данных"}</dd><dt className="text-[color:var(--atlas-text-soft)]">Статус заказа</dt><dd>{selected.status ? <Badge tone={statusTone(selected.status)}>{statusLabel(selected.status)}</Badge> : <MissingData />}</dd><dt className="text-[color:var(--atlas-text-soft)]">Состояние callback</dt><dd>{selected.last_event?.processed_ok === true ? "Обработан" : selected.last_event?.processed_ok === false ? "Требует проверки" : <MissingData />}</dd><dt className="text-[color:var(--atlas-text-soft)]">Событий callback</dt><dd className="tabular-nums">{finite(selected.event_count) === null ? "— · Нет данных" : selected.event_count}</dd></dl>
                  <div className="border-t border-[color:var(--atlas-border)] pt-3"><label className="block font-semibold">Новый статус<select aria-label="Статус сверки" value={nextStatus} onChange={(event) => setNextStatus(event.target.value)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="manual_review">Ручная проверка</option><option value="pending_verification">Ожидает проверки</option><option value="paid">Оплачен</option><option value="failed">Ошибка</option><option value="refunded">Возврат</option></select></label><label className="mt-3 block font-semibold">Примечание оператора<textarea aria-label="Примечание сверки" value={note} onChange={(event) => { setNote(event.target.value); setFormError(""); }} className="mt-1 min-h-24 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3" /></label>{formError ? <p role="alert" className="mt-2 text-[color:var(--atlas-status-danger-text)]">{formError}</p> : null}<p className="mt-2 text-[11px] text-[color:var(--atlas-text-muted)]">Не вставляйте provider payload, секреты, callback body, URL подписки или IP.</p><Button tone="primary" className="mt-3" onClick={() => openReconcile(selected)}><ShieldCheck size={15} /> Проверить и сверить</Button></div>
                </div> : null}
              </RouteBoundary>
            )}
          </Card>
        </aside>
      </section>
      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={reloadAll} onCheckState={reloadAll} />
    </div>
  );
}
