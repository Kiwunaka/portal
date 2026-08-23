import type { PlanCatalogRow } from "@/lib/api";
import { assertCommercialPlanProjection, getCheckoutTariffPlans } from "@/lib/portal";

export const CABINET_PLAN_CODES = [
  "start_99",
  "1_month",
  "3_months",
  "6_months",
  "9_months",
  "12_months",
] as const;

export function getCabinetFallbackPlans(): PlanCatalogRow[] {
  const tariffPlans = getCheckoutTariffPlans();
  assertCommercialPlanProjection(tariffPlans);
  const byCode = new Map<string, PlanCatalogRow>(
    tariffPlans.map((plan) => [
      plan.code,
      {
        code: plan.code,
        label: plan.label,
        amount_rub: Number(plan.amount_rub || 0),
        amount_stars: Number(plan.amount_stars || 0),
        days: Number(plan.duration_days || 0),
        device_limit: Number(plan.device_limit || 0),
        node_policy: plan.node_policy,
        badge: plan.badge || null,
        is_active: Boolean(plan.is_active),
        sort_order: Number(plan.sort_order || 0),
      } satisfies PlanCatalogRow,
    ]),
  );

  return CABINET_PLAN_CODES.map((code) => byCode.get(code)).filter((plan): plan is PlanCatalogRow => Boolean(plan));
}

export function resolveCabinetPlans(apiPlans: PlanCatalogRow[] | null | undefined): PlanCatalogRow[] {
  const fallback = getCabinetFallbackPlans();
  const apiByCode = new Map(
    (apiPlans || [])
      .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
      .map((plan) => [plan.code, plan]),
  );

  if (!CABINET_PLAN_CODES.every((code) => apiByCode.has(code))) return fallback;
  return CABINET_PLAN_CODES.map((code) => apiByCode.get(code) as PlanCatalogRow);
}
