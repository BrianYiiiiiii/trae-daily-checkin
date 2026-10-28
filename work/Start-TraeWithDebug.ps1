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
    # 用 127.0.0.1 而非 localhost：pwsh 7 可能把 localhost 解析到 ::1，而 Trae 只监听 IPv4
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/version" -UseBasicParsing -TimeoutSec 5
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Trae 就绪后后台触发一次签到（pythonw 无窗口；脚本自身幂等：当天已签只走零界面 api_claim）
# 注意：函数内 $MyInvocation.ScriptName 不可靠，用脚本级变量 $ScriptRoot
$ScriptRoot = $PSScriptRoot
function Send-Checkin {
    $root = Split-Path -Parent $ScriptRoot
    $script = Join-Path $root "src\trae_checkin.py"
    if (Test-Path $script) {
        $py = "D:\Python311\pythonw.exe"
        if (-not (Test-Path $py)) { $py = "pythonw.exe" }
        Start-Process -FilePath $py -ArgumentList @($script, "--no-auto-start", "--wait", "5") -WindowStyle Hidden
    }
}

$running = Get-Process -Name "Trae CN" -ErrorAction SilentlyContinue

# 已运行时把窗口带到前台（用户点图标的预期行为）；仅窗口激活，不涉及任何输入模拟
function Show-TraeWindow {
    Add-Type -Namespace W -Name Win32Show -MemberDefinition @"
        [System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr h, int c);
        [System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool SetForegroundWindow(System.IntPtr h);
"@
    $p = Get-Process -Name "Trae CN" -ErrorAction SilentlyContinue |
         Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if ($p) {
        [W.Win32Show]::ShowWindow($p.MainWindowHandle, 9) | Out-Null   # SW_RESTORE
        [W.Win32Show]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    }
}

if (Test-CdpPort) {
    Show-TraeWindow
    Send-Checkin
    Write-Output "CDP_READY"
    exit 0
}

if ($running -and -not $ForceRestart) {
    Show-TraeWindow
    Write-Output "RUNNING_WITHOUT_CDP"
    exit 1
}

if ($running -and $ForceRestart) {
    Stop-Process -Name "Trae CN" -Force
    Start-Sleep -Seconds 3
}

Start-Process -FilePath $TraeExe -ArgumentList "--remote-debugging-port=$Port"

# Wait for CDP to come up (app boot can take a while; 实测冷启动最慢约 2.5 分钟)
$deadline = (Get-Date).AddSeconds(240)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    if (Test-CdpPort) {
        Send-Checkin
        Write-Output "CDP_READY"
        exit 0
    }
}

Write-Output "CDP_TIMEOUT"
exit 2
