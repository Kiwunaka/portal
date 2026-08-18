"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { FileText, Gauge, Radio, RefreshCw, Send, ShieldAlert, UsersRound } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, MetricCell, MetricStrip, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest, AdminActionResult, PreparedActionIntent } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import {
  fetchActionIntentStatus,
  fetchBroadcastDelivery,
  type BroadcastDeliverySummary,
} from "@/lib/admin-api/control";

type BroadcastSegment = "all_active" | "paid" | "trial" | "pending" | "expired" | "custom";
type BroadcastDraft = {
  segment: BroadcastSegment;
  limit: string;
  customIds: string;
  text: string;
};

const STORAGE_KEY = "pokrov_admin_broadcast_draft_v1";
const EMPTY_DRAFT: BroadcastDraft = { segment: "all_active", limit: "500", customIds: "", text: "" };
const SEGMENTS: BroadcastSegment[] = ["all_active", "paid", "trial", "pending", "expired", "custom"];
const SEGMENT_LABELS: Record<BroadcastSegment, string> = {
  all_active: "Все активные",
  paid: "Платные",
  trial: "Пробный период",
  pending: "Ожидают доступа",
  expired: "Истёкшие",
  custom: "Список ID",
};

function loadDraft(): BroadcastDraft {
  if (typeof window === "undefined") return EMPTY_DRAFT;
  try {
    const parsed = JSON.parse(String(window.sessionStorage.getItem(STORAGE_KEY) || "{}")) as Partial<BroadcastDraft>;
    return {
      segment: SEGMENTS.includes(parsed.segment as BroadcastSegment) ? parsed.segment as BroadcastSegment : EMPTY_DRAFT.segment,
      limit: typeof parsed.limit === "string" ? parsed.limit : EMPTY_DRAFT.limit,
      customIds: typeof parsed.customIds === "string" ? parsed.customIds : "",
      text: typeof parsed.text === "string" ? parsed.text.slice(0, 4000) : "",
    };
  } catch {
    return EMPTY_DRAFT;
  }
}

function parseCustomIds(value: string): number[] | null {
  const tokens = value.split(/[\s,;]+/).map((item) => item.trim()).filter(Boolean);
  if (!tokens.length) return [];
  if (tokens.some((item) => !/^\d+$/.test(item))) return null;
  const ids = tokens.map(Number);
  if (ids.some((item) => !Number.isSafeInteger(item) || item <= 0)) return null;
  return [...new Set(ids)].sort((left, right) => left - right);
}

