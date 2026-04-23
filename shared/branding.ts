import { getProductFacts } from "./product-facts";
import { getPublicUrls } from "./public-urls";

const productFacts = getProductFacts();
const publicUrls = getPublicUrls();

export const POKROV_THEME_STORAGE_KEY = "pokrov-theme";
export const POKROV_LEGACY_THEME_STORAGE_KEYS = ["portal-theme"] as const;

export const pokrovBranding = {
  brandName: productFacts.brands.platform,
  clientName: productFacts.brands.client,
  cabinetName: "Личный кабинет",
  cabinetEyebrow: "личный кабинет",
  siteLinkLabel: `На сайт ${productFacts.brands.platform}`,
  marketingUrl: publicUrls.surfaces.marketing,
  webappUrl: publicUrls.surfaces.webapp,
  themeStorageKey: POKROV_THEME_STORAGE_KEY,
  legacyThemeStorageKeys: POKROV_LEGACY_THEME_STORAGE_KEYS,
  metadataTitle: `${productFacts.brands.platform} - Личный кабинет`,
  metadataDescription:
    "Проверяйте доступ, управляйте устройствами и обращайтесь в поддержку из одного спокойного кабинета.",
} as const;

export type PokrovBranding = typeof pokrovBranding;
