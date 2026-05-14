"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetHero, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
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
    } catch (error) {
      setError(String((error as { message?: string })?.message || error));
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
    } catch (error) {
      setReplyError(String((error as { message?: string })?.message || error));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <CabinetRoute eyebrow="Поддержка" title="Загружаем обращение" description="Подтягиваем историю кейса и вложения.">
        <CabinetSection eyebrow="История" title="Пожалуйста, подождите" description="Обычно это занимает несколько секунд.">
          <div className="atlas-skeleton min-h-40 rounded-[var(--pokrov-radius-card,0.875rem)]" />
        </CabinetSection>
      </CabinetRoute>
    );
  }

  if (error || !ticket) {
    return (
      <CabinetRoute
        eyebrow="Поддержка"
        title="Не удалось открыть обращение"
        description={error || "Обращение не найдено."}
        actions={
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Назад в поддержку
          </AppRouteLink>
        }
      >
        <CabinetSection eyebrow="Что дальше" title="Вернитесь к списку кейсов" description="Если обращение было закрыто или ссылка устарела, создайте новый кейс из раздела поддержки.">
          <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Открыть поддержку
          </AppRouteLink>
        </CabinetSection>
      </CabinetRoute>
    );
  }

  return (
    <CabinetRoute
      eyebrow="Поддержка"
      title={ticket.subject || "Обращение без темы"}
      description={`Кейс #${ticket.id}. Статус: ${statusTitle(ticket.status)}. Обновлен ${fmtDate(ticket.updated_at)}.`}
      actions={
        <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
          К списку
        </AppRouteLink>
      }
      metrics={[
        {
          label: "Кейс",
          value: `#${ticket.id}`,
          hint: "Этот номер можно назвать поддержке.",
          tone: "neutral",
        },
        {
          label: "Статус",
          value: statusTitle(ticket.status),
          hint: canReply ? "Можно отправить ответ." : "Кейс закрыт.",
          tone: canReply ? "info" : "neutral",
        },
        {
          label: "Сообщений",
          value: String(ticket.messages.length),
          hint: "Вся история остается здесь.",
          tone: "neutral",
        },
        {
          label: "Вложения",
          value: attachmentFile ? "Готово" : "По желанию",
          hint: "Скриншот или видео можно добавить к ответу.",
          tone: attachmentFile ? "success" : "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Диалог"
        badge={statusTitle(ticket.status)}
        badgeTone={canReply ? "info" : "neutral"}
        title="Продолжайте этот же кейс"
        description="Так не теряется история, вложения и контекст. Не присылайте личные ссылки или ключи, если поддержка прямо их не запросила."
        details={[
          {
            label: "Тема",
            value: ticket.subject || "Без темы",
            hint: "Можно уточнить детали ниже.",
            tone: "neutral",
          },
          {
            label: "Последнее обновление",
            value: fmtDate(ticket.updated_at),
            hint: "Время отображается по данным backend.",
            tone: "neutral",
          },
          {
            label: "Ответ",
            value: canReply ? "Доступен" : "Закрыт",
            hint: canReply ? "Напишите коротко, что изменилось." : "Для нового вопроса создайте новый кейс.",
            tone: canReply ? "success" : "neutral",
          },
        ]}
      />

      <CabinetSection eyebrow="История" title="Сообщения по кейсу" description="Здесь только переписка и вложения к этому обращению.">
        <div className="max-h-[52vh] space-y-4 overflow-y-auto pr-1">
          {ticket.messages.length === 0 ? (
            <div className="rounded-[var(--pokrov-radius-card,0.875rem)] border border-[color:var(--atlas-border)] bg-[var(--atlas-surface)] px-4 py-3 text-sm text-[var(--atlas-text-soft)]">История сообщений пока пустая.</div>
            ) : (
              ticket.messages.map((msg) => {
                const isAdmin = msg.sender_role === "admin";
                const attachment = ticketAttachment(msg);
                return (
                  <div key={msg.id} className={`flex ${isAdmin ? "justify-start" : "justify-end"}`}>
                    <div className={`max-w-[86%] rounded-2xl border border-[color:var(--atlas-border)] px-4 py-3 text-sm leading-6 ${isAdmin ? "bg-[var(--atlas-surface)]" : "bg-[var(--atlas-status-info-bg)]"}`}>
                      <p className="text-xs font-semibold text-[var(--atlas-text-muted)]">{isAdmin ? "Оператор" : "Вы"}</p>
                      <p className="mt-1 whitespace-pre-line">{msg.body}</p>
                      {attachment?.kind === "image" ? (
                        <a href={attachment.url} target="_blank" rel="noreferrer" className="mt-3 block overflow-hidden rounded-2xl border border-[color:var(--atlas-border)]">
                          <img src={attachment.url} alt={attachment.name || "Вложение"} className="max-h-72 w-full object-cover" />
                        </a>
                      ) : null}
                      {attachment?.kind === "video" ? (
                        <video src={attachment.url} controls className="mt-3 max-h-72 w-full rounded-2xl border border-[color:var(--atlas-border)] bg-slate-950/60" />
                      ) : null}
                      {attachment && attachment.kind !== "image" && attachment.kind !== "video" ? (
                        <a
                          href={attachment.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-3 flex items-center justify-between gap-3 rounded-2xl border border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] px-3 py-2 text-xs"
                        >
                          <span className="truncate">{attachment.name || "Вложение"}</span>
                          <span className="shrink-0 text-[var(--atlas-text-muted)]">{attachment.size ? formatFileSize(attachment.size) : "Открыть"}</span>
                        </a>
                      ) : null}
                      <p className="mt-2 text-xs text-[var(--atlas-text-muted)]">{fmtDate(msg.created_at)}</p>
                    </div>
                  </div>
              );
            })
          )}
          <div ref={listEndRef} />
        </div>

        <div className="mt-4 border-t border-[color:var(--atlas-border)] pt-4">
          {!canReply ? (
            <p className="text-sm text-[var(--atlas-text-soft)]">Обращение закрыто. Для нового вопроса создайте новое обращение.</p>
          ) : (
            <>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={4}
                placeholder="Напишите ответ..."
                className="w-full rounded-xl border border-[color:var(--atlas-border)] bg-[var(--atlas-surface)] px-4 py-3 text-sm outline-none transition focus:border-emerald-400"
              />
              <label className="mt-3 block rounded-2xl border border-dashed border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] px-4 py-4 text-sm">
                <span className="block font-medium">Добавить вложение</span>
                <span className="mt-1 block text-xs text-[var(--atlas-text-muted)]">Скриншот, видео, PDF или текстовый файл до 20 МБ.</span>
                <input
                  type="file"
                  accept="image/*,video/*,.pdf,.txt,.log,application/pdf,text/plain"
                  className="mt-3 block w-full cursor-pointer text-sm text-[var(--atlas-text-soft)] file:mr-3 file:rounded-xl file:border-0 file:bg-emerald-500/15 file:px-4 file:py-2 file:font-medium file:text-emerald-700 dark:file:bg-emerald-500/20 dark:file:text-emerald-200"
                  onChange={(event) => setAttachmentFile(event.target.files?.[0] ?? null)}
                />
                {attachmentFile ? (
                  <div className="mt-3 flex items-center justify-between gap-3 rounded-xl bg-[var(--atlas-surface)] px-3 py-2 text-xs">
                    <span className="truncate">{attachmentFile.name}</span>
                    <button type="button" onClick={() => setAttachmentFile(null)} className="text-rose-500">
                      Убрать
                    </button>
                  </div>
                ) : null}
                {attachmentFile ? <p className="mt-2 text-xs text-[var(--atlas-text-muted)]">{formatFileSize(attachmentFile.size)}</p> : null}
              </label>
              <div className="mt-3 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void onSendReply()}
                  disabled={busy || !message.trim()}
                  className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold disabled:opacity-60"
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
                  className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold"
                >
                  Очистить
                </button>
              </div>
              {replyError ? <p className="mt-2 text-xs text-rose-500">{replyError}</p> : null}
            </>
          )}
        </div>
      </CabinetSection>
    </CabinetRoute>
  );
}
