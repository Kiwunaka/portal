"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Clock3, Download, Inbox, Paperclip, Send, UserRound } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { Badge, Button, Card, SectionTitle, type Tone } from "@/components/ui";
import { EmptyState } from "@/components/ui/states";
import type { ActionIntentRequest, AdminActionResult } from "@/lib/admin-api/actions";
import { downloadAdminTicketAttachment, type AdminTicket } from "@/lib/admin-api/support";

function dateText(value: string | null): string {
  if (!value) return "Нет данных";
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return "Нет данных";
  return new Date(parsed).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function statusLabel(status: string): string {
  if (status === "open") return "Открыт";
  if (status === "in_progress") return "В работе";
  if (status === "closed") return "Закрыт";
  return "Неизвестно";
}

function statusTone(status: string): Tone {
  if (status === "open") return "warning";
  if (status === "in_progress") return "info";
  if (status === "closed") return "success";
  return "neutral";
}

function senderLabel(role: string): string {
  if (role === "admin") return "Оператор";
  if (role === "assistant") return "ИИ-помощник";
  if (role === "user") return "Пользователь";
  return "Неизвестный отправитель";
}

function attachmentSize(sizeBytes: number | null): string | null {
  if (sizeBytes === null) return null;
  if (sizeBytes < 1024) return `${sizeBytes} Б`;
  if (sizeBytes < 1024 * 1024) return `${Math.ceil(sizeBytes / 1024)} КиБ`;
  return `${(sizeBytes / (1024 * 1024)).toLocaleString("ru-RU", { maximumFractionDigits: 1 })} МиБ`;
}

function attachmentFallbackName(type: string): string {
  if (type === "image") return "изображение";
  if (type === "video") return "видео";
  if (type === "audio") return "аудио";
  return "файл";
}

function safeDownloadName(name: string | null, type: string): string {
  const fallback = `вложение-${attachmentFallbackName(type)}`;
  return String(name || fallback).replace(/[\\/:*?"<>|\u0000-\u001f]/g, "_").trim().slice(0, 120) || "вложение";
}

function ticketRequest(ticketId: number, action: "reply" | "status", payload: Record<string, unknown>): ActionIntentRequest {
  return {
    action: `ticket.${action}`,
    target: { type: "ticket", id: String(ticketId) },
    payload,
    endpoint: `/api/admin/tickets/${ticketId}/${action}`,
  };
}

export function TicketDetail({ ticket, onRefresh }: { ticket: AdminTicket; onRefresh: () => void }) {
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [downloadState, setDownloadState] = useState<{ key: string | null; errorKey: string | null; error: string | null }>({ key: null, errorKey: null, error: null });
  const draft = drafts[ticket.id] || "";
  const messageCount = ticket.messages.length;

  const statusActions = useMemo(() => ([
    { value: "open", label: "Открыт", icon: Inbox },
    { value: "in_progress", label: "В работе", icon: Clock3 },
    { value: "closed", label: "Закрыт", icon: CheckCircle2 },
  ]), []);

  function openAction(nextRequest: ActionIntentRequest) {
    setRequest(nextRequest);
    setDialogOpen(true);
  }

  function handleResult(result: AdminActionResult) {
    if (request?.action === "ticket.reply" && result.status === "completed") {
      setDrafts((current) => ({ ...current, [ticket.id]: "" }));
    }
  }

  async function downloadAttachment(messageId: number, path: string, name: string | null, type: string) {
    const key = `${ticket.id}:${messageId}`;
    setDownloadState({ key, errorKey: null, error: null });
    try {
      const blob = await downloadAdminTicketAttachment(path);
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = safeDownloadName(name, type);
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      setDownloadState({ key: null, errorKey: null, error: null });
    } catch {
      setDownloadState({ key: null, errorKey: key, error: "Не удалось скачать вложение. Проверьте доступ и повторите попытку." });
    }
  }

  return (
    <>
      <div className="space-y-3">
        <Card>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Тикет #{ticket.id}</h2>
              <p className="mt-1 text-sm text-[color:var(--atlas-text-soft)]">{ticket.subject}</p>
              <a href={`/users?selected=${ticket.userTgId}&tab=tickets`} className="mt-2 inline-flex items-center gap-2 text-xs font-semibold text-[color:var(--atlas-primary)] hover:underline"><UserRound size={14} /> Пользователь {ticket.userTgId}</a>
            </div>
            <div className="text-right"><Badge tone={statusTone(ticket.status)}>{statusLabel(ticket.status)}</Badge><p className="mt-2 text-xs text-[color:var(--atlas-text-muted)]">Обновлён {dateText(ticket.updatedAt)}</p></div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Изменить статус тикета">
            {statusActions.map((item) => {
              const Icon = item.icon;
              const active = ticket.status === item.value;
              return <Button key={item.value} tone={active ? "primary" : "secondary"} disabled={active} onClick={() => openAction(ticketRequest(ticket.id, "status", { status: item.value }))}><Icon size={14} /> {item.label}</Button>;
            })}
          </div>
        </Card>

        <Card>
          <SectionTitle title="Переписка" description={`${messageCount} сообщений. Полная переписка загружена отдельным запросом только после выбора тикета.`} />
          {ticket.messages.length ? (
            <div className="ops-scrollbar flex max-h-[48vh] flex-col gap-2 overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3" aria-label="Сообщения тикета">
              {ticket.messages.map((message) => {
                const operator = message.senderRole === "admin" || message.senderRole === "assistant";
                const attachment = message.attachment;
                const downloadUrl = attachment?.downloadUrl || null;
                return (
                  <article key={message.id} className={`max-w-[88%] rounded-[var(--pokrov-radius-card)] border p-3 ${operator ? "ml-auto border-[color:var(--atlas-status-info-line)] bg-[color:var(--atlas-status-info-bg)]" : "mr-auto border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]"}`}>
                    <div className="flex flex-wrap items-center justify-between gap-3 text-[11px]"><strong>{senderLabel(message.senderRole)}</strong><time dateTime={message.createdAt || undefined} className="text-[color:var(--atlas-text-muted)]">{dateText(message.createdAt)}</time></div>
                    <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6">{message.body}</p>
                    {attachment ? (
                      <div className="mt-3 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-2 text-xs">
                        <div className="flex items-center gap-2 font-semibold"><Paperclip size={14} /> Вложение: {attachment.name || attachmentFallbackName(attachment.type)}</div>
                        <p className="mt-1 text-[11px] text-[color:var(--atlas-text-muted)]">{[attachment.contentType, attachmentSize(attachment.sizeBytes)].filter(Boolean).join(" · ") || "Тип и размер не указаны"}</p>
                        {downloadUrl ? (
                          <Button tone="secondary" className="mt-2" disabled={downloadState.key === `${ticket.id}:${message.id}`} onClick={() => void downloadAttachment(message.id, downloadUrl, attachment.name, attachment.type)}><Download size={13} /> {downloadState.key === `${ticket.id}:${message.id}` ? "Скачиваем…" : "Скачать вложение"}</Button>
                        ) : <p className="mt-2 text-[11px] text-[color:var(--atlas-status-warning-text)]">Скачивание этого вложения в админке недоступно.</p>}
                        {downloadState.errorKey === `${ticket.id}:${message.id}` ? <p className="mt-2 text-[11px] text-[color:var(--atlas-status-danger-text)]">{downloadState.error}</p> : null}
                      </div>
                    ) : null}
                  </article>
                );
              })}
            </div>
          ) : <EmptyState description="В тикете пока нет сообщений." className="min-h-28" />}
        </Card>

        <Card>
          <SectionTitle title="Ответ пользователю" description="Черновик останется на месте при известной ошибке или неясном итоге. Он очищается только после подтверждённой отправки." />
          <label className="block text-xs font-semibold text-[color:var(--atlas-text-soft)]">
            Текст ответа
            <textarea
              value={draft}
              onChange={(event) => setDrafts((current) => ({ ...current, [ticket.id]: event.target.value }))}
              rows={5}
              maxLength={2000}
              placeholder="Напишите ответ простыми словами"
              className="mt-1 w-full resize-y rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
              onKeyDown={(event) => {
                if (event.key === "Enter" && (event.ctrlKey || event.metaKey) && draft.trim()) {
                  event.preventDefault();
                  openAction(ticketRequest(ticket.id, "reply", { body: draft.trim(), media_type: null, media_file_id: null, media_payload: null }));
                }
              }}
            />
          </label>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            <span className="text-[11px] text-[color:var(--atlas-text-muted)]">{draft.length} / 2000 · Ctrl/⌘ + Enter</span>
            <Button tone="primary" disabled={!draft.trim()} onClick={() => openAction(ticketRequest(ticket.id, "reply", { body: draft.trim(), media_type: null, media_file_id: null, media_payload: null }))}><Send size={15} /> Подготовить ответ</Button>
          </div>
        </Card>
      </div>

      <ActionIntentDialog
        open={dialogOpen}
        request={request}
        onOpenChange={(nextOpen) => {
          setDialogOpen(nextOpen);
          if (!nextOpen) setRequest(null);
        }}
        onKnownOutcome={onRefresh}
        onCheckState={onRefresh}
        onResult={handleResult}
      />
    </>
  );
}
