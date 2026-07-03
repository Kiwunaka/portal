"use client";

import { AdminEmptyState, adminButtonClass, adminFieldClass, adminInsetPanelClass, adminPanelClass } from "@/components/admin/admin-shell";
import { SupportMessageBody } from "@/components/support-message-body";
import { adminTicketReply, adminTicketStatus, adminTickets, type TicketInfo } from "@/lib/api";
import { fmtRuDate } from "@/lib/date-format";
import { SUPPORT_REPLY_MACROS, type SupportMacroIcon } from "@/lib/support-macros";
import {
  CheckCircle,
  Clock,
  CreditCard,
  Download,
  Gift,
  Inbox,
  LifeBuoy,
  Link2,
  ListChecks,
  Loader2,
  MessageCircle,
  Monitor,
  RefreshCw,
  Send,
  Smartphone,
  type LucideIcon,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

const STATUS_META: Record<string, { color: string; badge: string; icon: typeof Clock }> = {
  open: { color: "badge-info", badge: "Открыт", icon: Inbox },
  in_progress: { color: "badge-warning", badge: "В работе", icon: Clock },
  closed: { color: "badge-success", badge: "Закрыт", icon: CheckCircle },
};

const SUPPORT_MACRO_ICONS: Record<SupportMacroIcon, LucideIcon> = {
  credit_card: CreditCard,
  download: Download,
  gift: Gift,
  life_buoy: LifeBuoy,
  link: Link2,
  monitor: Monitor,
  smartphone: Smartphone,
  steps: ListChecks,
};

function normalizeTicketStatus(ticket: Pick<TicketInfo, "status" | "status_title"> | null | undefined): keyof typeof STATUS_META {
  const raw = String(ticket?.status || "").toLowerCase().replace(/\s+/g, "_");
  if (raw in STATUS_META) return raw as keyof typeof STATUS_META;

  const title = String(ticket?.status_title || "").toLowerCase().replace(/\s+/g, "_");
  if (title === "в_работе") return "in_progress";
  if (title === "закрыт") return "closed";
  return "open";
}

export default function AdminTicketsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [selectedId, setSelectedId] = useState<number>(0);
  const [reply, setReply] = useState("");
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
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [selected?.messages]);

  const sendReply = async (): Promise<void> => {
    if (!selected || !reply.trim()) return;
    setBusy(true);
    try {
      const updated = await adminTicketReply(selected.id, reply.trim());
      setReply("");
      setTickets((prev) => prev.map((row) => (row.id === updated.id ? updated : row)));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось отправить ответ."));
    } finally {
      setBusy(false);
    }
  };

  const insertReplyTemplate = (body: string): void => {
    setError("");
    setReply((current) => {
      const existing = current.trim();
      return existing ? `${existing}\n\n${body}` : body;
    });
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
            <div className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] text-[color:var(--atlas-text-soft)]">
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
          <p className="text-xs leading-5 text-[color:var(--atlas-text-soft)]">
            Здесь собраны обращения пользователей. Слева очередь, справа переписка и быстрые смены статуса.
          </p>
        </div>

        {error ? <p className="mt-3 text-sm text-[color:var(--atlas-status-danger-text)]">{error}</p> : null}

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
                  selectedId === ticket.id ? "border-[color:var(--atlas-text)] bg-[color:var(--atlas-text)] text-[color:var(--atlas-canvas)]" : "hover:border-[color:var(--atlas-border-strong)] hover:bg-[color:var(--atlas-surface)]"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-bold">#{ticket.id}</span>
                  <span className={`badge ${meta.color}`}>{meta.badge}</span>
                </div>
                <p className="mt-1.5 text-sm font-medium">{ticket.subject || "Новое обращение"}</p>
                <p className={`mt-1 text-xs line-clamp-1 ${selectedId === ticket.id ? "text-[color:color-mix(in_srgb,var(--atlas-canvas)_70%,transparent)]" : "text-[color:var(--atlas-text-soft)]"}`}>
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
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-text-soft)]">Выбранный тред</p>
                <h2 className="mt-1 font-display text-2xl font-semibold text-[color:var(--atlas-text)]">Обращение #{selected.id}</h2>
                <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">Последнее обновление: {fmtRuDate(selected.updated_at)}</p>
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

            <div className="flex max-h-[42vh] flex-col gap-2 overflow-auto rounded-[1rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-3">
              {(selected.messages || []).length === 0 ? (
                <AdminEmptyState className="min-h-[180px]" title="Нет сообщений" description="В этом обращении пока нет переписки." />
              ) : null}
              {(selected.messages || []).map((message) => {
                const isAdmin = message.sender_role === "admin";
                const isAssistant = message.sender_role === "assistant";
                const senderLabel = isAdmin ? "Оператор" : isAssistant ? "AI-помощник" : "Пользователь";
                return (
                  <div key={message.id} className={`flex ${isAdmin ? "justify-end" : "justify-start"}`}>
                    <div className={`chat-bubble text-sm ${isAdmin ? "chat-bubble-admin" : "chat-bubble-user"}`}>
                      <p className="mb-1 text-[10px] uppercase tracking-[0.12em] text-[color:var(--atlas-text-soft)]">
                        {senderLabel}
                      </p>
                      <SupportMessageBody body={message.body} />
                      <p className="mt-1.5 text-right text-[10px] text-[color:var(--atlas-text-muted)]">{fmtRuDate(message.created_at)}</p>
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEnd} />
            </div>

            <div className="mt-3 space-y-2">
              <div className="flex flex-wrap gap-2">
                {SUPPORT_REPLY_MACROS.map((template) => {
                  const Icon = SUPPORT_MACRO_ICONS[template.icon] || LifeBuoy;
                  return (
                    <button
                      key={template.id}
                      type="button"
                      onClick={() => insertReplyTemplate(template.body)}
                      className={adminButtonClass("ghost", "xs")}
                      title={`Вставить шаблон: ${template.label}`}
                    >
                      <Icon size={12} />
                      {template.label}
                    </button>
                  );
                })}
              </div>
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
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-[10px] text-[color:var(--atlas-text-muted)]">Подсказка: можно отправить быстрее через Ctrl/⌘ + Enter</p>
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
