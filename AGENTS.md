# Trae 每日签到助手 · 项目指引（L3 局部规则）

本项目目录：`D:\workspace\10_PROJECTS\active\23-2026-10-25_trae-daily-checkin\` —— **默认修改位置**
创建日期：2026-10-25

## 开工必读

1. `D:\workspace\00_SYSTEM\SPEC.md`（唯一规范正本）
2. `D:\workspace\00_SYSTEM\ENV_MIGRATION.md`（环境变更；路径/依赖问题先读它）
3. `D:\workspace\ACTIVE_TASK.md`
4. `D:\workspace\00_SYSTEM\PITFALL_LOG.md`
5. 本目录 `README.md`、`TASKS.md`、`CHANGELOG.md`

## 项目专有约束

- **只走 CDP**（`http://localhost:9222`）。禁止加入鼠标坐标点击、`SendInput`、`pyautogui` 等界面模拟——会抢焦点、干扰用户工作，该方案已明确废弃。
- **不得擅自重启 Trae**。`work\Start-TraeWithDebug.ps1 -ForceRestart` 只能由用户手动执行；脚本自身只允许在 `--auto-start`（计划任务默认关闭）下启动新实例。
- **签到选择器依赖 Trae 前端结构**：触发条是 `button[class*="accountTrigger"]`，点击必须走完整 pointer/mouse 事件序列（`DISPATCH_FUNC`），普通 `.click()` 会被忽略。Trae 升级后若返回 `panel_not_found`，先改这里。
- **每天只汇报一次**：`data\history.json` 里的 `reported` 标记控制，同日多次触发只写 `logs\checkin.log`。
- **连续天数用本地记录**，不要伪造成 Trae 官方数字；文案已注明来源。
- 不改 Trae 安装目录、不修改其配置文件；快捷方式加 `--remote-debugging-port=9222` 是唯一对运行方式的改动。

## 依赖

- 依赖实体放工作区依赖池，**不在本目录建副本**（`node_modules` / `.venv` 属可重建物，不算长期依赖）
- 取用前先查 `D:\workspace\20_ASSETS\DEP_INDEX.md`；命中即复用，未登记不得下载
- 本项目声明写在 `deps.json`；环境变量契约见 SPEC 附录 A

> 目录说明见 `README.md`（按 SPEC 6.6 单一所有权，本文件不重复目录结构）。

## 记录要求

- `README.md` 保持中英双语：完整中文在前，完整英文在后
- 改源码后更新 `CHANGELOG.md`；有阻塞更新 `TASKS.md`；重要操作写 `logs\`
- 踩坑追加 `PITFALL_LOG.md`（**只追加，禁止整体重写**）
- 有架构/规则类决策追加 `D:\workspace\DECISIONS.md`
- 未经明确要求「打包 / 发版 / 更新版本」时，不生成版本号、不建发布目录、不压缩
- 旧目录 / 迁移来源目录**只读参考，不在其中改源码**
