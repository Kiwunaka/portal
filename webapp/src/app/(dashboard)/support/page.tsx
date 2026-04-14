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

import { pokrovBranding } from "@/app/branding";

type TicketCategory = "Подключение" | "Оплата" | "Скорость" | "Любой другой вопрос";
type ContactCard =
  | {
      label: string;
      href: string;
      icon: string;
      title: string;
      hint: string;
      action?: never;
    }
  | {
      label: string;
      href?: never;
      icon: string;
      title: string;
      hint: string;
      action: () => void;
    };

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const CATEGORIES: TicketCategory[] = ["Подключение", "Оплата", "Скорость", "Любой другой вопрос"];

const FAQ = [
  {
    q: "Когда лучше сразу писать в Telegram?",
    a: "Если нужен быстрый ответ вживую или вы уже общаетесь с оператором, Telegram остаётся самым быстрым каналом.",
  },
  {
    q: "Когда лучше открыть тикет в кабинете?",
    a: "Если важно приложить скриншот, видео или сохранить всю историю диалога в одном месте, удобнее открыть обращение прямо здесь.",
  },
  {
    q: "Что лучше написать в первом сообщении?",
    a: "Коротко опишите проблему, устройство, что уже попробовали и на каком шаге всё остановилось. Это помогает команде быстрее сориентироваться.",
  },
  {
    q: "Можно ли продолжить старый диалог позже?",
    a: "Да. Все обращения сохраняются в кабинете, и вы можете вернуться к ним в любой момент.",
  },
] as const;

const TICKET_CATEGORY_DETAILS: Record<
  TicketCategory,
  {
    intro: string;
    subject: string;
    body: string;
    checklist: string[];
  }
> = {
  Подключение: {
    intro: "Подходит, если приложение не подключается, не синхронизирует доступ или новое устройство не подтягивает кабинет.",
    subject: "Не получается подключить устройство",
    body: "Что происходит:\n\nЧто уже попробовал:\n\nУстройство и версия приложения:",
    checklist: ["Модель устройства", "Где именно остановилось", "Что уже успели попробовать"],
  },
  Оплата: {
    intro: "Подходит для вопросов по продлению, оплате, непрошедшему платежу или несоответствию статуса доступа.",
    subject: "Вопрос по оплате или продлению",
    body: "Что ожидал увидеть:\n\nЧто произошло вместо этого:\n\nКогда была попытка оплаты:",
    checklist: ["Скрин шага оплаты", "Примерное время платежа", "Какой тариф выбирали"],
  },
  Скорость: {
    intro: "Подходит, если сервис работает медленно, соединение нестабильно или есть сомнения по текущему маршруту.",
    subject: "Нестабильная скорость или маршрут",
    body: "Как проявляется проблема:\n\nНа каком устройстве заметно:\n\nЕсть ли разница между сетями Wi‑Fi и мобильной:",
    checklist: ["Тип сети", "Когда началось", "Скрин или короткое видео, если удобно"],
  },
  "Любой другой вопрос": {
    intro: "Подходит для любых вопросов по доступу, устройствам, восстановлению входа или обратной связи.",
    subject: "Вопрос по кабинету POKROV",
    body: "Коротко опишите вопрос:\n\nЧто хотите получить в итоге:\n\nНужны ли вложения или скриншоты:",
    checklist: ["Краткое описание", "Желаемый результат", "Нужны ли вложения"],
  },
};

function statusLabel(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "Открыт";
  if (normalized === "in_progress") return "В работе";
  if (normalized === "closed") return "Закрыт";
  return normalized || "Неизвестно";
}

function statusClass(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "bg-amber-100 text-amber-700 dark:bg-amber-900/35 dark:text-amber-200";
  if (normalized === "in_progress") return "bg-sky-100 text-sky-700 dark:bg-sky-900/35 dark:text-sky-200";
  if (normalized === "closed") return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/35 dark:text-emerald-300";
  return "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
}

function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 Б";
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
}

