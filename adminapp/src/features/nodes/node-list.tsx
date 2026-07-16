"use client";

import { useMemo, type KeyboardEvent } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import type {
  NodeAlertFilter,
  NodeFreshnessFilter,
  NodeLifecycleFilter,
  NodeListRow,
  RuNodeStatus
} from "@/lib/admin-api/nodes";

import { opsStatusFromSource } from "./node-source-summary";

export type NodeFilters = {
  q: string;
  state: NodeLifecycleFilter;
  freshness: NodeFreshnessFilter;
  country: string;
  hoster: string;
  transport: string;
  alert: NodeAlertFilter;
};

function finiteNumber(value: number | null | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatNumber(value: number | null | undefined, suffix = ""): string {
  const number = finiteNumber(value);
  if (number === null) return "—";
  return `${number.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}${suffix}`;
}

function countryOf(row: NodeListRow): string {
  const explicit = String(row.country_code || "").trim().toUpperCase();
  if (explicit) return explicit;
  const inferred = String(row.code || "").split(/[-_]/, 1)[0].slice(0, 2).toUpperCase();
  return inferred || "—";
}

function lifecycleOf(row: NodeListRow): Exclude<NodeLifecycleFilter, "all"> {
  if (!row.enabled) return "disabled";
  if (row.is_draining || !row.accepting_new_clients) return "draining";
  return "enabled";
}

function lifecycleText(row: NodeListRow): string {
  const state = lifecycleOf(row);
  if (state === "enabled") return "Включена";
  if (state === "draining") return "Выводится";
  return "Отключена";
}

function brainStatus(row: NodeListRow) {
  if (!row.freshness_status) return "missing" as const;
  if (row.freshness_status === "stale") return "stale" as const;
  if (row.is_healthy === false) return "failed" as const;
  if (row.is_healthy === true) return "ok" as const;
  return "missing" as const;
}

function worstReason(row: NodeListRow): string {
  if (row.alert_kinds.length) return `${row.alert_kinds.length} активн. сигнал`;
  if (row.is_healthy === false) return "Проверка здоровья не пройдена";
  if (row.capacity_reject_reason) return "Ёмкость ограничивает размещение";
  if (row.freshness_status === "stale") return "Обязательные данные устарели";
  return "Обязательные сигналы без отклонений";
}

function oldestAge(row: NodeListRow, ru: RuNodeStatus | null): number | null {
  const values = [finiteNumber(row.freshness_age_seconds), finiteNumber(ru?.age_seconds)].filter((value): value is number => value !== null);
  return values.length ? Math.max(...values) : null;
}

function ageText(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${seconds} сек`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} мин`;
  return `${Math.floor(seconds / 3600)} ч`;
}

function selectOnKeyboard(event: KeyboardEvent<HTMLTableRowElement>, code: string, onSelect: (code: string) => void) {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  onSelect(code);
}

export function NodeList({
  rows,
  ruByCode,
  filters,
  selected,
  onFiltersChange,
  onSelect
}: {
  rows: NodeListRow[];
  ruByCode: ReadonlyMap<string, RuNodeStatus>;
  filters: NodeFilters;
  selected: string | null;
  onFiltersChange: (patch: Partial<NodeFilters>) => void;
  onSelect: (code: string) => void;
}) {
  const countries = useMemo(() => [...new Set(rows.map(countryOf).filter((value) => value !== "—"))].sort(), [rows]);
  const hosters = useMemo(() => [...new Set(rows.map((row) => row.hoster_family).filter((value): value is string => Boolean(value)))].sort(), [rows]);
  const transports = useMemo(() => [...new Set(rows.flatMap((row) => row.transport_profiles.map((profile) => profile.name)).filter(Boolean))].sort(), [rows]);
  const filteredRows = useMemo(() => {
    const query = filters.q.trim().toLowerCase();
    return rows.filter((row) => {
      if (query) {
        const searchValues = [row.code, row.name, row.hoster_family, row.hoster_asn, row.subnet].map((value) => String(value || "").toLowerCase());
        if (!searchValues.some((value) => value.includes(query))) return false;
      }
      if (filters.state !== "all" && lifecycleOf(row) !== filters.state) return false;
      const freshness = row.freshness_status === "fresh" ? "fresh" : row.freshness_status === "stale" ? "stale" : "missing";
      if (filters.freshness !== "all" && freshness !== filters.freshness) return false;
      if (filters.country !== "all" && countryOf(row) !== filters.country) return false;
      if (filters.hoster !== "all" && row.hoster_family !== filters.hoster) return false;
      if (filters.transport !== "all" && !row.transport_profiles.some((profile) => profile.name === filters.transport)) return false;
      const hasAlert = row.alert_kinds.length > 0;
      if (filters.alert === "with" && !hasAlert) return false;
      if (filters.alert === "without" && hasAlert) return false;
      return true;
    });
  }, [filters, rows]);

  return (
    <div className="space-y-3">
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <label className="xl:col-span-2">
          <span className="mb-1 block text-[11px] font-semibold text-[color:var(--atlas-text-soft)]">Поиск</span>
          <input
            type="search"
            value={filters.q}
            onChange={(event) => onFiltersChange({ q: event.target.value })}
            aria-label="Поиск по нодам"
            placeholder="Код, хостер, ASN или подсеть"
            className="w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs text-[color:var(--atlas-text)] placeholder:text-[color:var(--atlas-text-muted)]"
          />
        </label>
        <FilterSelect label="Состояние ноды" value={filters.state} onChange={(value) => onFiltersChange({ state: value as NodeLifecycleFilter })} options={[["all", "Все состояния"], ["enabled", "Включена"], ["draining", "Выводится"], ["disabled", "Отключена"]]} />
        <FilterSelect label="Свежесть данных" value={filters.freshness} onChange={(value) => onFiltersChange({ freshness: value as NodeFreshnessFilter })} options={[["all", "Любая свежесть"], ["fresh", "Свежие"], ["stale", "Устаревшие"], ["missing", "Нет данных"]]} />
        <FilterSelect label="Страна" value={filters.country} onChange={(country) => onFiltersChange({ country })} options={[["all", "Все страны"], ...countries.map((country) => [country, country] as [string, string])]} />
        <FilterSelect label="Хостер" value={filters.hoster} onChange={(hoster) => onFiltersChange({ hoster })} options={[["all", "Все хостеры"], ...hosters.map((hoster) => [hoster, hoster] as [string, string])]} />
        <FilterSelect label="Транспорт" value={filters.transport} onChange={(transport) => onFiltersChange({ transport })} options={[["all", "Все транспорты"], ...transports.map((transport) => [transport, transport] as [string, string])]} />
        <FilterSelect label="Активный алерт" value={filters.alert} onChange={(value) => onFiltersChange({ alert: value as NodeAlertFilter })} options={[["all", "Любой"], ["with", "Есть алерт"], ["without", "Без алерта"]]} />
      </div>

      <div className="ops-scrollbar overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]">
        <table aria-label="Список нод" className="w-full min-w-[960px] border-collapse text-left text-xs">
          <thead className="bg-[color:var(--pokrov-table-header-bg)] text-[11px] text-[color:var(--atlas-text-soft)]">
            <tr>
              <th className="px-3 py-2">Нода</th>
              <th className="px-3 py-2">Состояние</th>
              <th className="px-3 py-2">Худший сигнал</th>
              <th className="px-3 py-2">Brain</th>
              <th className="px-3 py-2">RU</th>
              <th className="px-3 py-2">CPU</th>
              <th className="px-3 py-2">Порт</th>
              <th className="px-3 py-2">Клиенты</th>
              <th className="px-3 py-2">Старейший источник</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.length ? filteredRows.map((row) => {
              const code = row.code.toLowerCase();
              const ru = ruByCode.get(code) || null;
              const isSelected = selected === code;
              return (
                <tr
                  key={code}
                  tabIndex={0}
                  aria-selected={isSelected}
                  onClick={() => onSelect(code)}
                  onKeyDown={(event) => selectOnKeyboard(event, code, onSelect)}
                  className={`cursor-pointer border-t border-[color:var(--pokrov-table-divider)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[color:var(--atlas-focus)] ${isSelected ? "bg-[color:var(--pokrov-nav-active-bg)]" : "hover:bg-[color:var(--pokrov-table-row-hover-bg)]"}`}
                >
                  <td className="px-3 py-2">
                    <div className="font-mono text-sm font-semibold uppercase">{row.code}</div>
                    <div className="mt-1 text-[11px] text-[color:var(--atlas-text-soft)]">{countryOf(row)} · {row.name || "Без названия"}</div>
                  </td>
                  <td className="px-3 py-2"><span className="font-semibold">{lifecycleText(row)}</span></td>
                  <td className="max-w-48 px-3 py-2 text-[color:var(--atlas-text-soft)]">{worstReason(row)}</td>
                  <td className="px-3 py-2"><StatusBadge status={brainStatus(row)} /></td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col items-start gap-1">
                      <StatusBadge status={opsStatusFromSource(ru?.status)} />
                      {ru?.status === "not_in_scope" ? <span className="text-[10px] text-[color:var(--atlas-text-muted)]">не в контуре</span> : null}
                    </div>
                  </td>
                  <td className="px-3 py-2 tabular-nums">{formatNumber(row.cpu_percent, "%")}</td>
                  <td className="px-3 py-2 tabular-nums">{formatNumber(row.network_utilization_percent, "%")}</td>
                  <td className="px-3 py-2 tabular-nums"><span>{formatNumber(row.provisioned_clients_count)}</span><span className="text-[color:var(--atlas-text-muted)]"> / {formatNumber(row.online_connections_hint)} онлайн</span></td>
                  <td className="px-3 py-2 tabular-nums">{ageText(oldestAge(row, ru))}</td>
                </tr>
              );
            }) : (
              <tr><td colSpan={9} className="px-3 py-10 text-center text-sm text-[color:var(--atlas-text-muted)]">Ноды по выбранным фильтрам не найдены.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-[color:var(--atlas-text-muted)]">Клиенты: подготовлено / текущая оценка онлайн. «—» означает отсутствие измерения, а не ноль.</p>
    </div>
  );
}

function FilterSelect({ label, value, options, onChange }: { label: string; value: string; options: Array<[string, string]>; onChange: (value: string) => void }) {
  return (
    <label>
      <span className="mb-1 block text-[11px] font-semibold text-[color:var(--atlas-text-soft)]">{label}</span>
      <select
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs text-[color:var(--atlas-text)]"
      >
        {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  );
}
