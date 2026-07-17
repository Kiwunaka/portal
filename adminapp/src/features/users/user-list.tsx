"use client";

import { useEffect, useId, useState, type RefObject } from "react";
import { Search } from "lucide-react";

import { Badge, Button } from "@/components/ui";
import { EmptyState } from "@/components/ui/states";
import { OpsTooltip } from "@/components/ui/tooltip";
import type { AdminOnlineUser } from "@/lib/admin-api/support";
import type { AdminUserListRow, UserListSort, UserListStatus } from "@/lib/admin-api/users";
import { formatSourceAge } from "@/lib/ops-status/presentation";

export type UserListFilters = {
  q: string;
  status: UserListStatus;
  sort: UserListSort;
};

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: "Активен",
    inactive: "Неактивен",
    expired: "Истёк",
    blocked: "Заблокирован",
    manual: "Тестовый",
    manual_test: "Тестовый",
  };
  return labels[status.toLowerCase()] || "Неизвестно";
}

function statusTone(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "active") return "success";
  if (["expired", "manual", "manual_test", "watch", "observer_watch"].includes(status)) return "warning";
  if (["blocked", "suspicious", "observer_suspicious"].includes(status)) return "danger";
  return "neutral";
}

function planLabel(plan: string | null): string {
  const value = String(plan || "").toLowerCase();
  if (value === "paid") return "Платный";
  if (value === "free") return "Бесплатный";
  if (value === "manual") return "Ручной";
  return plan || "Не указан";
}

