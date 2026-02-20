"use client";

import { addTicketMessage, getTicket, type TicketInfo } from "@/lib/api";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

function statusTitle(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "Открыт";
  if (normalized === "in_progress") return "В работе";
  if (normalized === "closed") return "Закрыт";
  return normalized || "Неизвестно";
}

function fmtDate(value?: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("ru-RU");
}

export default function SupportTicketThreadPage() {
  const searchParams = useSearchParams();
  const ticketId = Number(searchParams.get("id") || 0);

  const [ticket, setTicket] = useState<TicketInfo | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [replyError, setReplyError] = useState("");
  const listEndRef = useRef<HTMLDivElement | null>(null);

  const canReply = useMemo(() => ticket && String(ticket.status || "").toLowerCase() !== "closed", [ticket]);

  const loadTicket = async (): Promise<void> => {
    if (!ticketId) {
      setLoading(false);
      setError("Не передан ticket id");
      return;
    }
    setLoading(true);
    try {
      const data = await getTicket(ticketId);
      setTicket(data);
      setError("");
    } catch (error) {
      setError(String((error as { message?: string })?.message || error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTicket();
  }, [ticketId]);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [ticket?.messages?.length]);

  const onSendReply = async (): Promise<void> => {
    if (!ticket || !message.trim() || !canReply) return;
    setBusy(true);
    setReplyError("");
    try {
      const updated = await addTicketMessage(ticket.id, message.trim());
      setTicket(updated);
      setMessage("");
    } catch (error) {
      setReplyError(String((error as { message?: string })?.message || error));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <h1 className="font-display text-3xl font-bold">Загрузка тикета...</h1>
        </section>
      </main>
    );
  }

  if (error || !ticket) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <h1 className="font-display text-3xl font-bold">Не удалось открыть тикет</h1>
          <p className="mt-3 text-sm text-rose-500">{error || "Тикет не найден"}</p>
          <div className="mt-4">
            <Link href="/support/" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]">
              Назад в поддержку
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-5">
      <section className="glass-card p-5 md:p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-violet-600 dark:text-violet-300">#{ticket.id}</span>
              <h1 className="font-display text-2xl font-bold">{ticket.subject || "Тикет без темы"}</h1>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {statusTitle(ticket.status)} • обновлён {fmtDate(ticket.updated_at)}
            </p>
          </div>
          <Link href="/support/" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]">
            К списку
          </Link>
        </div>
      </section>

      <section className="glass-card p-4 md:p-5">
        <div className="max-h-[52vh] space-y-4 overflow-y-auto pr-1">
          {ticket.messages.length === 0 ? (
            <div className="rounded-xl bg-white/65 px-4 py-3 text-sm text-slate-500 dark:bg-white/10">История сообщений пока пустая.</div>
          ) : (
            ticket.messages.map((msg) => {
              const isAdmin = msg.sender_role === "admin";
              return (
                <div key={msg.id} className={`flex ${isAdmin ? "justify-start" : "justify-end"}`}>
                  <div className={`max-w-[86%] rounded-2xl px-4 py-3 text-sm leading-6 ${isAdmin ? "bg-white/75 dark:bg-white/10" : "bg-violet-500/15 dark:bg-violet-500/25"}`}>
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-500">{isAdmin ? "Оператор" : "Вы"}</p>
                    <p className="mt-1 whitespace-pre-line">{msg.body}</p>
                    <p className="mt-2 text-[10px] text-slate-500">{fmtDate(msg.created_at)}</p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={listEndRef} />
        </div>

        <div className="mt-4 border-t border-white/45 pt-4 dark:border-white/10">
          {!canReply ? (
            <p className="text-sm text-slate-500">Тикет закрыт. Для нового вопроса создайте новое обращение.</p>
          ) : (
            <>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={4}
                placeholder="Напишите ответ..."
                className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              />
              <div className="mt-3 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void onSendReply()}
                  disabled={busy || !message.trim()}
                  className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
                >
                  {busy ? "Отправляем..." : "Отправить"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMessage("");
                    setReplyError("");
                  }}
                  className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
                >
                  Очистить
                </button>
              </div>
              {replyError ? <p className="mt-2 text-xs text-rose-500">{replyError}</p> : null}
            </>
          )}
        </div>
      </section>
    </main>
  );
}
