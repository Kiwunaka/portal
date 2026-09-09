"use client";

import { useCallback, useEffect, useId, useMemo, useState, type ReactNode } from "react";
import { Radio, RefreshCw, Search, Server, UsersRound, Wifi } from "lucide-react";

import { RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import { EmptyState } from "@/components/ui/states";
import { OpsTooltip } from "@/components/ui/tooltip";
import { WindowedTable } from "@/components/ui/windowed-table";
import type { AdminApiError } from "@/lib/admin-api/client";
import { fetchOnlineUsers, type AdminOnlineUser, type OnlineSourceFilter } from "@/lib/admin-api/support";
import { formatSourceAge } from "@/lib/ops-status/presentation";
import { readUrlState, replaceUrlState, subscribeToUrlState, type UrlStateCodec, type UrlStateCodecs } from "@/lib/url-state";
import { useRouteResource } from "@/lib/use-route-resource";

const ONLINE_POLL_MS = 30_000;
const ONLINE_SOURCES = ["all", "user", "panel"] as const;

type OnlineUrlState = {
  node: string;
  source: OnlineSourceFilter;
  q: string;
};

function cleanStringCodec(): UrlStateCodec<string> {
  return { parse: (value) => value?.trim() || "", serialize: (value) => value.trim() || null };
}

function cleanEnumCodec<T extends string>(values: readonly T[], defaultValue: T): UrlStateCodec<T> {
  const allowed = new Set(values);
  return { parse: (value) => value && allowed.has(value as T) ? value as T : defaultValue, serialize: (value) => value === defaultValue ? null : value };
}

const ONLINE_URL_CODECS: UrlStateCodecs<OnlineUrlState> = {
  node: cleanStringCodec(),
  source: cleanEnumCodec<OnlineSourceFilter>(ONLINE_SOURCES, "all"),
  q: cleanStringCodec(),
};

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function statusLabel(value: string): string {
  if (value === "active") return "Активен";
  if (value === "blocked") return "Заблокирован";
  if (value === "expired") return "Истёк";
  if (value === "manual_test") return "Тестовый";
  return "Неизвестно";
}

function statusTone(value: string): Tone {
  if (value === "active") return "success";
  if (value === "blocked") return "danger";
  if (value === "expired" || value === "manual_test") return "warning";
  return "neutral";
}

function riskLabel(flags: string[]): string {
  if (!flags.length) return "Нет сигналов";
  if (flags.includes("manual_review")) return "Нужна ручная проверка";
  if (flags.some((flag) => flag.includes("suspicious"))) return "Подозрение";
  if (flags.some((flag) => flag.includes("multi_ip"))) return "Несколько адресов";
  return "Есть сигнал";
}

function Metric({ label, value, explanation, sampledAt, icon, tone = "neutral" }: { label: string; value: string; explanation: string; sampledAt: string | null; icon: ReactNode; tone?: Tone }) {
  const id = useId();
  return (
    <MetricCell
      icon={icon}
      label={label}
      value={value}
      detail="Оперативный снимок"
      tone={tone}
      aside={<OpsTooltip id={`${id}-online-metric`} content={explanation} source="Панель · агрегат без полных IP-адресов" sampledAt={sampledAt} threshold="Обновляется каждые 30 секунд при видимой вкладке" />}
    />
  );
}

function searchable(row: AdminOnlineUser): string {
  return [row.tgId, row.displayName, row.username, row.nodesOnline.join(" ")].filter(Boolean).join(" ").toLowerCase();
}

function panelErrorLabel(code: string): string {
  if (code === "missing_node_code") return "у источника нет кода ноды";
  if (code === "panel_unavailable") return "панель недоступна";
  return "оперативный запрос не выполнен";
}

export function OnlinePage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<OnlineUrlState>(() => readUrlState(ONLINE_URL_CODECS));
  useEffect(() => subscribeToUrlState<OnlineUrlState>(ONLINE_URL_CODECS, setUrlState), []);

  const load = useCallback((signal: AbortSignal) => fetchOnlineUsers({ limit: 200 }, { signal }), []);
  const online = useRouteResource("online:all", load, { enabled: true, pollMs: ONLINE_POLL_MS });

  const rows = useMemo(() => {
    const query = urlState.q.toLowerCase();
    return (online.data?.rows || []).filter((row) => {
      if (urlState.node && !row.nodesOnline.some((node) => node.toLowerCase() === urlState.node.toLowerCase())) return false;
      if (urlState.source !== "all" && row.source !== urlState.source) return false;
      return !query || searchable(row).includes(query);
    });
  }, [online.data, urlState.node, urlState.q, urlState.source]);
  const nodes = useMemo(() => [...new Set([
    ...(online.data?.rows || []).flatMap((row) => row.nodesOnline.map((node) => node.toLowerCase())),
    ...(urlState.node ? [urlState.node.toLowerCase()] : []),
  ])].sort(), [online.data, urlState.node]);

  useEffect(() => {
    onShellStatus?.({
      api: online.error ? "failed" : online.loading ? "missing" : online.data?.summary.nodesWithPanelErrors ? "degraded" : "ok",
      session: isAccessDenied(online.error) ? "failed" : online.data ? "ok" : online.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: online.data?.generatedAt || null,
    });
  }, [onShellStatus, online.data, online.error, online.loading]);

  const generatedAt = online.data?.generatedAt || null;
  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={online.error || online.data?.summary.nodesWithPanelErrors ? "warning" : online.data ? "success" : "neutral"}>{online.error ? "Источник не ответил" : online.data?.summary.nodesWithPanelErrors ? "Снимок неполный" : online.data ? "Оперативный источник отвечает" : "Ожидаем источник"}</Badge>
          <span>{generatedAt ? `Снимок ${formatSourceAge(generatedAt)}` : "Снимок ещё не получен"}</span>
          {online.refreshing ? <Badge tone="info">Обновляем</Badge> : null}
        </div>
        <Button tone="secondary" disabled={online.loading || online.refreshing} onClick={online.reload}><RefreshCw size={15} className={online.refreshing ? "animate-spin" : ""} /> Обновить</Button>
      </div>

      {online.data ? (
        <MetricStrip>
          <Metric label="Пользователи онлайн" value={String(online.data.summary.knownUsersOnline)} explanation="Сопоставленные с записью пользователя идентификаторы из оперативного снимка." sampledAt={generatedAt} icon={<UsersRound size={15} />} tone="success" />
          <Metric label="Соединения" value={String(online.data.summary.onlineConnectionsNow)} explanation="Сумма соединений панели; не число уникальных людей." sampledAt={generatedAt} icon={<Wifi size={15} />} tone="info" />
          <Metric label="Ключи онлайн" value={String(online.data.summary.onlineKeysNow)} explanation="Количество ключей, присутствующих в текущем оперативном снимке." sampledAt={generatedAt} icon={<Radio size={15} />} tone="info" />
          <Metric label="Сбои нод" value={String(online.data.summary.nodesWithPanelErrors)} explanation="Число нод, по которым панель не дала пригодный оперативный снимок." sampledAt={generatedAt} icon={<Server size={15} />} tone={online.data.summary.nodesWithPanelErrors ? "warning" : "success"} />
        </MetricStrip>
      ) : null}

      <Card>
        <SectionTitle title="Сейчас онлайн" description="Ограниченный оперативный агрегат. Полные IP-адреса здесь не запрашиваются и не отображаются." />
        <div className="grid gap-2 md:grid-cols-[minmax(240px,1fr)_180px_200px]">
          <label className="relative">
            <span className="sr-only">Поиск в оперативном списке</span>
            <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--atlas-text-muted)]" size={15} />
            <input type="search" aria-label="Поиск в оперативном списке" value={urlState.q} onChange={(event) => replaceUrlState<OnlineUrlState>({ q: event.target.value }, ONLINE_URL_CODECS)} placeholder="Telegram ID, имя или нода" className="min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] pl-9 pr-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]" />
          </label>
          <select aria-label="Фильтр по ноде" value={urlState.node} onChange={(event) => replaceUrlState<OnlineUrlState>({ node: event.target.value }, ONLINE_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]">
            <option value="">Все ноды</option>
            {nodes.map((node) => <option key={node} value={node}>{node.toUpperCase()}</option>)}
          </select>
          <select aria-label="Источник сопоставления" value={urlState.source} onChange={(event) => replaceUrlState<OnlineUrlState>({ source: event.target.value as OnlineSourceFilter }, ONLINE_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm outline-none focus:border-[color:var(--atlas-focus)]">
            <option value="all">Все источники</option>
            <option value="user">Сопоставлен с пользователем</option>
            <option value="panel">Только панель</option>
          </select>
        </div>

        <div className="mt-3">
          <RouteBoundary loading={online.loading} refreshing={online.refreshing} error={online.error} hasData={online.data !== null} retryLabel="Повторить загрузку оперативного списка" onRetry={online.reload}>
            {rows.length ? (
              <WindowedTable label="Оперативный список пользователей" columnCount={7} tableClassName="w-full min-w-[900px] border-collapse text-left text-xs"
                header={<thead className="bg-[color:var(--pokrov-table-header-bg)] text-[11px] text-[color:var(--atlas-text-soft)]"><tr>{["Пользователь", "Доступ", "Ноды", "Ключи / соединения", "Адресов", "Риск", "Возраст сигнала"].map((header) => <th key={header} className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">{header}</th>)}</tr></thead>}
                rows={rows.map((row) => (
                    <tr key={row.rowId} className="border-b border-[color:var(--pokrov-table-divider)] hover:bg-[color:var(--pokrov-table-row-hover-bg)]">
                      <td className="px-3 py-2">{row.tgId !== null ? <a href={`/users?selected=${row.tgId}`} className="font-semibold text-[color:var(--atlas-primary)] hover:underline">Пользователь {row.tgId}<span className="block font-normal text-[color:var(--atlas-text-muted)]">{row.displayName || (row.username ? `@${row.username}` : "Без имени")}</span></a> : <span><strong>Не сопоставлен</strong><span className="block text-[color:var(--atlas-text-muted)]">Только запись панели</span></span>}</td>
                      <td className="px-3 py-2"><Badge tone={statusTone(row.status)}>{statusLabel(row.status)}</Badge></td>
                      <td className="px-3 py-2 font-mono">{row.nodesOnline.length ? row.nodesOnline.map((node) => node.toUpperCase()).join(", ") : "Нет данных"}</td>
                      <td className="px-3 py-2 tabular-nums">{row.onlineKeysNow} / {row.onlineConnectionsNow}</td>
                      <td className="px-3 py-2 tabular-nums">{row.connectionAddressCount}</td>
                      <td className="px-3 py-2"><Badge tone={row.riskFlags.length ? "warning" : "success"}>{riskLabel(row.riskFlags)}</Badge></td>
                      <td className="px-3 py-2">{row.lastOnlineAt ? formatSourceAge(row.lastOnlineAt) : "Нет данных"}<span className="block text-[11px] text-[color:var(--atlas-text-muted)]">{row.source === "user" ? "Сопоставлен с пользователем" : "Только панель"}</span></td>
                    </tr>
                  ))}
              />
            ) : online.data ? <EmptyState title="Строки оперативного снимка не найдены" description="Измените фильтры. Пустой снимок не подтверждает, что панель и все ноды доступны." /> : null}
          </RouteBoundary>
        </div>
      </Card>

      {online.data?.panelErrors.length ? (
        <Card><SectionTitle title="Неполный оперативный снимок" description="Часть нод не ответила. Остальные строки сохранены." /><div className="flex flex-wrap gap-2">{online.data.panelErrors.map((error, index) => <Badge key={`${error.nodeCode}-${error.evidenceCode}-${index}`} tone="warning">{error.nodeCode ? `Нода ${error.nodeCode.toUpperCase()}` : "Нода не указана"}: {panelErrorLabel(error.evidenceCode)}</Badge>)}</div></Card>
      ) : null}
    </div>
  );
}
