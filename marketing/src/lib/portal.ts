export type PortalPublicConfig = {
  apiBaseUrl: string;
  webappUrl: string;
  checkoutUrl: string;
  botUrl: string;
  helpbotUrl: string;
  supportTelegramUrl: string;
  contactEmail: string;
  enterpriseEmail: string;
  contactFormUrl: string;
  newsChannelUrl: string;
  androidPlayUrl: string;
  androidApkUrl: string;
  androidMirrorUrl: string;
  windowsExeUrl: string;
  windowsMirrorUrl: string;
  docsUrl: string;
};

export const PLAN_ALIAS_TO_CODE = {
  start: "start_99",
  pro: "1_month",
  ultra: "12_months",
} as const;

export type PlanAlias = keyof typeof PLAN_ALIAS_TO_CODE;
export type PlanCode = (typeof PLAN_ALIAS_TO_CODE)[PlanAlias] | "3_months" | "6_months" | "9_months";

type CatalogItem = {
  ru: string;
};

const COPY: Record<string, CatalogItem> = {
  "marketing.meta.title": { ru: "PORTAL - цифровой доступ без лишних шагов" },
  "marketing.meta.description": { ru: "Быстрый запуск через Telegram, оплата в рублях и спокойный личный кабинет без перегруза деталями." },
  "marketing.hero.kicker": { ru: "PORTAL • запуск через Telegram • оплата в рублях" },
  "marketing.hero.title": { ru: "Подключайтесь быстро и без лишней настройки" },
  "marketing.hero.subtitle": { ru: "Откройте Telegram, выберите удобный план и продолжайте свои дела без длинного онбординга." },
  "marketing.hero.primary_cta": { ru: "Подключиться в Telegram" },
  "marketing.hero.secondary_cta": { ru: "Посмотреть планы" },
  "marketing.support.title": { ru: "Если нужен человек, мы рядом" },
  "marketing.support.subtitle": { ru: "Поддержка в Telegram, понятные ответы и быстрый переход к обращению из любого экрана." },
  "marketing.checkout.title": { ru: "Оплата в пару шагов" },
  "marketing.checkout.subtitle": { ru: "Выберите срок, проверьте итоговую сумму и перейдите на страницу оплаты без лишних экранов." },
  "marketing.checkout.primary_cta": { ru: "Перейти к оплате" },
  "marketing.legal.offer.intro": { ru: "Этот документ описывает условия доступа к цифровым услугам PORTAL и порядок оплаты выбранного периода." },
  "marketing.legal.privacy.intro": { ru: "PORTAL хранит только те данные, которые действительно нужны для работы аккаунта, поддержки и безопасности сервиса." },
};

function trim(value: string | undefined, fallback = ""): string {
  return String(value || fallback).trim();
}

function cleanUrl(value: string, fallback = ""): string {
  return trim(value, fallback).replace(/\/+$/, "");
}

export function normalizeTelegramUrl(raw: string, fallback: string): string {
  const value = cleanUrl(raw, fallback);
  if (!value) return fallback;
  if (value.startsWith("http://") || value.startsWith("https://")) return value;
  return `https://t.me/${value.replace(/^@+/, "")}`;
}

export function normalizeCheckoutUrl(raw: string, webDomainFallback = "https://portal-privacy.online"): string {
  const value = cleanUrl(raw);
  if (!value) return `${cleanUrl(webDomainFallback)}/checkout`;
  return value;
}

export function normalizePlanCode(raw: string | null | undefined, fallback: PlanCode = "1_month"): PlanCode {
  const normalized = String(raw || "").trim().toLowerCase();
  if (!normalized) return fallback;
  if (normalized in PLAN_ALIAS_TO_CODE) {
    return PLAN_ALIAS_TO_CODE[normalized as PlanAlias];
  }
  if (["start_99", "1_month", "3_months", "6_months", "9_months", "12_months"].includes(normalized)) {
    return normalized as PlanCode;
  }
  return fallback;
}

export function getPortalPublicConfig(env: Record<string, string | undefined>): PortalPublicConfig {
  const apiBaseUrl = cleanUrl(
    env.NEXT_PUBLIC_API_BASE_URL ||
      env.NEXT_PUBLIC_PUBLIC_API_BASE_URL ||
      env.VITE_PUBLIC_API_BASE_URL ||
      "https://portal-privacy.online",
  );
  const webappUrl = cleanUrl(env.NEXT_PUBLIC_WEBAPP_URL || "https://portal-privacy.online/webapp");
  const botUrl = normalizeTelegramUrl(env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "", "https://t.me/portal_privacy_bot");
  const helpbotUrl = normalizeTelegramUrl(
    env.NEXT_PUBLIC_CONTACT_TG_URL || env.NEXT_PUBLIC_SUPPORT_TG_URL || "",
    "https://t.me/portal_privacy_helpbot",
  );
  const contactFormUrl = normalizeTelegramUrl(env.NEXT_PUBLIC_CONTACT_FORM_URL || "", helpbotUrl);
  const checkoutUrl = normalizeCheckoutUrl(
    env.NEXT_PUBLIC_CHECKOUT_PAGE_URL || env.NEXT_PUBLIC_PAY_CHECKOUT_URL || env.PAY_CHECKOUT_URL || "",
    "https://portal-privacy.online",
  );
  return {
    apiBaseUrl,
    webappUrl,
    checkoutUrl,
    botUrl,
    helpbotUrl,
    supportTelegramUrl: helpbotUrl,
    contactEmail: trim(env.NEXT_PUBLIC_CONTACT_EMAIL, "support@portal-privacy.online"),
    enterpriseEmail: trim(env.NEXT_PUBLIC_ENTERPRISE_EMAIL, "enterprise@portal-privacy.online"),
    contactFormUrl,
    newsChannelUrl: normalizeTelegramUrl(
      env.NEXT_PUBLIC_TG_CHANNEL_LINK || env.NEXT_PUBLIC_NEWS_CHANNEL || "",
      "https://t.me/portal_privacy",
    ),
    androidPlayUrl: trim(env.NEXT_PUBLIC_APP_ANDROID_PLAY_URL),
    androidApkUrl: trim(env.NEXT_PUBLIC_APP_ANDROID_APK_URL),
    androidMirrorUrl: trim(env.NEXT_PUBLIC_APP_ANDROID_MIRROR_URL),
    windowsExeUrl: trim(env.NEXT_PUBLIC_APP_WINDOWS_EXE_URL),
    windowsMirrorUrl: trim(env.NEXT_PUBLIC_APP_WINDOWS_MIRROR_URL),
    docsUrl: trim(env.NEXT_PUBLIC_APP_DOCS_URL),
  };
}

export function getCatalogItem(key: string): CatalogItem | null {
  return COPY[key] || null;
}

export function getCopyText(
  key: string,
  fallback = "",
  variables?: Record<string, string | number | null | undefined>,
): string {
  const base = COPY[key]?.ru || fallback;
  if (!variables || !base) return base;
  return base.replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, name: string) => {
    const value = variables[name];
    return value == null ? "" : String(value);
  });
}

export function getCopyCatalogVersion(): string {
  return "2026-03-06";
}
