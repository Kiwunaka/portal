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
  if (seconds == null || Number.isNaN(Number(seconds))) return "РЅРµС‚ РґР°РЅРЅС‹С…";
  const total = Math.max(0, Math.round(Number(seconds)));
  if (total < 60) return `${total}СЃ`;
  if (total < 3600) return `${Math.round(total / 60)}Рј`;
  if (total < 86400) return `${Math.round(total / 3600)}С‡`;
  return `${Math.round(total / 86400)}Рґ`;
}

function buildMetricsHealthSummary(metrics: AdminMetricsStatus | null): { value: string; detail: string } {
  if (!metrics) {
    return {
      value: "РЅРµС‚ РґР°РЅРЅС‹С…",
      detail: "РџСЂРѕРІРµСЂРєР° РјРµС‚СЂРёРє РµС‰С‘ РЅРµ Р·Р°РІРµСЂС€РёР»Р°СЃСЊ. РћР±С‹С‡РЅРѕ СЌС‚Рѕ Р·РЅР°С‡РёС‚, С‡С‚Рѕ СЃС‚СЂР°РЅРёС†Р° С‚РѕР»СЊРєРѕ РѕС‚РєСЂС‹Р»Р°СЃСЊ РёР»Рё collector РµС‰С‘ РЅРµ РѕС‚РґР°Р» СЃРІРµР¶РёР№ СЃСЂРµР·.",
    };
  }

  const age = formatSecondsToShortAge(metrics.age_seconds);
  const threshold = formatSecondsToShortAge(metrics.stale_after_seconds);
  const sample = metrics.last_sample_at ? fmtRuDate(metrics.last_sample_at) : "РЅРµС‚ СЃСЌРјРїР»Р°";

  if (metrics.status === "stale") {
    return {
      value: `СѓСЃС‚Р°СЂРµР»Рё / ${age}`,
      detail: `РџРѕСЃР»РµРґРЅРёР№ СЃСЂРµР· РїРѕР»СѓС‡РµРЅ ${sample}. Р•СЃР»Рё РІРѕР·СЂР°СЃС‚ Р±РѕР»СЊС€Рµ ${threshold}, РґР°РЅРЅС‹Рµ РїРѕ РЅРѕРґР°Рј СѓР¶Рµ РЅРµР°РєС‚СѓР°Р»СЊРЅС‹ Рё РЅСѓР¶РЅРѕ РїСЂРѕРІРµСЂРёС‚СЊ collector.`,
    };
  }

  return {
    value: `Р°РєС‚СѓР°Р»СЊРЅС‹ / ${age}`,
    detail: `РџРѕСЃР»РµРґРЅРёР№ СЃСЂРµР· РїРѕР»СѓС‡РµРЅ ${sample}. Р’СЃС‘ РІ РїРѕСЂСЏРґРєРµ, РїРѕРєР° РІРѕР·СЂР°СЃС‚ РЅРµ РїСЂРµРІС‹С€Р°РµС‚ ${threshold}.`,
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
      setError(String((err as { message?: string })?.message || err || "РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё"));
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
      ? `РњРµС‚СЂРёРєРё РґР°РІРЅРѕ РЅРµ РѕР±РЅРѕРІР»СЏР»РёСЃСЊ: РїРѕСЃР»РµРґРЅРёР№ СЃСЂРµР· ${metrics?.last_sample_at ? fmtRuDate(metrics.last_sample_at) : "РЅРµРёР·РІРµСЃС‚РµРЅ"}, РІРѕР·СЂР°СЃС‚ ${formatSecondsToShortAge(metrics?.age_seconds)}.`
      : "",
    Number(summary?.errors.unhealthy_nodes || 0) > 0
      ? `Р•СЃС‚СЊ РЅРѕРґС‹ СЃ СЂРёСЃРєРѕРј: ${summary?.errors.unhealthy_nodes}. РЎРЅР°С‡Р°Р»Р° РїСЂРѕРІРµСЂСЊС‚Рµ Р·Р°РґРµСЂР¶РєСѓ, СЃС‚Р°Р±РёР»СЊРЅРѕСЃС‚СЊ РїР°РЅРµР»Рё Рё СЃРІРµР¶РµСЃС‚СЊ РјРµС‚СЂРёРє.`
      : "",
    Number(summary?.errors.payment_callback_failures_24h || 0) > 0
      ? `РџР»Р°С‚С‘Р¶РЅС‹Рµ СѓРІРµРґРѕРјР»РµРЅРёСЏ РґР°Р»Рё РѕС€РёР±РєРё ${summary?.errors.payment_callback_failures_24h} СЂР°Р· Р·Р° 24 С‡Р°СЃР°. Р›СѓС‡С€Рµ РїСЂРѕРІРµСЂРёС‚СЊ Р»РѕРіРё Рё СѓР±РµРґРёС‚СЊСЃСЏ, С‡С‚Рѕ РѕРїР»Р°С‚С‹ РґРѕС…РѕРґСЏС‚ РґРѕ СЃРёСЃС‚РµРјС‹.`
      : "",
    Number(summary?.errors.subscription_numeric_fallbacks_24h || 0) > 0
      ? `РЎС‚Р°СЂС‹Р№ СЃРїРѕСЃРѕР± РїРѕРёСЃРєР° РїРѕРґРїРёСЃРєРё СЃСЂР°Р±РѕС‚Р°Р» ${summary?.errors.subscription_numeric_fallbacks_24h} СЂР°Р· Р·Р° 24 С‡Р°СЃР°. Р­С‚Рѕ Р·РЅР°С‡РёС‚, С‡С‚Рѕ Сѓ С‡Р°СЃС‚Рё РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РµС‰С‘ РѕСЃС‚Р°Р»РёСЃСЊ СЃС‚Р°СЂС‹Рµ С‚РѕРєРµРЅС‹.`
      : "",
    Number(summary?.errors.open_tickets || 0) > 0
      ? `Р’ РїРѕРґРґРµСЂР¶РєРµ СЃРµР№С‡Р°СЃ ${summary?.errors.open_tickets} РѕС‚РєСЂС‹С‚С‹С… РѕР±СЂР°С‰РµРЅРёР№. РџСЂРѕРІРµСЂСЊС‚Рµ, РЅРµ РєРѕРїРёС‚СЃСЏ Р»Рё РѕС‡РµСЂРµРґСЊ РїРµСЂРµРґ Р·Р°РїСѓСЃРєРѕРј СЂР°СЃСЃС‹Р»РєРё РёР»Рё СЂРµР»РёР·Р°.`
      : "",
    Number(summary?.bonus_events_24h.channel_denied || 0) > Number(summary?.bonus_events_24h.channel_activated || 0)
      ? `РџРѕ Р±РѕРЅСѓСЃСѓ Р·Р° РєР°РЅР°Р» РѕС‚РєР°Р·РѕРІ Р±РѕР»СЊС€Рµ, С‡РµРј СѓСЃРїРµС€РЅС‹С… Р°РєС‚РёРІР°С†РёР№: ${summary?.bonus_events_24h.channel_denied} РїСЂРѕС‚РёРІ ${summary?.bonus_events_24h.channel_activated}. РџСЂРѕРІРµСЂСЊС‚Рµ РєР°РЅР°Р» Рё СЃС†РµРЅР°СЂРёР№ РІС‹РґР°С‡Рё Р±РѕРЅСѓСЃР°.`
      : "",
    Number(summary?.bonus_events_24h.promo_denied || 0) > Number(summary?.bonus_events_24h.promo_redeemed || 0)
      ? `РџРѕ РїСЂРѕРјРѕРєРѕРґР°Рј РѕС‚РєР°Р·РѕРІ Р±РѕР»СЊС€Рµ, С‡РµРј СѓСЃРїРµС€РЅС‹С… Р°РєС‚РёРІР°С†РёР№: ${summary?.bonus_events_24h.promo_denied} РїСЂРѕС‚РёРІ ${summary?.bonus_events_24h.promo_redeemed}. Р’РѕР·РјРѕР¶РЅРѕ, С‡Р°СЃС‚СЊ РєРѕРґРѕРІ РёСЃС‚РµРєР»Р° РёР»Рё РЅР°СЃС‚СЂРѕРµРЅР° СЃР»РёС€РєРѕРј СЃС‚СЂРѕРіРѕ.`
      : "",
    Number(summary?.bonus_events_24h.gift_denied || 0) > Number(summary?.bonus_events_24h.gift_redeemed || 0)
      ? `РџРѕ РїРѕРґР°СЂРѕС‡РЅС‹Рј РєРѕРґР°Рј РѕС‚РєР°Р·РѕРІ Р±РѕР»СЊС€Рµ, С‡РµРј СѓСЃРїРµС€РЅС‹С… Р°РєС‚РёРІР°С†РёР№: ${summary?.bonus_events_24h.gift_denied} РїСЂРѕС‚РёРІ ${summary?.bonus_events_24h.gift_redeemed}. РџСЂРѕРІРµСЂСЊС‚Рµ СЃР°РјРё РєРѕРґС‹ Рё РѕРіСЂР°РЅРёС‡РµРЅРёСЏ РґР»СЏ РєР°РјРїР°РЅРёР№.`
      : "",
  ].filter(Boolean);

  const errorCards = [
    {
      label: "РњРµС‚СЂРёРєРё",
      value: metricsHealth.value,
      tone: summary?.errors.stale_metrics ? "badge-warning" : "badge-success",
      detail: metricsHealth.detail,
    },
    {
      label: "РќРѕРґС‹ СЃ СЂРёСЃРєРѕРј",
      value: summary?.errors.unhealthy_nodes ?? "вЂ”",
      tone: Number(summary?.errors.unhealthy_nodes || 0) > 0 ? "badge-danger" : "badge-success",
      detail: "РќРѕРґС‹, Сѓ РєРѕС‚РѕСЂС‹С… СѓС…СѓРґС€РёР»РёСЃСЊ РѕС‚РєР»РёРє, СЃС‚Р°Р±РёР»СЊРЅРѕСЃС‚СЊ РїР°РЅРµР»Рё РёР»Рё СЃРІРµР¶РµСЃС‚СЊ РјРµС‚СЂРёРє.",
    },
    {
      label: "РџР»Р°С‚РµР¶Рё СЃ РѕС€РёР±РєРѕР№ 24С‡",
      value: summary?.errors.payment_callback_failures_24h ?? "вЂ”",
      tone: Number(summary?.errors.payment_callback_failures_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "РџР»Р°С‚С‘Р¶РЅС‹Рµ СѓРІРµРґРѕРјР»РµРЅРёСЏ, РєРѕС‚РѕСЂС‹Рµ РЅРµ СѓРґР°Р»РѕСЃСЊ РїСЂРёРЅСЏС‚СЊ РёР»Рё РѕР±СЂР°Р±РѕС‚Р°С‚СЊ.",
    },
    {
      label: "РЎС‚Р°СЂС‹Рµ РїРѕРґРїРёСЃРєРё 24С‡",
      value: summary?.errors.subscription_numeric_fallbacks_24h ?? "вЂ”",
      tone: Number(summary?.errors.subscription_numeric_fallbacks_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "РЎР»СѓС‡Р°Рё, РєРѕРіРґР° СЃРёСЃС‚РµРјР° РЅР°С€Р»Р° РїРѕРґРїРёСЃРєСѓ РїРѕ СЃС‚Р°СЂРѕР№ СЃС…РµРјРµ РІРјРµСЃС‚Рѕ РЅРѕСЂРјР°Р»СЊРЅРѕРіРѕ С‚РѕРєРµРЅР°.",
    },
    {
      label: "РћС‚РєСЂС‹С‚С‹Рµ С‚РёРєРµС‚С‹",
      value: summary?.errors.open_tickets ?? "вЂ”",
      tone: Number(summary?.errors.open_tickets || 0) > 0 ? "badge-info" : "badge-success",
      detail: "РўРµРєСѓС‰Р°СЏ РѕС‡РµСЂРµРґСЊ РїРѕРґРґРµСЂР¶РєРё. Р§РµРј С‡РёСЃР»Рѕ РІС‹С€Рµ, С‚РµРј РІС‹С€Рµ СЂРёСЃРє Р·Р°РґРµСЂР¶РєРё РѕС‚РІРµС‚Р°.",
    },
  ];

  const statCards = [
    {
      label: "РџРѕР»СЊР·РѕРІР°С‚РµР»Рё",
      value: summary?.users.total ?? "вЂ”",
      sub: `РђРєС‚РёРІРЅС‹Рµ: ${summary?.users.active ?? "вЂ”"}`,
      icon: Users,
      iconClass: "stat-icon-violet",
      sparkline: registrationValues,
      sparkColor: "violet" as const,
    },
    {
      label: "РўРёРєРµС‚С‹",
      value: summary?.tickets.open ?? "вЂ”",
      sub: "РЎРєРѕР»СЊРєРѕ РґРёР°Р»РѕРіРѕРІ Р¶РґСѓС‚ РѕС‚РІРµС‚Р° РѕРїРµСЂР°С‚РѕСЂР°",
      icon: Ticket,
      iconClass: "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "violet" as const,
    },
    {
      label: "РќРѕРґС‹",
      value: `${summary?.nodes.healthy ?? "вЂ”"} / ${summary?.nodes.total ?? "вЂ”"}`,
      sub: metrics?.status === "fresh" ? `РњРµС‚СЂРёРєРё Р°РєС‚СѓР°Р»СЊРЅС‹ (${formatSecondsToShortAge(metrics?.age_seconds)})` : `РњРµС‚СЂРёРєРё СѓСЃС‚Р°СЂРµР»Рё (${formatSecondsToShortAge(metrics?.age_seconds)})`,
      icon: Server,
      iconClass: metrics?.status === "fresh" ? "stat-icon-emerald" : "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "emerald" as const,
    },
    {
      label: "Р’С‹СЂСѓС‡РєР° (7Рґ)",
      value: `${Math.round(totals.revenueRub)} в‚Ѕ`,
      sub: "Основная сводка строится по RUB-кассам",
      icon: TrendingUp,
      iconClass: "stat-icon-emerald",
      sparkline: revenueValues,
      sparkColor: "emerald" as const,
    },
  ];

  const bonusCards = [
    {
      label: "Р‘РѕРЅСѓСЃ Р·Р° РєР°РЅР°Р»: РІС‹РґР°РЅ",
      value: summary?.bonus_events_24h.channel_activated ?? "вЂ”",
      tone: Number(summary?.bonus_events_24h.channel_activated || 0) > 0 ? "badge-success" : "badge-info",
      detail: "РЈСЃРїРµС€РЅС‹Рµ РІС‹РґР°С‡Рё Р±РѕРЅСѓСЃР° Р·Р° РєР°РЅР°Р» Р·Р° 24С‡",
    },
    {
      label: "Р‘РѕРЅСѓСЃ Р·Р° РєР°РЅР°Р»: РѕС‚РєР°Р·",
      value: summary?.bonus_events_24h.channel_denied ?? "вЂ”",
      tone: Number(summary?.bonus_events_24h.channel_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "РЎРєРѕР»СЊРєРѕ СЂР°Р· Р±РѕРЅСѓСЃ РЅРµ РІС‹РґР°Р»СЃСЏ: РЅРµС‚ РїРѕРґРїРёСЃРєРё, РЅРµ РІС‹РїРѕР»РЅРµРЅС‹ СѓСЃР»РѕРІРёСЏ РёР»Рё СЃСЂР°Р±РѕС‚Р°Р»Рё РѕРіСЂР°РЅРёС‡РµРЅРёСЏ.",
    },
    {
      label: "РџСЂРѕРјРѕРєРѕРґС‹: СЃСЂР°Р±РѕС‚Р°Р»Рё",
      value: summary?.bonus_events_24h.promo_redeemed ?? "вЂ”",
      tone: Number(summary?.bonus_events_24h.promo_redeemed || 0) > 0 ? "badge-success" : "badge-info",
      detail: "РЈСЃРїРµС€РЅС‹Рµ Р°РєС‚РёРІР°С†РёРё РїСЂРѕРјРѕРєРѕРґРѕРІ Р·Р° 24С‡",
    },
    {
      label: "РџСЂРѕРјРѕРєРѕРґС‹: РѕС‚РєР°Р·",
      value: summary?.bonus_events_24h.promo_denied ?? "вЂ”",
      tone: Number(summary?.bonus_events_24h.promo_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "РџСЂРѕРјРѕРєРѕРґ РЅРµ СЃСЂР°Р±РѕС‚Р°Р»: РёСЃС‚С‘Рє, СѓР¶Рµ РёСЃРїРѕР»СЊР·РѕРІР°РЅ РёР»Рё РЅРµ РїРѕРґС…РѕРґРёС‚ РїРѕРґ СѓСЃР»РѕРІРёСЏ.",
    },
    {
      label: "РџРѕРґР°СЂРєРё: СЃСЂР°Р±РѕС‚Р°Р»Рё",
      value: summary?.bonus_events_24h.gift_redeemed ?? "вЂ”",
      tone: Number(summary?.bonus_events_24h.gift_redeemed || 0) > 0 ? "badge-success" : "badge-info",
      detail: "РЈСЃРїРµС€РЅС‹Рµ Р°РєС‚РёРІР°С†РёРё gift code Р·Р° 24С‡",
    },
    {
      label: "РџРѕРґР°СЂРєРё: РѕС‚РєР°Р·",
      value: summary?.bonus_events_24h.gift_denied ?? "вЂ”",
      tone: Number(summary?.bonus_events_24h.gift_denied || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "РџРѕРґР°СЂРѕС‡РЅС‹Р№ РєРѕРґ РЅРµ СЃСЂР°Р±РѕС‚Р°Р»: РєРѕРґ СѓР¶Рµ РёСЃРїРѕР»СЊР·РѕРІР°РЅ, РЅРµРІРµСЂРЅС‹Р№ РёР»Рё РЅРµ РїРѕРґС…РѕРґРёС‚ РїРѕРґ С‚РµРєСѓС‰СѓСЋ РєР°РјРїР°РЅРёСЋ.",
    },
  ];

  const retentionCards = [
    {
      label: "РСЃС‚РµРєР°СЋС‚ Р·Р° 3 РґРЅСЏ",
      value: summary?.retention.expiring_3d ?? "вЂ”",
      tone: Number(summary?.retention.expiring_3d || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "РџРѕР»СЊР·РѕРІР°С‚РµР»Рё, Сѓ РєРѕС‚РѕСЂС‹С… СЃРєРѕСЂРѕ Р·Р°РєРѕРЅС‡РёС‚СЃСЏ РґРѕСЃС‚СѓРї. РРј СЃС‚РѕРёС‚ РЅР°РїРѕРјРЅРёС‚СЊ Рѕ РїСЂРѕРґР»РµРЅРёРё.",
    },
    {
      label: "РСЃС‚РµРєР»Рё Р·Р° 7 РґРЅРµР№",
      value: summary?.retention.expired_7d ?? "вЂ”",
      tone: Number(summary?.retention.expired_7d || 0) > 0 ? "badge-info" : "badge-success",
      detail: "РџРѕР»СЊР·РѕРІР°С‚РµР»Рё, Сѓ РєРѕС‚РѕСЂС‹С… РґРѕСЃС‚СѓРї СѓР¶Рµ Р·Р°РєРѕРЅС‡РёР»СЃСЏ. Р­С‚Рѕ РєР°РЅРґРёРґР°С‚С‹ РЅР° РІРѕР·РІСЂР°С‚.",
    },
    {
      label: "РљР°РЅРґРёРґР°С‚С‹ РЅР° reactivate",
      value: summary?.retention.reactivation_candidates ?? "вЂ”",
      tone: Number(summary?.retention.reactivation_candidates || 0) > 0 ? "badge-info" : "badge-success",
      detail: "Р‘Р°Р·Р° РґР»СЏ СЃС†РµРЅР°СЂРёРµРІ РІРѕР·РІСЂР°С‚Р° Рё РїРѕРІС‚РѕСЂРЅРѕРіРѕ РїСЂРµРґР»РѕР¶РµРЅРёСЏ С‚Р°СЂРёС„Р°.",
    },
    {
      label: "Retention ping 24С‡",
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
      detail: `РќР°РїРѕРјРёРЅР°РЅРёСЏ РїРµСЂРµРґ РѕРєРѕРЅС‡Р°РЅРёРµРј РґРѕСЃС‚СѓРїР°: T-3 вЂ” ${summary?.retention.pings_24h.t3 ?? 0}, T-1 вЂ” ${summary?.retention.pings_24h.t1 ?? 0}, T0 вЂ” ${summary?.retention.pings_24h.t0 ?? 0}.`,
    },
    {
      label: "Welcome ping 24С‡",
      value: summary?.retention.pings_24h.welcome ?? "вЂ”",
      tone: Number(summary?.retention.pings_24h.welcome || 0) > 0 ? "badge-success" : "badge-info",
      detail: "РЎРєРѕР»СЊРєРѕ РЅРѕРІС‹С… РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РїРѕР»СѓС‡РёР»Рё РїРµСЂРІРѕРµ РїСЂРёРІРµС‚СЃС‚РІРµРЅРЅРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ.",
    },
    {
      label: "Reactivate / Start99 24С‡",
      value: `${summary?.retention.pings_24h.reactivation ?? 0} / ${summary?.retention.pings_24h.start99_offer ?? 0}`,
      tone:
        Number(summary?.retention.pings_24h.reactivation || 0) > 0 || Number(summary?.retention.pings_24h.start99_offer || 0) > 0
          ? "badge-success"
          : "badge-info",
      detail: "РЎРєРѕР»СЊРєРѕ С‡РµР»РѕРІРµРє РїРѕР»СѓС‡РёР»Рё РїСЂРµРґР»РѕР¶РµРЅРёРµ РІРµСЂРЅСѓС‚СЊСЃСЏ РёР»Рё РїРѕРїСЂРѕР±РѕРІР°С‚СЊ СЃС‚Р°СЂС‚РѕРІС‹Р№ С‚Р°СЂРёС„.",
    },
  ];

  return (
    <section className="space-y-5">
      <div className="glass-card p-5">
        <h2 className="font-display text-xl font-bold">РљР°Рє С‡РёС‚Р°С‚СЊ СЌС‚Сѓ СЃС‚СЂР°РЅРёС†Сѓ</h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Р­С‚РѕС‚ СЌРєСЂР°РЅ РЅСѓР¶РµРЅ, С‡С‚РѕР±С‹ Р·Р° РјРёРЅСѓС‚Сѓ РїРѕРЅСЏС‚СЊ РѕР±С‰РµРµ СЃРѕСЃС‚РѕСЏРЅРёРµ СЃРµСЂРІРёСЃР°. Р•СЃР»Рё РІСЂРµРјРµРЅРё РјР°Р»Рѕ, СЃРЅР°С‡Р°Р»Р° СЃРјРѕС‚СЂРёС‚Рµ Р±Р»РѕРє В«РЎРІРѕРґРєР° РѕС€РёР±РѕРє Рё СЂРёСЃРєРѕРІВ», РїРѕС‚РѕРј В«РўРѕРї РЅРѕРґВ», Р° СѓР¶Рµ РїРѕСЃР»Рµ СЌС‚РѕРіРѕ СѓС…РѕРґРёС‚Рµ РІ РґРµС‚Р°Р»Рё РїРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРј Рё Р±РѕРЅСѓСЃР°Рј.
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
              <h2 className="font-display text-xl font-bold">Р”РЅРµРІРЅС‹Рµ РјРµС‚СЂРёРєРё</h2>
              <p className="text-xs text-slate-500">РџРѕСЃР»РµРґРЅРёРµ 7 РґРЅРµР№</p>
            </div>
          </div>
          <button
            className="outline-btn inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold"
            type="button"
            onClick={() => void refresh()}
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            РћР±РЅРѕРІРёС‚СЊ
          </button>
        </div>
        {loading ? <p className="text-sm text-slate-500">Р—Р°РіСЂСѓР·РєР°...</p> : null}
        {error ? <p className="text-sm text-rose-500">{error}</p> : null}
        {!loading && !error ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-3 py-2.5">Р”Р°С‚Р°</th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1"><ArrowUp size={12} className="text-emerald-500" /> Р РµРіРёСЃС‚СЂР°С†РёРё</span>
                  </th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1"><ArrowDown size={12} className="text-rose-500" /> РћС‚С‚РѕРє</span>
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
                    <td className="px-3 py-2.5 font-medium">{Math.round(point.revenue_rub || 0)} в‚Ѕ</td>
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
            <h2 className="font-display text-xl font-bold">РўРѕРї РЅРѕРґ</h2>
            <p className="text-xs text-slate-500">Р—РґРѕСЂРѕРІСЊРµ Рё РјРµС‚СЂРёРєРё РїРѕ РЅРѕРґР°Рј</p>
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
                  <span>Р—Р°РґРµСЂР¶РєР°: {node.panel_latency_ms ?? "вЂ”"} ms</span>
                  <span className="font-medium">{node.active_clients} РєР»РёРµРЅС‚РѕРІ</span>
                </div>
              </article>
            );
          })}
          {(summary?.top_nodes || []).length === 0 && !loading ? (
            <div className="empty-state col-span-full">
              <Server size={32} />
              <p className="text-sm">РќРµС‚ РґР°РЅРЅС‹С… Рѕ РЅРѕРґР°С…</p>
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
            <h2 className="font-display text-xl font-bold">РЎРІРѕРґРєР° РѕС€РёР±РѕРє Рё СЂРёСЃРєРѕРІ</h2>
            <p className="text-xs text-slate-500">РўРѕ, С‡С‚Рѕ СЃРµР№С‡Р°СЃ С‚СЂРµР±СѓРµС‚ РІРЅРёРјР°РЅРёСЏ РѕРїРµСЂР°С‚РѕСЂР°</p>
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
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-amber-300">Р§С‚Рѕ РїСЂРѕРІРµСЂРёС‚СЊ СЃРµР№С‡Р°СЃ</p>
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
            РљСЂРёС‚РёС‡РЅС‹С… СЃРёРіРЅР°Р»РѕРІ СЃРµР№С‡Р°СЃ РЅРµС‚: РјРµС‚СЂРёРєРё СЃРІРµР¶РёРµ, callback-РѕС€РёР±РєРё Рё fallback-С…РёС‚С‹ РїРѕРґ РєРѕРЅС‚СЂРѕР»РµРј.
          </div>
        )}
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-violet">
            <Gift size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Р‘РѕРЅСѓСЃС‹ Рё РїСЂРѕРјРѕ Р·Р° 24 С‡Р°СЃР°</h2>
            <p className="text-xs text-slate-500">РџРѕРєР°Р·С‹РІР°РµС‚, СЃРєРѕР»СЊРєРѕ Р±РѕРЅСѓСЃРѕРІ СЂРµР°Р»СЊРЅРѕ СЃСЂР°Р±РѕС‚Р°Р»Рѕ, Р° СЃРєРѕР»СЊРєРѕ РЅРµ РІС‹РґР°Р»РѕСЃСЊ РёР·-Р·Р° СѓСЃР»РѕРІРёР№ РёР»Рё РѕС€РёР±РѕРє.</p>
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
            <h2 className="font-display text-xl font-bold">РЈРґРµСЂР¶Р°РЅРёРµ Рё СЂРµР°РєС‚РёРІР°С†РёСЏ</h2>
            <p className="text-xs text-slate-500">РџРѕРјРѕРіР°РµС‚ РїРѕРЅСЏС‚СЊ, РєРѕРјСѓ РїРѕСЂР° РЅР°РїРѕРјРЅРёС‚СЊ Рѕ РїСЂРѕРґР»РµРЅРёРё Рё РєРѕРіРѕ СѓР¶Рµ СЃС‚РѕРёС‚ РІРѕР·РІСЂР°С‰Р°С‚СЊ РѕР±СЂР°С‚РЅРѕ.</p>
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
            РС‚РѕРіРѕ Р·Р° 7 РґРЅРµР№: <strong>{totals.registrations}</strong> СЂРµРіРёСЃС‚СЂР°С†РёР№, <strong>{totals.churn}</strong> РѕС‚С‚РѕРє, РІС‹СЂСѓС‡РєР° <strong>{Math.round(totals.revenueRub)} в‚Ѕ</strong> Рё
          </p>
        </div>
      </div>
      {summary?.errors.stale_metrics || Number(summary?.errors.unhealthy_nodes || 0) > 0 || summary?.resilience.single_point_risk ? (
        <p className="text-xs text-amber-500">
          РџРµСЂРµРґ СЂРµР»РёР·РѕРј РёР»Рё СЂР°СЃСЃС‹Р»РєРѕР№ РїСЂРѕРІРµСЂСЊС‚Рµ С‚Р°Р№РјРµСЂ РјРµС‚СЂРёРє, СЃРІРµР¶РµСЃС‚СЊ СЃСЂРµР·РѕРІ Рё РЅРѕРґС‹ СЃ РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏРјРё.
        </p>
      ) : null}
    </section>
  );
}

