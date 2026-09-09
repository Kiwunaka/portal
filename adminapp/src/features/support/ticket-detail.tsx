"use client";

import { useCallback, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, Download, Inbox, Link2, MessageSquareText, Paperclip, Send, ShieldCheck, UserCheck, UserRound } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { Badge, Button, Card, SectionTitle, type Tone } from "@/components/ui";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import type { ActionIntentRequest, AdminActionResult } from "@/lib/admin-api/actions";
import { downloadAdminTicketAttachment, downloadSupportBundleCiphertext, fetchSupportAttempts, fetchSupportKnownIssues, fetchSupportMacros, type AdminTicket, type SupportAttemptEvent } from "@/lib/admin-api/support";
import { useRouteResource } from "@/lib/use-route-resource";

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

function ticketRequest(ticketId: number, action: "reply" | "status" | "note", payload: Record<string, unknown>): ActionIntentRequest {
  return {
    action: `ticket.${action}`,
    target: { type: "ticket", id: String(ticketId) },
    payload,
    endpoint: `/api/admin/tickets/${ticketId}/${action}`,
    workspace: action === "note" ? "support" : undefined,
  };
}

function supportRequest(ticketId: number, action: "ticket.claim" | "ticket.assign" | "ticket.update", payload: Record<string, unknown>): ActionIntentRequest {
  return { action, target: { type: "ticket", id: String(ticketId) }, payload, endpoint: "", workspace: "support" };
}

function diagnosticFact(events: SupportAttemptEvent[], needles: string[]): SupportAttemptEvent | null {
  return [...events].reverse().find((event) => {
    const haystack = `${event.eventName} ${event.subsystem || ""} ${event.stage || ""}`.toLowerCase();
    return needles.some((needle) => haystack.includes(needle));
  }) || null;
}

function diagnosticTone(result: string | null): Tone {
  if (result === "success" || result === "ok" || result === "pass") return "success";
  if (result === "failure" || result === "failed" || result === "error") return "danger";
  if (result) return "warning";
  return "neutral";
}

