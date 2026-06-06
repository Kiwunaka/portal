"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { SupportMessageBody } from "@/components/support-message-body";
import { addTicketMessage, getTicket, resolveApiUrl, uploadTicketAttachment, type TicketAttachmentInput, type TicketInfo, type TicketMessage } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

function icon(name: string) {
  return <span className="material-symbols-rounded text-[20px]">{name}</span>;
}

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

type ParsedAttachment = {
  kind: "image" | "video" | "file" | "link";
  url: string;
  name: string;
  contentType: string;
  size: number;
};

type QuickReplyAction = {
  label: string;
  body: string;
};

const QUICK_REPLY_ACTIONS: QuickReplyAction[] = [
  {
    label: "Не получилось",
    body: "Не получилось после этих шагов.\n\nУстройство:\nКлиент:\nНа каком шаге остановилось:\nЧто видно на экране:",
  },
  {
    label: "Дайте шаги",
    body: "Можно, пожалуйста, пошагово для моего устройства?\n\nУстройство:\nКлиент, если уже установлен:\nЧто хочу сделать:",
  },
  {
    label: "Уточнить",
    body: "Уточняю детали:\n\nЧто пробовал:\nЧто изменилось:\nТекст ошибки, если есть:",
  },
  {
    label: "Нужен оператор",
    body: "Нужна ручная проверка оператором.\n\nКоротко что случилось:\nПримерное время проблемы:\nСкриншот могу приложить без личной ссылки и QR.",
  },
];

function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 Б";
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
}

function ticketAttachment(message: TicketMessage): ParsedAttachment | null {
  try {
    const payload = JSON.parse(String(message.media_payload || "{}"));
    const rawUrl = String(payload?.url || "").trim();
    if (!rawUrl) return null;
    if (rawUrl.startsWith("/uploads/support/")) {
      const kind = String(message.media_type || "").toLowerCase();
      return {
        kind: kind === "video" ? "video" : kind === "image" ? "image" : "file",
        url: resolveApiUrl(rawUrl),
        name: String(payload?.name || "Вложение"),
        contentType: String(payload?.content_type || ""),
        size: Number(payload?.size || 0),
      };
    }
    const parsed = new URL(rawUrl);
    if (!["http:", "https:"].includes(parsed.protocol)) {
      return null;
    }
    return {
      kind: String(message.media_type || "").toLowerCase() === "link" ? "link" : "file",
      url: parsed.toString(),
      name: String(payload?.name || "Вложение"),
      contentType: String(payload?.content_type || ""),
      size: Number(payload?.size || 0),
    };
  } catch {
    return null;
  }
}

