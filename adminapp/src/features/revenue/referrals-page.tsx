"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CircleCheck, Clock3, Gift, Play, RefreshCw, TriangleAlert } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import type { ActionIntentRequest } from "@/lib/admin-api/actions";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchReferrals, type ReferralRow } from "@/lib/admin-api/revenue";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type ReferralUrlState = { status: string; q: string; selected: string | null };
const REFERRAL_URL_CODECS = { status: urlCodecs.string("rewarded"), q: urlCodecs.string(""), selected: urlCodecs.optionalString() };

const BASIS_PRIORITY: Record<string, number> = { reward_ready: 0, rejected_missing_user: 1, rejected_referrer_inactive: 2, rejected_no_activity: 3, waiting_for_activity: 4, waiting_ready_at: 5 };
function basisLabel(value: string): string {
  return ({ reward_ready: "Готово к награде", rejected_missing_user: "Нет пользователя", rejected_referrer_inactive: "Реферер неактивен", rejected_no_activity: "Нет активности", waiting_for_activity: "Ждём активность", waiting_ready_at: "Ждём готовность", rewarded: "Награждён", rejected: "Отклонён" } as Record<string, string>)[value] || value || "—";
}
function tone(value: string): Tone {
  if (["reward_ready", "rewarded"].includes(value)) return "success";
  if (value.startsWith("rejected")) return "danger";
  if (value.startsWith("waiting")) return "warning";
  return "neutral";
}
function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}
function isAccessDenied(error: AdminApiError | null): boolean { return Boolean(error && (error.status === 401 || error.status === 403)); }

