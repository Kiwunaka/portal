"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { CalendarX, CircleCheck, PackageX, Plus, RefreshCw, Save, Tag, Trash2 } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchPromos, type PromoRow } from "@/lib/admin-api/revenue";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";
import { CampaignSlotsPanel } from "./campaign-slots-panel";
import { WinbackPilotDecisionPanel } from "./winback-pilot-decision-panel";

type PromoUrlState = { state: string; q: string; selected: string | null };
type PromoDraft = { code: string; promoType: "discount" | "days"; value: string; usesLeft: string; expiresAt: string };
type PromoEditState = { key: string; draft: PromoDraft; sourceVersion: string; dirty: boolean; error: string };
const PROMO_URL_CODECS = { state: urlCodecs.string(""), q: urlCodecs.string(""), selected: urlCodecs.optionalString() };

function promoState(row: PromoRow): string {
  if (row.value === null || row.uses_left === null || row.promo_type === null) return "unknown";
  if (row.expires_at && Number.isNaN(Date.parse(row.expires_at))) return "unknown";
  if (row.expires_at && Date.parse(row.expires_at) <= Date.now()) return "expired";
  if (row.uses_left === 0) return "depleted";
  return "active";
}

function stateLabel(value: string): string {
  return ({ active: "Активен", expired: "Истёк", depleted: "Исчерпан", unknown: "Нет данных" } as Record<string, string>)[value] || value;
}

