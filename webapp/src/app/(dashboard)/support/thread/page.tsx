"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { addTicketMessage, getTicket, resolveApiUrl, uploadTicketAttachment, type TicketAttachmentInput, type TicketInfo, type TicketMessage } from "@/lib/api";

function statusTitle(status: string): string {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "open") return "Открыт";
  if (normalized === "in_progress") return "В работе";
  if (normalized === "closed") return "Закрыт";
  return normalized || "Уточняется";
}

function fmtDate(value?: string | null): string {
  if (!value) return "без даты";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "обновлено недавно";
  return parsed.toLocaleString("ru-RU");
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

  const canReply = useMemo(() => ticket && String(ticket.status || "").toLowerCase() !== "closed", [ticket]);

  const loadTicket = useCallback(async (): Promise<void> => {
    if (!ticketId) {
      setLoading(false);
      setError("Не передан номер кейса.");
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

  if (loading) {
    return (
      <CabinetRoute eyebrow="Поддержка" title="Открываем кейс" description="Подтягиваем историю и вложения. Если сеть медленная, это может занять несколько секунд.">
        <CabinetSection title="История" description="Пока показываем честное состояние загрузки.">
          <div className="space-y-3">
            <div className="h-16 animate-pulse rounded-[1.2rem] bg-slate-100 dark:bg-white/[0.06]" />
            <div className="h-24 animate-pulse rounded-[1.2rem] bg-slate-100 dark:bg-white/[0.06]" />
          </div>
        </CabinetSection>
      </CabinetRoute>
    );
  }

  if (error || !ticket) {
    return (
      <CabinetRoute
        eyebrow="Поддержка"
        title="Не удалось открыть кейс"
        description={error || "Кейс не найден. Возможно, ссылка устарела или номер был передан не полностью."}
        actions={
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            К поддержке
          </AppRouteLink>
        }
      >
        <CabinetSection title="Что можно сделать" description="Вернитесь к списку кейсов или создайте новый, если вопрос еще актуален.">
          <AppRouteLink href="/support/" className="btn-primary inline-flex rounded-2xl px-5 py-3 text-sm font-semibold">
            Открыть список кейсов
          </AppRouteLink>
        </CabinetSection>
      </CabinetRoute>
    );
  }

  return (
    <CabinetRoute
      eyebrow="Поддержка"
      title={ticket.subject || `Кейс #${ticket.id}`}
      description={`${statusTitle(ticket.status)} · обновлен ${fmtDate(ticket.updated_at || ticket.created_at)}`}
      actions={
        <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
          К списку
        </AppRouteLink>
      }
      metrics={[
        {
          label: "Кейс",
          value: `#${ticket.id}`,
          hint: "Номер нужен только для продолжения этой истории.",
          tone: "neutral",
        },
        {
          label: "Состояние",
          value: statusTitle(ticket.status),
          hint: canReply ? "Можно добавить уточнение или вложение." : "Кейс закрыт, история остается доступной.",
          tone: canReply ? "info" : "neutral",
        },
        {
          label: "Сообщений",
          value: String(ticket.messages.length),
          hint: "Все сообщения остаются в одном месте.",
          tone: "neutral",
        },
        {
          label: "Обновлен",
          value: fmtDate(ticket.updated_at || ticket.created_at),
          hint: "Показываем последнюю известную дату.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetSection
        eyebrow="История"
        title="Переписка по кейсу"
        description="Ответы и вложения сохраняются в кейсе, чтобы не терять контекст. Мы не обещаем мгновенный диалог на этом экране."
      >
        <div className="max-h-[52vh] space-y-4 overflow-y-auto rounded-[1.3rem] border border-slate-200/80 bg-slate-50/70 p-3 pr-2 dark:border-white/10 dark:bg-white/[0.03]">
          {ticket.messages.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200/80 bg-white/80 px-4 py-3 text-sm text-slate-500 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-400">
              История сообщений пока пустая. Добавьте первое уточнение ниже.
            </div>
          ) : (
            ticket.messages.map((msg) => {
              const isAdmin = msg.sender_role === "admin";
              const attachment = ticketAttachment(msg);
              return (
                <div key={msg.id} className={`flex ${isAdmin ? "justify-start" : "justify-end"}`}>
                  <div
                    className={`max-w-[88%] rounded-2xl border px-4 py-3 text-sm leading-6 shadow-[0_18px_45px_-38px_rgba(15,23,42,0.22)] ${
                      isAdmin
                        ? "border-slate-200/80 bg-white text-slate-800 dark:border-white/10 dark:bg-[#101713] dark:text-slate-100"
                        : "border-emerald-200/70 bg-emerald-50 text-emerald-950 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-100"
                    }`}
                  >
                    <p className="text-xs uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">{isAdmin ? "Поддержка" : "Вы"}</p>
                    <p className="mt-1 whitespace-pre-line">{msg.body}</p>
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
                        className="mt-3 flex items-center justify-between gap-3 rounded-2xl border border-slate-200/80 bg-white/75 px-3 py-2 text-xs dark:border-white/10 dark:bg-white/5"
                      >
                        <span className="truncate">{attachment.name || "Вложение"}</span>
                        <span className="shrink-0 text-slate-500">{attachment.size ? formatFileSize(attachment.size) : "Открыть"}</span>
                      </a>
                    ) : null}
                    <p className="mt-2 text-[10px] text-slate-500 dark:text-slate-400">{fmtDate(msg.created_at)}</p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={listEndRef} />
        </div>

        <div className="mt-4 border-t border-slate-200/80 pt-4 dark:border-white/10">
          {!canReply ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">Кейс закрыт. Для нового вопроса создайте новый кейс в поддержке.</p>
          ) : (
            <>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={4}
                placeholder="Напишите уточнение по этому кейсу..."
                className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
              />
              <label className="mt-3 block rounded-2xl border border-dashed border-slate-200/80 bg-slate-50/90 px-4 py-4 text-sm dark:border-white/10 dark:bg-white/[0.04]">
                <span className="block font-medium text-slate-900 dark:text-slate-50">Добавить вложение</span>
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
                {attachmentFile ? <p className="mt-2 text-[11px] uppercase tracking-[0.12em] text-slate-500">{formatFileSize(attachmentFile.size)}</p> : null}
              </label>
              <div className="mt-3 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void onSendReply()}
                  disabled={busy || !message.trim()}
                  className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
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
                  className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
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
