$ErrorActionPreference = 'Stop'
$taskSecure = [IO.File]::ReadAllText('E:/r12-brain-rehearsal-private-20260909/backup-passphrase.dpapi').Trim() | ConvertTo-SecureString
$taskCredential = [PSCredential]::new('local-backup', $taskSecure)
$env:POKROV_POSTGRES_BACKUP_PASSPHRASE = $taskCredential.GetNetworkCredential().Password
try {
    python -B scripts/remote_postgres_backup_restore_gate.py --brain-ip 82.21.114.104 --passwords 'C:/Users/kiwun/Documents/ai/VPN/VPN NODE SSH KEYS/PASSWORDS.txt' --source-db portal --confirm-source portal --target-db portal_r12_20260909_rehearsal --confirm-target portal_r12_20260909_rehearsal --backup-dir /root/backups/r12-20260909 --backup-retain-count 30 --report E:/r12-brain-rehearsal-20260909/backup-restore-v2.json --apply *> E:/r12-brain-rehearsal-20260909/backup-restore-v2.log
    $taskExit = $LASTEXITCODE
} finally {
    Remove-Item Env:POKROV_POSTGRES_BACKUP_PASSPHRASE -ErrorAction SilentlyContinue
    $taskCredential = $null
    $taskSecure.Dispose()
}
Write-Output "Backup gate retry exit: $taskExit"
exit $taskExit
