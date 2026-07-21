import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

const canonicalRoutes = [
  "/mobile/",
  "/tiktok/",
  "/youtube/",
  "/devices/",
  "/telegram/",
  "/vpn/",
  "/android/",
  "/windows/",
  "/install/android/",
  "/install/windows/",
  "/trial/no-card/",
  "/billing/no-autosubscription/",
  "/trust/github-releases/",
  "/compare/free-vpn/",
  "/support/install/",
];

const seoRegistryRoutes = [
  ...canonicalRoutes,
  "/install/",
];

const legacyRedirectMap = new Map([
  ["/bystryy-vpn-na-telefon/", "/mobile/"],
  ["/vpn-dlya-tiktok/", "/tiktok/"],
  ["/vpn-dlya-youtube/", "/youtube/"],
  ["/vpn-na-iphone-android-windows/", "/devices/"],
  ["/vpn-telegram-bot/", "/telegram/"],
  ["/vpn-skachat/", "/vpn/"],
  ["/vpn-skachat-besplatno/", "/vpn/"],
  ["/skachat-vpn/", "/vpn/"],
  ["/besplatnyy-vpn/", "/vpn/"],
  ["/vpn-android/", "/android/"],
  ["/vpn-windows/", "/windows/"],
  ["/no-card-trial/", "/trial/no-card/"],
  ["/without-subscription/", "/billing/no-autosubscription/"],
  ["/github-releases/", "/trust/github-releases/"],
  ["/telegram-bonus/", "/telegram/"],
  ["/support-install/", "/support/install/"],
  ["/install/windows-smartscreen/", "/install/windows/"],
  ["/trust/checksums/", "/trust/github-releases/"],
]);

const sourceFiles = [
  "src/app/layout.tsx",
  "src/app/page.tsx",
  "src/app/manifest.ts",
  "src/app/install/page.tsx",
  "src/app/checkout/page.tsx",
  "src/app/offer/page.tsx",
  "src/app/privacy/page.tsx",
  "src/app/mobile/page.tsx",
  "src/app/tiktok/page.tsx",
  "src/app/youtube/page.tsx",
  "src/app/devices/page.tsx",
  "src/app/telegram/page.tsx",
  "src/app/vpn/page.tsx",
  "src/components/home/services-grid.tsx",
  "src/components/intent/intent-landing.tsx",
  "src/components/layout/page-shell.tsx",
  "src/components/layout/footer.tsx",
  "src/components/seo/seo-content-page.tsx",
  "src/lib/marketing-site.ts",
  "src/lib/seo-pages.ts",
];

const outputExtensions = new Set([".html", ".xml", ".webmanifest", ".txt", ".md"]);
const errors = [];

function readText(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

function fileExists(relativePath) {
  return fs.existsSync(path.join(root, relativePath));
}

function pushError(message) {
  errors.push(message);
}

function containsStandaloneRoute(content, route) {
  const escaped = route.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|["'\\s(=])${escaped}($|["'\\s)#?])`).test(content);
}

function walkFiles(dirPath, visitor) {
  if (!fs.existsSync(dirPath)) return;
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      walkFiles(fullPath, visitor);
      continue;
    }
    visitor(fullPath);
  }
}

function checkCanonicalRoutes() {
  for (const route of canonicalRoutes) {
    const pagePath = `src/app${route}page.tsx`;
    if (!fileExists(pagePath)) {
      pushError(`Missing canonical marketing route file: ${pagePath}`);
    }
  }
}

function checkRedirectsFile() {
  const redirectsPath = "public/_redirects";
  if (!fileExists(redirectsPath)) {
    pushError(`Missing ${redirectsPath} with legacy permanent redirects.`);
    return;
  }

  const redirects = readText(redirectsPath)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  for (const [legacy, target] of legacyRedirectMap) {
    const expectedWithSlash = `${legacy} ${target} 301!`;
    const expectedWithoutSlash = `${legacy.replace(/\/$/, "")} ${target} 301!`;
    const found = redirects.includes(expectedWithSlash) || redirects.includes(expectedWithoutSlash);
    if (!found) {
      pushError(`Missing permanent redirect for ${legacy} -> ${target} in public/_redirects.`);
    }
  }
}

function checkSourceCopy() {
  const forbiddenPublicPatterns = [
    { label: "visible brand 'POKROV Network'", regex: /POKROV Network/g },
  ];

  for (const relativePath of sourceFiles) {
    const content = readText(relativePath);
    for (const pattern of forbiddenPublicPatterns) {
      if (pattern.regex.test(content)) {
        pushError(`Forbidden ${pattern.label} remains in ${relativePath}.`);
      }
      pattern.regex.lastIndex = 0;
    }
  }

  const catalog = JSON.parse(readText("../copy/catalog.ru.json"));
  for (const [key, item] of Object.entries(catalog.items || {})) {
    if (!String(key).startsWith("marketing.")) continue;
    const ru = String(item?.ru || "");
    if (/POKROV Network/.test(ru)) {
      pushError(`Catalog marketing key ${key} still uses 'POKROV Network'.`);
    }
  }
}

