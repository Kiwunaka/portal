"use client";

import {
  AdminConfirmDialog,
  AdminBadge,
  AdminEmptyState,
  AdminInlineNote,
  AdminKpiCard,
  AdminPanelHeader,
  AdminSurfaceHeader,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTextAreaClass,
} from "@/components/admin/admin-shell";
import { adminTicketReply, adminTicketStatus, adminTickets, type TicketInfo } from "@/lib/api";
import { CheckCircle, Clock3, Inbox, Loader2, MessageCircle, RefreshCw, Send } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fmtRuDate } from "../nav";

type TicketStatus = "open" | "in_progress" | "closed";
type SlaTone = "success" | "warning" | "danger" | "accent" | "neutral";

const STATUSES: Array<{ key: TicketStatus; label: string }> = [
  { key: "open", label: "Открыт" },
  { key: "in_progress", label: "В работе" },
  { key: "closed", label: "Закрыт" },
];

function normalizeStatus(ticket: Pick<TicketInfo, "status" | "status_title"> | null | undefined): TicketStatus {
  const raw = String(ticket?.status || "").toLowerCase().replace(/\s+/g, "_");
  if (raw === "in_progress" || raw === "closed" || raw === "open") return raw;
  const title = String(ticket?.status_title || "").toLowerCase();
  if (title.includes("работ")) return "in_progress";
  if (title.includes("закры")) return "closed";
  return "open";
}

function ticketAgeHours(ticket: TicketInfo): number {
  const value = ticket.updated_at || ticket.created_at;
  if (!value) return 0;
  const time = new Date(value).getTime();
  if (Number.isNaN(time)) return 0;
  return Math.max(0, (Date.now() - time) / 36e5);
}

function slaMeta(ticket: TicketInfo): { label: string; tone: SlaTone; rank: number } {
  if (normalizeStatus(ticket) === "closed") return { label: "done", tone: "success", rank: 0 };
  const hours = ticketAgeHours(ticket);
  if (hours >= 24) return { label: "urgent 24h+", tone: "danger", rank: 4 };
  if (hours >= 8) return { label: "high 8h+", tone: "warning", rank: 3 };
  if (hours >= 3) return { label: "watch 3h+", tone: "accent", rank: 2 };
  return { label: "normal", tone: "success", rank: 1 };
}

function statusLabel(status: TicketStatus): string {
  return STATUSES.find((row) => row.key === status)?.label || status;
}

function preview(ticket: TicketInfo): string {
  return ticket.last_message_preview || ticket.messages.at(-1)?.body || "Нет сообщений";
}

