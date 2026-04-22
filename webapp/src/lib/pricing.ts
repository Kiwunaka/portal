import {
  getPricingPreviewDiscountPercent,
  getTariffPlan,
  getTariffPlans,
  normalizePlanCode,
  type PlanCode,
} from "./portal";

export type PricingPlan = {
  code: PlanCode;
  label: string;
  price: number;
  days: number;
  deviceLimit: number;
  badge?: string;
  isOneTime?: boolean;
  note: string;
};

function toPricingPlan(rawCode: string): PricingPlan {
  const plan = getTariffPlan(rawCode);
  if (!plan) {
    return {
      code: "1_month",
      label: "1 месяц",
      price: 249,
      days: 30,
      deviceLimit: 5,
      badge: "Базовый",
      note: "Ежемесячный managed premium без длинных обязательств.",
    };
  }

  return {
    code: plan.code as PlanCode,
    label: plan.label,
    price: Number(plan.amount_rub || 0),
    days: Math.max(1, Number(plan.duration_days || 30)),
    deviceLimit: Math.max(1, Number(plan.device_limit || 1)),
    badge: plan.badge || undefined,
    isOneTime: plan.code === "start_99",
    note: plan.marketing_note || plan.cabinet_note || plan.label,
  };
}

export const PRICING_PLANS: PricingPlan[] = getTariffPlans()
  .slice()
  .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
  .map((plan) => toPricingPlan(plan.code));

export function normalizePromo(raw: string): string {
  return raw.trim().toUpperCase();
}

export function promoDiscountPercent(raw: string): number {
  return getPricingPreviewDiscountPercent(normalizePromo(raw));
}

export function getPricingPlan(raw: string | null | undefined): PricingPlan {
  const code = normalizePlanCode(raw, "1_month");
  return PRICING_PLANS.find((plan) => plan.code === code) || toPricingPlan(code);
}

export function computePlanPrice(planCode: string | null | undefined, promo: string) {
  const plan = getPricingPlan(planCode);
  const discountPercent = promoDiscountPercent(promo);
  const discountAmount = Math.round((plan.price * discountPercent) / 100);
  const total = Math.max(0, plan.price - discountAmount);
  return {
    plan,
    base: plan.price,
    discountPercent,
    discountAmount,
    total,
  };
}
