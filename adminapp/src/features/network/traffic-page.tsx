"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Database, Network, RefreshCw, Server, Waypoints } from "lucide-react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ColumnDef } from "@tanstack/react-table";

import { MISSING_DATA_TEXT, MissingData } from "@/components/ops/missing-data";
import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, MetricCell, MetricStrip, SectionTitle } from "@/components/ui";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchTrafficSummary, type TrafficRange, type TrafficRow } from "@/lib/admin-api/network";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type TrafficUrlState = { range: TrafficRange; node: string };
type TrafficChartPoint = { date: string; label: string; [key: string]: string | number | null };

const TRAFFIC_URL_CODECS = {
  range: urlCodecs.enum(["7d", "30d", "90d"] as const, "30d"),
  node: urlCodecs.string(""),
};

const MISSING_POOL = "__missing_pool__";
const POOL_STROKES = [
  "var(--atlas-primary)",
  "var(--atlas-status-warning-text)",
  "var(--atlas-status-success-text)",
  "var(--atlas-status-danger-text)",
];

function finite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberText(value: unknown, digits = 2): string {
  const normalized = finite(value);
  return normalized === null ? "—" : new Intl.NumberFormat("ru-RU", { maximumFractionDigits: digits }).format(normalized);
}

function MissingNumber({ value, suffix = "" }: { value: unknown; suffix?: string }) {
  const normalized = finite(value);
  return normalized === null ? <MissingData /> : <span className="tabular-nums">{numberText(normalized)}{suffix}</span>;
}

