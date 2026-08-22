// Next 16 static export may write route segment payloads as nested files while
// the client requests their dot-joined equivalents. Add deterministic copies
// so a plain static server can serve the exact paths requested by the bundle.
import { cpSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const outDir = path.join(process.cwd(), "out");

function collectFiles(dir) {
  const files = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...collectFiles(full));
    else files.push(full);
  }
  return files;
}

function flattenSegmentDir(parentDir, segmentDirName) {
  const segmentDir = path.join(parentDir, segmentDirName);
  let created = 0;
  for (const file of collectFiles(segmentDir)) {
    const relative = path.relative(segmentDir, file);
    const dotted = `${segmentDirName}.${relative.split(path.sep).join(".")}`;
    cpSync(file, path.join(parentDir, dotted));
    created += 1;
  }
  return created;
}

function walk(dir) {
  let created = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const full = path.join(dir, entry.name);
    if (entry.name.startsWith("__next.")) {
      created += flattenSegmentDir(dir, entry.name);
    } else {
      created += walk(full);
    }
  }
  return created;
}

try {
  statSync(outDir);
} catch {
  console.error(`[fix-export-segment-paths] out directory not found: ${outDir}`);
  process.exit(1);
}

const created = walk(outDir);
console.log(`[fix-export-segment-paths] created ${created} dot-joined segment payload copies`);
