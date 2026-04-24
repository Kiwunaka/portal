import catalog from "../copy/catalog.ru.json";

export type CatalogItem = {
  surface: string;
  ru: string;
  variables: string[];
  tone: string;
  allowed_public: boolean;
  compliance_notes: string;
  ab_variant: string;
};

type CatalogShape = {
  catalog_version: string;
  locale: string;
  items: Record<string, CatalogItem>;
};

const typedCatalog = catalog as CatalogShape;
export const GLOBAL_CTA_COPY_KEYS = {
  primary: "marketing.hero.primary_cta",
  secondary: "marketing.hero.secondary_cta",
  checkout: "marketing.checkout.primary_cta",
  install: "marketing.install.primary_cta",
  support: "bot.shared.support_cta",
} as const;

export const GLOBAL_GLOSSARY_COPY_KEYS = {
  brandSubtitle: "brand.subtitle",
  appConnection: "app.nav.protection",
  appLocations: "app.nav.locations",
  appRules: "app.nav.rules",
  appProfile: "app.nav.profile",
  cabinetHome: "cabinet.nav.home",
  cabinetBilling: "cabinet.nav.billing",
  cabinetDevices: "cabinet.nav.devices",
  cabinetDownloads: "cabinet.nav.downloads",
  cabinetSupport: "cabinet.nav.support",
  cabinetProfile: "cabinet.nav.profile",
  cabinetSettings: "cabinet.nav.settings",
  appleBadge: "platform.apple.badge",
} as const;

const legacyPublicVpnAllowlist = [
  /\bPOKROV VPN\b/gi,
  /\b@pokrov_vpn\b/gi,
  /\bt\.me\/pokrov_vpn\b/gi,
  /\bpokrov_vpn\b/gi,
];
const directMeaningVpnPattern = /\bVPN\b/i;

export type PublicCopyValidation = {
  ok: boolean;
  hasDirectMeaningVpnWording: boolean;
  reason: string | null;
};

export type CatalogPublicCopyValidation = PublicCopyValidation & {
  key: string;
  exists: boolean;
  allowedPublic: boolean;
};

function stripLegacyPublicVpnExceptions(text: string): string {
  return legacyPublicVpnAllowlist.reduce((current, pattern) => current.replace(pattern, ""), text);
}

export function getCopyCatalog(): CatalogShape {
  return typedCatalog;
}

export function getCatalogItem(key: string): CatalogItem | null {
  return typedCatalog.items[key] || null;
}

export function hasCatalogItem(key: string): boolean {
  return key in typedCatalog.items;
}

export function listCatalogKeys(prefix?: string): string[] {
  const keys = Object.keys(typedCatalog.items);
  if (!prefix) {
    return keys.sort();
  }
  return keys.filter((key) => key.startsWith(prefix)).sort();
}

export function getCatalogEntriesByPrefix(prefix: string): Array<[string, CatalogItem]> {
  return listCatalogKeys(prefix).map((key) => [key, typedCatalog.items[key]] as [string, CatalogItem]);
}

export function getCatalogNamespaces(): string[] {
  return Array.from(new Set(Object.keys(typedCatalog.items).map((key) => key.split(".")[0]))).sort();
}

export function getCopyText(
  key: string,
  fallback = "",
  variables?: Record<string, string | number | null | undefined>,
): string {
  const item = getCatalogItem(key);
  const base = item?.ru || fallback;
  if (!variables || !base) return base;
  return base.replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, name: string) => {
    const value = variables[name];
    return value == null ? "" : String(value);
  });
}

export function getCopyCatalogVersion(): string {
  return typedCatalog.catalog_version;
}

export function containsDirectMeaningVpnWording(text: string): boolean {
  return directMeaningVpnPattern.test(stripLegacyPublicVpnExceptions(text));
}

export function validatePublicCopyText(text: string): PublicCopyValidation {
  const hasDirectMeaningVpnWording = containsDirectMeaningVpnWording(text);
  return {
    ok: !hasDirectMeaningVpnWording,
    hasDirectMeaningVpnWording,
    reason: hasDirectMeaningVpnWording
      ? "Direct-meaning VPN wording is not allowed for public-safe shared copy."
      : null,
  };
}

export function validateCatalogItemPublicCopy(key: string): CatalogPublicCopyValidation {
  const item = getCatalogItem(key);
  if (!item) {
    return {
      key,
      exists: false,
      allowedPublic: false,
      ok: false,
      hasDirectMeaningVpnWording: false,
      reason: "Catalog item not found.",
    };
  }

  const validation = validatePublicCopyText(item.ru);
  return {
    key,
    exists: true,
    allowedPublic: item.allowed_public,
    ok: !item.allowed_public || validation.ok,
    hasDirectMeaningVpnWording: validation.hasDirectMeaningVpnWording,
    reason:
      item.allowed_public && !validation.ok
        ? validation.reason
        : null,
  };
}
