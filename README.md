
# Trae 每日签到助手

> 项目目录：`D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin`
> 创建日期：2026-10-25

---

## 一、项目目的

自动完成 Trae CN 客户端的每日签到领取积分，用户不需要任何操作。脚本通过 Chrome DevTools Protocol（CDP）连接本机 Trae，在页面内直接把签到面板点开、读取状态、领取积分，再把结果同时落到四个地方：Trae 界面右下角的通知卡片、Windows 系统通知气泡（静音）、`data\签到日报.md` 日报、`data\history.json` 结构化历史。配合 Windows 计划任务，在解锁、登录和每天五个固定时刻自动运行，全程不移动鼠标、不抢焦点、窗口最小化也能跑。

## 二、运行方式

### 环境要求

- 操作系统：Windows 11
- 运行时：Python 3.11（`D:\Python311\python.exe`；计划任务用同目录 `pythonw.exe` 静默运行）
- 关键依赖：`requests 2.31.0`、`websocket-client 1.9.0`、`windows-toasts 1.3.1`（系统 Python 已装；windows-toasts 用于发静音 Windows 系统气泡）
- 前置条件：Trae 启动时带 `--remote-debugging-port=9222`（桌面与开始菜单快捷方式已加该参数）

### 依赖准备

依赖统一从工作区依赖池取用，**不要在本目录内建副本**：

1. 先查台账：`D:\workspace\20_ASSETS\DEP_INDEX.md`
2. 命中即复用；未命中才下载，并登记回台账
3. 项目自身声明写在 `deps.json`

### 启动步骤

```powershell
# 手动跑一次（前台输出 JSON 结果）
python "D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src\trae_checkin.py" --no-auto-start

# 后台等待模式（Trae 未开时最多等 N 分钟）
python "...\src\trae_checkin.py" --no-auto-start --wait 15

# Trae 没开调试端口时，用这个带端口重启
pwsh -NoProfile -File "...\work\Start-TraeWithDebug.ps1"
```

计划任务：`TraeDailyCheckin`（解锁 / 登录 / 每日 00:05 / 09:05 / 12:30 / 15:30 / 19:00 触发，`pythonw` 静默）。

## 三、目录说明

```
23-2026-10-25_trae-daily-checkin
├── README.md      本文件
├── TASKS.md       待办 / 已完成 / 阻塞
├── CHANGELOG.md   重要改动记录
├── AGENTS.md      AI 入口（默认修改位置）
├── deps.json      依赖声明
├── docs\          说明文档、需求、参考资料
├── src\           签到脚本 trae_checkin.py
├── data\          签到日报.md、history.json
├── work\          临时脚本（带端口启动器等）
├── outputs\       本项目产物
└── logs\          运行日志 checkin.log
```

## 四、关键路径

| 用途 | 路径 |
|---|---|
| 源码 | `src\trae_checkin.py` |
| 签到日报 | `data\签到日报.md` |
| 历史数据 | `data\history.json` |
| 日志 | `logs\checkin.log` |
| 带端口启动器 | `work\Start-TraeWithDebug.ps1` |
| 依赖实体（区一） | 无（仅用系统 Python 预装包） |

## 五、边界与注意事项

- **本目录是默认修改位置**；旧目录/迁移来源目录**只读参考，不在其中改源码**。
- 以下内容**不纳入版本库、不打包、不迁移**：浏览器 profile、登录态（cookie/token/session）、本地数据库、缓存、导出结果、隐私数据。
- 未经明确要求「打包 / 发版 / 更新版本」时，**只改源码与文档**，不生成版本号、不建发布目录、不压缩。
- **只走 CDP**：不要用鼠标坐标点击或 Win32 鼠标模拟（会抢焦点、干扰工作），该方案已废弃。
- 不要在用户不知情时重启 Trae；`-ForceRestart` 只能由用户手动使用。
- Trae 未带调试端口时脚本无法领取，只能报告 `running_without_cdp`，不得退化成界面点击。
- 连续签到天数按本地 `history.json` 计算（从 2026-10-25 起），不是 Trae 官方连续天数。

## 六、当前状态

