"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, RefreshCw, ShieldAlert } from "lucide-react";

import { Badge, Button } from "@/components/ui";
import { Dialog } from "@/components/ui/dialog";
import {
  executeAdminAction,
  prepareActionIntent,
  type ActionIntentRequest,
  type AdminActionResult,
  type PreparedActionIntent,
} from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";

type DialogPhase =
  | "preparing"
  | "ready"
  | "executing"
  | "completed"
  | "failed"
  | "uncertain"
  | "expired"
  | "stale"
  | "required"
  | "prepare_failed";

const FIELD_LABELS: Record<string, string> = {
  code: "Нода",
  name: "Название",
  enabled: "Включена",
  accepting_new_clients: "Принимает новых клиентов",
  is_draining: "Выводится из контура",
  mapped_users: "Привязанные пользователи",
  selected_users: "Выбрано для переноса",
  planned_moves: "Запланировано переносов",
  without_target: "Без целевой ноды",
  dry_run: "Только проверка",
  tg_id: "Telegram ID",
  user_tg_id: "Telegram ID пользователя",
  ticket_id: "Тикет",
  status: "Статус",
  manual_users: "Ручные пользователи",
  display_name_length: "Длина имени",
  sub_type: "Тип подписки",
  is_active: "Доступ активен",
  expiry_at: "Срок доступа",
  expires_at: "Срок доступа",
  manual_test: "Ручной или тестовый пользователь",
  key_count: "Количество ключей",
  days: "Дней",
  delta_days: "Изменение срока, дней",
  allow_deactivate: "Разрешить деактивацию",
  blocked: "Заблокирован",
  token: "Токен подписки",
  panel_sync: "Синхронизация панели",
  exists: "Сущность существует",
  node_code: "Нода",
  key_id: "Ключ",
  traffic: "Трафик",
  sub_id: "Идентификатор подписки",
  body_length: "Длина сообщения",
  text_length: "Длина сообщения",
  message_length: "Длина сообщения",
  messages: "Сообщений в тикете",
  message_count: "Сообщений в тикете",
  media_type: "Вложение",
  has_media_file_id: "Есть идентификатор вложения",
  media_payload_length: "Длина метаданных вложения",
  selection_count: "Выбрано записей",
  selected_count: "Выбрано пользователей",
  selection_hash: "Хэш зафиксированной выборки",
  action_title: "Массовое действие",
  burst_mbps: "Ограничение скорости, Мбит/с",
  soft_cap_gb: "Мягкий лимит, ГиБ",
  hard_cap_gb: "Жёсткий лимит, ГиБ",
  notify_soft: "Уведомить о мягком лимите",
  notify_hard: "Уведомить о жёстком лимите",
  auto_disable_on_hard: "Выключить при жёстком лимите",
  apply_now: "Применить сейчас",
  tier_days: "Дней награды",
  expiry: "Срок доступа",
  scenario: "Сценарий",
  state: "Состояние",
  updated_at: "Обновлено",
  count: "Выбрано привязок",
  hash: "Хэш выборки",
  enabled_count: "Включено ключей",
  online_count: "Ключей онлайн",
};

function valueText(value: unknown, field: string): string {
  if (value === true) return "Да";
  if (value === false) return "Нет";
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") return value.toLocaleString("ru-RU");
  const raw = String(value);
  if (field.endsWith("_at")) {
    const timestamp = Date.parse(raw);
    if (!Number.isNaN(timestamp)) {
      return new Date(timestamp).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
    }
  }
  const labels: Record<string, string> = {
    active: "Активен",
    inactive: "Неактивен",
    blocked: "Заблокирован",
    expired: "Истёк",
    open: "Открыт",
    in_progress: "В работе",
    closed: "Закрыт",
    enabled: "Включён",
    disabled: "Выключен",
  };
  return labels[raw.trim().toLowerCase()] || raw;
}

