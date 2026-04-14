import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, "..");

const canonicalRoutes = ["/mobile/", "/tiktok/", "/youtube/", "/devices/", "/telegram/"];
const legacyRedirectMap = new Map([
  ["/bystryy-vpn-na-telefon/", "/mobile/"],
  ["/vpn-dlya-tiktok/", "/tiktok/"],
  ["/vpn-dlya-youtube/", "/youtube/"],
  ["/vpn-na-iphone-android-windows/", "/devices/"],
  ["/vpn-telegram-bot/", "/telegram/"],
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
  "src/components/marketing-landing.tsx",
  "src/lib/marketing-site.ts",
];

const outputExtensions = new Set([".html", ".xml", ".webmanifest"]);
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
    { label: "public VPN wording", regex: /\bVPN\b|\bvpn\b|\bвпн\b/gimu },
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
    if (/\bVPN\b|\bvpn\b|\bвпн\b/gimu.test(ru)) {
      pushError(`Catalog marketing key ${key} still contains public VPN wording.`);
    }
  }
}

function checkSitemapSource() {
  const content = readText("src/lib/marketing-site.ts");
  for (const legacyRoute of legacyRedirectMap.keys()) {
    if (content.includes(`path: "${legacyRoute}"`)) {
      pushError(`Legacy route ${legacyRoute} still appears in MARKETING_SITEMAP_ROUTES.`);
    }
  }
  for (const route of canonicalRoutes) {
    if (!content.includes(`"${route}"`)) {
      pushError(`Canonical route ${route} is missing from MARKETING_SITEMAP_ROUTES.`);
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
    if (/\bVPN\b|\bvpn\b|\bвпн\b/gimu.test(content)) {
      pushError(`Built artifact ${relativePath} still exposes public VPN wording.`);
    }
    for (const legacyRoute of legacyRedirectMap.keys()) {
      if (content.includes(legacyRoute)) {
        pushError(`Built artifact ${relativePath} still references legacy route ${legacyRoute}.`);
      }
    }
  });
}

checkCanonicalRoutes();
checkRedirectsFile();
checkSourceCopy();
checkSitemapSource();
checkBuiltOutput();

if (errors.length > 0) {
  console.error("Marketing SEO/brand checks failed:");
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exit(1);
}

console.log("Marketing SEO/brand checks passed.");
