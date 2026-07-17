"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";

import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, SectionTitle } from "@/components/ui";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { AdminApiError } from "@/lib/admin-api/client";
import {
  fetchNodeList,
  fetchNodeObservability,
  fetchRuHistory,
  fetchRuLatest,
  fetchRuUploaderStatus,
  type NodeAlertFilter,
  type NodeDetailTab,
  type NodeFreshnessFilter,
  type NodeLifecycleFilter,
  type RuHistoryRange,
  type RuNodeStatus,
  type RuRunSummary
} from "@/lib/admin-api/nodes";
import { pushUrlState, readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs, type UrlStateCodec, type UrlStateCodecs } from "@/lib/url-state";
import { useRouteResource } from "@/lib/use-route-resource";

import { NodeDetail } from "./node-detail";
import { NodeList, type NodeFilters } from "./node-list";

const NODE_POLL_MS = 60_000;
const NODE_TABS = ["overview", "ru", "load", "clients", "transport", "alerts", "technical"] as const;
const HISTORY_RANGES = ["24h", "7d", "30d", "180d"] as const;
const LIFECYCLE_FILTERS = ["all", "enabled", "draining", "disabled"] as const;
const FRESHNESS_FILTERS = ["all", "fresh", "stale", "missing"] as const;
const ALERT_FILTERS = ["all", "with", "without"] as const;

type NodeUrlState = NodeFilters & {
  selected: string | null;
  tab: NodeDetailTab;
  range: RuHistoryRange;
};

type HistoryContinuation = {
  key: string;
  items: RuRunSummary[];
  nextCursor: string | null;
  loaded: boolean;
  loading: boolean;
  error: string | null;
};

const EMPTY_HISTORY_CONTINUATION: HistoryContinuation = {
  key: "",
  items: [],
  nextCursor: null,
  loaded: false,
  loading: false,
  error: null
};

function historyRunIdentity(run: RuRunSummary): string {
  return Number.isFinite(run.run_db_id) ? `db:${run.run_db_id}` : `run:${run.run_id}`;
}

function mergeHistoryRuns(...pages: RuRunSummary[][]): RuRunSummary[] {
  const seen = new Set<string>();
  const merged: RuRunSummary[] = [];
  for (const run of pages.flat()) {
    const identity = historyRunIdentity(run);
    if (seen.has(identity)) continue;
    seen.add(identity);
    merged.push(run);
  }
  return merged;
}

function cleanEnumCodec<T extends string>(values: readonly T[], defaultValue: T): UrlStateCodec<T> {
  const approved = new Set(values);
  return {
    parse: (value) => value && approved.has(value as T) ? value as T : defaultValue,
    serialize: (value) => value === defaultValue ? null : value
  };
}

const NODE_URL_CODECS: UrlStateCodecs<NodeUrlState> = {
  q: urlCodecs.string(""),
  state: cleanEnumCodec<NodeLifecycleFilter>(LIFECYCLE_FILTERS, "all"),
  freshness: cleanEnumCodec<NodeFreshnessFilter>(FRESHNESS_FILTERS, "all"),
  country: urlCodecs.string("all"),
  hoster: urlCodecs.string("all"),
  transport: urlCodecs.string("all"),
  alert: cleanEnumCodec<NodeAlertFilter>(ALERT_FILTERS, "all"),
  selected: urlCodecs.optionalString(),
  tab: cleanEnumCodec<NodeDetailTab>(NODE_TABS, "overview"),
  range: cleanEnumCodec<RuHistoryRange>(HISTORY_RANGES, "24h")
};

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function errorText(error: AdminApiError | null, fallback: string): string | null {
  return error ? adminApiErrorText(error, fallback) : null;
}