function resultCount(result: AdminActionResult | null, key: "attempted" | "sent" | "failed"): number | null {
  if (!result) return null;
  const direct = (result as AdminActionResult & Record<string, unknown>)[key];
  const nested = result.result?.[key];
  const value = typeof direct === "number" ? direct : nested;
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

const DELIVERY_REASON_LABELS: Record<string, string> = {
  blocked: "Бот заблокирован",
  bot_not_started_or_chat_not_found: "Бот не запущен или чат не найден",
  account_deactivated: "Аккаунт Telegram удалён",
  rate_limited: "Лимит Telegram",
  transient_provider: "Временный сбой Telegram",
  delivery_uncertain: "Итог доставки неизвестен — не повторять",
  internal: "Внутренняя ошибка",
  unknown_safe: "Неизвестная безопасная категория",
};

function resultTone(result: AdminActionResult): "success" | "warning" | "danger" {
  if (result.status === "completed") return "success";
  if (result.status === "uncertain" || result.status === "executing") return "warning";
  return "danger";
}

function isDefinitiveStoredOutcome(result: AdminActionResult): boolean {
  return result.status === "completed" || result.status === "failed";
}

export function BroadcastPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [draft, setDraft] = useState<BroadcastDraft>(loadDraft);
  const [formError, setFormError] = useState("");
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [lastResult, setLastResult] = useState<AdminActionResult | null>(null);
  const [statusIntentId, setStatusIntentId] = useState<string | null>(null);
  const [statusError, setStatusError] = useState("");
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [outcomeUncertain, setOutcomeUncertain] = useState(false);
  const [delivery, setDelivery] = useState<BroadcastDeliverySummary | null>(null);
  const clearStorageOnEmptyRef = useRef(false);

  useEffect(() => {
    try {
      if (clearStorageOnEmptyRef.current && draft.text === "" && draft.customIds === "") {
        window.sessionStorage.removeItem(STORAGE_KEY);
        clearStorageOnEmptyRef.current = false;
        return;
      }
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
    } catch {
      // The in-memory draft remains available when storage is blocked.
    }
  }, [draft]);

  useEffect(() => {
    onShellStatus?.({
      api: statusError ? "degraded" : lastResult ? lastResult.status === "completed" ? "ok" : "degraded" : "missing",
      session: "missing",
      oldestRequiredSourceAt: null,
    });
  }, [lastResult, onShellStatus, statusError]);

  const clearConfirmedDraft = useCallback(() => {
    clearStorageOnEmptyRef.current = true;
    try {
      window.sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // State still clears after a confirmed outcome.
    }
    setDraft(EMPTY_DRAFT);
  }, []);

  const handleResult = useCallback((result: AdminActionResult) => {
    setLastResult(result);
    setStatusIntentId(result.action_intent_id || null);
    setStatusError("");
    setOutcomeUncertain(!isDefinitiveStoredOutcome(result));
    if (result.status === "completed" && result.ok) clearConfirmedDraft();
    if (result.action_intent_id) {
      void fetchBroadcastDelivery(result.action_intent_id)
        .then(setDelivery)
        .catch(() => undefined);
    }
  }, [clearConfirmedDraft]);

  const handleUncertainOutcome = useCallback(() => {
    setOutcomeUncertain(true);
    setStatusError("");
  }, []);

  const handlePrepared = useCallback((intent: PreparedActionIntent) => {
    setStatusIntentId(intent.intent_id);
    setStatusError("");
  }, []);

  const checkStatus = useCallback(async () => {
    if (!statusIntentId || checkingStatus) return;
    setCheckingStatus(true);
    setStatusError("");
    try {
      const [result, deliveryResult] = await Promise.all([
        fetchActionIntentStatus(statusIntentId, { timeoutMs: 15_000 }),
        fetchBroadcastDelivery(statusIntentId, { timeoutMs: 15_000 }).catch(() => null),
      ]);
      setLastResult(result);
      if (deliveryResult) setDelivery(deliveryResult);
      setOutcomeUncertain(!isDefinitiveStoredOutcome(result));
      if (result.status === "completed" && result.ok) clearConfirmedDraft();
    } catch (error) {
      const apiError = error instanceof AdminApiError ? error : null;
      setStatusError(apiError?.correlationId ? `Статус недоступен. ID обращения: ${apiError.correlationId}` : "Статус отправки сейчас недоступен. Не повторяйте отправку.");
    } finally {
      setCheckingStatus(false);
    }
  }, [checkingStatus, clearConfirmedDraft, statusIntentId]);

  function updateDraft(patch: Partial<BroadcastDraft>) {
    setDraft((current) => ({ ...current, ...patch }));
    setFormError("");
  }

  function openPreview(event: FormEvent) {
    event.preventDefault();
    if (outcomeUncertain) {
      setFormError("Новая рассылка заблокирована, пока сервер не подтвердит итог предыдущей отправки.");
      return;
    }
    const limit = Number(draft.limit.trim());
    if (!Number.isInteger(limit) || limit < 1 || limit > 1000) {
      setFormError("Лимит должен быть целым числом от 1 до 1000.");
      return;
    }
    if (!draft.text.trim() || draft.text.length > 4000) {
      setFormError("Введите сообщение длиной от 1 до 4000 символов.");
      return;
    }
    const customIds = parseCustomIds(draft.customIds);
    if (customIds === null || (draft.segment === "custom" && customIds.length === 0)) {
      setFormError("Для пользовательского сегмента укажите корректные положительные Telegram ID.");
      return;
    }
    const payload = {
      segment: draft.segment,
      limit,
      tg_ids: draft.segment === "custom" ? customIds : [],
      text: draft.text,
    };
    setFormError("");
    setLastResult(null);
    setStatusError("");
    setRequest({
      action: "broadcast.send",
      target: { type: "broadcast", id: "broadcast" },
      payload,
      endpoint: "/api/admin/broadcast",
      method: "POST",
    });
    setDialogOpen(true);
  }

  function openFailedRetry() {
    if (!statusIntentId || !delivery?.retryable_failed || !draft.text.trim()) {
      setFormError("Для безопасного повтора нужен исходный текст и подтверждённые временные ошибки.");
      return;
    }
    setRequest({
      action: "broadcast.send",
      target: { type: "broadcast", id: "broadcast" },
      payload: {
        segment: "retry_failed",
        limit: 1000,
        tg_ids: [],
        retry_intent_id: statusIntentId,
        text: draft.text,
      },
      endpoint: "/api/admin/broadcast",
      method: "POST",
    });
    setDialogOpen(true);
  }

  const attempted = useMemo(() => resultCount(lastResult, "attempted"), [lastResult]);
  const sent = useMemo(() => resultCount(lastResult, "sent"), [lastResult]);
  const failed = useMemo(() => resultCount(lastResult, "failed"), [lastResult]);

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone="danger">L3 · внешняя отправка</Badge>
          <span>Получатели фиксируются сервером до подтверждения. Автоматического повтора нет.</span>
        </div>
        {statusIntentId ? <Button tone="secondary" disabled={checkingStatus} onClick={() => void checkStatus()}><RefreshCw size={15} className={checkingStatus ? "animate-spin" : ""} /> Проверить статус</Button> : null}
      </div>

      <MetricStrip label="Сводка рассылки">
        <MetricCell icon={<UsersRound aria-hidden="true" size={17} />} label="Сегмент" value={SEGMENT_LABELS[draft.segment]} detail={draft.segment === "custom" ? parseCustomIds(draft.customIds) === null ? "Есть некорректные ID" : `${parseCustomIds(draft.customIds)?.length || 0} уникальных ID` : "Получатели определяются сервером"} tone="info" />
        <MetricCell icon={<Gauge aria-hidden="true" size={17} />} label="Лимит" value={draft.limit.trim() || "—"} detail="Допустимо от 1 до 1000" tone="neutral" />
        <MetricCell icon={<FileText aria-hidden="true" size={17} />} label="Черновик" value={`${draft.text.length} / 4000`} detail={draft.text.trim() ? "Готов к предпросмотру" : "Введите сообщение"} tone={draft.text.trim() ? "success" : "neutral"} />
        <MetricCell icon={<Send aria-hidden="true" size={17} />} label="Последний результат" value={lastResult ? lastResult.status : "Не запускалась"} detail={sent === null ? "Подтверждённого итога нет" : `Отправлено: ${sent}`} tone={lastResult ? resultTone(lastResult) : "neutral"} />
      </MetricStrip>

      <div className="ops-workspace xl:grid-cols-[minmax(0,0.72fr)_minmax(320px,0.28fr)]">
        <Card>
          <SectionTitle title="Защищённая рассылка" description="Черновик → серверный предпросмотр → точная фраза «ОТПРАВИТЬ» → однократный внешний исполнитель. Изменение сообщения после предпросмотра блокируется." />
          <ol aria-label="Этапы защищённой рассылки" className="mb-5 grid gap-2 sm:grid-cols-3">
            {[
              ["1", "Черновик", "Сегмент, лимит и текст"],
              ["2", "Предпросмотр", "Сервер фиксирует получателей"],
              ["3", "Подтверждение", "Фраза «ОТПРАВИТЬ»"],
            ].map(([step, title, description]) => (
              <li key={step} className="flex gap-2 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-2.5">
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[color:var(--pokrov-status-success-bg)] text-[11px] font-bold text-[color:var(--atlas-primary)]">{step}</span>
                <span><strong className="block text-xs">{title}</strong><span className="mt-0.5 block text-[10px] leading-4 text-[color:var(--atlas-text-muted)]">{description}</span></span>
              </li>
            ))}
          </ol>
          <form className="space-y-4" onSubmit={openPreview}>
            {outcomeUncertain ? <div role="status" className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] p-3 text-xs leading-5 text-[color:var(--atlas-status-warning-text)]"><span className="font-semibold">Новая рассылка заблокирована.</span> Итог предыдущей отправки ещё не подтверждён сервером. Доступна только проверка статуса.</div> : null}
            {formError ? <div role="alert" className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] p-3 text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</div> : null}
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-xs font-semibold">Сегмент<select aria-label="Сегмент рассылки" value={draft.segment} disabled={outcomeUncertain} onChange={(event) => updateDraft({ segment: event.target.value as BroadcastSegment })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="all_active">Все активные</option><option value="paid">Оплаченные</option><option value="trial">Пробный период</option><option value="pending">Ожидают доступа</option><option value="expired">Истёкшие</option><option value="custom">Список Telegram ID</option></select></label>
              <label className="block text-xs font-semibold">Лимит<input aria-label="Лимит рассылки" inputMode="numeric" value={draft.limit} disabled={outcomeUncertain} onChange={(event) => updateDraft({ limit: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 tabular-nums" /></label>
            </div>
            {draft.segment === "custom" ? <label className="block text-xs font-semibold">Telegram ID получателей<textarea aria-label="Telegram ID получателей" value={draft.customIds} disabled={outcomeUncertain} onChange={(event) => updateDraft({ customIds: event.target.value })} placeholder="10001, 10002" className="mt-1 min-h-20 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 font-mono text-xs" /><span className="mt-1 block font-normal text-[color:var(--atlas-text-muted)]">Список не возвращается в UI и не попадает в intent/audit; сохраняются только count и SHA-256.</span></label> : null}
            <label className="block text-xs font-semibold">Сообщение<textarea aria-label="Текст рассылки" value={draft.text} maxLength={4000} disabled={outcomeUncertain} onChange={(event) => updateDraft({ text: event.target.value })} placeholder="Текст сообщения" className="mt-1 min-h-44 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-sm leading-6" /><span className="mt-1 flex justify-between font-normal text-[color:var(--atlas-text-muted)]"><span>Черновик хранится только в sessionStorage этого окна. Не вставляйте секреты.</span><span>{draft.text.length} / 4000</span></span><span className="mt-1 block font-normal leading-5 text-[color:var(--atlas-text-muted)]">Ссылка уйдёт без большой карточки предпросмотра. Фирменный знак — аватар бота; не ставьте эмодзи вместо логотипа в начале сообщения.</span></label>
            <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] p-3 text-xs leading-5 text-[color:var(--atlas-status-warning-text)]"><div className="flex items-center gap-2 font-semibold"><ShieldAlert size={15} /> После timeout итог считается неопределённым</div><p className="mt-1">Не создавайте новую отправку. Используйте только «Проверить статус» и сверку с аудитом.</p></div>
            <Button tone="danger" type="submit" disabled={outcomeUncertain}><Radio size={15} /> Подготовить защищённый предпросмотр</Button>
          </form>
        </Card>

        <aside className="space-y-4 xl:sticky xl:top-[7.75rem] xl:self-start" aria-label="Состояние рассылки">
          <Card>
            <SectionTitle title="Последний результат" description="Показываются только агрегаты backend, ID intent и ID аудита." />
            {lastResult ? <div className="space-y-3 text-xs">
              <Badge tone={resultTone(lastResult)}>{lastResult.status === "completed" ? "Отправка подтверждена" : lastResult.status === "uncertain" || lastResult.status === "executing" ? "Итог неясен — не повторять" : "Отправка завершилась с ошибкой"}</Badge>
              <dl className="grid grid-cols-2 gap-2"><dt className="text-[color:var(--atlas-text-muted)]">Попыток</dt><dd className="font-semibold tabular-nums">{attempted ?? "— · Нет данных"}</dd><dt className="text-[color:var(--atlas-text-muted)]">Отправлено</dt><dd className="font-semibold tabular-nums">{sent ?? "— · Нет данных"}</dd><dt className="text-[color:var(--atlas-text-muted)]">Ошибок</dt><dd className="font-semibold tabular-nums">{failed ?? "— · Нет данных"}</dd><dt className="text-[color:var(--atlas-text-muted)]">Код результата</dt><dd className="break-all font-mono text-[11px]">{lastResult.result_code || "— · Нет данных"}</dd></dl>
              <div className="border-t border-[color:var(--atlas-border)] pt-3"><p className="text-[color:var(--atlas-text-muted)]">Intent ID</p><code className="mt-1 block break-all">{lastResult.action_intent_id || "— · Нет данных"}</code><p className="mt-2 text-[color:var(--atlas-text-muted)]">Audit ID</p><code className="mt-1 block">{lastResult.audit_id ?? "— · Нет данных"}</code></div>
              {delivery ? <div className="border-t border-[color:var(--atlas-border)] pt-3">
                <dl className="grid grid-cols-2 gap-2">
                  <dt className="text-[color:var(--atlas-text-muted)]">Можно повторить</dt><dd className="font-semibold tabular-nums">{delivery.retryable_failed}</dd>
                  <dt className="text-[color:var(--atlas-text-muted)]">Без повтора</dt><dd className="font-semibold tabular-nums">{delivery.terminal_failed}</dd>
                  <dt className="text-[color:var(--atlas-text-muted)]">Всего попыток</dt><dd className="font-semibold tabular-nums">{delivery.attempts}</dd>
                  <dt className="text-[color:var(--atlas-text-muted)]">Среднее время</dt><dd className="font-semibold tabular-nums">{delivery.average_duration_ms === null ? "—" : `${delivery.average_duration_ms} мс`}</dd>
                </dl>
                {Object.keys(delivery.reason_counts).length ? <ul className="mt-3 space-y-1" aria-label="Причины ошибок доставки">{Object.entries(delivery.reason_counts).map(([reason, count]) => <li key={reason} className="flex justify-between gap-3"><span>{DELIVERY_REASON_LABELS[reason] || reason}</span><strong className="tabular-nums">{count}</strong></li>)}</ul> : null}
                {delivery.retryable_failed > 0 ? <Button className="mt-3 w-full" tone="secondary" onClick={openFailedRetry}><RefreshCw size={15} /> Повторить только временные ошибки</Button> : null}
              </div> : null}
            </div> : <p className="text-xs leading-5 text-[color:var(--atlas-text-soft)]">Подтверждённого результата ещё нет. Черновик не очищается при ошибке, 401 или неопределённом исходе.</p>}
          </Card>
          {statusError ? <Card><div role="alert" className="text-xs leading-5 text-[color:var(--atlas-status-warning-text)]">{statusError}</div></Card> : null}
        </aside>
      </div>

      <ActionIntentDialog
        open={dialogOpen}
        request={request}
        onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }}
        onKnownOutcome={() => undefined}
        onCheckState={() => { void checkStatus(); }}
        onUncertainOutcome={handleUncertainOutcome}
        onResult={handleResult}
        onPrepared={handlePrepared}
      />
    </div>
  );
}
