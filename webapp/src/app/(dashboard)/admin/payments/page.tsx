"use client";

import {
  AdminBadge,
  AdminEmptyState,
  AdminPanelHeader,
  adminButtonClass,
  adminFieldClass,
  adminPanelClass,
  adminTableShellClass,
  adminTextAreaClass,
} from "@/components/admin/admin-shell";
import { adminPaymentOrders, adminPaymentReconcile, type AdminPaymentOrder } from "@/lib/api";
import { RefreshCw, Search } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

const STATUS_OPTIONS = ["", "created", "pending", "paid", "failed", "cancelled", "refunded", "chargeback", "manual_review", "pending_verification"];
const RECONCILE_STATUSES = ["manual_review", "pending", "paid", "failed", "cancelled", "refunded", "chargeback"];
const STATUS_LABELS: Record<string, string> = {
  created: "Создан",
  pending: "Ожидает",
  paid: "Оплачен",
  failed: "Ошибка",
  cancelled: "Отменён",
  refunded: "Возврат",
  chargeback: "Chargeback",
  manual_review: "Ручная проверка",
  pending_verification: "Ждёт проверки",
};

function errorMessage(err: unknown, fallback: string): string {
  return String((err as { message?: string })?.message || err || fallback);
}

function statusTone(status: string): "neutral" | "success" | "warning" | "danger" | "accent" {
  const value = String(status || "").toLowerCase();
  if (value === "paid") return "success";
  if (["failed", "cancelled", "refunded", "chargeback"].includes(value)) return "danger";
  if (["manual_review", "pending_verification"].includes(value)) return "warning";
  if (value === "pending") return "accent";
  return "neutral";
}

function money(order: AdminPaymentOrder): string {
  return `${Number(order.amount || 0).toLocaleString("ru-RU")} ${order.currency || "RUB"}`;
}

function statusLabel(status: string): string {
  return STATUS_LABELS[String(status || "").toLowerCase()] || status || "Без статуса";
}

type ReconcileDialog = {
  order: AdminPaymentOrder;
  status: string;
  note: string;
} | null;

