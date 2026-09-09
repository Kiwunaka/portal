$ErrorActionPreference = 'Stop'
$taskPrivateDir = 'E:/r12-brain-rehearsal-private-20260909'
$taskSecretFile = Join-Path $taskPrivateDir 'backup-passphrase.dpapi'
if (Test-Path -LiteralPath $taskSecretFile) { throw 'Existing protected passphrase; preserve previous run.' }
New-Item -ItemType Directory -Path $taskPrivateDir -Force | Out-Null
$taskBytes = [Security.Cryptography.RandomNumberGenerator]::GetBytes(48)
$taskPassphrase = [Convert]::ToBase64String($taskBytes)
$taskSecure = ConvertTo-SecureString -String $taskPassphrase -AsPlainText -Force
$taskSecure | ConvertFrom-SecureString | Set-Content -LiteralPath $taskSecretFile
$env:POKROV_POSTGRES_BACKUP_PASSPHRASE = $taskPassphrase
try {
    python -B scripts/remote_postgres_backup_restore_gate.py --brain-ip 82.21.114.104 --passwords 'C:/Users/kiwun/Documents/ai/VPN/VPN NODE SSH KEYS/PASSWORDS.txt' --source-db portal --confirm-source portal --target-db portal_r12_20260909_rehearsal --confirm-target portal_r12_20260909_rehearsal --backup-dir /root/backups/r12-20260909 --backup-retain-count 30 --report E:/r12-brain-rehearsal-20260909/backup-restore.json --apply *> E:/r12-brain-rehearsal-20260909/backup-restore.log
    $taskExit = $LASTEXITCODE
} finally {
    Remove-Item Env:POKROV_POSTGRES_BACKUP_PASSPHRASE -ErrorAction SilentlyContinue
    $taskPassphrase = $null
    $taskSecure.Dispose()
    [Array]::Clear($taskBytes)
}
Write-Output "Backup gate exit: $taskExit"
exit $taskExit
