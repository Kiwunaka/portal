import tariffCatalogJson from "./tariff-catalog.json";

export type TariffCatalog = typeof tariffCatalogJson;
export type TariffPlan = TariffCatalog["plans"][number];

export const tariffCatalog: TariffCatalog = tariffCatalogJson;

export function getTariffCatalog(): TariffCatalog {
  return tariffCatalog;
}

export function getTariffPlans(options?: { onlyActive?: boolean }): TariffPlan[] {
  const onlyActive = options?.onlyActive !== false;
  return tariffCatalog.plans.filter((plan) => (!onlyActive || plan.is_active) && plan.public_visibility !== "hidden");
}

export function isCheckoutTariffPlan(plan: TariffPlan | null | undefined): boolean {
  return Boolean(plan?.is_active) && plan?.public_visibility !== "hidden" && Number(plan?.amount_rub || 0) > 0;
}

export function getCheckoutTariffPlans(): TariffPlan[] {
  return getTariffPlans()
    .filter((plan) => isCheckoutTariffPlan(plan))
    .slice()
    .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0));
}

export function getTariffPlan(code: string | null | undefined): TariffPlan | null {
  const target = String(code || "").trim().toLowerCase();
  if (!target) return null;
  return tariffCatalog.plans.find((plan) => plan.code === target) || null;
}

export function normalizeTariffPlanCode(code: string | null | undefined, fallback = "1_month"): string {
  const target = String(code || "").trim().toLowerCase();
  if (!target) return fallback;
  if (tariffCatalog.plans.some((plan) => plan.code === target)) return target;
  const aliased = tariffCatalog.plan_aliases[target as keyof typeof tariffCatalog.plan_aliases];
  return aliased || fallback;
}

export function getPricingPreviewDiscountPercent(raw: string | null | undefined): number {
  const normalized = String(raw || "").trim().toUpperCase();
  if (!normalized) return 0;
  return Number(tariffCatalog.pricing_preview.discount_codes[normalized as keyof typeof tariffCatalog.pricing_preview.discount_codes] || 0);
}

export function tariffPlanAllowsDiscount(code: string | null | undefined): boolean {
  return normalizeTariffPlanCode(code, "") !== "start_99";
}