function PreviewState({ title, values }: { title: string; values: Record<string, unknown> }) {
  const supportedEntries = Object.entries(values).filter(([key]) => Object.prototype.hasOwnProperty.call(FIELD_LABELS, key));
  return (
    <section className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <h3 className="text-xs font-semibold text-[color:var(--atlas-text)]">{title}</h3>
      <dl className="mt-3 grid gap-2 text-xs">
        {supportedEntries.map(([key, value]) => (
          <div key={key} className="flex items-start justify-between gap-3">
            <dt className="text-[color:var(--atlas-text-soft)]">{FIELD_LABELS[key]}</dt>
            <dd className="text-right font-semibold text-[color:var(--atlas-text)]">{valueText(value, key)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function phaseMessage(phase: DialogPhase): { title: string; body: string } | null {
  const messages: Partial<Record<DialogPhase, { title: string; body: string }>> = {
    completed: {
      title: "Действие выполнено",
      body: "Сервер подтвердил итог. Список и карточка обновляются по основным данным сервера.",
    },
    failed: {
      title: "Действие завершилось с ошибкой",
      body: "Сервер сохранил известный итог. Перед новым действием проверьте текущее состояние сущности.",
    },
    uncertain: {
      title: "Итог действия неясен",
      body: "Команда могла дойти до внешней системы. Не повторяйте её: сначала проверьте текущее состояние.",
    },
    expired: {
      title: "Срок предпросмотра истёк",
      body: "Состояние нужно перечитать и подготовить новый предпросмотр.",
    },
    stale: {
      title: "Состояние изменилось",
      body: "Сохранённый предпросмотр больше не соответствует сущности. Подготовьте новый предпросмотр.",
    },
    required: {
      title: "Нет действующего защищённого намерения",
      body: "Команда не отправлена. Подготовьте серверный предпросмотр заново.",
    },
    prepare_failed: {
      title: "Предпросмотр недоступен",
      body: "Действие не запускалось. Можно закрыть окно или вручную повторить подготовку предпросмотра.",
    },
  };
  return messages[phase] || null;
}

export function ActionIntentDialog({
  open,
  request,
  onOpenChange,
  onKnownOutcome,
  onCheckState,
  onResult,
}: {
  open: boolean;
  request: ActionIntentRequest | null;
  onOpenChange: (open: boolean) => void;
  onKnownOutcome: () => void;
  onCheckState: () => void;
  onResult?: (result: AdminActionResult) => void;
}) {
  const [phase, setPhase] = useState<DialogPhase>("preparing");
  const [intent, setIntent] = useState<PreparedActionIntent | null>(null);
  const [result, setResult] = useState<AdminActionResult | null>(null);
  const [confirmation, setConfirmation] = useState("");
  const [correlationId, setCorrelationId] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const preparedRequestRef = useRef<ActionIntentRequest | null>(null);
  const prepareSequenceRef = useRef(0);
  const executingRef = useRef(false);

  const prepare = useCallback(async (nextRequest: ActionIntentRequest) => {
    const sequence = ++prepareSequenceRef.current;
    setPhase("preparing");
    setIntent(null);
    setResult(null);
    setConfirmation("");
    setCorrelationId(null);
    try {
      const prepared = await prepareActionIntent(nextRequest);
      if (sequence !== prepareSequenceRef.current) return;
      setIntent(prepared);
      setPhase("ready");
    } catch (error) {
      if (sequence !== prepareSequenceRef.current) return;
      setCorrelationId(error instanceof AdminApiError ? error.correlationId : null);
      setPhase("prepare_failed");
    }
  }, []);

  useEffect(() => {
    if (!open || !request) {
      preparedRequestRef.current = null;
      prepareSequenceRef.current += 1;
      executingRef.current = false;
      return;
    }
    if (preparedRequestRef.current === request) return;
    preparedRequestRef.current = request;
    void prepare(request);
  }, [open, prepare, request]);

  const confirmationMatches = useMemo(() => {
    if (!intent) return false;
    return confirmation.normalize("NFC").trim() === intent.confirmation_challenge.normalize("NFC").trim();
  }, [confirmation, intent]);

  const unsupportedPreviewFields = useMemo(() => {
    if (!intent?.preview) return [];
    const records = [
      intent.preview.before,
      intent.preview.after,
      intent.preview.selection || {},
    ];
    return [...new Set(records.flatMap((values) => Object.keys(values)))]
      .filter((key) => !Object.prototype.hasOwnProperty.call(FIELD_LABELS, key))
      .sort();
  }, [intent]);
  const previewSchemaSupported = unsupportedPreviewFields.length === 0;

  const execute = useCallback(async () => {
    if (!request || !intent || !confirmationMatches || !previewSchemaSupported || executingRef.current) return;
    if (Date.parse(intent.expires_at) <= Date.now()) {
      setPhase("expired");
      return;
    }
    executingRef.current = true;
    setPhase("executing");
    setCorrelationId(null);
    try {
      const completed = await executeAdminAction({
        endpoint: request.endpoint,
        payload: request.payload,
        intent,
        confirmation,
        method: request.method,
      });
      setResult(completed);
      onResult?.(completed);
      if (completed.status === "completed") {
        setPhase("completed");
        onKnownOutcome();
      } else if (completed.status === "uncertain" || completed.status === "executing") {
        setPhase("uncertain");
      } else {
        setPhase("failed");
        onKnownOutcome();
      }
    } catch (error) {
      const apiError = error instanceof AdminApiError ? error : null;
      setCorrelationId(apiError?.correlationId || null);
      if (apiError?.code === "expired_intent") setPhase("expired");
      else if (apiError?.code === "stale_intent") setPhase("stale");
      else if (apiError?.status === 428 || apiError?.code === "intent_required") setPhase("required");
      else if (!apiError || apiError.status >= 500) setPhase("uncertain");
      else setPhase("failed");
    } finally {
      executingRef.current = false;
    }
  }, [confirmation, confirmationMatches, intent, onKnownOutcome, onResult, previewSchemaSupported, request]);

  const prepareAgain = useCallback(() => {
    if (!request) return;
    preparedRequestRef.current = request;
    void prepare(request);
  }, [prepare, request]);

  const checkState = useCallback(() => {
    if (checking) return;
    setChecking(true);
    try {
      onCheckState();
    } finally {
      window.setTimeout(() => setChecking(false), 500);
    }
  }, [checking, onCheckState]);

  const message = phaseMessage(phase);
  const preview = intent?.preview;
  const expiresAt = intent ? Date.parse(intent.expires_at) : Number.NaN;
  const expiresText = Number.isFinite(expiresAt)
    ? new Date(expiresAt).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "medium" })
    : "не указано";

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (phase === "executing") return;
        onOpenChange(nextOpen);
      }}
      title="Проверка действия"
      description="Сервер перечитал сущность и привязал предпросмотр к её текущей версии. Команда не повторяется автоматически."
      className="max-w-3xl"
      footer={(
        <>
          <Button tone="ghost" disabled={phase === "executing"} onClick={() => onOpenChange(false)}>Закрыть</Button>
          {phase === "ready" ? (
            <Button tone={intent?.risk_level === "L3" ? "danger" : "primary"} disabled={!confirmationMatches || !previewSchemaSupported} onClick={() => void execute()}>
              Выполнить
            </Button>
          ) : null}
          {phase === "expired" || phase === "stale" || phase === "required" || phase === "prepare_failed" ? (
            <Button tone="secondary" onClick={prepareAgain}><RefreshCw size={15} /> Подготовить новый предпросмотр</Button>
          ) : null}
          {phase === "uncertain" ? (
            <Button tone="primary" disabled={checking} onClick={checkState}>
              <RefreshCw size={15} className={checking ? "animate-spin" : ""} /> Проверить текущее состояние
            </Button>
          ) : null}
        </>
      )}
    >
      {phase === "preparing" ? (
        <div className="flex min-h-40 items-center justify-center gap-2 text-sm text-[color:var(--atlas-text-soft)]">
          <RefreshCw size={17} className="animate-spin" /> Сервер готовит предпросмотр…
        </div>
      ) : null}

      {intent && preview ? (
        <div className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold">{preview.title}</h3>
              <p className="mt-1 text-sm text-[color:var(--atlas-text-soft)]">{preview.summary}</p>
            </div>
            <Badge tone={intent.risk_level === "L3" ? "danger" : "warning"}>Риск {intent.risk_level}</Badge>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <PreviewState title="Сейчас" values={preview.before} />
            <PreviewState title="После выполнения" values={preview.after} />
          </div>

          {preview.selection ? <PreviewState title="Зафиксированная выборка" values={preview.selection} /> : null}

          {!previewSchemaSupported ? (
            <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] p-3 text-xs text-[color:var(--atlas-status-danger-text)]">
              <div className="flex items-center gap-2 font-semibold"><ShieldAlert size={15} /> Неподдерживаемая схема предпросмотра</div>
              <p className="mt-2 leading-5">Сервер вернул неизвестные поля: {unsupportedPreviewFields.join(", ")}. Выполнение заблокировано до обновления интерфейса.</p>
            </div>
          ) : null}

          {preview.warnings.length ? (
            <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] p-3 text-xs text-[color:var(--atlas-status-warning-text)]">
              <div className="flex items-center gap-2 font-semibold"><AlertTriangle size={15} /> Важные последствия</div>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {preview.warnings.map((warning) => <li key={warning}>{warning}</li>)}
              </ul>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
            <Clock3 size={14} /> Предпросмотр действует до {expiresText}
          </div>

          {phase === "ready" || phase === "executing" ? (
            <label className="block text-xs font-semibold text-[color:var(--atlas-text)]">
              Подтверждение
              <span className="mt-1 block font-normal text-[color:var(--atlas-text-soft)]">
                Введите «{intent.confirmation_challenge}» — пробелы по краям не учитываются.
              </span>
              <input
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                disabled={phase === "executing"}
                autoComplete="off"
                spellCheck={false}
                className="mt-2 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 font-mono text-sm uppercase outline-none focus:border-[color:var(--atlas-focus)]"
              />
            </label>
          ) : null}
        </div>
      ) : null}

      {phase === "executing" ? (
        <div className="mt-4 flex items-center gap-2 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3 text-xs text-[color:var(--atlas-text-soft)]">
          <RefreshCw size={15} className="animate-spin" /> Команда выполняется один раз…
        </div>
      ) : null}

      {message ? (
        <div className={`mt-4 rounded-[var(--pokrov-radius-card)] border p-3 ${phase === "completed" ? "border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)]" : phase === "uncertain" || phase === "expired" || phase === "stale" ? "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)]" : "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)]"}`}>
          <div className="flex items-center gap-2 text-sm font-semibold">
            {phase === "completed" ? <CheckCircle2 size={17} /> : <ShieldAlert size={17} />}
            {message.title}
          </div>
          <p className="mt-1 text-xs leading-5">{message.body}</p>
          {result?.audit_id ? <p className="mt-2 text-xs font-semibold">ID аудита: {result.audit_id}</p> : null}
          {result?.action_intent_id ? <p className="mt-1 text-[11px] text-[color:var(--atlas-text-soft)]">ID действия: {result.action_intent_id}</p> : null}
          {correlationId ? <p className="mt-1 text-[11px] text-[color:var(--atlas-text-soft)]">ID обращения: {correlationId}</p> : null}
        </div>
      ) : null}
    </Dialog>
  );
}
