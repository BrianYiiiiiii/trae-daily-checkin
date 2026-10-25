# Start Trae CN with Chrome DevTools Protocol (CDP) remote debugging enabled.
# Usage:
#   .\Start-TrapeWithDebug.ps1              # start Trae with debug port; warn if already running without it
#   .\Start-TrapeWithDebug.ps1 -ForceRestart # restart Trae with debug port (closes running instance)
param(
    [switch]$ForceRestart,
    [int]$Port = 9222
)

$TraeExe = "D:\Applications\Trae\Trae CN.exe"

function Test-CdpPort {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$Port/json/version" -UseBasicParsing -TimeoutSec 2
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

$running = Get-Process -Name "Trae CN" -ErrorAction SilentlyContinue

if (Test-CdpPort) {
    Write-Output "CDP_READY"
    exit 0
}

if ($running -and -not $ForceRestart) {
    Write-Output "RUNNING_WITHOUT_CDP"
    exit 1
}

if ($running -and $ForceRestart) {
    Stop-Process -Name "Trae CN" -Force
    Start-Sleep -Seconds 3
}

Start-Process -FilePath $TraeExe -ArgumentList "--remote-debugging-port=$Port"

# Wait for CDP to come up (app boot can take a while)
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    if (Test-CdpPort) {
        Write-Output "CDP_READY"
        exit 0
    }
}

Write-Output "CDP_TIMEOUT"
exit 2
