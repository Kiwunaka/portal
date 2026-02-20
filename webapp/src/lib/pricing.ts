export type PlanKey = "start" | "pro" | "ultra";
export type BillingPeriod = "monthly" | "annual";

export type PlanConfig = {
  key: PlanKey;
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
    key: "start",
    name: "Start",
    subtitle: "Мягкий вход без лишних затрат",
    shortPrice: 99,
    longPrice: 99,
    shortLabel: "30 дней",
    longLabel: "30 дней",
    devices: "1 устройство",
    promise: "Проверяете сервис в реальных задачах с минимальным порогом входа.",
    objection: "Когда захотите больше устройств и стран, легко перейти на Pro.",
    perks: ["30 дней", "1 устройство", "NL-маршрут"],
  },
  {
    key: "pro",
    name: "Pro",
    subtitle: "Оптимум на каждый день",
    shortPrice: 249,
    longPrice: 699,
    shortLabel: "1 месяц",
    longLabel: "3 месяца",
    devices: "до 5 устройств",
    promise: "Сбалансированный выбор для стабильного ежедневного использования.",
    objection: "Если хотите меньше рутины с продлением, подойдет Ultra.",
    perks: ["1 или 3 месяца", "До 5 устройств", "Все страны"],
  },
  {
    key: "ultra",
    name: "Ultra",
    subtitle: "Длинный горизонт и спокойный ритм",
    shortPrice: 1199,
    longPrice: 1499,
    shortLabel: "6 месяцев",
    longLabel: "12 месяцев",
    devices: "до 5 устройств",
    promise: "Ниже цена за месяц и меньше возвратов к оплате.",
    objection: "В линейке есть 6, 9 и 12 месяцев: 1199 / 1399 / 1499 ₽.",
    perks: ["6, 9 или 12 месяцев", "До 5 устройств", "Максимальный приоритет"],
  },
];

const PROMO_RULES: Record<string, number> = {
  PORTAL10: 10,
  WELCOME15: 15,
  FAST20: 20,
};

export function normalizePromo(raw: string): string {
  return raw.trim().toUpperCase();
}

export function promoDiscountPercent(raw: string): number {
  const key = normalizePromo(raw);
  return PROMO_RULES[key] || 0;
}

export function parsePlan(raw: string | null | undefined): PlanKey {
  if (raw === "start" || raw === "pro" || raw === "ultra") return raw;
  return "pro";
}

export function parseBillingPeriod(raw: string | null | undefined): BillingPeriod {
  if (raw === "annual" || raw === "monthly") return raw;
  return "monthly";
}

export function getPlan(plan: PlanKey): PlanConfig {
  return PLAN_CONFIG.find((item) => item.key === plan) || PLAN_CONFIG[1];
}

export function computePrice(plan: PlanKey, period: BillingPeriod, promo: string) {
  const config = getPlan(plan);
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
  };
}
