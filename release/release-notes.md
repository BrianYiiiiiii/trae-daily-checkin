# Trae Daily Check-in · 标准技能包

自动领取 Trae CN 每日签到积分。全程走 CDP 协议，不动鼠标、不抢焦点，窗口最小化也能跑。签到成功后双路提示：Trae 界面右下角卡片 + Windows 静音系统气泡。

## 使用步骤

1. 下载 `trae-daily-checkin.zip` 并解压
2. 在解压目录运行安装脚本（自动装依赖 + 注册每日计划任务）：

   ```powershell
   pwsh -NoProfile -File .\install.ps1
   ```

   只想手动跑、不注册计划任务：`.\install.ps1 -NoTask`
3. 确保 Trae 启动时带调试端口：快捷方式"目标"末尾追加 `--remote-debugging-port=9222`
4. 手动验证一次：

   ```powershell
   python .\scripts\trae_checkin.py --no-auto-start
   ```

## 也可以装成 Trae 技能

Trae → 插件市场 → 技能 → 上传技能，选择本 zip 内的 `trae-daily-checkin` 文件夹（含 `SKILL.md`）。

## 环境变量（一般不用设，脚本会自动探测）

| 变量 | 默认 | 说明 |
|---|---|---|
| `TRAE_EXE` | 自动探测（PATH / 常见安装路径） | Trae CN.exe 完整路径 |
| `TRAE_CDP_PORT` | `9222` | CDP 调试端口 |
| `PYTHON_EXE` | 自动探测（PATH） | Python 完整路径 |

## 依赖

Python 3.11+，以及 `requests` / `websocket-client` / `windows-toasts`（install.ps1 会自动 pip 安装）。

## 说明

- 计划任务 `TraeDailyCheckin` 在登录/解锁及每日 00:05 / 09:05 / 12:30 / 15:30 / 19:00 触发，同一天只弹一次提示
- 不修改 Trae 安装目录，不模拟鼠标操作
- 详见仓库 [README](https://github.com/BrianYiiiiiii/trae-daily-checkin#readme)
