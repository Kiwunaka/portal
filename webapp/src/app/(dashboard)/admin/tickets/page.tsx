"use client";

import { adminTicketReply, adminTicketStatus, adminTickets, type TicketInfo } from "@/lib/api";
import { useCallback, useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

export default function AdminTicketsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [selectedId, setSelectedId] = useState<number>(0);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

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

  return (
    <section className="grid gap-4 xl:grid-cols-[0.95fr,1.05fr]">
      <article className="glass-card p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          >
            <option value="">Активные</option>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="closed">Closed</option>
          </select>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void load()}>
            Обновить
          </button>
        </div>
        {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}
        <div className="max-h-[64vh] space-y-2 overflow-auto">
          {tickets.map((ticket) => (
            <button
              key={ticket.id}
              type="button"
              onClick={() => setSelectedId(ticket.id)}
              className={`w-full rounded-xl px-3 py-3 text-left ${selectedId === ticket.id ? "bg-violet-500/15" : "bg-white/70 dark:bg-white/10"}`}
            >
              <div className="flex items-center justify-between gap-2">
                <strong>#{ticket.id}</strong>
                <span className="text-xs text-slate-500">{ticket.status_title}</span>
              </div>
              <p className="mt-1 text-sm">{ticket.subject || "Без темы"}</p>
              <p className="mt-1 text-xs text-slate-500">{ticket.last_message_preview || "Нет сообщений"}</p>
            </button>
          ))}
        </div>
      </article>

      <article className="glass-card p-4">
        {!selected ? (
          <p className="text-sm text-slate-500">Выберите тикет в левом списке.</p>
        ) : (
          <>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="font-display text-2xl font-semibold">Тикет #{selected.id}</h2>
                <p className="text-xs text-slate-500">Обновлен: {fmtRuDate(selected.updated_at)}</p>
              </div>
              <div className="flex gap-2">
                <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void updateStatus("open")} disabled={busy}>
                  Open
                </button>
                <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void updateStatus("in_progress")} disabled={busy}>
                  In progress
                </button>
                <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={() => void updateStatus("closed")} disabled={busy}>
                  Close
                </button>
              </div>
            </div>

            <div className="max-h-[44vh] space-y-2 overflow-auto rounded-xl bg-white/60 p-3 dark:bg-white/5">
              {(selected.messages || []).map((msg) => (
                <div key={msg.id} className={`rounded-xl px-3 py-2 text-sm ${msg.sender_role === "admin" ? "bg-violet-500/15" : "bg-white/70 dark:bg-white/10"}`}>
                  <p className="text-xs uppercase tracking-[0.12em] text-slate-500">{msg.sender_role}</p>
                  <p className="mt-1 whitespace-pre-line">{msg.body}</p>
                  <p className="mt-1 text-[10px] text-slate-500">{fmtRuDate(msg.created_at)}</p>
                </div>
              ))}
            </div>

            <div className="mt-3 space-y-2">
              <textarea
                value={reply}
                onChange={(event) => setReply(event.target.value)}
                rows={4}
                placeholder="Ответ оператором..."
                className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              />
              <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={() => void sendReply()} disabled={busy || !reply.trim()}>
                {busy ? "Отправка..." : "Отправить ответ"}
              </button>
            </div>
          </>
        )}
      </article>
    </section>
  );
}
