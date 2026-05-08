"use client";

import { AdminEmptyState, adminButtonClass, adminFieldClass, adminInsetPanelClass, adminPanelClass } from "@/components/admin/admin-shell";
import { adminTicket, adminTicketReply, adminTicketStatus, adminTickets, fetchTicketAttachmentBlob, uploadTicketAttachment, type TicketAttachmentInput, type TicketInfo, type TicketMessage } from "@/lib/api";
import { CheckCircle, Clock, Inbox, Loader2, MessageCircle, RefreshCw, Send } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fmtRuDate } from "../nav";

const STATUS_META: Record<string, { color: string; badge: string; icon: typeof Clock }> = {
  open: { color: "badge-info", badge: "Открыт", icon: Inbox },
  in_progress: { color: "badge-warning", badge: "В работе", icon: Clock },
  closed: { color: "badge-success", badge: "Закрыт", icon: CheckCircle },
};

function normalizeTicketStatus(ticket: Pick<TicketInfo, "status" | "status_title"> | null | undefined): keyof typeof STATUS_META {
  const raw = String(ticket?.status || "").toLowerCase().replace(/\s+/g, "_");
  if (raw in STATUS_META) return raw as keyof typeof STATUS_META;

  const title = String(ticket?.status_title || "").toLowerCase().replace(/\s+/g, "_");
  if (title === "в_работе") return "in_progress";
  if (title === "закрыт") return "closed";
  return "open";
}

type ParsedTicketAttachment = {
  kind: "image" | "video" | "file" | "link";
  url: string;
  name: string;
  size: number;
};
const MAX_TICKET_ATTACHMENT_BYTES = 20 * 1024 * 1024;

