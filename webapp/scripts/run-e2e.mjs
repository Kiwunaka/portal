import { spawnSync } from "node:child_process";
import process from "node:process";

const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const npxCommand = process.platform === "win32" ? "npx.cmd" : "npx";

const suites = {
  full: {
    port: "3102",
    specs: ["e2e/admin-gate.spec.ts", "e2e/cabinet-flow.spec.ts", "e2e/rewards.spec.ts"],
  },
  admin: {
    port: "3101",
    specs: ["e2e/admin-gate.spec.ts"],
  },
  cabinet: {
    port: "3103",
    specs: ["e2e/cabinet-flow.spec.ts", "e2e/rewards.spec.ts"],
  },
};

const [suiteName = "full", ...extraArgs] = process.argv.slice(2);
const suite = suites[suiteName];

if (!suite) {
  console.error(`[e2e] unknown suite: ${suiteName}`);
  console.error(`[e2e] expected one of: ${Object.keys(suites).join(", ")}`);
  process.exit(2);
}

function run(command, args, options = {}) {
  const shellCommand =
    process.platform === "win32" ? [command, ...args].map(quoteForShell).join(" ") : command;
  const shellArgs = process.platform === "win32" ? [] : args;

  const result = spawnSync(shellCommand, shellArgs, {
    stdio: "inherit",
    shell: process.platform === "win32",
    ...options,
  });

  if (result.error) {
    console.error(`[e2e] failed to start ${command}: ${result.error.message}`);
    process.exit(127);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function quoteForShell(value) {
  const text = String(value);
  if (!/[\s"&|<>^]/.test(text)) {
    return text;
  }
  return `"${text.replace(/"/g, '\\"')}"`;
}

function stopPort(port) {
  if (process.platform === "win32") {
    spawnSync(
      "powershell",
      [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        `$port=${port}; Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }; exit 0`,
      ],
      { stdio: "ignore", shell: false },
    );
    return;
  }

  const lookup = spawnSync("lsof", ["-ti", `tcp:${port}`], {
    encoding: "utf-8",
    shell: false,
  });
  if (lookup.error || lookup.status !== 0 || !lookup.stdout?.trim()) {
    return;
  }

  for (const pid of lookup.stdout.trim().split(/\s+/)) {
    spawnSync("kill", ["-9", pid], { stdio: "ignore", shell: false });
  }
}

stopPort(suite.port);
run(npmCommand, ["run", "build"]);

run(npxCommand, ["playwright", "test", ...suite.specs, ...extraArgs], {
  env: {
    ...process.env,
    E2E_PORT: suite.port,
    PLAYWRIGHT_FRESH_SERVER: "1",
    PLAYWRIGHT_SERVER_MODE: "start",
  },
});
