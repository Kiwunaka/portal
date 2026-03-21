"use client";

import { adminMetricsStatus, adminMetricsTimeseries, adminSummary, type AdminMetricsPoint, type AdminMetricsStatus, type AdminSummaryPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { Activity, RefreshCw, Server, TrendingUp, Users, Ticket, ArrowUp, ArrowDown, AlertTriangle, Gift } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

function lastDaysRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - Math.max(1, days - 1));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function MiniBar({ values, color = "violet" }: { values: number[]; color?: string }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const colorClass = color === "emerald" ? "bg-emerald-500" : color === "rose" ? "bg-rose-500" : "bg-violet-500";
  return (
    <div className="flex h-8 items-end gap-[3px]">
      {values.map((value, index) => (
        <div
          key={index}
          className={`w-[5px] rounded-sm ${colorClass} transition-all duration-300`}
          style={{ height: `${Math.max(8, (value / max) * 100)}%`, opacity: 0.4 + (value / max) * 0.6 }}
        />
      ))}
    </div>
  );
}

function formatSecondsToShortAge(seconds?: number | null): string {
  if (seconds == null || Number.isNaN(Number(seconds))) return "нет данных";
  const total = Math.max(0, Math.round(Number(seconds)));
  if (total < 60) return `${total}с`;
  if (total < 3600) return `${Math.round(total / 60)}м`;
  if (total < 86400) return `${Math.round(total / 3600)}ч`;
  return `${Math.round(total / 86400)}д`;
}

function buildMetricsHealthSummary(metrics: AdminMetricsStatus | null): { value: string; detail: string } {
  if (!metrics) {
    return {
      value: "нет данных",
      detail: "Проверка метрик ещё не завершилась. Обычно это значит, что страница только открылась или collector ещё не отдал свежий срез.",
    };
  }

  const age = formatSecondsToShortAge(metrics.age_seconds);
  const threshold = formatSecondsToShortAge(metrics.stale_after_seconds);
  const sample = metrics.last_sample_at ? fmtRuDate(metrics.last_sample_at) : " ";

  if (metrics.status === "stale") {
    return {
      value: `устарели / ${age}`,
      detail: `Последний срез получен ${sample}. Если возраст больше ${threshold}, данные по нодам уже неактуальны и нужно проверить collector.`,
    };
  }

  return {
    value: `актуальны / ${age}`,
    detail: `Последний срез получен ${sample}. Всё в порядке, пока возраст не превышает ${threshold}.`,
  };
}

