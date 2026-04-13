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
    label: "Старт: Ускорение на 30 дней",
    price: 99,
    days: 30,
    deviceLimit: 1,
    badge: "Пробный",
    isOneTime: true,
    note: "Позволяет лично убедиться в качестве магии ускорения без лишних обязательств.",
  },
  {
    code: "1_month",
    label: "Оптимизатор на 1 месяц",
    price: 249,
    days: 30,
    deviceLimit: 5,
    badge: "Стандарт",
    note: "Удобный ежемесячный вариант для стабильной работы ваших приложений.",
  },
  {
    code: "3_months",
    label: "Квартал: Стабильная сеть",
    price: 699,
    days: 91,
    deviceLimit: 5,
    badge: "Выгоднее",
    note: "Популярный выбор для тех, кто ценит предсказуемость и надежный результат.",
  },
  {
    code: "6_months",
    label: "Полугодие: Полный разгон",
    price: 1199,
    days: 182,
    deviceLimit: 5,
    badge: "Популярный",
    note: "Оптимальный баланс для тех, кто уже сделал быструю сеть частью своего дня.",
  },
  {
    code: "9_months",
    label: "Премиум-доступ: 9 месяцев",
    price: 1399,
    days: 273,
    deviceLimit: 5,
    badge: "Надолго",
    note: "Зафиксируйте идеальную скорость на длительный срок без лишних забот.",
  },
  {
    code: "12_months",
    label: "Годовой абонемент: POKROV Network",
    price: 1644,
    days: 365,
    deviceLimit: 5,
    badge: "-45%",
    note: "Максимальный комфорт и экономия для тех, кому всегда нужен лучший интернет.",
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
