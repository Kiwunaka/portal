"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clock3, RefreshCw, ShieldAlert, XCircle } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, SectionTitle, type Tone } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchProgramApplications, type ProgramApplication } from "@/lib/admin-api/money";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

const KIND_LABELS: Record<string, string> = { competitor_switch: "Переход от VPN", research: "Исследование", team_pack: "Команда" };
const STATUS_LABELS: Record<string, string> = { submitted: "Принята", under_review: "Проверяется", approved: "Одобрена", rejected: "Отклонена", rewarded: "Награждена", cancelled: "Отменена" };
type ProgramsUrlState = { status: string; kind: string; selected: string | null };
type ReviewDraft = { key: string; note: string; rewardDays: string };
const PROGRAM_CODECS = { status: urlCodecs.string(""), kind: urlCodecs.string(""), selected: urlCodecs.optionalString() };

function statusTone(status: string): Tone {
  if (["approved", "rewarded"].includes(status)) return "success";
  if (status === "rejected" || status === "cancelled") return "danger";
  if (status === "under_review") return "warning";
  return "info";
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function ProgramsPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<ProgramsUrlState>(() => readUrlState(PROGRAM_CODECS));
  useEffect(() => subscribeToUrlState<ProgramsUrlState>(PROGRAM_CODECS, setUrlState), []);
  const load = useCallback((signal: AbortSignal) => fetchProgramApplications({ status: urlState.status, kind: urlState.kind }, { signal }), [urlState.kind, urlState.status]);
  const resource = useRouteResource(`growth-programs:${urlState.status}:${urlState.kind}`, load, { enabled: true, pollMs: 60_000 });
  const selected = useMemo(() => resource.data?.find((row) => row.id === urlState.selected) || null, [resource.data, urlState.selected]);
  const [draft, setDraft] = useState<ReviewDraft | null>(null);
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formError, setFormError] = useState("");

  const effectiveDraft: ReviewDraft = draft && draft.key === selected?.id
    ? draft
    : { key: selected?.id || "", note: selected?.operator_note || "", rewardDays: String(selected?.reward_days || 0) };

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.updatedAt,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading, resource.updatedAt]);

  function choose(row: ProgramApplication) {
    setDraft({ key: row.id, note: row.operator_note || "", rewardDays: String(row.reward_days || 0) });
    setFormError("");
    replaceUrlState<ProgramsUrlState>({ selected: row.id }, PROGRAM_CODECS);
  }

  function review(status: "under_review" | "approved" | "rejected") {
    if (!selected) return;
    const reward = Number(effectiveDraft.rewardDays);
    if (![0, 1, 3, 7].includes(reward)) {
      setFormError("Награда должна быть 0, 1, 3 или 7 дней.");
      return;
    }
    if (reward > 0 && status !== "approved") {
      setFormError("Награду можно начислить только вместе с одобрением.");
      return;
    }
    if (selected.kind === "team_pack" && reward > 0) {
      setFormError("Team-pack не создаёт entitlement reward.");
      return;
    }
    setFormError("");
    setRequest({
      action: "program_application.review",
      target: { type: "program_application", id: selected.id },
      payload: { status, operator_note: effectiveDraft.note.trim() || null, reward_days: reward },
      endpoint: `/api/admin/program-applications/${encodeURIComponent(selected.id)}/review`,
      workspace: "growth",
    });
    setDialogOpen(true);
  }

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar"><div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]"><Badge tone="warning">L3 review</Badge><span>Статус и reward grant изменяются одной транзакцией после точного подтверждения ID заявки.</span></div><Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button></div>
      <Card><div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Заявки программ" description="Уникальная legacy-возможность перенесена в канонический Operator Center без прямой записи." /><div className="flex flex-wrap gap-2"><label className="text-xs font-semibold">Статус<select aria-label="Статус заявок" value={urlState.status} onChange={(event) => replaceUrlState<ProgramsUrlState>({ status: event.target.value, selected: null }, PROGRAM_CODECS)} className="ml-2 min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все</option>{Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className="text-xs font-semibold">Тип<select aria-label="Тип заявок" value={urlState.kind} onChange={(event) => replaceUrlState<ProgramsUrlState>({ kind: event.target.value, selected: null }, PROGRAM_CODECS)} className="ml-2 min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все</option>{Object.entries(KIND_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div></div></Card>

      <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку заявок" onRetry={resource.reload}>
        {resource.data ? <div className="ops-workspace xl:grid-cols-[minmax(0,0.9fr)_minmax(22rem,1.1fr)]">
          <Card><div className="mb-3 flex items-center justify-between"><SectionTitle title="Очередь" description="Account ID заменён стабильной непрозрачной ссылкой." /><Badge tone="info">{resource.data.length}</Badge></div><div className="space-y-2">{resource.data.map((row) => <button key={row.id} type="button" onClick={() => choose(row)} className={`w-full rounded-[var(--pokrov-radius-card)] border p-3 text-left outline-none transition ${selected?.id === row.id ? "border-[color:var(--atlas-focus)] bg-[color:var(--atlas-accent-soft)]" : "border-[color:var(--atlas-border)] hover:border-[color:var(--atlas-border-strong)]"}`}><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="font-semibold">{KIND_LABELS[row.kind] || row.kind}</p><p className="mt-1 line-clamp-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{row.summary}</p><p className="mt-2 truncate font-mono text-[10px] text-[color:var(--atlas-text-muted)]">{row.account_ref} · {dateText(row.created_at)}</p></div><Badge tone={statusTone(row.status)}>{STATUS_LABELS[row.status] || row.status}</Badge></div></button>)}{!resource.data.length ? <EmptyState description="Заявок по выбранному фильтру нет." /> : null}</div></Card>

          <Card className="xl:sticky xl:top-[7.75rem] xl:self-start"><SectionTitle title={selected ? KIND_LABELS[selected.kind] || selected.kind : "Карточка заявки"} description={selected ? selected.id : "Выберите заявку в очереди."} />{!selected ? <EmptyState title="Заявка не выбрана" description="Справа появятся доказательства и форма решения." /> : <div className="mt-4 space-y-4"><div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] p-3 text-sm"><p className="whitespace-pre-wrap leading-6">{selected.summary}</p><dl className="mt-3 grid grid-cols-[8rem_1fr] gap-2 text-xs"><dt className="text-[color:var(--atlas-text-muted)]">Статус</dt><dd><Badge tone={statusTone(selected.status)}>{STATUS_LABELS[selected.status] || selected.status}</Badge></dd><dt className="text-[color:var(--atlas-text-muted)]">Account ref</dt><dd className="break-all font-mono text-[11px]">{selected.account_ref}</dd><dt className="text-[color:var(--atlas-text-muted)]">Источник</dt><dd>{selected.source_name || "—"}</dd><dt className="text-[color:var(--atlas-text-muted)]">Контакт</dt><dd className="break-all">{selected.contact || "—"}</dd><dt className="text-[color:var(--atlas-text-muted)]">Мест</dt><dd>{selected.seats ?? "—"}</dd></dl></div><label className="block text-xs font-semibold">Комментарий<textarea aria-label="Комментарий по заявке" maxLength={1000} value={effectiveDraft.note} onChange={(event) => setDraft({ ...effectiveDraft, note: event.target.value })} className="mt-1 min-h-28 w-full rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3" /></label><label className="block text-xs font-semibold">Награда<select aria-label="Награда по заявке" value={effectiveDraft.rewardDays} disabled={selected.kind === "team_pack"} onChange={(event) => setDraft({ ...effectiveDraft, rewardDays: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="0">Без начисления</option><option value="1">1 день</option><option value="3">3 дня</option><option value="7">7 дней</option></select></label>{formError ? <p role="alert" className="text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</p> : null}<div className="flex flex-wrap gap-2"><Button tone="secondary" onClick={() => review("under_review")}><Clock3 size={15} /> В работу</Button><Button tone="primary" onClick={() => review("approved")}><CheckCircle2 size={15} /> Одобрить</Button><Button tone="danger" onClick={() => review("rejected")} disabled={Number(effectiveDraft.rewardDays) > 0}><XCircle size={15} /> Отклонить</Button></div><p className="flex gap-2 text-xs leading-5 text-[color:var(--atlas-text-muted)]"><ShieldAlert size={15} className="mt-0.5 shrink-0" />Повторная команда с тем же intent не создаёт второй grant; изменившаяся заявка отклоняется как stale.</p></div>}</Card>
        </div> : null}
      </RouteBoundary>
      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={() => { setDraft(null); resource.reload(); }} onCheckState={resource.reload} />
    </div>
  );
}