export default function AdminDashboardPage() {
  const { loading: sessionLoading, user, webLoginRequired } = usePortalSession();
  const [summary, setSummary] = useState<AdminSummaryPayload | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsStatus | null>(null);
  const [series, setSeries] = useState<AdminMetricsPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async (): Promise<void> => {
    if (sessionLoading || webLoginRequired || !user?.is_admin) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const range = lastDaysRange(7);
      const [sum, status, ts] = await Promise.all([
        adminSummary(),
        adminMetricsStatus(),
        adminMetricsTimeseries(range),
      ]);
      setSummary(sum);
      setMetrics(status);
      setSeries(ts.points || []);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || " "));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionLoading || webLoginRequired || !user?.is_admin) {
      return;
    }
    void refresh();
  }, [sessionLoading, user?.is_admin, webLoginRequired]);

  const totals = useMemo(() => {
    return (series || []).reduce(
      (acc, point) => {
        acc.registrations += Number(point.registrations || 0);
        acc.churn += Number(point.churn || 0);
        acc.revenueRub += Number(point.revenue_rub || 0);
        return acc;
      },
      { registrations: 0, churn: 0, revenueRub: 0 },
    );
  }, [series]);

  const registrationValues = useMemo(() => series.map((p) => Number(p.registrations || 0)), [series]);
  const revenueValues = useMemo(() => series.map((p) => Number(p.revenue_rub || 0)), [series]);
  const metricsHealth = useMemo(() => buildMetricsHealthSummary(metrics), [metrics]);

  const attentionItems = [
    summary?.errors.stale_metrics
      ? `   :   ${metrics?.last_sample_at ? fmtRuDate(metrics.last_sample_at) : ""},  ${formatSecondsToShortAge(metrics?.age_seconds)}.`
      : "",
    Number(summary?.errors.unhealthy_nodes || 0) > 0
      ? `   : ${summary?.errors.unhealthy_nodes}.   ,     .`
      : "",
    Number(summary?.errors.payment_callback_failures_24h || 0) > 0
      ? `    ${summary?.errors.payment_callback_failures_24h}   24 .     ,     .`
      : "",
    Number(summary?.errors.subscription_numeric_fallbacks_24h || 0) > 0
      ? `     ${summary?.errors.subscription_numeric_fallbacks_24h}   24 .  ,        .`
      : "",
    Number(summary?.errors.open_tickets || 0) > 0
      ? `   ${summary?.errors.open_tickets}  . ,         .`
      : "",
    Number(summary?.bonus_events_24h.channel_denied || 0) > Number(summary?.bonus_events_24h.channel_activated || 0)
      ? `     ,   : ${summary?.bonus_events_24h.channel_denied}  ${summary?.bonus_events_24h.channel_activated}.      .`
      : "",
    Number(summary?.bonus_events_24h.promo_denied || 0) > Number(summary?.bonus_events_24h.promo_redeemed || 0)
      ? `   ,   : ${summary?.bonus_events_24h.promo_denied}  ${summary?.bonus_events_24h.promo_redeemed}. ,       .`
      : "",
    Number(summary?.bonus_events_24h.gift_denied || 0) > Number(summary?.bonus_events_24h.gift_redeemed || 0)
      ? `    ,   : ${summary?.bonus_events_24h.gift_denied}  ${summary?.bonus_events_24h.gift_redeemed}.       .`
      : "",
  ].filter(Boolean);

  const errorCards = [
    {
      label: "Метрики",
      value: metricsHealth.value,
      tone: summary?.errors.stale_metrics ? "badge-warning" : "badge-success",
      detail: metricsHealth.detail,
    },
    {
      label: "Ноды с риском",
      value: summary?.errors.unhealthy_nodes ?? "",
      tone: Number(summary?.errors.unhealthy_nodes || 0) > 0 ? "badge-danger" : "badge-success",
      detail: "Ноды, у которых ухудшились отклик, стабильность панели или свежесть метрик.",
    },
    {
      label: "Платежи с ошибкой 24ч",
      value: summary?.errors.payment_callback_failures_24h ?? "",
      tone: Number(summary?.errors.payment_callback_failures_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Платёжные уведомления, которые не удалось принять или обработать.",
    },
    {
      label: "Старые подписки 24ч",
      value: summary?.errors.subscription_numeric_fallbacks_24h ?? "",
      tone: Number(summary?.errors.subscription_numeric_fallbacks_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Случаи, когда система нашла подписку по старой схеме вместо нормального токена.",
    },
    {
      label: "Открытые тикеты",
      value: summary?.errors.open_tickets ?? "",
      tone: Number(summary?.errors.open_tickets || 0) > 0 ? "badge-info" : "badge-success",
      detail: "Текущая очередь поддержки. Чем число выше, тем выше риск задержки ответа.",
    },
  ];

  const statCards = [
    {
      label: "Пользователи",
      value: summary?.users.total ?? "",
      sub: `: ${summary?.users.active ?? ""}`,
      icon: Users,
      iconClass: "stat-icon-violet",
      sparkline: registrationValues,
      sparkColor: "violet" as const,
    },
    {
      label: "Тикеты",
      value: summary?.tickets.open ?? "",
      sub: "Сколько диалогов ждут ответа оператора",
      icon: Ticket,
      iconClass: "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "violet" as const,
    },
    {
      label: "Ноды",
      value: `${summary?.nodes.healthy ?? ""} / ${summary?.nodes.total ?? ""}`,
      sub: metrics?.status === "fresh" ? `  (${formatSecondsToShortAge(metrics?.age_seconds)})` : `  (${formatSecondsToShortAge(metrics?.age_seconds)})`,
      icon: Server,
      iconClass: metrics?.status === "fresh" ? "stat-icon-emerald" : "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "emerald" as const,
    },
    {
      label: "Выручка (7д)",
      value: `${Math.round(totals.revenueRub)} ₽`,
      sub: "�������� ������ �������� �� RUB-������",
      icon: TrendingUp,
      iconClass: "stat-icon-emerald",
      sparkline: revenueValues,
      sparkColor: "emerald" as const,
    },
  ];

  const bonusCards = [
    {
      label: "Бонус за канал: выдан",
      value: summary?.bonus_events_24h.channel_activated ?? "",
      tone: Number(summary?.bonus_events_24h.channel_activated || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Успешные выдачи бонуса за канал за 24ч",
    },
    {
      label: "Бонус за канал: отказ",
      value: summary?.bonus_events_24h.channel_denied ?? "",
      tone: Number(summary?.bonus_events_24h.channel_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Сколько раз бонус не выдался: нет подписки, не выполнены условия или сработали ограничения.",
    },
    {
      label: "Промокоды: сработали",
      value: summary?.bonus_events_24h.promo_redeemed ?? "",
      tone: Number(summary?.bonus_events_24h.promo_redeemed || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Успешные активации промокодов за 24ч",
    },
    {
      label: "Промокоды: отказ",
      value: summary?.bonus_events_24h.promo_denied ?? "",
      tone: Number(summary?.bonus_events_24h.promo_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Промокод не сработал: истёк, уже использован или не подходит под условия.",
    },
    {
      label: "Подарки: сработали",
      value: summary?.bonus_events_24h.gift_redeemed ?? "",
      tone: Number(summary?.bonus_events_24h.gift_redeemed || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Успешные активации gift code за 24ч",
    },
    {
      label: "Подарки: отказ",
      value: summary?.bonus_events_24h.gift_denied ?? "",
      tone: Number(summary?.bonus_events_24h.gift_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Подарочный код не сработал: код уже использован, неверный или не подходит под текущую кампанию.",
    },
  ];

  const retentionCards = [
    {
      label: "Истекают за 3 дня",
      value: summary?.retention.expiring_3d ?? "",
      tone: Number(summary?.retention.expiring_3d || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Пользователи, у которых скоро закончится доступ. Им стоит напомнить о продлении.",
    },
    {
      label: "Истекли за 7 дней",
      value: summary?.retention.expired_7d ?? "",
      tone: Number(summary?.retention.expired_7d || 0) > 0 ? "badge-info" : "badge-success",
      detail: "Пользователи, у которых доступ уже закончился. Это кандидаты на возврат.",
    },
    {
      label: "Кандидаты на reactivate",
      value: summary?.retention.reactivation_candidates ?? "",
      tone: Number(summary?.retention.reactivation_candidates || 0) > 0 ? "badge-info" : "badge-success",
      detail: "База для сценариев возврата и повторного предложения тарифа.",
    },
    {
      label: "Retention ping 24ч",
      value:
        Number(summary?.retention.pings_24h.t3 || 0) +
        Number(summary?.retention.pings_24h.t1 || 0) +
        Number(summary?.retention.pings_24h.t0 || 0),
      tone:
        Number(summary?.retention.pings_24h.t3 || 0) +
          Number(summary?.retention.pings_24h.t1 || 0) +
          Number(summary?.retention.pings_24h.t0 || 0) >
        0
          ? "badge-success"
          : "badge-warning",
      detail: `   : T-3  ${summary?.retention.pings_24h.t3 ?? 0}, T-1  ${summary?.retention.pings_24h.t1 ?? 0}, T0  ${summary?.retention.pings_24h.t0 ?? 0}.`,
    },
    {
      label: "Welcome ping 24ч",
      value: summary?.retention.pings_24h.welcome ?? "",
      tone: Number(summary?.retention.pings_24h.welcome || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Сколько новых пользователей получили первое приветственное сообщение.",
    },
    {
      label: "Reactivate / Start99 24ч",
      value: `${summary?.retention.pings_24h.reactivation ?? 0} / ${summary?.retention.pings_24h.start99_offer ?? 0}`,
      tone:
        Number(summary?.retention.pings_24h.reactivation || 0) > 0 || Number(summary?.retention.pings_24h.start99_offer || 0) > 0
          ? "badge-success"
          : "badge-info",
      detail: "Сколько человек получили предложение вернуться или попробовать стартовый тариф.",
    },
  ];

  return (
    <section className="space-y-5">
      <div className="glass-card p-5">
        <h2 className="font-display text-xl font-bold">Как читать эту страницу</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Этот экран нужен, чтобы за минуту понять общее состояние сервиса. Если времени мало, сначала смотрите блок «Сводка ошибок и рисков», потом «Топ нод», а уже после этого уходите в детали по пользователям и бонусам.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <article key={card.label} className="stat-card p-5">
              <div className="flex items-start justify-between gap-3">
                <div className={`stat-icon ${card.iconClass}`}>
                  <Icon size={20} />
                </div>
                {card.sparkline.length > 0 ? <MiniBar values={card.sparkline} color={card.sparkColor} /> : null}
              </div>
              <p className="mt-3 text-3xl font-bold gradient-text">{card.value}</p>
              <p className="mt-1 text-xs uppercase tracking-[0.12em] text-slate-500">{card.label}</p>
              <p className="mt-0.5 text-xs text-slate-500">{card.sub}</p>
            </article>
          );
        })}
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <Activity size={20} />
            </div>
            <div>
              <h2 className="font-display text-xl font-bold">Дневные метрики</h2>
              <p className="text-xs text-slate-500">Последние 7 дней</p>
            </div>
          </div>
          <button
            className="outline-btn inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold"
            type="button"
            onClick={() => void refresh()}
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Обновить
          </button>
        </div>
        {loading ? <p className="text-sm text-slate-500">...</p> : null}
        {error ? <p className="text-sm text-rose-500">{error}</p> : null}
        {!loading && !error ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-3 py-2.5">Дата</th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1"><ArrowUp size={12} className="text-emerald-500" /> Регистрации</span>
                  </th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1"><ArrowDown size={12} className="text-rose-500" /> Отток</span>
                  </th>
                  <th className="px-3 py-2.5">RUB</th>
                </tr>
              </thead>
              <tbody>
                {series.map((point, idx) => (
                  <tr key={point.date} className={`border-t border-white/20 dark:border-white/5 ${idx % 2 === 0 ? "bg-white/30 dark:bg-white/[0.02]" : ""}`}>
                    <td className="px-3 py-2.5 font-medium">{fmtRuDate(point.date)}</td>
                    <td className="px-3 py-2.5">
                      {Number(point.registrations) > 0 ? <span className="badge badge-success">{point.registrations}</span> : <span className="text-slate-400">0</span>}
                    </td>
                    <td className="px-3 py-2.5">
                      {Number(point.churn) > 0 ? <span className="badge badge-danger">{point.churn}</span> : <span className="text-slate-400">0</span>}
                    </td>
                    <td className="px-3 py-2.5 font-medium">{Math.round(point.revenue_rub || 0)} ₽</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-emerald">
            <Server size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Топ нод</h2>
            <p className="text-xs text-slate-500">Здоровье и метрики по нодам</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(summary?.top_nodes || []).map((node) => {
            const score = Number(node.health_score || 0);
            const healthPct = Math.min(100, Math.max(0, score * 10));
            const fillClass = score >= 8 ? "progress-fill-emerald" : score >= 5 ? "progress-fill-amber" : "progress-fill-rose";
            return (
              <article key={node.code} className="node-card">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`status-dot ${score >= 8 ? "status-dot-online" : score >= 5 ? "status-dot-warning" : "status-dot-offline"}`} />
                    <strong className="text-sm font-bold">{node.code.toUpperCase()}</strong>
                  </div>
                  <span className={`badge ${score >= 8 ? "badge-success" : score >= 5 ? "badge-warning" : "badge-danger"}`}>
                    {score.toFixed(1)}
                  </span>
                </div>
                <div className="mt-3">
                  <div className="progress-track">
                    <div className={`progress-fill ${fillClass}`} style={{ width: `${healthPct}%` }} />
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                  <span>: {node.panel_latency_ms ?? ""} ms</span>
                  <span className="font-medium">{node.active_clients} клиентов</span>
                </div>
              </article>
            );
          })}
          {(summary?.top_nodes || []).length === 0 && !loading ? (
            <div className="empty-state col-span-full">
              <Server size={32} />
              <p className="text-sm">Нет данных о нодах</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-amber">
            <AlertTriangle size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Сводка ошибок и рисков</h2>
            <p className="text-xs text-slate-500">То, что сейчас требует внимания оператора</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {errorCards.map((card) => (
            <article key={card.label} className="node-card">
              <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">{card.label}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className={`badge ${card.tone}`}>{card.value}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{card.detail}</p>
            </article>
          ))}
        </div>
        {attentionItems.length ? (
          <div className="mt-4 rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-amber-300">Что проверить сейчас</p>
            <ul className="mt-2 space-y-2 text-sm text-slate-200">
              {attentionItems.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-300" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-200">
            Критичных сигналов сейчас нет: метрики свежие, callback-ошибки и fallback-хиты под контролем.
          </div>
        )}
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-violet">
            <Gift size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Бонусы и промо за 24 часа</h2>
            <p className="text-xs text-slate-500">Показывает, сколько бонусов реально сработало, а сколько не выдалось из-за условий или ошибок.</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {bonusCards.map((card) => (
            <article key={card.label} className="node-card">
              <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">{card.label}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className={`badge ${card.tone}`}>{card.value}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{card.detail}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-blue">
            <TrendingUp size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Удержание и реактивация</h2>
            <p className="text-xs text-slate-500">Помогает понять, кому пора напомнить о продлении и кого уже стоит возвращать обратно.</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {retentionCards.map((card) => (
            <article key={card.label} className="node-card">
              <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">{card.label}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className={`badge ${card.tone}`}>{card.value}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{card.detail}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="stat-card p-4">
        <div className="flex items-center gap-3">
          <div className="stat-icon stat-icon-violet">
            <Activity size={18} />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Итого за 7 дней: <strong>{totals.registrations}</strong> регистраций, <strong>{totals.churn}</strong> отток, выручка <strong>{Math.round(totals.revenueRub)} ₽</strong> и
          </p>
        </div>
      </div>
      {summary?.errors.stale_metrics || Number(summary?.errors.unhealthy_nodes || 0) > 0 || summary?.resilience.single_point_risk ? (
        <p className="text-xs text-amber-500">
          Перед релизом или рассылкой проверьте таймер метрик, свежесть срезов и ноды с предупреждениями.
        </p>
      ) : null}
    </section>
  );
}

