// Regenerates src/app/favicon.ico from the WebApp vector mark.
// Sync src/app/icon.svg from the current brand master before running this.
// Usage: npm run generate:favicon
import { chromium } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const SIZES = [16, 32, 48, 256];
const svgPath = path.join(process.cwd(), "src", "app", "icon.svg");
const outPath = path.join(process.cwd(), "src", "app", "favicon.ico");

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
for (const size of SIZES) {
  frames.push({ size, png: await renderPng(page, size) });
}
await browser.close();

const ico = packIco(frames);
writeFileSync(outPath, ico);
console.log(
  `[generate-favicon] wrote ${outPath} (${ico.length} bytes, sizes: ${SIZES.join(", ")})`,
);
