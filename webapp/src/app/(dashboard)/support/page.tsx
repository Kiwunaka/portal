"use client";

import AppRouteLink from "@/components/app-route-link";
import { createTicket, fetchTickets, uploadTicketAttachment, type TicketAttachmentInput, type TicketInfo } from "@/lib/api";
import { getCopyText, getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

type TicketCategory = "Подключение" | "Оплата" | "Скорость" | "Общий вопрос";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const CATEGORIES: TicketCategory[] = ["Подключение", "Оплата", "Скорость", "Общий вопрос"];

const FAQ = [
  {
    q: "Где запускать тест?",
    a: "Главный вход для первого шага находится в Telegram. Там запускается тест на 3 дня, а дальше уже можно перейти в кабинет и к продлению.",
  },
  {
    q: "Чем отличаются free, trial и premium?",
    a: "Trial — это основной лид-магнит на 3 дня. Free остаётся как ограниченный fallback. Premium — платные тарифы с нормальным сроком, несколькими устройствами и полным сценарным использованием.",
  },
  {
    q: "Что делать, если касса не открылась?",
    a: "Не пытайтесь насильно добивать broken checkout. Продолжите в Telegram или напишите в поддержку — это основной fallback, пока кассы не стабилизированы.",
  },
  {
    q: "Как понять, что профиль уже активен?",
    a: "На главном экране кабинета видны статус, срок доступа, ключ, QR и следующие действия. Если чего-то не хватает, лучше сразу открыть обращение.",
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

function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 Б";
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
}

export default function SupportPage() {
  const { user, dash } = usePortalSession();
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [loadingTickets, setLoadingTickets] = useState(true);
  const [openedFaq, setOpenedFaq] = useState<number | null>(0);
  const [createOpen, setCreateOpen] = useState(false);
  const [category, setCategory] = useState<TicketCategory>(CATEGORIES[0]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const supportLink = user?.support?.link || config.supportTelegramUrl;
  const isTrialLike = ["FREE", "TRIAL", "BONUS"].includes(String(dash?.sub_type || "").toUpperCase()) || String(dash?.current_plan_code || "") === "trial";

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
        href: `mailto:${config.contactEmail}`,
        icon: "mail",
        hint: "Если удобнее написать письмом",
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
      notify("Добавьте описание перед отправкой.");
      return;
    }

    setBusy(true);
    setError("");
    try {
      let attachment: TicketAttachmentInput | undefined;
      if (attachmentFile) {
        const uploaded = await uploadTicketAttachment(attachmentFile);
        attachment = uploaded.attachment;
      }
      const prefixedSubject = normalizedSubject ? `[${category}] ${normalizedSubject}` : `[${category}] Обращение из кабинета`;
      const created = await createTicket(prefixedSubject, normalizedBody, attachment || undefined);
      setCreateOpen(false);
      setCategory(CATEGORIES[0]);
      setSubject("");
      setBody("");
      setAttachmentFile(null);
      await loadTickets();
      notify(`Обращение #${created.id} создано.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || ""));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <h1 className="font-display text-4xl font-bold">{getCopyText("webapp.support.title", "Поддержка PORTAL. Мы на связи.")}</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {getCopyText("webapp.support.subtitle", "Что-то не подключается, касса не открылась или просто есть вопрос? Напишите нам. Отвечаем быстро, спокойно и по делу.")}
        </p>
      </section>

      {isTrialLike ? (
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-300">trial support</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Застряли на старте? Не мучайтесь — поможем всё настроить за пару минут.</h2>
          <p className="mt-3 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
            Если что-то не заработало с первого раза, просто напишите нам. Поможем быстро, спокойно и без лишней переписки.
          </p>
        </section>
      ) : null}

      <section className="grid gap-5 xl:grid-cols-[1.2fr,0.9fr]">
        <article className="space-y-3">
          <div className="glass-card p-5">
            <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">документы</p>
            <h2 className="mt-2 font-display text-2xl font-semibold">Оферта и политика</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Юридические документы вынесены отдельно, чтобы всё важное было под рукой.</p>
            <div className="mt-4 flex flex-wrap gap-3">
              <AppRouteLink href="/support/legal" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                Открыть документы
              </AppRouteLink>
              <button type="button" onClick={() => setCreateOpen(true)} className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]">
                Создать обращение
              </button>
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
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Если checkout или подключение тормозит, лучше не ждать и сразу перейти в живой канал поддержки.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {contactCards.map((card) => (
                <AppRouteLink key={card.label} href={card.href} target="_blank" hardNavigate={false} className="outline-btn rounded-xl px-3 py-3 text-center text-sm font-semibold">
                  <div className="flex items-center justify-center gap-2">
                    <span className="material-symbols-rounded text-base">{card.icon}</span>
                    {card.label}
                  </div>
                  <div className="mt-1 text-[11px] font-normal uppercase tracking-[0.12em] text-slate-500">{card.hint}</div>
                </AppRouteLink>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="px-1 font-display text-xl font-semibold">Мои обращения</h3>
            {loadingTickets ? (
              <div className="glass-card p-4 text-sm text-slate-500">Загружаем обращения...</div>
            ) : tickets.length === 0 ? (
              <div className="glass-card p-4 text-sm text-slate-500">
                {getCopyText("webapp.support.empty_tickets", "Обращений пока нет. Если нужна помощь, создайте первое сообщение в пару строк.")}
              </div>
            ) : (
              tickets.map((ticket) => (
                <AppRouteLink key={ticket.id} href={`/support/thread/?id=${ticket.id}`} className="glass-card block px-4 py-3 transition hover:scale-[1.01]">
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-mono">#{ticket.id}</span>
                    <span className={`rounded-full px-2 py-1 ${statusClass(ticket.status)}`}>{statusLabel(ticket.status)}</span>
                  </div>
                  <p className="font-medium">{ticket.subject || "Без темы"}</p>
                  <p className="mt-1 text-xs text-slate-500">{ticket.last_message_preview || "Сообщений пока нет"}</p>
                </AppRouteLink>
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
                <h3 className="font-display text-2xl font-semibold">Создать обращение</h3>
                <button type="button" onClick={() => setCreateOpen(false)} className="rounded-lg bg-white/70 p-2 dark:bg-white/10">
                  <span className="material-symbols-rounded">close</span>
                </button>
              </div>

              <div className="space-y-4">
                <select value={category} onChange={(event) => setCategory(event.target.value as TicketCategory)} className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70">
                  {CATEGORIES.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
                <input value={subject} onChange={(event) => setSubject(event.target.value)} className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" placeholder="Коротко: что случилось" />
                <textarea value={body} onChange={(event) => setBody(event.target.value)} className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70" rows={5} placeholder="Опишите, что происходит и на каком устройстве это заметили" />
                <label className="block rounded-2xl border border-dashed border-violet-300/60 bg-white/70 px-4 py-4 text-sm dark:border-violet-500/35 dark:bg-slate-900/55">
                  <span className="mb-2 block font-medium">Скриншот, видео или лог</span>
                  <span className="block text-xs text-slate-500">Поддерживаются изображения, видео, PDF и текстовые файлы до 20 МБ.</span>
                  <input
                    type="file"
                    accept="image/*,video/*,.pdf,.txt,.log,application/pdf,text/plain"
                    className="mt-3 block w-full cursor-pointer text-sm text-slate-600 file:mr-3 file:rounded-xl file:border-0 file:bg-violet-500/15 file:px-4 file:py-2 file:font-medium file:text-violet-700 dark:text-slate-300 dark:file:bg-violet-500/20 dark:file:text-violet-200"
                    onChange={(event) => setAttachmentFile(event.target.files?.[0] ?? null)}
                  />
                  {attachmentFile ? (
                    <div className="mt-3 flex items-center justify-between gap-3 rounded-xl bg-white/75 px-3 py-2 text-xs dark:bg-white/10">
                      <span className="truncate">{attachmentFile.name}</span>
                      <button type="button" onClick={() => setAttachmentFile(null)} className="text-rose-500">
                        Убрать
                      </button>
                    </div>
                  ) : null}
                  {attachmentFile ? <p className="mt-2 text-[11px] uppercase tracking-[0.12em] text-slate-500">{formatFileSize(attachmentFile.size)}</p> : null}
                </label>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs text-slate-500">После отправки обращение появится справа, а вложение сохранится в истории переписки.</span>
                  <button type="button" onClick={() => void onCreateTicket()} disabled={busy || !body.trim()} className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60">
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
