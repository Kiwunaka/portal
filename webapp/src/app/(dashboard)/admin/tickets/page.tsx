"use client";

import { adminTicketReply, adminTicketStatus, adminTickets, type TicketInfo } from "@/lib/api";
import { CheckCircle, Clock, Inbox, Loader2, MessageCircle, RefreshCw, Send } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fmtRuDate } from "../nav";

const STATUS_META: Record<string, { color: string; badge: string; icon: typeof Clock }> = {
  open: { color: "badge-info", badge: "Открыт", icon: Inbox },
  in_progress: { color: "badge-warning", badge: "В работе", icon: Clock },
  closed: { color: "badge-success", badge: "Закрыт", icon: CheckCircle },
};

export default function AdminTicketsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [selectedId, setSelectedId] = useState<number>(0);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => tickets.find((t) => t.id === selectedId) || null, [selectedId, tickets]);

  const load = useCallback(async (): Promise<void> => {
    setError("");
    try {
      const rows = await adminTickets(statusFilter, 80);
      setTickets(rows);
      if (rows[0]?.id) {
        setSelectedId((prev) => prev || rows[0].id);
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки тикетов"));
    }
  }, [statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [selected?.messages]);

  const sendReply = async (): Promise<void> => {
    if (!selected || !reply.trim()) return;
    setBusy(true);
    try {
      const updated = await adminTicketReply(selected.id, reply.trim());
      setReply("");
      setTickets((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось отправить ответ"));
    } finally {
      setBusy(false);
    }
  };

  const updateStatus = async (nextStatus: string): Promise<void> => {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = await adminTicketStatus(selected.id, nextStatus);
      setTickets((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить статус"));
    } finally {
      setBusy(false);
    }
  };

  const selectedStatus = selected?.status_title?.toLowerCase().replace(/\s+/g, "_") || "open";

  return (
    <section className="grid gap-4 xl:grid-cols-[0.9fr,1.1fr]">
      {/* ── Ticket list ────────────────────────────────── */}
      <article className="glass-card p-4">
        <div className="mb-3 rounded-xl bg-white/60 p-3 text-xs text-slate-500 dark:bg-white/5 dark:text-slate-400">
          Здесь собраны обращения пользователей. Слева список диалогов, справа переписка и быстрые статусы. Если нужно просто разобрать очередь, начните с фильтра и верхних карточек.
        </div>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <div className="stat-icon stat-icon-amber">
            <MessageCircle size={18} />
          </div>
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="flex-1 rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          >
            <option value="">Активные</option>
            <option value="open">Открыт</option>
            <option value="in_progress">В работе</option>
            <option value="closed">Закрыт</option>
          </select>
          <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void load()}>
            <RefreshCw size={13} />
          </button>
        </div>
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        <div className="max-h-[64vh] space-y-1.5 overflow-auto">
          {tickets.length === 0 ? (
            <div className="empty-state">
              <Inbox size={32} />
              <p className="text-sm">Нет тикетов</p>
            </div>
          ) : null}
          {tickets.map((ticket) => {
            const tStatus = ticket.status_title?.toLowerCase().replace(/\s+/g, "_") || "open";
            const meta = STATUS_META[tStatus] || STATUS_META.open;
            return (
              <button
                key={ticket.id}
                type="button"
                onClick={() => setSelectedId(ticket.id)}
                className={`haptic-tap w-full rounded-xl px-4 py-3 text-left transition-all ${selectedId === ticket.id ? "stat-card" : "bg-white/60 hover:bg-white/80 dark:bg-white/5 dark:hover:bg-white/10"}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2">
                    <span className="text-sm font-bold">#{ticket.id}</span>
                  </span>
                  <span className={`badge ${meta.color}`}>{meta.badge}</span>
                </div>
                <p className="mt-1.5 text-sm font-medium">{ticket.subject || "Без темы"}</p>
                <p className="mt-1 text-xs text-slate-500 line-clamp-1">{ticket.last_message_preview || "Нет сообщений"}</p>
              </button>
            );
          })}
        </div>
      </article>

      {/* ── Ticket detail ──────────────────────────────── */}
      <article className="glass-card p-4">
        {!selected ? (
          <div className="empty-state min-h-[300px]">
            <MessageCircle size={36} />
            <p className="text-sm">Выберите тикет в левом списке</p>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-2xl font-bold">Тикет #{selected.id}</h2>
                <p className="mt-0.5 text-xs text-slate-500">Обновлен: {fmtRuDate(selected.updated_at)}</p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(STATUS_META).map(([key, meta]) => {
                  const Icon = meta.icon;
                  const isActive = selectedStatus === key;
                  return (
                    <button
                      key={key}
                      className={`haptic-tap rounded-xl px-3 py-1.5 text-xs font-semibold inline-flex items-center gap-1.5 transition-all ${isActive
                          ? "bg-violet-600 text-white shadow-md shadow-violet-600/20"
                          : "outline-btn"
                        }`}
                      type="button"
                      onClick={() => void updateStatus(key)}
                      disabled={busy}
                    >
                      <Icon size={12} />
                      {meta.badge}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* ── Chat messages ──────────────────────────── */}
            <div className="max-h-[42vh] overflow-auto rounded-xl bg-white/40 p-3 dark:bg-white/[0.03] flex flex-col gap-2">
              {(selected.messages || []).length === 0 ? (
                <div className="empty-state py-8">
                  <MessageCircle size={24} />
                  <p className="text-xs">Нет сообщений</p>
                </div>
              ) : null}
              {(selected.messages || []).map((msg) => {
                const isAdmin = msg.sender_role === "admin";
                return (
                  <div key={msg.id} className={`flex ${isAdmin ? "justify-end" : "justify-start"}`}>
                    <div className={`chat-bubble ${isAdmin ? "chat-bubble-admin" : "chat-bubble-user"} text-sm`}>
                      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 mb-1">{isAdmin ? "оператор" : "пользователь"}</p>
                      <p className="whitespace-pre-line">{msg.body}</p>
                      <p className="mt-1.5 text-[10px] text-slate-400 text-right">{fmtRuDate(msg.created_at)}</p>
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEnd} />
            </div>

            {/* ── Reply box ─────────────────────────────── */}
            <div className="mt-3 space-y-2">
              <textarea
                value={reply}
                onChange={(event) => setReply(event.target.value)}
                rows={3}
                placeholder="Напишите ответ пользователю простыми словами"
                className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70 resize-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && reply.trim()) {
                    void sendReply();
                  }
                }}
              />
              <div className="flex items-center justify-between">
                <p className="text-[10px] text-slate-400">Подсказка: можно отправить быстрее через Ctrl/⌘ + Enter</p>
                <button
                  className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em] inline-flex items-center gap-2"
                  type="button"
                  onClick={() => void sendReply()}
                  disabled={busy || !reply.trim()}
                >
                  {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                  {busy ? "Отправка..." : "Отправить"}
                </button>
              </div>
            </div>
          </>
        )}
      </article>
    </section>
  );
}
