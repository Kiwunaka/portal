"use client";

import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
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

type TicketCategory = "Не могу подключиться" | "Вопрос по оплате" | "Медленно работает" | "Другое";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const CATEGORIES: TicketCategory[] = ["Не могу подключиться", "Вопрос по оплате", "Медленно работает", "Другое"];

const CATEGORY_PRESETS: Record<TicketCategory, { subject: string; body: string; hint: string }> = {
  "Не могу подключиться": {
    subject: "Не получается подключить устройство",
    body: "Что происходит:\n\nУстройство:\n\nЧто уже пробовали:",
    hint: "Устройство, шаг подключения и текст ошибки, если он есть.",
  },
  "Вопрос по оплате": {
    subject: "Вопрос по оплате или продлению",
    body: "Что ожидали увидеть:\n\nЧто произошло вместо этого:\n\nПримерное время оплаты:",
    hint: "Срок, способ оплаты и примерное время операции.",
  },
  "Медленно работает": {
    subject: "Нестабильная скорость или подключение",
    body: "Как выглядит проблема:\n\nУстройство:\n\nWi-Fi или мобильная сеть:",
    hint: "Где заметно замедление и когда оно началось.",
  },
  Другое: {
    subject: "Вопрос по кабинету POKROV",
    body: "Коротко опишите вопрос:\n\nКакой результат нужен:",
    hint: "Любой вопрос по кабинету, доступу или устройствам.",
  },
};

function icon(name: string) {
  return <span className="material-symbols-rounded text-[20px]">{name}</span>;
}

function statusLabel(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "Открыт";
  if (normalized === "in_progress") return "В работе";
  if (normalized === "closed") return "Закрыт";
  return normalized || "Неизвестно";
}

