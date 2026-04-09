export type {
  PlanAlias,
  PlanCode,
  PortalPublicConfig as PokrovPublicConfig,
} from "../../../shared/portal-config";

export {
  CANONICAL_API_BASE_URL,
  CANONICAL_BOT_URL,
  CANONICAL_CHECKOUT_URL,
  CANONICAL_CLIENT_BRAND,
  CANONICAL_CONNECT_URL,
  CANONICAL_CONTACT_EMAIL,
  CANONICAL_ENTERPRISE_EMAIL,
  CANONICAL_FEEDBACK_BOT_URL,
  CANONICAL_MARKETING_SITE_URL,
  CANONICAL_NEWS_CHANNEL_URL,
  CANONICAL_PAY_ORIGIN,
  CANONICAL_PLATFORM_BRAND,
  CANONICAL_SUPPORT_BOT_URL,
  CANONICAL_WEBAPP_URL,
  PLAN_ALIAS_TO_CODE,
  normalizeCheckoutUrl,
  normalizePlanCode,
  normalizeTelegramUrl,
} from "../../../shared/portal-config";

export {
  getCatalogItem,
  getCopyCatalogVersion,
  getCopyText,
} from "../../../shared/copy";

export { getPortalPublicConfig as getPokrovPublicConfig } from "../../../shared/portal-config";
