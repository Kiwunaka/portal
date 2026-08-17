"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Cable, Clock3, CreditCard, Percent, RefreshCw, UsersRound } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ColumnDef } from "@tanstack/react-table";

import { MissingData } from "@/components/ops/missing-data";
import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, DataTable, EmptyState, MetricCell, MetricStrip, SectionTitle } from "@/components/ui";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchFunnel, type FunnelDiagnosticRow, type FunnelRange, type FunnelSource, type FunnelStage, type FunnelVersionRow } from "@/lib/admin-api/revenue";
import { useRouteResource } from "@/lib/use-route-resource";
import { readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type FunnelView = "acquisition" | "product";
type FunnelUrlState = { range: FunnelRange; view: FunnelView; source: string; stage: string };

const FUNNEL_URL_CODECS = {
  range: urlCodecs.enum(["7d", "30d", "90d"] as const, "30d"),
  view: urlCodecs.enum(["acquisition", "product"] as const, "acquisition"),
  source: urlCodecs.string(""),
  stage: urlCodecs.string(""),
};

const ACQUISITION_SOURCE_METRICS: Array<{ label: string; key: keyof FunnelSource }> = [
  { label: "Первый визит", key: "sessions" },
  { label: "Скачали / открыли бота", key: "entry_intents" },
  { label: "Подтвердили вход", key: "resolved_entries" },
  { label: "Начали оплату", key: "checkouts" },
  { label: "Оплатили", key: "paid" },
  { label: "Подключились", key: "connected" },
];

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

export function FunnelPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<FunnelUrlState>(() => readUrlState(FUNNEL_URL_CODECS));
  useEffect(() => subscribeToUrlState<FunnelUrlState>(FUNNEL_URL_CODECS, setUrlState), []);
  const load = useCallback((signal: AbortSignal) => fetchFunnel(urlState.range, { signal }), [urlState.range]);
  const resource = useRouteResource(`funnel:${urlState.range}`, load, { enabled: true, pollMs: 60_000 });

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: resource.data?.period.from || null,
    });
  }, [onShellStatus, resource.data, resource.error, resource.loading]);

  const acquisition = resource.data?.acquisition || null;
  const product = resource.data?.product || null;
  const section = urlState.view === "acquisition" ? acquisition : product;
  const sources = useMemo(() => acquisition?.by_source || [], [acquisition?.by_source]);
  const selectedSource = urlState.view === "acquisition" && urlState.source
    ? sources.find((row) => row.source === urlState.source) || null
    : null;
  const filteredSources = useMemo(
    () => sources.filter((row) => !urlState.source || row.source === urlState.source),
    [sources, urlState.source],
  );
  const filteredStages = useMemo(
    () => (section?.stages || []).filter((stage) => !urlState.stage || stage.key === urlState.stage),
    [section?.stages, urlState.stage],
  );
  const chartRows = useMemo(
    () => filteredStages.map((stage) => ({ label: stage.label, value: finite(stage.reached_next) })),
    [filteredStages],
  );

  const firstValue = selectedSource?.sessions
    ?? (urlState.view === "acquisition" ? acquisition?.totals.sessions : product?.totals.opened)
    ?? null;
  const paidValue = selectedSource?.paid
    ?? (urlState.view === "acquisition" ? acquisition?.totals.paid : product?.totals.paid)
    ?? null;
  const connectedValue = selectedSource?.connected
    ?? (urlState.view === "acquisition" ? acquisition?.totals.connected : product?.totals.connected)
    ?? null;
  const conversion = finite(firstValue) !== null && finite(connectedValue) !== null && Number(firstValue) > 0
    ? Number(connectedValue) / Number(firstValue) * 100
    : null;

  const stageColumns = useMemo<ColumnDef<FunnelStage>[]>(() => [
    { header: "Переход", accessorKey: "label" },
    { header: "Вошли", cell: ({ row }) => <NumberValue value={row.original.entered} /> },
    { header: "Прошли дальше", cell: ({ row }) => <NumberValue value={row.original.reached_next} /> },
    { header: "Потеря", cell: ({ row }) => <NumberValue value={row.original.dropped} /> },
    { header: "Конверсия", cell: ({ row }) => <NumberValue value={row.original.conversion_pct} suffix="%" /> },
  ], []);
  const sourceColumns = useMemo<ColumnDef<FunnelSource>[]>(() => [
    { header: "Источник", cell: ({ row }) => <span className="font-semibold">{row.original.source || "— · Нет данных"}</span> },
    ...ACQUISITION_SOURCE_METRICS.map((metric): ColumnDef<FunnelSource> => ({
      header: metric.label,
      cell: ({ row }) => <NumberValue value={row.original[metric.key]} />,
    })),
  ], []);
  const diagnosticColumns = useMemo<ColumnDef<FunnelDiagnosticRow>[]>(() => [
    { header: "Код", cell: ({ row }) => <span className="font-mono text-xs">{row.original.key}</span> },
    { header: "События", cell: ({ row }) => <NumberValue value={row.original.count} /> },
    { header: "Последнее", cell: ({ row }) => row.original.latest_at ? new Date(row.original.latest_at).toLocaleString("ru-RU") : <MissingData /> },
  ], []);
  const versionColumns = useMemo<ColumnDef<FunnelVersionRow>[]>(() => [
    { header: "Клиент", cell: ({ row }) => <span className="font-semibold">{row.original.platform} · {row.original.app_version}</span> },
    { header: "Пользователи", cell: ({ row }) => <NumberValue value={row.original.users} /> },
    { header: "События", cell: ({ row }) => <NumberValue value={row.original.events} /> },
    { header: "Последнее", cell: ({ row }) => row.original.latest_at ? new Date(row.original.latest_at).toLocaleString("ru-RU") : <MissingData /> },
  ], []);

  const selectView = (view: FunnelView) => {
    replaceUrlState<FunnelUrlState>({ view, source: "", stage: "" }, FUNNEL_URL_CODECS);
  };
  const dropReasons = section?.drop_reasons || [];

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap gap-2 text-xs">
          <Badge tone={resource.error ? "warning" : resource.data ? "success" : "neutral"}>{resource.error ? "Источник воронки отвечает с ошибкой" : resource.data ? "Воронки рассчитаны" : "Воронки ещё не получены"}</Badge>
          <span className="text-[color:var(--atlas-text-soft)]">Первичные сессии и известные пользователи считаются отдельно.</span>
        </div>
        <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      {resource.data ? (
        <MetricStrip label={urlState.view === "acquisition" ? "Сводка рекламной воронки" : "Сводка продуктовой воронки"}>
          <MetricCell icon={<UsersRound aria-hidden="true" size={17} />} label={urlState.view === "acquisition" ? "Первый визит" : "Открыли продукт"} value={finite(firstValue) === null ? <MissingData /> : valueText(firstValue)} detail={selectedSource?.source || (urlState.view === "acquisition" ? "First-touch cohort" : "Известные пользователи")} tone="info" />
          <MetricCell icon={<CreditCard aria-hidden="true" size={17} />} label="Оплатили" value={finite(paidValue) === null ? <MissingData /> : valueText(paidValue)} detail={`Диапазон: ${urlState.range}`} tone="success" />
          <MetricCell icon={<Cable aria-hidden="true" size={17} />} label="Подключились" value={finite(connectedValue) === null ? <MissingData /> : valueText(connectedValue)} detail="Серверно подтверждено" tone="success" />
          <MetricCell icon={<Percent aria-hidden="true" size={17} />} label="До подключения" value={conversion === null ? <MissingData /> : valueText(conversion, "%")} detail={urlState.view === "acquisition" ? "Подключились / первый визит" : "Подключились / открыли продукт"} tone={conversion !== null && conversion < 20 ? "warning" : "neutral"} />
        </MetricStrip>
      ) : null}

      <Card>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <SectionTitle
            title={urlState.view === "acquisition" ? "Рекламная воронка" : "Продуктовая воронка"}
            description={urlState.view === "acquisition"
              ? "First-touch сессия проходит только через серверно связанный handoff, оплату и аккаунт."
              : "Один известный пользователь считается один раз, даже если оставил несколько событий или попыток оплаты."}
          />
          <div className="grid gap-2 sm:grid-cols-[auto_auto_minmax(9rem,1fr)_minmax(11rem,1fr)]">
            <Button tone={urlState.view === "acquisition" ? "primary" : "secondary"} aria-pressed={urlState.view === "acquisition"} onClick={() => selectView("acquisition")}>Реклама</Button>
            <Button tone={urlState.view === "product" ? "primary" : "secondary"} aria-pressed={urlState.view === "product"} onClick={() => selectView("product")}>Продукт</Button>
            <label className="text-xs font-semibold">Диапазон<select aria-label="Диапазон воронки" value={urlState.range} onChange={(event) => replaceUrlState<FunnelUrlState>({ range: event.target.value as FunnelRange }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="7d">7 дней</option><option value="30d">30 дней</option><option value="90d">90 дней</option></select></label>
            <label className="text-xs font-semibold">Стадия<select aria-label="Стадия воронки" value={urlState.stage} onChange={(event) => replaceUrlState<FunnelUrlState>({ stage: event.target.value }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все стадии</option>{(section?.stages || []).map((stage) => <option key={stage.key} value={stage.key}>{stage.label}</option>)}</select></label>
          </div>
        </div>
        {urlState.view === "acquisition" ? <label className="mt-3 block max-w-xs text-xs font-semibold">Источник<select aria-label="Источник воронки" value={urlState.source} onChange={(event) => replaceUrlState<FunnelUrlState>({ source: event.target.value }, FUNNEL_URL_CODECS)} className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3"><option value="">Все источники</option>{sources.map((row) => <option key={row.source} value={row.source}>{row.source}</option>)}</select></label> : null}
        <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить воронку" onRetry={resource.reload}>
          {chartRows.length ? <div aria-label="График воронки" data-view={urlState.view} data-source={urlState.source || "all"} data-stage={urlState.stage || "all"} className="mt-4 h-72"><ResponsiveContainer width="100%" height="100%"><BarChart data={chartRows}><CartesianGrid stroke="var(--atlas-border)" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="label" tick={{ fill: "var(--atlas-text-muted)", fontSize: 10 }} interval={0} /><YAxis tick={{ fill: "var(--atlas-text-muted)", fontSize: 11 }} /><Tooltip formatter={(value) => [finite(value) === null ? "— · Нет данных" : valueText(value), "Прошли дальше"]} /><Bar dataKey="value" fill="var(--atlas-primary)" radius={[3, 3, 0, 0]} /></BarChart></ResponsiveContainer></div> : resource.data ? <EmptyState description="Для выбранных фильтров нет агрегатов. Это не равно нулевой конверсии." /> : null}
        </RouteBoundary>
      </Card>

      <section className="ops-workspace xl:grid-cols-[minmax(0,1.32fr)_minmax(20rem,0.68fr)]">
        <Card><SectionTitle title="Стадии" description="Каждая следующая стадия — подмножество предыдущей; суммы разных источников не склеиваются." />{filteredStages.length ? <DataTable data={filteredStages} columns={stageColumns} empty="Нет стадий" /> : resource.data ? <EmptyState description="Для выбранной стадии нет данных." /> : <MissingData />}</Card>
        <aside aria-label="Причины потерь"><Card><SectionTitle title="Причины потерь" />{dropReasons.length ? <dl className="divide-y divide-[color:var(--atlas-border)]">{dropReasons.map((row) => <div key={row.reason} className="flex justify-between gap-3 py-2 text-xs"><dt>{row.reason}</dt><dd><NumberValue value={row.count} /></dd></div>)}</dl> : resource.data ? <EmptyState description="Причины не рассчитаны." className="min-h-0" /> : <MissingData />}</Card></aside>
      </section>

      {urlState.view === "acquisition" ? (
        <Card><SectionTitle title="Источники первого касания" description="Источник фиксируется при первой first-party сессии. Ни raw URL, ни IP, ни идентификаторы пользователя сюда не попадают." />{filteredSources.length ? <DataTable data={filteredSources} columns={sourceColumns} empty="Нет источников" /> : resource.data ? <EmptyState description="По выбранному источнику нет данных." /> : <MissingData />}</Card>
      ) : (
        <div className="space-y-3">
          <MetricStrip label="Качество продукта">
            <MetricCell icon={<UsersRound aria-hidden="true" size={17} />} label="Активны за 7 дней" value={finite(product?.observability.summary.active_users_7d) === null ? <MissingData /> : valueText(product?.observability.summary.active_users_7d)} detail="Успешно подключались" tone="success" />
            <MetricCell icon={<Activity aria-hidden="true" size={17} />} label="События" value={finite(product?.observability.summary.events) === null ? <MissingData /> : valueText(product?.observability.summary.events)} detail={`Диапазон: ${urlState.range}`} tone="info" />
            <MetricCell icon={<AlertTriangle aria-hidden="true" size={17} />} label="Ошибки" value={finite(product?.observability.summary.failures) === null ? <MissingData /> : valueText(product?.observability.summary.failures)} detail={`${valueText(product?.observability.summary.retryable_failures)} временных`} tone={Number(product?.observability.summary.failures || 0) > 0 ? "warning" : "neutral"} />
            <MetricCell icon={<Clock3 aria-hidden="true" size={17} />} label="Сдвиг часов" value={finite(product?.observability.summary.clock_skewed) === null ? <MissingData /> : valueText(product?.observability.summary.clock_skewed)} detail="Поздние или будущие события" tone={Number(product?.observability.summary.clock_skewed || 0) > 0 ? "warning" : "neutral"} />
          </MetricStrip>
          <section className="ops-workspace xl:grid-cols-2">
            <Card><SectionTitle title="Ошибки клиента" description="Без текста сообщений, URL, IP и пользовательских идентификаторов." />{product?.observability.errors.length ? <DataTable data={product.observability.errors} columns={diagnosticColumns} empty="Ошибок нет" /> : <EmptyState description="За выбранный период кодированных ошибок нет." className="min-h-0" />}</Card>
            <Card><SectionTitle title="Где ломается" description="Стадии и подсистемы, в которых зафиксирован отрицательный результат." />{product?.observability.stages.length ? <DataTable data={product.observability.stages} columns={diagnosticColumns} empty="Стадий нет" /> : <EmptyState description="Сервер не получил ошибок с указанием стадии." className="min-h-0" />}</Card>
          </section>
          <Card><SectionTitle title="Версии клиентов" description="Разрез по платформе и версии помогает увидеть старые сборки и миграционные проблемы." />{product?.observability.versions.length ? <DataTable data={product.observability.versions} columns={versionColumns} empty="Версий нет" /> : <EmptyState description="Клиенты ещё не прислали версию в Event Envelope V1." className="min-h-0" />}</Card>
          <Card><SectionTitle title="Как считается продукт" description="Открытия, checkout, оплаты и подключения объединяются по известному серверному пользователю. Повторные события не раздувают показатели." /><p className="mt-3 max-w-3xl text-sm text-[color:var(--atlas-text-soft)]">Этот срез отвечает на вопрос «где спотыкаются уже известные пользователи». Для рекламных решений вернитесь в «Реклама»: там действует first-touch cohort и доступен разрез по источнику.</p></Card>
        </div>
      )}
    </div>
  );
}
