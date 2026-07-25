"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Cable, CreditCard, Percent, RefreshCw, UsersRound } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ColumnDef } from "@tanstack/react-table";

import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, MetricCell, MetricStrip, SectionTitle } from "@/components/ui";
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

const STAGE_METRICS: Array<{ value: string; label: string; key: keyof FunnelSource; stageKey: string }> = [
  { value: "visitors", label: "Посетители", key: "visitors", stageKey: "site_to_app" },
  { value: "app_opens", label: "Открыли кабинет/бот", key: "app_opens", stageKey: "site_to_app" },
  { value: "checkouts", label: "Начали оплату", key: "checkouts", stageKey: "app_to_checkout" },
  { value: "paid", label: "Оплатили", key: "paid", stageKey: "checkout_to_paid" },
  { value: "connected", label: "Подключились", key: "connected", stageKey: "paid_to_connected" },
];

export function FunnelPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<FunnelUrlState>(() => readUrlState(FUNNEL_URL_CODECS));
  useEffect(() => subscribeToUrlState<FunnelUrlState>(FUNNEL_URL_CODECS, setUrlState), []);
  const load = useCallback((signal: AbortSignal) => fetchFunnel(urlState.range, { signal }), [urlState.range]);
  const resource = useRouteResource(`funnel:${urlState.range}`, load, { enabled: true, pollMs: 60_000 });

  useEffect(() => {
    onShellStatus?.({ api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok", session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing", oldestRequiredSourceAt: resource.data?.period.from || null });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const sources = useMemo(() => resource.data?.by_source || [], [resource.data?.by_source]);
  const filteredSources = useMemo(() => sources.filter((row) => !urlState.source || row.source === urlState.source), [sources, urlState.source]);
  const selectedMetric = STAGE_METRICS.find((item) => item.value === urlState.stage)
    || STAGE_METRICS.find((item) => item.value !== "visitors" && item.stageKey === urlState.stage)
    || null;
  const filteredMetrics = useMemo(() => STAGE_METRICS.filter((metric) => !selectedMetric || metric.value === selectedMetric.value), [selectedMetric]);
  const filteredStages = useMemo(() => (resource.data?.stages || []).filter((stage) => !urlState.stage || stage.key === (selectedMetric?.stageKey || urlState.stage)), [resource.data?.stages, selectedMetric, urlState.stage]);
  const chartRows = useMemo(() => {
    if (urlState.source) {
      const source = filteredSources[0];
      return source ? filteredMetrics.map((metric) => ({ label: metric.label, value: finite(source[metric.key]) })) : [];
    }
    return filteredStages.map((stage) => ({ label: stage.label, value: finite(stage.reached_next) }));
  }, [filteredMetrics, filteredSources, filteredStages, urlState.source]);

  const stageColumns = useMemo<ColumnDef<FunnelStage>[]>(() => [
    { header: "Переход", accessorKey: "label" },
    { header: "Вошли", cell: ({ row }) => <NumberValue value={row.original.entered} /> },
    { header: "Прошли дальше", cell: ({ row }) => <NumberValue value={row.original.reached_next} /> },
    { header: "Потеря", cell: ({ row }) => <NumberValue value={row.original.dropped} /> },
    { header: "Конверсия", cell: ({ row }) => <NumberValue value={row.original.conversion_pct} suffix="%" /> },
  ], []);
  const sourceColumns = useMemo<ColumnDef<FunnelSource>[]>(() => [
    { header: "Источник", cell: ({ row }) => <span className="font-semibold">{row.original.source || "— · Нет данных"}</span> },
    ...filteredMetrics.map((metric): ColumnDef<FunnelSource> => ({ header: metric.label, cell: ({ row }) => <NumberValue value={row.original[metric.key]} /> })),
  ], [filteredMetrics]);
  const aggregate = (key: keyof FunnelSource): number | null => {
    if (!filteredSources.length || filteredSources.some((row) => finite(row[key]) === null)) return null;
    return filteredSources.reduce((sum, row) => sum + Number(row[key]), 0);
  };
  const visitors = aggregate("visitors");
  const paid = aggregate("paid");
  const connected = aggregate("connected");
  const conversion = visitors !== null && connected !== null && visitors > 0
    ? connected / visitors * 100
    : null;

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar"><div className="flex flex-wrap gap-2 text-xs"><Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>{resource.error ? "Источник воронки отвечает с ошибкой" : resource.data ? "Воронка рассчитана" : "Воронка ещё не получена"}</Badge><span className="text-[color:var(--atlas-text-soft)]">Агрегаты не являются бухгалтерской сверкой.</span></div><Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button></div>

      {resource.data ? (
        <MetricStrip label="Сводка воронки">
          <MetricCell icon={<UsersRound aria-hidden="true" size={17} />} label="Посетители" value={visitors === null ? <MissingData /> : valueText(visitors)} detail={urlState.source || "Все источники"} tone="info" />
          <MetricCell icon={<CreditCard aria-hidden="true" size={17} />} label="Оплатили" value={paid === null ? <MissingData /> : valueText(paid)} detail={`Диапазон: ${urlState.range}`} tone="success" />
          <MetricCell icon={<Cable aria-hidden="true" size={17} />} label="Подключились" value={connected === null ? <MissingData /> : valueText(connected)} detail="Подтверждённое подключение" tone="success" />
          <MetricCell icon={<Percent aria-hidden="true" size={17} />} label="До подключения" value={conversion === null ? <MissingData /> : valueText(conversion, "%")} detail="Подключились / посетители" tone={conversion !== null && conversion < 20 ? "warning" : "neutral"} />
        </MetricStrip>
      ) : null}

      <Card>
        <div className="flex flex-wrap items-end justify-between gap-3"><SectionTitle title="Воронка денег и подключения" description="График и таблицы используют один диапазон, источник и выбранную стадию. Сырые события и JSON не выводятся." /><div className="grid gap-2 sm:grid-cols-3"><label className="text-xs font-semibold">Диапазон<select aria-label="Диапазон воронки" value={urlState.range} onChange={(event) => replaceUrlState<FunnelUrlState>({ range: event.target.value as FunnelRange }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="7d">7 дней</option><option value="30d">30 дней</option><option value="90d">90 дней</option></select></label><label className="text-xs font-semibold">Источник<select aria-label="Источник воронки" value={urlState.source} onChange={(event) => replaceUrlState<FunnelUrlState>({ source: event.target.value }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все источники</option>{sources.map((row) => <option key={row.source} value={row.source}>{row.source}</option>)}</select></label><label className="text-xs font-semibold">Стадия<select aria-label="Стадия воронки" value={urlState.stage} onChange={(event) => replaceUrlState<FunnelUrlState>({ stage: event.target.value }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все стадии</option>{urlState.source ? STAGE_METRICS.map((metric) => <option key={metric.value} value={metric.value}>{metric.label}</option>) : (resource.data?.stages || []).map((stage) => <option key={stage.key} value={stage.key}>{stage.label}</option>)}</select></label></div></div>
        <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить воронку" onRetry={resource.reload}>
          {chartRows.length ? <div aria-label="График воронки" data-source={urlState.source || "all"} data-stage={urlState.stage || "all"} className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartRows}><CartesianGrid stroke="var(--atlas-border)" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="label" tick={{ fill: "var(--atlas-text-muted)", fontSize: 10 }} interval={0} /><YAxis tick={{ fill: "var(--atlas-text-muted)", fontSize: 11 }} /><Tooltip formatter={(value) => [finite(value) === null ? "— · Нет данных" : valueText(value), "Количество"]} /><Bar dataKey="value" fill="var(--atlas-primary)" radius={[3, 3, 0, 0]} /></BarChart></ResponsiveContainer></div> : resource.data ? <EmptyState description="Для выбранных фильтров нет агрегатов. Это не равно нулевой конверсии." /> : null}
        </RouteBoundary>
      </Card>

      <section className="ops-workspace xl:grid-cols-[minmax(0,1.32fr)_minmax(20rem,0.68fr)]">
        <Card><SectionTitle title="Стадии" description="Переход, потери и конверсия рассчитаны сервером." />{filteredStages.length ? <DataTable data={filteredStages} columns={stageColumns} empty="Нет стадий" /> : resource.data ? <EmptyState description="Для выбранной стадии нет данных." /> : <MissingData />}</Card>
        <aside aria-label="Причины потерь"><Card><SectionTitle title="Причины потерь" />{resource.data?.drop_reasons.length ? <dl className="divide-y divide-[color:var(--atlas-border)]">{resource.data.drop_reasons.map((row) => <div key={row.reason} className="flex justify-between gap-3 py-2 text-xs"><dt>{row.reason}</dt><dd><NumberValue value={row.count} /></dd></div>)}</dl> : resource.data ? <EmptyState description="Причины не рассчитаны." className="min-h-0" /> : <MissingData />}</Card></aside>
      </section>

      <Card><SectionTitle title="Источники" description="Те же range/source/stage отражены в URL и применены к аналитическому полотну." />{filteredSources.length ? <DataTable data={filteredSources} columns={sourceColumns} empty="Нет источников" /> : resource.data ? <EmptyState description="По выбранному источнику нет данных." /> : <MissingData />}</Card>
    </div>
  );
}
