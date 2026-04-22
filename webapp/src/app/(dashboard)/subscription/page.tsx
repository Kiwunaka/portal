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
import { getCopyText, getTariffPlans, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useState } from "react";

const COMPARISON_ROWS = [
  { metric: "\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430", start: "1", standard: "\u0414\u043e 5", long: "\u0414\u043e 5" },
  {
    metric: "\u041b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u043e\u043a\u0430\u0446\u0438\u044f",
    start: "\u041e\u0434\u043d\u0430 \u043b\u043e\u043a\u0430\u0446\u0438\u044f POKROV",
    standard: "\u041e\u0434\u043d\u0430 \u043b\u043e\u043a\u0430\u0446\u0438\u044f POKROV",
    long: "\u041e\u0434\u043d\u0430 \u043b\u043e\u043a\u0430\u0446\u0438\u044f POKROV",
  },
  { metric: "\u0421\u0440\u043e\u043a", start: "\u0421\u0442\u0430\u0440\u0442", standard: "1-3 \u043c\u0435\u0441\u044f\u0446\u0430", long: "6-12 \u043c\u0435\u0441\u044f\u0446\u0435\u0432" },
  {
    metric: "\u041f\u0443\u0431\u043b\u0438\u0447\u043d\u044b\u0439 \u043c\u0430\u0440\u0448\u0440\u0443\u0442",
    start: "All except RU",
    standard: "All except RU",
    long: "All except RU",
  },
] as const;

const RENEWAL_STEPS = [
  "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0442\u0435\u043a\u0443\u0449\u0438\u0439 \u0440\u0435\u0436\u0438\u043c \u0434\u043e\u0441\u0442\u0443\u043f\u0430 \u0438 \u043b\u0438\u043c\u0438\u0442\u044b \u043f\u0440\u044f\u043c\u043e \u0432 \u043a\u0430\u0431\u0438\u043d\u0435\u0442\u0435.",
  "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u043f\u0440\u043e\u0434\u043b\u0435\u043d\u0438\u0435 \u0438\u043b\u0438 \u043f\u043e\u0434\u0445\u043e\u0434\u044f\u0449\u0438\u0439 \u0441\u0440\u043e\u043a \u0431\u0435\u0437 \u043f\u043e\u043a\u0430\u0437\u0430 raw-\u0441\u0441\u044b\u043b\u043e\u043a.",
  "\u0415\u0441\u043b\u0438 \u043c\u0435\u043d\u044f\u0435\u0442\u0441\u044f \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e, \u043f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0439\u0442\u0435 \u0432\u0445\u043e\u0434 \u0432 \u0442\u043e\u0442 \u0436\u0435 app-first \u0430\u043a\u043a\u0430\u0443\u043d\u0442 \u0438 \u043f\u0440\u0438 \u043d\u0443\u0436\u0434\u0435 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 redeem \u043a\u043b\u044e\u0447.",
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
      label: "\u0421\u0442\u0430\u0440\u0442 30 \u0434\u043d\u0435\u0439",
      amount_rub: 99,
      amount_stars: 99,
      days: 30,
      device_limit: 1,
      node_policy: "managed_premium",
      badge: "\u0421\u0442\u0430\u0440\u0442",
      is_active: true,
      sort_order: 1,
    },
    {
      code: "1_month",
      label: "1 \u043c\u0435\u0441\u044f\u0446",
      amount_rub: 249,
      amount_stars: 249,
      days: 30,
      device_limit: 5,
      node_policy: "managed_premium",
      badge: "\u0411\u0430\u0437\u043e\u0432\u044b\u0439",
      is_active: true,
      sort_order: 2,
    },
    {
      code: "12_months",
      label: "12 \u043c\u0435\u0441\u044f\u0446\u0435\u0432",
      amount_rub: 1644,
      amount_stars: 1644,
      days: 365,
      device_limit: 5,
      node_policy: "managed_premium",
      badge: "-45%",
      is_active: true,
      sort_order: 3,
    },
  ];
}

function sharedFallbackPlans(): PlanCatalogRow[] {
  const rows = getTariffPlans()
    .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
    .map((plan) => ({
      code: plan.code,
      label: plan.label,
      amount_rub: Number(plan.amount_rub || 0),
      amount_stars: Number(plan.amount_stars || 0),
      days: Number(plan.duration_days || 0),
      device_limit: Number(plan.device_limit || 0),
      node_policy: plan.node_policy,
      badge: plan.badge || "",
      is_active: Boolean(plan.is_active),
      sort_order: Number(plan.sort_order || 0),
    }))
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
  return rows.length ? rows : fallbackPlans();
}

