---
name: Trae Daily Check-in
description: 自动领取 Trae CN 每日签到积分 · 走 CDP 协议 · 不动鼠标 · Trae 右下角卡片 + Windows 静音气泡双路提示
---

# Trae Daily Check-in 技能

自动完成 Trae CN 客户端每日签到，领取积分。全程走 Chrome DevTools Protocol（CDP），不移动鼠标、不抢焦点、窗口最小化也能跑。签到成功后同时弹出 Trae 界面内卡片 + Windows 静音系统气泡。

## 什么时候使用

当用户说出以下意图时触发本技能：

- 签到、领积分、每日签到、check in、checkin
- 自动领取 Trae 积分、Trae 签到助手、Trae daily checkin

## 前置条件（必须满足）

1. **Trae CN 已安装**，启动时带 `--remote-debugging-port=9222`（桌面/开始菜单快捷方式属性 → 目标末尾追加该参数）
2. **Python 3.11+** 已安装并在 PATH 中（或设置环境变量 `PYTHON_EXE`）
3. Windows 10 / 11

## 指令

### 第一步：首次安装（仅首次需要）

在技能目录下执行安装脚本，它会自动：
- 探测本机 Python
- 安装 pip 依赖（requests、websocket-client、windows-toasts）
- 注册 Windows 计划任务（每日 7 个触发点自动签到）

```powershell
# 在技能根目录下运行
pwsh -NoProfile -File .\install.ps1
```

如果用户不想注册计划任务（只想手动跑），加 `-NoTask` 参数。

### 第二步：手动执行一次（验证）

```powershell
python .\scripts\trae_checkin.py --no-auto-start
```

输出最后一行是 JSON 结果，关键字段：

| status | 含义 | 后续动作 |
|---|---|---|
| success | 签到成功，含 gained 和 usage | 汇报用户，卡片+气泡自动弹 |
| already | 今日已签到 | 无需重复 |
| running_without_cdp | Trae 在跑但没带端口 | 提醒用户用快捷方式重启，或跑 `.\scripts\Start-TraeWithDebug.ps1` |
| not_running / start_timeout | Trae 未启动或启动超时 | 告诉用户先打开 Trae |

### 第三步：自动运行（可选）

install.ps1 默认已注册计划任务 `TraeDailyCheckin`，触发时机：
- 用户登录 / 锁屏解锁
- 每日 00:05 / 09:05 / 12:30 / 15:30 / 19:00

同一天内多次触发只会写日志（`logs\checkin.log`），不会重复弹卡片。

## 输出示例

```json
{"status":"success","gained":100,"usage":"3,787","how":"already_running"}
```

签到成功后，Trae 右下角会弹出带对勾图标的卡片，Windows 屏幕右下角同时弹出静音系统气泡。

## 环境变量（可选覆盖默认路径）

| 变量 | 默认值 | 用途 |
|---|---|---|
| TRAE_EXE | 自动探测（PATH / 常见路径） | Trae CN.exe 路径 |
| TRAE_CDP_PORT | 9222 | CDP 端口 |
| PYTHON_EXE | 自动探测（PATH） | Python 完整路径 |

PowerShell 临时设置：`$env:TRAE_EXE = "C:\path\to\Trae CN.exe"`
持久设置：`setx TRAE_EXE "..."`（新开终端生效）

## 重要约束

- **必须走 CDP**，不要退回鼠标坐标点击或 UI 模拟（会抢焦点）
- 不要自行重启 Trae（会中断用户对话）
- 连续天数是本地 `data\history.json` 算的，不是 Trae 官方数字

## 故障排查

运行 `.\scripts\Start-TraeWithDebug.ps1` 检查 CDP 是否就绪；查看 `logs\checkin.log` 里的详细记录。
