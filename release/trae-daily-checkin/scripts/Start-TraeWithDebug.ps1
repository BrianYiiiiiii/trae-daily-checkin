# Start Trae CN with Chrome DevTools Protocol (CDP) remote debugging enabled.
# Usage:
#   .\Start-TrapeWithDebug.ps1              # start Trae with debug port; warn if already running without it
#   .\Start-TrapeWithDebug.ps1 -ForceRestart # restart Trae with debug port (closes running instance)
param(
    [switch]$ForceRestart,
    [int]$Port = $(if ($env:TRAE_CDP_PORT) { [int]$env:TRAE_CDP_PORT } else { 9222 })
)

# 自动探测 Trae 安装路径：环境变量 > PATH > 常见安装位置
function Resolve-TraeExe {
    if ($env:TRAE_EXE -and (Test-Path $env:TRAE_EXE)) { return $env:TRAE_EXE }
    # PATH 里找
    $fromPath = Get-Command "Trae CN.exe" -ErrorAction SilentlyContinue
    if ($fromPath) { return $fromPath.Source }
    # 常见安装位置
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Trae\Trae CN.exe",
        "$env:LOCALAPPDATA\Trae\Trae CN.exe",
        "D:\Applications\Trae\Trae CN.exe",
        "C:\Applications\Trae\Trae CN.exe",
        "C:\Program Files\Trae\Trae CN.exe",
        "C:\Program Files (x86)\Trae\Trae CN.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    return $null
}

$TraeExe = Resolve-TraeExe
if (-not $TraeExe) {
    Write-Output "TRAE_NOT_FOUND"
    Write-Output "请设置环境变量 TRAE_EXE 指向 Trae CN.exe 的完整路径"
    exit 3
}

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