export function TicketDetail({ ticket, permissions, onRefresh }: { ticket: AdminTicket; permissions: string[]; onRefresh: () => void }) {
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [noteDrafts, setNoteDrafts] = useState<Record<number, string>>({});
  const [macroCodes, setMacroCodes] = useState<Record<number, string | null>>({});
  const [assignee, setAssignee] = useState("");
  const [assignedTeam, setAssignedTeam] = useState(ticket.assignedTeam || "support");
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [downloadState, setDownloadState] = useState<{ key: string | null; errorKey: string | null; error: string | null }>({ key: null, errorKey: null, error: null });
  const [bundleReasons, setBundleReasons] = useState<Record<string, "" | "customer_case" | "incident_review" | "release_validation" | "security_review">>({});
  const [bundleDownloadState, setBundleDownloadState] = useState<{ key: string | null; errorKey: string | null; error: string | null }>({ key: null, errorKey: null, error: null });
  const draft = drafts[ticket.id] || "";
  const noteDraft = noteDrafts[ticket.id] || "";
  const selectedMacro = macroCodes[ticket.id] || null;
  const messageCount = ticket.messages.length;
  const loadMacros = useCallback((signal: AbortSignal) => fetchSupportMacros({ signal }), []);
  const loadAttempts = useCallback((signal: AbortSignal) => fetchSupportAttempts({ ticketId: ticket.id, attemptRef: ticket.attemptRef }, { signal }), [ticket.attemptRef, ticket.id]);
  const macros = useRouteResource("support:macros", loadMacros, { enabled: true });
  const attempts = useRouteResource(`support:attempts:${ticket.id}:${ticket.attemptRef || "none"}`, loadAttempts, { enabled: true });
  const issueScope = ticket.supportBundles.find((bundle) => Boolean(bundle.lastErrorCode)) || null;
  const issueErrorCode = issueScope?.lastErrorCode || null;
  const issueAppVersion = issueScope?.appVersion || null;
  const issueBuildNumber = issueScope?.buildNumber || null;
  const issuePlatform = issueScope?.platform || null;
  const loadKnownIssues = useCallback((signal: AbortSignal) => issueErrorCode ? fetchSupportKnownIssues({ errorCode: issueErrorCode, appVersion: issueAppVersion, buildNumber: issueBuildNumber, platform: issuePlatform }, { signal }) : Promise.resolve([]), [issueAppVersion, issueBuildNumber, issueErrorCode, issuePlatform]);
  const knownIssues = useRouteResource(JSON.stringify(["support:known-issues", ticket.id, issueErrorCode, issueAppVersion, issueBuildNumber, issuePlatform]), loadKnownIssues, { enabled: Boolean(issueErrorCode) });
  const canReadSensitiveBundles = permissions.includes("support.sensitive.read");
  const linkedAttemptRef = ticket.attemptRef || attempts.data?.linkedAttemptRef || null;
  const selectedAttempt = linkedAttemptRef
    ? attempts.data?.selected?.attemptRef === linkedAttemptRef ? attempts.data.selected : null
    : attempts.data?.attempts[0] || null;
  const attemptBuild = selectedAttempt?.events.at(-1);
  const diagnosticFacts = selectedAttempt ? [
    { label: "Разрешения", event: diagnosticFact(selectedAttempt.events, ["permission"]) },
    { label: "Core", event: diagnosticFact(selectedAttempt.events, ["core", "runtime"]) },
    { label: "TUN", event: diagnosticFact(selectedAttempt.events, ["tun"]) },
    { label: "DNS", event: diagnosticFact(selectedAttempt.events, ["dns"]) },
    { label: "Egress", event: diagnosticFact(selectedAttempt.events, ["egress"]) },
  ] : [];
  const caseTimeline = useMemo(() => [
    { key: "created", label: "Обращение создано", at: ticket.createdAt },
    ...ticket.messages.map((message) => ({ key: `message-${message.id}`, label: message.visibility === "internal" ? "Внутренняя заметка" : `${senderLabel(message.senderRole)}: сообщение`, at: message.createdAt })),
    { key: "updated", label: `Состояние: ${statusLabel(ticket.status)}`, at: ticket.updatedAt },
    ...(ticket.closedAt ? [{ key: "closed", label: "Обращение закрыто", at: ticket.closedAt }] : []),
  ].filter((item) => item.at).sort((left, right) => Date.parse(String(left.at)) - Date.parse(String(right.at))), [ticket.closedAt, ticket.createdAt, ticket.messages, ticket.status, ticket.updatedAt]);

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
      setMacroCodes((current) => ({ ...current, [ticket.id]: null }));
    }
    if (request?.action === "ticket.note" && result.status === "completed") {
      setNoteDrafts((current) => ({ ...current, [ticket.id]: "" }));
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

  async function downloadBundle(bundleRef: string) {
    const reason = bundleReasons[bundleRef] || "customer_case";
    setBundleDownloadState({ key: bundleRef, errorKey: null, error: null });
    try {
      const blob = await downloadSupportBundleCiphertext(ticket.id, bundleRef, reason);
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = `pokrov-support-${bundleRef}.bin`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      setBundleDownloadState({ key: null, errorKey: null, error: null });
      onRefresh();
    } catch {
      setBundleDownloadState({ key: null, errorKey: bundleRef, error: "Доступ отклонён. Нужны L2/SRE/Security, свежий step-up и обязательная причина." });
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
            <div className="text-right"><div className="flex flex-wrap justify-end gap-2"><Badge tone={statusTone(ticket.status)}>{statusLabel(ticket.status)}</Badge><Badge tone={ticket.slaStatus === "breached" ? "danger" : ticket.slaStatus === "at_risk" ? "warning" : "neutral"}>SLA: {ticket.slaStatus === "breached" ? "нарушен" : ticket.slaStatus === "at_risk" ? "под риском" : ticket.slaStatus === "ok" ? "в норме" : "остановлен"}</Badge>{ticket.escalatedAt ? <Badge tone="danger">Эскалация</Badge> : null}</div><p className="mt-2 text-xs text-[color:var(--atlas-text-muted)]">Обновлён {dateText(ticket.updatedAt)} · версия {ticket.version}</p></div>
          </div>

          <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-2"><dt className="text-[color:var(--atlas-text-muted)]">Очередь</dt><dd className="mt-1 font-semibold">{ticket.queue}</dd></div>
            <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-2"><dt className="text-[color:var(--atlas-text-muted)]">Назначение</dt><dd className="mt-1 font-semibold">{ticket.assignedAdminTgId || "Не назначен"}{ticket.assignedTeam ? ` · ${ticket.assignedTeam}` : ""}</dd></div>
            <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-2"><dt className="text-[color:var(--atlas-text-muted)]">Ожидаем</dt><dd className="mt-1 font-semibold">{ticket.waitingOn || "Никого"}</dd></div>
            <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-2"><dt className="text-[color:var(--atlas-text-muted)]">SLA до</dt><dd className="mt-1 font-semibold">{dateText(ticket.slaDueAt)}</dd></div>
          </dl>

          <div className="mt-4 flex flex-wrap gap-2" role="group" aria-label="Изменить статус тикета">
            {statusActions.map((item) => {
              const Icon = item.icon;
              const active = ticket.status === item.value;
              return <Button key={item.value} tone={active ? "primary" : "secondary"} disabled={active} onClick={() => openAction(ticketRequest(ticket.id, "status", { status: item.value, expected_version: ticket.version }))}><Icon size={14} /> {item.label}</Button>;
            })}
            <Button tone="secondary" disabled={ticket.assignedAdminTgId !== null} onClick={() => openAction(supportRequest(ticket.id, "ticket.claim", { expected_version: ticket.version }))}><UserCheck size={14} /> Взять в работу</Button>
            <Button tone={ticket.escalatedAt ? "secondary" : "danger"} onClick={() => openAction(supportRequest(ticket.id, "ticket.update", { expected_version: ticket.version, escalated: !ticket.escalatedAt }))}><AlertTriangle size={14} /> {ticket.escalatedAt ? "Снять эскалацию" : "Эскалировать"}</Button>
          </div>

          <div className="mt-3 grid gap-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
            <input aria-label="Telegram ID назначаемого оператора" value={assignee} inputMode="numeric" onChange={(event) => setAssignee(event.target.value.replace(/\D/g, ""))} placeholder="TG ID оператора" className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm" />
            <input aria-label="Команда поддержки" value={assignedTeam} maxLength={48} onChange={(event) => setAssignedTeam(event.target.value)} placeholder="Команда" className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm" />
            <Button tone="secondary" disabled={!assignee.trim()} onClick={() => openAction(supportRequest(ticket.id, "ticket.assign", { expected_version: ticket.version, assignee_admin_tg_id: Number(assignee), assigned_team: assignedTeam.trim() || null }))}>Назначить</Button>
          </div>
        </Card>

        <Card>
          <SectionTitle title="Timeline обращения" description="Создание, сообщения, внутренние заметки и смена состояния собраны в один хронологический ряд. Пакет диагностики здесь не раскрывается." />
          <ol className="space-y-2" aria-label="Timeline обращения">
            {caseTimeline.map((item) => <li key={item.key} className="grid grid-cols-[auto_minmax(0,1fr)] gap-3 text-xs"><span className="mt-1 h-2 w-2 rounded-full bg-[color:var(--atlas-primary)]" aria-hidden="true" /><div><strong>{item.label}</strong><p className="mt-1 text-[color:var(--atlas-text-muted)]">{dateText(item.at)}</p></div></li>)}
          </ol>
        </Card>

        <Card>
          <SectionTitle title="Переписка" description={`${messageCount} сообщений. Полная переписка загружена отдельным запросом только после выбора тикета.`} />
          {ticket.messages.length ? (
            <div className="ops-scrollbar flex max-h-[48vh] flex-col gap-2 overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3" aria-label="Сообщения тикета">
              {ticket.messages.map((message) => {
                const operator = message.senderRole === "admin" || message.senderRole === "assistant";
                const internal = message.visibility === "internal";
                const attachment = message.attachment;
                const downloadUrl = attachment?.downloadUrl || null;
                return (
                  <article key={message.id} className={`max-w-[88%] rounded-[var(--pokrov-radius-card)] border p-3 ${internal ? "ml-auto border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)]" : operator ? "ml-auto border-[color:var(--atlas-status-info-line)] bg-[color:var(--atlas-status-info-bg)]" : "mr-auto border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)]"}`}>
                    <div className="flex flex-wrap items-center justify-between gap-3 text-[11px]"><strong>{internal ? "Внутренняя заметка" : senderLabel(message.senderRole)}{message.macroCode ? ` · ${message.macroCode}` : ""}</strong><time dateTime={message.createdAt || undefined} className="text-[color:var(--atlas-text-muted)]">{dateText(message.createdAt)}</time></div>
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
          {macros.data?.length ? <div className="mb-3 flex flex-wrap gap-2" aria-label="Макросы ответа">{macros.data.map((macro) => <Button key={macro.code} tone={selectedMacro === macro.code ? "primary" : "secondary"} onClick={() => { setDrafts((current) => ({ ...current, [ticket.id]: macro.body })); setMacroCodes((current) => ({ ...current, [ticket.id]: macro.code })); }}>{macro.title}</Button>)}</div> : null}
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
                  openAction(ticketRequest(ticket.id, "reply", { body: draft.trim(), media_type: null, media_file_id: null, media_payload: null, expected_version: ticket.version, macro_code: selectedMacro }));
                }
              }}
            />
          </label>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
            <span className="text-[11px] text-[color:var(--atlas-text-muted)]">{draft.length} / 2000 · Ctrl/⌘ + Enter</span>
            <Button tone="primary" disabled={!draft.trim()} onClick={() => openAction(ticketRequest(ticket.id, "reply", { body: draft.trim(), media_type: null, media_file_id: null, media_payload: null, expected_version: ticket.version, macro_code: selectedMacro }))}><Send size={15} /> Подготовить ответ</Button>
          </div>
        </Card>

        <Card>
          <SectionTitle title="Внутренняя заметка" description="Видна только операторам, не возвращается в пользовательские API и не отправляется в Telegram." />
          <textarea value={noteDraft} onChange={(event) => setNoteDrafts((current) => ({ ...current, [ticket.id]: event.target.value }))} rows={4} maxLength={2000} placeholder="Зафиксируйте ход разбора без секретов и сырых сетевых данных" className="w-full resize-y rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-sm" />
          <div className="mt-2 flex justify-end"><Button tone="secondary" disabled={!noteDraft.trim()} onClick={() => openAction(ticketRequest(ticket.id, "note", { body: noteDraft.trim(), expected_version: ticket.version, macro_code: null }))}><MessageSquareText size={15} /> Добавить заметку</Button></div>
        </Card>

        <Card>
          <SectionTitle title="Диагностика и попытки" description="Только серверный allowlist: версии, этапы, коды и opaque refs. Raw meta, IP, URL, токены и конфигурации исключены." />
          {attempts.loading && !attempts.data ? <LoadingState title="Группируем попытки" description="События связываются по opaque installation/session/attempt refs." /> : null}
          {attempts.error ? <ErrorState title="Диагностика недоступна" description="Для этого источника нужны права L2 или повторный запрос." /> : null}
          {attempts.data && !attempts.loading && linkedAttemptRef && !selectedAttempt ? <EmptyState description="Связанная попытка отсутствует в доступных данных." className="min-h-20" /> : null}
          {selectedAttempt ? <div className="mb-3 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3"><div className="flex flex-wrap items-center justify-between gap-2 text-xs"><div><strong>{linkedAttemptRef ? "Сводка связанной попытки" : "Последняя попытка пользователя · не связана с обращением"}</strong><p className="mt-1 text-[color:var(--atlas-text-muted)]">{[attemptBuild?.platform, attemptBuild?.appVersion, attemptBuild?.buildNumber].filter(Boolean).join(" · ") || "Версия не указана"}</p></div><code className="text-[11px]">{selectedAttempt.attemptRef}</code></div><dl className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">{diagnosticFacts.map((fact) => <div key={fact.label} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-2 text-xs"><dt className="text-[color:var(--atlas-text-muted)]">{fact.label}</dt><dd className="mt-1 flex flex-wrap items-center gap-2"><Badge tone={diagnosticTone(fact.event?.result || null)}>{fact.event?.result || "Нет сигнала"}</Badge>{fact.event?.errorCode ? <code>{fact.event.errorCode}</code> : null}</dd></div>)}</dl></div> : null}
          {attempts.data ? <div className="space-y-2">{attempts.data.attempts.slice(0, 8).map((attempt) => <article key={attempt.attemptRef} className={`rounded-[var(--pokrov-radius-control)] border p-3 text-xs ${ticket.attemptRef === attempt.attemptRef ? "border-[color:var(--atlas-primary)] bg-[color:var(--pokrov-nav-active-bg)]" : "border-[color:var(--atlas-border)]"}`}><div className="flex flex-wrap items-center justify-between gap-2"><code className="font-mono text-[11px]">{attempt.attemptRef}</code><Badge tone={diagnosticTone(attempt.outcome)}>{attempt.outcome || "Нет результата"}</Badge></div><p className="mt-2 text-[color:var(--atlas-text-muted)]">{attempt.eventCount} событий · {dateText(attempt.endedAt)}</p><Button tone="secondary" className="mt-2" disabled={ticket.attemptRef === attempt.attemptRef} onClick={() => openAction(supportRequest(ticket.id, "ticket.update", { expected_version: ticket.version, attempt_ref: attempt.attemptRef }))}><Link2 size={13} /> {ticket.attemptRef === attempt.attemptRef ? "Связана" : "Связать с тикетом"}</Button></article>)}{attempts.data.attempts.length === 0 ? <EmptyState description="Для пользователя нет коррелируемых клиентских попыток." className="min-h-20" /> : null}</div> : null}
        </Card>

        <Card>
          <SectionTitle title="Известные проблемы и действия" description="Матчинг выполняется по error code, версии, build и платформе. Оператор видит только безопасное описание и связанные записи." />
          {knownIssues.loading && !knownIssues.data ? <LoadingState title="Сверяем known issues" description="Реестр привязан к версии клиента." /> : null}
          {knownIssues.error ? <ErrorState title="Known issues недоступны" description="Ручная догадка не считается подтверждённым решением." /> : null}
          {knownIssues.data?.length ? <div className="space-y-2">{knownIssues.data.map((issue) => <article key={`${issue.candidateLabel}:${issue.issueCode}`} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] p-3 text-xs"><div className="flex flex-wrap items-center justify-between gap-2"><strong>{issue.title}</strong><div className="flex gap-2"><Badge tone="warning">{issue.issueCode}</Badge><Badge tone="neutral">{issue.errorCode}</Badge></div></div><p className="mt-2 leading-5">{issue.safeSummary}</p><div className="mt-3 flex flex-wrap gap-2">{issue.incidentRef ? <a className="inline-flex items-center gap-1 font-semibold text-[color:var(--atlas-primary)] hover:underline" href={`/incidents?selected=${encodeURIComponent(issue.incidentRef)}`}><Link2 size={13} /> Открыть инцидент</a> : null}{issue.releaseRef ? <a className="inline-flex items-center gap-1 font-semibold text-[color:var(--atlas-primary)] hover:underline" href={`/release?selected=${encodeURIComponent(issue.releaseRef)}`}><Link2 size={13} /> Открыть релиз</a> : null}</div></article>)}</div> : knownIssues.data ? <EmptyState description="Для текущего кода и версии известная проблема не зарегистрирована." className="min-h-20" /> : null}
        </Card>

        <Card>
          <SectionTitle title="Пакеты поддержки" description="Показываются только безопасная сводка, срок хранения и агрегат аудита доступа. Содержимое требует отдельного grant." />
          {ticket.supportBundles.length ? <div className="space-y-2">{ticket.supportBundles.map((bundle) => <article key={bundle.bundleRef} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3 text-xs"><div className="flex flex-wrap items-center justify-between gap-2"><code>{bundle.bundleRef}</code><Badge tone={bundle.status === "validated" ? "success" : "neutral"}>{bundle.status}</Badge></div><p className="mt-2">{[bundle.platform, bundle.appVersion, bundle.buildNumber].filter(Boolean).join(" · ") || "Клиент не указан"}</p><p className="mt-1 text-[color:var(--atlas-text-muted)]">TTL до {dateText(bundle.expiresAt)} · доступов {bundle.accessCount} · retention hold: {bundle.retentionHold ? "да" : "нет"}</p>{canReadSensitiveBundles ? <div className="mt-3 flex flex-wrap items-end gap-2 border-t border-[color:var(--atlas-border)] pt-3"><label className="grid gap-1"><span className="font-semibold">Причина доступа</span><select aria-label={`Причина доступа к ${bundle.bundleRef}`} value={bundleReasons[bundle.bundleRef] || "customer_case"} onChange={(event) => setBundleReasons((current) => ({ ...current, [bundle.bundleRef]: event.target.value as "customer_case" | "incident_review" | "release_validation" | "security_review" }))} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="customer_case">Обращение клиента</option><option value="incident_review">Разбор инцидента</option><option value="release_validation">Проверка релиза</option><option value="security_review">Проверка безопасности</option></select></label><Button tone="secondary" disabled={bundleDownloadState.key === bundle.bundleRef} onClick={() => void downloadBundle(bundle.bundleRef)}><ShieldCheck size={14} /> {bundleDownloadState.key === bundle.bundleRef ? "Выдаём grant…" : "Скачать шифротекст"}</Button>{bundleDownloadState.errorKey === bundle.bundleRef ? <p className="w-full text-[color:var(--atlas-danger)]">{bundleDownloadState.error || "Grant не выдан или уже использован. Повторите с обоснованием."}</p> : null}</div> : <p className="mt-3 flex items-center gap-2 border-t border-[color:var(--atlas-border)] pt-3 text-[color:var(--atlas-text-muted)]"><ShieldCheck size={14} /> L1 видит только безопасную сводку; скачивание и содержимое скрыты.</p>}</article>)}</div> : <EmptyState description="Пакеты поддержки к тикету не привязаны." className="min-h-20" />}
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
