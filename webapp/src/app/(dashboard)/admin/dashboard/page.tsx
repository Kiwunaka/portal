"use client";

import {
  adminMetricsStatus,
  adminMetricsTimeseries,
  adminSummary,
  type AdminMetricsPoint,
  type AdminMetricsStatus,
  type AdminSummaryPayload,
} from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Gift,
  RefreshCw,
  Server,
  Ticket,
  TrendingUp,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
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

function metricsSummary(metrics: AdminMetricsStatus | null): { value: string; detail: string } {
  if (!metrics) {
    return {
      value: "нет данных",
      detail: "Сборщик метрик еще не отдал свежий срез. Обычно это бывает сразу после открытия страницы или при проблеме с таймером.",
    };
  }

  const age = formatSecondsToShortAge(metrics.age_seconds);
  const threshold = formatSecondsToShortAge(metrics.stale_after_seconds);
  const sample = metrics.last_sample_at ? fmtRuDate(metrics.last_sample_at) : "нет данных";

  if (metrics.status === "stale") {
    return {
      value: `устарели / ${age}`,
      detail: `Последний срез получен ${sample}. Если возраст больше ${threshold}, нужно проверить сборщик и таймер метрик.`,
    };
  }

  if (metrics.status === "missing") {
    return {
      value: "нет данных",
      detail: "Метрики по нодам пока не пришли. Проверьте таймер и админ-API статуса.",
    };
  }

  return {
    value: `свежие / ${age}`,
    detail: `Последний срез получен ${sample}. Пока возраст не превышает ${threshold}, данные по нодам считаются актуальными.`,
  };
}

function toneByScore(score: number): string {
  if (score >= 8) return "badge-success";
  if (score >= 5) return "badge-warning";
  return "badge-danger";
}

