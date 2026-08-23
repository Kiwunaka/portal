import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const appRoot = resolve(import.meta.dirname, "..");
const outRoot = join(appRoot, "out");

function fail(message) {
  throw new Error(`operator cutover verification: ${message}`);
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function filesBelow(root, suffix) {
  const found = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) found.push(...filesBelow(path, suffix));
    else if (entry.isFile() && entry.name.endsWith(suffix)) found.push(path);
  }
  return found;
}

const manifest = JSON.parse(readFileSync(join(appRoot, "operator-center.manifest.json"), "utf8"));
const cutover = JSON.parse(readFileSync(join(appRoot, "operator-center.cutover.json"), "utf8"));
const build = JSON.parse(readFileSync(join(outRoot, "__build.json"), "utf8"));
const routes = JSON.parse(readFileSync(join(outRoot, "__routes.json"), "utf8"));
const expectedRouteHash = sha256(stableJson(manifest));
const expectedCutoverHash = sha256(stableJson(cutover));

if (build.route_manifest_hash !== expectedRouteHash || routes.manifest_hash !== expectedRouteHash) fail("route manifest hash mismatch");
if (build.cutover_matrix_hash !== expectedCutoverHash || routes.cutover_matrix_hash !== expectedCutoverHash) fail("cutover matrix hash mismatch");
if (cutover.local_parity.status !== "PASS") fail("local parity is not PASS");
if (manifest.routes.some((route) => route.state === "legacy-route-active")) fail("legacy route state remains active");

for (const route of manifest.routes) {
  const html = route.path === "/" ? join(outRoot, "index.html") : join(outRoot, route.path.slice(1), "index.html");
  if (!existsSync(html)) fail(`static route is missing: ${route.path}`);
}

const jsFiles = filesBelow(join(outRoot, "_next", "static", "chunks"), ".js");
const jsBytes = jsFiles.reduce((total, path) => total + statSync(path).size, 0);
const largestJsBytes = Math.max(0, ...jsFiles.map((path) => statSync(path).size));
if (jsFiles.length > 20) fail(`JavaScript chunk count exceeds budget: ${jsFiles.length}`);
if (jsBytes > 2_500_000) fail(`JavaScript bytes exceed budget: ${jsBytes}`);
if (largestJsBytes > 1_250_000) fail(`largest JavaScript chunk exceeds budget: ${largestJsBytes}`);

const browserSource = jsFiles.map((path) => readFileSync(path, "utf8")).join("\n");
for (const forbidden of [
  "/api/admin/ops/overview",
  "/api/admin/online/users",
  "/api/admin/funnel/summary",
  "/api/admin/referrals/pending",
  "/api/admin/referrals/process",
  "/api/admin/auth/session",
  "X-Web-Auth-Token",
]) {
  if (browserSource.includes(forbidden)) fail(`forbidden browser contract remains: ${forbidden}`);
}

process.stdout.write(`${JSON.stringify({
  ok: true,
  routes: manifest.routes.length,
  workspaces: manifest.workspaces.length,
  js_chunks: jsFiles.length,
  js_bytes: jsBytes,
  largest_js_bytes: largestJsBytes,
  route_manifest_hash: expectedRouteHash,
  cutover_matrix_hash: expectedCutoverHash,
})}\n`);
