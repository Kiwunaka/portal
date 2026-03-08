"use client";

import AppRouteLink from "@/components/app-route-link";
import { fetchPublicPlans, type PlanCatalogRow } from "@/lib/api";
import { getCopyText, getPortalPublicConfig, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

const COMPARISON_ROWS = [
  { metric: "Устройства", start: "1", standard: "До 5", long: "До 5" },
  { metric: "Страны", start: "NL", standard: "IT, NL, PL, US", long: "IT, NL, PL, US" },
  { metric: "Срок", start: "30 дней", standard: "1 или 3 месяца", long: "6, 9 или 12 месяцев" },
  { metric: "Для кого", start: "Спокойная проверка сервиса", standard: "Обычное ежемесячное использование", long: "Редкие продления и лучший срок" },
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

export default function SubscriptionPage() {
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
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

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">subscription</p>
        <h1 className="mt-2 font-display text-4xl font-bold">
          {getCopyText("webapp.subscription.title", "Управление доступом")}
        </h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {getCopyText(
            "webapp.subscription.subtitle",
            "Сравните планы, проверьте лимиты и продлите доступ без лишних шагов.",
          )}
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            {getCopyText("webapp.dashboard.primary_cta", "Открыть оплату")}
          </AppRouteLink>
          <AppRouteLink href={config.botUrl} target="_blank" hardNavigate={false} className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Продолжить в Telegram
          </AppRouteLink>
        </div>
        <p className="mt-4 text-xs text-slate-500">
          Пользователь: {user?.username ? `@${user.username}` : `ID ${user?.tg_id || "—"}`}
        </p>
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
          <h2 className="mt-2 font-display text-3xl font-bold">Что видно сейчас</h2>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/45 dark:border-white/10">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="bg-white/55 dark:bg-white/5">
              <tr>
                <th className="px-4 py-3">Параметр</th>
                <th className={`px-4 py-3 ${activeColumn === "start" ? "text-violet-600 dark:text-violet-300" : ""}`}>Приветственный</th>
                <th className={`px-4 py-3 ${activeColumn === "standard" ? "text-violet-600 dark:text-violet-300" : ""}`}>1–3 месяца</th>
                <th className={`px-4 py-3 ${activeColumn === "long" ? "text-violet-600 dark:text-violet-300" : ""}`}>6–12 месяцев</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.metric} className="border-t border-white/40 dark:border-white/10">
                  <td className="px-4 py-3 font-semibold">{row.metric}</td>
                  <td className={`px-4 py-3 ${activeColumn === "start" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.start}</td>
                  <td className={`px-4 py-3 ${activeColumn === "standard" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.standard}</td>
                  <td className={`px-4 py-3 ${activeColumn === "long" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.long}</td>
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
