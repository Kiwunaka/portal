"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw, Search } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, Progress, SectionTitle, type Tone } from "@/components/ui";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchFreeTier, type FreeTierUser } from "@/lib/admin-api/network";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type FreeUrlState = { q: string };
const FREE_URL_CODECS = { q: urlCodecs.string("") };

function finite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberText(value: unknown, suffix = "", digits = 2): string {
  const normalized = finite(value);
  return normalized === null ? "—" : `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: digits }).format(normalized)}${suffix}`;
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function tone(value: string): Tone {
  const normalized = value.toLowerCase();
  if (normalized === "over_cap") return "danger";
  if (normalized === "near_cap") return "warning";
  if (normalized === "ok") return "success";
  return "neutral";
}

function stateLabel(value: string): string {
  return { ok: "В пределах лимита", near_cap: "Близко к лимиту", over_cap: "Лимит исчерпан" }[value.toLowerCase()] || value || "Нет данных";
}

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return <div className="border-b border-[color:var(--atlas-border)] py-3 last:border-b-0"><dt className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">{label}</dt><dd className="mt-1 text-xl font-semibold tracking-tight tabular-nums">{value}</dd><p className="mt-1 text-[11px] text-[color:var(--atlas-text-muted)]">{hint}</p></div>;
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function FreeTierPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<FreeUrlState>(() => readUrlState(FREE_URL_CODECS));
  useEffect(() => subscribeToUrlState<FreeUrlState>(FREE_URL_CODECS, setUrlState), []);
  const load = useCallback((signal: AbortSignal) => fetchFreeTier(urlState.q, { signal }), [urlState.q]);
  const resource = useRouteResource(`free-tier:${urlState.q}`, load, { enabled: true, pollMs: 60_000 });

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.generatedAt || resource.data?.summary.generated_at || null,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const columns = useMemo<ColumnDef<FreeTierUser>[]>(() => [
    {
      header: "Пользователь",
      cell: ({ row }) => <a href={`/users?selected=${encodeURIComponent(String(row.original.tg_id))}`} className="rounded-sm font-semibold outline-none hover:underline focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]">{row.original.display_name || row.original.username || `Пользователь ${row.original.tg_id}`}<span className="block text-[11px] font-normal text-[color:var(--atlas-text-muted)]">Telegram ID {row.original.tg_id}</span></a>,
    },
    { header: "Состояние", cell: ({ row }) => <Badge tone={tone(row.original.state)}>{stateLabel(row.original.state)}</Badge> },
    { header: "Использовано", cell: ({ row }) => finite(row.original.used_gb) === null ? <span>—<span className="block text-[11px] text-[color:var(--atlas-text-muted)]">Нет данных</span></span> : <span className="tabular-nums">{numberText(row.original.used_gb, " ГиБ")}</span> },
    { header: "Осталось", cell: ({ row }) => finite(row.original.remaining_gb) === null ? <span>—<span className="block text-[11px] text-[color:var(--atlas-text-muted)]">Нет данных</span></span> : <span className="tabular-nums">{numberText(row.original.remaining_gb, " ГиБ")}</span> },
    { header: "Лимит", cell: ({ row }) => finite(row.original.used_pct) === null ? <span>—<span className="block text-[11px] text-[color:var(--atlas-text-muted)]">Нет данных</span></span> : <div className="min-w-28"><div className="mb-1 tabular-nums">{numberText(row.original.used_pct, "%", 1)}</div><Progress value={row.original.used_pct as number} tone={tone(row.original.state)} /></div> },
    { header: "Следующий сброс", cell: ({ row }) => <span>{dateText(row.original.next_reset_at || row.original.cycle_end)}{!(row.original.next_reset_at || row.original.cycle_end) ? <span className="block text-[11px] text-[color:var(--atlas-text-muted)]">Нет данных</span> : null}</span> },
  ], []);

  const summary = resource.data?.summary;
  const facts = resource.data?.facts;
  const usedPct = finite(summary?.used_pct);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]"><Badge tone={resource.error ? "warning" : "info"}>Только бесплатный контур</Badge><span>Платный пул в расчёты и строки этого экрана не входит.</span></div>
        <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку бесплатного контура" onRetry={resource.reload}>
        {resource.data ? (
          <div className="grid gap-4 lg:grid-cols-[minmax(300px,0.65fr)_minmax(0,1.35fr)]">
            <Card>
              <SectionTitle title="Темп расхода" description="Серверная сумма только по FREE-пользователям и их циклам." />
              <dl>
                <Metric label="Расход в день" value={numberText(summary?.burn_rate_gb_per_day, " ГиБ", 3)} hint={finite(summary?.burn_rate_gb_per_day) === null ? "Нет данных" : "По доступным rollup за текущие циклы"} />
                <Metric label="Использовано всего" value={numberText(summary?.used_gb, " ГиБ")} hint={`Из лимита ${numberText(summary?.limit_gb_total, " ГиБ")}`} />
                <Metric label="Лимит на пользователя" value={numberText(summary?.limit_gb_per_user ?? facts?.traffic_limit_gb, " ГиБ")} hint={finite(summary?.limit_gb_per_user ?? facts?.traffic_limit_gb) === null ? "Нет данных" : `Цикл: ${numberText(summary?.cycle_days ?? facts?.cycle_days, " дней", 0)}`} />
                <Metric label="Пользователи" value={numberText(summary?.free_users, "", 0)} hint={`С данными: ${numberText(summary?.sampled_users, "", 0)}`} />
              </dl>
              {usedPct === null ? <div className="mt-3 text-xs text-[color:var(--atlas-text-muted)]">Заполнение: — · Нет данных</div> : <div className="mt-3"><div className="mb-2 flex justify-between text-xs"><span>Заполнение общего лимита</span><strong className="tabular-nums">{numberText(usedPct, "%", 1)}</strong></div><Progress value={usedPct} tone={finite(summary?.over_cap_users) && Number(summary?.over_cap_users) > 0 ? "danger" : finite(summary?.near_cap_users) && Number(summary?.near_cap_users) > 0 ? "warning" : "success"} /></div>}
              <div className="mt-4 flex flex-wrap gap-2"><Badge tone="warning">Близко к лимиту: {numberText(summary?.near_cap_users, "", 0)}</Badge><Badge tone="danger">Исчерпали: {numberText(summary?.over_cap_users, "", 0)}</Badge></div>
              <p className="mt-4 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Пул: {facts?.node_pool || "— · Нет данных"}. Скорость: {numberText(facts?.speed_limit_mbps, " Мбит/с", 0)}. Устройств: {numberText(facts?.device_limit, "", 0)}.</p>
            </Card>

            <Card>
              <div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Пользователи бесплатного контура" description="Только строки FREE, без подмешивания платных пользователей." /><label className="relative block min-w-[240px] text-xs font-semibold">Поиск<span className="pointer-events-none absolute bottom-3 left-3 text-[color:var(--atlas-text-muted)]"><Search size={14} /></span><input type="search" aria-label="Поиск в бесплатном контуре" value={urlState.q} onChange={(event) => replaceUrlState<FreeUrlState>({ q: event.target.value }, FREE_URL_CODECS)} placeholder="Telegram ID или имя" className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] pl-9 pr-3 outline-none focus:border-[color:var(--atlas-focus)]" /></label></div>
              {resource.data.users.length ? <DataTable data={resource.data.users} columns={columns} empty="Нет пользователей" /> : <EmptyState description={urlState.q ? "По этому запросу бесплатные пользователи не найдены." : "Сервер вернул пустой FREE-список. Это не считается нулевым расходом."} />}
              <p className="mt-3 text-xs text-[color:var(--atlas-text-muted)]">Всего по серверному фильтру: {numberText(resource.data.total, "", 0)}. Источник: {summary?.source || "— · Нет данных"}.</p>
            </Card>
          </div>
        ) : null}
      </RouteBoundary>
    </div>
  );
}
