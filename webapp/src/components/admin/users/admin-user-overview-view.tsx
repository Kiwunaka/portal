"use client";

import { adminButtonClass, adminInsetPanelClass } from "@/components/admin/admin-shell";
import type { AdminUserCard } from "@/lib/api";
import { ACTIVE_USERS_HINT, ACTIVE_USERS_LABEL, fmtTraffic, observerHasData, observerStateBadgeClass, observerStateLabel, panelStateLabel, ticketStatusLabel } from "./admin-users-format";

type AdminUserOverviewViewProps = {
  selected: AdminUserCard;
  busy: boolean;
  onGrantLoyalty: (tierDays: number) => void;
};

export function AdminUserOverviewView({ selected, busy, onGrantLoyalty }: AdminUserOverviewViewProps) {
  const summary = selected.summary;
  const observer = selected.observer;
  const loyalty = selected.loyalty;

  return (
    <div className="mt-3 space-y-3">
      <div className={adminInsetPanelClass}>
        <p className="text-sm font-semibold text-[color:var(--atlas-text)]">Сводка по подключению</p>
        <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-muted)]">
          Здесь видно, на каких нодах есть пользователь, работает ли подключение и совпадает ли состояние панелей.
        </p>
        {summary ? (
          <>
            <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
              <p>Нод с пользователем: <strong>{summary.nodes_with_client}/{summary.nodes_total}</strong></p>
              <p>Нод в сети: <strong>{summary.nodes_online}</strong></p>
              <p>Ключей в сети сейчас: <strong>{summary.online_keys_now}</strong></p>
              <p>Подключений сейчас: <strong>{summary.online_connections_now}</strong></p>
              <p>Включённых нод: <strong>{summary.nodes_enabled}</strong></p>
              <p>Расхождений по подписке: <strong>{summary.subid_mismatch_count}</strong></p>
              <p>Всего трафика: <strong>{fmtTraffic(summary.traffic_total_bytes)}</strong></p>
              <p>Состояние панелей: <strong>{panelStateLabel(String(summary.panel_state || ""))}</strong></p>
            </div>
            <div className="mt-3 rounded-xl border border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] p-3 text-xs text-emerald-100">
              <p className="font-semibold">
                {ACTIVE_USERS_LABEL}: {summary.active_users_estimate}
              </p>
              <p className="mt-1 text-emerald-200/80">{ACTIVE_USERS_HINT}</p>
            </div>
          </>
        ) : (
          <p className="mt-3 text-xs text-[color:var(--atlas-text-muted)]">Сводка по этому пользователю пока недоступна.</p>
        )}
        {summary?.online_node_codes_now?.length ? (
          <p className="mt-3 text-xs text-[color:var(--atlas-text-muted)]">
            Сейчас в сети на нодах: <strong>{summary.online_node_codes_now.map((code) => String(code || "").toUpperCase()).join(", ")}</strong>
          </p>
        ) : (
          <p className="mt-3 text-xs text-[color:var(--atlas-text-muted)]">Сейчас пользователь не виден онлайн на нодах.</p>
        )}
      </div>

      <div className={adminInsetPanelClass}>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <p className="text-sm font-semibold text-[color:var(--atlas-text)]">Проверка по IP и нодам</p>
          <span className={`badge ${observerStateBadgeClass(observer?.state || selected.user.observer_state)}`}>
            {observerStateLabel(observer?.state || selected.user.observer_state)}
          </span>
        </div>
        {!observerHasData(observer) ? (
          <p className="text-xs text-[color:var(--atlas-text-muted)]">Данных наблюдения пока нет.</p>
        ) : (
          <div className="grid gap-3 lg:grid-cols-[minmax(0,0.9fr),minmax(0,1.1fr)]">
            <div className="space-y-1 text-xs text-[color:var(--atlas-text-muted)]">
              <p>IP: <strong>{observer?.observed_ip_count_24h ?? 0}</strong> / 24 ч, <strong>{observer?.observed_ip_count_7d ?? 0}</strong> / 7 дн., <strong>{observer?.observed_ip_count_30d ?? 0}</strong> / 30 дн.</p>
              <p>Ноды: <strong>{observer?.observed_node_count_24h ?? 0}</strong> / 24 ч, <strong>{observer?.observed_node_count_7d ?? 0}</strong> / 7 дн., <strong>{observer?.observed_node_count_30d ?? 0}</strong> / 30 дн.</p>
              <p>Совпадения за 24 ч: <strong>{observer?.overlap_count_24h ?? 0}</strong></p>
              <p>Последнее наблюдение: <strong>{observer?.last_observed_at ? new Date(observer.last_observed_at).toLocaleString("ru-RU") : "-"}</strong></p>
              <p>Причины: <strong>{observer?.reasons?.length ? observer.reasons.join(", ") : "нет"}</strong></p>
            </div>
            <div className="grid gap-3 lg:grid-cols-2">
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-text-soft)]">Последние IP</p>
                <div className="space-y-2">
                  {(observer?.recent_ips || []).map((row) => (
                    <div key={`${row.node_code}:${row.source_ip_raw}:${row.last_seen_at}`} className="rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2 text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{row.source_ip_raw}</span>
                        <span className="text-[color:var(--atlas-text-soft)]">{row.node_code || "-"}</span>
                      </div>
                      <div className="mt-1 text-[11px] text-[color:var(--atlas-text-soft)]">
                        {row.node_name || "нода"} · {row.last_seen_at ? new Date(row.last_seen_at).toLocaleString("ru-RU") : "-"} · {row.counts_for_suspicion ? "учитывается" : "не учитывается"}
                      </div>
                    </div>
                  ))}
                  {!observer?.recent_ips?.length ? <p className="text-xs text-[color:var(--atlas-text-muted)]">Последних IP нет.</p> : null}
                </div>
              </div>
              <div>
                <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--atlas-text-soft)]">Последние ноды</p>
                <div className="space-y-2">
                  {(observer?.recent_nodes || []).map((row) => (
                    <div key={`${row.node_id}:${row.last_seen_at}`} className="rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2 text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{row.node_code || `нода #${row.node_id}`}</span>
                        <span className="text-[color:var(--atlas-text-soft)]">IP: {row.score_ip_count}</span>
                      </div>
                      <div className="mt-1 text-[11px] text-[color:var(--atlas-text-soft)]">
                        {row.node_name || "нода"} · {row.last_seen_at ? new Date(row.last_seen_at).toLocaleString("ru-RU") : "-"}
                      </div>
                    </div>
                  ))}
                  {!observer?.recent_nodes?.length ? <p className="text-xs text-[color:var(--atlas-text-muted)]">Последних нод нет.</p> : null}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className={adminInsetPanelClass}>
        <p className="text-sm font-semibold text-[color:var(--atlas-text)]">Последние обращения</p>
        {selected.tickets?.length ? (
          <div className="mt-3 space-y-2">
            {selected.tickets.map((ticket) => (
              <div key={ticket.id} className="rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-2 text-xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold">{ticket.subject || `Обращение #${ticket.id}`}</p>
                  <span className="badge badge-violet">{ticketStatusLabel(ticket.status)}</span>
                </div>
                <p className="mt-1 text-[color:var(--atlas-text-muted)]">{ticket.last_message_preview || ticket.messages?.at(-1)?.body || "Без сообщения"}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-2 text-xs text-[color:var(--atlas-text-muted)]">Обращений пока нет.</p>
        )}
      </div>

      {loyalty?.tiers?.length ? (
        <div className={adminInsetPanelClass}>
          <p className="text-sm font-semibold text-[color:var(--atlas-text)]">Бонусы за лояльность</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {loyalty.tiers.map((tier) => (
              <div key={tier.reward_key} className="rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] p-3 text-xs">
                <p className="font-semibold">{tier.days} дн.</p>
                <p>Бонус: {tier.bonus_days} дн.</p>
                <p>Перк: {tier.perk}</p>
                <p className="mt-1">Статус: {tier.claimed ? "выдано" : tier.unlocked ? "готово к выдаче" : "заблокировано"}</p>
                {!tier.claimed && tier.unlocked ? (
                  <button className={`${adminButtonClass("secondary", "xs")} mt-2`} type="button" disabled={busy} onClick={() => onGrantLoyalty(tier.days)}>
                    Выдать награду
                  </button>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
