"use client";

import { createTicket, fetchTickets, type TicketInfo } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

const FAQ = [
  {
    q: "Как быстро запустить VPN на iOS?",
    a: "Откройте раздел загрузок, выберите iOS-клиент и импортируйте ключ из блока подключения в кабинете.",
  },
  {
    q: "Как продлить подписку без паузы?",
    a: "Откройте раздел оплаты, выберите тариф и завершите оплату. Статус обновится автоматически.",
  },
  {
    q: "Что делать при низкой скорости?",
    a: "Проверьте статус узлов, переключите страну и при необходимости создайте тикет — мы разберёмся по логам.",
  },
];

function statusLabel(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "Открыт";
  if (normalized === "in_progress") return "В работе";
  if (normalized === "closed") return "Закрыт";
  return normalized || "Неизвестно";
}

function statusClass(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "bg-violet-100 text-violet-700 dark:bg-violet-900/35 dark:text-violet-300";
  if (normalized === "in_progress") return "bg-blue-100 text-blue-700 dark:bg-blue-900/35 dark:text-blue-300";
  if (normalized === "closed") return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/35 dark:text-emerald-300";
  return "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
}

export default function SupportPage() {
  const { user } = usePortalSession();
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [openedFaq, setOpenedFaq] = useState<number | null>(0);

  const supportLink = useMemo(() => {
    const username = String(user?.support?.username || "portal_privacy_helpbot").replace(/^@+/, "");
    return `https://t.me/${username}?start=ticket_new`;
  }, [user?.support?.username]);

  const loadTickets = async (): Promise<void> => {
    try {
      const rows = await fetchTickets(30);
      setTickets(rows);
      setError("");
    } catch (error) {
      setError(String((error as { message?: string })?.message || error));
    }
  };

  useEffect(() => {
    void loadTickets();
  }, []);

  const onCreateTicket = async (): Promise<void> => {
    if (!body.trim()) return;
    setBusy(true);
    setError("");
    try {
      await createTicket(subject.trim(), body.trim());
      setSubject("");
      setBody("");
      await loadTickets();
    } catch (error) {
      setError(String((error as { message?: string })?.message || error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <h1 className="font-display text-4xl font-bold">Центр поддержки</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Живые ответы в тикетах, история переписки и быстрый переход в Telegram-бот поддержки.
        </p>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.2fr,0.9fr]">
        <article className="space-y-3">
          <div className="glass-card p-5">
            <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">новый тикет</p>
            <h2 className="mt-2 font-display text-2xl font-semibold">Опишите проблему</h2>
            <div className="mt-4 space-y-3">
              <input
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
                placeholder="Тема (опционально)"
                className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              />
              <textarea
                value={body}
                onChange={(event) => setBody(event.target.value)}
                rows={5}
                placeholder="Опишите проблему: что делали, на каком устройстве, какой результат получили"
                className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              />
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void onCreateTicket()}
                  disabled={busy || !body.trim()}
                  className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
                >
                  {busy ? "Отправляем..." : "Создать тикет"}
                </button>
                <Link href={supportLink} target="_blank" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
                  Бот поддержки
                </Link>
              </div>
              {error ? <p className="text-xs text-rose-500">{error}</p> : null}
            </div>
          </div>

          {FAQ.map((item, idx) => {
            const opened = openedFaq === idx;
            return (
              <button key={item.q} type="button" onClick={() => setOpenedFaq(opened ? null : idx)} className="glass-card w-full px-5 py-4 text-left">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold">{item.q}</span>
                  <span className="material-symbols-rounded text-violet-500">{opened ? "expand_less" : "expand_more"}</span>
                </div>
                {opened ? <p className="pt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.a}</p> : null}
              </button>
            );
          })}
        </article>

        <aside className="space-y-4">
          <div className="glass-card p-6 text-center">
            <span className="material-symbols-rounded rounded-full bg-violet-100 p-3 text-3xl text-violet-600 dark:bg-violet-900/35 dark:text-violet-200">
              headset_mic
            </span>
            <h2 className="mt-3 font-display text-2xl font-semibold">Нужна помощь прямо сейчас?</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Среднее время ответа 10-15 минут.</p>
            <Link href={supportLink} target="_blank" className="btn-primary mt-5 inline-flex rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Открыть Telegram-поддержку
            </Link>
          </div>

          <div className="space-y-3">
            <h3 className="px-1 font-display text-xl font-semibold">Мои обращения</h3>
            {tickets.length === 0 ? (
              <div className="glass-card p-4 text-sm text-slate-500">Тикетов пока нет.</div>
            ) : (
              tickets.map((ticket) => (
                <Link key={ticket.id} href={`/support/thread/?id=${ticket.id}`} className="glass-card block px-4 py-3 transition hover:scale-[1.01]">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-mono">#{ticket.id}</span>
                    <span className={`rounded-full px-2 py-1 ${statusClass(ticket.status)}`}>{statusLabel(ticket.status)}</span>
                  </div>
                  <p className="font-medium">{ticket.subject || "Без темы"}</p>
                  <p className="mt-1 text-xs text-slate-500">{ticket.last_message_preview || "Сообщений пока нет"}</p>
                </Link>
              ))
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