function nodePolicyLabel(value: string | null | undefined): string {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "free_single_location" || normalized === "nl_only") return "NL-free";
  if (normalized === "managed_premium" || normalized === "paid_pool") {
    return "\u041e\u0434\u043d\u0430 \u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043b\u043e\u043a\u0430\u0446\u0438\u044f POKROV";
  }
  return "\u0423\u043f\u0440\u0430\u0432\u043b\u044f\u0435\u0442\u0441\u044f \u043f\u0440\u043e\u0444\u0438\u043b\u0435\u043c";
}

function formatDate(value?: string | null): string {
  if (!value) return "\u2014";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ru-RU");
}

export default function SubscriptionPage() {
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<PlanCatalogRow[]>(() => sharedFallbackPlans());
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
          setPlans(rows.length ? rows : sharedFallbackPlans());
          setError("");
        }
      } catch (nextError) {
        if (!cancelled) {
          setPlans(sharedFallbackPlans());
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
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">\u0434\u043e\u0441\u0442\u0443\u043f</p>
        <h1 className="mt-2 font-display text-4xl font-bold">
          {getCopyText("webapp.subscription.title", "\u0414\u043e\u0441\u0442\u0443\u043f \u0438 \u043f\u0440\u043e\u0434\u043b\u0435\u043d\u0438\u0435")}
        </h1>
        <h2 className="mt-4 font-display text-2xl font-semibold">
          {"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 \u0432\u0435\u0434\u0451\u043c \u0447\u0435\u0440\u0435\u0437 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f POKROV"}
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
          {getCopyText(
            "webapp.subscription.subtitle",
            "\u0417\u0434\u0435\u0441\u044c \u0432\u0438\u0434\u043d\u043e \u0442\u0435\u043a\u0443\u0449\u0438\u0439 \u0440\u0435\u0436\u0438\u043c \u0434\u043e\u0441\u0442\u0443\u043f\u0430, \u043f\u0440\u043e\u0434\u043b\u0435\u043d\u0438\u0435, redeem \u043a\u043b\u044e\u0447\u0430 \u0438 \u0441\u043f\u043e\u043a\u043e\u0439\u043d\u044b\u0439 support path \u0431\u0435\u0437 raw subscription link \u0432 default UX.",
          )}
        </p>
        <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
          {
            "\u041f\u0443\u0431\u043b\u0438\u0447\u043d\u043e \u043c\u044b \u0434\u0435\u0440\u0436\u0438\u043c \u043e\u0434\u043d\u0443 \u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u0443\u044e \u043b\u043e\u043a\u0430\u0446\u0438\u044e. \u0422\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u043d\u044b\u0435 \u0432\u0430\u0440\u0438\u0430\u043d\u0442\u044b \u0438 \u0434\u0438\u0430\u0433\u043d\u043e\u0441\u0442\u0438\u043a\u0430 \u043e\u0441\u0442\u0430\u044e\u0442\u0441\u044f \u0432 \u0443\u043f\u0440\u0430\u0432\u043b\u044f\u0435\u043c\u043e\u043c \u043f\u0440\u043e\u0444\u0438\u043b\u0435, \u0430 \u043d\u0435 \u0432 \u043c\u0430\u0441\u0441\u043e\u0432\u043e\u043c UI."
          }
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <AppRouteLink href="/dashboard/downloads/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            {"\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043c\u043e\u0438 \u043f\u0440\u0438\u043b\u043e\u0436\u0435\u043d\u0438\u044f"}
          </AppRouteLink>
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            {"\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043f\u0440\u043e\u0434\u043b\u0435\u043d\u0438\u0435"}
          </AppRouteLink>
          <AppRouteLink href="/redeem/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            {"Redeem key"}
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            {"\u041d\u0443\u0436\u043d\u0430 \u043f\u043e\u043c\u043e\u0449\u044c \u0441 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e\u043c"}
          </AppRouteLink>
        </div>
        <p className="mt-4 text-xs text-slate-500">
          {"\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c: "}
          {user?.username ? `@${user.username}` : `ID ${user?.tg_id || "\u2014"}`}
        </p>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-emerald-500">
            {"\u0447\u0442\u043e \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u0441\u0435\u0439\u0447\u0430\u0441"}
          </p>
          <h2 className="mt-2 font-display text-3xl font-bold">{resolvePlanLabel(dash, user)}</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <p>{"\u0422\u0440\u0430\u0444\u0438\u043a: "}{resolveTrafficStatusText(dash, user)}</p>
            <p>{"\u0423\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u0430: \u0434\u043e "}{deviceLimit}</p>
            <p>{"\u0421\u0440\u043e\u043a \u0434\u043e\u0441\u0442\u0443\u043f\u0430: "}{formatDate(dash?.expiry_at)}</p>
            {freeMode && nextResetAt ? <p>{"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u0441\u0431\u0440\u043e\u0441: "}{formatDate(nextResetAt)}</p> : null}
          </div>
        </article>
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">
            {"\u043b\u043e\u0433\u0438\u043a\u0430 \u0434\u043e\u0441\u0442\u0443\u043f\u0430"}
          </p>
          <h2 className="mt-2 font-display text-3xl font-bold">
            {paidMode
              ? "\u041e\u043f\u043b\u0430\u0447\u0435\u043d\u043d\u044b\u0439 \u0434\u043e\u0441\u0442\u0443\u043f \u0443\u0436\u0435 \u0438\u0434\u0451\u0442 \u043a\u0430\u043a managed premium"
              : trialMode
                ? "\u041f\u043e\u0441\u043b\u0435 trial \u043f\u0440\u043e\u0444\u0438\u043b\u044c \u043f\u0435\u0440\u0435\u0439\u0434\u0451\u0442 \u0432 Free Monthly"
                : softMode
                  ? "\u0421\u0435\u0439\u0447\u0430\u0441 \u043f\u0440\u043e\u0444\u0438\u043b\u044c \u0432 \u043c\u044f\u0433\u043a\u043e\u043c \u0440\u0435\u0436\u0438\u043c\u0435"
                  : "Free Monthly \u043e\u0441\u0442\u0430\u0451\u0442\u0441\u044f \u0431\u0435\u0441\u043f\u043b\u0430\u0442\u043d\u043e\u0439 \u0442\u043e\u0447\u043a\u043e\u0439 \u0432\u0445\u043e\u0434\u0430"}
          </h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            {paidMode
              ? "\u041f\u043e\u043a\u0443\u043f\u043a\u0430 \u0442\u0435\u043f\u0435\u0440\u044c \u0441\u0432\u044f\u0437\u0430\u043d\u0430 \u0441 key-first commerce: buy key, redeem key, managed premium."
              : trialMode
                ? "\u041f\u0435\u0440\u0432\u043e\u0435 \u0432\u0430\u043b\u0438\u0434\u043d\u043e\u0435 \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432\u043e \u043f\u043e\u043b\u0443\u0447\u0430\u0435\u0442 5-\u0434\u043d\u0435\u0432\u043d\u044b\u0439 premium trial, \u0430 \u043f\u043e\u0442\u043e\u043c \u043f\u0430\u0434\u0430\u0435\u0442 \u0432 free tier."
                : softMode
                  ? "\u041c\u044f\u0433\u043a\u0438\u0439 \u0440\u0435\u0436\u0438\u043c \u0432\u043a\u043b\u044e\u0447\u0430\u0435\u0442\u0441\u044f \u043f\u043e\u0441\u043b\u0435 \u0438\u0441\u0447\u0435\u0440\u043f\u0430\u043d\u0438\u044f \u043c\u0435\u0441\u044f\u0447\u043d\u043e\u0439 \u043a\u0432\u043e\u0442\u044b \u0438 \u0441\u043d\u0438\u043c\u0430\u0435\u0442\u0441\u044f \u043d\u0430 \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u043c reset."
                  : `Free Monthly - ${freeLimitGb || 5} GB / 30 days, 1 device, NL-free.`}
          </p>
        </article>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr,0.95fr]">
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-emerald-500">
            {"\u043a\u0430\u043a \u043f\u0440\u043e\u0434\u043b\u0438\u0442\u044c \u0431\u0435\u0437 \u0441\u044e\u0440\u043f\u0440\u0438\u0437\u043e\u0432"}
          </p>
          <h2 className="mt-2 font-display text-3xl font-bold">
            {"\u041a\u0430\u0431\u0438\u043d\u0435\u0442 \u0432\u0435\u0434\u0451\u0442 \u0432 checkout \u0438 redeem, \u0430 \u043d\u0435 \u0432 \u0440\u0443\u0447\u043d\u0443\u044e \u0440\u0430\u0437\u0434\u0430\u0447\u0443 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432"}
          </h2>
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
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">
            {"\u0447\u0442\u043e \u0432\u0430\u0436\u043d\u043e \u043f\u043e\u043c\u043d\u0438\u0442\u044c"}
          </p>
          <h2 className="mt-2 font-display text-3xl font-bold">
            {"\u041f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e \u043c\u044b \u043d\u0435 \u043f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0435\u043c raw subscription link"}
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            {
              "\u042d\u0442\u043e \u0441\u043e\u0437\u043d\u0430\u0442\u0435\u043b\u044c\u043d\u043e: default UX \u0434\u0435\u0440\u0436\u0438\u0442 key-first commerce, managed profile \u0438 support/recovery path. \u0420\u0443\u0447\u043d\u0430\u044f \u0441\u0441\u044b\u043b\u043a\u0430 \u043e\u0441\u0442\u0430\u0451\u0442\u0441\u044f \u0442\u043e\u043b\u044c\u043a\u043e \u0434\u043b\u044f recovery \u0438 manual request."
            }
          </p>
          <div className="mt-4 rounded-2xl border border-white/40 bg-white/55 p-4 text-sm text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
            {
              "\u0415\u0441\u043b\u0438 premium \u043d\u0435 \u043f\u043e\u0434\u0442\u044f\u043d\u0443\u043b\u0441\u044f \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438, \u043e\u0442\u043a\u0440\u043e\u0439\u0442\u0435 support \u0438\u043b\u0438 Telegram continuation. \u0421\u0435\u0441\u0441\u0438\u044f, linked identities \u0438 access state \u0443\u0436\u0435 \u0432\u044b\u0440\u043e\u0432\u043d\u0435\u043d\u044b \u0432 \u0435\u0434\u0438\u043d\u044b\u0439 contract."
            }
          </div>
        </article>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        {plans.map((plan) => (
          <article key={plan.code} className="glass-card p-6">
            <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">{plan.badge || "\u041f\u043b\u0430\u043d"}</p>
            <h2 className="mt-2 font-display text-3xl font-bold">{plan.label}</h2>
            <p className="mt-3 text-2xl font-semibold">{Number(plan.amount_rub || 0)} &#8381;</p>
            <p className="mt-1 text-xs text-slate-500">
              {plan.days} {"\u0434\u043d\u0435\u0439 \u2022 \u0434\u043e "} {plan.device_limit} {" \u0443\u0441\u0442\u0440\u043e\u0439\u0441\u0442\u0432 \u2022 "} {nodePolicyLabel(plan.node_policy)}
            </p>
            <AppRouteLink
              href={`/subscription/checkout/?plan=${encodeURIComponent(plan.code)}`}
              className="btn-primary mt-5 inline-flex rounded-xl px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.12em]"
            >
              {"\u041f\u0440\u043e\u0434\u043b\u0438\u0442\u044c \u043d\u0430 "} {plan.label}
            </AppRouteLink>
          </article>
        ))}
      </section>

      <section className="glass-card p-7">
        <div className="mb-4">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">
            {"\u0441\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435"}
          </p>
          <h2 className="mt-2 font-display text-3xl font-bold">
            {"\u0427\u0442\u043e \u043c\u0435\u043d\u044f\u0435\u0442\u0441\u044f \u043f\u043e \u0441\u0440\u043e\u043a\u0430\u043c"}
          </h2>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/45 dark:border-white/10">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="bg-white/55 dark:bg-white/5">
              <tr>
                <th className="px-4 py-3">{"\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440"}</th>
                <th className={`px-4 py-3 ${activeColumn === "start" ? "text-emerald-700 dark:text-emerald-300" : ""}`}>
                  {"\u0421\u0442\u0430\u0440\u0442"}
                </th>
                <th className={`px-4 py-3 ${activeColumn === "standard" ? "text-emerald-700 dark:text-emerald-300" : ""}`}>
                  {"1-3 \u043c\u0435\u0441\u044f\u0446\u0430"}
                </th>
                <th className={`px-4 py-3 ${activeColumn === "long" ? "text-emerald-700 dark:text-emerald-300" : ""}`}>
                  {"6-12 \u043c\u0435\u0441\u044f\u0446\u0435\u0432"}
                </th>
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

        {error ? (
          <p className="mt-3 text-xs text-amber-600 dark:text-amber-300">
            {"\u041d\u0435 \u0432\u0441\u0435 \u0434\u0430\u043d\u043d\u044b\u0435 \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u043b\u0438\u0441\u044c \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438: "}
            {error}
          </p>
        ) : null}
      </section>
    </main>
  );
}