function formatDate(value?: string | null): string {
  if (!value) return "недавно";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "недавно";
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
  const [notice, setNotice] = useState("");

  const supportLink = user?.support?.link || config.supportTelegramUrl;
  const latestTicket = tickets[0] || null;
  const openCount = tickets.filter((ticket) => String(ticket.status || "").toLowerCase() !== "closed").length;
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const deviceLimit = getDeviceLimit(dash, user);
  const preset = CATEGORY_PRESETS[category];

  const loadTickets = async (): Promise<void> => {
    setLoadingTickets(true);
    try {
      const rows = await fetchTickets(20);
      setTickets(rows);
      setError("");
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || ""));
    } finally {
      setLoadingTickets(false);
    }
  };

  useEffect(() => {
    void loadTickets();
  }, []);

  const openComposer = (nextCategory: TicketCategory = category): void => {
    const nextPreset = CATEGORY_PRESETS[nextCategory];
    setCategory(nextCategory);
    setSubject((current) => current || nextPreset.subject);
    setBody((current) => current || nextPreset.body);
    setNotice("");
    setComposeOpen(true);
  };

  const onCreateTicket = async (): Promise<void> => {
    const normalizedBody = body.trim();
    const normalizedSubject = subject.trim();

    if (!normalizedBody) {
      setNotice("Добавьте пару строк: что делали, где сломалось и что видите сейчас.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");

    try {
      let attachment: TicketAttachmentInput | undefined;
      if (attachmentFile) {
        const uploaded = await uploadTicketAttachment(attachmentFile);
        attachment = uploaded.attachment;
      }

      const title = normalizedSubject ? `[${category}] ${normalizedSubject}` : `[${category}] Обращение из кабинета`;
      const created = await createTicket(title, normalizedBody, attachment || undefined);

      setComposeOpen(false);
      setSubject("");
      setBody("");
      setAttachmentFile(null);
      await loadTickets();
      setNotice(`Обращение #${created.id} создано.`);
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || ""));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <main className="mx-auto w-full max-w-[840px] space-y-5">
        <CabinetStatus
          title="Помощь"
          meta={latestTicket ? `${statusLabel(latestTicket.status)} · #${latestTicket.id}` : "Кабинет и Telegram"}
          body={
            latestTicket
              ? "Продолжайте уже открытое обращение: история, вложения и контекст останутся в одном месте."
              : "Опишите проблему коротко. Личные ссылки, коды оплаты и банковские данные присылать не нужно."
          }
          tone={openCount ? "info" : "neutral"}
          action={
            <button type="button" onClick={() => openComposer(CATEGORIES[0])} className="btn-primary w-full rounded-full px-5 py-3 text-sm font-semibold sm:w-auto">
              Новый вопрос
            </button>
          }
        />

        <CabinetGroup
          title="Последнее обращение"
          action={
            latestTicket ? (
              <AppRouteLink href={`/support/thread/?id=${latestTicket.id}`} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                Открыть
              </AppRouteLink>
            ) : null
          }
        >
          {loadingTickets ? (
            <CabinetRow icon={icon("hourglass_empty")} label="Загружаем обращения" hint="Обычно это занимает несколько секунд" />
          ) : latestTicket ? (
            <CabinetRow
              icon={icon("forum")}
              label={latestTicket.subject || `Обращение #${latestTicket.id}`}
              hint={latestTicket.last_message_preview || "Сообщений пока нет"}
              value={formatDate(latestTicket.updated_at || latestTicket.created_at)}
              href={`/support/thread/?id=${latestTicket.id}`}
            />
          ) : (
            <CabinetRow icon={icon("chat_bubble")} label="Обращений пока нет" hint="Создайте первый вопрос, если что-то пошло не так" />
          )}
        </CabinetGroup>

        <CabinetGroup title="Быстрые действия">
          <CabinetRow
            icon={icon("add_comment")}
            label="Новый вопрос"
            hint="Короткая форма с вложением"
            action={
              <button type="button" onClick={() => openComposer(CATEGORIES[0])} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                Написать
              </button>
            }
          />
          <CabinetRow
            icon={icon("send")}
            label="Telegram"
            hint="Удобно для быстрого живого ответа"
            action={
              <AppRouteLink href={supportLink} target="_blank" hardNavigate={false} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                Открыть
              </AppRouteLink>
            }
          />
          <CabinetRow icon={icon("download")} label="Скачать приложение" hint="Android APK и Windows beta" href="/downloads/" />
          <CabinetRow icon={icon("key")} label="Активировать код" hint="Оплата, подарок или промокод" href="/redeem/" />
        </CabinetGroup>

        <CabinetGroup title="Диагностика">
          <CabinetRow icon={icon("verified_user")} label="Доступ" hint="Без личных ссылок и ключей" value={resolvePlanLabel(dash, user)} />
          <CabinetRow icon={icon("devices")} label="Устройства" hint="Сколько связано с профилем" value={`${deviceCount} из ${deviceLimit}`} />
          <CabinetRow icon={icon("wifi_tethering")} label="Подключения" hint="Только безопасная сводка" value={String(activeConnections)} />
          <CabinetRow icon={icon("description")} label="Документы" hint="Оплата и условия" href="/support/legal/" />
        </CabinetGroup>

        {notice ? <p className="px-1 text-sm font-semibold text-emerald-800 dark:text-emerald-300">{notice}</p> : null}
        {error ? <p className="px-1 text-sm text-rose-600 dark:text-rose-300">{error}</p> : null}
      </main>

      {composeOpen ? (
        <div className="fixed inset-0 z-[230] grid place-items-end bg-slate-950/48 p-0 sm:place-items-center sm:p-4" onClick={() => setComposeOpen(false)}>
          <div
            className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-t-3xl border border-slate-200/80 bg-white/96 p-5 shadow-[0_32px_80px_-50px_rgba(15,23,42,0.35)] dark:border-white/10 dark:bg-[#101713]/96 sm:rounded-3xl sm:p-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Новое обращение</p>
                <h2 className="mt-2 text-2xl font-semibold leading-tight text-slate-950 dark:text-slate-50">Новый вопрос</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{preset.hint}</p>
              </div>
              <button type="button" onClick={() => setComposeOpen(false)} className="outline-btn rounded-xl p-2" aria-label="Закрыть">
                <span className="material-symbols-rounded">close</span>
              </button>
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {CATEGORIES.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => {
                    const nextPreset = CATEGORY_PRESETS[item];
                    setCategory(item);
                    setSubject(nextPreset.subject);
                    setBody(nextPreset.body);
                  }}
                  className={`rounded-full border px-4 py-2 text-sm font-semibold transition active:scale-[0.98] ${
                    item === category
                      ? "border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-400/40 dark:bg-emerald-500/15 dark:text-emerald-100"
                      : "border-slate-200 bg-white text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>

            <div className="mt-5 space-y-4">
              <input
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
                className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                placeholder="Коротко: что случилось"
              />
              <textarea
                value={body}
                onChange={(event) => setBody(event.target.value)}
                rows={7}
                className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
                placeholder="Опишите, что делали, где сломалось и что видите сейчас."
              />

              <label className="block rounded-2xl border border-dashed border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm dark:border-white/10 dark:bg-white/[0.04]">
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
                {attachmentFile ? <p className="mt-2 text-xs text-slate-500">{formatFileSize(attachmentFile.size)}</p> : null}
              </label>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  disabled={busy || !body.trim()}
                  onClick={() => void onCreateTicket()}
                  className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
                >
                  {busy ? "Отправляем..." : "Отправить вопрос"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSubject("");
                    setBody("");
                    setAttachmentFile(null);
                    setNotice("");
                  }}
                  className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold"
                >
                  Очистить
                </button>
              </div>
              {notice ? <p className="text-sm text-emerald-700 dark:text-emerald-300">{notice}</p> : null}
              {error ? <p className="text-sm text-rose-600 dark:text-rose-300">{error}</p> : null}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
