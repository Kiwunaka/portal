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

function normalizeTicketStatus(ticket: Pick<TicketInfo, "status" | "status_title"> | null | undefined): keyof typeof STATUS_META {
  const raw = String(ticket?.status || "").toLowerCase().replace(/\s+/g, "_");
  if (raw in STATUS_META) return raw as keyof typeof STATUS_META;

  const title = String(ticket?.status_title || "").toLowerCase().replace(/\s+/g, "_");
  if (title === "в_работе") return "in_progress";
  if (title === "закрыт") return "closed";
  return "open";
}

export default function AdminTicketsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [selectedId, setSelectedId] = useState<number>(0);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => tickets.find((ticket) => ticket.id === selectedId) || null, [selectedId, tickets]);

  const load = useCallback(async (): Promise<void> => {
    setError("");
    try {
      const rows = await adminTickets(statusFilter, 80);
      setTickets(rows);
      if (rows[0]?.id) {
        setSelectedId((prev) => (rows.some((ticket) => ticket.id === prev) ? prev : rows[0].id));
      } else {
        setSelectedId(0);
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить тикеты."));
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
      setError(String((err as { message?: string })?.message || err || "Не удалось отправить ответ."));
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
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить статус тикета."));
    } finally {
      setBusy(false);
    }
  };

  const selectedStatus = normalizeTicketStatus(selected);

  return (
    <section className="grid gap-4 xl:grid-cols-[0.9fr,1.1fr]">
      <article className="glass-card p-4">
        <div className="mb-3 rounded-xl bg-white/60 p-3 text-xs text-slate-500 dark:bg-white/5 dark:text-slate-400">
          Здесь собраны обращения пользователей. Слева список диалогов, справа переписка и быстрые статусы. Если нужно
          быстро разобрать очередь, начните с фильтра и верхних карточек.
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
          <button
            className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold"
            type="button"
            onClick={() => void load()}
          >
            <RefreshCw size={13} />
            Обновить
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
            const meta = STATUS_META[normalizeTicketStatus(ticket)] || STATUS_META.open;
            return (
              <button
                key={ticket.id}
                type="button"
                onClick={() => setSelectedId(ticket.id)}
                className={`haptic-tap w-full rounded-xl px-4 py-3 text-left transition-all ${
                  selectedId === ticket.id ? "stat-card" : "bg-white/60 hover:bg-white/80 dark:bg-white/5 dark:hover:bg-white/10"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-bold">#{ticket.id}</span>
                  <span className={`badge ${meta.color}`}>{meta.badge}</span>
                </div>
                <p className="mt-1.5 text-sm font-medium">{ticket.subject || "Без темы"}</p>
                <p className="mt-1 text-xs text-slate-500 line-clamp-1">{ticket.last_message_preview || "Нет сообщений"}</p>
              </button>
            );
          })}
        </div>
      </article>

      <article className="glass-card p-4">
        {!selected ? (
          <div className="empty-state min-h-[300px]">
            <MessageCircle size={36} />
            <p className="text-sm">Выберите тикет в левом списке</p>
          </div>
        ) : (
          <>
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-2xl font-bold">Тикет #{selected.id}</h2>
                <p className="mt-0.5 text-xs text-slate-500">Последнее обновление: {fmtRuDate(selected.updated_at)}</p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(STATUS_META).map(([key, meta]) => {
                  const Icon = meta.icon;
                  const isActive = selectedStatus === key;
                  return (
                    <button
                      key={key}
                      className={`haptic-tap inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold transition-all ${
                        isActive ? "bg-violet-600 text-white shadow-md shadow-violet-600/20" : "outline-btn"
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

            <div className="flex max-h-[42vh] flex-col gap-2 overflow-auto rounded-xl bg-white/40 p-3 dark:bg-white/[0.03]">
              {(selected.messages || []).length === 0 ? (
                <div className="empty-state py-8">
                  <MessageCircle size={24} />
                  <p className="text-xs">Нет сообщений</p>
                </div>
              ) : null}
              {(selected.messages || []).map((message) => {
                const isAdmin = message.sender_role === "admin";
                return (
                  <div key={message.id} className={`flex ${isAdmin ? "justify-end" : "justify-start"}`}>
                    <div className={`chat-bubble text-sm ${isAdmin ? "chat-bubble-admin" : "chat-bubble-user"}`}>
                      <p className="mb-1 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                        {isAdmin ? "Оператор" : "Пользователь"}
                      </p>
                      <p className="whitespace-pre-line">{message.body}</p>
                      <p className="mt-1.5 text-right text-[10px] text-slate-400">{fmtRuDate(message.created_at)}</p>
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEnd} />
            </div>

            <div className="mt-3 space-y-2">
              <textarea
                value={reply}
                onChange={(event) => setReply(event.target.value)}
                rows={3}
                placeholder="Напишите ответ пользователю простыми словами"
                className="w-full resize-none rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                onKeyDown={(event) => {
                  if (event.key === "Enter" && (event.metaKey || event.ctrlKey) && reply.trim()) {
                    void sendReply();
                  }
                }}
              />
              <div className="flex items-center justify-between gap-3">
                <p className="text-[10px] text-slate-400">Подсказка: можно отправить быстрее через Ctrl/⌘ + Enter</p>
                <button
                  className="btn-primary inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]"
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