export function ReferralsPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<ReferralUrlState>(() => readUrlState(REFERRAL_URL_CODECS));
  const [forceWithoutActivity, setForceWithoutActivity] = useState(false);
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  useEffect(() => subscribeToUrlState<ReferralUrlState>(REFERRAL_URL_CODECS, setUrlState), []);
  const loadQueue = useCallback((signal: AbortSignal) => fetchReferrals("pending", { signal }), []);
  const queue = useRouteResource("referrals:pending", loadQueue, { enabled: true, pollMs: 60_000 });
  const historyStatus = urlState.status === "pending" ? "" : urlState.status;
  const loadHistory = useCallback((signal: AbortSignal) => fetchReferrals(historyStatus, { signal }), [historyStatus]);
  const history = useRouteResource(`referrals:history:${historyStatus}`, loadHistory, { enabled: true, pollMs: 60_000 });

  useEffect(() => {
    const errors = [queue.error, history.error].filter(Boolean);
    const hasData = Boolean(queue.data || history.data);
    onShellStatus?.({ api: errors.length ? hasData ? "degraded" : "failed" : queue.loading || history.loading ? "missing" : "ok", session: errors.some((error) => isAccessDenied(error)) ? "failed" : hasData ? "ok" : errors.length ? "unavailable" : "missing", oldestRequiredSourceAt: [...(queue.data || []), ...(history.data || [])].map((row) => row.queued_at).filter((value): value is string => Boolean(value)).sort().at(0) || null });
  }, [history.data, history.error, history.loading, onShellStatus, queue.data, queue.error, queue.loading]);

  const queueRows = useMemo(() => [...(queue.data || [])].filter((row) => !urlState.q || `${row.order_id} ${row.referrer_tg_id} ${row.referred_tg_id}`.toLowerCase().includes(urlState.q.toLowerCase())).sort((left, right) => (left.basis ? BASIS_PRIORITY[left.basis] ?? 99 : 99) - (right.basis ? BASIS_PRIORITY[right.basis] ?? 99 : 99) || String(left.ready_at || "").localeCompare(String(right.ready_at || "")) || left.id - right.id), [queue.data, urlState.q]);
  const historyRows = useMemo(() => (history.data || []).filter((row) => row.status !== "pending" && (!urlState.q || `${row.order_id} ${row.referrer_tg_id} ${row.referred_tg_id}`.toLowerCase().includes(urlState.q.toLowerCase()))), [history.data, urlState.q]);
  const selectedId = Number(urlState.selected);
  const selected = [...queueRows, ...historyRows].find((row) => row.id === selectedId) || null;
  const columns = useMemo<ColumnDef<ReferralRow>[]>(() => [
    { header: "Очередь", cell: ({ row }) => <button className="text-left font-semibold hover:underline" onClick={() => replaceUrlState<ReferralUrlState>({ selected: String(row.original.id) }, REFERRAL_URL_CODECS)}>#{row.original.id}<span className="block font-normal text-[11px] text-[color:var(--atlas-text-muted)]">{row.original.order_id}</span></button> },
    { header: "Реферер", cell: ({ row }) => <span className="tabular-nums">{row.original.referrer_tg_id}</span> },
    { header: "Приглашённый", cell: ({ row }) => <span className="tabular-nums">{row.original.referred_tg_id}</span> },
    { header: "Основание", cell: ({ row }) => row.original.basis ? <Badge tone={tone(row.original.basis)}>{basisLabel(row.original.basis)}</Badge> : <MissingData /> },
    { header: "Готово с", cell: ({ row }) => row.original.ready_at ? dateText(row.original.ready_at) : <MissingData /> },
    { header: "Статус", cell: ({ row }) => row.original.status ? <Badge tone={tone(row.original.status)}>{basisLabel(row.original.status)}</Badge> : <MissingData /> },
  ], []);

  function reloadAll() { queue.reload(); history.reload(); }
  function processQueue() {
    setRequest({ action: "referral.process", target: { type: "referral_queue", id: "ready" }, payload: { limit: 100, force_without_activity: forceWithoutActivity }, endpoint: "/api/admin/referrals/process", method: "POST" });
    setDialogOpen(true);
  }

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar"><div className="flex gap-2 text-xs"><Badge tone={queue.error || history.error ? "warning" : queue.data || history.data ? "success" : "neutral"}>{queue.error || history.error ? "Часть реферальных источников недоступна" : queue.data || history.data ? "Реферальные данные получены" : "Реферальные данные ещё не получены"}</Badge><span className="text-[color:var(--atlas-text-soft)]">Очередь сортируется: основание → ready_at → ID.</span></div><Button tone="secondary" disabled={queue.refreshing || history.refreshing} onClick={reloadAll}><RefreshCw size={15} className={queue.refreshing || history.refreshing ? "animate-spin" : ""} /> Обновить</Button></div>
      <MetricStrip label="Сводка реферальной очереди">
        <MetricCell icon={<Gift aria-hidden="true" size={17} />} label="В очереди" value={queue.data === null ? <MissingData /> : queueRows.length} detail="С учётом текущего поиска" tone={queueRows.length ? "info" : "success"} />
        <MetricCell icon={<CircleCheck aria-hidden="true" size={17} />} label="Готовы к награде" value={queue.data === null ? <MissingData /> : queueRows.filter((row) => row.basis === "reward_ready").length} detail="Можно обработать сейчас" tone={queueRows.some((row) => row.basis === "reward_ready") ? "success" : "neutral"} />
        <MetricCell icon={<Clock3 aria-hidden="true" size={17} />} label="Ожидают условия" value={queue.data === null ? <MissingData /> : queueRows.filter((row) => String(row.basis || "").startsWith("waiting")).length} detail="Активность или ready_at" tone="warning" />
        <MetricCell icon={<TriangleAlert aria-hidden="true" size={17} />} label="Отклонены в истории" value={history.data === null ? <MissingData /> : historyRows.filter((row) => String(row.status || row.basis || "").startsWith("rejected")).length} detail="По выбранному фильтру истории" tone={historyRows.some((row) => String(row.status || row.basis || "").startsWith("rejected")) ? "warning" : "neutral"} />
      </MetricStrip>
      <section className="ops-workspace xl:grid-cols-[minmax(0,1.38fr)_minmax(21rem,0.62fr)]">
        <div className="space-y-4">
          <Card><div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Очередь решений" description="Основание рассчитано сервером; интерфейс не создаёт новый платёжный механизм." /><div className="flex flex-wrap items-center gap-2"><input aria-label="Поиск рефералов" defaultValue={urlState.q} placeholder="order или Telegram ID" onBlur={(event) => replaceUrlState<ReferralUrlState>({ q: event.target.value }, REFERRAL_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs" /><label className="flex min-h-10 items-center gap-2 text-xs font-semibold"><input type="checkbox" checked={forceWithoutActivity} onChange={(event) => setForceWithoutActivity(event.target.checked)} /> Без активности</label><Button tone="primary" disabled={!queueRows.length} onClick={processQueue}><Play size={15} /> Проверить и обработать</Button></div></div><RouteBoundary loading={queue.loading} refreshing={queue.refreshing} error={queue.error} hasData={queue.data !== null} retryLabel="Повторить очередь" onRetry={queue.reload}>{queueRows.length ? <DataTable data={queueRows} columns={columns} empty="Очередь пуста" /> : queue.data ? <EmptyState title="Очередь пуста" description="Готовых pending-записей нет. Это не подтверждает отсутствие истории." /> : null}</RouteBoundary></Card>
          <Card><div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="История" description="Обработанные решения остаются отдельным блоком и не скрываются сбоем очереди." /><select aria-label="Статус истории рефералов" value={urlState.status} onChange={(event) => replaceUrlState<ReferralUrlState>({ status: event.target.value }, REFERRAL_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs"><option value="rewarded">Награждённые</option><option value="">Все решения</option><option value="rejected_no_activity">Без активности</option><option value="rejected_missing_user">Нет пользователя</option><option value="rejected_referrer_inactive">Реферер неактивен</option></select></div><RouteBoundary loading={history.loading} refreshing={history.refreshing} error={history.error} hasData={history.data !== null} retryLabel="Повторить историю" onRetry={history.reload}>{historyRows.length ? <DataTable data={historyRows} columns={columns} empty="История пуста" /> : history.data ? <EmptyState description="По выбранному статусу нет обработанных решений." /> : null}</RouteBoundary></Card>
        </div>
        <aside aria-label="Карточка реферального решения"><Card className="xl:sticky xl:top-[7.75rem]"><SectionTitle title={selected ? `Запись #${selected.id}` : "Карточка решения"} description="Только безопасные идентификаторы, статус и основание; raw meta не возвращается." />{selected ? <dl className="grid grid-cols-2 gap-3 text-xs"><dt className="text-[color:var(--atlas-text-soft)]">Заказ</dt><dd className="font-semibold">{selected.order_id}</dd><dt className="text-[color:var(--atlas-text-soft)]">Реферер</dt><dd className="tabular-nums">{selected.referrer_tg_id}</dd><dt className="text-[color:var(--atlas-text-soft)]">Приглашённый</dt><dd className="tabular-nums">{selected.referred_tg_id}</dd><dt className="text-[color:var(--atlas-text-soft)]">Основание</dt><dd>{selected.basis ? basisLabel(selected.basis) : <MissingData />}</dd><dt className="text-[color:var(--atlas-text-soft)]">Поставлено</dt><dd>{selected.queued_at ? dateText(selected.queued_at) : "— · Нет данных"}</dd><dt className="text-[color:var(--atlas-text-soft)]">Обработано</dt><dd>{selected.processed_at ? dateText(selected.processed_at) : "— · Нет данных"}</dd></dl> : <EmptyState title="Выберите запись" description="Откройте строку очереди или истории." />}</Card></aside>
      </section>
      <ActionIntentDialog open={dialogOpen} request={request} onOpenChange={(open) => { setDialogOpen(open); if (!open) setRequest(null); }} onKnownOutcome={reloadAll} onCheckState={reloadAll} />
    </div>
  );
}
