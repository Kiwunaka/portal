// Regenerates WebApp and marketing browser icons from one vector mark.
// Sync src/app/icon.svg from the current brand master before running this.
// Usage: npm run generate:favicon
import { chromium } from "@playwright/test";
import { copyFileSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ICO_SIZES = [16, 32, 48, 256];
const RASTER_SIZES = [...ICO_SIZES, 512];
const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const webappRoot = path.resolve(scriptDir, "..");
const repoRoot = path.resolve(webappRoot, "..");
const svgPath = path.join(webappRoot, "src", "app", "icon.svg");
const webappFaviconPath = path.join(webappRoot, "src", "app", "favicon.ico");
const marketingPublic = path.join(repoRoot, "marketing", "public");

const svgMarkup = readFileSync(svgPath, "utf8");
const svgDataUrl = `data:image/svg+xml;base64,${Buffer.from(svgMarkup).toString("base64")}`;

async function renderPng(page, size) {
  await page.setViewportSize({ width: size, height: size });
  await page.setContent(
    `<style>html,body{margin:0;padding:0;background:transparent;overflow:hidden}img{display:block}</style>` +
      `<img src="${svgDataUrl}" width="${size}" height="${size}" alt="">`,
    { waitUntil: "load" },
  );
  return await page.screenshot({
    omitBackground: true,
    clip: { x: 0, y: 0, width: size, height: size },
  });
}

function packIco(frames) {
  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(frames.length, 4);

  const entries = [];
  let offset = 6 + frames.length * 16;
  for (const { size, png } of frames) {
    const entry = Buffer.alloc(16);
    entry.writeUInt8(size >= 256 ? 0 : size, 0);
    entry.writeUInt8(size >= 256 ? 0 : size, 1);
    entry.writeUInt8(0, 2);
    entry.writeUInt8(0, 3);
    entry.writeUInt16LE(1, 4);
    entry.writeUInt16LE(32, 6);
    entry.writeUInt32LE(png.length, 8);
    entry.writeUInt32LE(offset, 12);
    entries.push(entry);
    offset += png.length;
  }
  return Buffer.concat([header, ...entries, ...frames.map((frame) => frame.png)]);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ deviceScaleFactor: 1 });
const frames = [];
for (const size of RASTER_SIZES) {
  frames.push({ size, png: await renderPng(page, size) });
}
await browser.close();

const frame = (size) => frames.find((item) => item.size === size).png;
const ico = packIco(frames.filter((item) => ICO_SIZES.includes(item.size)));
writeFileSync(webappFaviconPath, ico);
writeFileSync(path.join(marketingPublic, "favicon.ico"), ico);
writeFileSync(path.join(marketingPublic, "tab-icon-32.png"), frame(32));
writeFileSync(path.join(marketingPublic, "tab-icon-256.png"), frame(256));
writeFileSync(path.join(marketingPublic, "apple-icon.png"), frame(512));
copyFileSync(svgPath, path.join(marketingPublic, "pokrov-logo.svg"));
console.log(
  `[generate-favicon] synced WebApp + marketing icons (${ico.length} ICO bytes; raster sizes: ${RASTER_SIZES.join(", ")})`,
);
