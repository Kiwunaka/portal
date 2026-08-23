import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const manifestPath = join(appRoot, "operator-center.manifest.json");
const cutoverPath = join(appRoot, "operator-center.cutover.json");
const packagePath = join(appRoot, "package.json");
const args = process.argv.slice(2);
const outIndex = args.indexOf("--out-dir");
const outputDir = resolve(outIndex >= 0 ? args[outIndex + 1] : join(appRoot, "public"));

function fail(message) {
  throw new Error(`operator build contract: ${message}`);
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

function gitValue(argsList, fallback) {
  try {
    return execFileSync("git", argsList, { cwd: resolve(appRoot, ".."), encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim() || fallback;
  } catch {
    return fallback;
  }
}

const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const cutover = JSON.parse(readFileSync(cutoverPath, "utf8"));
const packageJson = JSON.parse(readFileSync(packagePath, "utf8"));
if (manifest.schema !== "pokrov-operator-center-manifest-v1") fail("unsupported manifest schema");
if (manifest.app !== "pokrov-operator-center") fail("unexpected application identity");
if (manifest.canonical_domain !== "admin.pokrov.space") fail("unexpected canonical domain");
if (!/^admin-v2\.[0-9]+$/.test(manifest.expected_api_schema || "")) fail("invalid expected API schema");
if (!Array.isArray(manifest.workspaces) || manifest.workspaces.length !== 7) fail("exactly seven workspaces are required");
if (!Array.isArray(manifest.routes) || manifest.routes.length === 0) fail("route inventory is empty");
if (manifest.cutover_matrix !== "operator-center.cutover.json") fail("cutover matrix is not canonical");
if (cutover.schema !== "pokrov-operator-center-cutover-v1") fail("unsupported cutover schema");
if (cutover.local_parity?.route_count !== manifest.routes.length) fail("cutover route count mismatch");

const workspaceIds = new Set(manifest.workspaces.map((item) => item.id));
if (workspaceIds.size !== 7) fail("workspace ids are not unique");
const routePaths = new Set();
for (const route of manifest.routes) {
  if (!workspaceIds.has(route.workspace)) fail(`unknown workspace for ${route.path}`);
  if (routePaths.has(route.path)) fail(`duplicate route ${route.path}`);
  routePaths.add(route.path);
}

const canonicalManifest = stableJson(manifest);
const routeManifestHash = sha256(canonicalManifest);
const cutoverMatrixHash = sha256(stableJson(cutover));
const commit = String(process.env.POKROV_ADMIN_FRONTEND_COMMIT || process.env.GITHUB_SHA || gitValue(["rev-parse", "HEAD"], "unknown")).trim();
const sourceState = String(process.env.POKROV_ADMIN_SOURCE_STATE || (gitValue(["status", "--porcelain", "--", "adminapp"], "") ? "dirty" : "clean")).trim();
const builtAt = String(process.env.POKROV_ADMIN_BUILT_AT || new Date().toISOString()).trim();

if (!/^(?:[0-9a-f]{7,64}|unknown)$/i.test(commit)) fail("frontend commit is malformed");
if (!/^(?:clean|dirty|unknown)$/.test(sourceState)) fail("source state is malformed");
if (!Number.isFinite(Date.parse(builtAt))) fail("build timestamp is malformed");

const build = {
  schema: "pokrov-operator-build-v1",
  app: manifest.app,
  version: packageJson.version,
  frontend_commit: commit,
  built_at: builtAt,
  source_state: sourceState,
  route_manifest_hash: routeManifestHash,
  cutover_matrix_hash: cutoverMatrixHash,
  expected_api_schema: manifest.expected_api_schema,
  canonical_domain: manifest.canonical_domain
};
const routes = {
  schema: "pokrov-operator-route-manifest-v1",
  app: manifest.app,
  manifest_hash: routeManifestHash,
  cutover_matrix_hash: cutoverMatrixHash,
  implementation_state: manifest.implementation_state,
  local_parity: cutover.local_parity,
  cutover_gates: cutover.cutover_gates,
  workspaces: manifest.workspaces,
  routes: manifest.routes,
  unique_legacy_capabilities: manifest.unique_legacy_capabilities
};

mkdirSync(outputDir, { recursive: true });
writeFileSync(join(outputDir, "__build.json"), `${JSON.stringify(build, null, 2)}\n`, "utf8");
writeFileSync(join(outputDir, "__routes.json"), `${JSON.stringify(routes, null, 2)}\n`, "utf8");
process.stdout.write(`${JSON.stringify({ ok: true, output_dir: outputDir, route_manifest_hash: routeManifestHash, cutover_matrix_hash: cutoverMatrixHash })}\n`);
