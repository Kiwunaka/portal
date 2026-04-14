"use client";

import AppRouteLink from "@/components/app-route-link";
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
import { getCopyText, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useState } from "react";

const COMPARISON_ROWS = [
  { metric: "Устройства", start: "1", standard: "До 5", long: "До 5" },
  { metric: "Страны", start: "NL", standard: "IT, NL, PL, US", long: "IT, NL, PL, US" },
  { metric: "Срок", start: "Старт", standard: "1 или 3 месяца", long: "6, 9 или 12 месяцев" },
  {
    metric: "Для кого",
    start: "Быстро проверить сервис",
    standard: "Спокойный рабочий режим",
    long: "Редкие продления и лучшая цена",
  },
] as const;

const RENEWAL_STEPS = [
  "Проверьте текущий статус доступа и лимиты прямо в кабинете.",
  "Выберите продление или подходящий срок без ручной настройки подключения.",
  "Если доступ переносится на новое устройство, откройте приложения POKROV и продолжайте уже там.",
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
  const [plans, setPlans] = useState<PlanCatalogRow[]>(() => fallbackPlans());
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await fetchPublicPlans();
        const rows = (payload.plans || [])
          .filter((plan) => Boolean(plan.is_active))
          .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
        if (!cancelled) {
          setPlans(rows.length ? rows : fallbackPlans());
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
  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const softMode = isSoftModeState(accessState);
  const nextResetAt = getNextResetAt(dash, user);
  const deviceLimit = getDeviceLimit(dash, user);
  const freeLimitGb = getTrafficLimitGb(dash, user);

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">подписка</p>
        <h1 className="mt-2 font-display text-4xl font-bold">
          {getCopyText("webapp.subscription.title", "Доступ и продление")}
        </h1>
        <h2 className="mt-4 font-display text-2xl font-semibold">Подключение ведём через приложения POKROV</h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
          {getCopyText(
            "webapp.subscription.subtitle",
            "Здесь видно текущий режим доступа, варианты продления и спокойный следующий шаг, если меняется устройство или нужна помощь.",
          )}
        </p>
        <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
          Кабинет не показывает и не редактирует личные ссылки подключения. Само подключение продолжается через приложения POKROV, а браузерный путь остаётся местом для статуса, продления и поддержки.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть продление
          </AppRouteLink>
          <AppRouteLink href="/dashboard/downloads/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть мои приложения
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Нужна помощь с устройством
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
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">логика доступа</p>
          <h2 className="mt-2 font-display text-3xl font-bold">
            {paidMode
              ? "Оплаченный доступ уже даёт безлимит и спокойный запас по устройствам"
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
                  : `Free Monthly — это ${freeLimitGb || 5} ГБ в месяц и до ${deviceLimit} устройств.`}
          </p>
        </article>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr,0.95fr]">
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-emerald-500">как продлить без сюрпризов</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Продление остаётся в кабинете, подключение — в приложениях</h2>
          <div className="mt-4 space-y-3">
            {RENEWAL_STEPS.map((step, index) => (
              <div key={step} className="flex items-start gap-3 rounded-2xl border border-white/40 bg-white/55 p-4 dark:border-white/10 dark:bg-white/5">
                <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-900 text-xs font-semibold text-white dark:bg-emerald-700">
                  {index + 1}
                </span>
                <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">{step}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">что важно помнить</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Личный маршрут не выводим на экран кабинета</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Это сделано специально: так пользователь не копирует личный путь в буфер обмена, историю браузера или скриншоты. Если доступ нужно продолжить на новом устройстве, открывайте приложения POKROV и входите в тот же аккаунт.
          </p>
          <div className="mt-4 rounded-2xl border border-white/40 bg-white/55 p-4 text-sm text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
            Если устройство не подтянуло доступ автоматически, лучше открыть службу заботы. Команда подскажет безопасный следующий шаг без ручной раздачи личных ссылок.
          </div>
        </article>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        {plans.map((plan) => (
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
              Продлить на {plan.label}
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
                <th className={`px-4 py-3 ${activeColumn === "start" ? "text-emerald-700 dark:text-emerald-300" : ""}`}>Старт</th>
                <th className={`px-4 py-3 ${activeColumn === "standard" ? "text-emerald-700 dark:text-emerald-300" : ""}`}>1-3 месяца</th>
                <th className={`px-4 py-3 ${activeColumn === "long" ? "text-emerald-700 dark:text-emerald-300" : ""}`}>6-12 месяцев</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.metric} className="border-t border-white/40 dark:border-white/10">
                  <td className="px-4 py-3 font-semibold">{row.metric}</td>
                  <td className={`px-4 py-3 ${activeColumn === "start" ? "font-semibold text-emerald-700 dark:text-emerald-300" : ""}`}>{row.start}</td>
                  <td className={`px-4 py-3 ${activeColumn === "standard" ? "font-semibold text-emerald-700 dark:text-emerald-300" : ""}`}>{row.standard}</td>
                  <td className={`px-4 py-3 ${activeColumn === "long" ? "font-semibold text-emerald-700 dark:text-emerald-300" : ""}`}>{row.long}</td>
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
