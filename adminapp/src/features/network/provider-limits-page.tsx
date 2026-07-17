"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { RefreshCw, Save, Trash2 } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { MISSING_DATA_TEXT, MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, Progress, SectionTitle, type Tone } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchProviderQuotas, type ProviderQuotaConfig, type ProviderQuotaStatus } from "@/lib/admin-api/network";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type ProviderUrlState = { selected: string | null };
const PROVIDER_URL_CODECS = { selected: urlCodecs.optionalString() };

type QuotaDraft = {
  nodeCode: string;
  includedGb: string;
  resetDay: string;
  timezone: string;
  warningRatio: string;
  criticalRatio: string;
  enabled: boolean;
  operatorNote: string;
};

type QuotaEditState = {
  nodeCode: string;
  draft: QuotaDraft;
  sourceVersion: string;
  dirty: boolean;
  error: string;
};

function tone(value: string): Tone {
  const normalized = value.toLowerCase();
  if (normalized === "critical") return "danger";
  if (["warning", "missing_limit"].includes(normalized)) return "warning";
  if (normalized === "ok") return "success";
  return "neutral";
}

function stateLabel(value: string): string {
  return {
    ok: "Норма",
    warning: "Приближается лимит",
    critical: "Критический расход",
    disabled: "Контроль выключен",
    missing_limit: "Лимит не задан",
    unconfigured: "Не настроено",
  }[value.toLowerCase()] || value || MISSING_DATA_TEXT;
}

function finite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberText(value: unknown, suffix = ""): string {
  const normalized = finite(value);
  return normalized === null ? "—" : `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(normalized)}${suffix}`;
}