function checkNoMetaKeywords() {
  for (const relativePath of sourceFiles) {
    const content = readText(relativePath);
    if (/\bkeywords\s*:/.test(content)) {
      pushError(`Meta keywords remain in ${relativePath}.`);
    }
  }
}

function checkRobotsSource() {
  const robots = readText("src/app/robots.ts");
  const requiredBots = [
    "OAI-SearchBot",
    "ChatGPT-User",
    "GPTBot",
    "ClaudeBot",
    "Claude-SearchBot",
    "Claude-User",
    "PerplexityBot",
    "Perplexity-User",
    "Googlebot",
    "Bingbot",
  ];

  if (robots.includes('"/_next/"') || robots.includes("'/_next/'")) {
    pushError("robots.ts must not disallow /_next/.");
  }
  if (!robots.includes('"/api/"') && !robots.includes("'/api/'")) {
    pushError("robots.ts must keep /api/ disallowed.");
  }
  for (const bot of requiredBots) {
    if (!robots.includes(bot)) {
      pushError(`robots.ts is missing user agent ${bot}.`);
    }
  }
}

function checkSitemapSource() {
  const marketingSite = readText("src/lib/marketing-site.ts");
  const seoPages = readText("src/lib/seo-pages.ts");

  for (const legacyRoute of legacyRedirectMap.keys()) {
    if (containsStandaloneRoute(marketingSite, legacyRoute)) {
      pushError(`Legacy route ${legacyRoute} still appears in MARKETING_SITEMAP_ROUTES.`);
    }
  }
  for (const route of seoRegistryRoutes) {
    if (!seoPages.includes(`"${route}"`)) {
      pushError(`SEO registry route ${route} is missing from src/lib/seo-pages.ts.`);
    }
  }
  if (!marketingSite.includes("SEO_SITEMAP_ROUTES")) {
    pushError("MARKETING_SITEMAP_ROUTES must include SEO_SITEMAP_ROUTES.");
  }
  if (marketingSite.includes("lastModified: new Date(),")) {
    pushError("Sitemap still uses dynamic new Date() instead of route lastReviewed.");
  }
}

function checkMachineReadableFiles() {
  const llms = readText("public/llms.txt");
  const pricing = readText("public/pricing.md");

  for (const route of seoRegistryRoutes) {
    const absoluteUrl = `https://pokrov.space${route}`;
    if (!llms.includes(absoluteUrl)) {
      pushError(`llms.txt is missing ${absoluteUrl}.`);
    }
  }
  for (const snippet of ["5 days", "no card", "No automatic renewal", "99 RUB", "GitHub Releases", "+5 days", "up to 10 days"]) {
    if (!pricing.includes(snippet) && !llms.includes(snippet)) {
      pushError(`Machine-readable files are missing SEO/pricing snippet: ${snippet}`);
    }
  }
}

function checkSchemaHelpers() {
  const marketingSite = readText("src/lib/marketing-site.ts");
  const seoPage = readText("src/components/seo/seo-content-page.tsx");
  for (const snippet of [
    "buildWebPageJsonLd",
    "buildHowToJsonLd",
    "buildItemListJsonLd",
    "buildCheckoutServiceJsonLd",
    "FAQPage",
    "@id",
  ]) {
    if (!marketingSite.includes(snippet) && !seoPage.includes(snippet)) {
      pushError(`Structured data helper is missing ${snippet}.`);
    }
  }
}

function checkBuiltOutput() {
  const outDir = path.join(root, "out");
  if (!fs.existsSync(outDir)) return;

  walkFiles(outDir, (fullPath) => {
    if (!outputExtensions.has(path.extname(fullPath))) return;
    const relativePath = path.relative(root, fullPath).replace(/\\/g, "/");
    const content = fs.readFileSync(fullPath, "utf8");
    if (/POKROV Network/.test(content)) {
      pushError(`Built artifact ${relativePath} still exposes 'POKROV Network'.`);
    }
    if (/<meta name="keywords"/i.test(content)) {
      pushError(`Built artifact ${relativePath} still emits meta keywords.`);
    }
    for (const legacyRoute of legacyRedirectMap.keys()) {
      if (containsStandaloneRoute(content, legacyRoute)) {
        pushError(`Built artifact ${relativePath} still references legacy route ${legacyRoute}.`);
      }
    }
  });
}

checkCanonicalRoutes();
checkRedirectsFile();
checkSourceCopy();
checkNoMetaKeywords();
checkRobotsSource();
checkSitemapSource();
checkMachineReadableFiles();
checkSchemaHelpers();
checkBuiltOutput();

if (errors.length > 0) {
  console.error("Marketing SEO/brand checks failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log("Marketing SEO/brand checks passed.");