export default function AdminPaymentsPage() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [orders, setOrders] = useState<AdminPaymentOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState(() => searchParams.get("status") || "");
  const [provider, setProvider] = useState(() => searchParams.get("provider") || "");
  const [query, setQuery] = useState(() => searchParams.get("q") || "");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [okMessage, setOkMessage] = useState("");
  const [dialog, setDialog] = useState<ReconcileDialog>(null);

  const providers = useMemo(() => Array.from(new Set(orders.map((order) => order.provider).filter(Boolean))).sort(), [orders]);

  const syncFilters = useCallback(
    (next: { status?: string; provider?: string; q?: string }) => {
      const nextStatus = next.status ?? status;
      const nextProvider = next.provider ?? provider;
      const nextQuery = next.q ?? query;
      const params = new URLSearchParams();
      if (nextStatus) params.set("status", nextStatus);
      if (nextProvider) params.set("provider", nextProvider);
      if (nextQuery.trim()) params.set("q", nextQuery.trim());
      const suffix = params.toString();
      router.replace(suffix ? `${pathname}?${suffix}` : pathname, { scroll: false });
    },
    [pathname, provider, query, router, status],
  );

  useEffect(() => {
    setStatus(searchParams.get("status") || "");
    setProvider(searchParams.get("provider") || "");
    setQuery(searchParams.get("q") || "");
  }, [searchParams]);

  const loadOrders = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError("");
    try {
      const payload = await adminPaymentOrders({
        status: status || undefined,
        provider: provider || undefined,
        q: query.trim() || undefined,
        limit: 100,
      });
      setOrders(payload.orders);
      setTotal(payload.total);
    } catch (err) {
      setError(errorMessage(err, "Не удалось загрузить платёжный журнал."));
    } finally {
      setLoading(false);
    }
  }, [provider, query, status]);

  useEffect(() => {
    void loadOrders();
  }, [loadOrders]);

  const openReconcile = (order: AdminPaymentOrder): void => {
    setDialog({ order, status: order.status || "manual_review", note: "" });
    setError("");
    setOkMessage("");
  };

  const saveReconcile = async (): Promise<void> => {
    if (!dialog) return;
    const note = dialog.note.trim();
    if (!note) {
      setError("Для ручной сверки нужна заметка аудита.");
      return;
    }
    setBusy(true);
    setError("");
    setOkMessage("");
    try {
      const payload = await adminPaymentReconcile({
        provider: dialog.order.provider,
        order_id: dialog.order.order_id,
        status: dialog.status,
        note,
      });
      setOrders((current) =>
        current.map((order) =>
          order.provider === payload.order.provider && order.order_id === payload.order.order_id ? payload.order : order,
        ),
      );
      setDialog(null);
      setOkMessage("Сверка сохранена. Доступ пользователя автоматически не менялся.");
    } catch (err) {
      setError(errorMessage(err, "Не удалось сохранить заметку сверки."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="paid beta finance"
          title="Платёжный журнал"
          description="Реальные заказы и callback-события из backend. Ручная сверка требует заметку аудита и не выдаёт доступ молча."
          actions={
            <button type="button" className={adminButtonClass("secondary", "sm")} onClick={() => void loadOrders()} disabled={loading}>
              <RefreshCw size={14} />
              Обновить
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="accent">заказов: {total}</AdminBadge>
          <AdminBadge tone="warning">ручная проверка видна оператору</AdminBadge>
          <AdminBadge>сырые payload провайдера не выводятся</AdminBadge>
        </div>
      </article>

      <article className={adminPanelClass("neutral")}>
        <div className="grid gap-3 lg:grid-cols-[minmax(180px,0.8fr),minmax(180px,0.8fr),minmax(220px,1fr),auto]">
          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              syncFilters({ status: event.target.value });
            }}
            className={adminFieldClass}
            aria-label="Статус платежа"
          >
            {STATUS_OPTIONS.map((item) => (
              <option key={item || "all"} value={item}>
                {item ? statusLabel(item) : "Все статусы"}
              </option>
            ))}
          </select>
          <select
            value={provider}
            onChange={(event) => {
              setProvider(event.target.value);
              syncFilters({ provider: event.target.value });
            }}
            className={adminFieldClass}
            aria-label="Провайдер"
          >
            <option value="">Все провайдеры</option>
            {providers.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <label className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                syncFilters({ q: event.target.value });
              }}
              className={`${adminFieldClass} pl-9`}
              placeholder="заказ, провайдер, план, кампания, Telegram ID"
            />
          </label>
          <button type="button" className={adminButtonClass("primary")} onClick={() => void loadOrders()} disabled={loading}>
            Найти
          </button>
        </div>
      </article>

      {okMessage ? <div className={`${adminPanelClass("success")} text-sm`}>{okMessage}</div> : null}
      {error ? <div className={`${adminPanelClass("danger")} text-sm`}>{error}</div> : null}

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="orders and callbacks"
          title="Заказы провайдера"
          description="Строки идут из backend-таблиц оплаты. Callback показывается кратко, без печати полного payload."
        />

        {loading ? (
          <div className="grid gap-3 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-24 animate-pulse rounded-[1rem] bg-slate-100" />
            ))}
          </div>
        ) : orders.length ? (
          <div className={adminTableShellClass}>
            <div className="overflow-auto">
              <table className="min-w-[980px] text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                    <th className="px-3 py-3">Заказ</th>
                    <th className="px-3 py-3">Пользователь</th>
                    <th className="px-3 py-3">План</th>
                    <th className="px-3 py-3">Сумма</th>
                    <th className="px-3 py-3">Статус</th>
                    <th className="px-3 py-3">Callback</th>
                    <th className="px-3 py-3">Создан</th>
                    <th className="px-3 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={`${order.provider}:${order.order_id}`} className="border-t border-slate-200 align-top text-slate-700">
                      <td className="px-3 py-3">
                        <p className="font-mono font-semibold text-slate-900">{order.order_id}</p>
                        <p className="mt-1 text-slate-500">{order.provider}</p>
                        {order.source ? <p className="mt-1 text-slate-500">источник: {order.source}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        <p>{order.user?.display_name || order.user?.username || (order.tg_id ? `#${order.tg_id}` : "-")}</p>
                        {order.tg_id ? <p className="mt-1 text-slate-500">tg: {order.tg_id}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        <p>{order.plan_code || "-"}</p>
                        {order.promo_code ? <p className="mt-1 text-slate-500">promo: {order.promo_code}</p> : null}
                        {order.campaign ? <p className="mt-1 text-slate-500">кампания: {order.campaign}</p> : null}
                      </td>
                      <td className="px-3 py-3">{money(order)}</td>
                      <td className="px-3 py-3">
                        <AdminBadge tone={statusTone(order.status)}>{statusLabel(order.status)}</AdminBadge>
                        <p className="mt-1 font-mono text-[11px] text-slate-400">{order.status || "-"}</p>
                        {order.paid_at ? <p className="mt-2 text-slate-500">оплачен: {fmtRuDate(order.paid_at)}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        {order.last_event ? (
                          <div className="space-y-1">
                            <p>{order.last_event.event_type}</p>
                            <p className="font-mono text-slate-400">{order.last_event.external_id}</p>
                            <p className={order.last_event.signature_ok ? "text-emerald-700" : "text-rose-700"}>
                              подпись {order.last_event.signature_ok ? "ok" : "bad"}
                            </p>
                            <p className={order.last_event.processed_ok ? "text-emerald-700" : "text-amber-700"}>
                              обработка {order.last_event.processed_ok ? "ok" : "нужна проверка"}
                            </p>
                            <p className="text-slate-500">событий: {order.event_count}</p>
                          </div>
                        ) : (
                          <span className="text-slate-500">callback не было</span>
                        )}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">{fmtRuDate(order.created_at)}</td>
                      <td className="px-3 py-3">
                        <button type="button" className={adminButtonClass("secondary", "xs")} onClick={() => openReconcile(order)}>
                          Сверка
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <AdminEmptyState
            title="Backend не вернул платёжные заказы"
            description="Это явное пустое состояние, а не счётчик выручки и не фиктивный успешный экран."
          />
        )}
      </article>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-xl`}>
            <AdminPanelHeader
              eyebrow="ручная сверка"
              title={`Заказ ${dialog.order.order_id}`}
              description="Запишите, что именно проверил оператор. Действие обновляет состояние журнала и пишет audit-метаданные; доступ само по себе не выдаёт."
            />
            <label className="block text-sm">
              <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">статус</span>
              <select value={dialog.status} onChange={(event) => setDialog({ ...dialog, status: event.target.value })} className={adminFieldClass}>
                {RECONCILE_STATUSES.map((item) => (
                  <option key={item} value={item}>
                    {statusLabel(item)}
                  </option>
                ))}
              </select>
            </label>
            <label className="mt-3 block text-sm">
              <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">заметка аудита</span>
              <textarea
                value={dialog.note}
                onChange={(event) => setDialog({ ...dialog, note: event.target.value })}
                className={adminTextAreaClass}
                placeholder="Что видно в кабинете провайдера, какой пользователь или тикет связан с заказом, почему выбран этот статус."
                rows={5}
              />
            </label>
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button type="button" className={adminButtonClass("secondary")} onClick={() => setDialog(null)} disabled={busy}>
                Отмена
              </button>
              <button type="button" className={adminButtonClass("primary")} onClick={() => void saveReconcile()} disabled={busy}>
                Сохранить сверку
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
