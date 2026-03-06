import { PLAN_ALIAS_TO_CODE, type PlanAlias, type PlanCode } from "./portal";

export type BillingPeriod = "monthly" | "annual";

export type PlanConfig = {
  alias: PlanAlias;
  defaultCode: PlanCode;
  name: string;
  subtitle: string;
  shortPrice: number;
  longPrice: number;
  shortLabel: string;
  longLabel: string;
  devices: string;
  promise: string;
  objection: string;
  perks: string[];
};

export const PLAN_CONFIG: PlanConfig[] = [
  {
    alias: "start",
    defaultCode: PLAN_ALIAS_TO_CODE.start,
    name: "Start",
    subtitle: "Спокойный вход без лишних затрат",
    shortPrice: 99,
    longPrice: 99,
    shortLabel: "30 дней",
    longLabel: "30 дней",
    devices: "1 устройство",
    promise: "Подходит, чтобы спокойно проверить сервис в реальном ежедневном сценарии.",
    objection: "Если позже понадобится больше устройств и стран, можно перейти на Pro.",
    perks: ["30 дней доступа", "1 устройство", "Базовый набор стран"]
  },
  {
    alias: "pro",
    defaultCode: PLAN_ALIAS_TO_CODE.pro,
    name: "Pro",
    subtitle: "Оптимальный ритм на каждый день",
    shortPrice: 249,
    longPrice: 699,
    shortLabel: "1 месяц",
    longLabel: "3 месяца",
    devices: "До 5 устройств",
    promise: "Хороший баланс по сроку, цене и количеству устройств для повседневного использования.",
    objection: "Если не хотите часто возвращаться к продлению, удобнее взять Ultra на долгий срок.",
    perks: ["1 или 3 месяца", "До 5 устройств", "Полный набор стран"]
  },
  {
    alias: "ultra",
    defaultCode: PLAN_ALIAS_TO_CODE.ultra,
    name: "Ultra",
    subtitle: "Длинный горизонт и меньше рутины",
    shortPrice: 1199,
    longPrice: 1499,
    shortLabel: "6 месяцев",
    longLabel: "12 месяцев",
    devices: "До 5 устройств",
    promise: "Самая спокойная модель для тех, кто не хочет постоянно возвращаться к оплате.",
    objection: "В линейке есть 6, 9 и 12 месяцев, так что можно выбрать удобный запас по сроку.",
    perks: ["6, 9 или 12 месяцев", "До 5 устройств", "Приоритетная поддержка"]
  }
];

const PROMO_RULES: Record<string, number> = {
  PORTAL10: 10,
  WELCOME15: 15,
  STARTBOOST: 15
};

export function normalizePromo(raw: string): string {
  return raw.trim().toUpperCase();
}

export function promoDiscountPercent(raw: string): number {
  return PROMO_RULES[normalizePromo(raw)] || 0;
}

export function parsePlanAlias(raw: string | null | undefined): PlanAlias {
  if (raw === "start" || raw === "pro" || raw === "ultra") return raw;
  return "pro";
}

export function parseBillingPeriod(raw: string | null | undefined): BillingPeriod {
  if (raw === "annual" || raw === "monthly") return raw;
  return "monthly";
}

export function getPlan(alias: PlanAlias): PlanConfig {
  return PLAN_CONFIG.find((item) => item.alias === alias) || PLAN_CONFIG[1];
}

export function computePrice(alias: PlanAlias, period: BillingPeriod, promo: string) {
  const config = getPlan(alias);
  const base = period === "annual" ? config.longPrice : config.shortPrice;
  const periodLabel = period === "annual" ? config.longLabel : config.shortLabel;
  const discountPercent = promoDiscountPercent(promo);
  const discountAmount = Math.round((base * discountPercent) / 100);
  const total = Math.max(0, base - discountAmount);

  return {
    base,
    periodLabel,
    discountPercent,
    discountAmount,
    total,
    planCode: config.defaultCode
  };
}
