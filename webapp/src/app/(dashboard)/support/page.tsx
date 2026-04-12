"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  createTicket,
  fetchTickets,
  uploadTicketAttachment,
  type TicketAttachmentInput,
  type TicketInfo,
} from "@/lib/api";
import { getCopyText, getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

type TicketCategory = "Подключение" | "Оплата" | "Скорость" | "Любой другой вопрос";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const CATEGORIES: TicketCategory[] = ["Подключение", "Оплата", "Скорость", "Любой другой вопрос"];

const FAQ = [
  {
    q: "С чего лучше начать, если я только открыл кабинет?",
    a: "Активируйте подписку в нашем приветливом Telegram-боте, а здесь скачивайте приложения и управляйте доступом.",
  },
  {
    q: "Чем отличается тест от полного доступа?",
    a: "Тест нужен, чтобы спокойно проверить скорость и запуск на своих устройствах. Полный доступ подходит для постоянного использования без жёстких ограничений по сценарию.",
  },
  {
    q: "Как быть, если возникли трудности с оплатой?",
    a: "Не теряйте ни секунды времени! Напишите нам в Telegram, и мы моментально решим вопрос на месте.",
  },
  {
    q: "Когда стоит создавать обращение, а когда просто писать в Telegram?",
    a: "Если вопрос короткий и нужен быстрый ответ, Telegram подойдёт лучше. Если важно приложить скриншот, видео, лог или сохранить историю диалога, удобнее создать обращение здесь.",
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
  if (normalized === "open") return "bg-amber-100 text-amber-800 dark:bg-amber-900/35 dark:text-amber-200";
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
  const isTrialLike =
    ["FREE", "TRIAL", "BONUS"].includes(String(dash?.sub_type || "").toUpperCase()) ||
    String(dash?.current_plan_code || "") === "trial";

  const contactCards = useMemo(
    () => [
      {
        label: "Telegram",
        href: supportLink,
        icon: "send",
        hint: "Быстрый ответ",
      },
      {
        label: "Email",
        href: `mailto:${config.contactEmail}`,
        icon: "mail",
        hint: "Если удобнее написать письмом",
      },
      {
        label: "Отзывы",
        href: config.feedbackbotUrl,
        icon: "rate_review",
        hint: "Мы открыты к предложениям",
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
      const prefixedSubject = normalizedSubject
        ? `[${category}] ${normalizedSubject}`
        : `[${category}] Обращение из кабинета POKROV`;
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
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-emerald-600 dark:text-amber-200">support / pokrov</p>
        <h1 className="font-display text-4xl font-bold">
          {getCopyText("webapp.support.title", "Служба заботы POKROV VPN")}
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {getCopyText(
            "webapp.support.subtitle",
            "Быстрый вопрос, новое обращение или продолжение диалога — всё в одном месте и без лишней бюрократии.",
          )}
        </p>
      </section>

      {isTrialLike ? (
        <section className="glass-card p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-500">помощь в тесте</p>
          <h2 className="mt-2 font-display text-2xl font-semibold">Если на старте что-то пошло не так, поможем быстро и спокойно.</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
            Мы ценим ваше время. Напишите нам, и наш оператор заботливо поможет с подключением или любым другим вопросом.
          </p>
        </section>
      ) : null}

      <section className="grid gap-5 xl:grid-cols-[1.2fr,0.9fr]">
        <article className="space-y-3">
          <div className="glass-card p-5">
            <p className="font-mono text-xs uppercase tracking-[0.15em] text-slate-500">документы</p>
            <h2 className="mt-2 font-display text-2xl font-semibold">Оферта и политика</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Все важные юридические документы вынесены отдельно, чтобы их можно было открыть в один клик.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <AppRouteLink href="/support/legal" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                Открыть документы
              </AppRouteLink>
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
                  <span className="material-symbols-rounded text-emerald-700 dark:text-amber-200">
                    {opened ? "expand_less" : "expand_more"}
                  </span>
                </div>
                {opened ? <p className="pt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.a}</p> : null}
              </button>
            );
          })}
        </article>

        <aside className="space-y-4">
          <div className="glass-card p-6 text-center">
            <span className="material-symbols-rounded rounded-full bg-emerald-100 p-3 text-3xl text-emerald-700 dark:bg-amber-900/25 dark:text-amber-200">
              headset_mic
            </span>
            <h2 className="mt-3 font-display text-2xl font-semibold">Нужна помощь прямо сейчас?</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Если оплата тормозит, не импортируется ключ или хотите просто быстро уточнить шаг, удобнее всего написать в живой канал поддержки.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {contactCards.map((card) => (
                <AppRouteLink
                  key={card.label}
                  href={card.href}
                  target="_blank"
                  hardNavigate={false}
                  className="outline-btn rounded-xl px-3 py-3 text-center text-sm font-semibold"
                >
                  <div className="flex items-center justify-center gap-2">
                    <span className="material-symbols-rounded text-base">{card.icon}</span>
                    {card.label}
                  </div>
                  <div className="mt-1 text-[11px] font-normal uppercase tracking-[0.12em] text-slate-500">
                    {card.hint}
                  </div>
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
                {getCopyText(
                  "webapp.support.empty_tickets",
                  "Вы пока не задавали вопросов, значит все работает отлично! Если что, мы всегда рядом.",
                )}
              </div>
            ) : (
              tickets.map((ticket) => (
                <AppRouteLink
                  key={ticket.id}
                  href={`/support/thread/?id=${ticket.id}`}
                  className="glass-card block px-4 py-3 transition hover:scale-[1.01]"
                >
                  <div className="mb-2 flex items-center justify-between text-xs">
                    <span className="font-mono">#{ticket.id}</span>
                    <span className={`rounded-full px-2 py-1 ${statusClass(ticket.status)}`}>
                      {statusLabel(ticket.status)}
                    </span>
                  </div>
                  <p className="font-medium">{ticket.subject || "Новое обращение"}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {ticket.last_message_preview || "Сообщений пока нет"}
                  </p>
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
                <select
                  value={category}
                  onChange={(event) => setCategory(event.target.value as TicketCategory)}
                  className="brand-input px-4 py-3 text-sm"
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
                  className="brand-input px-4 py-3 text-sm"
                  placeholder="Расскажите, что произошло"
                />
                <textarea
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  className="brand-input px-4 py-3 text-sm"
                  rows={5}
                  placeholder="Опишите вашу ситуацию во всех подробностях"
                />
                <label className="brand-upload block px-4 py-4 text-sm">
                  <span className="mb-2 block font-medium">Скриншот, видео или лог</span>
                  <span className="block text-xs text-slate-500">
                    Поддерживаются изображения, видео, PDF и текстовые файлы до 20 МБ.
                  </span>
                  <input
                    type="file"
                    accept="image/*,video/*,.pdf,.txt,.log,application/pdf,text/plain"
                    className="brand-file mt-3 block w-full cursor-pointer text-sm text-slate-600 dark:text-slate-300"
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
                  {attachmentFile ? (
                    <p className="mt-2 text-[11px] uppercase tracking-[0.12em] text-slate-500">
                      {formatFileSize(attachmentFile.size)}
                    </p>
                  ) : null}
                </label>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs text-slate-500">
                    После отправки обращение появится справа, а вложение сохранится в истории переписки.
                  </span>
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