export default function SupportTicketThreadPage() {
  const searchParams = useSearchParams();
  const ticketId = Number(searchParams.get("id") || 0);

  const [ticket, setTicket] = useState<TicketInfo | null>(null);
  const [message, setMessage] = useState("");
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [replyError, setReplyError] = useState("");
  const listEndRef = useRef<HTMLDivElement | null>(null);

  const canReply = useMemo(() => Boolean(ticket && String(ticket.status || "").toLowerCase() !== "closed"), [ticket]);

  const loadTicket = useCallback(async (): Promise<void> => {
    if (!ticketId) {
      setLoading(false);
      setError("Не передан ID обращения");
      return;
    }
    setLoading(true);
    try {
      const data = await getTicket(ticketId);
      setTicket(data);
      setError("");
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError));
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    void loadTicket();
  }, [loadTicket]);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [ticket?.messages?.length]);

  const onSendReply = async (): Promise<void> => {
    if (!ticket || !message.trim() || !canReply) return;
    setBusy(true);
    setReplyError("");
    try {
      let attachment: TicketAttachmentInput | undefined;
      if (attachmentFile) {
        const uploaded = await uploadTicketAttachment(attachmentFile);
        attachment = uploaded.attachment;
      }
      const updated = await addTicketMessage(ticket.id, message.trim(), attachment || undefined);
      setTicket(updated);
      setMessage("");
      setAttachmentFile(null);
    } catch (nextError) {
      setReplyError(String((nextError as { message?: string })?.message || nextError));
    } finally {
      setBusy(false);
    }
  };

  const applyQuickReply = (body: string): void => {
    setReplyError("");
    setMessage((current) => {
      const existing = current.trim();
      return existing ? `${existing}\n\n${body}` : body;
    });
  };

  if (loading) {
    return (
      <main className="mx-auto w-full max-w-[840px] space-y-5">
        <CabinetStatus title="Загружаем обращение" meta="Поддержка" body="Подтягиваем историю и вложения." tone="neutral" />
        <CabinetGroup title="История">
          <CabinetRow icon={icon("hourglass_empty")} label="Пожалуйста, подождите" hint="Обычно это занимает несколько секунд" />
        </CabinetGroup>
      </main>
    );
  }

  if (error || !ticket) {
    return (
      <main className="mx-auto w-full max-w-[840px] space-y-5">
        <CabinetStatus
          title="Не удалось открыть обращение"
          meta="Поддержка"
          body={error || "Обращение не найдено."}
          tone="warning"
          action={
            <AppRouteLink href="/support/" className="outline-btn w-full rounded-full px-5 py-3 text-center text-sm font-semibold sm:w-auto">
              Назад
            </AppRouteLink>
          }
        />
        <CabinetGroup title="Что дальше">
          <CabinetRow icon={icon("support_agent")} label="Открыть поддержку" hint="Создайте новое обращение или выберите другое" href="/support/" />
        </CabinetGroup>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[840px] space-y-5">
      <CabinetStatus
        title={`Обращение #${ticket.id}`}
        meta={statusTitle(ticket.status)}
        body={ticket.subject || "Обращение без темы"}
        tone={canReply ? "info" : "neutral"}
        action={
          <AppRouteLink href="/support/" className="outline-btn w-full rounded-full px-5 py-3 text-center text-sm font-semibold sm:w-auto">
            К списку
          </AppRouteLink>
        }
      />

      <CabinetGroup title="Сводка">
        <CabinetRow icon={icon("label")} label="Тема" hint="В этом обращении" value={ticket.subject || "Без темы"} />
        <CabinetRow icon={icon("pending_actions")} label="Статус" hint={canReply ? "Можно отправить ответ" : "Обращение закрыто"} value={statusTitle(ticket.status)} />
        <CabinetRow icon={icon("chat_bubble")} label="Сообщений" hint="Вся история остается здесь" value={String(ticket.messages.length)} />
        <CabinetRow icon={icon("schedule")} label="Обновлено" hint="Последнее изменение" value={fmtDate(ticket.updated_at)} />
      </CabinetGroup>

      <CabinetGroup title="История">
        <div className="max-h-[52vh] space-y-4 overflow-y-auto p-4">
          {ticket.messages.length === 0 ? (
            <p className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-3 text-sm text-slate-500 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-400">
              История сообщений пока пустая.
            </p>
          ) : (
            ticket.messages.map((msg) => {
              const isAdmin = msg.sender_role === "admin";
              const isAssistant = msg.sender_role === "assistant";
              const senderLabel = isAdmin ? "Оператор" : isAssistant ? "AI-помощник" : "Вы";
              const attachment = ticketAttachment(msg);
              return (
                <div key={msg.id} className={`flex ${isAdmin || isAssistant ? "justify-start" : "justify-end"}`}>
                  <div className={`max-w-[88%] rounded-2xl border px-4 py-3 text-sm leading-6 ${
                    isAdmin
                      ? "border-slate-200/80 bg-white/86 dark:border-white/10 dark:bg-white/[0.04]"
                      : isAssistant
                        ? "border-sky-200/80 bg-sky-50/85 dark:border-sky-500/25 dark:bg-sky-500/10"
                        : "border-emerald-200/80 bg-emerald-50/85 dark:border-emerald-500/25 dark:bg-emerald-500/10"
                  }`}>
                    <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">{senderLabel}</p>
                    <SupportMessageBody body={msg.body} className="mt-1" />
                    {attachment?.kind === "image" ? (
                      <a href={attachment.url} target="_blank" rel="noreferrer" className="mt-3 block overflow-hidden rounded-2xl border border-slate-200/80 dark:border-white/10">
                        <img src={attachment.url} alt={attachment.name || "Вложение"} className="max-h-72 w-full object-cover" />
                      </a>
                    ) : null}
                    {attachment?.kind === "video" ? (
                      <video src={attachment.url} controls className="mt-3 max-h-72 w-full rounded-2xl border border-slate-200/80 bg-slate-950/60 dark:border-white/10" />
                    ) : null}
                    {attachment && attachment.kind !== "image" && attachment.kind !== "video" ? (
                      <a
                        href={attachment.url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 flex items-center justify-between gap-3 rounded-2xl border border-slate-200/80 bg-white/80 px-3 py-2 text-xs dark:border-white/10 dark:bg-white/[0.04]"
                      >
                        <span className="truncate">{attachment.name || "Вложение"}</span>
                        <span className="shrink-0 text-slate-500 dark:text-slate-400">{attachment.size ? formatFileSize(attachment.size) : "Открыть"}</span>
                      </a>
                    ) : null}
                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{fmtDate(msg.created_at)}</p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={listEndRef} />
        </div>
      </CabinetGroup>

      <CabinetGroup title="Ответ">
        {!canReply ? (
          <CabinetRow icon={icon("lock")} label="Обращение закрыто" hint="Для нового вопроса создайте новое обращение" href="/support/" />
        ) : (
          <div className="space-y-3 p-4">
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              rows={4}
              placeholder="Напишите ответ..."
              className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
            />
            <div className="flex flex-wrap gap-2">
              {QUICK_REPLY_ACTIONS.map((action) => (
                <button
                  key={action.label}
                  type="button"
                  onClick={() => applyQuickReply(action.body)}
                  className="rounded-xl border border-slate-200/80 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-emerald-400/60 hover:bg-emerald-500/10 active:scale-[0.98] dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200"
                >
                  {action.label}
                </button>
              ))}
            </div>
            <label className="block rounded-2xl border border-dashed border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm dark:border-white/10 dark:bg-white/[0.04]">
              <span className="block font-medium">Добавить вложение</span>
              <span className="mt-1 block text-xs text-slate-500 dark:text-slate-400">Скриншот, видео, PDF или текстовый файл до 20 МБ.</span>
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
              {attachmentFile ? <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{formatFileSize(attachmentFile.size)}</p> : null}
            </label>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void onSendReply()}
                disabled={busy || !message.trim()}
                className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
              >
                {busy ? "Отправляем..." : "Отправить"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setMessage("");
                  setAttachmentFile(null);
                  setReplyError("");
                }}
                className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold"
              >
                Очистить
              </button>
            </div>
            {replyError ? <p className="text-sm text-rose-600 dark:text-rose-300">{replyError}</p> : null}
          </div>
        )}
      </CabinetGroup>
    </main>
  );
}
