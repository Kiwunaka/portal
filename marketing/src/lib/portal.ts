export type PortalPublicConfig = {
  apiBaseUrl: string;
  webappUrl: string;
  connectUrl: string;
  checkoutUrl: string;
  botUrl: string;
  helpbotUrl: string;
  feedbackbotUrl: string;
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

export const CANONICAL_PLATFORM_BRAND = "POKROV";
export const CANONICAL_CLIENT_BRAND = "POKROV VPN";
export const CANONICAL_API_BASE_URL = "https://api.pokrov.space";
export const CANONICAL_WEBAPP_URL = "https://app.pokrov.space";
export const CANONICAL_CONNECT_URL = "https://connect.pokrov.space";
export const CANONICAL_PAY_ORIGIN = "https://pay.pokrov.space";
export const CANONICAL_CHECKOUT_URL = `${CANONICAL_PAY_ORIGIN}/checkout`;
export const CANONICAL_BOT_URL = "https://t.me/pokrov_vpnbot";
export const CANONICAL_SUPPORT_BOT_URL = "https://t.me/pokrov_supportbot";
export const CANONICAL_FEEDBACK_BOT_URL = "https://t.me/pokrov_feedbackbot";
export const CANONICAL_NEWS_CHANNEL_URL = "https://t.me/pokrov_vpn";
export const CANONICAL_CONTACT_EMAIL = "support@pokrov.space";
export const CANONICAL_ENTERPRISE_EMAIL = "enterprise@pokrov.space";

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
  "marketing.meta.title": { ru: "POKROV VPN - свободный интернет без лишней суеты" },
  "marketing.meta.description": {
    ru: "Запуск через Telegram, 5 дней теста, понятный кабинет и поддержка без сложной настройки и лишних шагов.",
  },
  "marketing.hero.kicker": { ru: "POKROV VPN • Telegram-first • понятный старт" },
  "marketing.hero.title": { ru: "Свободный интернет без сложной настройки" },
  "marketing.hero.subtitle": {
    ru: "Откройте Telegram, запустите тест на 5 дней и спокойно проверьте сервис на своих устройствах. Если всё подходит, продолжите в кабинете без перегруза и лишних экранов.",
  },
  "marketing.hero.primary_cta": { ru: "Начать в Telegram" },
  "marketing.hero.secondary_cta": { ru: "Посмотреть тарифы" },
  "marketing.support.title": { ru: "Если нужна помощь, мы рядом" },
  "marketing.support.subtitle": {
    ru: "Поддержка отвечает в Telegram и помогает с оплатой, приложениями и подключением без долгой переписки и бюрократии.",
  },
  "marketing.checkout.title": { ru: "Оплата без лишних экранов" },
  "marketing.checkout.subtitle": {
    ru: "Срок и итоговая сумма видны сразу. После оплаты доступ обновляется автоматически.",
  },
  "marketing.checkout.primary_cta": { ru: "Перейти к оплате" },
  "marketing.legal.offer.intro": {
    ru: "Здесь собраны основные условия доступа к сервису POKROV VPN, правила оплаты и порядок использования выбранного периода доступа.",
  },
  "marketing.legal.privacy.intro": {
    ru: "POKROV VPN хранит только те данные, которые нужны для работы аккаунта, поддержки и стабильности сервиса.",
  },
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

export function normalizeCheckoutUrl(raw: string, webDomainFallback = "https://pay.pokrov.space"): string {
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
      CANONICAL_API_BASE_URL,
  );
  const webappUrl = cleanUrl(env.NEXT_PUBLIC_WEBAPP_URL || CANONICAL_WEBAPP_URL);
  const connectUrl = cleanUrl(env.NEXT_PUBLIC_CONNECT_URL || CANONICAL_CONNECT_URL);
  const botUrl = normalizeTelegramUrl(env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "", CANONICAL_BOT_URL);
  const helpbotUrl = normalizeTelegramUrl(
    env.NEXT_PUBLIC_CONTACT_TG_URL || env.NEXT_PUBLIC_SUPPORT_TG_URL || "",
    CANONICAL_SUPPORT_BOT_URL,
  );
  const feedbackbotUrl = normalizeTelegramUrl(
    env.NEXT_PUBLIC_FEEDBACK_TG_URL || env.NEXT_PUBLIC_FEEDBACK_BOT_URL || "",
    CANONICAL_FEEDBACK_BOT_URL,
  );
  const contactFormUrl = normalizeTelegramUrl(env.NEXT_PUBLIC_CONTACT_FORM_URL || "", helpbotUrl);
  const checkoutUrl = normalizeCheckoutUrl(
    env.NEXT_PUBLIC_CHECKOUT_PAGE_URL || env.NEXT_PUBLIC_PAY_CHECKOUT_URL || env.PAY_CHECKOUT_URL || "",
    CANONICAL_PAY_ORIGIN,
  );
  return {
    apiBaseUrl,
    webappUrl,
    connectUrl,
    checkoutUrl,
    botUrl,
    helpbotUrl,
    feedbackbotUrl,
    supportTelegramUrl: helpbotUrl,
    contactEmail: trim(env.NEXT_PUBLIC_CONTACT_EMAIL, CANONICAL_CONTACT_EMAIL),
    enterpriseEmail: trim(env.NEXT_PUBLIC_ENTERPRISE_EMAIL, CANONICAL_ENTERPRISE_EMAIL),
    contactFormUrl,
    newsChannelUrl: normalizeTelegramUrl(
      env.NEXT_PUBLIC_TG_CHANNEL_LINK || env.NEXT_PUBLIC_NEWS_CHANNEL || "",
      CANONICAL_NEWS_CHANNEL_URL,
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
  return "2026-03-22";
}
