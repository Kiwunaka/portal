import { normalizePlanCode, type PlanCode } from "./portal";

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

export const PRICING_PLANS: PricingPlan[] = [
  {
    code: "start_99",
    label: "Приветственный 30 дней",
    price: 99,
    days: 30,
    deviceLimit: 1,
    badge: "Один раз",
    isOneTime: true,
    note: "Чтобы спокойно проверить сервис без лишних обязательств.",
  },
  {
    code: "1_month",
    label: "1 месяц",
    price: 249,
    days: 30,
    deviceLimit: 5,
    badge: "Базовый",
    note: "Короткий понятный срок для обычного ежемесячного использования.",
  },
  {
    code: "3_months",
    label: "3 месяца",
    price: 699,
    days: 91,
    deviceLimit: 5,
    badge: "Выгоднее",
    note: "Удобный вариант, если не хочется возвращаться к оплате каждый месяц.",
  },
  {
    code: "6_months",
    label: "6 месяцев",
    price: 1199,
    days: 182,
    deviceLimit: 5,
    badge: "Популярный",
    note: "Хороший баланс между общей суммой и экономией на длительном сроке.",
  },
  {
    code: "9_months",
    label: "9 месяцев",
    price: 1399,
    days: 273,
    deviceLimit: 5,
    badge: "Надолго",
    note: "Для тех, кто хочет реже продлевать и зафиксировать доступ заранее.",
  },
  {
    code: "12_months",
    label: "12 месяцев",
    price: 1644,
    days: 365,
    deviceLimit: 5,
    badge: "-45%",
    note: "Максимальный срок с крупной скидкой, но без слишком агрессивного дисконта.",
  },
];

const PROMO_RULES: Record<string, number> = {
  POKROV10: 10,
  PORTAL10: 10,
  WELCOME15: 15,
  STARTBOOST: 15,
};

export function normalizePromo(raw: string): string {
  return raw.trim().toUpperCase();
}

export function promoDiscountPercent(raw: string): number {
  return PROMO_RULES[normalizePromo(raw)] || 0;
}

export function getPricingPlan(raw: string | null | undefined): PricingPlan {
  const code = normalizePlanCode(raw, "1_month");
  return PRICING_PLANS.find((plan) => plan.code === code) || PRICING_PLANS[1];
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