export function NodesPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<NodeUrlState>(() => readUrlState(NODE_URL_CODECS));
  const selected = urlState.selected?.trim().toLowerCase() || null;
  const ruTabActive = Boolean(selected && urlState.tab === "ru");

  useEffect(() => subscribeToUrlState<NodeUrlState>(NODE_URL_CODECS, setUrlState), []);

  const loadList = useCallback((signal: AbortSignal) => fetchNodeList({ signal }), []);
  const loadLatest = useCallback((signal: AbortSignal) => fetchRuLatest({ signal }), []);
  const loadDetail = useCallback((signal: AbortSignal) => {
    if (!selected) throw new Error("Node is not selected");
    return fetchNodeObservability(selected, { signal });
  }, [selected]);
  const loadHistory = useCallback((signal: AbortSignal) => {
    if (!selected) throw new Error("Node is not selected");
    return fetchRuHistory(selected, urlState.range, null, { signal });
  }, [selected, urlState.range]);
  const loadUploader = useCallback((signal: AbortSignal) => fetchRuUploaderStatus({ signal }), []);

  const list = useRouteResource("nodes-list", loadList, { pollMs: NODE_POLL_MS, enabled: true });
  const latest = useRouteResource("nodes-ru-latest", loadLatest, { pollMs: NODE_POLL_MS, enabled: true });
  const detail = useRouteResource(`node-detail:${selected || "none"}`, loadDetail, { enabled: Boolean(selected) });
  const history = useRouteResource(`node-history:${selected || "none"}:${urlState.range}`, loadHistory, { enabled: ruTabActive });
  const uploader = useRouteResource(`node-uploader:${selected || "none"}`, loadUploader, { pollMs: NODE_POLL_MS, enabled: ruTabActive });

  const ruByCode = useMemo(() => new Map((latest.data?.nodes || []).map((row) => [row.node_code.toLowerCase(), row])), [latest.data]);
  const selectedRuStatus = useMemo<RuNodeStatus | null>(() => {
    if (!selected || !latest.data) return null;
    const status = ruByCode.get(selected);
    if (status) return status;
    return {
      node_code: selected,
      status: "missing",
      sampled_at: latest.data.sampled_at,
      age_seconds: latest.data.age_seconds,
      threshold_seconds: latest.data.threshold_seconds,
      reason_code: "selected_target_missing",
      run_id: latest.data.latest_received_attempt?.run_id || null,
      target: null
    };
  }, [latest.data, ruByCode, selected]);

  const historyScopeKey = `${selected || "none"}:${urlState.range}`;
  const firstPageIdentity = history.data
    ? `${history.data.items.map(historyRunIdentity).join(",")}|${history.data.next_cursor || "end"}`
    : "pending";
  const historyKey = `${historyScopeKey}:${firstPageIdentity}`;
  const [historyContinuation, setHistoryContinuation] = useState<HistoryContinuation>(EMPTY_HISTORY_CONTINUATION);
  const activeHistoryContinuation = historyContinuation.key === historyKey ? historyContinuation : EMPTY_HISTORY_CONTINUATION;
  const historyMoreController = useRef<AbortController | null>(null);
  const historyMoreInFlight = useRef(false);

  useEffect(() => {
    historyMoreController.current?.abort();
    historyMoreInFlight.current = false;
  }, [historyKey]);

  useEffect(() => () => historyMoreController.current?.abort(), []);

  const resetHistoryContinuation = useCallback(() => {
    historyMoreController.current?.abort();
    historyMoreController.current = null;
    historyMoreInFlight.current = false;
    setHistoryContinuation({ ...EMPTY_HISTORY_CONTINUATION, key: historyKey });
  }, [historyKey]);

  const loadMoreHistory = useCallback(async () => {
    const cursor = activeHistoryContinuation.loaded ? activeHistoryContinuation.nextCursor : history.data?.next_cursor;
    if (!selected || !cursor || activeHistoryContinuation.loading || historyMoreInFlight.current) return;
    historyMoreController.current?.abort();
    const controller = new AbortController();
    historyMoreController.current = controller;
    historyMoreInFlight.current = true;
    setHistoryContinuation({ ...activeHistoryContinuation, key: historyKey, loading: true, error: null });
    try {
      const page = await fetchRuHistory(selected, urlState.range, cursor, { signal: controller.signal });
      if (controller.signal.aborted) return;
      setHistoryContinuation((current) => current.key === historyKey ? {
        ...current,
        items: mergeHistoryRuns(current.items, page.items),
        nextCursor: page.next_cursor,
        loaded: true,
        loading: false,
        error: null
      } : current);
    } catch (error) {
      if (controller.signal.aborted) return;
      const normalized = error instanceof AdminApiError ? error : null;
      setHistoryContinuation((current) => current.key === historyKey ? {
        ...current,
        loading: false,
        error: adminApiErrorText(normalized, "Повторите загрузку следующей страницы истории.")
      } : current);
    } finally {
      if (historyMoreController.current === controller) {
        historyMoreController.current = null;
        historyMoreInFlight.current = false;
        setHistoryContinuation((current) => current.key === historyKey && current.loading
          ? { ...current, loading: false }
          : current);
      }
    }
  }, [activeHistoryContinuation, history.data?.next_cursor, historyKey, selected, urlState.range]);

  const visibleHistory = useMemo(() => history.data ? {
    ...history.data,
    items: mergeHistoryRuns(history.data.items, activeHistoryContinuation.items),
    next_cursor: activeHistoryContinuation.loaded ? activeHistoryContinuation.nextCursor : history.data.next_cursor
  } : null, [activeHistoryContinuation.items, activeHistoryContinuation.loaded, activeHistoryContinuation.nextCursor, history.data]);

  useEffect(() => {
    const errors = [list.error, latest.error, detail.error, history.error, uploader.error].filter((error): error is AdminApiError => error !== null);
    const successCount = Number(list.data !== null) + Number(latest.data !== null) + Number(detail.data !== null);
    const requiredTimes = [
      ...(list.data || []).map((row) => row.last_health_at).filter((value): value is string => Boolean(value)),
      latest.data?.sampled_at,
      detail.data?.sources.brain_metrics.sampled_at,
      detail.data?.sources.runtime.sampled_at,
      detail.data?.sources.observer.sampled_at
    ].filter((value): value is string => Boolean(value)).sort();
    onShellStatus?.({
      api: errors.length ? successCount ? "degraded" : "failed" : list.loading || latest.loading ? "missing" : "ok",
      session: errors.some(isAccessDenied) ? "failed" : successCount ? "ok" : errors.length ? "unavailable" : "missing",
      oldestRequiredSourceAt: requiredTimes.at(0) || null
    });
  }, [detail.data, detail.error, history.error, latest.data, latest.error, list.data, list.error, list.loading, latest.loading, onShellStatus, uploader.error]);

  const updateFilters = useCallback((patch: Partial<NodeFilters>) => {
    replaceUrlState<NodeUrlState>(patch, NODE_URL_CODECS);
  }, []);

  const refreshing = list.refreshing || latest.refreshing || detail.refreshing || history.refreshing || uploader.refreshing;
  const anyError = Boolean(list.error || latest.error || detail.error || history.error || uploader.error);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={anyError ? "warning" : "success"}>{anyError ? "Есть сбой источника" : "Источники отвечают"}</Badge>
          <span>{list.data ? `${list.data.length} нод в текущем списке` : "Список ещё не получен"}</span>
          {refreshing ? <Badge tone="info">Обновляем</Badge> : null}
        </div>
        <Button
          tone="secondary"
          disabled={list.loading || latest.loading || refreshing}
          onClick={() => {
            list.reload();
            latest.reload();
            if (selected) detail.reload();
            if (ruTabActive) {
              resetHistoryContinuation();
              history.reload();
              uploader.reload();
            }
          }}
        >
          <RefreshCw size={15} className={refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      {latest.error ? (
        <ErrorState
          title="RU-origin не обновился"
          description={`${adminApiErrorText(latest.error, "Повторите запрос RU-origin.")} Список и Brain-данные остаются доступны.`}
          action={<Button tone="secondary" onClick={latest.reload}>Повторить RU-origin</Button>}
          className="min-h-0"
        />
      ) : null}

      <div className="grid min-w-0 gap-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.25fr)]">
        <section aria-label="Ноды" className={`min-w-0 ${selected ? "max-lg:hidden" : ""}`}>
          <Card className="min-h-[420px] p-3">
            <SectionTitle title="Ноды" description="Плотный список, где сначала видно состояние. Выберите строку, чтобы открыть независимые источники и историю." />
            <RouteBoundary loading={list.loading} refreshing={list.refreshing} error={list.error} hasData={list.data !== null} retryLabel="Повторить загрузку нод" onRetry={list.reload}>
              {list.data?.length ? (
                <NodeList
                  rows={list.data}
                  ruByCode={ruByCode}
                  filters={urlState}
                  selected={selected}
                  onFiltersChange={updateFilters}
                  onSelect={(code) => {
                    resetHistoryContinuation();
                    pushUrlState<NodeUrlState>({ selected: code }, NODE_URL_CODECS);
                  }}
                />
              ) : list.data ? <EmptyState description="Сервер вернул пустой список нод. Это не считается нулевой нагрузкой." /> : null}
            </RouteBoundary>
          </Card>
        </section>

        <section aria-label="Карточка ноды" className={`min-w-0 ${selected ? "" : "max-lg:hidden"}`}>
          {!selected ? (
            <Card className="hidden min-h-[420px] lg:block">
              <EmptyState title="Выберите ноду" description="Карточка загрузится отдельным запросом после выбора строки; история RU-origin загрузится только при открытии своей вкладки." />
            </Card>
          ) : null}
          {selected ? (
            <Button tone="ghost" className="mb-2 lg:hidden" onClick={() => {
              resetHistoryContinuation();
              pushUrlState<NodeUrlState>({ selected: null }, NODE_URL_CODECS);
            }}>
              <ArrowLeft size={15} /> Назад к нодам
            </Button>
          ) : null}
          {selected && detail.loading && !detail.data ? <LoadingState title="Загружаем карточку ноды" description="Список остаётся доступен, карточка запрашивается отдельно." /> : null}
          {selected && detail.error && !detail.data ? (
            <ErrorState title="Карточка ноды недоступна" description={adminApiErrorText(detail.error, "Повторите запрос выбранной ноды.")} action={<Button tone="secondary" onClick={detail.reload}>Повторить карточку</Button>} />
          ) : null}
          {selected && detail.data ? (
            <NodeDetail
              data={detail.data}
              tab={urlState.tab}
              onTabChange={(tab) => pushUrlState<NodeUrlState>({ tab }, NODE_URL_CODECS)}
              ruLatest={latest.data}
              ruStatus={selectedRuStatus}
              latestLoading={latest.loading}
              latestError={errorText(latest.error, "Повторите загрузку текущего RU-origin.")}
              onLatestRetry={latest.reload}
              history={visibleHistory}
              historyLoading={history.loading}
              historyError={errorText(history.error, "Повторите загрузку истории.")}
              onHistoryRetry={() => {
                resetHistoryContinuation();
                history.reload();
              }}
              historyMoreLoading={activeHistoryContinuation.loading}
              historyMoreError={activeHistoryContinuation.error}
              onHistoryLoadMore={loadMoreHistory}
              uploader={uploader.data}
              uploaderLoading={uploader.loading}
              uploaderError={errorText(uploader.error, "Повторите загрузку служебного сигнала.")}
              onUploaderRetry={uploader.reload}
              range={urlState.range}
              onRangeChange={(range) => {
                resetHistoryContinuation();
                pushUrlState<NodeUrlState>({ range }, NODE_URL_CODECS);
              }}
            />
          ) : null}
        </section>
      </div>
    </div>
  );
}
