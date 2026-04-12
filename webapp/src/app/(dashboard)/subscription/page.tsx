"use client";

import AppRouteLink from "@/components/app-route-link";
import SubscriptionQrCard from "@/components/subscription-qr-card";
import {
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  getTrafficLimitGb,
  isFreeMonthlyState,
  isPaidUnlimitedState,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { fetchPublicPlans, type PlanCatalogRow } from "@/lib/api";
import { getCopyText, getPortalPublicConfig, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

const COMPARISON_ROWS = [
  { metric: "Устройства", start: "1", standard: "До 5", long: "До 5" },
  { metric: "Страны", start: "NL", standard: "IT, NL, PL, US", long: "IT, NL, PL, US" },
  { metric: "Срок", start: "Старт", standard: "1 или 3 месяца", long: "6, 9 или 12 месяцев" },
  {
    metric: "Для кого",
    start: "Быстро проверить сервис",
    standard: "Обычный рабочий режим",
    long: "Редкие продления и лучшая цена",
  },
] as const;

function planColumn(planCode: string | null | undefined): "start" | "standard" | "long" {
  const code = normalizePlanCode(planCode || "");
  if (code === "start_99") return "start";
  if (code === "1_month" || code === "3_months") return "standard";
  return "long";
}

function fallbackPlans(): PlanCatalogRow[] {
  return [
    {
      code: "start_99",
      label: "Приветственный 30 дней",
      amount_rub: 99,
      amount_stars: 99,
      days: 30,
      device_limit: 1,
      node_policy: "nl_only",
      badge: "Один раз",
      is_active: true,
      sort_order: 1,
    },
    {
      code: "1_month",
      label: "1 месяц",
      amount_rub: 249,
      amount_stars: 249,
      days: 30,
      device_limit: 5,
      node_policy: "paid_pool",
      badge: "Базовый",
      is_active: true,
      sort_order: 2,
    },
    {
      code: "12_months",
      label: "12 месяцев",
      amount_rub: 1644,
      amount_stars: 1644,
      days: 365,
      device_limit: 5,
      node_policy: "paid_pool",
      badge: "-45%",
      is_active: true,
      sort_order: 3,
    },
  ];
}

function nodePolicyLabel(value: string | null | undefined): string {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "nl_only") return "NL";
  if (normalized === "paid_pool") return "IT, NL, PL, US";
  return "Актуальный пул";
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ru-RU");
}

export default function SubscriptionPage() {
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
  const [error, setError] = useState("");
  const [copyState, setCopyState] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await fetchPublicPlans();
        const rows = (payload.plans || [])
          .filter((plan) => Boolean(plan.is_active))
          .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
        if (!cancelled) {
          setPlans(rows);
          setError("");
        }
      } catch (nextError) {
        if (!cancelled) {
          setPlans(fallbackPlans());
          setError(String((nextError as { message?: string })?.message || nextError || ""));
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeColumn = planColumn(dash?.current_plan_code || dash?.sub_type || "");
  const planCards = useMemo(() => (plans.length ? plans : fallbackPlans()), [plans]);
  const connectionLink = String(dash?.subscription_url || user?.subscription_url || "").trim();
  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const softMode = isSoftModeState(accessState);
  const nextResetAt = getNextResetAt(dash, user);
  const deviceLimit = getDeviceLimit(dash, user);
  const freeLimitGb = getTrafficLimitGb(dash, user);

  const copyLink = async () => {
    if (!connectionLink) return;
    try {
      await navigator.clipboard.writeText(connectionLink);
      setCopyState(true);
      window.setTimeout(() => setCopyState(false), 1800);
    } catch {
      setCopyState(false);
    }
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">подписка</p>
        <h1 className="mt-2 font-display text-4xl font-bold">
          {getCopyText("webapp.subscription.title", "Подписка и подключение")}
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {getCopyText(
            "webapp.subscription.subtitle",
            "Здесь видно текущий режим доступа, ссылка подключения и варианты продления.",
          )}
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть продление
          </AppRouteLink>
          <AppRouteLink href={config.botUrl} target="_blank" hardNavigate={false} className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Продолжить в Telegram
          </AppRouteLink>
        </div>
        <p className="mt-4 text-xs text-slate-500">Пользователь: {user?.username ? `@${user.username}` : `ID ${user?.tg_id || "—"}`}</p>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-emerald-500">что доступно сейчас</p>
          <h2 className="mt-2 font-display text-3xl font-bold">{resolvePlanLabel(dash, user)}</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <p>Трафик: {resolveTrafficStatusText(dash, user)}</p>
            <p>Устройства: до {deviceLimit}</p>
            <p>Срок доступа: {formatDate(dash?.expiry_at)}</p>
            {freeMode && nextResetAt ? <p>Следующий сброс: {formatDate(nextResetAt)}</p> : null}
          </div>
        </article>
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">логика тарифов</p>
          <h2 className="mt-2 font-display text-3xl font-bold">
            {paidMode
              ? "Paid уже даёт безлимит и до 5 устройств"
              : trialMode
                ? "После премиум-периода включится Free Monthly"
                : softMode
                  ? "Сейчас профиль в мягком режиме"
                  : "Free Monthly остаётся режимом с квотой"}
          </h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            {paidMode
              ? "На paid не показываем остаток в гигабайтах: это безлимитный доступ."
              : trialMode
                ? "Премиум-период нужен для старта. После него профиль автоматически переходит в бесплатный режим 5 ГБ в месяц."
                : softMode
                  ? "Мягкий режим включается после исчерпания месячной квоты и снимается следующим сбросом."
                  : `Free Monthly — это ${freeLimitGb || 5} ГБ в месяц и до ${deviceLimit} устройства.`}
          </p>
        </article>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-emerald-500">ссылка подключения</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Одна ссылка для всех подключений</h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            Используйте её в приложении или импортируйте в совместимый клиент через {` `}
            {config.connectUrl.replace(/^https?:\/\//, "")}.
          </p>
          <div className="mt-4 rounded-2xl border border-white/40 bg-white/50 p-4 text-xs text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
            {connectionLink || "Ссылка появится после активации доступа."}
          </div>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void copyLink()}
              className="btn-primary rounded-xl px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.12em]"
              disabled={!connectionLink}
            >
              {copyState ? "Скопировано" : "Скопировать"}
            </button>
          </div>
        </article>

        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">qr для подключения</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Откройте на втором устройстве</h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            Отсканируйте QR-код, чтобы быстро передать ссылку на телефон, планшет или другой компьютер.
          </p>
          <div className="mt-4 flex flex-col items-start gap-3">
            <SubscriptionQrCard value={connectionLink} />
          </div>
        </article>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        {planCards.map((plan) => (
          <article key={plan.code} className="glass-card p-6">
            <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">{plan.badge || "План"}</p>
            <h2 className="mt-2 font-display text-3xl font-bold">{plan.label}</h2>
            <p className="mt-3 text-2xl font-semibold">{Number(plan.amount_rub || 0)} ₽</p>
            <p className="mt-1 text-xs text-slate-500">
              {plan.days} дней • до {plan.device_limit} устройств • {nodePolicyLabel(plan.node_policy)}
            </p>
            <AppRouteLink
              href={`/subscription/checkout/?plan=${encodeURIComponent(plan.code)}`}
              className="btn-primary mt-5 inline-flex rounded-xl px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.12em]"
            >
              Выбрать
            </AppRouteLink>
          </article>
        ))}
      </section>

      <section className="glass-card p-7">
        <div className="mb-4">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">сравнение</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Что меняется по срокам</h2>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/45 dark:border-white/10">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="bg-white/55 dark:bg-white/5">
              <tr>
                <th className="px-4 py-3">Параметр</th>
                <th className={`px-4 py-3 ${activeColumn === "start" ? "text-emerald-700 dark:text-amber-200" : ""}`}>Старт</th>
                <th className={`px-4 py-3 ${activeColumn === "standard" ? "text-emerald-700 dark:text-amber-200" : ""}`}>1-3 месяца</th>
                <th className={`px-4 py-3 ${activeColumn === "long" ? "text-emerald-700 dark:text-amber-200" : ""}`}>6-12 месяцев</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.metric} className="border-t border-white/40 dark:border-white/10">
                  <td className="px-4 py-3 font-semibold">{row.metric}</td>
                  <td className={`px-4 py-3 ${activeColumn === "start" ? "font-semibold text-emerald-700 dark:text-amber-200" : ""}`}>{row.start}</td>
                  <td className={`px-4 py-3 ${activeColumn === "standard" ? "font-semibold text-emerald-700 dark:text-amber-200" : ""}`}>{row.standard}</td>
                  <td className={`px-4 py-3 ${activeColumn === "long" ? "font-semibold text-emerald-700 dark:text-amber-200" : ""}`}>{row.long}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {error ? <p className="mt-3 text-xs text-amber-600 dark:text-amber-300">Не все данные загрузились автоматически: {error}</p> : null}
      </section>
    </main>
  );
}