function dateText(value: string | null): string {
  if (!value) return "Нет данных";
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return "Нет данных";
  return new Date(parsed).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function userName(row: AdminUserListRow): string {
  return row.displayName || (row.username ? `@${row.username}` : `Пользователь ${row.tgId}`);
}

export function UserList({
  rows,
  total,
  onlineByTgId,
  onlineSampledAt,
  filters,
  selected,
  onFiltersChange,
  onSelect,
  scrollRef,
}: {
  rows: AdminUserListRow[];
  total: number;
  onlineByTgId: ReadonlyMap<number, AdminOnlineUser>;
  onlineSampledAt: string | null;
  filters: UserListFilters;
  selected: number | null;
  onFiltersChange: (patch: Partial<UserListFilters>) => void;
  onSelect: (tgId: number) => void;
  scrollRef: RefObject<HTMLDivElement | null>;
}) {
  const [queryDraft, setQueryDraft] = useState(filters.q);
  const tooltipId = useId();

  useEffect(() => setQueryDraft(filters.q), [filters.q]);

  return (
    <div className="space-y-3">
      <form
        role="search"
        aria-label="Поиск пользователей"
        className="grid gap-2 md:grid-cols-[minmax(220px,1fr)_160px_190px_auto]"
        onSubmit={(event) => {
          event.preventDefault();
          onFiltersChange({ q: queryDraft.trim() });
        }}
      >
        <label className="relative">
          <span className="sr-only">Поиск по пользователям</span>
          <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--atlas-text-muted)]" size={15} />
          <input
            type="search"
            value={queryDraft}
            onChange={(event) => setQueryDraft(event.target.value)}
            placeholder="Telegram ID, имя, ID установки, почта"
            className="min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] pl-9 pr-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
          />
        </label>
        <label>
          <span className="sr-only">Статус доступа</span>
          <select
            aria-label="Статус доступа"
            value={filters.status}
            onChange={(event) => onFiltersChange({ status: event.target.value as UserListStatus })}
            className="min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
          >
            <option value="all">Все статусы</option>
            <option value="active">Активные</option>
            <option value="inactive">Неактивные</option>
            <option value="expired">Истёкшие</option>
            <option value="blocked">Заблокированные</option>
            <option value="manual">Тестовые</option>
          </select>
        </label>
        <label>
          <span className="sr-only">Сортировка пользователей</span>
          <select
            aria-label="Сортировка пользователей"
            value={filters.sort}
            onChange={(event) => onFiltersChange({ sort: event.target.value as UserListSort })}
            className="min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
          >
            <option value="created_desc">Сначала новые</option>
            <option value="created_asc">Сначала старые</option>
            <option value="expiry_asc">Скоро истекают</option>
            <option value="expiry_desc">Позже истекают</option>
            <option value="name_asc">Имя: А—Я</option>
            <option value="name_desc">Имя: Я—А</option>
          </select>
        </label>
        <Button type="submit" tone="primary"><Search size={15} /> Найти</Button>
      </form>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[color:var(--atlas-text-soft)]">
        <span>Найдено: {new Intl.NumberFormat("ru-RU").format(total)}</span>
        <span>Присутствие в сети берётся из отдельного оперативного снимка без исходных IP-адресов.</span>
      </div>

      {rows.length ? (
        <div ref={scrollRef} className="ops-scrollbar max-h-[calc(100vh-19rem)] overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]">
          <table className="w-full min-w-[940px] border-collapse text-left text-xs">
            <thead className="sticky top-0 z-10 bg-[color:var(--pokrov-table-header-bg)] text-[11px] text-[color:var(--atlas-text-soft)]">
              <tr>
                <th className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">Пользователь</th>
                <th className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">Доступ</th>
                <th className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">План</th>
                <th className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">Истекает</th>
                <th className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">
                  <span className="inline-flex items-center gap-1">Онлайн и источник <OpsTooltip id={`${tooltipId}-online`} content="Оперативный снимок панели сопоставляется по Telegram ID. Отсутствие строки означает только отсутствие в текущем снимке, а не подтверждённый офлайн." source="Панель · агрегат без исходных IP-адресов" sampledAt={onlineSampledAt} threshold="Обновление каждые 30 секунд в разделе «Сейчас онлайн»" /></span>
                </th>
                <th className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">Ноды сейчас</th>
                <th className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">Наблюдатель</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const online = onlineByTgId.get(row.tgId);
                const isSelected = selected === row.tgId;
                return (
                  <tr key={row.tgId} className={`border-b border-[color:var(--pokrov-table-divider)] ${isSelected ? "bg-[color:var(--pokrov-nav-active-bg)]" : "hover:bg-[color:var(--pokrov-table-row-hover-bg)]"}`}>
                    <td className="px-3 py-2 align-middle">
                      <button type="button" aria-current={isSelected ? "true" : undefined} onClick={() => onSelect(row.tgId)} className="min-h-10 text-left font-semibold text-[color:var(--atlas-text)] hover:underline">
                        {userName(row)}
                        <span className="block font-mono text-[10px] font-normal text-[color:var(--atlas-text-muted)]">TG {row.tgId}</span>
                      </button>
                    </td>
                    <td className="px-3 py-2"><Badge tone={statusTone(row.status)}>{statusLabel(row.status)}</Badge></td>
                    <td className="px-3 py-2">{planLabel(row.plan)}</td>
                    <td className="px-3 py-2 tabular-nums"><time dateTime={row.expiryAt || undefined}>{dateText(row.expiryAt)}</time></td>
                    <td className="px-3 py-2">
                      {online ? (
                        <div>
                          <Badge tone="success">Сейчас в сети</Badge>
                          <div className="mt-1 text-[11px] text-[color:var(--atlas-text-muted)]">{online.onlineConnectionsNow} соединений · {online.lastOnlineAt ? formatSourceAge(online.lastOnlineAt) : "возраст неизвестен"}</div>
                        </div>
                      ) : <span className="text-[color:var(--atlas-text-muted)]">Нет в оперативном снимке</span>}
                    </td>
                    <td className="px-3 py-2">{online?.nodesOnline.length ? online.nodesOnline.join(", ") : "Нет данных"}</td>
                    <td className="px-3 py-2"><Badge tone={statusTone(row.observerState)}>{row.observerState === "ok" ? "Норма" : row.observerState === "watch" ? "Наблюдение" : row.observerState === "suspicious" ? "Подозрение" : "Нет данных"}</Badge></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="Пользователи не найдены" description="Измените поиск или фильтр статуса. Пустой результат не означает отсутствие пользователей в базе." />
      )}
    </div>
  );
}