function QuotaNumber({ value, suffix = "" }: { value: unknown; suffix?: string }) {
  return finite(value) === null ? <MissingData /> : <span className="tabular-nums">{numberText(value, suffix)}</span>;
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function draftFor(nodeCode: string, config: ProviderQuotaConfig | null, status: ProviderQuotaStatus | null): QuotaDraft {
  return {
    nodeCode,
    includedGb: String(config?.included_gb ?? status?.included_gb ?? ""),
    resetDay: String(config?.reset_day ?? status?.reset_day ?? 1),
    timezone: config?.timezone || status?.timezone || "UTC",
    warningRatio: String(config?.warning_ratio ?? status?.warning_ratio ?? 0.8),
    criticalRatio: String(config?.critical_ratio ?? status?.critical_ratio ?? 0.95),
    enabled: config?.enabled ?? status?.enabled ?? true,
    operatorNote: "",
  };
}

function quotaSourceVersion(config: ProviderQuotaConfig | null, status: ProviderQuotaStatus | null): string {
  if (config) return `config:${config.id}:${config.updated_at || "missing"}`;
  if (!status) return "missing";
  return `status:${status.node_code}:${status.updated_at || "missing"}:${status.included_gb ?? "missing"}:${status.reset_day ?? "missing"}:${status.timezone || "missing"}:${status.warning_ratio ?? "missing"}:${status.critical_ratio ?? "missing"}:${status.enabled}`;
}

export function ProviderLimitsPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<ProviderUrlState>(() => readUrlState(PROVIDER_URL_CODECS));
  const [editState, setEditState] = useState<QuotaEditState | null>(null);
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  useEffect(() => subscribeToUrlState<ProviderUrlState>(PROVIDER_URL_CODECS, setUrlState), []);

  const load = useCallback((signal: AbortSignal) => fetchProviderQuotas({ signal }), []);
  const resource = useRouteResource("provider-quotas", load, { enabled: true, pollMs: 60_000 });
  const selectedCode = urlState.selected?.trim().toLowerCase() || null;
  const selectedConfig = resource.data?.configs.find((row) => row.node_code.toLowerCase() === selectedCode) || null;
  const selectedStatus = resource.data?.statuses.find((row) => row.node_code.toLowerCase() === selectedCode) || null;
  const selectedSourceVersion = quotaSourceVersion(selectedConfig, selectedStatus);
  const activeEdit = editState?.nodeCode === selectedCode ? editState : null;
  const serverDraft = selectedCode && resource.data !== null ? draftFor(selectedCode, selectedConfig, selectedStatus) : null;
  const draft = activeEdit?.draft || serverDraft;
  const draftSourceVersion = activeEdit?.sourceVersion || selectedSourceVersion;
  const dirty = activeEdit?.dirty || false;
  const formError = activeEdit?.error || "";

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.statuses.map((row) => row.updated_at).filter((value): value is string => Boolean(value)).sort().at(0) || resource.data?.generatedAt || null,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const columns = useMemo<ColumnDef<ProviderQuotaStatus>[]>(() => [
    {
      header: "Нода",
      cell: ({ row }) => <button aria-label={`Открыть лимит ${row.original.node_code.toUpperCase()}`} className="rounded-sm text-left font-semibold uppercase outline-none hover:underline focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]" onClick={() => replaceUrlState<ProviderUrlState>({ selected: row.original.node_code }, PROVIDER_URL_CODECS)}>{row.original.node_code}<span className="block font-normal normal-case text-[11px] text-[color:var(--atlas-text-muted)]">{row.original.node_name || "Название: — · Нет данных"}</span></button>,
    },
    { header: "Состояние", cell: ({ row }) => <Badge tone={tone(row.original.state)}>{stateLabel(row.original.state)}</Badge> },
    { header: "Использовано", cell: ({ row }) => row.original.configured && finite(row.original.used_gb) !== null && finite(row.original.included_gb) !== null ? <span className="tabular-nums">{numberText(row.original.used_gb, " ГиБ")} / {numberText(row.original.included_gb, " ГиБ")}</span> : <MissingData /> },
    { header: "Осталось", cell: ({ row }) => <QuotaNumber value={row.original.configured ? row.original.remaining_gb : null} suffix=" ГиБ" /> },
    { header: "Заполнение", cell: ({ row }) => row.original.configured && finite(row.original.used_pct) !== null ? <div className="min-w-28"><div className="mb-1 tabular-nums">{numberText(row.original.used_pct, "%")}</div><Progress value={row.original.used_pct as number} tone={tone(row.original.state)} /></div> : <MissingData /> },
    { header: "Сброс", cell: ({ row }) => row.original.cycle_end ? <span>{dateText(row.original.cycle_end)}</span> : <MissingData /> },
  ], []);

  function updateDraft(patch: Partial<QuotaDraft>) {
    if (!selectedCode || !draft) return;
    setEditState((current) => {
      const base = current?.nodeCode === selectedCode
        ? current
        : { nodeCode: selectedCode, draft, sourceVersion: selectedSourceVersion, dirty: false, error: "" };
      return { ...base, draft: { ...base.draft, ...patch }, dirty: true, error: "" };
    });
  }

  function setCurrentError(error: string) {
    if (!selectedCode || !draft) return;
    setEditState((current) => current?.nodeCode === selectedCode
      ? { ...current, error }
      : { nodeCode: selectedCode, draft, sourceVersion: selectedSourceVersion, dirty: false, error });
  }

  function resetDraftFromServer() {
    if (!selectedCode || resource.data === null) return;
    setEditState(null);
  }

  function handleKnownOutcome() {
    setEditState(null);
    resource.reload();
  }

  function openSave(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    if (!draft.includedGb.trim()) {
      setCurrentError("Введите лимит квоты в ГиБ: пустое значение нельзя сохранить.");
      return;
    }
    if ([draft.resetDay, draft.warningRatio, draft.criticalRatio].some((value) => !value.trim())) {
      setCurrentError("Заполните день сброса и оба порога квоты.");
      return;
    }
    const includedGb = Number(draft.includedGb.trim());
    const resetDay = Number(draft.resetDay.trim());
    const warningRatio = Number(draft.warningRatio.trim());
    const criticalRatio = Number(draft.criticalRatio.trim());
    if (![includedGb, resetDay, warningRatio, criticalRatio].every(Number.isFinite) || includedGb < 0 || !Number.isInteger(resetDay) || resetDay < 1 || resetDay > 31) {
      setCurrentError("Проверьте лимит и день сброса: нужны допустимые числовые значения.");
      return;
    }
    if (warningRatio >= criticalRatio || warningRatio < 0.01 || criticalRatio > 1) {
      setCurrentError("Порог предупреждения должен быть ниже критического; оба значения — от 0.01 до 1.0.");
      return;
    }
    if (!draft.timezone.trim()) {
      setCurrentError("Укажите часовой пояс квоты.");
      return;
    }
    const operatorNote = draft.operatorNote.trim();
    const basePayload: Record<string, unknown> = { included_gb: includedGb, reset_day: resetDay, timezone: draft.timezone.trim(), warning_ratio: warningRatio, critical_ratio: criticalRatio, enabled: draft.enabled };
    if (selectedConfig) {
      if (operatorNote) basePayload.notes = operatorNote;
    } else {
      basePayload.notes = operatorNote || null;
    }
    setCurrentError("");
    setRequest({
      action: selectedConfig ? "provider_quota.update" : "provider_quota.create",
      target: { type: "provider_quota", id: draft.nodeCode },
      payload: selectedConfig ? basePayload : { node_code: draft.nodeCode, ...basePayload },
      endpoint: selectedConfig ? `/api/admin/provider-quotas/${encodeURIComponent(draft.nodeCode)}` : "/api/admin/provider-quotas",
      method: selectedConfig ? "PATCH" : "POST",
    });
    setDialogOpen(true);
  }

  function openDelete() {
    if (!draft || !selectedConfig) return;
    setRequest({ action: "provider_quota.delete", target: { type: "provider_quota", id: draft.nodeCode }, payload: {}, endpoint: `/api/admin/provider-quotas/${encodeURIComponent(draft.nodeCode)}`, method: "DELETE" });
    setDialogOpen(true);
  }

  const serverChangedWhileEditing = Boolean(dirty && draftSourceVersion !== selectedSourceVersion);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]"><Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>{resource.error ? "Есть сбой источника" : resource.data ? "Лимиты перечитаны" : "Лимиты ещё не получены"}</Badge><span>{resource.data ? `${resource.data.configs.length} настроенных квот` : "Данные ещё не получены"}</span></div>
        <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)]">
        <Card>
          <SectionTitle title="Лимиты провайдеров" description="Серверный расход, окно сброса и остаток по нодам. Исходные provider payload и секреты не показываются." />
          <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку лимитов" onRetry={resource.reload}>
            {resource.data?.statuses.length ? <DataTable data={resource.data.statuses} columns={columns} empty="Нет нод или квот" /> : resource.data ? <EmptyState description="Сервер не вернул ни одной ноды для настройки квоты." /> : null}
          </RouteBoundary>
        </Card>

        <aside aria-label="Редактор лимита">
          <Card className="xl:sticky xl:top-4">
            <SectionTitle title={selectedConfig ? `Квота ${selectedCode?.toUpperCase()}` : selectedCode ? `Новая квота ${selectedCode.toUpperCase()}` : "Редактор квоты"} description="Сохранение сначала открывает серверный review. Удаление потребует точный код ноды." />
            {!draft ? <EmptyState title="Выберите ноду" description="Откройте строку в таблице, чтобы настроить или проверить квоту." /> : (
              <form className="space-y-3" onSubmit={openSave}>
                {dirty ? <div role="status" className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] p-3 text-xs text-[color:var(--atlas-status-warning-text)]"><p>{serverChangedWhileEditing ? "На сервере есть более свежая версия. Несохранённый черновик не перезаписан." : "Есть несохранённые изменения."}</p><Button tone="secondary" type="button" className="mt-2" onClick={resetDraftFromServer}><RefreshCw size={14} /> Перечитать с сервера</Button></div> : null}
                {formError ? <div role="alert" className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] p-3 text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</div> : null}
                <label className="block text-xs font-semibold">Лимит, ГиБ<input aria-label="Лимит квоты в ГиБ" inputMode="decimal" value={draft.includedGb} onChange={(event) => updateDraft({ includedGb: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 tabular-nums outline-none focus:border-[color:var(--atlas-focus)]" /></label>
                <div className="grid grid-cols-2 gap-2">
                  <label className="block text-xs font-semibold">День сброса<input aria-label="День сброса квоты" inputMode="numeric" value={draft.resetDay} onChange={(event) => updateDraft({ resetDay: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 tabular-nums outline-none focus:border-[color:var(--atlas-focus)]" /></label>
                  <label className="block text-xs font-semibold">Часовой пояс<input aria-label="Часовой пояс квоты" value={draft.timezone} onChange={(event) => updateDraft({ timezone: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 outline-none focus:border-[color:var(--atlas-focus)]" /></label>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <label className="block text-xs font-semibold">Порог предупреждения<input aria-label="Порог предупреждения квоты" inputMode="decimal" value={draft.warningRatio} onChange={(event) => updateDraft({ warningRatio: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 tabular-nums outline-none focus:border-[color:var(--atlas-focus)]" /></label>
                  <label className="block text-xs font-semibold">Критический порог<input aria-label="Критический порог квоты" inputMode="decimal" value={draft.criticalRatio} onChange={(event) => updateDraft({ criticalRatio: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 tabular-nums outline-none focus:border-[color:var(--atlas-focus)]" /></label>
                </div>
                <label className="flex min-h-10 items-center gap-2 text-xs font-semibold"><input type="checkbox" checked={draft.enabled} onChange={(event) => updateDraft({ enabled: event.target.checked })} /> Контроль лимита включён</label>
                <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--command-surface-raised)] p-3 text-xs text-[color:var(--atlas-text-soft)]">{selectedConfig?.notes_present ? `Сохранённое примечание есть (${selectedConfig.notes_length} символов). Его текст намеренно не возвращается в интерфейс.` : "Сохранённого примечания нет."}</div>
                <label className="block text-xs font-semibold">Новое примечание оператора<textarea aria-label="Новое примечание к квоте" value={draft.operatorNote} onChange={(event) => updateDraft({ operatorNote: event.target.value })} className="mt-1 min-h-20 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 outline-none focus:border-[color:var(--atlas-focus)]" /></label>
                <p className="text-[11px] leading-5 text-[color:var(--atlas-text-muted)]">Оставьте поле пустым, чтобы не менять сохранённое примечание. Не вставляйте ключи, URL подписок, IP-адреса и сырой ответ провайдера.</p>
                <div className="flex flex-wrap gap-2"><Button tone="primary" type="submit"><Save size={15} /> Проверить и сохранить</Button>{selectedConfig ? <Button tone="danger" type="button" onClick={openDelete}><Trash2 size={15} /> Удалить</Button> : null}</div>
                {selectedStatus ? <p className="text-xs leading-5 text-[color:var(--atlas-text-soft)]">Текущий серверный статус: {stateLabel(selectedStatus.state)}. Источник: {selectedStatus.source || "— · Нет данных"}.</p> : null}
              </form>
            )}
          </Card>
        </aside>
      </div>

      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={handleKnownOutcome} onCheckState={resource.reload} />
    </div>
  );
}
