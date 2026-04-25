"use client";

import { useEffect, useMemo, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { resolvePlanLabel } from "@/lib/access-policy";
import {
  createTicket,
  fetchTickets,
  uploadTicketAttachment,
  type TicketAttachmentInput,
  type TicketInfo,
} from "@/lib/api";
import { getDeviceLimit, resolvePlanLabel } from "@/lib/access-policy";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";

type TicketCategory = "Подключение" | "Оплата" | "Скорость" | "Другой вопрос";

type CategoryPreset = {
  intro: string;
  subject: string;
  body: string;
  checklist: string[];
};

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const CATEGORIES: TicketCategory[] = ["Подключение", "Оплата", "Скорость", "Другой вопрос"];

const CATEGORY_PRESETS: Record<TicketCategory, CategoryPreset> = {
  Подключение: {
    intro: "Подходит, если приложение не подключается, доступ не подтягивается или новое устройство не появляется в кабинете.",
    subject: "Не получается подключить устройство",
    body: "Что происходит:\n\nНа каком устройстве это видно:\n\nЧто уже пробовали сделать:",
    checklist: ["Модель устройства", "Шаг, на котором все остановилось", "Что уже пробовали"],
  },
  Оплата: {
    intro: "Подходит, если возник вопрос по продлению, платежу или статус не обновился после оплаты.",
    subject: "Вопрос по оплате или продлению",
    body: "Что ожидали увидеть:\n\nЧто произошло вместо этого:\n\nПримерное время оплаты:",
    checklist: ["Какой вариант выбирали", "Примерное время платежа", "Скрин шага оплаты, если удобно"],
  },
  Скорость: {
    intro: "Подходит, если доступ стал заметно медленнее или соединение ведет себя нестабильно.",
    subject: "Нестабильная скорость или путь доступа",
    body: "Как выглядит проблема:\n\nНа каком устройстве это заметно:\n\nЧто меняется между Wi-Fi и мобильной сетью:",
    checklist: ["Тип сети", "Когда это началось", "Скрин или короткое видео, если удобно"],
  },
  "Другой вопрос": {
    intro: "Подходит для любых остальных вопросов по кабинету, доступу и связанным устройствам.",
    subject: "Вопрос по кабинету POKROV",
    body: "Коротко опишите вопрос:\n\nКакой результат нужен:\n\nНужны ли вложения:",
    checklist: ["Короткое описание", "Желаемый результат", "Нужны ли файлы или скриншоты"],
  },
};

function statusLabel(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "Открыт";
  if (normalized === "in_progress") return "В работе";
  if (normalized === "closed") return "Закрыт";
  return normalized || "Уточняется";
}

function formatDate(value?: string | null): string {
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
  const [composeOpen, setComposeOpen] = useState(false);
  const [category, setCategory] = useState<TicketCategory>(CATEGORIES[0]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const supportLink = user?.support?.link || config.supportTelegramUrl;
  const latestTicket = tickets[0] || null;
  const openCount = tickets.filter((ticket) => String(ticket.status || "").toLowerCase() !== "closed").length;
  const preset = CATEGORY_PRESETS[category];
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const deviceLimit = getDeviceLimit(dash, user);

  const loadTickets = async (): Promise<void> => {
    setLoadingTickets(true);
    try {
      const rows = await fetchTickets(30);
      setTickets(rows);
      setError("");
    } catch {
      setError("Не удалось обновить историю обращений. Попробуйте еще раз или напишите в Telegram.");
    } finally {
      setLoadingTickets(false);
    }
  };

  useEffect(() => {
    void loadTickets();
  }, []);

  const ticketItems = useMemo(
    () =>
      tickets.map((ticket) => ({
        key: String(ticket.id),
        title: ticket.subject || `Кейс #${ticket.id}`,
        body: ticket.last_message_preview || "Сообщений пока нет.",
        badge: `${statusLabel(ticket.status)} · #${ticket.id}`,
        tone:
          String(ticket.status || "").toLowerCase() === "closed"
            ? ("neutral" as const)
            : String(ticket.status || "").toLowerCase() === "in_progress"
              ? ("info" as const)
              : ("warning" as const),
        action: (
          <AppRouteLink href={`/support/thread/?id=${ticket.id}`} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Открыть
          </AppRouteLink>
        ),
      })),
    [tickets],
  );

  const helpCards = [
    {
      key: "continue",
      title: latestTicket ? "Лучше продолжить уже открытый кейс" : "Если вопрос понятен, можно сразу открыть кейс",
      body: latestTicket
        ? "Так не теряется история, вложения и то, что вы уже успели объяснить."
        : "Особенно если нужен скриншот, видео или понятная история переписки.",
      badge: "Кабинет",
      tone: "neutral" as const,
      action: latestTicket ? (
        <AppRouteLink href={`/support/thread/?id=${latestTicket.id}`} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Продолжить
        </AppRouteLink>
      ) : (
        <button type="button" onClick={() => setComposeOpen(true)} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Новый кейс
        </button>
      ),
    },
    {
      key: "telegram",
      title: "Telegram удобен для короткого вопроса",
      body: "Если не нужны вложения и длинная история, можно написать туда. Для развернутой проверки лучше оставить кейс в кабинете.",
      badge: "Внешний контакт",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href={supportLink} target="_blank" hardNavigate={false} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть
        </AppRouteLink>
      ),
    },
    {
      key: "legal",
      title: "Документы тоже под рукой",
      body: "Если вопрос касается оплаты или формальных условий, оферта и политика открываются отсюда без поиска по старым сообщениям.",
      badge: "Документы",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/legal/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть
        </AppRouteLink>
      ),
    },
  ];

  const prepareTemplate = (): void => {
    if (!subject.trim()) setSubject(preset.subject);
    if (!body.trim()) setBody(preset.body);
  };

  const onCreateTicket = async (): Promise<void> => {
    const normalizedBody = body.trim();
    const normalizedSubject = subject.trim();

    if (!normalizedBody) {
      setMessage("Добавьте пару строк, чтобы нам было понятно, с чего начать.");
      return;
    }

    setBusy(true);
    setError("");
    setMessage("");

    try {
      let attachment: TicketAttachmentInput | undefined;
      if (attachmentFile) {
        const uploaded = await uploadTicketAttachment(attachmentFile);
        attachment = uploaded.attachment;
      }

      const nextSubject = normalizedSubject ? `[${category}] ${normalizedSubject}` : `[${category}] Кейс из кабинета`;
      const created = await createTicket(nextSubject, normalizedBody, attachment || undefined);

      setComposeOpen(false);
      setCategory(CATEGORIES[0]);
      setSubject("");
      setBody("");
      setAttachmentFile(null);
      await loadTickets();
      setMessage(`Кейс #${created.id} создан. Его можно продолжить из списка.`);
    } catch {
      setError("Не удалось создать кейс. Попробуйте еще раз или напишите в Telegram.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <CabinetRoute
        eyebrow="Поддержка"
        title="Один кейс на весь вопрос"
        description="Здесь удобно открыть новый кейс, продолжить старый и не потерять контекст, если вопрос тянется дольше одного сообщения."
        actions={
          <>
            <button type="button" onClick={() => setComposeOpen(true)} className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
              Новый кейс
            </button>
            <AppRouteLink href={supportLink} target="_blank" hardNavigate={false} className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Telegram
            </AppRouteLink>
          </>
        }
        metrics={[
          {
            label: "Аккаунт",
            value: user?.username ? `@${user.username}` : user?.tg_id ? `ID ${user.tg_id}` : "POKROV",
            hint: "Поддержка видит тот же аккаунт, что и ваши устройства.",
            tone: "neutral",
          },
          {
            label: "Открытых кейсов",
            value: String(openCount),
            hint: latestTicket ? `Последнее обновление ${formatDate(latestTicket.updated_at || latestTicket.created_at)}.` : "Если вопросов еще не было, просто создайте первый кейс.",
            tone: openCount ? "warning" : "success",
          },
          {
            label: "Текущий режим",
            value: resolvePlanLabel(dash, user),
            hint: "Это помогает нам быстрее понять контекст.",
            tone: "neutral",
          },
          {
            label: "Диагностика",
            value: "Кейс + вложения",
            hint: "Для скриншотов, видео и длинного описания используйте кейс в кабинете.",
            tone: "neutral",
          },
        ]}
      >
        <CabinetHero
          eyebrow="Что делать сейчас"
          badge={latestTicket ? "Есть кейс, который можно продолжить" : "Можно открыть первый кейс"}
          badgeTone={latestTicket ? "success" : "info"}
          title={latestTicket ? latestTicket.subject || `Кейс #${latestTicket.id}` : "Не нужно начинать заново каждый раз"}
          description={
            latestTicket
              ? latestTicket.last_message_preview || "Если вопрос еще не решен, удобнее продолжить именно этот кейс."
              : "Откройте один кейс и продолжайте его дальше. Так поддержка видит всю историю рядом, а вы не пересказываете одно и то же."
          }
          actions={
            <>
              {latestTicket ? (
                <AppRouteLink href={`/support/thread/?id=${latestTicket.id}`} className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                  Продолжить кейс
                </AppRouteLink>
              ) : (
                <button type="button" onClick={() => setComposeOpen(true)} className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                  Создать кейс
                </button>
              )}
              <AppRouteLink href={supportLink} target="_blank" hardNavigate={false} className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
                Telegram
              </AppRouteLink>
            </>
          }
          details={[
            {
              label: "Состояние поддержки",
              value: latestTicket ? statusLabel(latestTicket.status) : "Готовы принять",
              hint: latestTicket ? `Кейс #${latestTicket.id}` : "Первый кейс можно открыть отсюда.",
              tone: latestTicket ? "success" : "neutral",
            },
            {
              label: "Что помогает диагностике",
              value: "Короткое описание",
              hint: "Добавьте устройство, шаг и что уже пробовали. Этого обычно хватает для старта.",
              tone: "neutral",
            },
            {
              label: "Если нужен быстрый контакт",
              value: "Telegram",
              hint: "Подходит для коротких уточнений без вложений и длинной истории.",
              tone: "neutral",
            },
          ]}
        />

        <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
          <CabinetSection
            eyebrow="История"
            title="Ваши кейсы"
            description="Если вопрос уже был, лучше продолжать тот же кейс. Так быстрее и спокойнее."
            actions={
              <button type="button" onClick={() => setComposeOpen(true)} className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
                Новый кейс
              </button>
            }
          >
            {loadingTickets ? (
              <div className="rounded-[1.3rem] border border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-400">
                Загружаем историю обращений...
              </div>
            ) : (
              <CabinetList items={ticketItems} empty="Пока обращений нет. Если что-то пошло не так, откройте первый кейс отсюда." />
            )}
            {error ? <p className="mt-4 text-sm text-rose-600 dark:text-rose-300">{error}</p> : null}
          </CabinetSection>

          <CabinetSection
            eyebrow="Куда идти"
            title="Быстрые варианты"
            description="Если сомневаетесь, обычно достаточно выбрать один из этих путей."
          >
            <CabinetCardGrid items={helpCards} className="xl:grid-cols-1" />
          </CabinetSection>
        </div>

        <CabinetSection
          eyebrow="Безопасная диагностика"
          title="Что мы можем передать в кейс"
          description="Только полезный контекст из кабинета. Личные ссылки, ключи, адреса точек доступа и публичный адрес устройства не показываем и не просим присылать."
        >
          <CabinetCardGrid
            items={[
              {
                key: "access",
                title: "Режим доступа",
                body: resolvePlanLabel(dash, user),
                badge: dash?.is_active ? "Активен" : "Нужен следующий шаг",
                tone: dash?.is_active ? ("success" as const) : ("warning" as const),
              },
              {
                key: "devices",
                title: "Устройства",
                body: `${deviceCount} из ${deviceLimit} уже связаны с профилем.`,
                badge: "Профиль",
                tone: "neutral" as const,
              },
              {
                key: "connections",
                title: "Подключения сейчас",
                body: `${activeConnections} активных подключений по профилю.`,
                badge: "Сводка",
                tone: activeConnections > 0 ? ("success" as const) : ("neutral" as const),
              },
            ]}
          />
        </CabinetSection>

        <CabinetSection
          eyebrow="Что помогает нам ответить быстрее"
          title="Пара полезных деталей"
          description="Не нужно писать длинно. Достаточно короткого и честного описания."
        >
          <CabinetCardGrid
            items={preset.checklist.map((item, index) => ({
              key: `${item}-${index}`,
              title: item,
              body:
                index === 0
                  ? "Это помогает понять среду, в которой все произошло."
                  : index === 1
                    ? "Так быстрее видно, с чего начать проверку."
                    : "Даже короткое уточнение часто экономит много времени.",
              badge: `Пункт ${index + 1}`,
              tone: "neutral" as const,
            }))}
          />
        </CabinetSection>
      </CabinetRoute>

      {composeOpen ? (
        <div className="fixed inset-0 z-[230] grid place-items-center bg-slate-950/48 p-4" onClick={() => setComposeOpen(false)}>
          <div
            className="w-full max-w-3xl rounded-[1.8rem] border border-slate-200/80 bg-white/96 p-5 shadow-[0_32px_80px_-50px_rgba(15,23,42,0.35)] dark:border-white/10 dark:bg-[#101713]/96 sm:p-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Новый кейс</p>
                <h2 className="mt-2 font-display text-2xl font-semibold text-slate-950 dark:text-slate-50">Опишите вопрос коротко и по делу</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{preset.intro}</p>
              </div>
              <button type="button" onClick={() => setComposeOpen(false)} className="outline-btn rounded-xl p-2" aria-label="Закрыть">
                <span className="material-symbols-rounded">close</span>
              </button>
            </div>

            <div className="mt-5 grid gap-5 lg:grid-cols-[0.92fr_1.08fr]">
              <div className="space-y-4">
                <div className="rounded-[1.3rem] border border-slate-200/80 bg-slate-50/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
                  <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                    Категория
                  </label>
                  <select
                    value={category}
                    onChange={(event) => setCategory(event.target.value as TicketCategory)}
                    className="mt-3 w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none dark:border-white/10 dark:bg-white/[0.04]"
                  >
                    {CATEGORIES.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={prepareTemplate}
                    className="mt-3 text-xs font-semibold uppercase tracking-[0.12em] text-emerald-800 dark:text-emerald-300"
                  >
                    Подставить шаблон
                  </button>
                </div>

                <div className="rounded-[1.3rem] border border-slate-200/80 bg-slate-50/90 p-4 dark:border-white/10 dark:bg-white/[0.04]">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Что стоит добавить</p>
                  <ul className="mt-3 space-y-2">
                    {preset.checklist.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
                        <span className="mt-2 h-2 w-2 rounded-full bg-emerald-700 dark:bg-emerald-400" />
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
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                  placeholder="Коротко: что случилось"
                />
                <textarea
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  rows={8}
                  className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                  placeholder="Опишите ситуацию так, чтобы нам было понятно, с чего начать."
                />

                <label className="block rounded-[1.3rem] border border-dashed border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm dark:border-white/10 dark:bg-white/[0.04]">
                  <span className="block font-medium text-slate-900 dark:text-slate-50">Вложение</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-500 dark:text-slate-400">
                    Скриншот, видео, PDF или текстовый файл до 20 МБ.
                  </span>
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
                  {attachmentFile ? <p className="mt-2 text-[11px] uppercase tracking-[0.12em] text-slate-500">{formatFileSize(attachmentFile.size)}</p> : null}
                </label>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={busy || !body.trim()}
                    onClick={() => void onCreateTicket()}
                    className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
                  >
                    {busy ? "Отправляем..." : "Создать кейс"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setSubject("");
                      setBody("");
                      setAttachmentFile(null);
                      setMessage("");
                    }}
                    className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
                  >
                    Очистить
                  </button>
                </div>
                {message ? <p className="text-sm text-emerald-700 dark:text-emerald-300">{message}</p> : null}
                {error ? <p className="text-sm text-rose-600 dark:text-rose-300">{error}</p> : null}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