export default function AdminDashboardPage() {
  const { loading: sessionLoading, user, webLoginRequired } = usePortalSession();
  const [summary, setSummary] = useState<AdminSummaryPayload | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsStatus | null>(null);
  const [series, setSeries] = useState<AdminMetricsPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async (): Promise<void> => {
    if (sessionLoading || webLoginRequired || !user?.is_admin) return;
    setLoading(true);
    setError("");
    try {
      const range = lastDaysRange(7);
      const [sum, status, ts] = await Promise.all([adminSummary(), adminMetricsStatus(), adminMetricsTimeseries(range)]);
      setSummary(sum);
      setMetrics(status);
      setSeries(ts.points || []);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить сводку."));
    } finally {
      setLoading(false);
    }
  }, [sessionLoading, user?.is_admin, webLoginRequired]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const totals = useMemo(
    () =>
      (series || []).reduce(
        (acc, point) => {
          acc.registrations += Number(point.registrations || 0);
          acc.churn += Number(point.churn || 0);
          acc.revenueRub += Number(point.revenue_rub || 0);
          return acc;
        },
        { registrations: 0, churn: 0, revenueRub: 0 },
      ),
    [series],
  );

  const registrationValues = useMemo(() => series.map((point) => Number(point.registrations || 0)), [series]);
  const revenueValues = useMemo(() => series.map((point) => Number(point.revenue_rub || 0)), [series]);
  const health = useMemo(() => metricsSummary(metrics), [metrics]);

  const attentionItems = [
    summary?.errors.stale_metrics
      ? `Метрики устарели: последний срез ${metrics?.last_sample_at ? fmtRuDate(metrics.last_sample_at) : "неизвестно"}, возраст ${formatSecondsToShortAge(metrics?.age_seconds)}.`
      : "",
    Number(summary?.errors.unhealthy_nodes || 0) > 0
      ? `Есть ноды с риском: ${summary?.errors.unhealthy_nodes}. Откройте раздел нод и проверьте задержку, error rate и свежесть метрик по каждой.`
      : "",
    Number(summary?.errors.payment_callback_failures_24h || 0) > 0
      ? `Проблемные платежные callback за 24 часа: ${summary?.errors.payment_callback_failures_24h}. Проверьте прием платежей и логи кассы.`
      : "",
    Number(summary?.errors.subscription_numeric_fallbacks_24h || 0) > 0
      ? `Сработал резервный поиск по старым подпискам: ${summary?.errors.subscription_numeric_fallbacks_24h}. Это сигнал проверить миграцию на токены.`
      : "",
    Number(summary?.errors.open_tickets || 0) > 0
      ? `Открытых тикетов: ${summary?.errors.open_tickets}. Посмотрите очередь поддержки, чтобы не копить задержку ответов.`
      : "",
    Number(summary?.bonus_events_24h.channel_denied || 0) > Number(summary?.bonus_events_24h.channel_activated || 0)
      ? `Отказов по бонусу за канал больше, чем выдач: ${summary?.bonus_events_24h.channel_denied} против ${summary?.bonus_events_24h.channel_activated}.`
      : "",
    summary?.resilience.single_point_risk ? "Есть риск единой точки отказа. Перед релизом проверьте резерв по нодам и управляющей панели." : "",
  ].filter(Boolean);

  const errorCards = [
    {
      label: "Метрики",
      value: health.value,
      tone: summary?.errors.stale_metrics ? "badge-warning" : "badge-success",
      detail: health.detail,
    },
    {
      label: "Ноды с риском",
      value: summary?.errors.unhealthy_nodes ?? 0,
      tone: Number(summary?.errors.unhealthy_nodes || 0) > 0 ? "badge-danger" : "badge-success",
      detail: "Ноды, где ухудшились задержка, error rate, health score или свежесть метрик.",
    },
    {
      label: "Ошибки платежей 24ч",
      value: summary?.errors.payment_callback_failures_24h ?? 0,
      tone: Number(summary?.errors.payment_callback_failures_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Платежные callback, которые не удалось принять или обработать.",
    },
    {
      label: "Резервный поиск подписок 24ч",
      value: summary?.errors.subscription_numeric_fallbacks_24h ?? 0,
      tone: Number(summary?.errors.subscription_numeric_fallbacks_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Случаи, когда система искала доступ по старой числовой схеме вместо нормального токена.",
    },
    {
      label: "Открытые тикеты",
      value: summary?.errors.open_tickets ?? 0,
      tone: Number(summary?.errors.open_tickets || 0) > 0 ? "badge-info" : "badge-success",
      detail: "Текущая очередь поддержки, которая требует ответа оператора.",
    },
  ];

  const statCards = [
    {
      label: "Пользователи",
      value: summary?.users.total ?? 0,
      sub: `Активные: ${summary?.users.active ?? 0}`,
      icon: Users,
      iconClass: "stat-icon-violet",
      sparkline: registrationValues,
      sparkColor: "violet" as const,
    },
    {
      label: "Тикеты",
      value: summary?.tickets.open ?? 0,
      sub: "Сколько диалогов ждут ответа оператора",
      icon: Ticket,
      iconClass: "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "violet" as const,
    },
    {
      label: "Ноды",
      value: `${summary?.nodes.healthy ?? 0} / ${summary?.nodes.total ?? 0}`,
      sub: metrics?.status === "fresh" ? `Метрики свежие (${formatSecondsToShortAge(metrics?.age_seconds)})` : `Проверьте свежесть (${formatSecondsToShortAge(metrics?.age_seconds)})`,
      icon: Server,
      iconClass: metrics?.status === "fresh" ? "stat-icon-emerald" : "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "emerald" as const,
    },
    {
      label: "Выручка (7д)",
      value: `${Math.round(totals.revenueRub)} ₽`,
      sub: "Сумма оплаченных событий за последние семь дней",
      icon: TrendingUp,
      iconClass: "stat-icon-emerald",
      sparkline: revenueValues,
      sparkColor: "emerald" as const,
    },
    {
      label: "Observer watch",
      value: summary?.observer.watch_users ?? 0,
      sub: "Пользователи под наблюдением observer-lite",
      icon: Activity,
      iconClass: Number(summary?.observer.watch_users || 0) > 0 ? "stat-icon-amber" : "stat-icon-blue",
      sparkline: [] as number[],
      sparkColor: "violet" as const,
    },
    {
      label: "Observer suspicious",
      value: summary?.observer.suspicious_users ?? 0,
      sub: "Консервативные подозрения без авто-блокировок",
      icon: AlertTriangle,
      iconClass: Number(summary?.observer.suspicious_users || 0) > 0 ? "stat-icon-rose" : "stat-icon-blue",
      sparkline: [] as number[],
      sparkColor: "rose" as const,
    },
  ];

  const bonusCards = [
    {
      label: "Бонус за канал: выдан",
      value: summary?.bonus_events_24h.channel_activated ?? 0,
      tone: Number(summary?.bonus_events_24h.channel_activated || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Успешные выдачи бонуса за канал за 24 часа.",
    },
    {
      label: "Бонус за канал: отказ",
      value: summary?.bonus_events_24h.channel_denied ?? 0,
      tone: Number(summary?.bonus_events_24h.channel_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Отказы из-за невыполненных условий, лимитов или ошибок проверки.",
    },
    {
      label: "Промокоды: сработали",
      value: summary?.bonus_events_24h.promo_redeemed ?? 0,
      tone: Number(summary?.bonus_events_24h.promo_redeemed || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Успешные активации промокодов за 24 часа.",
    },
    {
      label: "Промокоды: отказ",
      value: summary?.bonus_events_24h.promo_denied ?? 0,
      tone: Number(summary?.bonus_events_24h.promo_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Промокод истек, уже использован или не подходит под условия кампании.",
    },
    {
      label: "Подарки: сработали",
      value: summary?.bonus_events_24h.gift_redeemed ?? 0,
      tone: Number(summary?.bonus_events_24h.gift_redeemed || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Успешные активации подарочных кодов за 24 часа.",
    },
    {
      label: "Подарки: отказ",
      value: summary?.bonus_events_24h.gift_denied ?? 0,
      tone: Number(summary?.bonus_events_24h.gift_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Код уже использован, неверен или не соответствует текущей кампании.",
    },
  ];

  const retentionCards = [
    {
      label: "Истекают за 3 дня",
      value: summary?.retention.expiring_3d ?? 0,
      tone: Number(summary?.retention.expiring_3d || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "Пользователи, которым пора напомнить о продлении.",
    },
    {
      label: "Истекли за 7 дней",
      value: summary?.retention.expired_7d ?? 0,
      tone: Number(summary?.retention.expired_7d || 0) > 0 ? "badge-info" : "badge-success",
      detail: "База для сценариев возврата и повторного предложения тарифа.",
    },
    {
      label: "Кандидаты на возврат",
      value: summary?.retention.reactivation_candidates ?? 0,
      tone: Number(summary?.retention.reactivation_candidates || 0) > 0 ? "badge-info" : "badge-success",
      detail: "Пользователи, которым можно отправить возвратное предложение.",
    },
    {
      label: "Retention-сообщения 24ч",
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
      detail: `Отправлено: за 3 дня — ${summary?.retention.pings_24h.t3 ?? 0}, за 1 день — ${summary?.retention.pings_24h.t1 ?? 0}, в день окончания — ${summary?.retention.pings_24h.t0 ?? 0}.`,
    },
    {
      label: "Welcome-сообщения 24ч",
      value: summary?.retention.pings_24h.welcome ?? 0,
      tone: Number(summary?.retention.pings_24h.welcome || 0) > 0 ? "badge-success" : "badge-info",
      detail: "Сколько новых пользователей получили приветственное сообщение.",
    },
    {
      label: "Возврат / Start99 24ч",
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
          Это короткая операционная сводка. Если времени мало, сначала смотрите блок «Сводка ошибок и рисков», затем
          «Топ нод», и только потом переходите в детали по бонусам, удержанию и пользователям.
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
        {loading ? <p className="text-sm text-slate-500">Загружаю сводку...</p> : null}
        {error ? <p className="text-sm text-rose-500">{error}</p> : null}
        {!loading && !error ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-3 py-2.5">Дата</th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1">
                      <ArrowUp size={12} className="text-emerald-500" />
                      Регистрации
                    </span>
                  </th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1">
                      <ArrowDown size={12} className="text-rose-500" />
                      Отток
                    </span>
                  </th>
                  <th className="px-3 py-2.5">RUB</th>
                </tr>
              </thead>
              <tbody>
                {series.map((point, index) => (
                  <tr
                    key={point.date}
                    className={`border-t border-white/20 dark:border-white/5 ${index % 2 === 0 ? "bg-white/30 dark:bg-white/[0.02]" : ""}`}
                  >
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
            <p className="text-xs text-slate-500">Быстрый срез по health score, отклику и активным клиентам.</p>
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
                  <span className={`badge ${toneByScore(score)}`}>{score.toFixed(1)}</span>
                </div>
                <div className="mt-3">
                  <div className="progress-track">
                    <div className={`progress-fill ${fillClass}`} style={{ width: `${healthPct}%` }} />
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                  <span>Latency: {node.panel_latency_ms ?? "—"} ms</span>
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
            <p className="text-xs text-slate-500">То, что сейчас требует внимания оператора.</p>
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
            Критичных сигналов сейчас нет: метрики свежие, callback-ошибки и fallback по подпискам под контролем.
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
            <p className="text-xs text-slate-500">Показывает, сколько бонусов реально сработало и сколько было отказов.</p>
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
            <p className="text-xs text-slate-500">Помогает понять, кому пора напомнить о продлении и кого уже стоит возвращать.</p>
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
            Итого за 7 дней: <strong>{totals.registrations}</strong> регистраций, <strong>{totals.churn}</strong> отток,
            выручка <strong>{Math.round(totals.revenueRub)} ₽</strong>.
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
