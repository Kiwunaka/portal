import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import * as fsSync from "node:fs";
import * as fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";
import { fileURLToPath, pathToFileURL } from "node:url";

import { renderAnalytical } from "./src/analytical.mjs";
import { validateDataset } from "./src/common.mjs";
import { renderGrowthFunnel } from "./src/growth-funnel.mjs";
import { renderWarRoom } from "./src/war-room.mjs";

const execFileAsync = promisify(execFile);
const WIDTH = 1600;
const HEIGHT = 5000;
const INFOGRAPHICS_DIR = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_SOURCE_PATH = path.resolve(
  INFOGRAPHICS_DIR,
  "../archive/infographic-data.json",
);
const OUTPUT_DIR = INFOGRAPHICS_DIR;

const OUTPUTS = [
  {
    name: "01-analytical-report",
    render: renderAnalytical,
  },
  {
    name: "02-war-room",
    render: renderWarRoom,
  },
  {
    name: "03-growth-funnel",
    render: renderGrowthFunnel,
  },
];

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

export function manifestSourcePath(sourcePath = DEFAULT_SOURCE_PATH) {
  return path.relative(OUTPUT_DIR, path.resolve(sourcePath)).split(path.sep).join("/");
}

function findBrowserExecutable() {
  const candidates = [
    process.env.CHROME_EXECUTABLE_PATH,
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
  ].filter(Boolean);

  const executablePath = candidates.find((candidate) => fsSync.existsSync(candidate));
  if (!executablePath) throw new Error("No local Chrome/Edge executable found");
  return executablePath;
}

export async function renderPng(htmlPath, pngPath) {
  const executablePath = findBrowserExecutable();
  const resolvedHtmlPath = path.resolve(htmlPath);
  const resolvedPngPath = path.resolve(pngPath);

  await execFileAsync(executablePath, [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
    `--window-size=${WIDTH},${HEIGHT}`,
    `--screenshot=${resolvedPngPath}`,
    pathToFileURL(resolvedHtmlPath).href,
  ], { timeout: 120000, windowsHide: true });

  const stat = await fs.stat(resolvedPngPath);
  if (stat.size < 10000) throw new Error(`Suspicious PNG size: ${stat.size}`);
}

export async function buildAll(sourcePath = DEFAULT_SOURCE_PATH) {
  const resolvedSourcePath = path.resolve(sourcePath);
  const sourceBytes = await fs.readFile(resolvedSourcePath);
  const data = JSON.parse(sourceBytes.toString("utf8"));
  validateDataset(data);

  const sourceSha256 = sha256(sourceBytes);
  await fs.mkdir(OUTPUT_DIR, { recursive: true });

  const outputs = [];
  for (const output of OUTPUTS) {
    const htmlFilename = `${output.name}.html`;
    const pngFilename = `${output.name}.png`;
    const htmlPath = path.join(OUTPUT_DIR, htmlFilename);
    const pngPath = path.join(OUTPUT_DIR, pngFilename);
    const html = output.render(data, sourceSha256);
    const normalizedHtml = `${html.replace(/[ \t]+$/gm, "").trimEnd()}\n`;

    await fs.writeFile(htmlPath, normalizedHtml, "utf8");
    await renderPng(htmlPath, pngPath);
    const pngBytes = await fs.readFile(pngPath);

    outputs.push({
      html: htmlFilename,
      png: pngFilename,
      width: WIDTH,
      height: HEIGHT,
      sha256: sha256(pngBytes),
      source_sha256: sourceSha256,
    });
  }

  const manifest = {
    generated_at: new Date().toISOString(),
    source: manifestSourcePath(resolvedSourcePath),
    source_sha256: sourceSha256,
    dimensions: { width: WIDTH, height: HEIGHT },
    outputs,
  };
  await fs.writeFile(
    path.join(OUTPUT_DIR, "manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
    "utf8",
  );
  return manifest;
}

const isDirectRun = process.argv[1]
  && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isDirectRun) {
  const manifest = await buildAll(process.argv[2] ?? DEFAULT_SOURCE_PATH);
  console.log(JSON.stringify(manifest, null, 2));
}
