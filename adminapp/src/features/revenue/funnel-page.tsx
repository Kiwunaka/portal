"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ColumnDef } from "@tanstack/react-table";

import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, SectionTitle } from "@/components/ui";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchFunnel, type FunnelRange, type FunnelSource, type FunnelStage } from "@/lib/admin-api/revenue";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type FunnelUrlState = { range: FunnelRange; source: string; stage: string };
const FUNNEL_URL_CODECS = { range: urlCodecs.enum(["7d", "30d", "90d"] as const, "30d"), source: urlCodecs.string(""), stage: urlCodecs.string("") };

function finite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function valueText(value: unknown, suffix = ""): string {
  const normalized = finite(value);
  return normalized === null ? "—" : `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 }).format(normalized)}${suffix}`;
}

function NumberValue({ value, suffix = "" }: { value: unknown; suffix?: string }) {
  return finite(value) === null ? <MissingData /> : <span className="tabular-nums">{valueText(value, suffix)}</span>;
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

const STAGE_METRICS: Array<{ value: string; label: string; key: keyof FunnelSource }> = [
  { value: "visitors", label: "Посетители", key: "visitors" },
  { value: "app_opens", label: "Открыли кабинет/бот", key: "app_opens" },
  { value: "checkouts", label: "Начали оплату", key: "checkouts" },
  { value: "paid", label: "Оплатили", key: "paid" },
  { value: "connected", label: "Подключились", key: "connected" },
];

export function FunnelPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<FunnelUrlState>(() => readUrlState(FUNNEL_URL_CODECS));
  useEffect(() => subscribeToUrlState<FunnelUrlState>(FUNNEL_URL_CODECS, setUrlState), []);
  const load = useCallback((signal: AbortSignal) => fetchFunnel(urlState.range, { signal }), [urlState.range]);
  const resource = useRouteResource(`funnel:${urlState.range}`, load, { enabled: true, pollMs: 60_000 });

  useEffect(() => {
    onShellStatus?.({ api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok", session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing", oldestRequiredSourceAt: resource.data?.period.from || null });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const sources = resource.data?.by_source || [];
  const filteredSources = useMemo(() => sources.filter((row) => !urlState.source || row.source === urlState.source), [sources, urlState.source]);
  const selectedMetric = STAGE_METRICS.find((item) => item.value === urlState.stage) || null;
  const chartRows = useMemo(() => {
    if (urlState.source) {
      const source = sources.find((row) => row.source === urlState.source);
      return source ? STAGE_METRICS.filter((metric) => !selectedMetric || metric.value === selectedMetric.value).map((metric) => ({ label: metric.label, value: finite(source[metric.key]) })) : [];
    }
    return (resource.data?.stages || []).filter((stage) => !urlState.stage || stage.key === urlState.stage).map((stage) => ({ label: stage.label, value: finite(stage.reached_next) }));
  }, [resource.data?.stages, selectedMetric, sources, urlState.source, urlState.stage]);

  const stageColumns = useMemo<ColumnDef<FunnelStage>[]>(() => [
    { header: "Переход", accessorKey: "label" },
    { header: "Вошли", cell: ({ row }) => <NumberValue value={row.original.entered} /> },
    { header: "Прошли дальше", cell: ({ row }) => <NumberValue value={row.original.reached_next} /> },
    { header: "Потеря", cell: ({ row }) => <NumberValue value={row.original.dropped} /> },
    { header: "Конверсия", cell: ({ row }) => <NumberValue value={row.original.conversion_pct} suffix="%" /> },
  ], []);
  const sourceColumns = useMemo<ColumnDef<FunnelSource>[]>(() => [
    { header: "Источник", cell: ({ row }) => <span className="font-semibold">{row.original.source || "— · Нет данных"}</span> },
    ...STAGE_METRICS.map((metric): ColumnDef<FunnelSource> => ({ header: metric.label, cell: ({ row }) => <NumberValue value={row.original[metric.key]} /> })),
  ], []);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex flex-wrap gap-2 text-xs"><Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>{resource.error ? "Источник воронки отвечает с ошибкой" : resource.data ? "Воронка рассчитана" : "Воронка ещё не получена"}</Badge><span className="text-[color:var(--atlas-text-soft)]">Агрегаты не являются бухгалтерской сверкой.</span></div><Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button></div>

      <Card>
        <div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Воронка денег и подключения" description="График и таблицы используют один диапазон, источник и выбранную стадию. Сырые события и JSON не выводятся." /><div className="grid gap-2 sm:grid-cols-3"><label className="text-xs font-semibold">Диапазон<select aria-label="Диапазон воронки" value={urlState.range} onChange={(event) => replaceUrlState<FunnelUrlState>({ range: event.target.value as FunnelRange }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="7d">7 дней</option><option value="30d">30 дней</option><option value="90d">90 дней</option></select></label><label className="text-xs font-semibold">Источник<select aria-label="Источник воронки" value={urlState.source} onChange={(event) => replaceUrlState<FunnelUrlState>({ source: event.target.value }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все источники</option>{sources.map((row) => <option key={row.source} value={row.source}>{row.source}</option>)}</select></label><label className="text-xs font-semibold">Стадия<select aria-label="Стадия воронки" value={urlState.stage} onChange={(event) => replaceUrlState<FunnelUrlState>({ stage: event.target.value }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все стадии</option>{urlState.source ? STAGE_METRICS.map((metric) => <option key={metric.value} value={metric.value}>{metric.label}</option>) : (resource.data?.stages || []).map((stage) => <option key={stage.key} value={stage.key}>{stage.label}</option>)}</select></label></div></div>
        <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить воронку" onRetry={resource.reload}>
          {chartRows.length ? <div aria-label="График воронки" data-source={urlState.source || "all"} data-stage={urlState.stage || "all"} className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartRows}><CartesianGrid stroke="var(--atlas-border)" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="label" tick={{ fill: "var(--atlas-text-muted)", fontSize: 10 }} interval={0} /><YAxis tick={{ fill: "var(--atlas-text-muted)", fontSize: 11 }} /><Tooltip formatter={(value) => [finite(value) === null ? "— · Нет данных" : valueText(value), "Количество"]} /><Bar dataKey="value" fill="var(--atlas-primary)" radius={[3, 3, 0, 0]} /></BarChart></ResponsiveContainer></div> : resource.data ? <EmptyState description="Для выбранных фильтров нет агрегатов. Это не равно нулевой конверсии." /> : null}
        </RouteBoundary>
      </Card>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
        <Card><SectionTitle title="Стадии" description="Переход, потери и конверсия рассчитаны сервером." />{resource.data?.stages.length ? <DataTable data={resource.data.stages.filter((row) => !urlState.stage || urlState.source || row.key === urlState.stage)} columns={stageColumns} empty="Нет стадий" /> : resource.data ? <EmptyState description="Стадии не пришли от источника." /> : <MissingData />}</Card>
        <aside aria-label="Причины потерь"><Card><SectionTitle title="Причины потерь" />{resource.data?.drop_reasons.length ? <dl className="divide-y divide-[color:var(--atlas-border)]">{resource.data.drop_reasons.map((row) => <div key={row.reason} className="flex justify-between gap-3 py-2 text-xs"><dt>{row.reason}</dt><dd><NumberValue value={row.count} /></dd></div>)}</dl> : resource.data ? <EmptyState description="Причины не рассчитаны." className="min-h-0" /> : <MissingData />}</Card></aside>
      </section>

      <Card><SectionTitle title="Источники" description="Те же range/source/stage отражены в URL и применены к аналитическому полотну." />{filteredSources.length ? <DataTable data={filteredSources} columns={sourceColumns} empty="Нет источников" /> : resource.data ? <EmptyState description="По выбранному источнику нет данных." /> : <MissingData />}</Card>
    </div>
  );
}
