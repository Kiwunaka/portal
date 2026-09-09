$ErrorActionPreference = 'Stop'
$env:PATH = 'C:/Users/kiwun/tools/flutter/git-3.38.5/bin;E:/POKROV-tools/runtimes/node-v22.14.0-win-x64;E:/POKROV-tools/toolchains/go1.25.13-windows-amd64/go/bin;' + $env:PATH
$env:GOTOOLCHAIN = 'go1.26.8'
$env:POKROV_PLATFORM_ROOT = 'E:/r12-promoted-platform-20260909'
$env:POKROV_CORE_ROOT = 'E:/r12core-implementation'
$env:PLAYWRIGHT_BROWSERS_PATH = 'C:/Users/kiwun/AppData/Local/ms-playwright'
Set-Location -LiteralPath E:/r12-promoted-platform-20260909
python.exe -B scripts/release_1_2_local_quality_gate.py --platform-root E:/r12-promoted-platform-20260909 --client-root E:/r12-promoted-client-20260909 --core-root E:/r12core-implementation --evidence-dir E:/r12-promoted-quality-20260909 *> E:/r12-source-promotion-20260909/local-quality.log
$gateExit = $LASTEXITCODE
Write-Output "Local quality gate exit: $gateExit"
exit $gateExit