function formatTicketDate(value?: string | null): string {
  if (!value) return "только что";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "обновлено недавно";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function sanitizeSupportCopy(value: string): string {
  return value.replace(/POKROV\s+Network/gi, "POKROV").replace(/\bNetwork\b/gi, "").replace(/\s{2,}/g, " ").trim();
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
  const activeCategory = TICKET_CATEGORY_DETAILS[category];
  const openCount = tickets.filter((ticket) => String(ticket.status || "").toLowerCase() !== "closed").length;

  const contactCards = useMemo<ContactCard[]>(
    () => [
      {
        label: "Telegram",
        href: supportLink,
        icon: "send",
        title: "Быстрый живой ответ",
        hint: "Лучше всего для короткого вопроса или если оператор уже ведёт диалог.",
      },
      {
        label: "Обращение",
        action: () => setCreateOpen(true),
        icon: "support",
        title: "История и вложения",
        hint: "Подходит, когда нужно сохранить переписку, добавить видео, лог или скриншоты.",
      },
      {
        label: "Email",
        href: `mailto:${config.contactEmail}`,
        icon: "mail",
        title: "Резервный канал",
        hint: "Если удобнее написать письмом или нужен формальный ответ на почту.",
      },
    ],
    [supportLink],
  );

  const supportContext = useMemo(
    () => [
      {
        label: "Профиль",
        value: user?.username ? `@${user.username}` : `ID ${user?.tg_id || "—"}`,
      },
      {
        label: "План",
        value: dash?.current_plan_code || dash?.sub_type || "уточняется",
      },
      {
        label: "Устройства",
        value: `${user?.sync?.device_count ?? user?.devices?.length ?? 0} известно`,
      },
      {
        label: "Сеансы",
        value: `${dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0} активно`,
      },
    ],
    [dash, user],
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

  const applyCategoryTemplate = (): void => {
    if (!subject.trim()) setSubject(activeCategory.subject);
    if (!body.trim()) setBody(activeCategory.body);
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
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">{pokrovBranding.supportTitle}</p>
            <h1 className="mt-2 font-display text-4xl font-bold">
              {sanitizeSupportCopy(getCopyText("webapp.support.title", "Служба заботы POKROV"))}
            </h1>
            <p className="mt-2 text-sm leading-7 text-slate-600 dark:text-slate-300">
              {sanitizeSupportCopy(
                getCopyText(
                  "webapp.support.subtitle",
                  "Быстрый вопрос, новое обращение или продолжение диалога — всё в одном спокойном маршруте, без лишней бюрократии.",
                ),
              )}
            </p>
          </div>
          <div className="rounded-2xl border border-emerald-900/10 bg-emerald-900/[0.04] px-4 py-4 text-sm leading-6 text-slate-700 dark:border-emerald-200/10 dark:bg-emerald-200/[0.05] dark:text-slate-200">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-800/80 dark:text-emerald-200/80">
              Как это работает
            </p>
            <p className="mt-2">{pokrovBranding.appFirstSummary}</p>
          </div>
        </div>

        <div className="mt-5 grid gap-3 lg:grid-cols-3">
          {contactCards.map((card) =>
            card.href ? (
              <AppRouteLink
                key={card.label}
                href={card.href}
                target="_blank"
                hardNavigate={false}
                className="rounded-[24px] border border-white/70 bg-white/72 p-5 text-left transition hover:-translate-y-0.5 dark:border-white/10 dark:bg-white/[0.04]"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-900/8 text-emerald-800 dark:bg-emerald-200/10 dark:text-emerald-200">
                  <span className="material-symbols-rounded text-[22px]">{card.icon}</span>
                </span>
                <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-50">{card.title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{card.hint}</p>
              </AppRouteLink>
            ) : (
              <button
                key={card.label}
                type="button"
                onClick={card.action}
                className="rounded-[24px] border border-white/70 bg-white/72 p-5 text-left transition hover:-translate-y-0.5 dark:border-white/10 dark:bg-white/[0.04]"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-900/8 text-emerald-800 dark:bg-emerald-200/10 dark:text-emerald-200">
                  <span className="material-symbols-rounded text-[22px]">{card.icon}</span>
                </span>
                <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-50">{card.title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{card.hint}</p>
              </button>
            ),
          )}
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.15fr,0.85fr]">
        <article className="space-y-4">
          <div className="glass-card p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-500">обращения</p>
                <h2 className="mt-2 font-display text-3xl font-semibold">Что лучше выбрать прямо сейчас</h2>
              </div>
              <button
                type="button"
                onClick={() => setCreateOpen(true)}
                className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]"
              >
                Создать обращение
              </button>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl bg-white/70 p-4 dark:bg-white/10">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Открыто сейчас</p>
                <p className="mt-2 text-2xl font-semibold">{openCount}</p>
                <p className="mt-2 text-[11px] text-slate-500">Столько обращений ждут ответа или ещё в работе</p>
              </div>
              <div className="rounded-2xl bg-white/70 p-4 dark:bg-white/10">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Всего обращений</p>
                <p className="mt-2 text-2xl font-semibold">{tickets.length}</p>
                <p className="mt-2 text-[11px] text-slate-500">История ваших диалогов сохраняется в кабинете</p>
              </div>
              <div className="rounded-2xl bg-white/70 p-4 dark:bg-white/10">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Юридические документы</p>
                <AppRouteLink href="/support/legal" className="mt-2 inline-flex text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                  Открыть оферту и политику
                </AppRouteLink>
                <p className="mt-2 text-[11px] text-slate-500">Если нужен официальный текст, он вынесен отдельно</p>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">что подготовить</p>
            <h2 className="mt-2 font-display text-3xl font-semibold">Чем подробнее первое сообщение, тем быстрее помощь</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {supportContext.map((item) => (
                <div key={item.label} className="rounded-2xl border border-white/40 bg-white/55 p-4 dark:border-white/10 dark:bg-white/5">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{item.label}</p>
                  <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-50">{item.value}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-2xl border border-white/40 bg-white/55 p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
              Лучше всего помогают: модель устройства, короткое описание шага, где всё остановилось, и скриншот или видео, если проблема визуальная.
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="px-1 font-display text-xl font-semibold">Частые вопросы</h3>
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
                    <span className="material-symbols-rounded text-emerald-600 dark:text-emerald-300">
                      {opened ? "expand_less" : "expand_more"}
                    </span>
                  </div>
                  {opened ? <p className="pt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.a}</p> : null}
                </button>
              );
            })}
          </div>
        </article>

        <aside className="space-y-4">
          <div className="glass-card p-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-500">мои обращения</p>
                <h2 className="mt-2 font-display text-2xl font-semibold">История поддержки</h2>
              </div>
              <button
                type="button"
                onClick={() => setCreateOpen(true)}
                className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em]"
              >
                Новое
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {loadingTickets ? (
                <div className="rounded-2xl border border-white/40 bg-white/55 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5">
                  Загружаем обращения…
                </div>
              ) : tickets.length === 0 ? (
                <div className="rounded-2xl border border-white/40 bg-white/55 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5">
                  {getCopyText(
                    "webapp.support.empty_tickets",
                    "Пока здесь пусто. Если появится вопрос по доступу, устройствам или оплате, можно открыть новое обращение в пару кликов.",
                  )}
                </div>
              ) : (
                tickets.map((ticket) => (
                  <AppRouteLink
                    key={ticket.id}
                    href={`/support/thread/?id=${ticket.id}`}
                    className="block rounded-2xl border border-white/40 bg-white/55 px-4 py-4 transition hover:-translate-y-0.5 dark:border-white/10 dark:bg-white/5"
                  >
                    <div className="mb-2 flex items-center justify-between gap-3 text-xs">
                      <span className="font-mono">#{ticket.id}</span>
                      <span className={`rounded-full px-2 py-1 ${statusClass(ticket.status)}`}>{statusLabel(ticket.status)}</span>
                    </div>
                    <p className="font-medium text-slate-900 dark:text-slate-50">{ticket.subject || "Новое обращение"}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{ticket.last_message_preview || "Сообщений пока нет"}</p>
                    <p className="mt-2 text-[11px] uppercase tracking-[0.12em] text-slate-400">{formatTicketDate(ticket.updated_at || ticket.created_at)}</p>
                  </AppRouteLink>
                ))
              )}
              {error ? <p className="text-xs text-rose-500">{error}</p> : null}
            </div>
          </div>

          <div className="glass-card p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">обратная связь</p>
            <h2 className="mt-2 font-display text-2xl font-semibold">Хотите оставить отзыв или идею?</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
              Для отзывов и предложений есть отдельный канал. Он не заменяет поддержку, но помогает нам улучшать POKROV и выбирать, что показывать на публичных поверхностях.
            </p>
            <AppRouteLink
              href={config.feedbackbotUrl}
              target="_blank"
              hardNavigate={false}
              className="outline-btn mt-4 inline-flex rounded-xl px-4 py-2 text-sm font-semibold"
            >
              Открыть отзывы
            </AppRouteLink>
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
              className="glass-card w-full max-w-2xl p-6"
              onClick={(event) => event.stopPropagation()}
            >
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-500">новое обращение</p>
                  <h3 className="mt-2 font-display text-2xl font-semibold">Создать обращение</h3>
                </div>
                <button type="button" onClick={() => setCreateOpen(false)} className="rounded-lg bg-white/70 p-2 dark:bg-white/10">
                  <span className="material-symbols-rounded">close</span>
                </button>
              </div>

              <div className="grid gap-5 lg:grid-cols-[0.95fr,1.05fr]">
                <div className="space-y-4">
                  <div className="rounded-2xl border border-emerald-900/10 bg-emerald-900/[0.04] p-4 dark:border-emerald-200/10 dark:bg-emerald-200/[0.05]">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-800/80 dark:text-emerald-200/80">Категория</p>
                    <select
                      value={category}
                      onChange={(event) => setCategory(event.target.value as TicketCategory)}
                      className="mt-3 w-full rounded-xl border border-emerald-900/10 bg-white/90 px-4 py-3 text-sm outline-none dark:border-emerald-200/10 dark:bg-[#0f1714]"
                    >
                      {CATEGORIES.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                    <p className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-200">{activeCategory.intro}</p>
                  </div>

                  <div className="rounded-2xl border border-white/40 bg-white/55 p-4 dark:border-white/10 dark:bg-white/5">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Что лучше добавить</p>
                      <button
                        type="button"
                        onClick={applyCategoryTemplate}
                        className="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-700 dark:text-emerald-300"
                      >
                        Подставить шаблон
                      </button>
                    </div>
                    <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
                      {activeCategory.checklist.map((item) => (
                        <li key={item} className="flex items-start gap-2">
                          <span className="material-symbols-rounded mt-0.5 text-[18px] text-emerald-600 dark:text-emerald-300">check_circle</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="space-y-4">
                  <input
                    value={subject}
                    onChange={(event) => setSubject(event.target.value)}
                    className="w-full rounded-xl border border-white/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-white/10 dark:bg-slate-900/70"
                    placeholder="Расскажите, что произошло"
                  />
                  <textarea
                    value={body}
                    onChange={(event) => setBody(event.target.value)}
                    className="w-full rounded-xl border border-white/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-white/10 dark:bg-slate-900/70"
                    rows={7}
                    placeholder="Опишите вашу ситуацию во всех подробностях"
                  />
                  <label className="block rounded-2xl border border-dashed border-white/50 bg-white/70 px-4 py-4 text-sm dark:border-white/10 dark:bg-slate-900/55">
                    <span className="mb-2 block font-medium">Скриншот, видео или лог</span>
                    <span className="block text-xs text-slate-500">Поддерживаются изображения, видео, PDF и текстовые файлы до 20 МБ.</span>
                    <input
                      type="file"
                      accept="image/*,video/*,.pdf,.txt,.log,application/pdf,text/plain"
                      className="mt-3 block w-full cursor-pointer text-sm text-slate-600 file:mr-3 file:rounded-xl file:border-0 file:bg-emerald-500/15 file:px-4 file:py-2 file:font-medium file:text-emerald-700 dark:text-slate-300 dark:file:bg-emerald-500/20 dark:file:text-emerald-200"
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
                      После отправки обращение появится в истории справа, а вложение сохранится в переписке.
                    </span>
                    <button
                      type="button"
                      onClick={() => void onCreateTicket()}
                      disabled={busy || !body.trim()}
                      className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
                    >
                      {busy ? "Отправляем…" : "Отправить"}
                    </button>
                  </div>
                  {error ? <p className="text-xs text-rose-500">{error}</p> : null}
                </div>
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