function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 Б";
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`;
}

function parseTicketAttachment(message: TicketMessage): ParsedTicketAttachment | null {
  try {
    const payload = JSON.parse(String(message.media_payload || "{}"));
    const rawUrl = String(payload?.url || "").trim();
    if (!rawUrl) return null;

    const rawKind = String(message.media_type || "").toLowerCase();
    const kind: ParsedTicketAttachment["kind"] =
      rawKind === "video" ? "video" : rawKind === "image" || rawKind === "photo" ? "image" : rawKind === "link" ? "link" : "file";
    const common: ParsedTicketAttachment = {
      kind,
      url: rawUrl,
      name: String(payload?.name || "Вложение"),
      size: Number(payload?.size || 0),
    };

    if (rawUrl.startsWith("/uploads/support/")) {
      return common;
    }

    const parsed = new URL(rawUrl);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    return { ...common, url: parsed.toString() };
  } catch {
    return null;
  }
}

function AdminTicketAttachmentView({ message }: { message: TicketMessage }) {
  const attachment = useMemo(() => parseTicketAttachment(message), [message]);
  const [objectUrl, setObjectUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const protectedUrl = Boolean(attachment?.url.startsWith("/uploads/support/"));

  useEffect(() => {
    if (!attachment || !protectedUrl) {
      setObjectUrl("");
      setLoading(false);
      setError("");
      return;
    }

    let active = true;
    let createdUrl = "";
    setObjectUrl("");
    setLoading(true);
    setError("");

    fetchTicketAttachmentBlob(attachment.url)
      .then((blob) => {
        if (!active) return;
        createdUrl = URL.createObjectURL(blob);
        setObjectUrl(createdUrl);
      })
      .catch(() => {
        if (active) setError("Не удалось открыть вложение");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [attachment, protectedUrl]);

  if (!attachment) return null;
  if (loading) {
    return <div className="mt-2 rounded-xl border border-slate-200/75 bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-400">Загружаем вложение...</div>;
  }
  if (error) {
    return <div className="mt-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-400/20 dark:bg-rose-500/10 dark:text-rose-200">{error}</div>;
  }

  const displayUrl = protectedUrl ? objectUrl : attachment.url;
  if (!displayUrl) return null;

  if (attachment.kind === "image") {
    return (
      <a href={displayUrl} target="_blank" rel="noreferrer" className="mt-2 block overflow-hidden rounded-xl border border-slate-200/75 bg-slate-100 dark:border-white/10 dark:bg-slate-950/60">
        <img src={displayUrl} alt={attachment.name || "Вложение"} className="max-h-56 w-full object-cover" />
      </a>
    );
  }

  if (attachment.kind === "video") {
    return <video src={displayUrl} controls className="mt-2 max-h-56 w-full rounded-xl border border-slate-200/75 bg-slate-950/60 dark:border-white/10" />;
  }

  return (
    <a
      href={displayUrl}
      target={protectedUrl ? undefined : "_blank"}
      rel={protectedUrl ? undefined : "noreferrer"}
      download={protectedUrl ? attachment.name || "attachment" : undefined}
      className="mt-2 flex items-center justify-between gap-3 rounded-xl border border-slate-200/75 bg-slate-50 px-3 py-2 text-xs dark:border-white/10 dark:bg-white/[0.04]"
    >
      <span className="truncate">{attachment.name || "Вложение"}</span>
      <span className="shrink-0 text-slate-500 dark:text-slate-400">{attachment.size ? formatFileSize(attachment.size) : "Открыть"}</span>
    </a>
  );
}

export default function AdminTicketsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [selectedId, setSelectedId] = useState<number>(0);
  const [reply, setReply] = useState("");
  const [replyAttachmentFile, setReplyAttachmentFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => tickets.find((ticket) => ticket.id === selectedId) || null, [selectedId, tickets]);

  const load = useCallback(async (): Promise<void> => {
    setError("");
    try {
      const rows = await adminTickets(statusFilter, 80);
      setTickets(rows);
      if (rows[0]?.id) {
        setSelectedId((prev) => (rows.some((ticket) => ticket.id === prev) ? prev : rows[0].id));
      } else {
        setSelectedId(0);
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить обращения."));
    }
  }, [statusFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;

    adminTicket(selectedId)
      .then((updated) => {
        if (!active) return;
        setTickets((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
        setError("");
      })
      .catch((err) => {
        if (!active) return;
        setError(String((err as { message?: string })?.message || err || "Не удалось загрузить историю обращения."));
      });

    return () => {
      active = false;
    };
  }, [selectedId]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [selected?.messages]);

  const sendReply = async (): Promise<void> => {
    if (!selected || !reply.trim()) return;
    if (replyAttachmentFile && replyAttachmentFile.size > MAX_TICKET_ATTACHMENT_BYTES) {
      setError("Файл больше 20 МБ. Уменьшите вложение или отправьте ответ без файла.");
      return;
    }
    setBusy(true);
    try {
      let attachment: TicketAttachmentInput | undefined;
      if (replyAttachmentFile) {
        const uploaded = await uploadTicketAttachment(replyAttachmentFile);
        attachment = uploaded.attachment;
      }
      const updated = await adminTicketReply(selected.id, reply.trim(), attachment);
      setReply("");
      setReplyAttachmentFile(null);
      setTickets((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось отправить ответ."));
    } finally {
      setBusy(false);
    }
  };

  const updateStatus = async (nextStatus: string): Promise<void> => {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = await adminTicketStatus(selected.id, nextStatus);
      setTickets((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось обновить статус обращения."));
    } finally {
      setBusy(false);
    }
  };

  const selectedStatus = normalizeTicketStatus(selected);

  return (
    <section className="grid gap-4 xl:grid-cols-[0.9fr,1.1fr]">
      <article className={adminPanelClass("neutral")}>
        <div className={adminInsetPanelClass}>
          <div className="mb-3 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <div className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200/80 bg-white text-slate-700 dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-100">
              <MessageCircle size={16} />
            </div>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className={`${adminFieldClass} flex-1`}>
              <option value="">Активные</option>
              <option value="open">Открыт</option>
              <option value="in_progress">В работе</option>
              <option value="closed">Закрыт</option>
            </select>
            <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => void load()}>
              <RefreshCw size={13} />
              Обновить
            </button>
          </div>
          <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
            Здесь собраны обращения пользователей. Слева очередь, справа переписка и быстрые смены статуса.
          </p>
        </div>

        {error ? <p className="mt-3 text-sm text-rose-500">{error}</p> : null}

        <div className="mt-3 max-h-[64vh] space-y-2 overflow-auto">
          {tickets.length === 0 ? (
            <AdminEmptyState title="Нет обращений" description="По текущему фильтру очередь пустая." />
          ) : null}
          {tickets.map((ticket) => {
            const meta = STATUS_META[normalizeTicketStatus(ticket)] || STATUS_META.open;
            return (
              <button
                key={ticket.id}
                type="button"
                onClick={() => setSelectedId(ticket.id)}
                className={`${adminInsetPanelClass} w-full text-left transition ${
                  selectedId === ticket.id ? "border-slate-950 bg-slate-950 text-white dark:border-white dark:bg-white dark:text-slate-950" : "hover:border-slate-300 hover:bg-white dark:hover:bg-white/[0.06]"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-bold">#{ticket.id}</span>
                  <span className={`badge ${meta.color}`}>{meta.badge}</span>
                </div>
                <p className="mt-1.5 text-sm font-medium">{ticket.subject || "Новое обращение"}</p>
                <p className={`mt-1 text-xs line-clamp-1 ${selectedId === ticket.id ? "text-white/70 dark:text-slate-700" : "text-slate-500 dark:text-slate-400"}`}>
                  {ticket.last_message_preview || "Нет сообщений"}
                </p>
              </button>
            );
          })}
        </div>
      </article>

      <article className={adminPanelClass("neutral")}>
        {!selected ? (
          <AdminEmptyState className="min-h-[420px]" title="Выберите обращение" description="Откройте тред из очереди, чтобы ответить, сменить статус или просмотреть всю переписку." />
        ) : (
          <>
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Выбранный тред</p>
                <h2 className="mt-1 font-display text-2xl font-semibold text-slate-950 dark:text-slate-50">Обращение #{selected.id}</h2>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Последнее обновление: {fmtRuDate(selected.updated_at)}</p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(STATUS_META).map(([key, meta]) => {
                  const Icon = meta.icon;
                  const isActive = selectedStatus === key;
                  return (
                    <button
                      key={key}
                      className={
                        isActive
                          ? "inline-flex min-h-8 items-center justify-center gap-2 rounded-lg bg-violet-600 px-2.5 text-[11px] font-semibold text-white shadow-lg shadow-violet-600/25 transition disabled:cursor-not-allowed disabled:opacity-55"
                          : adminButtonClass("ghost", "xs")
                      }
                      type="button"
                      onClick={() => void updateStatus(key)}
                      disabled={busy}
                    >
                      <Icon size={12} />
                      {meta.badge}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex max-h-[42vh] flex-col gap-2 overflow-auto rounded-[1rem] border border-slate-200/75 bg-slate-50/75 p-3 dark:border-white/10 dark:bg-white/[0.03]">
              {(selected.messages || []).length === 0 ? (
                <AdminEmptyState className="min-h-[180px]" title="Нет сообщений" description="В этом обращении пока нет переписки." />
              ) : null}
              {(selected.messages || []).map((message) => {
                const isAdmin = message.sender_role === "admin";
                return (
                  <div key={message.id} className={`flex ${isAdmin ? "justify-end" : "justify-start"}`}>
                    <div className={`chat-bubble text-sm ${isAdmin ? "chat-bubble-admin" : "chat-bubble-user"}`}>
                      <p className="mb-1 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                        {isAdmin ? "Оператор" : "Пользователь"}
                      </p>
                      <p className="whitespace-pre-line">{message.body}</p>
                      <AdminTicketAttachmentView message={message} />
                      <p className="mt-1.5 text-right text-[10px] text-slate-400">{fmtRuDate(message.created_at)}</p>
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEnd} />
            </div>

            <div className="mt-3 space-y-2">
              <textarea
                value={reply}
                onChange={(event) => setReply(event.target.value)}
                rows={3}
                placeholder="Напишите ответ пользователю простыми словами"
                className={`${adminFieldClass} min-h-[120px] resize-none py-3`}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && (event.metaKey || event.ctrlKey) && reply.trim()) {
                    void sendReply();
                  }
                }}
              />
              <label className="block rounded-xl border border-dashed border-slate-200/80 bg-slate-50/75 px-3 py-3 text-xs text-slate-600 dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-300">
                <span className="block font-semibold">Добавить вложение к ответу</span>
                <input
                  type="file"
                  accept="image/*,video/*,.pdf,.txt,.log,application/pdf,text/plain"
                  className="mt-2 block w-full cursor-pointer text-xs file:mr-3 file:rounded-lg file:border-0 file:bg-violet-600/10 file:px-3 file:py-1.5 file:font-semibold file:text-violet-700 dark:file:bg-violet-400/15 dark:file:text-violet-200"
                  onChange={(event) => setReplyAttachmentFile(event.target.files?.[0] ?? null)}
                />
                {replyAttachmentFile ? (
                  <div className="mt-2 flex items-center justify-between gap-3 rounded-lg bg-white px-3 py-2 dark:bg-white/[0.05]">
                    <span className="truncate">{replyAttachmentFile.name}</span>
                    <span className="shrink-0 text-slate-500 dark:text-slate-400">{formatFileSize(replyAttachmentFile.size)}</span>
                    <button type="button" onClick={() => setReplyAttachmentFile(null)} className="shrink-0 font-semibold text-rose-500">
                      Убрать
                    </button>
                  </div>
                ) : null}
              </label>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[10px] text-slate-400">Подсказка: можно отправить быстрее через Ctrl/⌘ + Enter</p>
                <button className={adminButtonClass("primary")} type="button" onClick={() => void sendReply()} disabled={busy || !reply.trim()}>
                  {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                  {busy ? "Отправка..." : "Отправить"}
                </button>
              </div>
            </div>
          </>
        )}
      </article>
    </section>
  );
}