export default function AdminTicketsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [selectedId, setSelectedId] = useState(0);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [closeReason, setCloseReason] = useState("");
  const [confirmClose, setConfirmClose] = useState(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => tickets.find((ticket) => ticket.id === selectedId) || null, [selectedId, tickets]);
  const selectedStatus = normalizeStatus(selected);

  const orderedTickets = useMemo(
    () =>
      [...tickets].sort((a, b) => {
        const slaDelta = slaMeta(b).rank - slaMeta(a).rank;
        if (slaDelta) return slaDelta;
        return new Date(b.updated_at || b.created_at || 0).getTime() - new Date(a.updated_at || a.created_at || 0).getTime();
      }),
    [tickets],
  );

  const totals = useMemo(() => {
    const open = tickets.filter((ticket) => normalizeStatus(ticket) === "open").length;
    const inWork = tickets.filter((ticket) => normalizeStatus(ticket) === "in_progress").length;
    const closed = tickets.filter((ticket) => normalizeStatus(ticket) === "closed").length;
    const urgent = tickets.filter((ticket) => slaMeta(ticket).rank >= 4).length;
    return { open, inWork, closed, urgent };
  }, [tickets]);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError("");
    try {
      const rows = await adminTickets(statusFilter, 80);
      setTickets(rows);
      setSelectedId((prev) => (rows.some((ticket) => ticket.id === prev) ? prev : rows[0]?.id || 0));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить обращения."));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [selected?.messages]);

  const replaceTicket = (updated: TicketInfo): void => {
    setTickets((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
  };

  const changeStatus = async (nextStatus: TicketStatus): Promise<void> => {
    if (!selected) return;
    if (nextStatus === "closed") {
      setConfirmClose(true);
      return;
    }
    setBusy(true);
    setError("");
    try {
      replaceTicket(await adminTicketStatus(selected.id, nextStatus));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить статус обращения."));
    } finally {
      setBusy(false);
    }
  };

  const closeTicket = async (): Promise<void> => {
    if (!selected) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      replaceTicket(await adminTicketStatus(selected.id, "closed", closeReason.trim()));
      setNotice(`Обращение #${selected.id} закрыто. Причина: ${closeReason.trim()}`);
      setConfirmClose(false);
      setCloseReason("");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось закрыть обращение."));
    } finally {
      setBusy(false);
    }
  };

  const sendReply = async (): Promise<void> => {
    if (!selected || !reply.trim()) return;
    setBusy(true);
    setError("");
    try {
      const updated = await adminTicketReply(selected.id, reply.trim());
      replaceTicket(updated);
      setReply("");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось отправить ответ."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <AdminSurfaceHeader
        title="Ticket operations"
        description="Здесь собраны обращения пользователей. Queue, SLA priority, safe status changes, and compact conversation view for support operators."
        meta={
          <>
            <AdminBadge tone="neutral">{tickets.length} loaded</AdminBadge>
            <AdminBadge tone={totals.urgent ? "danger" : "success"}>{totals.urgent} urgent</AdminBadge>
          </>
        }
        actions={
          <>
            <select className={`${adminFieldClass} w-auto min-w-[150px]`} value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              {STATUSES.map((row) => (
                <option key={row.key} value={row.key}>{row.label}</option>
              ))}
            </select>
            <button type="button" className={adminButtonClass("secondary", "sm")} onClick={load} disabled={loading || busy}>
              <RefreshCw size={14} /> Обновить
            </button>
          </>
        }
      />

      {error ? <AdminInlineNote tone="danger">{error}</AdminInlineNote> : null}
      {notice ? <AdminInlineNote tone="success">{notice}</AdminInlineNote> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <AdminKpiCard label="Открыто" value={totals.open} hint="Ждет первого ответа оператора." tone={totals.open ? "warning" : "success"} />
        <AdminKpiCard label="В работе" value={totals.inWork} hint="Ведется через support-flow." tone="accent" />
        <AdminKpiCard label="Срочно" value={totals.urgent} hint="SLA старше 24 часов." tone={totals.urgent ? "danger" : "success"} />
        <AdminKpiCard label="Закрыто в выборке" value={totals.closed} hint="В текущем фильтре." />
      </div>

      <div className="grid gap-4 xl:grid-cols-[420px_minmax(0,1fr)]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="очередь" title="Очередь обращений" description="Сортировка по SLA, затем по последней активности." />
          {orderedTickets.length ? (
            <div className="space-y-2">
              {orderedTickets.map((ticket) => {
                const sla = slaMeta(ticket);
                const status = normalizeStatus(ticket);
                const active = ticket.id === selectedId;
                return (
                  <button
                    key={ticket.id}
                    type="button"
                    className={`w-full rounded-xl border p-3 text-left transition ${
                      active ? "border-emerald-500 bg-emerald-100" : "border-[#c6e6db] bg-[#f8fffc] hover:border-[#426c5f]"
                    }`}
                    onClick={() => setSelectedId(ticket.id)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-100">{ticket.subject || `Ticket #${ticket.id}`}</p>
                        <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{preview(ticket)}</p>
                      </div>
                      <AdminBadge tone={sla.tone}>{sla.label}</AdminBadge>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                      <AdminBadge tone={status === "closed" ? "success" : status === "in_progress" ? "accent" : "warning"}>{statusLabel(status)}</AdminBadge>
                      <span>#{ticket.id}</span>
                      <span>Telegram ID {ticket.user_tg_id}</span>
                      <span>{fmtRuDate(ticket.updated_at || ticket.created_at)}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <AdminEmptyState title="No tickets in this filter" description="The API returned an empty queue." />
          )}
        </article>

        <article className={adminPanelClass("neutral")}>
          {selected ? (
            <>
              <AdminPanelHeader
                eyebrow={`Ticket #${selected.id}`}
                title="Thread detail"
                description={`Telegram ID ${selected.user_tg_id} · updated ${fmtRuDate(selected.updated_at || selected.created_at)}`}
                actions={
                  <div className="flex flex-wrap gap-2">
                    {STATUSES.map((row) => {
                      const active = selectedStatus === row.key;
                      return (
                        <button
                          key={row.key}
                          type="button"
                          className={`inline-flex min-h-9 items-center justify-center rounded-lg px-3 text-xs font-semibold transition ${
                            active ? "bg-emerald-700 text-white" : "border border-[#99cdbb] bg-[#ffffff] text-slate-900 hover:bg-[#dff3eb]"
                          }`}
                          onClick={() => changeStatus(row.key)}
                          disabled={busy}
                        >
                          {row.label}
                        </button>
                      );
                    })}
                  </div>
                }
              />

              <div className="mb-4 grid gap-3 md:grid-cols-3">
                <div className={adminInsetPanelClass}><p className="text-[11px] text-slate-500">SLA</p><p className="mt-1 font-semibold text-slate-100">{slaMeta(selected).label}</p></div>
                <div className={adminInsetPanelClass}><p className="text-[11px] text-slate-500">Priority</p><p className="mt-1 font-semibold text-slate-100">{slaMeta(selected).rank >= 4 ? "urgent" : "normal"}</p></div>
                <div className={adminInsetPanelClass}><p className="text-[11px] text-slate-500">Messages</p><p className="mt-1 font-semibold text-slate-100">{selected.messages.length}</p></div>
              </div>

              <div className="max-h-[520px] space-y-3 overflow-y-auto rounded-xl border border-[#c6e6db] bg-[#ffffff] p-3">
                {selected.messages.length ? (
                  selected.messages.map((message) => {
                    const isAdmin = message.sender_role === "admin";
                    return (
                      <div key={message.id} className={`flex ${isAdmin ? "justify-end" : "justify-start"}`}>
                        <div
                          className={`max-w-[78%] rounded-2xl px-3 py-2 text-sm leading-6 ${
                            isAdmin ? "chat-bubble-admin bg-emerald-100 text-emerald-950" : "bg-[#eef8f3] text-slate-900"
                          }`}
                        >
                          <div className="mb-1 flex items-center gap-2 text-[10px] uppercase tracking-[0.14em] text-slate-500">
                            {isAdmin ? <CheckCircle size={12} /> : <MessageCircle size={12} />}
                            {isAdmin ? "Admin" : "User"} · {fmtRuDate(message.created_at)}
                          </div>
                          <p>{message.body}</p>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <AdminEmptyState title="No messages" description="This ticket has no message history in the current response." />
                )}
                <div ref={messagesEnd} />
              </div>

              <div className="mt-4 rounded-xl border border-[#c6e6db] bg-[#f8fffc] p-3">
                <label className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  <Inbox size={14} /> Reply
                </label>
                <textarea
                  className={`${adminTextAreaClass} min-h-[110px]`}
                  value={reply}
                  onChange={(event) => setReply(event.target.value)}
                  placeholder="Напишите ответ пользователю простыми словами"
                />
                <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs leading-5 text-slate-500">Do not expose internal node names, topology, tokens, or operator-only diagnostics.</p>
                  <button type="button" className={adminButtonClass("primary", "sm")} onClick={sendReply} disabled={busy || !reply.trim()}>
                    {busy ? <Loader2 className="animate-spin" size={14} /> : <Send size={14} />} Отправить
                  </button>
                </div>
              </div>
            </>
          ) : (
            <AdminEmptyState title="Select a ticket" description="Pick a queue item to inspect the thread and change status." />
          )}
        </article>
      </div>

      <AdminConfirmDialog
        open={confirmClose && Boolean(selected)}
        title={selected ? `Закрыть обращение #${selected.id}` : "Закрыть обращение"}
        description="Закрытие видно в поддержке. Укажите причину или итог решения."
        reason={closeReason}
        onReasonChange={setCloseReason}
        onCancel={() => setConfirmClose(false)}
        onConfirm={() => void closeTicket()}
        confirmLabel={busy ? "Закрываем..." : "Закрыть"}
        busy={busy}
      />
    </section>
  );
}
