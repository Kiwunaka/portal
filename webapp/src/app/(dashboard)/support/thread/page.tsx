"use client";

import { CalendarClock, Hourglass, LifeBuoy, Lock, MessageCircle, MessagesSquare, Tag, Timer } from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { Note } from "@/components/ui/note";
import { Textarea } from "@/components/ui/input";
import { SupportMessageBody } from "@/components/support-message-body";
import { addTicketMessage, getTicket, resolveApiUrl, uploadTicketAttachment, type TicketAttachmentInput, type TicketInfo, type TicketMessage } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
      <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
        <StatusHero title="Загружаем обращение" meta="Поддержка" body="Подтягиваем историю и вложения." tone="neutral" />
        <GroupedSection title="История">
          <Row icon={Hourglass} label="Пожалуйста, подождите" hint="Обычно это занимает несколько секунд" />
        </GroupedSection>
      </main>
    );
  }

  if (error || !ticket) {
    return (
      <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
        <StatusHero
          title="Не удалось открыть обращение"
          meta="Поддержка"
          body={error || "Обращение не найдено."}
          tone="warning"
          action={
            <Button variant="secondary" href="/support/" className="w-full sm:w-auto">
              Назад
            </Button>
          }
        />
        <GroupedSection title="Что дальше">
          <Row icon={LifeBuoy} label="Открыть поддержку" hint="Создайте новое обращение или выберите другое" href="/support/" />
        </GroupedSection>
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title={`Обращение #${ticket.id}`}
        meta={statusTitle(ticket.status)}
        body={ticket.subject || "Обращение без темы"}
        tone={canReply ? "info" : "neutral"}
        icon={MessagesSquare}
        action={
          <Button variant="secondary" href="/support/" className="w-full sm:w-auto">
            К списку
          </Button>
        }
      />

      <GroupedSection title="Сводка">
        <Row icon={Tag} label="Тема" hint="В этом обращении" value={ticket.subject || "Без темы"} />
        <Row icon={Timer} label="Статус" hint={canReply ? "Можно отправить ответ" : "Обращение закрыто"} value={statusTitle(ticket.status)} />
        <Row icon={MessageCircle} label="Сообщений" hint="Вся история остается здесь" value={String(ticket.messages.length)} />
        <Row icon={CalendarClock} label="Обновлено" hint="Последнее изменение" value={fmtDate(ticket.updated_at)} />
      </GroupedSection>

      <GroupedSection title="История">
        <div className="max-h-[52vh] space-y-4 overflow-y-auto p-4">
          {ticket.messages.length === 0 ? (
            <p className="rounded-control border border-line bg-canvas-alt px-4 py-3 text-sm text-ink-muted">
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
                  <div
                    className={`max-w-[88%] rounded-card border px-4 py-3 text-sm leading-6 ${
                      isAdmin
                        ? "border-line bg-surface text-ink"
                        : isAssistant
                          ? "border-info-line bg-info-bg text-info-text"
                          : "border-ok-line bg-ok-bg text-ok-text"
                    }`}
                  >
                    <p className="text-xs font-semibold opacity-70">{senderLabel}</p>
                    <SupportMessageBody body={msg.body} className="mt-1" />
                    {attachment?.kind === "image" ? (
                      <a href={attachment.url} target="_blank" rel="noreferrer" className="mt-3 block overflow-hidden rounded-tile border border-line">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={attachment.url} alt={attachment.name || "Вложение"} className="max-h-72 w-full object-cover" />
                      </a>
                    ) : null}
                    {attachment?.kind === "video" ? (
                      <video src={attachment.url} controls className="mt-3 max-h-72 w-full rounded-tile border border-line bg-black/60" />
                    ) : null}
                    {attachment && attachment.kind !== "image" && attachment.kind !== "video" ? (
                      <a
                        href={attachment.url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-3 flex items-center justify-between gap-3 rounded-tile border border-line bg-surface px-3 py-2 text-xs"
                      >
                        <span className="truncate">{attachment.name || "Вложение"}</span>
                        <span className="shrink-0 opacity-70">{attachment.size ? formatFileSize(attachment.size) : "Открыть"}</span>
                      </a>
                    ) : null}
                    <p className="mt-2 text-xs opacity-60">{fmtDate(msg.created_at)}</p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={listEndRef} />
        </div>
      </GroupedSection>

      <GroupedSection title="Ответ">
        {!canReply ? (
          <Row icon={Lock} label="Обращение закрыто" hint="Для нового вопроса создайте новое обращение" href="/support/" />
        ) : (
          <div className="space-y-3 p-4">
            <Textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              rows={4}
              placeholder="Напишите ответ..."
            />
            <div className="flex flex-wrap gap-2">
              {QUICK_REPLY_ACTIONS.map((action) => (
                <Chip key={action.label} onClick={() => applyQuickReply(action.body)}>
                  {action.label}
                </Chip>
              ))}
            </div>
            <label className="block rounded-control border border-dashed border-line bg-canvas-alt px-4 py-4 text-sm">
              <span className="block font-medium text-ink">Добавить вложение</span>
              <span className="mt-1 block text-xs text-ink-muted">Скриншот, видео, PDF или текстовый файл до 20 МБ.</span>
              <input
                type="file"
                accept="image/*,video/*,.pdf,.txt,.log,application/pdf,text/plain"
                className="mt-3 block w-full cursor-pointer text-sm text-ink-soft file:mr-3 file:rounded-control file:border-0 file:bg-brand-soft file:px-4 file:py-2 file:font-medium file:text-brand"
                onChange={(event) => setAttachmentFile(event.target.files?.[0] ?? null)}
              />
              {attachmentFile ? (
                <div className="mt-3 flex items-center justify-between gap-3 rounded-tile bg-surface px-3 py-2 text-xs">
                  <span className="truncate">{attachmentFile.name}</span>
                  <button type="button" onClick={() => setAttachmentFile(null)} className="text-danger-text">
                    Убрать
                  </button>
                </div>
              ) : null}
              {attachmentFile ? <p className="mt-2 text-xs text-ink-muted">{formatFileSize(attachmentFile.size)}</p> : null}
            </label>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => void onSendReply()} disabled={busy || !message.trim()}>
                {busy ? "Отправляем..." : "Отправить"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setMessage("");
                  setAttachmentFile(null);
                  setReplyError("");
                }}
              >
                Очистить
              </Button>
            </div>
            {replyError ? <Note tone="danger">{replyError}</Note> : null}
          </div>
        )}
      </GroupedSection>
    </main>
  );
}