function stateTone(value: string): Tone {
  return value === "active" ? "success" : value === "expired" ? "danger" : value === "depleted" ? "warning" : "neutral";
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function dateInput(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function draftFrom(row: PromoRow | null): PromoDraft {
  return { code: row?.code || "", promoType: row?.promo_type === "days" ? "days" : "discount", value: row?.value === null || row?.value === undefined ? "" : String(row.value), usesLeft: row?.uses_left === null || row?.uses_left === undefined ? "-1" : String(row.uses_left), expiresAt: dateInput(row?.expires_at || null) };
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function PromosPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<PromoUrlState>(() => readUrlState(PROMO_URL_CODECS));
  const [editState, setEditState] = useState<PromoEditState | null>(null);
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  useEffect(() => subscribeToUrlState<PromoUrlState>(PROMO_URL_CODECS, setUrlState), []);
  const load = useCallback((signal: AbortSignal) => fetchPromos({ signal }), []);
  const resource = useRouteResource("promos", load, { enabled: true, pollMs: 60_000 });
  const selected = urlState.selected && urlState.selected !== "new" ? resource.data?.find((row) => row.code.toUpperCase() === urlState.selected?.toUpperCase()) || null : null;
  const creating = urlState.selected === "new";
  const selectionKey = urlState.selected?.toUpperCase() || null;
  const serverDraft = creating ? draftFrom(null) : selected ? draftFrom(selected) : null;
  const selectedSourceVersion = JSON.stringify(serverDraft);
  const matchingEdit = editState?.key === selectionKey ? editState : null;
  const activeEdit = matchingEdit && (matchingEdit.dirty || matchingEdit.sourceVersion === selectedSourceVersion)
    ? matchingEdit
    : null;
  const draft = activeEdit?.draft || serverDraft;
  const dirty = activeEdit?.dirty || false;
  const formError = activeEdit?.error || "";
  useEffect(() => {
    onShellStatus?.({ api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok", session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing", oldestRequiredSourceAt: resource.data?.map((row) => row.created_at).filter((value): value is string => Boolean(value)).sort().at(0) || null });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const rows = useMemo(() => (resource.data || []).filter((row) => (!urlState.state || promoState(row) === urlState.state) && (!urlState.q || row.code.toLowerCase().includes(urlState.q.toLowerCase()))), [resource.data, urlState.q, urlState.state]);
  const columns = useMemo<ColumnDef<PromoRow>[]>(() => [
    { header: "Промокод", cell: ({ row }) => <button className="font-mono font-semibold hover:underline" onClick={() => replaceUrlState<PromoUrlState>({ selected: row.original.code }, PROMO_URL_CODECS)}>{row.original.code}</button> },
    { header: "Состояние", cell: ({ row }) => promoState(row.original) === "unknown" ? <MissingData /> : <Badge tone={stateTone(promoState(row.original))}>{stateLabel(promoState(row.original))}</Badge> },
    { header: "Тип", cell: ({ row }) => row.original.promo_type === "days" ? "Дни" : row.original.promo_type === "discount" ? "Скидка" : <MissingData /> },
    { header: "Значение", cell: ({ row }) => row.original.value === null || row.original.promo_type === null ? <MissingData /> : <span className="tabular-nums">{row.original.value}{row.original.promo_type === "discount" ? "%" : " дн."}</span> },
    { header: "Осталось / использовано", cell: ({ row }) => row.original.uses_left === null || row.original.used_count === null ? <MissingData /> : <span className="tabular-nums">{row.original.uses_left < 0 ? "∞" : row.original.uses_left} / {row.original.used_count}</span> },
    { header: "Истекает", cell: ({ row }) => row.original.expires_at ? dateText(row.original.expires_at) : <span>Без срока</span> },
  ], []);

  function updateDraft(patch: Partial<PromoDraft>) {
    if (!selectionKey || !draft) return;
    setEditState((current) => {
      const base = current?.key === selectionKey && (current.dirty || current.sourceVersion === selectedSourceVersion)
        ? current
        : { key: selectionKey, draft, sourceVersion: selectedSourceVersion, dirty: false, error: "" };
      return { ...base, draft: { ...base.draft, ...patch }, dirty: true, error: "" };
    });
  }
  function setCurrentError(error: string) {
    if (!selectionKey || !draft) return;
    setEditState((current) => current?.key === selectionKey && (current.dirty || current.sourceVersion === selectedSourceVersion)
      ? { ...current, error }
      : { key: selectionKey, draft, sourceVersion: selectedSourceVersion, dirty: false, error });
  }
  function reload() { setEditState(null); resource.reload(); }
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    const code = draft.code.trim().toUpperCase();
    const value = Number(draft.value);
    const usesLeft = Number(draft.usesLeft);
    if (!/^[A-Z0-9][A-Z0-9_-]{2,19}$/.test(code)) { setCurrentError("Код: 3–20 символов A-Z, цифр, дефиса или подчёркивания."); return; }
    if (!Number.isInteger(value) || value < 1 || !Number.isInteger(usesLeft) || usesLeft < -1) { setCurrentError("Значение и остаток должны быть допустимыми целыми числами; -1 означает безлимит."); return; }
    const payload = creating ? { code, promo_type: draft.promoType, value, uses_left: usesLeft, expires_at: draft.expiresAt || null } : { new_code: code, promo_type: draft.promoType, value, uses_left: usesLeft, expires_at: draft.expiresAt || null };
    setRequest({ action: creating ? "promo.create" : "promo.update", target: { type: "promo", id: creating ? code : String(selected?.code) }, payload, endpoint: creating ? "/api/admin/promos" : `/api/admin/promos/${encodeURIComponent(String(selected?.code))}`, method: creating ? "POST" : "PATCH", workspace: "money" });
    setDialogOpen(true);
  }
  function remove() {
    if (!selected) return;
    setRequest({ action: "promo.delete", target: { type: "promo", id: selected.code }, payload: {}, endpoint: `/api/admin/promos/${encodeURIComponent(selected.code)}`, method: "DELETE", workspace: "money" });
    setDialogOpen(true);
  }

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar"><div className="flex gap-2 text-xs"><Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>{resource.error ? "Источник промо отвечает с ошибкой" : resource.data ? "Промокоды получены" : "Промокоды ещё не получены"}</Badge><span className="text-[color:var(--atlas-text-soft)]">{resource.data ? `${resource.data.length} записей` : "— · Нет данных"}</span></div><div className="flex gap-2"><Button tone="primary" onClick={() => replaceUrlState<PromoUrlState>({ selected: "new" }, PROMO_URL_CODECS)}><Plus size={15} /> Создать</Button><Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button></div></div>
      {resource.data ? (
        <MetricStrip label="Сводка промокодов">
          <MetricCell icon={<Tag aria-hidden="true" size={17} />} label="Всего" value={resource.data.length} detail="В серверном реестре" tone="info" />
          <MetricCell icon={<CircleCheck aria-hidden="true" size={17} />} label="Активные" value={resource.data.filter((row) => promoState(row) === "active").length} detail="Можно применить сейчас" tone="success" />
          <MetricCell icon={<CalendarX aria-hidden="true" size={17} />} label="Истекли" value={resource.data.filter((row) => promoState(row) === "expired").length} detail="Срок закончился" tone="neutral" />
          <MetricCell icon={<PackageX aria-hidden="true" size={17} />} label="Исчерпаны" value={resource.data.filter((row) => promoState(row) === "depleted").length} detail="Остаток равен нулю" tone="warning" />
        </MetricStrip>
      ) : null}
      <CampaignSlotsPanel />
      <WinbackPilotDecisionPanel />
      <section className="ops-workspace xl:grid-cols-[minmax(0,1.38fr)_minmax(21rem,0.62fr)]">
        <Card><div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Промокоды" description="Срок, тип, значение и остаток подтверждаются сервером before/after." /><div className="flex gap-2"><input aria-label="Поиск промокодов" defaultValue={urlState.q} placeholder="Код" onBlur={(event) => replaceUrlState<PromoUrlState>({ q: event.target.value }, PROMO_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs" /><select aria-label="Состояние промокодов" value={urlState.state} onChange={(event) => replaceUrlState<PromoUrlState>({ state: event.target.value }, PROMO_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs"><option value="">Все состояния</option><option value="active">Активные</option><option value="expired">Истёкшие</option><option value="depleted">Исчерпанные</option></select></div></div><RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить промокоды" onRetry={resource.reload}>{rows.length ? <DataTable data={rows} columns={columns} empty="Промокоды не найдены" /> : resource.data ? <EmptyState description="По фильтрам нет промокодов." /> : null}</RouteBoundary></Card>
        <aside aria-label="Редактор промокода"><Card className="xl:sticky xl:top-[7.75rem]"><SectionTitle title={creating ? "Новый промокод" : selected ? `Промокод ${selected.code}` : "Редактор промокода"} description="Сохранение — L2 review; удаление — L3 с точным кодом." />{!draft ? <EmptyState title="Выберите промокод" description="Откройте строку или создайте новую запись." /> : <form className="space-y-3" onSubmit={submit}>{dirty ? <Badge tone="warning">Есть несохранённый черновик</Badge> : null}{formError ? <p role="alert" className="text-xs text-[color:var(--atlas-status-danger-text)]">{formError}</p> : null}<label className="block text-xs font-semibold">Код<input aria-label="Код промокода" value={draft.code} onChange={(event) => updateDraft({ code: event.target.value.toUpperCase() })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 font-mono" /></label><label className="block text-xs font-semibold">Тип<select aria-label="Тип промокода" value={draft.promoType} onChange={(event) => updateDraft({ promoType: event.target.value as PromoDraft["promoType"] })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="discount">Скидка, %</option><option value="days">Дополнительные дни</option></select></label><div className="grid grid-cols-2 gap-2"><label className="block text-xs font-semibold">Значение<input aria-label="Значение промокода" inputMode="numeric" value={draft.value} onChange={(event) => updateDraft({ value: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 tabular-nums" /></label><label className="block text-xs font-semibold">Осталось<input aria-label="Остаток промокода" inputMode="numeric" value={draft.usesLeft} onChange={(event) => updateDraft({ usesLeft: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 tabular-nums" /></label></div><label className="block text-xs font-semibold">Истекает<input aria-label="Срок промокода" type="datetime-local" value={draft.expiresAt} onChange={(event) => updateDraft({ expiresAt: event.target.value })} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3" /></label><div className="flex flex-wrap gap-2"><Button tone="primary" type="submit"><Save size={15} /> Проверить и сохранить</Button>{selected ? <Button tone="danger" type="button" onClick={remove}><Trash2 size={15} /> Удалить</Button> : null}</div></form>}</Card></aside>
      </section>
      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={reload} onCheckState={resource.reload} />
    </div>
  );
}