function poolCode(row: TrafficRow): string {
  return row.pool_code.trim() || MISSING_POOL;
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function TrafficPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<TrafficUrlState>(() => readUrlState(TRAFFIC_URL_CODECS));
  useEffect(() => subscribeToUrlState<TrafficUrlState>(TRAFFIC_URL_CODECS, setUrlState), []);

  const load = useCallback((signal: AbortSignal) => fetchTrafficSummary(urlState.range, { signal }), [urlState.range]);
  const resource = useRouteResource(`traffic:${urlState.range}`, load, { enabled: true, pollMs: 60_000 });

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.from || null,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const nodes = useMemo(() => [...new Set((resource.data?.rows || []).map((row) => row.node_code).filter(Boolean))].sort(), [resource.data]);
  const rows = useMemo(() => (resource.data?.rows || []).filter((row) => !urlState.node || row.node_code === urlState.node), [resource.data, urlState.node]);
  const poolSeries = useMemo(() => [...new Set(rows.map(poolCode))].sort().map((code, index) => ({
    code,
    dataKey: `pool_${index}`,
    label: code === MISSING_POOL ? MISSING_DATA_TEXT : code,
    stroke: POOL_STROKES[index % POOL_STROKES.length],
  })), [rows]);
  const chartData = useMemo<TrafficChartPoint[]>(() => {
    const dates = new Map<string, TrafficRow[]>();
    for (const row of rows) dates.set(row.date, [...(dates.get(row.date) || []), row]);
    return [...dates.entries()].sort(([left], [right]) => left.localeCompare(right)).map(([date, dayRows]) => {
      const point: TrafficChartPoint = {
        date,
        label: new Date(`${date}T00:00:00Z`).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" }),
      };
      for (const series of poolSeries) {
        const values = dayRows.filter((row) => poolCode(row) === series.code).map((row) => finite(row.traffic_gb));
        point[series.dataKey] = !values.length || values.some((value) => value === null)
          ? null
          : values.reduce<number>((sum, value) => sum + (value as number), 0);
      }
      return point;
    });
  }, [poolSeries, rows]);
  const nodeBreakdown = useMemo(() => {
    const values = new Map<string, number | null>();
    for (const row of rows) {
      const value = finite(row.traffic_gb);
      const previous = values.get(row.node_code);
      values.set(row.node_code, value === null || previous === null ? null : (previous || 0) + value);
    }
    return [...values.entries()].sort(([left], [right]) => left.localeCompare(right));
  }, [rows]);
  const poolBreakdown = useMemo(() => {
    const values = new Map<string, number | null>();
    for (const row of rows) {
      const value = finite(row.traffic_gb);
      const code = poolCode(row);
      const previous = values.get(code);
      values.set(code, value === null || previous === null ? null : (previous || 0) + value);
    }
    return [...values.entries()].sort(([left], [right]) => left.localeCompare(right));
  }, [rows]);

  const columns = useMemo<ColumnDef<TrafficRow>[]>(() => [
    { header: "Дата", cell: ({ row }) => <time dateTime={row.original.date}>{new Date(`${row.original.date}T00:00:00Z`).toLocaleDateString("ru-RU")}</time> },
    { header: "Нода", cell: ({ row }) => row.original.node_code ? <span className="font-semibold uppercase">{row.original.node_code}</span> : <MissingData /> },
    { header: "Контур", cell: ({ row }) => row.original.pool_code || <MissingData /> },
    { header: "Трафик", cell: ({ row }) => <MissingNumber value={row.original.traffic_gb} suffix=" ГиБ" /> },
    { header: "Измерения", cell: ({ row }) => <MissingNumber value={row.original.samples} /> },
  ], []);

  const trafficTotal = rows.length && rows.every((row) => finite(row.traffic_gb) !== null)
    ? rows.reduce((sum, row) => sum + Number(row.traffic_gb), 0)
    : null;
  const sampleTotal = rows.length && rows.every((row) => finite(row.samples) !== null)
    ? rows.reduce((sum, row) => sum + Number(row.samples), 0)
    : null;
  const refreshing = resource.refreshing;
  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>{resource.error ? "Источник отвечает с ошибкой" : resource.data ? "Сводка трафика получена" : "Сводка трафика ещё не получена"}</Badge>
          <span>{resource.updatedAt ? `Обновлено ${new Date(resource.updatedAt).toLocaleString("ru-RU")}` : "Данные ещё не получены"}</span>
        </div>
        <Button tone="secondary" disabled={resource.loading || refreshing} onClick={resource.reload}><RefreshCw size={15} className={refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      {resource.data ? (
        <MetricStrip label="Сводка трафика">
          <MetricCell icon={<Network aria-hidden="true" size={17} />} label="Трафик" value={trafficTotal === null ? <MissingData /> : `${numberText(trafficTotal)} ГиБ`} detail={`Диапазон: ${urlState.range}`} tone="success" />
          <MetricCell icon={<Server aria-hidden="true" size={17} />} label="Ноды" value={rows.length ? new Set(rows.map((row) => row.node_code)).size : <MissingData />} detail={urlState.node ? `Фильтр: ${urlState.node.toUpperCase()}` : "Все ноды"} tone="info" />
          <MetricCell icon={<Waypoints aria-hidden="true" size={17} />} label="Контуры" value={rows.length ? poolSeries.length : <MissingData />} detail="Раздельные серии" tone="info" />
          <MetricCell icon={<Database aria-hidden="true" size={17} />} label="Измерения" value={sampleTotal === null ? <MissingData /> : numberText(sampleTotal, 0)} detail="Сумма серверных samples" tone="neutral" />
        </MetricStrip>
      ) : null}

      <Card>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <SectionTitle title="Трафик по дням" description="Один диапазон и одна нода управляют графиком, разбивками и исходной таблицей; каждый контур остаётся отдельной серией." />
          <div className="grid gap-2 sm:grid-cols-2">
            <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">Диапазон
              <select aria-label="Диапазон трафика" value={urlState.range} onChange={(event) => replaceUrlState<TrafficUrlState>({ range: event.target.value as TrafficRange }, TRAFFIC_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 outline-none focus:border-[color:var(--atlas-focus)]">
                <option value="7d">7 дней</option><option value="30d">30 дней</option><option value="90d">90 дней</option>
              </select>
            </label>
            <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">Нода
              <select aria-label="Нода трафика" value={urlState.node} onChange={(event) => replaceUrlState<TrafficUrlState>({ node: event.target.value }, TRAFFIC_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 outline-none focus:border-[color:var(--atlas-focus)]">
                <option value="">Все ноды</option>{nodes.map((node) => <option key={node} value={node}>{node.toUpperCase()}</option>)}
              </select>
            </label>
          </div>
        </div>
        <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку трафика" onRetry={resource.reload}>
          {chartData.length ? (
            <div aria-label="График трафика" data-pools={poolSeries.map((series) => series.code).join(",")} className="h-72 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 8, right: 14, left: 0, bottom: 4 }}>
                  <CartesianGrid stroke="var(--atlas-border)" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fill: "var(--atlas-text-muted)", fontSize: 11 }} />
                  <YAxis tick={{ fill: "var(--atlas-text-muted)", fontSize: 11 }} width={48} />
                  <Tooltip formatter={(value, name) => [finite(value) === null ? MISSING_DATA_TEXT : `${numberText(value)} ГиБ`, String(name)]} />
                  <Legend />
                  {poolSeries.map((series) => <Line key={series.code} type="monotone" dataKey={series.dataKey} name={series.label} stroke={series.stroke} strokeWidth={2} dot={false} connectNulls={false} />)}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : resource.data ? <EmptyState description="В выбранном диапазоне нет строк. Это не означает нулевой трафик." /> : null}
          {chartData.some((point) => poolSeries.some((series) => point[series.dataKey] === null)) ? <p className="mt-2 text-xs text-[color:var(--atlas-text-soft)]">Разрыв линии означает «Нет данных»; отсутствующее измерение не заменено нулём.</p> : null}
        </RouteBoundary>
      </Card>

      <div className="ops-workspace lg:grid-cols-[minmax(0,1.45fr)_minmax(17rem,0.55fr)]">
        <Card>
          <SectionTitle title="Исходная таблица" description="Те же фильтры, что у графика. Бесплатный и платный пулы остаются отдельными строками." />
          <DataTable data={rows} columns={columns} empty="Нет данных для выбранных фильтров" />
        </Card>
        <aside className="space-y-4" aria-label="Разбивки трафика">
          <Card><SectionTitle title="По нодам" />{nodeBreakdown.length ? <dl className="divide-y divide-[color:var(--atlas-border)]">{nodeBreakdown.map(([label, value]) => <div key={label} className="flex justify-between gap-3 py-2 text-xs"><dt className="font-semibold uppercase">{label}</dt><dd><MissingNumber value={value} suffix=" ГиБ" /></dd></div>)}</dl> : <EmptyState description="Нет данных по нодам." className="min-h-0" />}</Card>
          <Card><SectionTitle title="По контурам" />{poolBreakdown.length ? <dl className="divide-y divide-[color:var(--atlas-border)]">{poolBreakdown.map(([label, value]) => <div key={label} className="flex justify-between gap-3 py-2 text-xs"><dt className="font-semibold">{label === MISSING_POOL ? <MissingData inline /> : label}</dt><dd><MissingNumber value={value} suffix=" ГиБ" /></dd></div>)}</dl> : <EmptyState description="Нет данных по контурам." className="min-h-0" />}</Card>
        </aside>
      </div>
      {resource.error && resource.data ? <p className="text-xs text-[color:var(--atlas-text-soft)]">{adminApiErrorText(resource.error, "Повторите загрузку.")}</p> : null}
    </div>
  );
}
