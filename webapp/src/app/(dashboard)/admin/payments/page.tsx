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
import { adminPaymentOrders, adminPaymentReconcile, adminPaymentResendAccessKeyEmail, type AdminPaymentOrder } from "@/lib/api";
import { RefreshCw, Search, Send } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

const STATUS_OPTIONS = ["", "created", "pending", "paid", "failed", "cancelled", "refunded", "chargeback", "manual_review", "pending_verification"];
const RECONCILE_STATUSES = ["manual_review", "pending", "paid", "failed", "cancelled", "refunded", "chargeback"];
const STATUS_LABELS: Record<string, string> = {
  "": "все статусы",
  created: "создан",
  pending: "ожидает",
  paid: "оплачен",
  failed: "ошибка",
  cancelled: "отменен",
  refunded: "возврат",
  chargeback: "чарджбек",
  manual_review: "ручная проверка",
  pending_verification: "ждет подтверждения",
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

function fulfillmentTone(status?: string | null): "neutral" | "success" | "warning" | "danger" | "accent" {
  const value = String(status || "").toLowerCase();
  if (["email_sent", "sent", "access_granted", "redeemed"].includes(value)) return "success";
  if (value.includes("error") || value.includes("failed") || value.includes("rejected")) return "danger";
  if (value.includes("pending") || value.includes("review") || value.includes("queued")) return "warning";
  if (value.includes("created") || value.includes("issued")) return "accent";
  return "neutral";
}

function money(order: AdminPaymentOrder): string {
  return `${Number(order.amount || 0).toLocaleString("ru-RU")} ${order.currency || "RUB"}`;
}

function statusLabel(value?: string | null): string {
  const key = String(value || "").toLowerCase();
  return STATUS_LABELS[key] || key || "не задан";
}

type ReconcileDialog = {
  order: AdminPaymentOrder;
  status: string;
  note: string;
} | null;

type ResendDialog = {
  order: AdminPaymentOrder;
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
  const [resendDialog, setResendDialog] = useState<ResendDialog>(null);

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
      setError(errorMessage(err, "Платежный журнал сейчас недоступен."));
    } finally {
      setLoading(false);
    }
  }, [provider, query, status]);

  useEffect(() => {
    void loadOrders();
  }, [loadOrders]);

  const openReconcile = (order: AdminPaymentOrder): void => {
    setDialog({ order, status: order.status || "manual_review", note: "" });
    setResendDialog(null);
    setError("");
    setOkMessage("");
  };

  const openResend = (order: AdminPaymentOrder): void => {
    setResendDialog({ order, note: "" });
    setDialog(null);
    setError("");
    setOkMessage("");
  };

  const saveReconcile = async (): Promise<void> => {
    if (!dialog) return;
    const note = dialog.note.trim();
    if (!note) {
      setError("Для ручной сверки нужна аудиторская заметка.");
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
      setOkMessage("Заметка сверки сохранена. Доступ автоматически не менялся.");
    } catch (err) {
      setError(errorMessage(err, "Не удалось сохранить заметку сверки."));
    } finally {
      setBusy(false);
    }
  };

  const saveResend = async (): Promise<void> => {
    if (!resendDialog) return;
    const note = resendDialog.note.trim();
    if (note.length < 8) {
      setError("Аудиторская заметка должна быть не короче 8 символов.");
      return;
    }
    setBusy(true);
    setError("");
    setOkMessage("");
    try {
      const payload = await adminPaymentResendAccessKeyEmail({
        provider: resendDialog.order.provider,
        order_id: resendDialog.order.order_id,
        note,
      });
      setOrders((current) =>
        current.map((order) =>
          order.provider === payload.order.provider && order.order_id === payload.order.order_id ? payload.order : order,
        ),
      );
      setResendDialog(null);
      setOkMessage(`Повторная отправка ключа на email записана: ${payload.delivery.status || "статус неизвестен"}.`);
    } catch (err) {
      setError(errorMessage(err, "Не удалось повторно отправить ключ на email."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="платежи беты"
          title="Платежный журнал"
          description="Реальные заказы и callback-записи. Ручная сверка требует аудиторскую заметку и не меняет доступ пользователя молча."
          actions={
            <button type="button" className={adminButtonClass("secondary", "sm")} onClick={() => void loadOrders()} disabled={loading}>
              <RefreshCw size={14} />
              Обновить
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="accent">заказов: {total}</AdminBadge>
          <AdminBadge tone="warning">ручная проверка видна</AdminBadge>
          <AdminBadge>без сырых payload провайдера</AdminBadge>
          <AdminBadge>статус email с ключом</AdminBadge>
        </div>
      </article>

      <article className={adminPanelClass("neutral")}>
        <div className="grid gap-3 lg:grid-cols-[minmax(180px,0.8fr),minmax(180px,0.8fr),minmax(220px,1fr),auto]">
          <select value={status} onChange={(event) => setStatus(event.target.value)} className={adminFieldClass} aria-label="Статус платежа">
            {STATUS_OPTIONS.map((item) => (
              <option key={item || "all"} value={item}>
                {statusLabel(item)}
              </option>
            ))}
          </select>
          <select value={provider} onChange={(event) => setProvider(event.target.value)} className={adminFieldClass} aria-label="Провайдер">
            <option value="">все провайдеры</option>
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
          eyebrow="заказы и callback"
          title="Записи заказов провайдера"
          description="Строки приходят из платежных таблиц. Callback payload намеренно показан только в кратком виде, без сырого тела."
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
              <table className="min-w-[1180px] text-left text-xs">
                <thead>
                  <tr className="border-b border-[#22303c] bg-[#101821] text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                    <th className="px-3 py-3">Заказ</th>
                    <th className="px-3 py-3">Пользователь</th>
                    <th className="px-3 py-3">План</th>
                    <th className="px-3 py-3">Сумма</th>
                    <th className="px-3 py-3">Статус</th>
                    <th className="px-3 py-3">Выдача</th>
                    <th className="px-3 py-3">Callback</th>
                    <th className="px-3 py-3">Создан</th>
                    <th className="px-3 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={`${order.provider}:${order.order_id}`} className="border-t border-[#22303c] align-top">
                      <td className="px-3 py-3">
                        <p className="font-mono text-slate-100">{order.order_id}</p>
                        <p className="mt-1 text-slate-500">{order.provider}</p>
                        {order.source ? <p className="mt-1 text-slate-500">источник: {order.source}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        <p>{order.user?.display_name || order.user?.username || (order.tg_id ? `#${order.tg_id}` : "-")}</p>
                        {order.tg_id ? <p className="mt-1 text-slate-500">tg: {order.tg_id}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        <p>{order.plan_code || "-"}</p>
                        {order.promo_code ? <p className="mt-1 text-slate-500">промо: {order.promo_code}</p> : null}
                        {order.campaign ? <p className="mt-1 text-slate-500">кампания: {order.campaign}</p> : null}
                      </td>
                      <td className="px-3 py-3">{money(order)}</td>
                      <td className="px-3 py-3">
                        <AdminBadge tone={statusTone(order.status)}>{statusLabel(order.status)}</AdminBadge>
                        {order.paid_at ? <p className="mt-2 text-slate-500">оплачен: {fmtRuDate(order.paid_at)}</p> : null}
                      </td>
                      <td className="px-3 py-3">
                        {order.fulfillment ? (
                          <div className="space-y-1.5">
                            <AdminBadge tone={fulfillmentTone(order.fulfillment.status)}>
                              {order.fulfillment.status || order.fulfillment.mode || "выдача"}
                            </AdminBadge>
                            {order.fulfillment.buyer_email ? (
                              <p className="break-all text-slate-400">{order.fulfillment.buyer_email}</p>
                            ) : null}
                            {order.fulfillment.access_key_preview ? (
                              <p className="font-mono text-slate-500">ключ {order.fulfillment.access_key_preview}</p>
                            ) : null}
                            {order.fulfillment.email_delivery?.status ? (
                              <p className="text-slate-500">
                                {order.fulfillment.email_delivery.status}
                                {order.fulfillment.email_delivery.mode ? ` через ${order.fulfillment.email_delivery.mode}` : ""}
                                {order.fulfillment.email_delivery.http_status ? ` (${order.fulfillment.email_delivery.http_status})` : ""}
                              </p>
                            ) : null}
                            {order.fulfillment.can_retry_email ? (
                              <button
                                type="button"
                                className={adminButtonClass("secondary", "xs")}
                                onClick={() => openResend(order)}
                                disabled={busy}
                              >
                                <Send size={13} />
                                Отправить email снова
                              </button>
                            ) : null}
                          </div>
                        ) : (
                          <span className="text-slate-500">не требуется</span>
                        )}
                      </td>
                      <td className="px-3 py-3">
                        {order.last_event ? (
                          <div className="space-y-1">
                            <p>{order.last_event.event_type}</p>
                            <p className="font-mono text-slate-400">{order.last_event.external_id}</p>
                            <p className={order.last_event.signature_ok ? "text-emerald-300" : "text-rose-300"}>
                              подпись {order.last_event.signature_ok ? "ок" : "ошибка"}
                            </p>
                            <p className={order.last_event.processed_ok ? "text-emerald-300" : "text-amber-300"}>
                              обработка {order.last_event.processed_ok ? "ок" : "нужна проверка"}
                            </p>
                            <p className="text-slate-500">событий: {order.event_count}</p>
                          </div>
                        ) : (
                          <span className="text-slate-500">callback нет</span>
                        )}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap">{fmtRuDate(order.created_at)}</td>
                      <td className="px-3 py-3">
                        <button type="button" className={adminButtonClass("secondary", "xs")} onClick={() => openReconcile(order)}>
                          Сверить
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
            title="Платежных заказов пока нет"
            description="Это честное пустое состояние. Оно не заменяет счетчик выручки и не выглядит как фиктивный успех."
          />
        )}
      </article>

      {dialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-xl`}>
            <AdminPanelHeader
              eyebrow="ручная сверка"
              title={`Заказ ${dialog.order.order_id}`}
              description="Запишите, что именно проверил оператор. Действие обновляет состояние журнала и пишет audit metadata, но само по себе не выдает доступ."
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
              <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">аудиторская заметка</span>
              <textarea
                value={dialog.note}
                onChange={(event) => setDialog({ ...dialog, note: event.target.value })}
                className={adminTextAreaClass}
                placeholder="Что видно в кабинете провайдера, контекст пользователя или тикета, и почему этот статус корректен."
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

      {resendDialog ? (
        <div className="fixed inset-0 z-[260] flex items-center justify-center bg-slate-950/70 p-4">
          <div className={`${adminPanelClass("neutral")} w-full max-w-xl`}>
            <AdminPanelHeader
              eyebrow="email с ключом доступа"
              title={`Повторная отправка ${resendDialog.order.order_id}`}
              description="Повторите письмо с оплаченным ключом только после проверки заказа и контекста клиента. Действие аудируется и не показывает сырой ключ в интерфейсе."
            />
            <div className="space-y-2 text-xs text-slate-400">
              <p>
                Получатель: <strong className="text-slate-200">{resendDialog.order.fulfillment?.buyer_email || "неизвестен"}</strong>
              </p>
              <p>
                Превью ключа: <strong className="font-mono text-slate-200">{resendDialog.order.fulfillment?.access_key_preview || "скрыто"}</strong>
              </p>
            </div>
            <label className="mt-3 block text-sm">
              <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">аудиторская заметка</span>
              <textarea
                value={resendDialog.note}
                onChange={(event) => setResendDialog({ ...resendDialog, note: event.target.value })}
                className={adminTextAreaClass}
                placeholder="Почему повторная отправка безопасна: оплаченный статус, запрос пользователя, тикет поддержки, контекст кабинета провайдера."
                rows={5}
              />
            </label>
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button type="button" className={adminButtonClass("secondary")} onClick={() => setResendDialog(null)} disabled={busy}>
                Отмена
              </button>
              <button type="button" className={adminButtonClass("primary")} onClick={() => void saveResend()} disabled={busy}>
                <Send size={14} />
                Отправить ключ на email
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
