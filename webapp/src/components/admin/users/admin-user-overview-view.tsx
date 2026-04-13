"use client";

import type { AdminUserCard } from "@/lib/api";
import { fmtTraffic, observerHasData, observerStateBadgeClass, observerStateLabel, panelStateLabel, ticketStatusLabel, ACTIVE_USERS_HINT, ACTIVE_USERS_LABEL } from "./admin-users-format";

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
    <>
      <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
        <p className="mb-2 font-semibold">Сводка по подключению</p>
        <p className="mb-2 text-xs text-slate-500">
          Единое окно контроля профиля: мониторинг состояния серверов, биллинга и коннекта пользователя.
        </p>
        {summary ? (
          <>
            <div className="grid gap-2 text-xs sm:grid-cols-2">
              <p>Нод с клиентом: <strong>{summary.nodes_with_client}/{summary.nodes_total}</strong></p>
              <p>Нод в сети: <strong>{summary.nodes_online}</strong></p>
              <p>Ключей online сейчас: <strong>{summary.online_keys_now}</strong></p>
              <p>Подключений сейчас: <strong>{summary.online_connections_now}</strong></p>
              <p>Нод в выдаче: <strong>{summary.nodes_enabled}</strong></p>
              <p>Расхождения sub ID: <strong>{summary.subid_mismatch_count}</strong></p>
              <p>Общий трафик: <strong>{fmtTraffic(summary.traffic_total_bytes)}</strong></p>
              <p>Состояние панели: <strong>{panelStateLabel(String(summary.panel_state || ""))}</strong></p>
            </div>
            <div className="mt-3 rounded-xl border border-emerald-200/60 bg-emerald-50/80 p-3 text-xs text-emerald-900 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100">
              <p className="font-semibold">
                {ACTIVE_USERS_LABEL}: {summary.active_users_estimate}
              </p>
              <p className="mt-1 text-emerald-800/80 dark:text-emerald-100/80">{ACTIVE_USERS_HINT}</p>
            </div>
          </>
        ) : (
          <p className="text-xs text-slate-500">Сводка по этому пользователю пока недоступна.</p>
        )}
        {summary?.online_node_codes_now?.length ? (
          <p className="mt-2 text-xs text-slate-500">
            Сейчас online на нодах: <strong>{summary.online_node_codes_now.map((code) => String(code || "").toUpperCase()).join(", ")}</strong>
          </p>
        ) : (
          <p className="mt-2 text-xs text-slate-500">Сейчас online ноды не видны: ключ либо офлайн, либо runtime ещё не обновился.</p>
        )}
      </div>

      <h3 className="mt-4 font-display text-xl font-semibold">Обращения поддержки</h3>
      <div className="mt-4 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <p className="font-semibold">Observer-lite</p>
          <span className={`badge ${observerStateBadgeClass(observer?.state || selected.user.observer_state)}`}>
            {observerStateLabel(observer?.state || selected.user.observer_state)}
          </span>
        </div>
        {!observerHasData(observer) ? (
          <p className="text-xs text-slate-500">Данных наблюдения пока нет.</p>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="space-y-1 text-xs">
              <p>IPs: <strong>{observer?.observed_ip_count_24h ?? 0}</strong> / 24h, <strong>{observer?.observed_ip_count_7d ?? 0}</strong> / 7d, <strong>{observer?.observed_ip_count_30d ?? 0}</strong> / 30d</p>
              <p>Nodes: <strong>{observer?.observed_node_count_24h ?? 0}</strong> / 24h, <strong>{observer?.observed_node_count_7d ?? 0}</strong> / 7d, <strong>{observer?.observed_node_count_30d ?? 0}</strong> / 30d</p>
              <p>Overlap 24h: <strong>{observer?.overlap_count_24h ?? 0}</strong></p>
              <p>Last observed: <strong>{observer?.last_observed_at ? new Date(observer.last_observed_at).toLocaleString("ru-RU") : "-"}</strong></p>
              <p>Reasons: <strong>{observer?.reasons?.length ? observer.reasons.join(", ") : "none"}</strong></p>
            </div>
            <div className="grid gap-3 lg:grid-cols-2">
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Recent IPs</p>
                <div className="space-y-1">
                  {(observer?.recent_ips || []).map((row) => (
                    <div key={`${row.node_code}:${row.source_ip_raw}:${row.last_seen_at}`} className="rounded-lg border border-white/20 bg-white/60 px-2 py-1 text-xs dark:border-white/10 dark:bg-white/5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{row.source_ip_raw}</span>
                        <span className="text-slate-500">{row.node_code || "-"}</span>
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {row.node_name || "node"} · {row.last_seen_at ? new Date(row.last_seen_at).toLocaleString("ru-RU") : "-"} · {row.counts_for_suspicion ? "counts" : "ignore"}
                      </div>
                    </div>
                  ))}
                  {!observer?.recent_ips?.length ? <p className="text-xs text-slate-500">No recent IPs.</p> : null}
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Recent nodes</p>
                <div className="space-y-1">
                  {(observer?.recent_nodes || []).map((row) => (
                    <div key={`${row.node_id}:${row.last_seen_at}`} className="rounded-lg border border-white/20 bg-white/60 px-2 py-1 text-xs dark:border-white/10 dark:bg-white/5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{row.node_code || `node #${row.node_id}`}</span>
                        <span className="text-slate-500">ip count {row.score_ip_count}</span>
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {row.node_name || "node"} · {row.last_seen_at ? new Date(row.last_seen_at).toLocaleString("ru-RU") : "-"}
                      </div>
                    </div>
                  ))}
                  {!observer?.recent_nodes?.length ? <p className="text-xs text-slate-500">No recent nodes.</p> : null}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {selected.tickets?.length ? (
        <div className="mt-4 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
          <p className="mb-2 font-semibold">Последние обращения</p>
          <div className="space-y-2">
            {selected.tickets.map((ticket) => (
              <div key={ticket.id} className="rounded-lg border border-white/20 bg-white/60 px-3 py-2 text-xs dark:border-white/10 dark:bg-white/5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold">{ticket.subject || `Ticket #${ticket.id}`}</p>
                  <span className="badge badge-violet">{ticketStatusLabel(ticket.status)}</span>
                </div>
                <p className="mt-1 text-slate-500">{ticket.last_message_preview || ticket.messages?.at(-1)?.body || "Без сообщения"}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-4 text-xs text-slate-500">Обращений пока нет.</p>
      )}

      {loyalty?.tiers?.length ? (
        <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
          <p className="mb-2 font-semibold">Loyalty-награды (30/90/180)</p>
          <div className="grid gap-2 sm:grid-cols-3">
            {loyalty.tiers.map((tier) => (
              <div key={tier.reward_key} className="rounded-xl border border-white/30 bg-white/70 p-2 text-xs dark:border-white/10 dark:bg-white/5">
                <p className="font-semibold">{tier.days} дн.</p>
                <p>Бонус: {tier.bonus_days} дн.</p>
                <p>Перк: {tier.perk}</p>
                <p className="mt-1">Статус: {tier.claimed ? "выдано" : tier.unlocked ? "готово к выдаче" : "заблокировано"}</p>
                {!tier.claimed && tier.unlocked ? (
                  <button className="mt-2 outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" disabled={busy} onClick={() => onGrantLoyalty(tier.days)}>
                    Выдать награду
                  </button>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}
