# CHANGELOG · Trae 每日签到助手

> 格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)；版本号用 `vMAJOR.MINOR.PATCH`。
> **只有用户明确要求「打包 / 发版 / 更新版本」时才新增版本号**（SPEC 第 1 章铁律 #6）。
> 未发布的改动都写在 `[Unreleased]` 下。

## [Unreleased]

### Added

- 项目初始化：目录骨架来自 `D:\workspace\10_PROJECTS\templates\project-skeleton`
- CDP 自动签到：连接 `localhost:9222`，用完整 pointer/mouse 事件序列展开侧边栏用户面板，读取签到状态并领取积分
- Trae 界面内成功提示：右下角卡片，配色取 `--vscode-notifications-*`，浅/深主题自适应，8 秒淡出，不拦截鼠标
- 每日汇报：`data\签到日报.md`（每天一条，最新在上）+ `data\history.json`（结构化历史，含本次增量与连续天数）
- 计划任务 `TraeDailyCheckin`：解锁 / 登录 / 09:05 / 12:30 / 15:30 / 19:00 触发，`pythonw` 静默运行
- `work\Start-TraeWithDebug.ps1`：带调试端口启动 Trae 的启动器

### Changed

- 签到成功后自动收起自己打开的面板（用户手动打开的不动）
- 数据与日志从 C 盘迁到本项目 `data\`、`logs\`；C 盘只保留技能入口 `SKILL.md` 指针
- 计划任务、技能文档、脚本常量全部改指 D 盘路径
- 2026-10-26：`TraeDailyCheckin` 追加每日 `00:05` 触发器。原因：原最早固定触发点是 09:05，跨日后空窗 8+ 小时，用户凌晨看到积分未领会误判为故障；电脑凌晨在跑则跨日 5 分钟即签，凌晨睡/关则由 SessionUnlock 兜底。任务名与既有触发器保持不变
- 2026-10-26：签到汇报从「仅 Trae 内卡片」改为「Trae 卡片 + Windows 系统气泡」双路提示，触发时机不变（`history.json` 的 `reported` 由 false→true 那一刻，一日一报）。系统气泡静音（`ToastAudio(silent=True)`），与卡片同时触发。之前 Removed 掉的 Windows 通知气泡是用户主动要求加回

### Fixed

- 2026-10-27：修复计划任务解锁触发时闪黑色控制台窗口。原因：pythonw（无控制台）subprocess 调用 tasklist（控制台程序）时 Windows 会分配新控制台；`--wait 15` 模式下每 20 秒轮询一次就闪一次。修复：subprocess 调用加 `CREATE_NO_WINDOW`。release 技能包同步更新

- 触发条点击原来取外层容器中心点，窗口尺寸变化会点空；改为点击按钮自身 `button[class*="accountTrigger"]`

### Added（2026-10-26 追记）

- `src\trae_checkin.py` 新增 `notify_windows()`：基于 PyPI `windows-toasts==1.3.1`（winrt 3.2.1）发静音系统通知气泡；`main()` 里 `ping(tip)` 之后同步调用；任何异常静默吞掉（不影响主流程）。新增依赖已登记 `D:\workspace\20_ASSETS\DEP_INDEX.md` 维护记录 + 本项目 `deps.json`
- `work\preview_toast.py`：预览脚本同步触发系统气泡，与真实签到后行为一致

### Removed

- 鼠标坐标点击兜底、早期 PowerShell Windows 通知气泡脚本（用户当时要求全后台静默、提示只在 Trae 内）；2026-10-26 用户改主意要加回气泡，改走 Python `windows-toasts` 实现（见上方 Added 追记），早期 PS 脚本不再使用

---

## 记录约定

- `Added` 新增功能 / `Changed` 行为变更 / `Fixed` 修复 / `Removed` 移除 / `Security` 安全相关
- 每条写清「改了什么 + 为什么」，不要只写文件名
- 发版时把 `[Unreleased]` 整体移到新版本号标题下，并补日期
- 发布产物位置统一为 `D:\workspace\30_OUTPUTS\releases\<ProjectName>\<版本>\`
