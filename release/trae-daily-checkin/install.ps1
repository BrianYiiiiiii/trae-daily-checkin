# Trae Daily Check-in 一键安装脚本
# 用法：在本目录下直接运行
#   .\install.ps1            # 安装依赖 + 注册计划任务
#   .\install.ps1 -NoTask    # 只装依赖，不注册计划任务
param([switch]$NoTask)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Scripts = Join-Path $Root "scripts"

# --- 探测 Python ---
$Py = $null
if ($env:PYTHON_EXE -and (Test-Path $env:PYTHON_EXE)) {
    $Py = $env:PYTHON_EXE
} else {
    $fromPath = Get-Command python -ErrorAction SilentlyContinue
    if ($fromPath) { $Py = $fromPath.Source }
    else {
        # 常见安装位置兜底
        foreach ($c in @("C:\Python311\python.exe", "C:\Python312\python.exe", "D:\Python311\python.exe", "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe")) {
            if (Test-Path $c) { $Py = $c; break }
        }
    }
}
if (-not $Py) { Write-Host "未找到 Python，请先安装 Python 3.11+ 或设置环境变量 PYTHON_EXE" -ForegroundColor Red; exit 1 }
Write-Host "Python 路径: $Py" -ForegroundColor Cyan

# --- 装依赖 ---
Write-Host "安装依赖 ..." -ForegroundColor Cyan
& $Py -m pip install -r (Join-Path $Scripts "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Host "pip install 失败" -ForegroundColor Red; exit 1 }
Write-Host "依赖安装完成" -ForegroundColor Green

# --- 注册计划任务（可选） ---
if (-not $NoTask) {
    $Pyw = $Py -replace 'python\.exe$', 'pythonw.exe'
    if (-not (Test-Path $Pyw)) { $Pyw = $Py }  # 某些发行版没有 pythonw
    $ScriptPath = Join-Path $Scripts "trae_checkin.py"
    $TaskName = "TraeDailyCheckin"
    $Action = New-ScheduledTaskAction -Execute $Pyw -Argument "`"$ScriptPath`" --no-auto-start --wait 15" -WorkingDirectory $Scripts

    # 触发器：登录 + 解锁 + 每日 00:05 / 09:05 / 12:30 / 15:30 / 19:00
    $Triggers = @()
    $Triggers += New-ScheduledTaskTrigger -AtLogOn
    $Triggers += New-ScheduledTaskTrigger -AtLogOff  # 覆盖锁屏解锁场景；某些 Win11 版本不支持则忽略
    try { $Triggers += New-ScheduledTaskTrigger -Daily -At 00:05 } catch {}
    try { $Triggers += New-ScheduledTaskTrigger -Daily -At 09:05 } catch {}
    try { $Triggers += New-ScheduledTaskTrigger -Daily -At 12:30 } catch {}
    try { $Triggers += New-ScheduledTaskTrigger -Daily -At 15:30 } catch {}
    try { $Triggers += New-ScheduledTaskTrigger -Daily -At 19:00 } catch {}

    $Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -StartWhenAvailable

    try {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Triggers -Settings $Settings -Description "Auto check-in for Trae CN credits" -RunLevel Limited | Out-Null
        Write-Host "计划任务 $TaskName 已注册" -ForegroundColor Green
    } catch {
        Write-Host "计划任务注册失败，需要管理员权限；可手动用 Task Scheduler 创建" -ForegroundColor Yellow
    }
}

# --- 提示 ---
Write-Host ""
Write-Host "====== 安装完成 ======" -ForegroundColor Green
Write-Host "手动运行一次：" -ForegroundColor Cyan
Write-Host "  $Py `"$ScriptPath`" --no-auto-start"
Write-Host ""
Write-Host "重要：Trae 启动时必须带 --remote-debugging-port=9222" -ForegroundColor Yellow
Write-Host "  快捷方式属性 → 目标末尾加 --remote-debugging-port=9222"
Write-Host "  或运行 .\scripts\Start-TraeWithDebug.ps1"
Write-Host ""
Write-Host "环境变量（可选）：" -ForegroundColor Cyan
Write-Host "  TRAE_EXE       = Trae CN.exe 完整路径"
Write-Host "  TRAE_CDP_PORT  = CDP 端口（默认 9222）"
Write-Host "  PYTHON_EXE     = Python 完整路径"
