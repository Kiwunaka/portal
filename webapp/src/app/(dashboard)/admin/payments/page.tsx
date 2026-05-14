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
import { useCallback, useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

const STATUS_OPTIONS = ["", "created", "pending", "paid", "failed", "cancelled", "refunded", "chargeback", "manual_review", "pending_verification"];
const RECONCILE_STATUSES = ["manual_review", "pending", "paid", "failed", "cancelled", "refunded", "chargeback"];

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

type ReconcileDialog = {
  order: AdminPaymentOrder;
  status: string;
  note: string;
} | null;

export default function AdminPaymentsPage() {
  const [orders, setOrders] = useState<AdminPaymentOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState("");
  const [provider, setProvider] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [okMessage, setOkMessage] = useState("");
  const [dialog, setDialog] = useState<ReconcileDialog>(null);

  const providers = useMemo(() => Array.from(new Set(orders.map((order) => order.provider).filter(Boolean))).sort(), [orders]);

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
      setError(errorMessage(err, "Payment ledger is unavailable."));
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
      setError("Audit note is required for manual reconciliation.");
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
      setOkMessage("Reconciliation note saved. No access was changed automatically.");
    } catch (err) {
      setError(errorMessage(err, "Could not save reconciliation note."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="paid beta finance"
          title="Payment ledger"
          description="Real backend order and callback records. Manual reconciliation requires an audit note and does not silently change user access."
          actions={
            <button type="button" className={adminButtonClass("secondary", "sm")} onClick={() => void loadOrders()} disabled={loading}>
              <RefreshCw size={14} />
              Refresh
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="accent">orders: {total}</AdminBadge>
          <AdminBadge tone="warning">manual review stays visible</AdminBadge>
          <AdminBadge>no raw provider payloads</AdminBadge>
        </div>
      </article>

      <article className={adminPanelClass("neutral")}>
        <div className="grid gap-3 lg:grid-cols-[minmax(180px,0.8fr),minmax(180px,0.8fr),minmax(220px,1fr),auto]">
          <select value={status} onChange={(event) => setStatus(event.target.value)} className={adminFieldClass} aria-label="Payment status">
            {STATUS_OPTIONS.map((item) => (
              <option key={item || "all"} value={item}>
                {item || "all statuses"}
              </option>
            ))}
          </select>
          <select value={provider} onChange={(event) => setProvider(event.target.value)} className={adminFieldClass} aria-label="Provider">
            <option value="">all providers</option>
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
              onChange={(event) => setQuery(event.target.value)}
              className={`${adminFieldClass} pl-9`}
              placeholder="order, provider, plan, campaign, Telegram ID"
            />
          </label>
          <button type="button" className={adminButtonClass("primary")} onClick={() => void loadOrders()} disabled={loading}>
            Search
          </button>
        </div>
      </article>

      {okMessage ? <div className={`${adminPanelClass("success")} text-sm`}>{okMessage}</div> : null}
      {error ? <div className={`${adminPanelClass("danger")} text-sm`}>{error}</div> : null}

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="orders and callbacks"
          title="Provider order records"
          description="Rows come from backend payment tables. Callback payloads are intentionally summarized, not printed."
        />

        {loading ? (
          <div className="grid gap-3 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-24 animate-pulse rounded-[1rem] bg-[#111922]" />
            ))}
          </div>
        ) : orders.length ? (
          <div className={adminTableShellClass}>
            <div className="overflow-auto">
              <table className="min-w-[980px] text-left text-xs">
                <thead>
                  <tr className="border-b border-[#22303c] bg-[#101821] text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                    <th className="px-3 py-3">Order</th>
                    <th className="px-3 py-3">User</th>
                    <th className="px-3 py-3">Plan</th>
                    <th className="px-3 py-3">Amount</th>
                    <th className="px-3 py-3">Status</th>
                    <th className="px-3 py-3">Callback</th>
                    <th className="px-3 py-3">Created</th>
                    <th className="px-3 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={`${order.provider}:${order.order_id}`} className="border-t border-[#22303c] align-top">
                      <td className="px-3 py-3">
                        <p className="font-mono text-slate-100">{order.order_id}</p>
                        <p className="mt-1 text-slate-500">{order.provider}</p>
                        {order.source ? <p className="mt-1 text-slate-500">source: {order.source}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        <p>{order.user?.display_name || order.user?.username || (order.tg_id ? `#${order.tg_id}` : "-")}</p>
                        {order.tg_id ? <p className="mt-1 text-slate-500">tg: {order.tg_id}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        <p>{order.plan_code || "-"}</p>
                        {order.promo_code ? <p className="mt-1 text-slate-500">promo: {order.promo_code}</p> : null}
                        {order.campaign ? <p className="mt-1 text-slate-500">campaign: {order.campaign}</p> : null}
                      </td>
                      <td className="px-3 py-3">{money(order)}</td>
                      <td className="px-3 py-3">
                        <AdminBadge tone={statusTone(order.status)}>{order.status}</AdminBadge>
                        {order.paid_at ? <p className="mt-2 text-slate-500">paid: {fmtRuDate(order.paid_at)}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        {order.last_event ? (
                          <div className="space-y-1">
                            <p>{order.last_event.event_type}</p>
                            <p className="font-mono text-slate-400">{order.last_event.external_id}</p>
                            <p className={order.last_event.signature_ok ? "text-emerald-300" : "text-rose-300"}>
                              signature {order.last_event.signature_ok ? "ok" : "bad"}
                            </p>
                            <p className={order.last_event.processed_ok ? "text-emerald-300" : "text-amber-300"}>
                              processed {order.last_event.processed_ok ? "ok" : "needs review"}
                            </p>
                            <p className="text-slate-500">events: {order.event_count}</p>
                          </div>
                        ) : (
                          <span className="text-slate-500">no callbacks</span>
                        )}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">{fmtRuDate(order.created_at)}</td>
                      <td className="px-3 py-3">
                        <button type="button" className={adminButtonClass("secondary", "xs")} onClick={() => openReconcile(order)}>
                          Reconcile
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
            title="No payment orders returned by the backend"
            description="This is an explicit empty state. It is not a revenue counter and not a fake success screen."
          />
        )}
      </article>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-xl`}>
            <AdminPanelHeader
              eyebrow="manual reconciliation"
              title={`Order ${dialog.order.order_id}`}
              description="Record what the operator verified. This action updates the ledger state and writes admin audit metadata; it does not grant access by itself."
            />
            <label className="block text-sm">
              <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">status</span>
              <select value={dialog.status} onChange={(event) => setDialog({ ...dialog, status: event.target.value })} className={adminFieldClass}>
                {RECONCILE_STATUSES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="mt-3 block text-sm">
              <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">audit note</span>
              <textarea
                value={dialog.note}
                onChange={(event) => setDialog({ ...dialog, note: event.target.value })}
                className={adminTextAreaClass}
                placeholder="Provider dashboard result, user/ticket context, and why this state is correct."
                rows={5}
              />
            </label>
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button type="button" className={adminButtonClass("secondary")} onClick={() => setDialog(null)} disabled={busy}>
                Cancel
              </button>
              <button type="button" className={adminButtonClass("primary")} onClick={() => void saveReconcile()} disabled={busy}>
                Save reconciliation
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
