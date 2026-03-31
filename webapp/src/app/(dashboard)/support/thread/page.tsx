"use client";

import { addTicketMessage, getTicket, resolveApiUrl, uploadTicketAttachment, type TicketAttachmentInput, type TicketInfo, type TicketMessage } from "@/lib/api";
import Link from "next/link";
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

  const canReply = useMemo(() => ticket && String(ticket.status || "").toLowerCase() !== "closed", [ticket]);

  const loadTicket = useCallback(async (): Promise<void> => {
    if (!ticketId) {
      setLoading(false);
      setError("Не передан ticket id");
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
      <main className="space-y-6">
        <section className="glass-card p-7">
          <h1 className="font-display text-3xl font-bold">Загрузка обращения...</h1>
        </section>
      </main>
    );
  }

  if (error || !ticket) {
    return (
      <main className="space-y-6">
        <section className="glass-card p-7">
          <h1 className="font-display text-3xl font-bold">Не удалось открыть обращение</h1>
          <p className="mt-3 text-sm text-rose-500">{error || "Обращение не найден"}</p>
          <div className="mt-4">
            <Link href="/support/" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]">
              Назад в службу заботы
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="space-y-5">
      <section className="glass-card p-5 md:p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-violet-600 dark:text-violet-300">#{ticket.id}</span>
              <h1 className="font-display text-2xl font-bold">{ticket.subject || "Обращение без темы"}</h1>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {statusTitle(ticket.status)} • обновлён {fmtDate(ticket.updated_at)}
            </p>
          </div>
          <Link href="/support/" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]">
            К списку
          </Link>
        </div>
      </section>

      <section className="glass-card p-4 md:p-5">
        <div className="max-h-[52vh] space-y-4 overflow-y-auto pr-1">
          {ticket.messages.length === 0 ? (
            <div className="rounded-xl bg-white/65 px-4 py-3 text-sm text-slate-500 dark:bg-white/10">История сообщений пока пустая.</div>
            ) : (
              ticket.messages.map((msg) => {
                const isAdmin = msg.sender_role === "admin";
                const attachment = ticketAttachment(msg);
                return (
                  <div key={msg.id} className={`flex ${isAdmin ? "justify-start" : "justify-end"}`}>
                    <div className={`max-w-[86%] rounded-2xl px-4 py-3 text-sm leading-6 ${isAdmin ? "bg-white/75 dark:bg-white/10" : "bg-violet-500/15 dark:bg-violet-500/25"}`}>
                      <p className="text-xs uppercase tracking-[0.12em] text-slate-500">{isAdmin ? "Оператор" : "Вы"}</p>
                      <p className="mt-1 whitespace-pre-line">{msg.body}</p>
                      {attachment?.kind === "image" ? (
                        <a href={attachment.url} target="_blank" rel="noreferrer" className="mt-3 block overflow-hidden rounded-2xl border border-white/40">
                          <img src={attachment.url} alt={attachment.name || "Вложение"} className="max-h-72 w-full object-cover" />
                        </a>
                      ) : null}
                      {attachment?.kind === "video" ? (
                        <video src={attachment.url} controls className="mt-3 max-h-72 w-full rounded-2xl border border-white/40 bg-slate-950/60" />
                      ) : null}
                      {attachment && attachment.kind !== "image" && attachment.kind !== "video" ? (
                        <a
                          href={attachment.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-3 flex items-center justify-between gap-3 rounded-2xl border border-white/40 bg-white/65 px-3 py-2 text-xs dark:bg-white/5"
                        >
                          <span className="truncate">{attachment.name || "Вложение"}</span>
                          <span className="shrink-0 text-slate-500">{attachment.size ? formatFileSize(attachment.size) : "Открыть"}</span>
                        </a>
                      ) : null}
                      <p className="mt-2 text-[10px] text-slate-500">{fmtDate(msg.created_at)}</p>
                    </div>
                  </div>
              );
            })
          )}
          <div ref={listEndRef} />
        </div>

        <div className="mt-4 border-t border-white/45 pt-4 dark:border-white/10">
          {!canReply ? (
            <p className="text-sm text-slate-500">Обращение закрыт. Для нового вопроса создайте новое обращение.</p>
          ) : (
            <>
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={4}
                placeholder="Напишите ответ..."
                className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
              />
              <label className="mt-3 block rounded-2xl border border-dashed border-violet-300/60 bg-white/70 px-4 py-4 text-sm dark:border-violet-500/35 dark:bg-slate-900/55">
                <span className="block font-medium">Добавить вложение</span>
                <span className="mt-1 block text-xs text-slate-500">Скриншот, видео, PDF или текстовый файл до 20 МБ.</span>
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
              <div className="mt-3 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void onSendReply()}
                  disabled={busy || !message.trim()}
                  className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
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
                  className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]"
                >
                  Очистить
                </button>
              </div>
              {replyError ? <p className="mt-2 text-xs text-rose-500">{replyError}</p> : null}
            </>
          )}
        </div>
      </section>
    </main>
  );
}
