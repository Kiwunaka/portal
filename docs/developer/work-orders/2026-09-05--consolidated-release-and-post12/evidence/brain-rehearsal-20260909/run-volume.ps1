$ErrorActionPreference = 'Stop'
$taskSecure = [IO.File]::ReadAllText('E:/r12-brain-rehearsal-private-20260909/backup-passphrase.dpapi').Trim() | ConvertTo-SecureString
$taskCredential = [PSCredential]::new('local-backup', $taskSecure)
$taskStart = [Diagnostics.ProcessStartInfo]::new((Get-Command python.exe).Source)
$taskStart.UseShellExecute = $false
$taskStart.CreateNoWindow = $true
$taskStart.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
$taskStart.RedirectStandardInput = $true
$taskStart.RedirectStandardOutput = $true
$taskStart.RedirectStandardError = $true
$taskStart.ArgumentList.Add('-B')
$taskStart.ArgumentList.Add('E:/r12-brain-rehearsal-20260909/volume-snapshot.py')
$taskStart.ArgumentList.Add('apply')
$taskProcess = [Diagnostics.Process]::Start($taskStart)
try {
    $taskOutput = $taskProcess.StandardOutput.ReadToEndAsync()
    $taskError = $taskProcess.StandardError.ReadToEndAsync()
    $taskProcess.StandardInput.Write($taskCredential.GetNetworkCredential().Password)
    $taskProcess.StandardInput.Close()
    $taskProcess.WaitForExit()
    [IO.File]::WriteAllText('E:/r12-brain-rehearsal-20260909/volume-apply-v2.log', $taskOutput.GetAwaiter().GetResult() + $taskError.GetAwaiter().GetResult())
    $taskExit = $taskProcess.ExitCode
} finally {
    $taskProcess.Dispose()
    $taskSecure.Dispose()
    $taskCredential = $null
}
Write-Output "Volume recovery exit: $taskExit"
exit $taskExit