- 版本：未发版
- 状态：已上线运行（2026-10-25）
- 已知问题：见 `TASKS.md`

---

## 1. Purpose

Automatically performs the daily check-in claim for Trae CN and collects the credits, with zero user interaction. The script connects to the local Trae client over the Chrome DevTools Protocol (CDP), opens the check-in popover inside the page, reads the current state, claims the credits, and records the outcome in four places: an in-app toast at the bottom-right corner of Trae, a silent Windows system notification bubble, a daily report file at `data\签到日报.md`, and a structured history at `data\history.json`. A Windows scheduled task runs it on unlock, on logon, and at five fixed times per day. It never moves the mouse, never steals focus, and works while the Trae window is minimized.

## 2. How to Run

### Requirements

- OS: Windows 11
- Runtime: Python 3.11 (`D:\Python311\python.exe`; the scheduled task uses `pythonw.exe` from the same folder for silent execution)
- Key dependencies: `requests 2.31.0`, `websocket-client 1.9.0`, `windows-toasts 1.3.1` (all installed into the system Python; `windows-toasts` is used to push the silent Windows notification bubble)
- Prerequisite: Trae must be started with `--remote-debugging-port=9222` (the desktop and Start-menu shortcuts already carry this flag)

### Preparing Dependencies

Dependencies are taken from the shared workspace dependency pool. **Do not create local copies:**

1. Check the ledger first: `D:\workspace\20_ASSETS\DEP_INDEX.md`
2. If it is already there, reuse it; only download when missing, then register it back in the ledger
3. Declare this project's own dependencies in `deps.json`

### Startup Steps

```powershell
# Run once in the foreground (prints a JSON result)
python "D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\src\trae_checkin.py" --no-auto-start

# Background wait mode (wait up to N minutes if Trae is not running yet)
python "...\src\trae_checkin.py" --no-auto-start --wait 15

# Restart Trae with the debug port if it is currently running without it
pwsh -NoProfile -File "...\work\Start-TraeWithDebug.ps1"
```

Scheduled task: `TraeDailyCheckin` (fires on unlock, on logon, and daily at 00:05, 09:05, 12:30, 15:30, 19:00; runs silently via `pythonw`).

## 3. Directory Layout

```
23-2026-10-25_trae-daily-checkin
├── README.md      This file
├── TASKS.md       Todo / done / blocked
├── CHANGELOG.md   Notable changes
├── AGENTS.md      AI entry point (default edit location)
├── deps.json      Dependency declarations
├── docs\          Documentation, requirements, references
├── src\           The check-in script trae_checkin.py
├── data\          Daily report and history data
├── work\          Throwaway scripts (debug-port launcher, probes)
├── outputs\       Project artifacts
└── logs\          Runtime log checkin.log
```

## 4. Key Paths

| Purpose | Path |
|---|---|
| Source | `src\trae_checkin.py` |
| Daily report | `data\签到日报.md` |
| History data | `data\history.json` |
| Logs | `logs\checkin.log` |
| Debug-port launcher | `work\Start-TraeWithDebug.ps1` |
| Dependency files (Area 1) | None (only pre-installed system Python packages) |

## 5. Boundaries and Cautions

- **This directory is the default edit location.** Legacy or migration-source directories are **read-only references — never edit source code there.**
- The following are **never committed, packaged, or migrated**: browser profiles, login state (cookies/tokens/sessions), local databases, caches, exported results, private data.
- Unless you are explicitly asked to "package / release / bump the version", **change source and docs only** — do not create version numbers, release directories, or archives.
- **CDP only.** Do not add mouse-coordinate clicks or Win32 mouse simulation: they steal focus and interfere with the user's work, and that approach has been retired.
- Never restart Trae without the user's knowledge; `-ForceRestart` is for manual use by the user only.
- If Trae is running without the debug port, the script cannot claim anything and must report `running_without_cdp`; it must not silently fall back to UI clicking.
- The consecutive-day count is computed from the local `history.json` (starting 2026-10-25) and is not Trae's official streak.

## 6. Current Status

- Version: unreleased
- Status: running in production (since 2026-10-25)
- Known issues: see `TASKS.md`
