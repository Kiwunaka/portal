"use client";

import { createTicket, fetchTickets, type TicketInfo } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useMemo, useState } from "react";
import { useEffect } from "react";

type TicketCategory = "Техническая проблема" | "Оплата и подписка" | "Скорость / медиасервисы" | "Общий вопрос";

const CATEGORIES: TicketCategory[] = [
  "Техническая проблема",
  "Оплата и подписка",
  "Скорость / медиасервисы",
  "Общий вопрос",
];

const FAQ = [
  {
    q: "Что значит: медиасервисы могут идти напрямую?",
    a: "В некоторых сценариях это снижает задержку для видео. Основной VPN-трафик при этом остается защищенным по выбранному тарифу.",
  },
  {
    q: "Premium действительно безлимитный?",
    a: "По трафику — да, формат безлимитный (best-effort). Итоговая скорость зависит от вашего канала, выбранной страны и текущей нагрузки.",
  },
  {
    q: "Какой тариф лучше для семьи?",
    a: "Ultra подходит для длительного периода и нескольких устройств. В сравнении тарифов в кабинете видны лимиты, скорость и уровень поддержки.",
  },
  {
    q: "Как быстро отвечаете в поддержке?",
    a: "Обычно первый ответ приходит в течение 10-15 минут. Для Premium обращений очередь приоритетная.",
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
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [openedFaq, setOpenedFaq] = useState<number | null>(0);

  const [createOpen, setCreateOpen] = useState(false);
  const [category, setCategory] = useState<TicketCategory>(CATEGORIES[0]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const supportUsername = String(user?.support?.username || "portal_privacy_helpbot").replace(/^@+/, "");
  const supportLink = `https://t.me/${supportUsername}?start=ticket_new`;

  const contactCards = useMemo(
    () => [
      {
        label: "Telegram",
        href: supportLink,
        icon: "send",
        hint: "Самый быстрый канал ответа",
      },
      {
        label: "Email",
        href: "mailto:support@portal-privacy.online",
        icon: "mail",
        hint: "Для подробных кейсов и файлов",
      },
    ],
    [supportLink],
  );

  const loadTickets = async (): Promise<void> => {
    setLoadingTickets(true);
    try {
      const rows = await fetchTickets(30);
      setTickets(rows);
      setError("");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || ""));
    } finally {
      setLoadingTickets(false);
    }
  };

  useEffect(() => {
    void loadTickets();
  }, []);

  const notify = (message: string): void => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2200);
  };

  const onCreateTicket = async (): Promise<void> => {
    const normalizedBody = body.trim();
    const normalizedSubject = subject.trim();
    if (!normalizedBody) {
      notify("Добавьте описание проблемы перед отправкой.");
      return;
    }

    setBusy(true);
    setError("");
    try {
      const prefixedSubject = normalizedSubject
        ? `[${category}] ${normalizedSubject}`
        : `[${category}] Обращение из поддержки`;
      const created = await createTicket(prefixedSubject, normalizedBody);
      setCreateOpen(false);
      setCategory(CATEGORIES[0]);
      setSubject("");
      setBody("");
      await loadTickets();
      notify(`Тикет #${created.id} создан. Мы уже в работе.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || ""));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <h1 className="font-display text-4xl font-bold">Центр поддержки PORTAL VPN</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Быстрые ответы, наглядные FAQ, история тикетов и удобное создание обращения в один шаг.
        </p>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.2fr,0.9fr]">
        <article className="space-y-3">
          <div className="glass-card p-5">
            <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">документы</p>
            <h2 className="mt-2 font-display text-2xl font-semibold">Оферта и политика</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Актуальные юридические документы доступны в отдельном разделе, чтобы всё было прозрачно.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href="/support/legal" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                Открыть документы
              </Link>
              <button
                type="button"
                onClick={() => setCreateOpen(true)}
                className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]"
              >
                Создать обращение
              </button>
            </div>
          </div>

          {FAQ.map((item, idx) => {
            const opened = openedFaq === idx;
            return (
              <button
                key={item.q}
                type="button"
                onClick={() => setOpenedFaq(opened ? null : idx)}
                className="glass-card w-full px-5 py-4 text-left"
              >
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
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {contactCards.map((card) => (
                <Link
                  key={card.label}
                  href={card.href}
                  target="_blank"
                  className="outline-btn rounded-xl px-3 py-3 text-center text-sm font-semibold"
                >
                  <div className="flex items-center justify-center gap-2">
                    <span className="material-symbols-rounded text-base">{card.icon}</span>
                    {card.label}
                  </div>
                  <div className="mt-1 text-[11px] font-normal uppercase tracking-[0.12em] text-slate-500">{card.hint}</div>
                </Link>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="px-1 font-display text-xl font-semibold">Мои обращения</h3>
            {loadingTickets ? (
              <div className="glass-card p-4 text-sm text-slate-500">Загружаем тикеты...</div>
            ) : tickets.length === 0 ? (
              <div className="glass-card p-4 text-sm text-slate-500">Тикетов пока нет. Создайте первое обращение.</div>
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
            {error ? <p className="text-xs text-rose-500">{error}</p> : null}
          </div>
        </aside>
      </section>

      <AnimatePresence>
        {createOpen ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[230] grid place-items-center bg-slate-900/60 p-4"
            onClick={() => setCreateOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 24, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 24, scale: 0.96 }}
              className="glass-card w-full max-w-xl p-6"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-display text-2xl font-semibold">Создать новое обращение</h3>
                <button type="button" onClick={() => setCreateOpen(false)} className="rounded-lg bg-white/70 p-2 dark:bg-white/10">
                  <span className="material-symbols-rounded">close</span>
                </button>
              </div>

              <div className="space-y-4">
                <select
                  value={category}
                  onChange={(event) => setCategory(event.target.value as TicketCategory)}
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                >
                  {CATEGORIES.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
                <input
                  value={subject}
                  onChange={(event) => setSubject(event.target.value)}
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder="Тема (например: не запускается на Windows)"
                />
                <textarea
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  rows={5}
                  placeholder="Опишите проблему: устройство, страна/узел, что ожидали и что получили"
                />
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs text-slate-500">После отправки тикет появится в списке справа.</span>
                  <button
                    type="button"
                    onClick={() => void onCreateTicket()}
                    disabled={busy || !body.trim()}
                    className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
                  >
                    {busy ? "Отправляем..." : "Отправить"}
                  </button>
                </div>
                {error ? <p className="text-xs text-rose-500">{error}</p> : null}
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <AnimatePresence>
        {toast ? (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            className="fixed bottom-24 left-1/2 z-[230] -translate-x-1/2 rounded-full bg-slate-900 px-4 py-2 text-xs text-white shadow-xl"
          >
            {toast}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </main>
  );
}
